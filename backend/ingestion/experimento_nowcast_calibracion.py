"""
Experimento: calibracion de intervalos del proto-predictor de nowcast.

Pendiente 3 de la decision 5 firmada en
docs/experimentos/experimento-nowcast-corto-plazo.md: los intervalos del modelo
corren estrechos (cobertura al 50 % en ~0.38-0.43 a h=4, nominal 0.50). Este
script prueba una capa de calibracion conformal (CQR) encima del mismo pipeline.

Reutiliza toda la maquinaria del script original
(`experimento_nowcast_corto_plazo.py`): carga de serie, features, WIS, baselines,
protocolo forward-chaining, criterio. Solo agrega la capa de calibracion. NO
toca el script original, NO escribe a Postgres, NO cambia el criterio firmado.

Metodo (CQR por intervalo, Romano et al. 2019 generalizado a 23 cuantiles):

  Para cada reajuste en el origen o:
    - se ordenan los pares de entrenamiento por fecha del objetivo;
    - los ultimos N_CAL pares son el conjunto de CALIBRACION;
    - el resto es PROPER-TRAIN -> se ajustan ahi los 23 modelos cuantil;
    - en calibracion, para cada par simetrico k con nivel nominal 1-alpha_k:
        E_i = max( q_lo(x_i) - y_i , y_i - q_hi(x_i) )        (escala log)
        nivel = ceil((n_cal+1)(1-alpha_k)) / n_cal
        adj_k = cuantil-nivel de {E_i}      (puede ser < 0: CQR tambien encoge)
    - en prediccion: q_lo -= adj_k , q_hi += adj_k ; la mediana no se toca ;
      se re-ordena el vector de 23 para monotonia ; se vuelve a escala de conteo.

Variantes que corre y compara en la misma pasada:
  - sin_calibrar   : el modelo tal cual, ajustado con TODOS los pares (baseline
                     real, identico al script original salvo ruido numerico).
  - cqr_r          : CQR escalado (Romano et al., variante "r"): la conformidad
                     y la correccion son MULTIPLICATIVAS sobre el ancho del
                     intervalo -> estable ante heterocedasticidad (el ancho
                     crece con el nivel de casos). Reentrena sobre proper-train.
  - inflado_global : un solo escalar s sobre (q - mediana), ajustado en
                     calibracion para que la cobertura al 80 % de al nominal.
                     Comparacion ingenua. Reentrena sobre proper-train.

Las dos variantes calibradas pagan el costo de apartar N_CAL pares del ajuste;
la comparacion honesta es "si adopto calibracion, que doy a cambio respecto al
modelo sin calibrar actual".

Uso:
    cd backend/ingestion
    POSTGRES_HOST=localhost ../.venv/bin/python experimento_nowcast_calibracion.py
    POSTGRES_HOST=localhost ../.venv/bin/python experimento_nowcast_calibracion.py --horizonte 4 --ncal 52,78
"""

from __future__ import annotations

import argparse
import json
from math import ceil
from pathlib import Path

import numpy as np

from experimento_nowcast_corto_plazo import (
    ALCANCES,
    ANIO_EXCLUIDO,
    ANIOS_PRUEBA,
    CADENCIA_REAJUSTE,
    CUANTILES,
    HGBR_KW,
    HORIZONTE_DECISIVO,
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
    resumen_resultado,
    skill_por_anio,
    verificar_sin_fuga,
    wis,
    _empaquetar,
)
from sklearn.ensemble import HistGradientBoostingRegressor

from db import get_connection

SALIDA_DIR = Path(__file__).parent / "data" / "interim" / "nowcast_calibracion"

NCAL_DEFAULT = 52          # pares de calibracion (los mas recientes por fecha objetivo)
MIN_PROPER = 120           # minimo de proper-train para ajustar
MIN_CAL = 40               # minimo de calibracion para calibrar

