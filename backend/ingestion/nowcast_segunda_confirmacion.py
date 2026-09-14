"""
Segunda confirmacion independiente del proto-predictor de nowcast de horizonte corto.

Metodo predeclarado en docs/experimentos/nowcast-segunda-confirmacion.md (commit anterior).

Reimplementacion DESDE CERO de: formula del WIS, bucle de forward-chaining, construccion de
features, baselines y criterio de veredicto. El script original
(experimento_nowcast_corto_plazo.py) se consulta solo para dudas de esquema/SQL.

Solo lectura de Postgres. No escribe filas, no toca esquema, migraciones, seed, FastAPI ni
frontend. numpy + psycopg2 + sklearn, sin pandas.

Uso:
    POSTGRES_HOST=localhost python nowcast_segunda_confirmacion.py --wis-test
    POSTGRES_HOST=localhost python nowcast_segunda_confirmacion.py --paridad
    POSTGRES_HOST=localhost python nowcast_segunda_confirmacion.py --esquema-b --cadencia 1,2,4
    POSTGRES_HOST=localhost python nowcast_segunda_confirmacion.py --esquema-a
    POSTGRES_HOST=localhost python nowcast_segunda_confirmacion.py --todo
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from db import get_connection

SALIDA = Path(__file__).parent / "data" / "interim" / "nowcast_confirmacion"

# --- constantes del experimento (firmadas) ---------------------------------
ANIOS_PRUEBA = (2019, 2021, 2022, 2023, 2024)
ANIO_EXCLUIDO = 2020
QUANTILES = np.array(
    [0.01, 0.025, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50,
     0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.975, 0.99]
)
IDX_MED = 11
N_Q = len(QUANTILES)
VARIABLES_CLIMA = (
    "temp_media", "temp_max", "temp_min",
    "precipitation_sum", "precipitation_hours",
    "humedad_relativa_media", "punto_rocio",
)
N_LAGS = 8
HGBR_KW = dict(
    loss="quantile", max_iter=150, max_leaf_nodes=7, min_samples_leaf=20,
    l2_regularization=1.0, learning_rate=0.05, early_stopping=False, random_state=0,
)
CRIT_COB_95 = (0.85, 0.99)
CRIT_COB_50 = (0.35, 0.65)
CRIT_MIN_ANIOS = 4


# ==========================================================================
# 1. WIS reimplementado desde cero
# ==========================================================================

def wis_single(y: float, q: np.ndarray) -> float:
    """Weighted Interval Score, 23 cuantiles simetricos, Bracher et al. 2021.

        WIS = ( w0*|y-m| + sum_{k=1..K} w_k * IS_{a_k}(y) ) / (K + 1/2)

    con w0 = 1/2, w_k = a_k/2, y el interval score

        IS_a(l,u,y) = (u-l) + (2/a)(l-y)[y<l] + (2/a)(y-u)[y>u].

    Los K = 11 intervalos centrales son (q_i, q_{22-i}) para i = 0..10, con nivel
    a_k = 2 * q_i (cobertura nominal 1 - a_k). Termino de mediana en q_11 = 0.50.
    """
    q = np.sort(np.asarray(q, dtype=float))
    m = q[IDX_MED]
    acc = 0.5 * abs(y - m)
    K = 0
    for i in range(11):
        lo = q[i]
        hi = q[22 - i]
        a = 2.0 * QUANTILES[i]
        is_a = (hi - lo)
        if y < lo:
            is_a += (2.0 / a) * (lo - y)
        elif y > hi:
            is_a += (2.0 / a) * (y - hi)
        acc += (a / 2.0) * is_a
        K += 1
    return acc / (K + 0.5)


def wis_vec(y: np.ndarray, qs: np.ndarray) -> np.ndarray:
    return np.array([wis_single(yi, qi) for yi, qi in zip(y, qs)])


def cobertura_emp(y: np.ndarray, qs: np.ndarray, lo_idx: int, hi_idx: int) -> float:
    s = np.sort(qs, axis=1)
    return float(np.mean((y >= s[:, lo_idx]) & (y <= s[:, hi_idx])))


def prueba_wis() -> bool:
    """Identidad degenerada + monotonias. Devuelve True si todo pasa."""
    rng = np.random.default_rng(0)
    ok = True
    for _ in range(2000):
        y = float(rng.uniform(-50, 5000))
        m = float(rng.uniform(-50, 5000))
        val = wis_single(y, np.full(N_Q, m))
        if abs(val - abs(y - m)) > 1e-9:
            print(f"  FALLO identidad: y={y:.3f} m={m:.3f} wis={val:.6f} |y-m|={abs(y-m):.6f}")
            ok = False
            break
    # y por encima de todos los cuantiles: cada intervalo k aporta pendiente
    # (a_k/2)(2/a_k) = 1 -> 11 intervalos + termino de mediana 0.5, todo /(K+1/2).
    q = np.linspace(10, 90, N_Q)
    w0 = wis_single(200.0, q)
    w1 = wis_single(201.0, q)
    esperado = (11 * 1.0 + 0.5) / (11 + 0.5)  # = 1.0
    if abs((w1 - w0) - esperado) > 1e-9:
        print(f"  FALLO pendiente fuera de intervalo: {(w1-w0):.6f} vs {esperado:.6f}")
        ok = False
    # con y dentro de un solo intervalo de cobertura (entre q10 y q12, fuera de
    # los 10 mas internos... en realidad entre q11 mediana): solo mediana movil.
    y_in = 50.0  # entre q[0]=10 y q[22]=90, cubierto por los 11 intervalos
    below = sum(1 for i in range(11) if not (q[i] <= y_in <= q[22 - i]))
    if below != 0:
        print(f"  aviso: y_in no cubierto por {below} intervalos")
    # cubrir mejor no empeora: forecast mas ancho centrado que cubre y
    ancho = np.array([100 + (i - IDX_MED) * 30 for i in range(N_Q)], dtype=float)
    estrecho = np.array([100 + (i - IDX_MED) * 5 for i in range(N_Q)], dtype=float)
    if not wis_single(100.0, estrecho) <= wis_single(100.0, ancho) + 1e-9:
        print("  FALLO: intervalo estrecho perfectamente calibrado deberia puntuar mejor")
        ok = False
    print(f"  prueba WIS: {'OK' if ok else 'FALLO'} (identidad degenerada en 2000 casos + monotonias)")
    return ok


# ==========================================================================
# 2. Carga de la serie (SQL tomado del esquema; agregacion reimplementada)
# ==========================================================================

class Serie:
    def __init__(self, fecha, anio, semana, doy, casos, clima, oni):
        self.fecha = fecha
        self.anio = anio
        self.semana = semana
        self.doy = doy
        self.casos = casos
        self.z = np.log1p(casos)
        self.clima = clima
        self.oni = oni
        self.T = len(fecha)


def cargar_serie() -> Serie:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.fecha_inicio, c.anio, c.semana_epi, c.conteo
            FROM casos_epidemiologicos c
            JOIN regiones r      ON r.id = c.region_id
            JOIN fuentes_datos f ON f.id = c.fuente_id
            JOIN semanas_epidemiologicas s
              ON s.anio = c.anio AND s.semana_epi = c.semana_epi
            WHERE r.codigo = 'SV' AND c.clasificacion = 'total'
              AND f.codigo = 'opendengue_v1_3'
            ORDER BY s.fecha_inicio
            """
        )
        filas = cur.fetchall()
        fecha = np.array([f[0] for f in filas], dtype=object)
        anio = np.array([int(f[1]) for f in filas])
        semana = np.array([int(f[2]) for f in filas])
        casos = np.array([float(f[3]) for f in filas])
        doy = np.array([d.timetuple().tm_yday for d in fecha])

        saltos = np.array([(fecha[i] - fecha[i - 1]).days for i in range(1, len(fecha))])
        if np.any((saltos < 6) | (saltos > 8)):
            raise SystemExit(f"serie no contigua: {saltos[(saltos<6)|(saltos>8)][:10]}")

        idx = {(int(a), int(w)): k for k, (a, w) in enumerate(zip(anio, semana))}
        clima = {}
        for var in VARIABLES_CLIMA:
            cur.execute(
                """
                SELECT va.anio, va.semana_epi, AVG(va.valor)
                FROM variables_ambientales va
                JOIN regiones r ON r.id = va.region_id
                WHERE r.nivel_admin = 1 AND r.pais = 'SV' AND va.variable = %s
                GROUP BY va.anio, va.semana_epi
                """,
                (var,),
            )
            col = np.full(len(fecha), np.nan)
            for a, w, v in cur.fetchall():
                k = idx.get((int(a), int(w)))
                if k is not None:
                    col[k] = float(v)
            clima[var] = col

        cur.execute(
            """
            SELECT va.anio, va.semana_epi, va.valor
            FROM variables_ambientales va
            JOIN regiones r ON r.id = va.region_id
            WHERE r.codigo = 'SV' AND va.variable = 'oni_anom'
            """
        )
        oni = np.full(len(fecha), np.nan)
        for a, w, v in cur.fetchall():
            k = idx.get((int(a), int(w)))
            if k is not None:
                oni[k] = float(v)
        for k in range(1, len(oni)):
            if np.isnan(oni[k]):
                oni[k] = oni[k - 1]
        if np.isnan(oni[0]):
            oni[0] = 0.0
    finally:
        conn.close()
    return Serie(fecha, anio, semana, doy, casos, clima, oni)


