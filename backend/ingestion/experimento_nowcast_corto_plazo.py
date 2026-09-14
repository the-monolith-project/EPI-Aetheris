"""
Experimento: proto-predictor de nowcast de horizonte corto.

Registro y ejecucion del experimento descrito en
docs/experimentos/experimento-nowcast-corto-plazo.md (parametros firmados por
Eduardo el 2026-09-08, opciones por defecto).

Pregunta unica: un nowcast probabilistico de la serie nacional semanal de casos
de dengue (OpenDengue, clasificacion 'total'), a horizonte corto, supera de forma
estable a los baselines de persistencia y climatologia estacional, con scoring
propio (WIS) y protocolo forward-chaining sin fuga temporal?

Es un diagnostico exploratorio. NO escribe a Postgres (solo lectura), NO toca
FastAPI ni el frontend, NO modifica el esquema, NO usa M1-M4 ni la etiqueta
alto/medio/bajo. Solo lee las tablas ya cargadas.

Reglas de datos (firmadas):

  - Serie objetivo: casos_epidemiologicos, clasificacion='total',
    fuente 'opendengue_v1_3', region 'SV'. Disponible 2014-2024 (la carga ya
    incluye 2014+, la decision 1 no requirio accion: ver seccion Resultados del
    doc).
  - 2020 (D1, docs/rescate-prediccion/...): EXCLUIDO como anio objetivo y como
    anio de origen de prueba; EXCLUIDO del pool de la climatologia; se conserva
    unicamente como insumo de rezagos autorregresivos para semanas vecinas.
  - Sensibilidad de alcance: el experimento corre completo en DOS ventanas de
    historia -- desde 2014 y desde 2016 -- porque 2014-2015 estan ~2x por encima
    del nivel de 2016+ en la serie 'total' de OpenDengue (posible cambio de base
    de reporte; el loader solo se verifico contra MINSAL para 2018 y 2022). Se
    reportan ambas. No se elige una en silencio.

Modelo (desviacion firmada respecto al doc): el doc proponia LightGBM; se usa
sklearn HistGradientBoostingRegressor(loss='quantile') para no agregar una
dependencia nueva y respetar la restriccion de "arboles ligeros / hardware
modesto" del proyecto. Es la misma familia (quantile gradient boosting).

Uso:

    python3 experimento_nowcast_corto_plazo.py --solo-baselines
    python3 experimento_nowcast_corto_plazo.py --modelo --horizonte 4
    python3 experimento_nowcast_corto_plazo.py --modelo --horizonte 1,2,8
    python3 experimento_nowcast_corto_plazo.py --control-mutacion
    python3 experimento_nowcast_corto_plazo.py --todo          # todo lo anterior

Salida: JSON por (alcance, horizonte) en backend/ingestion/data/interim/nowcast/
y un resumen por stdout. El doc se actualiza a mano con los numeros.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

try:
    from sklearn.ensemble import HistGradientBoostingRegressor
except Exception as exc:  # pragma: no cover
    print(f"ERROR: sklearn no disponible: {exc}", file=sys.stderr)
    raise SystemExit(1)

from db import get_connection

RAIZ_INGESTION = Path(__file__).parent
SALIDA_DIR = RAIZ_INGESTION / "data" / "interim" / "nowcast"

# --- parametros firmados -----------------------------------------------------

ANIOS_PRUEBA = (2019, 2021, 2022, 2023, 2024)  # 2020 excluido (D1)
ANIO_EXCLUIDO = 2020
ALCANCES = (2014, 2016)  # anio minimo de historia; se corre en ambos
HORIZONTE_DECISIVO = 4
CADENCIA_REAJUSTE = 2  # el modelo se reajusta cada N semanas (ventana expansiva)

# conjunto estandar de 23 cuantiles usado por los hubs de forecasting (CDC/OPS)
CUANTILES = np.array(
    [0.01, 0.025, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50,
     0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.975, 0.99]
)
IDX_MEDIANA = 11
# pares de intervalos centrales -> alpha = 2 * cuantil_inferior
PARES_INTERVALO = [(i, 22 - i) for i in range(11)]  # (0.01,0.99) ... (0.45,0.55)

VARIABLES_CLIMA = (
    "temp_media", "temp_max", "temp_min",
    "precipitation_sum", "precipitation_hours",
    "humedad_relativa_media", "punto_rocio",
)

# hiperparametros fijos (declarados; no se barren contra los folds de prueba)
HGBR_KW = dict(
    loss="quantile",
    max_iter=150,
    max_leaf_nodes=7,
    min_samples_leaf=20,
    l2_regularization=1.0,
    learning_rate=0.05,
    early_stopping=False,
    random_state=0,
)

# criterio de exito predeclarado (firmado, con el ajuste 3->4 de N=5 anios)
CRIT_COBERTURA_95 = (0.85, 0.99)
CRIT_COBERTURA_50 = (0.35, 0.65)
CRIT_MIN_ANIOS_GANADOS = 4  # de 5


# --- carga de datos --------------------------------------------------------


@dataclass
class Serie:
    """Serie nacional semanal, ordenada por fecha_inicio (indice contiguo)."""

    fecha: np.ndarray          # date[], longitud T
    anio: np.ndarray           # int[]
    semana: np.ndarray         # int[]
    doy: np.ndarray            # int[], dia del anio de fecha_inicio
    casos: np.ndarray          # float[], conteo 'total'
    z: np.ndarray              # float[], log1p(casos)
    clima: dict[str, np.ndarray]  # variable -> float[] (media nacional 14 deptos)
    oni: np.ndarray            # float[]

    @property
    def T(self) -> int:
        return len(self.fecha)


def cargar_serie(conn) -> Serie:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.fecha_inicio, c.anio, c.semana_epi, c.conteo
        FROM casos_epidemiologicos c
        JOIN regiones r        ON r.id = c.region_id
        JOIN fuentes_datos f   ON f.id = c.fuente_id
        JOIN semanas_epidemiologicas s
          ON s.anio = c.anio AND s.semana_epi = c.semana_epi
        WHERE r.codigo = 'SV'
          AND c.clasificacion = 'total'
          AND f.codigo = 'opendengue_v1_3'
        ORDER BY s.fecha_inicio
        """
    )
    filas = cur.fetchall()
    if not filas:
        raise SystemExit("ERROR: serie OpenDengue nacional 'total' vacia.")

    fecha = np.array([f[0] for f in filas], dtype=object)
    anio = np.array([f[1] for f in filas], dtype=int)
    semana = np.array([f[2] for f in filas], dtype=int)
    casos = np.array([float(f[3]) for f in filas], dtype=float)
    doy = np.array([d.timetuple().tm_yday for d in fecha], dtype=int)

    # continuidad: sin huecos de mas de 7 dias entre semanas consecutivas
    saltos = [(fecha[i] - fecha[i - 1]).days for i in range(1, len(fecha))]
    if any(s > 8 or s < 6 for s in saltos):
        raros = [(str(fecha[i]), saltos[i - 1]) for i in range(1, len(fecha))
                 if saltos[i - 1] > 8 or saltos[i - 1] < 6]
        raise SystemExit(f"ERROR: serie no contigua semana a semana: {raros[:10]}")

    # clima nacional = media simple sobre los 14 departamentos (nivel_admin=1)
    clima: dict[str, np.ndarray] = {}
    idx = {(int(a), int(w)): k for k, (a, w) in enumerate(zip(anio, semana))}
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
    # ONI es mensual interpolado -> rellenar huecos por arrastre hacia adelante
    for k in range(1, len(oni)):
        if np.isnan(oni[k]):
            oni[k] = oni[k - 1]

    z = np.log1p(casos)
    return Serie(fecha, anio, semana, doy, casos, z, clima, oni)