OBJ_COBERTURA_95 = (0.90, 0.98)   # objetivo de calibracion (mas estricto que la banda firmada)
OBJ_COBERTURA_50 = (0.42, 0.58)
# bandas FIRMADAS (decision 5) para el veredicto cumple/parcial/no-cumple:
FIRMA_COBERTURA_95 = (0.85, 0.99)
FIRMA_COBERTURA_50 = (0.35, 0.65)
CRIT_MIN_ANIOS_GANADOS = 4  # de 5


ALPHAS = np.array([2 * CUANTILES[lo] for lo, _ in PARES_INTERVALO])  # 0.02 .. 0.90


def _ajustes_cqr_r(qcal_z: np.ndarray, ycal_z: np.ndarray) -> np.ndarray:
    """CQR escalado (variante 'r'): conformidad normalizada por el semiancho del
    intervalo. Devuelve, por par k, un factor f_k tal que el intervalo calibrado
    es  [m - f_k*(m - q_lo),  m + f_k*(q_hi - m)]  (m = mediana). Multiplicativo
    -> estable ante heterocedasticidad. qcal_z: (n_cal, 23) ordenado por fila."""
    n = len(ycal_z)
    m = qcal_z[:, IDX_MEDIANA]
    fac = np.zeros(len(PARES_INTERVALO))
    for j, (lo, hi) in enumerate(PARES_INTERVALO):
        semi_lo = np.maximum(m - qcal_z[:, lo], 1e-3)
        semi_hi = np.maximum(qcal_z[:, hi] - m, 1e-3)
        # score = cuanto hay que estirar el semiancho para cubrir y_i
        e = np.maximum((m - ycal_z) / semi_lo, (ycal_z - m) / semi_hi)
        e = np.maximum(e, 0.0)
        # n_cal es corto (52): el score crudo lo domina una sola semana. Se
        # winsoriza al p90 antes de tomar el nivel y se topa el factor en 4.0.
        e = np.minimum(e, np.quantile(e, 0.90))
        nivel = min(ceil((n + 1) * (1.0 - ALPHAS[j])) / n, 1.0)
        if nivel >= 1.0:
            fac[j] = float(np.max(e))
        else:
            fac[j] = float(np.quantile(e, nivel, method="higher"))
        fac[j] = float(np.clip(fac[j], 0.0, 4.0))
    return fac


def _escala_inflado(qcal_z: np.ndarray, ycal_z: np.ndarray) -> float:
    """Un escalar s tal que, tras escalar (q - mediana) por s, la cobertura del
    intervalo 80 % (cuantiles 0.10 / 0.90, indices 3 / 19) da el nominal en
    calibracion. Comparacion ingenua contra CQR."""
    m = qcal_z[:, IDX_MEDIANA]
    lo0 = qcal_z[:, 3] - m       # cuantil 0.10
    hi0 = qcal_z[:, 19] - m      # cuantil 0.90
    objetivo = 0.80
    cand = np.linspace(0.5, 6.0, 276)
    mejor, mejor_gap = 1.0, 1e9
    for s in cand:
        cov = np.mean((ycal_z >= m + s * lo0) & (ycal_z <= m + s * hi0))
        g = abs(cov - objetivo)
        if g < mejor_gap:
            mejor_gap, mejor = g, s
    return float(mejor)


def _fit_q(X: np.ndarray, Y: np.ndarray) -> list[HistGradientBoostingRegressor]:
    ms = []
    for q in CUANTILES:
        m = HistGradientBoostingRegressor(quantile=float(q), **HGBR_KW)
        m.fit(X, Y)
        ms.append(m)
    return ms


