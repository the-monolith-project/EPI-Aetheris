"""
Precomputo del artefacto de estimacion a corto plazo de dengue para la UI.

Metodo: el mismo del experimento firmado
(`docs/experimentos/experimento-nowcast-corto-plazo.md`) mas la capa de
calibracion de intervalos cerrada el 2026-09-09 (CQR-r; ver la seccion
"Calibracion de intervalos" del mismo doc). Este script NO reentrena nada nuevo:
reutiliza la maquinaria validada de `experimento_nowcast_corto_plazo.py` y
`experimento_nowcast_calibracion.py`.

Que produce (`backend/api/datos/nowcast_dengue.json`, versionado):

  - ancla:   ultima semana observada de la serie (OpenDengue V1.3 termina en
             2024-12-22; la fuente va ~21 meses detras del tiempo real). La
             estimacion se extiende h = 1..8 semanas DESDE esa semana, no desde
             "hoy". El artefacto lleva la fecha de ancla explicita.
  - estimacion: 23 cuantiles calibrados (CQR-r) por horizonte, en escala de
             conteo, mas mediana y bandas 50 % / 95 %.
  - observado: ultimas ~120 semanas para el contexto de la grafica.
  - backtest: en los anios de prueba (2019, 2021-2024), la estimacion a h = 4
             semanas encadenada hacia adelante contra lo realmente observado.
  - desempeno: WIS del modelo vs. el baseline mas fuerte, skill por anio,
             anios ganados y cobertura empirica, a h = 4.

Solo lectura de Postgres. Sin dependencia nueva.

Uso:
    cd backend/ingestion
    POSTGRES_HOST=localhost ../.venv/bin/python nowcast_estimacion_dengue.py
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from experimento_nowcast_corto_plazo import (
    ANIOS_PRUEBA,
    CUANTILES,
    IDX_MEDIANA,
    PARES_INTERVALO,
    Serie,
    baseline_climatologia,
    baseline_persistencia,
    baseline_persistencia_estacional,
    cargar_serie,
    cobertura,
    features_en,
    origenes_de_prueba,
    pares_entrenamiento,
    skill_por_anio,
    wis,
)
from experimento_nowcast_calibracion import (
    _ajustes_cqr_r,
    _fit_q,
    correr_modelo_calibrado,
)

from db import get_connection

ALCANCE_HISTORIA = 2014          # ventana principal firmada (con brote grande previo)
HORIZONTE_BACKTEST = 4           # horizonte decisivo del experimento
HORIZONTES = list(range(1, 9))   # 1..8 semanas para la estimacion
N_CAL = 52                       # pares de calibracion CQR-r (valor del experimento)
SEMANAS_CONTEXTO = 120           # observado reciente que viaja en el artefacto
IDX_B50 = (6, 16)                # cuantiles 0.25 / 0.75
IDX_B95 = (1, 21)                # cuantiles 0.025 / 0.975

SALIDA = Path(__file__).resolve().parents[1] / "api" / "datos" / "nowcast_dengue.json"

NOTA_ALCANCE = (
    "La estimación asume una temporada con un brote grande ya presente en el "
    "historial de entrenamiento (serie desde 2014). Sin ese precedente el "
    "método pierde ventaja sobre una extrapolación ingenua; el alcance se "
    "detalla en docs/biblioteca/05-sensibilidad-y-honestidad.md."
)


def _extender_serie_futuro(serie: Serie, n: int) -> tuple[Serie, int]:
    """Anexa n semanas futuras con calendario real (fecha, doy, anio) y conteo
    NaN. Solo alimentan la estacionalidad determinista de la semana objetivo en
    `features_en`; nunca entran como pares de entrenamiento (su fecha es
    posterior al corte). Devuelve (serie_extendida, T_real)."""
    t_real = serie.T
    ult = serie.fecha[-1]
    fechas_fut = [ult + timedelta(days=7 * k) for k in range(1, n + 1)]

    fecha = np.concatenate([serie.fecha, np.array(fechas_fut, dtype=object)])
    anio = np.concatenate([serie.anio, np.array([f.year for f in fechas_fut], dtype=int)])
    semana = np.concatenate([serie.semana, np.array(
        [min(int(f.isocalendar()[1]), 53) for f in fechas_fut], dtype=int)])
    doy = np.concatenate([serie.doy, np.array(
        [f.timetuple().tm_yday for f in fechas_fut], dtype=int)])
    nan_fut = np.full(n, np.nan)
    casos = np.concatenate([serie.casos, nan_fut])
    z = np.concatenate([serie.z, nan_fut])
    clima = {k: np.concatenate([v, nan_fut]) for k, v in serie.clima.items()}
    oni = np.concatenate([serie.oni, np.full(n, serie.oni[-1])])

    return Serie(fecha, anio, semana, doy, casos, z, clima, oni), t_real


def _qs_calibrado_cqr_r(qz_pt_sorted: np.ndarray, fac_cqr: np.ndarray) -> np.ndarray:
    """Aplica el factor multiplicativo por par de intervalo sobre los cuantiles
    del proper-train (en log) y devuelve el vector natural, ordenado."""
    m0 = qz_pt_sorted[IDX_MEDIANA]
    qz_c = qz_pt_sorted.copy()
    for j, (lo, hi) in enumerate(PARES_INTERVALO):
        qz_c[lo] = m0 - fac_cqr[j] * (m0 - qz_pt_sorted[lo])
        qz_c[hi] = m0 + fac_cqr[j] * (qz_pt_sorted[hi] - m0)
    return np.clip(np.expm1(np.sort(qz_c)), 0.0, None)


def _paquete_cuantiles(q_nat: np.ndarray) -> dict:
    q_nat = np.sort(q_nat)
    return {
        "cuantiles": [round(float(v), 1) for v in q_nat],
        "mediana": round(float(q_nat[IDX_MEDIANA]), 1),
        "banda_50": [round(float(q_nat[IDX_B50[0]]), 1), round(float(q_nat[IDX_B50[1]]), 1)],
        "banda_95": [round(float(q_nat[IDX_B95[0]]), 1), round(float(q_nat[IDX_B95[1]]), 1)],
    }


def _monotona_en_horizonte(medianas: np.ndarray, q_por_h: np.ndarray) -> np.ndarray:
    """Impone que el semiancho de cada intervalo (respecto a la mediana de su
    propio horizonte) sea NO DECRECIENTE en h. La calibracion conformal por
    horizonte se ajusta con solo N_CAL=52 pares, ruido suficiente para invertir
    el orden natural del abanico (un pronostico a 8 semanas no puede tener menos
    incertidumbre que uno a 1). Es una restriccion estructural: no toca las
    medianas, solo ensancha los intervalos que hubieran quedado mas estrechos
    que un horizonte anterior. q_por_h: (n_h, 23) natural, ordenado por fila."""
    n_h, n_q = q_por_h.shape
    semi = q_por_h - medianas[:, None]              # negativo abajo, positivo arriba
    for j in range(n_q):
        if j < IDX_MEDIANA:
            semi[:, j] = -np.maximum.accumulate(-semi[:, j])  # cummin -> mas negativo
        elif j > IDX_MEDIANA:
            semi[:, j] = np.maximum.accumulate(semi[:, j])
    # Redondear el semiancho a la misma malla (0.1) con que se serializa el
    # artefacto: asi la monotonia sobrevive al redondeo por extremo de
    # _paquete_cuantiles (dos extremos a +-0.05 podrian invertir un ancho que
    # solo crece unas centesimas entre horizontes).
    semi = np.round(semi, 1)
    corr = np.round(medianas, 1)[:, None] + semi
    return np.clip(np.sort(corr, axis=1), 0.0, None)


def estimacion_futura(serie_ext: Serie, t_real: int) -> list[dict]:
    """Para cada h en HORIZONTES: ajusta 23 modelos cuantil sobre todo el
    historial 2014+ con objetivo anterior a la ultima semana observada, calibra
    con los ultimos N_CAL pares y proyecta desde esa semana. Al final se impone
    la monotonia del abanico en h (ver _monotona_en_horizonte)."""
    origen = t_real - 1  # ultima semana con conteo real
    filas, q_por_h, medianas = [], [], []
    for h in HORIZONTES:
        X, Y, idx = pares_entrenamiento(serie_ext, origen, h, ALCANCE_HISTORIA)
        orden = np.argsort([serie_ext.fecha[k] for k in idx])
        i_tr, i_ca = orden[: len(orden) - N_CAL], orden[len(orden) - N_CAL:]
        m_pt = _fit_q(X[i_tr], Y[i_tr])
        qca = np.sort(np.column_stack([m.predict(X[i_ca]) for m in m_pt]), axis=1)
        fac = _ajustes_cqr_r(qca, Y[i_ca])

        x = features_en(serie_ext, origen, h)
        qz_pt = np.sort(np.array([m.predict(x.reshape(1, -1))[0] for m in m_pt]))
        q_nat = _qs_calibrado_cqr_r(qz_pt, fac)

        q_por_h.append(q_nat)
        medianas.append(q_nat[IDX_MEDIANA])
        filas.append({
            "h": h,
            "fecha": serie_ext.fecha[origen + h].isoformat(),
            "anio": int(serie_ext.anio[origen + h]),
            "semana": int(serie_ext.semana[origen + h]),
        })

    q_mono = _monotona_en_horizonte(np.array(medianas), np.array(q_por_h))
    return [{**f, **_paquete_cuantiles(q_mono[k])} for k, f in enumerate(filas)]


def bloque_backtest(serie: Serie) -> tuple[list[dict], dict]:
    """Estimacion calibrada (CQR-r) a h = HORIZONTE_BACKTEST encadenada hacia
    adelante en los anios de prueba, con su desempeno agregado vs. el baseline
    mas fuerte."""
    h = HORIZONTE_BACKTEST
    origenes = origenes_de_prueba(serie, h, ALCANCE_HISTORIA)

    baselines = {
        "persistencia_rw": baseline_persistencia(serie, origenes, h, ALCANCE_HISTORIA),
        "climatologia_estacional": baseline_climatologia(serie, origenes, h, ALCANCE_HISTORIA),
        "persistencia_estacional": baseline_persistencia_estacional(serie, origenes, h, ALCANCE_HISTORIA),
    }
    decisivo = min(baselines.values(), key=lambda b: b["wis_por_pred"].mean())

    variantes = correr_modelo_calibrado(serie, origenes, h, ALCANCE_HISTORIA, N_CAL)
    mod = variantes["cqr_r"]

    puntos = []
    for k, o in enumerate(origenes):
        qs = np.sort(mod["qs"][k])
        puntos.append({
            "fecha": serie.fecha[o + h].isoformat(),
            "anio": int(serie.anio[o + h]),
            "observado": round(float(serie.casos[o + h]), 1),
            "mediana": round(float(qs[IDX_MEDIANA]), 1),
            "banda_50": [round(float(qs[IDX_B50[0]]), 1), round(float(qs[IDX_B50[1]]), 1)],
            "banda_95": [round(float(qs[IDX_B95[0]]), 1), round(float(qs[IDX_B95[1]]), 1)],
        })

    sk = skill_por_anio(mod, decisivo)
    anios_ganados = sum(
        1 for a in ANIOS_PRUEBA
        if (mod["anio"] == a).any()
        and mod["wis_por_pred"][mod["anio"] == a].mean()
        <= decisivo["wis_por_pred"][decisivo["anio"] == a].mean()
    )
    desempeno = {
        "horizonte": h,
        "baseline": decisivo["nombre"],
        "wis_modelo": round(float(mod["wis_por_pred"].mean()), 1),
        "wis_baseline": round(float(decisivo["wis_por_pred"].mean()), 1),
        "reduccion_wis": round(1.0 - mod["wis_por_pred"].mean() / decisivo["wis_por_pred"].mean(), 3),
        "skill_medio_por_anio": round(float(np.mean(list(sk.values()))), 3),
        "skill_por_anio": {int(a): round(float(v), 3) for a, v in sk.items()},
        "anios_ganados": int(anios_ganados),
        "n_anios": len(sk),
        "cobertura_50": round(cobertura(mod["y"], mod["qs"], *IDX_B50), 3),
        "cobertura_95": round(cobertura(mod["y"], mod["qs"], *IDX_B95), 3),
    }
    return puntos, desempeno


def main() -> None:
    conn = get_connection()
    try:
        serie = cargar_serie(conn)
    finally:
        conn.close()

    serie_ext, t_real = _extender_serie_futuro(serie, max(HORIZONTES))
    ancla = serie.fecha[-1]

    estimacion = estimacion_futura(serie_ext, t_real)
    bt_puntos, desempeno = bloque_backtest(serie)

    ctx = range(max(0, serie.T - SEMANAS_CONTEXTO), serie.T)
    observado = [
        {"fecha": serie.fecha[i].isoformat(), "casos": round(float(serie.casos[i]), 1)}
        for i in ctx
    ]

    artefacto = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente_serie": "opendengue_v1_3",
        "metodo": "HistGradientBoosting quantile (23 cuantiles) + calibracion CQR-r",
        "alcance_historia_desde": ALCANCE_HISTORIA,
        "ancla": {
            "fecha": ancla.isoformat(),
            "anio": int(serie.anio[-1]),
            "semana": int(serie.semana[-1]),
            "casos": round(float(serie.casos[-1]), 1),
        },
        "horizontes": HORIZONTES,
        "observado": observado,
        "estimacion": estimacion,
        "backtest": {
            "horizonte": HORIZONTE_BACKTEST,
            "anios": [a for a in ANIOS_PRUEBA],
            "puntos": bt_puntos,
        },
        "desempeno": desempeno,
        "nota_alcance": NOTA_ALCANCE,
    }

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(artefacto, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"artefacto -> {SALIDA}")
    print(f"  ancla {artefacto['ancla']['fecha']}  casos={artefacto['ancla']['casos']}")
    for e in estimacion:
        print(f"  h={e['h']}  mediana={e['mediana']:8.1f}  "
              f"50%[{e['banda_50'][0]:.0f}, {e['banda_50'][1]:.0f}]  "
              f"95%[{e['banda_95'][0]:.0f}, {e['banda_95'][1]:.0f}]")
    d = desempeno
    print(f"  backtest h={d['horizonte']}: WIS {d['wis_modelo']} vs {d['wis_baseline']} "
          f"({d['baseline']}), reduccion {d['reduccion_wis']:+.0%}, "
          f"skill/anio {d['skill_medio_por_anio']:+.3f}, "
          f"anios {d['anios_ganados']}/{d['n_anios']}, "
          f"cob50={d['cobertura_50']} cob95={d['cobertura_95']}")


if __name__ == "__main__":
    main()