# --- WIS -------------------------------------------------------------------


def wis(y: float, q_pred: np.ndarray) -> float:
    """Weighted Interval Score de una prediccion (23 cuantiles) contra y.

    Formula estandar (Bracher et al. 2021):
      WIS = 1/(K+1/2) * ( 1/2 |y - m| + sum_k alpha_k/2 * IS_{alpha_k} )
      IS_alpha(l,u,y) = (u-l) + 2/alpha (l-y) 1{y<l} + 2/alpha (y-u) 1{y>u}
    """
    q_pred = np.sort(q_pred)  # correccion de cruce de cuantiles (post-hoc)
    m = q_pred[IDX_MEDIANA]
    total = 0.5 * abs(y - m)
    K = len(PARES_INTERVALO)
    for lo, hi in PARES_INTERVALO:
        alpha = 2 * CUANTILES[lo]
        l, u = q_pred[lo], q_pred[hi]
        isc = (u - l)
        if y < l:
            isc += 2.0 / alpha * (l - y)
        if y > u:
            isc += 2.0 / alpha * (y - u)
        total += (alpha / 2.0) * isc
    return total / (K + 0.5)


def cobertura(y: np.ndarray, qs: np.ndarray, lo_idx: int, hi_idx: int) -> float:
    lo = np.sort(qs, axis=1)[:, lo_idx]
    hi = np.sort(qs, axis=1)[:, hi_idx]
    return float(np.mean((y >= lo) & (y <= hi)))