# ==========================================================================
# 3. Features (reimplementadas; replican el SCRIPT original para la paridad)
# ==========================================================================

def features(serie: Serie, t: int, h: int):
    if t < N_LAGS:
        return None
    z = serie.z
    lags = z[t - N_LAGS + 1: t + 1][::-1]          # z[t], z[t-1], ... z[t-7]
    media4 = float(z[t - 3: t + 1].mean())
    media8 = float(z[t - 7: t + 1].mean())
    momentum = float(z[t] - z[t - 4])
    tt = t + h if (t + h) < serie.T else t
    doy_obj = serie.doy[tt]
    harm = []
    for k in (1, 2, 3):
        ang = 2.0 * np.pi * k * doy_obj / 365.25
        harm += [np.sin(ang), np.cos(ang)]
    clima_feat = []
    for var in VARIABLES_CLIMA:
        v = serie.clima[var][t - 3: t + 1]
        if np.any(np.isnan(v)):
            return None
        clima_feat.append(float(v.mean()))
    oni_t = serie.oni[t]
    if np.isnan(oni_t):
        oni_t = 0.0
    anio_obj = float(serie.anio[tt])
    return np.concatenate([lags, [media4, media8, momentum], harm, clima_feat, [oni_t, anio_obj]])


# ==========================================================================
# 4. Pares de entrenamiento con asercion dura anti-fuga
# ==========================================================================

