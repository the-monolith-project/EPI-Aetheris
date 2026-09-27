"""
Experimento: la prediccion de dengue a corto plazo (ADR 0020) con la serie
extendida por el tablero de MINSAL (ADR 0021).

Serie: OpenDengue 'total' hasta la ultima semana de 2024 y, a continuacion,
los sospechosos de dengue del tablero (2025 y 2026). La semana 53 de 2025 no
esta publicada: queda como hueco (NaN), no se rellena. Un origen cuyos
rezagos tocan el hueco no tiene prediccion, y un par cuyo objetivo es el
hueco no entra al entrenamiento.

Metodo: el publicado, sin cambios (HGB por cuantiles, calibracion CQR-r con
los 52 pares mas recientes, reajuste cada 2 semanas, 2020 excluido como
objetivo). Se evalua con forward-chaining sobre los objetivos de 2024, 2025
y 2026: cada prediccion usa solo datos con fecha anterior a su origen.
2024 sirve de control: debe reproducir, salvo ruido, el resultado publicado.

La referencia de cada horizonte es la mas fuerte de las tres del experimento
original sobre estos mismos origenes (misma regla que el ADR 0020).

Uso:
    cd backend/ingestion
    POSTGRES_HOST=localhost ../.venv/bin/python experimento_nowcast_tablero.py
    # comparar variantes de calibracion de los rangos:
    POSTGRES_HOST=localhost ../.venv/bin/python experimento_nowcast_tablero.py --calibracion
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from math import ceil
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

import experimento_nowcast_corto_plazo as exp
import nowcast_retrospectivo_dengue as retro
from experimento_nowcast_calibracion import ALPHAS, MIN_CAL, MIN_PROPER, _fit_q
from experimento_nowcast_corto_plazo import (
    ANIO_EXCLUIDO,
    CADENCIA_REAJUSTE,
    CUANTILES,
    IDX_MEDIANA,
    PARES_INTERVALO,
    VARIABLES_CLIMA,
    Serie,
    cobertura,
    wis,
)
from nowcast_estimacion_dengue import (
    ALCANCE_HISTORIA,
    HORIZONTES,
    IDX_B50,
    IDX_B95,
    N_CAL,
    _qs_calibrado_cqr_r,
)

from db import get_connection

ANIOS_EVAL = (2024, 2025, 2026)
SALIDA = Path(__file__).parent / "data" / "interim" / "nowcast" / "experimento_tablero.json"


# --- serie mixta ---------------------------------------------------------


def cargar_serie_mixta(conn) -> Serie:
    """Calendario completo con OpenDengue hasta 2024 y el tablero desde 2025.

    Las semanas sin dato (la 53 de 2025) quedan como NaN."""
    cur = conn.cursor()
    cur.execute(
        """
        WITH casos AS (
            SELECT c.anio, c.semana_epi, c.conteo
            FROM casos_epidemiologicos c
            JOIN regiones r ON r.id = c.region_id
            JOIN fuentes_datos f ON f.id = c.fuente_id
            WHERE r.codigo = 'SV'
              AND ((f.codigo = 'opendengue_v1_3' AND c.clasificacion = 'total' AND c.anio <= 2024)
                OR (f.codigo = 'minsal_tablero' AND c.clasificacion = 'sospechoso' AND c.anio >= 2025))
        ),
        limites AS (
            SELECT min(s.fecha_inicio) AS desde, max(s.fecha_inicio) AS hasta
            FROM casos k JOIN semanas_epidemiologicas s USING (anio, semana_epi)
        )
        SELECT s.fecha_inicio, s.anio, s.semana_epi, k.conteo
        FROM semanas_epidemiologicas s
        CROSS JOIN limites l
        LEFT JOIN casos k ON k.anio = s.anio AND k.semana_epi = s.semana_epi
        WHERE s.fecha_inicio BETWEEN l.desde AND l.hasta
        ORDER BY s.fecha_inicio
        """
    )
    filas = cur.fetchall()
    fecha = np.array([f[0] for f in filas], dtype=object)
    anio = np.array([f[1] for f in filas], dtype=int)
    semana = np.array([f[2] for f in filas], dtype=int)
    casos = np.array([np.nan if f[3] is None else float(f[3]) for f in filas])
    doy = np.array([d.timetuple().tm_yday for d in fecha], dtype=int)
    saltos = {(fecha[i] - fecha[i - 1]).days for i in range(1, len(fecha))}
    assert saltos == {7}, f"calendario no contiguo: {saltos}"

    idx = {(int(a), int(w)): k for k, (a, w) in enumerate(zip(anio, semana))}
    clima: dict[str, np.ndarray] = {}
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
    for k in range(1, len(oni)):  # mismo arrastre que cargar_serie
        if np.isnan(oni[k]):
            oni[k] = oni[k - 1]

    return Serie(fecha, anio, semana, doy, casos, np.log1p(casos), clima, oni)


def ceros_como_hueco(serie: Serie) -> list[str]:
    """Pasa a NaN las semanas de OpenDengue con 0 casos.

    Son semanas en que MINSAL no notifico casos (Semana Santa, fiestas
    agostinas, fin de anio) y la semana siguiente trae aproximadamente el
    doble: 213, 0, 437 en 2016; 172, 0, 281 en 2023. Tratarlas como hueco es
    una eleccion de modelado para medir cuanto pesan en la evaluacion, no una
    correccion del dato; la base las conserva tal como las publica la fuente."""
    ks = np.flatnonzero((serie.anio <= 2024) & (serie.casos == 0))
    serie.casos[ks] = np.nan
    serie.z[ks] = np.nan
    return [str(serie.fecha[k]) for k in ks]


# --- el metodo publicado, con el hueco tratado como ausencia -------------

_features_original = exp.features_en
_pares_original = exp.pares_entrenamiento


def features_sin_hueco(serie: Serie, t: int, h: int):
    if t >= exp.N_LAGS - 1 and np.isnan(serie.z[t - exp.N_LAGS + 1: t + 1]).any():
        return None
    return _features_original(serie, t, h)


def pares_sin_hueco(serie: Serie, origen: int, h: int, anio_min: int, *a, **kw):
    X, Y, idx = _pares_original(serie, origen, h, anio_min, *a, **kw)
    ok = ~np.isnan(Y)
    return X[ok], Y[ok], idx[ok]


def _instalar_parches() -> None:
    # pares_entrenamiento busca features_en en su modulo al llamarla; la
    # cadena de nowcast_retrospectivo_dengue los importo por nombre
    exp.features_en = features_sin_hueco
    retro.features_en = features_sin_hueco
    retro.pares_entrenamiento = pares_sin_hueco


# --- referencias, iguales a las del experimento pero sin contar NaN ------


def _residuos(serie: Serie, o: int, h: int) -> np.ndarray:
    f_corte = serie.fecha[o]
    d = [serie.z[t + h] - serie.z[t] for t in range(serie.T - h)
         if serie.fecha[t + h] < f_corte
         and serie.anio[t + h] != ANIO_EXCLUIDO
         and serie.anio[t + h] >= ALCANCE_HISTORIA]
    d = np.array(d)
    return d[np.isfinite(d)]


def _pool(serie: Serie, anio_obj: int, semana_obj: int) -> np.ndarray:
    m = ((serie.anio < anio_obj) & (serie.anio >= ALCANCE_HISTORIA) & (serie.anio != ANIO_EXCLUIDO)
         & (np.abs(serie.semana - semana_obj) <= 1) & np.isfinite(serie.casos))
    return serie.casos[m]


def referencia(nombre: str, serie: Serie, o: int, h: int) -> np.ndarray:
    tgt = o + h
    if nombre == "persistencia_rw":
        return np.clip(np.expm1(serie.z[o] + np.quantile(_residuos(serie, o, h), CUANTILES)), 0, None)
    if nombre == "climatologia_estacional":
        pool = _pool(serie, int(serie.anio[tgt]), int(serie.semana[tgt]))
        if len(pool) < 3:
            return np.full(len(CUANTILES), serie.casos[o])
        return np.clip(np.quantile(pool, CUANTILES), 0, None)
    # persistencia_estacional
    d = _residuos(serie, o, h)
    p_o = _pool(serie, int(serie.anio[o]), int(serie.semana[o]))
    p_t = _pool(serie, int(serie.anio[tgt]), int(serie.semana[tgt]))
    ajuste = np.log1p(np.median(p_t)) - np.log1p(np.median(p_o)) if len(p_o) >= 3 and len(p_t) >= 3 else 0.0
    return np.clip(np.expm1(serie.z[o] + ajuste + np.quantile(d - np.median(d), CUANTILES)), 0, None)


REFERENCIAS = ("persistencia_rw", "climatologia_estacional", "persistencia_estacional")


# --- corrida ---------------------------------------------------------------


def origenes_eval(serie: Serie, h: int) -> list[int]:
    return [
        o for o in range(serie.T - h)
        if serie.anio[o + h] in ANIOS_EVAL
        and np.isfinite(serie.casos[o + h])
        and features_sin_hueco(serie, o, h) is not None
    ]


def _horizonte(args: tuple[Serie, int]) -> dict:
    serie, h = args
    threadpool_limits(retro.HILOS_POR_PROCESO)
    _instalar_parches()
    origenes = origenes_eval(serie, h)
    q = retro._cadena(serie, serie.T, origenes, h)
    filas = []
    for o in origenes:
        if q[o] is None:
            continue
        y = float(serie.casos[o + h])
        fila = {
            "origen": str(serie.fecha[o]),
            "anio_obj": int(serie.anio[o + h]),
            "semana_obj": int(serie.semana[o + h]),
            "y": y,
            "q": q[o].tolist(),
            "wis_modelo": wis(y, q[o]),
        }
        for nombre in REFERENCIAS:
            fila[f"wis_{nombre}"] = wis(y, referencia(nombre, serie, o, h))
        filas.append(fila)
    return {"h": h, "filas": filas, "sin_prediccion": len(origenes) - len(filas)}


def resumir(res: dict) -> dict:
    filas = res["filas"]
    decisivo = min(REFERENCIAS, key=lambda n: np.mean([f[f"wis_{n}"] for f in filas]))
    out = {"decisivo": decisivo, "sin_prediccion": res["sin_prediccion"], "por_anio": {}}
    for a in ANIOS_EVAL:
        fa = [f for f in filas if f["anio_obj"] == a]
        if not fa:
            continue
        y = np.array([f["y"] for f in fa])
        qs = np.array([f["q"] for f in fa])
        wm = float(np.mean([f["wis_modelo"] for f in fa]))
        wr = float(np.mean([f[f"wis_{decisivo}"] for f in fa]))
        wp = float(np.mean([f["wis_persistencia_rw"] for f in fa]))
        out["por_anio"][a] = {
            "n": len(fa),
            "wis_modelo": round(wm, 1),
            "wis_referencia": round(wr, 1),
            "skill": round(1 - wm / wr, 3),
            "skill_vs_persistencia": round(1 - wm / wp, 3),
            "cobertura_50": round(cobertura(y, qs, *IDX_B50), 3),
            "cobertura_95": round(cobertura(y, qs, *IDX_B95), 3),
        }
    return out


# --- variantes de calibracion (--calibracion) -----------------------------
#
# Fijadas antes de mirar resultados; se comparan todas y se informan todas.
#   V0 publicada: CQR-r, 52 pares mas recientes, score winsorizado al p90
#   V1 ventana_tablero: CQR-r calibrado con todos los pares con objetivo desde
#      2024 (serie con la forma del tablero), si hay al menos MIN_CAL
#   V2 cqr_aditivo: CQR clasico en log (Romano et al. 2019), 52 pares
#   V3 sin_winsor: V0 sin winsorizar el score
#   V4 ventana_tablero_sin_winsor: V1 + V3

INICIO_TABLERO = date(2024, 1, 1)
VARIANTES = ("V0_publicada", "V1_ventana_tablero", "V2_cqr_aditivo", "V3_sin_winsor", "V4_ventana_sin_winsor")


def _factores_cqr_r(qcal_z: np.ndarray, ycal_z: np.ndarray, winsor: bool) -> np.ndarray:
    """_ajustes_cqr_r con el winsorizado opcional (mismo nivel conformal)."""
    n = len(ycal_z)
    m = qcal_z[:, IDX_MEDIANA]
    fac = np.zeros(len(PARES_INTERVALO))
    for j, (lo, hi) in enumerate(PARES_INTERVALO):
        semi_lo = np.maximum(m - qcal_z[:, lo], 1e-3)
        semi_hi = np.maximum(qcal_z[:, hi] - m, 1e-3)
        e = np.maximum(np.maximum((m - ycal_z) / semi_lo, (ycal_z - m) / semi_hi), 0.0)
        if winsor:
            e = np.minimum(e, np.quantile(e, 0.90))
        nivel = min(ceil((n + 1) * (1.0 - ALPHAS[j])) / n, 1.0)
        f = np.max(e) if nivel >= 1.0 else np.quantile(e, nivel, method="higher")
        fac[j] = float(np.clip(f, 0.0, 4.0))
    return fac


def _margenes_cqr(qcal_z: np.ndarray, ycal_z: np.ndarray) -> np.ndarray:
    """CQR clasico: por par, el margen aditivo (en log) que cubre el nivel."""
    n = len(ycal_z)
    Q = np.zeros(len(PARES_INTERVALO))
    for j, (lo, hi) in enumerate(PARES_INTERVALO):
        s = np.maximum(qcal_z[:, lo] - ycal_z, ycal_z - qcal_z[:, hi])
        nivel = min(ceil((n + 1) * (1.0 - ALPHAS[j])) / n, 1.0)
        Q[j] = float(np.max(s) if nivel >= 1.0 else np.quantile(s, nivel, method="higher"))
    return Q


def _aplicar_margenes(qz: np.ndarray, Q: np.ndarray) -> np.ndarray:
    qz_c = qz.copy()
    for j, (lo, hi) in enumerate(PARES_INTERVALO):
        qz_c[lo] = qz[lo] - Q[j]
        qz_c[hi] = qz[hi] + Q[j]
    return np.clip(np.expm1(np.sort(qz_c)), 0.0, None)


def _cadena_variantes(serie: Serie, origenes: list[int], h: int) -> dict[int, dict[str, np.ndarray] | None]:
    out: dict[int, dict[str, np.ndarray] | None] = {}
    estado: dict | None = None
    ultimo = -10_000
    for o in origenes:
        if o - ultimo >= CADENCIA_REAJUSTE or estado is None:
            X, Y, idx = pares_sin_hueco(serie, o, h, ALCANCE_HISTORIA)
            if len(Y) < MIN_PROPER + MIN_CAL:
                out[o] = None
                estado = None
                continue
            orden = np.argsort([serie.fecha[k] for k in idx])
            # split A: los N_CAL mas recientes (publicado)
            tr_a, ca_a = orden[: len(orden) - N_CAL], orden[len(orden) - N_CAL:]
            m_a = _fit_q(X[tr_a], Y[tr_a])
            q_a = np.sort(np.column_stack([m.predict(X[ca_a]) for m in m_a]), axis=1)
            # split B: todo lo que tiene objetivo desde 2024
            n_b = int(sum(serie.fecha[idx[k]] >= INICIO_TABLERO for k in orden))
            if n_b >= MIN_CAL and len(orden) - n_b >= MIN_PROPER and n_b != N_CAL:
                tr_b, ca_b = orden[: len(orden) - n_b], orden[len(orden) - n_b:]
                m_b = _fit_q(X[tr_b], Y[tr_b])
                q_b = np.sort(np.column_stack([m.predict(X[ca_b]) for m in m_b]), axis=1)
                y_b = Y[ca_b]
            else:
                m_b, q_b, y_b = m_a, q_a, Y[ca_a]
            estado = {
                "m_a": m_a, "m_b": m_b,
                "f0": _factores_cqr_r(q_a, Y[ca_a], True),
                "f3": _factores_cqr_r(q_a, Y[ca_a], False),
                "Q2": _margenes_cqr(q_a, Y[ca_a]),
                "f1": _factores_cqr_r(q_b, y_b, True),
                "f4": _factores_cqr_r(q_b, y_b, False),
            }
            ultimo = o
        x = features_sin_hueco(serie, o, h)
        if x is None:
            out[o] = None
            continue
        xz = x.reshape(1, -1)
        qz_a = np.sort(np.array([m.predict(xz)[0] for m in estado["m_a"]]))
        qz_b = np.sort(np.array([m.predict(xz)[0] for m in estado["m_b"]]))
        out[o] = {
            "V0_publicada": _qs_calibrado_cqr_r(qz_a, estado["f0"]),
            "V1_ventana_tablero": _qs_calibrado_cqr_r(qz_b, estado["f1"]),
            "V2_cqr_aditivo": _aplicar_margenes(qz_a, estado["Q2"]),
            "V3_sin_winsor": _qs_calibrado_cqr_r(qz_a, estado["f3"]),
            "V4_ventana_sin_winsor": _qs_calibrado_cqr_r(qz_b, estado["f4"]),
        }
    return out


def _horizonte_variantes(args: tuple[Serie, int]) -> dict:
    serie, h = args
    threadpool_limits(retro.HILOS_POR_PROCESO)
    _instalar_parches()
    origenes = origenes_eval(serie, h)
    q = _cadena_variantes(serie, origenes, h)
    filas = []
    for o in origenes:
        if q[o] is None:
            continue
        y = float(serie.casos[o + h])
        fila = {"anio_obj": int(serie.anio[o + h]), "semana_obj": int(serie.semana[o + h]), "y": y,
                "q": {k: v.tolist() for k, v in q[o].items()}}
        for nombre in REFERENCIAS:
            fila[f"wis_{nombre}"] = wis(y, referencia(nombre, serie, o, h))
        filas.append(fila)
    return {"h": h, "filas": filas}


def comparar_calibraciones(serie: Serie, salida: Path) -> None:
    with ProcessPoolExecutor(max_workers=len(HORIZONTES)) as ex:
        resultados = list(ex.map(_horizonte_variantes, [(serie, h) for h in HORIZONTES]))
    tabla = []
    for r in resultados:
        filas = r["filas"]
        decisivo = min(REFERENCIAS, key=lambda n: np.mean([f[f"wis_{n}"] for f in filas]))
        for a in ANIOS_EVAL:
            fa = [f for f in filas if f["anio_obj"] == a]
            y = np.array([f["y"] for f in fa])
            wr = float(np.mean([f[f"wis_{decisivo}"] for f in fa]))
            for v in VARIANTES:
                qs = np.array([f["q"][v] for f in fa])
                wm = float(np.mean([wis(yy, qq) for yy, qq in zip(y, qs)]))
                tabla.append({"h": r["h"], "anio": a, "variante": v, "n": len(fa),
                              "skill": 1 - wm / wr,
                              "cob50": cobertura(y, qs, *IDX_B50), "cob95": cobertura(y, qs, *IDX_B95)})
    print(f"\npromedio de h = 1..8 (entre parentesis, h = 4)")
    print(f"{'variante':<24} {'anio':>5} {'skill':>14} {'cob50':>14} {'cob95':>14}")
    for v in VARIANTES:
        for a in ANIOS_EVAL:
            ft = [t for t in tabla if t["variante"] == v and t["anio"] == a]
            t4 = next(t for t in ft if t["h"] == 4)
            celdas = [f"{np.mean([t[k] for t in ft]):.2f} ({t4[k]:.2f})" for k in ("skill", "cob50", "cob95")]
            print(f"{v:<24} {a:>5} {celdas[0]:>14} {celdas[1]:>14} {celdas[2]:>14}")
    salida.write_text(json.dumps(tabla), encoding="utf-8")
    print(f"\ntabla -> {salida}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--calibracion", action="store_true", help="comparar las variantes de calibracion")
    ap.add_argument("--ceros-como-hueco", action="store_true",
                    help="tratar como hueco las semanas de OpenDengue con 0 casos")
    args = ap.parse_args()
    conn = get_connection()
    try:
        serie = cargar_serie_mixta(conn)
    finally:
        conn.close()
    sufijo = ""
    if args.ceros_como_hueco:
        sufijo = "_ceros_hueco"
        print(f"ceros de OpenDengue tratados como hueco: {ceros_como_hueco(serie)}")
    salida = SALIDA.with_name(SALIDA.stem + sufijo + ".json")
    huecos = [str(serie.fecha[k]) for k in np.flatnonzero(np.isnan(serie.casos))]
    print(f"serie mixta: {serie.T} semanas, {serie.fecha[0]} a {serie.fecha[-1]}; huecos {huecos}")

    if args.calibracion:
        comparar_calibraciones(serie, SALIDA.with_name(f"experimento_tablero_calibracion{sufijo}.json"))
        return

    with ProcessPoolExecutor(max_workers=len(HORIZONTES)) as ex:
        resultados = list(ex.map(_horizonte, [(serie, h) for h in HORIZONTES]))

    resumen = {r["h"]: resumir(r) for r in resultados}
    print(f"\n{'h':>2} {'anio':>5} {'n':>3} {'WIS mod':>8} {'WIS ref':>8} {'skill':>7} {'vs RW':>7} {'cob50':>6} {'cob95':>6}  ref")
    for h, r in resumen.items():
        for a, m in r["por_anio"].items():
            print(f"{h:>2} {a:>5} {m['n']:>3} {m['wis_modelo']:>8} {m['wis_referencia']:>8} "
                  f"{m['skill']:>7} {m['skill_vs_persistencia']:>7} {m['cobertura_50']:>6} {m['cobertura_95']:>6}  {r['decisivo']}")
        print(f"   sin prediccion (rezagos sobre el hueco o sin historia): {r['sin_prediccion']}")

    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps({"resumen": resumen, "detalle": resultados}, default=str), encoding="utf-8")
    print(f"\ndetalle -> {salida}")


if __name__ == "__main__":
    main()