# --- construccion de features --------------------------------------------


N_LAGS = 8


def features_en(serie: Serie, t: int, h: int) -> np.ndarray | None:
    """Vector de features conocido en el origen t para predecir t+h.

    Devuelve None si no hay historia suficiente (t < N_LAGS) o si algun
    insumo climatico del origen es NaN.
    """
    if t < N_LAGS:
        return None
    z = serie.z
    lags = z[t - N_LAGS + 1: t + 1][::-1]  # z[t], z[t-1], ..., z[t-7]
    media4 = z[t - 3: t + 1].mean()
    media8 = z[t - 7: t + 1].mean()
    momentum = z[t] - z[t - 4]

    # estacionalidad de la SEMANA OBJETIVO (t+h): determinista, conocida en t
    doy_obj = serie.doy[t + h] if (t + h) < serie.T else serie.doy[t]
    harm = []
    for k in (1, 2, 3):
        ang = 2 * np.pi * k * doy_obj / 365.25
        harm += [np.sin(ang), np.cos(ang)]

    clima_feat = []
    for var in VARIABLES_CLIMA:
        col = serie.clima[var]
        v = col[t - 3: t + 1]
        if np.any(np.isnan(v)):
            return None
        clima_feat.append(float(v.mean()))

    oni_t = serie.oni[t]
    if np.isnan(oni_t):
        oni_t = 0.0

    anio_obj = serie.anio[t + h] if (t + h) < serie.T else serie.anio[t]

    return np.concatenate([
        lags,
        [media4, media8, momentum],
        harm,
        clima_feat,
        [oni_t, float(anio_obj)],
    ])


# --- pares de entrenamiento (forward-chaining, sin fuga) -----------------


def pares_entrenamiento(serie: Serie, origen: int, h: int, anio_min: int,
                        mezclar_semilla: int | None = None,
                        permitir_fuga: bool = False):
    """Todos los (X, y) con fecha(objetivo) ESTRICTAMENTE anterior a fecha(origen).

    Excluye pares cuyo objetivo cae en 2020 (D1) o antes de anio_min.
    2020 se conserva solo como insumo de rezagos (no como etiqueta).

    Devuelve (X, Y, idx_objetivo). `idx_objetivo` permite verificar la
    condicion anti-fuga de forma INDEPENDIENTE del filtro (no como tautologia).
    `permitir_fuga=True` desactiva el filtro temporal -- solo para el control
    negativo que prueba que la asercion realmente muerde.
    """
    f_corte = serie.fecha[origen]
    X, Y, idx = [], [], []
    for t in range(serie.T):
        tgt = t + h
        if tgt >= serie.T:
            break
        if not permitir_fuga and serie.fecha[tgt] >= f_corte:
            continue  # <-- garantia dura anti-fuga
        if serie.anio[tgt] == ANIO_EXCLUIDO:
            continue
        if serie.anio[tgt] < anio_min:
            continue
        x = features_en(serie, t, h)
        if x is None:
            continue
        X.append(x)
        Y.append(serie.z[tgt])
        idx.append(tgt)
    X = np.array(X)
    Y = np.array(Y)
    idx = np.array(idx, dtype=int)
    if mezclar_semilla is not None and len(Y) > 0:
        rng = np.random.default_rng(mezclar_semilla)
        Y = Y[rng.permutation(len(Y))]  # control de mutacion
    return X, Y, idx