def pares_entrenamiento(serie: Serie, origen: int, h: int, anio_min: int,
                        permutar_semilla=None, holgura_fuga: int = 0):
    """(X, Y, idx_objetivo) con fecha(objetivo) < fecha(origen) - holgura.

    holgura_fuga: dias de holgura ANTES del corte. 0 = filtro correcto (estricto).
    Un valor negativo relaja el corte (control negativo: permite objetivos en la
    fecha del origen). idx_objetivo permite verificar la condicion de forma
    independiente del filtro.
    """
    from datetime import timedelta
    f_corte = serie.fecha[origen] - timedelta(days=holgura_fuga)
    X, Y, idx = [], [], []
    for t in range(serie.T - h):
        tgt = t + h
        if serie.fecha[tgt] >= f_corte:
            continue
        if serie.anio[tgt] == ANIO_EXCLUIDO or serie.anio[tgt] < anio_min:
            continue
        x = features(serie, t, h)
        if x is None:
            continue
        X.append(x)
        Y.append(serie.z[tgt])
        idx.append(tgt)
    X = np.array(X)
    Y = np.array(Y)
    idx = np.array(idx, dtype=int)
    if permutar_semilla is not None and len(Y):
        Y = Y[np.random.default_rng(permutar_semilla).permutation(len(Y))]
    return X, Y, idx