def correr_modelo_calibrado(serie: Serie, origenes: list[int], h: int,
                            anio_min: int, n_cal: int) -> dict[str, dict]:
    """Devuelve 'sin_calibrar' (ajuste completo), 'cqr_r' e 'inflado_global'
    (ajuste sobre proper-train, calibracion sobre los n_cal pares mas recientes)."""
    salida = {k: {"nombre": k, "qs": [], "y": [], "anio": []}
              for k in ("sin_calibrar", "cqr_r", "inflado_global")}

    m_full: list = []
    m_pt: list = []
    fac_cqr = np.ones(len(PARES_INTERVALO))
    s_infl = 1.0
    ultimo = -10_000
    n_fb = 0

    for o in origenes:
        if o - ultimo >= CADENCIA_REAJUSTE or not m_full:
            X, Y, idx = pares_entrenamiento(serie, o, h, anio_min)
            if len(Y) < MIN_PROPER + MIN_CAL:
                for k in salida:
                    salida[k]["qs"].append(np.full(len(CUANTILES), serie.casos[o]))
                    salida[k]["y"].append(serie.casos[o + h])
                    salida[k]["anio"].append(int(serie.anio[o + h]))
                n_fb += 1
                continue
            m_full = _fit_q(X, Y)
            # split temporal: los n_cal pares con objetivo mas reciente = calibracion
            orden = np.argsort([serie.fecha[k] for k in idx])
            i_tr, i_ca = orden[:len(orden) - n_cal], orden[len(orden) - n_cal:]
            m_pt = _fit_q(X[i_tr], Y[i_tr])
            qca = np.sort(np.column_stack([m.predict(X[i_ca]) for m in m_pt]), axis=1)
            fac_cqr = _ajustes_cqr_r(qca, Y[i_ca])
            s_infl = _escala_inflado(qca, Y[i_ca])
            ultimo = o

        x = features_en(serie, o, h)
        if x is None:
            for k in salida:
                salida[k]["qs"].append(np.full(len(CUANTILES), serie.casos[o]))
                salida[k]["y"].append(serie.casos[o + h])
                salida[k]["anio"].append(int(serie.anio[o + h]))
            n_fb += 1
            continue

        xz = x.reshape(1, -1)
        qz_full = np.sort(np.array([m.predict(xz)[0] for m in m_full]))
        qz_pt = np.sort(np.array([m.predict(xz)[0] for m in m_pt]))

        salida["sin_calibrar"]["qs"].append(np.clip(np.expm1(qz_full), 0, None))

        # cqr_r: estira cada semiancho por su factor
        m0 = qz_pt[IDX_MEDIANA]
        qz_c = qz_pt.copy()
        for j, (lo, hi) in enumerate(PARES_INTERVALO):
            qz_c[lo] = m0 - fac_cqr[j] * (m0 - qz_pt[lo])
            qz_c[hi] = m0 + fac_cqr[j] * (qz_pt[hi] - m0)
        salida["cqr_r"]["qs"].append(np.clip(np.expm1(np.sort(qz_c)), 0, None))

        # inflado_global
        qz_i = m0 + s_infl * (qz_pt - m0)
        salida["inflado_global"]["qs"].append(np.clip(np.expm1(np.sort(qz_i)), 0, None))

        for k in salida:
            salida[k]["y"].append(serie.casos[o + h])
            salida[k]["anio"].append(int(serie.anio[o + h]))

    out = {}
    for k, r in salida.items():
        r = _empaquetar(r)
        r["n_fallback"] = n_fb
        r["escala_inflado_ultima"] = float(s_infl)
        r["factores_cqr_r_ultimos"] = [round(float(f), 3) for f in fac_cqr]
        out[k] = r
    return out