# --- baselines ----------------------------------------------------------


def baseline_persistencia(serie: Serie, origenes: list[int], h: int,
                          anio_min: int) -> dict:
    """RW en log: z_hat(t+h) = z(t); incertidumbre = cuantiles empiricos de
    los residuos de h pasos d = z(t'+h) - z(t') sobre t' con objetivo anterior
    al origen (expansivo). Devuelto en escala de conteo."""
    res = {"nombre": "persistencia_rw", "qs": [], "y": [], "anio": []}
    for o in origenes:
        f_corte = serie.fecha[o]
        d = [serie.z[t + h] - serie.z[t] for t in range(serie.T - h)
             if serie.fecha[t + h] < f_corte
             and serie.anio[t + h] != ANIO_EXCLUIDO
             and serie.anio[t + h] >= anio_min]
        d = np.array(d)
        centro = serie.z[o]
        qz = centro + np.quantile(d, CUANTILES)
        res["qs"].append(np.clip(np.expm1(qz), 0, None))
        res["y"].append(serie.casos[o + h])
        res["anio"].append(int(serie.anio[o + h]))
    return _empaquetar(res)


def _pool_climatologico(serie: Serie, anio_obj: int, semana_obj: int,
                        anio_min: int) -> np.ndarray:
    """Conteos de la MISMA semana epi en anios estrictamente anteriores a
    anio_obj, dentro del alcance, excluyendo 2020 (D1). Ventana +-1 semana."""
    vals = []
    for t in range(serie.T):
        a = serie.anio[t]
        if a >= anio_obj or a < anio_min or a == ANIO_EXCLUIDO:
            continue
        if abs(int(serie.semana[t]) - semana_obj) <= 1:
            vals.append(serie.casos[t])
    return np.array(vals)


def baseline_climatologia(serie: Serie, origenes: list[int], h: int,
                          anio_min: int) -> dict:
    res = {"nombre": "climatologia_estacional", "qs": [], "y": [], "anio": []}
    for o in origenes:
        tgt = o + h
        pool = _pool_climatologico(serie, int(serie.anio[tgt]),
                                   int(serie.semana[tgt]), anio_min)
        if len(pool) < 3:
            q = np.full(len(CUANTILES), serie.casos[o])  # respaldo: persistencia
        else:
            q = np.quantile(pool, CUANTILES)
        res["qs"].append(np.clip(q, 0, None))
        res["y"].append(serie.casos[tgt])
        res["anio"].append(int(serie.anio[tgt]))
    return _empaquetar(res)


def baseline_persistencia_estacional(serie: Serie, origenes: list[int], h: int,
                                     anio_min: int) -> dict:
    """z_hat(t+h) = z(t) + [mediana_log_clim(sem t+h) - mediana_log_clim(sem t)],
    incertidumbre por los mismos residuos de h pasos que la RW."""
    res = {"nombre": "persistencia_estacional", "qs": [], "y": [], "anio": []}
    for o in origenes:
        f_corte = serie.fecha[o]
        d = np.array([serie.z[t + h] - serie.z[t] for t in range(serie.T - h)
                      if serie.fecha[t + h] < f_corte
                      and serie.anio[t + h] != ANIO_EXCLUIDO
                      and serie.anio[t + h] >= anio_min])
        tgt = o + h
        pool_o = _pool_climatologico(serie, int(serie.anio[o]),
                                     int(serie.semana[o]), anio_min)
        pool_t = _pool_climatologico(serie, int(serie.anio[tgt]),
                                     int(serie.semana[tgt]), anio_min)
        if len(pool_o) >= 3 and len(pool_t) >= 3:
            ajuste = np.log1p(np.median(pool_t)) - np.log1p(np.median(pool_o))
        else:
            ajuste = 0.0
        centro = serie.z[o] + ajuste
        qz = centro + np.quantile(d - np.median(d), CUANTILES)
        res["qs"].append(np.clip(np.expm1(qz), 0, None))
        res["y"].append(serie.casos[tgt])
        res["anio"].append(int(serie.anio[tgt]))
    return _empaquetar(res)