def verificar_anti_fuga(serie: Serie, origenes, h: int, anio_min: int) -> dict:
    muestra = origenes[:: max(1, len(origenes) // 15)]
    n_ok = 0
    for o in muestra:
        _, _, tgts = pares_entrenamiento(serie, o, h, anio_min)
        assert len(tgts) > 0
        peor = max(serie.fecha[k] for k in tgts)
        assert peor < serie.fecha[o], f"FUGA origen {o}: {peor} >= {serie.fecha[o]}"
        n_ok += 1
    # control negativo en el BORDE: relajar el corte un dia debe permitir
    # objetivos con fecha == fecha(origen) y hacer fallar la asercion estricta.
    mordio = False
    for o in muestra:
        _, _, tgts = pares_entrenamiento(serie, o, h, anio_min, holgura_fuga=-1)
        if any(serie.fecha[k] >= serie.fecha[o] for k in tgts):
            mordio = True
            break
    assert mordio, "control negativo de borde no mordio: la asercion no discrimina en el limite"
    return {"origenes_verificados": n_ok, "control_negativo_borde_mordio": True}


# ==========================================================================
# 5. Baselines reimplementados
# ==========================================================================

def _pool_clim(serie: Serie, anio_obj: int, semana_obj: int, anio_min: int) -> np.ndarray:
    m = ((serie.anio < anio_obj) & (serie.anio >= anio_min) & (serie.anio != ANIO_EXCLUIDO)
         & (np.abs(serie.semana - semana_obj) <= 1))
    return serie.casos[m]


def _residuos_h(serie: Serie, f_corte, h: int, anio_min: int) -> np.ndarray:
    out = []
    for t in range(serie.T - h):
        tgt = t + h
        if serie.fecha[tgt] < f_corte and serie.anio[tgt] != ANIO_EXCLUIDO and serie.anio[tgt] >= anio_min:
            out.append(serie.z[tgt] - serie.z[t])
    return np.array(out)


def baseline_persistencia(serie, origenes, h, anio_min):
    qs, y, an = [], [], []
    for o in origenes:
        d = _residuos_h(serie, serie.fecha[o], h, anio_min)
        qz = serie.z[o] + np.quantile(d, QUANTILES)
        qs.append(np.clip(np.expm1(qz), 0, None))
        y.append(serie.casos[o + h]); an.append(int(serie.anio[o + h]))
    return _pack("persistencia_rw", qs, y, an)


def baseline_climatologia(serie, origenes, h, anio_min):
    qs, y, an = [], [], []
    for o in origenes:
        tgt = o + h
        pool = _pool_clim(serie, int(serie.anio[tgt]), int(serie.semana[tgt]), anio_min)
        q = (np.full(N_Q, serie.casos[o]) if len(pool) < 3 else np.quantile(pool, QUANTILES))
        qs.append(np.clip(q, 0, None))
        y.append(serie.casos[tgt]); an.append(int(serie.anio[tgt]))
    return _pack("climatologia_estacional", qs, y, an)


def baseline_persistencia_estacional(serie, origenes, h, anio_min):
    qs, y, an = [], [], []
    for o in origenes:
        d = _residuos_h(serie, serie.fecha[o], h, anio_min)
        tgt = o + h
        pool_o = _pool_clim(serie, int(serie.anio[o]), int(serie.semana[o]), anio_min)
        pool_t = _pool_clim(serie, int(serie.anio[tgt]), int(serie.semana[tgt]), anio_min)
        ajuste = (np.log1p(np.median(pool_t)) - np.log1p(np.median(pool_o))
                  if len(pool_o) >= 3 and len(pool_t) >= 3 else 0.0)
        qz = serie.z[o] + ajuste + np.quantile(d - np.median(d), QUANTILES)
        qs.append(np.clip(np.expm1(qz), 0, None))
        y.append(serie.casos[tgt]); an.append(int(serie.anio[tgt]))
    return _pack("persistencia_estacional", qs, y, an)


def _pack(nombre, qs, y, an):
    qs = np.array(qs); y = np.array(y, dtype=float); an = np.array(an, dtype=int)
    return {"nombre": nombre, "qs": qs, "y": y, "anio": an, "wis": wis_vec(y, qs)}


# ==========================================================================
# 6. Modelo
# ==========================================================================

def correr_modelo(serie, origenes, h, anio_min, cadencia, permutar_semilla=None,
                  refit_unico=False, diag_saturacion=False):
    qs, y, an = [], [], []
    modelos = []
    ultimo = -10 ** 9
    n_fallback = 0
    diag = []
    for o in origenes:
        necesita = (not modelos) or (not refit_unico and o - ultimo >= cadencia)
        if necesita and not (refit_unico and modelos):
            X, Y, idxtr = pares_entrenamiento(serie, o, h, anio_min, permutar_semilla)
            if len(Y) < 60:
                n_fallback += 1
                qs.append(np.full(N_Q, serie.casos[o]))
                y.append(serie.casos[o + h]); an.append(int(serie.anio[o + h]))
                continue
            modelos = []
            for q in QUANTILES:
                mdl = HistGradientBoostingRegressor(quantile=float(q), **HGBR_KW)
                mdl.fit(X, Y)
                modelos.append(mdl)
            ultimo = o
            max_ztr = float(Y.max())
        x = features(serie, o, h)
        if x is None:
            n_fallback += 1
            qs.append(np.full(N_Q, serie.casos[o]))
        else:
            qz = np.sort(np.array([m.predict(x.reshape(1, -1))[0] for m in modelos]))
            qs.append(np.clip(np.expm1(qz), 0, None))
            if diag_saturacion and int(serie.anio[o + h]) == 2019:
                diag.append({
                    "origen_fecha": str(serie.fecha[o]),
                    "objetivo_fecha": str(serie.fecha[o + h]),
                    "z_obj_real": float(serie.z[o + h]),
                    "q99_pred_log": float(qz[-1]),
                    "q50_pred_log": float(qz[IDX_MED]),
                    "max_z_entrenamiento": max_ztr,
                })
        y.append(serie.casos[o + h]); an.append(int(serie.anio[o + h]))
    nom = "modelo" + ("_mutado" if permutar_semilla else "")
    p = _pack(nom, qs, y, an)
    p["n_fallback"] = n_fallback
    if diag_saturacion:
        p["diag_saturacion_2019"] = diag
    return p


# ==========================================================================
# 7. Evaluacion
# ==========================================================================

def resumen(res: dict) -> dict:
    y, qs = res["y"], res["qs"]
    s = np.sort(qs, axis=1)
    d = {
        "nombre": res["nombre"],
        "n_pred": int(len(y)),
        "wis_medio_natural": float(res["wis"].mean()),
        "wis_medio_log": float(np.mean([wis_single(np.log1p(yi), np.log1p(np.sort(qi)))
                                        for yi, qi in zip(y, qs)])),
        "mae_mediana": float(np.mean(np.abs(y - s[:, IDX_MED]))),
        "cobertura_50": cobertura_emp(y, qs, 6, 16),
        "cobertura_95": cobertura_emp(y, qs, 1, 21),
        "wis_por_anio": {int(a): float(res["wis"][res["anio"] == a].mean())
                         for a in ANIOS_PRUEBA if (res["anio"] == a).any()},
    }
    if "n_fallback" in res:
        d["n_fallback"] = res["n_fallback"]
    return d


def skill_por_anio(mod, base):
    out = {}
    for a in ANIOS_PRUEBA:
        mm, bb = mod["anio"] == a, base["anio"] == a
        if mm.sum() == 0:
            continue
        wb = base["wis"][bb].mean()
        out[int(a)] = float(1.0 - mod["wis"][mm].mean() / wb) if wb > 0 else float("nan")
    return out


def evaluar(serie, origenes, h, anio_min, cadencia, hacer_mutacion=False,
            refit_unico=False, diag_saturacion=False, etiqueta=""):
    antifuga = verificar_anti_fuga(serie, origenes, h, anio_min)
    baselines = {
        "persistencia_rw": baseline_persistencia(serie, origenes, h, anio_min),
        "climatologia_estacional": baseline_climatologia(serie, origenes, h, anio_min),
        "persistencia_estacional": baseline_persistencia_estacional(serie, origenes, h, anio_min),
    }
    decisivo = min(baselines.values(), key=lambda b: b["wis"].mean())
    mod = correr_modelo(serie, origenes, h, anio_min, cadencia,
                        refit_unico=refit_unico, diag_saturacion=diag_saturacion)
    sk = skill_por_anio(mod, decisivo)
    skill_medio = float(np.mean(list(sk.values()))) if sk else float("nan")
    anios_ganados = sum(
        1 for a in ANIOS_PRUEBA
        if (mod["anio"] == a).any()
        and mod["wis"][mod["anio"] == a].mean() <= decisivo["wis"][decisivo["anio"] == a].mean()
    )
    rs, bl = resumen(mod), resumen(decisivo)
    gana_agrupado = (rs["wis_medio_natural"] <= bl["wis_medio_natural"]
                     and rs["wis_medio_log"] <= bl["wis_medio_log"])
    cumple_firmado = (skill_medio > 0 and anios_ganados >= CRIT_MIN_ANIOS
                      and CRIT_COB_95[0] <= rs["cobertura_95"] <= CRIT_COB_95[1]
                      and CRIT_COB_50[0] <= rs["cobertura_50"] <= CRIT_COB_50[1])
    veredicto = ("CUMPLE" if cumple_firmado and gana_agrupado
                 else "PARCIAL" if cumple_firmado else "NO CUMPLE")
    out = {
        "etiqueta": etiqueta, "alcance_anio_min": anio_min, "horizonte": h,
        "cadencia_reajuste": cadencia, "refit_unico": refit_unico,
        "n_origenes": len(origenes), "anti_fuga": antifuga,
        "comparador_decisivo": decisivo["nombre"],
        "baselines": {k: resumen(v) for k, v in baselines.items()},
        "modelo": rs,
        "skill_por_anio_vs_decisivo": sk,
        "skill_medio_por_anio": skill_medio,
        "anios_ganados_vs_decisivo": anios_ganados,
        "gana_wis_agrupado_nat_y_log": bool(gana_agrupado),
        "cumple_criterio_firmado": bool(cumple_firmado),
        "cumple_criterio_exito": bool(cumple_firmado and gana_agrupado),
        "veredicto": veredicto,
    }
    if diag_saturacion:
        out["diag_saturacion_2019"] = mod.get("diag_saturacion_2019", [])
    if hacer_mutacion:
        mut = correr_modelo(serie, origenes, h, anio_min, cadencia, permutar_semilla=12345)
        out["control_mutacion"] = {
            "wis_medio_natural": float(mut["wis"].mean()),
            "wis_modelo": float(mod["wis"].mean()),
            "empeora": bool(mut["wis"].mean() > mod["wis"].mean()),
        }
    print(f"  [{etiqueta}] alc {anio_min}+ h{h} cad{cadencia}"
          f"{' refit-unico' if refit_unico else ''}: "
          f"base({decisivo['nombre']})={bl['wis_medio_natural']:.1f} "
          f"modelo={rs['wis_medio_natural']:.1f} skill/anio={skill_medio:+.3f} "
          f"anios={anios_ganados}/5 cob50={rs['cobertura_50']:.2f} cob95={rs['cobertura_95']:.2f} "
          f"fb={rs.get('n_fallback','?')} => {veredicto}")
    return out


# ==========================================================================
# 8. Seleccion de origenes por esquema
# ==========================================================================

def origenes_rolling(serie, h, anio_min, anios_obj=ANIOS_PRUEBA):
    ori = []
    for o in range(serie.T - h):
        if serie.anio[o] == ANIO_EXCLUIDO or serie.anio[o] < anio_min:
            continue
        if serie.anio[o + h] not in anios_obj:
            continue
        if features(serie, o, h) is None:
            continue
        ori.append(o)
    return ori


def origenes_terminal(serie, h, anio_min):
    """Esquema A: objetivos en 2023-2024, origen >= anio_min, un solo entrenamiento
    con datos hasta fin de 2022."""
    ori = []
    for o in range(serie.T - h):
        if serie.anio[o] < anio_min or serie.anio[o] == ANIO_EXCLUIDO:
            continue
        if serie.anio[o + h] not in (2023, 2024):
            continue
        if features(serie, o, h) is None:
            continue
        ori.append(o)
    return ori


# ==========================================================================
# 9. Main
# ==========================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wis-test", action="store_true")
    ap.add_argument("--paridad", action="store_true")
    ap.add_argument("--esquema-a", action="store_true")
    ap.add_argument("--esquema-b", action="store_true")
    ap.add_argument("--esquema-c", action="store_true")
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("--horizontes", default="1,2,4,8")
    ap.add_argument("--alcances", default="2014,2016")
    ap.add_argument("--cadencias", default="1,2,4")
    args = ap.parse_args()

    SALIDA.mkdir(parents=True, exist_ok=True)
    horizontes = [int(x) for x in args.horizontes.split(",")]
    alcances = [int(x) for x in args.alcances.split(",")]
    cadencias = [int(x) for x in args.cadencias.split(",")]

    if args.wis_test or args.todo:
        print("== prueba unitaria del WIS ==")
        if not prueba_wis():
            raise SystemExit("prueba WIS fallo; abortando")
        if args.wis_test and not args.todo:
            return

    serie = cargar_serie()
    print(f"serie: T={serie.T}  {serie.fecha[0]}..{serie.fecha[-1]}  "
          f"casos max={serie.casos.max():.0f} (z={serie.z.max():.3f})")

    resultados = {}

    if args.paridad or args.todo:
        print("\n== PARIDAD (config original: cadencia 2) ==")
        res = []
        for alc in alcances:
            for h in horizontes:
                ori = origenes_rolling(serie, h, alc)
                res.append(evaluar(serie, ori, h, alc, cadencia=2,
                                   hacer_mutacion=(h == 4), diag_saturacion=(h == 4),
                                   etiqueta="paridad"))
        resultados["paridad"] = res
        (SALIDA / "paridad.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

    if args.esquema_a or args.todo:
        print("\n== ESQUEMA A (held-out terminal: entrena <=2022, sin reajuste, predice 2023-2024) ==")
        res = []
        for alc in alcances:
            for h in horizontes:
                ori = origenes_terminal(serie, h, alc)
                res.append(evaluar(serie, ori, h, alc, cadencia=10 ** 9, refit_unico=True,
                                   etiqueta="A"))
        resultados["A"] = res
        (SALIDA / "esquema_a.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

    if args.esquema_b or args.todo:
        print("\n== ESQUEMA B (rolling origin denso, cadencia 1, todos los anios de prueba) ==")
        res = []
        for alc in alcances:
            for h in horizontes:
                ori = origenes_rolling(serie, h, alc)
                res.append(evaluar(serie, ori, h, alc, cadencia=1,
                                   hacer_mutacion=(h == 4), diag_saturacion=(h == 4),
                                   etiqueta="B"))
        resultados["B"] = res
        (SALIDA / "esquema_b.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

    if args.esquema_c or args.todo:
        print("\n== ESQUEMA C (variar cadencia de reajuste) ==")
        res = []
        for alc in alcances:
            for cad in cadencias:
                ori = origenes_rolling(serie, 4, alc)
                res.append(evaluar(serie, ori, 4, alc, cadencia=cad, etiqueta=f"C-cad{cad}"))
        resultados["C"] = res
        (SALIDA / "esquema_c.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

    (SALIDA / "todo.json").write_text(json.dumps(resultados, indent=2, ensure_ascii=False))
    print(f"\nescrito -> {SALIDA}")


if __name__ == "__main__":
    main()