def correr(alcance: int, h: int, n_cal: int) -> dict:
    conn = get_connection()
    try:
        serie = cargar_serie(conn)
    finally:
        conn.close()

    origenes = origenes_de_prueba(serie, h, alcance)
    print(f"\n=== alcance {alcance}+ | h {h} | n_cal {n_cal} | {len(origenes)} origenes ===")
    verificar_sin_fuga(serie, origenes, h, alcance)

    baselines = {
        "persistencia_rw": baseline_persistencia(serie, origenes, h, alcance),
        "climatologia_estacional": baseline_climatologia(serie, origenes, h, alcance),
        "persistencia_estacional": baseline_persistencia_estacional(serie, origenes, h, alcance),
    }
    decisivo = min(baselines.values(), key=lambda b: b["wis_por_pred"].mean())

    variantes = correr_modelo_calibrado(serie, origenes, h, alcance, n_cal)

    salida = {
        "alcance_anio_min": alcance, "horizonte": h, "n_cal": n_cal,
        "n_origenes": len(origenes),
        "comparador_decisivo": decisivo["nombre"],
        "baseline_decisivo": resumen_resultado(decisivo),
        "variantes": {},
    }
    bl = resumen_resultado(decisivo)
    for k, r in variantes.items():
        rs = resumen_resultado(r)
        sk = skill_por_anio(r, decisivo)
        rs["skill_por_anio_vs_decisivo"] = {int(a): float(v) for a, v in sk.items()}
        skill_medio = float(np.mean(list(sk.values()))) if sk else float("nan")
        rs["skill_medio_por_anio"] = skill_medio
        rs["n_fallback"] = r["n_fallback"]
        anios_ganados = sum(
            1 for a in ANIOS_PRUEBA
            if (r["anio"] == a).any()
            and r["wis_por_pred"][r["anio"] == a].mean()
            <= decisivo["wis_por_pred"][decisivo["anio"] == a].mean()
        )
        rs["anios_ganados_vs_decisivo"] = anios_ganados
        gana_wis_agrupado = (
            rs["wis_medio_natural"] <= bl["wis_medio_natural"]
            and rs["wis_medio_log"] <= bl["wis_medio_log"]
        )
        cumple_firmado = (
            skill_medio > 0
            and anios_ganados >= CRIT_MIN_ANIOS_GANADOS
            and FIRMA_COBERTURA_95[0] <= rs["cobertura_95"] <= FIRMA_COBERTURA_95[1]
            and FIRMA_COBERTURA_50[0] <= rs["cobertura_50"] <= FIRMA_COBERTURA_50[1]
        )
        rs["cumple_criterio_firmado"] = bool(cumple_firmado)
        rs["gana_wis_agrupado_nat_y_log"] = bool(gana_wis_agrupado)
        rs["cumple_criterio_exito"] = bool(cumple_firmado and gana_wis_agrupado)
        rs["veredicto"] = ("CUMPLE" if (cumple_firmado and gana_wis_agrupado)
                           else "PARCIAL" if cumple_firmado else "NO CUMPLE")
        # objetivo de calibracion (banda mas estricta, solo informativo)
        rs["cob50_en_objetivo"] = bool(OBJ_COBERTURA_50[0] <= rs["cobertura_50"] <= OBJ_COBERTURA_50[1])
        rs["cob95_en_objetivo"] = bool(OBJ_COBERTURA_95[0] <= rs["cobertura_95"] <= OBJ_COBERTURA_95[1])
        salida["variantes"][k] = rs
        print(f"  {k:16s} WIS_nat={rs['wis_medio_natural']:8.1f} "
              f"WIS_log={rs['wis_medio_log']:.3f} "
              f"skill/anio={skill_medio:+.3f} "
              f"anios={anios_ganados}/5 "
              f"cob50={rs['cobertura_50']:.2f} cob95={rs['cobertura_95']:.2f} "
              f"=> {rs['veredicto']}")
    if variantes["cqr_r"]["n_fallback"]:
        print(f"  [aviso] n_fallback={variantes['cqr_r']['n_fallback']} "
              f"(origenes sin modelo por pocos pares)")
    return salida


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--horizonte", default="4,1,2,8")
    p.add_argument("--alcance", default=",".join(str(a) for a in ALCANCES))
    p.add_argument("--ncal", default=str(NCAL_DEFAULT))
    args = p.parse_args()

    horizontes = [int(x) for x in args.horizonte.split(",")]
    alcances = [int(x) for x in args.alcance.split(",")]
    ncals = [int(x) for x in args.ncal.split(",")]

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    todo = []
    for alcance in alcances:
        for nc in ncals:
            for h in horizontes:
                s = correr(alcance, h, nc)
                f = SALIDA_DIR / f"cal_alcance{alcance}_h{h}_ncal{nc}.json"
                f.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
                todo.append(s)
    (SALIDA_DIR / "resumen.json").write_text(
        json.dumps(todo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResumen -> {SALIDA_DIR / 'resumen.json'}")


if __name__ == "__main__":
    main()