def _empaquetar(res: dict) -> dict:
    res["qs"] = np.array(res["qs"])
    res["y"] = np.array(res["y"], dtype=float)
    res["anio"] = np.array(res["anio"], dtype=int)
    res["wis_por_pred"] = np.array([wis(y, q) for y, q in zip(res["y"], res["qs"])])
    return res


# --- modelo -----------------------------------------------------------


def correr_modelo(serie: Serie, origenes: list[int], h: int, anio_min: int,
                  mezclar_semilla: int | None = None) -> dict:
    res = {
        "nombre": "modelo_hgbr_quantile" + ("_mutado" if mezclar_semilla else ""),
        "qs": [], "y": [], "anio": [],
    }
    modelos: list[HistGradientBoostingRegressor] = []
    ultimo_reajuste = -10_000
    for o in origenes:
        if o - ultimo_reajuste >= CADENCIA_REAJUSTE or not modelos:
            X, Y, _ = pares_entrenamiento(serie, o, h, anio_min, mezclar_semilla)
            if len(Y) < 60:
                res["qs"].append(np.full(len(CUANTILES), serie.casos[o]))
                res["y"].append(serie.casos[o + h])
                res["anio"].append(int(serie.anio[o + h]))
                continue
            modelos = []
            for q in CUANTILES:
                m = HistGradientBoostingRegressor(quantile=float(q), **HGBR_KW)
                m.fit(X, Y)
                modelos.append(m)
            ultimo_reajuste = o
        x = features_en(serie, o, h)
        if x is None:
            res["qs"].append(np.full(len(CUANTILES), serie.casos[o]))
        else:
            xz = x.reshape(1, -1)
            qz = np.array([m.predict(xz)[0] for m in modelos])
            res["qs"].append(np.clip(np.expm1(np.sort(qz)), 0, None))
        res["y"].append(serie.casos[o + h])
        res["anio"].append(int(serie.anio[o + h]))
    return _empaquetar(res)


# --- evaluacion -------------------------------------------------------


def skill_por_anio(modelo: dict, baseline: dict) -> dict[int, float]:
    out = {}
    for a in ANIOS_PRUEBA:
        mm = modelo["anio"] == a
        bb = baseline["anio"] == a
        if mm.sum() == 0:
            continue
        wm = modelo["wis_por_pred"][mm].mean()
        wb = baseline["wis_por_pred"][bb].mean()
        out[a] = 1.0 - wm / wb if wb > 0 else float("nan")
    return out


def wis_log(res: dict) -> float:
    """WIS en escala log1p (secundario): re-evalua con y y cuantiles en log."""
    vals = []
    for y, q in zip(res["y"], res["qs"]):
        vals.append(wis(np.log1p(y), np.log1p(np.sort(q))))
    return float(np.mean(vals))


def resumen_resultado(res: dict) -> dict:
    y, qs = res["y"], res["qs"]
    return {
        "nombre": res["nombre"],
        "n_pred": int(len(y)),
        "wis_medio_natural": float(res["wis_por_pred"].mean()),
        "wis_medio_log": wis_log(res),
        "mae_mediana": float(np.mean(np.abs(y - np.sort(qs, axis=1)[:, IDX_MEDIANA]))),
        "cobertura_50": cobertura(y, qs, 6, 16),
        "cobertura_95": cobertura(y, qs, 1, 21),
        "wis_por_anio": {int(a): float(res["wis_por_pred"][res["anio"] == a].mean())
                         for a in ANIOS_PRUEBA if (res["anio"] == a).any()},
    }


# --- orquestacion ----------------------------------------------------


def origenes_de_prueba(serie: Serie, h: int, anio_min: int) -> list[int]:
    ori = []
    for o in range(serie.T - h):
        if serie.anio[o] == ANIO_EXCLUIDO or serie.anio[o] < anio_min:
            continue
        tgt = o + h
        if serie.anio[tgt] not in ANIOS_PRUEBA:
            continue
        if features_en(serie, o, h) is None:
            continue
        ori.append(o)
    return ori


def verificar_sin_fuga(serie: Serie, origenes: list[int], h: int,
                       anio_min: int) -> None:
    """Garantia dura, verificada de forma INDEPENDIENTE del filtro.

    Para una muestra de origenes: toma los indices de objetivo que
    `pares_entrenamiento` realmente devolvio y comprueba que TODOS tienen
    fecha estrictamente anterior a la del origen. Luego un control negativo:
    con el filtro desactivado (`permitir_fuga=True`), la misma comprobacion
    DEBE fallar -- si no falla, la asercion no vale nada.
    """
    muestreados = origenes[:: max(1, len(origenes) // 12)]
    for o in muestreados:
        _, _, tgts = pares_entrenamiento(serie, o, h, anio_min)
        assert len(tgts) > 0, f"origen {o}: sin pares de entrenamiento"
        f_corte = serie.fecha[o]
        peor = max(serie.fecha[k] for k in tgts)
        assert peor < f_corte, f"FUGA en origen {o}: objetivo {peor} >= corte {f_corte}"

    # control negativo: sin filtro, la comprobacion tiene que romperse
    fallo_esperado = False
    for o in muestreados:
        _, _, tgts = pares_entrenamiento(serie, o, h, anio_min, permitir_fuga=True)
        f_corte = serie.fecha[o]
        if any(serie.fecha[k] >= f_corte for k in tgts):
            fallo_esperado = True
            break
    assert fallo_esperado, "control negativo no rompio: la verificacion no discrimina"

    print(f"  [ok] garantia anti-fuga: {len(muestreados)} origenes, "
          f"todos los objetivos de entrenamiento anteriores al corte; "
          f"control negativo rompe como se espera")


def correr(alcance: int, h: int, hacer_modelo: bool, hacer_mutacion: bool) -> dict:
    conn = get_connection()
    try:
        serie = cargar_serie(conn)
    finally:
        conn.close()

    origenes = origenes_de_prueba(serie, h, alcance)
    print(f"\n=== alcance {alcance}+ | horizonte {h} sem | {len(origenes)} origenes de prueba ===")
    verificar_sin_fuga(serie, origenes, h, alcance)

    baselines = {
        "persistencia_rw": baseline_persistencia(serie, origenes, h, alcance),
        "climatologia_estacional": baseline_climatologia(serie, origenes, h, alcance),
        "persistencia_estacional": baseline_persistencia_estacional(serie, origenes, h, alcance),
    }
    for b in baselines.values():
        print(f"  baseline {b['nombre']:26s} WIS_nat={b['wis_por_pred'].mean():10.1f}")

    # comparador decisivo = baseline mas fuerte por WIS natural agrupado
    decisivo = min(baselines.values(), key=lambda b: b["wis_por_pred"].mean())
    print(f"  -> comparador decisivo: {decisivo['nombre']}")

    salida = {
        "alcance_anio_min": alcance,
        "horizonte": h,
        "n_origenes": len(origenes),
        "anios_prueba": list(ANIOS_PRUEBA),
        "comparador_decisivo": decisivo["nombre"],
        "baselines": {k: resumen_resultado(v) for k, v in baselines.items()},
        "cadencia_reajuste_semanas": CADENCIA_REAJUSTE,
        "hgbr_kw": {k: v for k, v in HGBR_KW.items()},
    }

    if hacer_modelo:
        mod = correr_modelo(serie, origenes, h, alcance)
        salida["modelo"] = resumen_resultado(mod)
        sk = skill_por_anio(mod, decisivo)
        salida["skill_por_anio_vs_decisivo"] = {int(a): float(v) for a, v in sk.items()}
        skill_medio = float(np.mean(list(sk.values())))
        anios_ganados = sum(
            1 for a in ANIOS_PRUEBA
            if (mod["anio"] == a).any()
            and mod["wis_por_pred"][mod["anio"] == a].mean()
            <= decisivo["wis_por_pred"][decisivo["anio"] == a].mean()
        )
        rs = salida["modelo"]
        bl = salida["baselines"][decisivo["nombre"]]
        gana_wis_agrupado = (
            rs["wis_medio_natural"] <= bl["wis_medio_natural"]
            and rs["wis_medio_log"] <= bl["wis_medio_log"]
        )
        cumple_firmado = (
            skill_medio > 0
            and anios_ganados >= CRIT_MIN_ANIOS_GANADOS
            and CRIT_COBERTURA_95[0] <= rs["cobertura_95"] <= CRIT_COBERTURA_95[1]
            and CRIT_COBERTURA_50[0] <= rs["cobertura_50"] <= CRIT_COBERTURA_50[1]
        )
        salida["skill_medio_por_anio_vs_decisivo"] = skill_medio
        salida["anios_ganados_vs_decisivo"] = anios_ganados
        salida["cumple_criterio_firmado"] = bool(cumple_firmado)
        salida["gana_wis_agrupado_nat_y_log"] = bool(gana_wis_agrupado)
        # veredicto reportado: cumple firmado Y no queda peor en WIS agrupado
        salida["cumple_criterio_exito"] = bool(cumple_firmado and gana_wis_agrupado)
        veredicto = ("CUMPLE" if (cumple_firmado and gana_wis_agrupado)
                     else "PARCIAL" if cumple_firmado else "NO CUMPLE")
        print(f"  modelo WIS_nat={rs['wis_medio_natural']:.1f}  "
              f"skill medio/anio={skill_medio:+.3f}  anios ganados={anios_ganados}/5  "
              f"cob50={rs['cobertura_50']:.2f} cob95={rs['cobertura_95']:.2f}  "
              f"wis_agrupado_gana={gana_wis_agrupado}  => {veredicto}")

        if hacer_mutacion and h == HORIZONTE_DECISIVO:
            mut = correr_modelo(serie, origenes, h, alcance, mezclar_semilla=12345)
            salida["control_mutacion"] = resumen_resultado(mut)
            peor = mut["wis_por_pred"].mean() > mod["wis_por_pred"].mean()
            salida["control_mutacion"]["empeora_vs_modelo"] = bool(peor)
            print(f"  control mutacion (etiquetas permutadas): "
                  f"WIS_nat={mut['wis_por_pred'].mean():.1f} "
                  f"({'empeora, ok' if peor else 'NO empeora -- revisar'})")

    return salida


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--solo-baselines", action="store_true")
    p.add_argument("--modelo", action="store_true")
    p.add_argument("--control-mutacion", action="store_true")
    p.add_argument("--todo", action="store_true")
    p.add_argument("--horizonte", default=str(HORIZONTE_DECISIVO),
                   help="coma-separado, ej. '4' o '1,2,8'")
    p.add_argument("--alcance", default=",".join(str(a) for a in ALCANCES))
    args = p.parse_args()

    hacer_modelo = args.modelo or args.todo
    hacer_mutacion = args.control_mutacion or args.todo
    if not (hacer_modelo or args.solo_baselines or args.todo):
        args.solo_baselines = True

    horizontes = [int(x) for x in args.horizonte.split(",")]
    alcances = [int(x) for x in args.alcance.split(",")]

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    todo_salida = []
    for alcance in alcances:
        for h in horizontes:
            s = correr(alcance, h, hacer_modelo, hacer_mutacion)
            f = SALIDA_DIR / f"resultado_alcance{alcance}_h{h}.json"
            f.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  escrito {f}")
            todo_salida.append(s)

    resumen = SALIDA_DIR / "resumen.json"
    resumen.write_text(json.dumps(todo_salida, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResumen -> {resumen}")


if __name__ == "__main__":
    main()
