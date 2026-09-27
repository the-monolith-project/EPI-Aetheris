"""
Precomputo del artefacto retrospectivo de la prediccion de dengue a corto plazo.

El artefacto principal (`nowcast_estimacion_dengue.py`) solo trae el abanico
desde la ultima semana observada y el backtest a h = 4. Este script genera,
para CADA semana de la serie, el abanico h = 1..8 que el modelo habria dado
con los datos disponibles hasta esa semana, para que la UI pueda mover el
punto de partida a cualquier semana y contrastarlo con lo observado despues.

Metodo: el mismo del artefacto principal (ADR 0020), sin cambios. Por cada
horizonte se corren dos cadenas forward-chaining con la misma cadencia de
reajuste y la misma calibracion CQR-r:

  - cadena de prueba: exactamente los origenes de prueba del experimento
    (`origenes_de_prueba`), la misma secuencia de reajustes que el backtest
    publicado. `main` aborta si a h = 4 no reproduce el desempeno publicado.
  - cadena complementaria: el resto de las semanas (2014-2018, 2020 y las
    semanas cuyo objetivo cae fuera de los anios de prueba).

2020 sigue excluido como objetivo de entrenamiento (D1), asi que mostrar sus
semanas no cambia ninguna prediccion de los demas anios. Su resumen por anio
se publica aparte y no entra en ningun agregado.

Las primeras semanas de la serie no tienen prediccion: el modelo necesita
MIN_PROPER + MIN_CAL pares de entrenamiento (unos tres anios de historia).
El artefacto las marca con `motivo` en lugar de rellenarlas con persistencia.

La ultima semana observada no se incluye: su abanico es `estimacion` del
artefacto principal.

Formato compacto (arrays por posicion, descritos en `campos`) porque son
~570 origenes x 8 horizontes.

Uso:
    cd backend/ingestion
    POSTGRES_HOST=localhost ../.venv/bin/python nowcast_retrospectivo_dengue.py
    # rehacer solo el JSON a partir de la ultima corrida (~25 min menos):
    POSTGRES_HOST=localhost ../.venv/bin/python nowcast_retrospectivo_dengue.py --desde-crudo
"""

from __future__ import annotations

import argparse
import json
import pickle
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

from experimento_nowcast_corto_plazo import (
    ANIO_EXCLUIDO,
    ANIOS_PRUEBA,
    CADENCIA_REAJUSTE,
    CUANTILES,
    IDX_MEDIANA,
    Serie,
    baseline_climatologia,
    baseline_persistencia,
    baseline_persistencia_estacional,
    cargar_serie,
    features_en,
    origenes_de_prueba,
    pares_entrenamiento,
    wis,
)
from experimento_nowcast_calibracion import MIN_CAL, MIN_PROPER, _ajustes_cqr_r, _fit_q
from nowcast_estimacion_dengue import (
    ALCANCE_HISTORIA,
    HORIZONTE_BACKTEST,
    HORIZONTES,
    IDX_B50,
    IDX_B95,
    N_CAL,
    SALIDA as SALIDA_PRINCIPAL,
    _extender_serie_futuro,
    _qs_calibrado_cqr_r,
)

from db import get_connection

SALIDA = SALIDA_PRINCIPAL.with_name("nowcast_dengue_retrospectivo.json")
# resultado crudo por horizonte: si la verificacion falla, se inspecciona sin
# repetir la corrida (~25 min)
# Un proceso por horizonte con un solo hilo de OpenMP cada uno: con los hilos
# por defecto, 8 procesos x N hilos saturan la maquina y la corrida tarda
# varias veces mas. El numero de hilos no cambia el resultado mas alla del
# ruido de coma flotante que ya tolera la verificacion.
HILOS_POR_PROCESO = 1

CRUDO = Path(__file__).parent / "data" / "interim" / "nowcast" / "retrospectivo_crudo.pkl"

MOTIVO_HISTORIA = "historia_insuficiente"

AVISO_2020 = (
    "En 2020 la pandemia de COVID-19 redujo la consulta y la notificación. "
    "Este año no se usó para entrenar ni para validar el modelo."
)

CAMPOS_HORIZONTE = [
    "mediana", "b50_inf", "b50_sup", "b95_inf", "b95_sup",
    "wis_modelo", "wis_referencia",
]


def _cadena(serie_ext: Serie, t_real: int, origenes: list[int], h: int) -> dict[int, np.ndarray | None]:
    """Cuantiles calibrados (natural, 23) por origen, o None sin modelo.

    Replica la rama `cqr_r` de `correr_modelo_calibrado` (misma cadencia, mismo
    split de calibracion, mismo umbral de pares) sin ajustar el modelo sin
    calibrar, que aqui no se usa. La unica diferencia es que un origen sin
    modelo devuelve None en vez de un vector plano de persistencia."""
    out: dict[int, np.ndarray | None] = {}
    m_pt: list = []
    fac = np.ones(len(CUANTILES) // 2)
    ultimo = -10_000
    for n, o in enumerate(origenes):
        if n and n % 100 == 0:
            print(f"  h={h}: {n}/{len(origenes)} origenes", flush=True)
        if o - ultimo >= CADENCIA_REAJUSTE or not m_pt:
            X, Y, idx = pares_entrenamiento(serie_ext, o, h, ALCANCE_HISTORIA)
            if len(Y) < MIN_PROPER + MIN_CAL:
                out[o] = None
                continue
            orden = np.argsort([serie_ext.fecha[k] for k in idx])
            i_tr, i_ca = orden[: len(orden) - N_CAL], orden[len(orden) - N_CAL:]
            m_pt = _fit_q(X[i_tr], Y[i_tr])
            qca = np.sort(np.column_stack([m.predict(X[i_ca]) for m in m_pt]), axis=1)
            fac = _ajustes_cqr_r(qca, Y[i_ca])
            ultimo = o
        x = features_en(serie_ext, o, h)
        if x is None:
            out[o] = None
            continue
        qz = np.sort(np.array([m.predict(x.reshape(1, -1))[0] for m in m_pt]))
        out[o] = _qs_calibrado_cqr_r(qz, fac)
    return out


def _horizonte(args: tuple[Serie, Serie, int, int]) -> dict:
    """Trabajo de un horizonte: las dos cadenas, la referencia y el nombre del
    baseline decisivo (el mas fuerte en los origenes de prueba, igual que en
    el experimento)."""
    serie, serie_ext, t_real, h = args
    threadpool_limits(HILOS_POR_PROCESO)
    prueba = origenes_de_prueba(serie, h, ALCANCE_HISTORIA)
    set_prueba = set(prueba)
    resto = [o for o in range(t_real - 1) if o not in set_prueba]

    q = _cadena(serie_ext, t_real, prueba, h)
    q.update(_cadena(serie_ext, t_real, resto, h))

    baselines = {
        "persistencia_rw": baseline_persistencia,
        "climatologia_estacional": baseline_climatologia,
        "persistencia_estacional": baseline_persistencia_estacional,
    }
    en_prueba = {k: f(serie, prueba, h, ALCANCE_HISTORIA) for k, f in baselines.items()}
    decisivo = min(en_prueba, key=lambda k: en_prueba[k]["wis_por_pred"].mean())

    # la referencia se evalua donde hay prediccion y objetivo observado
    con_obs = [o for o, qs in sorted(q.items()) if qs is not None and o + h < t_real]
    ref = baselines[decisivo](serie, con_obs, h, ALCANCE_HISTORIA)
    q_ref = {o: ref["qs"][k] for k, o in enumerate(con_obs)}

    return {"h": h, "q": q, "q_ref": q_ref, "decisivo": decisivo}


def _r(v: float) -> float:
    return round(float(v), 1)


def verificar_contra_publicado(serie: Serie, por_h: dict, publicado: dict) -> None:
    hb = HORIZONTE_BACKTEST
    prueba = origenes_de_prueba(serie, hb, ALCANCE_HISTORIA)
    qs = [por_h[hb]["q"][o] for o in prueba]
    if any(q is None for q in qs):
        raise SystemExit(f"ERROR: h={hb}: hay origenes de prueba sin modelo")
    y = np.array([serie.casos[o + hb] for o in prueba])
    anio = np.array([int(serie.anio[o + hb]) for o in prueba])
    wm = np.array([wis(yy, q) for yy, q in zip(y, qs)])
    ref = baseline_persistencia(serie, prueba, hb, ALCANCE_HISTORIA)
    pub = publicado["desempeno"]
    if pub["baseline"] != "persistencia_rw":
        raise SystemExit(f"ERROR: el baseline publicado es {pub['baseline']}, no persistencia_rw")
    wr = ref["wis_por_pred"]
    qs_arr = np.sort(np.array(qs), axis=1)
    mio = {
        "wis_modelo": round(float(wm.mean()), 1),
        "wis_baseline": round(float(wr.mean()), 1),
        "cobertura_50": round(float(np.mean((y >= qs_arr[:, IDX_B50[0]]) & (y <= qs_arr[:, IDX_B50[1]]))), 3),
        "cobertura_95": round(float(np.mean((y >= qs_arr[:, IDX_B95[0]]) & (y <= qs_arr[:, IDX_B95[1]]))), 3),
    }
    for a in ANIOS_PRUEBA:
        m = anio == a
        mio[f"skill_{a}"] = round(1.0 - wm[m].mean() / wr[m].mean(), 3)
    suyo = {k: pub[k] for k in ("wis_modelo", "wis_baseline", "cobertura_50", "cobertura_95")}
    suyo.update({f"skill_{a}": pub["skill_por_anio"][str(a)] for a in ANIOS_PRUEBA})
    tolerancia = {"wis_modelo": 0.5, "wis_baseline": 0.0, "cobertura_50": 0.01, "cobertura_95": 0.01}
    fuera = {k: (mio[k], suyo[k]) for k in suyo
             if abs(mio[k] - suyo[k]) > tolerancia.get(k, 0.01)}

    dif = []
    for q, p in zip(qs_arr, publicado["backtest"]["puntos"]):
        dif.append(max(abs(q[IDX_MEDIANA] - p["mediana"]),
                       abs(q[IDX_B50[0]] - p["banda_50"][0]), abs(q[IDX_B50[1]] - p["banda_50"][1]),
                       abs(q[IDX_B95[0]] - p["banda_95"][0]), abs(q[IDX_B95[1]] - p["banda_95"][1])))
    dif = np.array(dif)
    print(f"  h={hb}: desempeno {mio}")
    print(f"  diferencia punto a punto con el backtest publicado: "
          f"{int((dif > 0.05).sum())} de {len(dif)} puntos distintos, maxima {dif.max():.1f} casos")
    if fuera:
        raise SystemExit(f"ERROR: el desempeno no reproduce el publicado (crudo en {CRUDO}): {fuera}")
    print("  [ok] desempeno publicado reproducido")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--desde-crudo", action="store_true",
                   help="reutiliza el resultado crudo de la ultima corrida en vez de reajustar")
    args = p.parse_args()

    conn = get_connection()
    try:
        serie = cargar_serie(conn)
    finally:
        conn.close()

    serie_ext, t_real = _extender_serie_futuro(serie, max(HORIZONTES))

    if args.desde_crudo:
        por_h = pickle.loads(CRUDO.read_bytes())
    else:
        # un proceso por horizonte
        with ProcessPoolExecutor(max_workers=len(HORIZONTES)) as ex:
            por_h = {r["h"]: r for r in ex.map(
                _horizonte, [(serie, serie_ext, t_real, h) for h in HORIZONTES])}
        CRUDO.parent.mkdir(parents=True, exist_ok=True)
        CRUDO.write_bytes(pickle.dumps(por_h))

    # Verificacion contra el artefacto publicado, a h = 4 en los origenes de
    # prueba. El ajuste no es reproducible bit a bit entre corridas (sumas de
    # OpenMP en coma flotante; con el propio nowcast_estimacion_dengue.py
    # tampoco), y una diferencia en la ultima cifra puede mover un factor
    # CQR-r, que se elige por cuantil. Por eso se exige que el desempeno
    # publicado se reproduzca con su redondeo y se reporta la mayor diferencia
    # punto a punto.
    publicado = json.loads(SALIDA_PRINCIPAL.read_text(encoding="utf-8"))
    verificar_contra_publicado(serie, por_h, publicado)

    origenes = []
    acumulado: dict[tuple[int, int], dict[str, list]] = {}
    for o in range(t_real - 1):
        fila = {
            "fecha": serie.fecha[o].isoformat(),
            "anio": int(serie.anio[o]),
            "semana": int(serie.semana[o]),
        }
        hs = []
        for h in HORIZONTES:
            qs = por_h[h]["q"].get(o)
            if qs is None:
                hs.append(None)
                continue
            qs = np.sort(qs)
            valores = [_r(qs[IDX_MEDIANA]), _r(qs[IDX_B50[0]]), _r(qs[IDX_B50[1]]),
                       _r(qs[IDX_B95[0]]), _r(qs[IDX_B95[1]])]
            tgt = o + h
            if tgt < t_real:
                y = float(serie.casos[tgt])
                wm = wis(y, qs)
                wr = wis(y, np.sort(por_h[h]["q_ref"][o]))
                valores += [_r(wm), _r(wr)]
                clave = (int(serie.anio[tgt]), h)
                a = acumulado.setdefault(clave, {"wm": [], "wr": [], "c50": [], "c95": []})
                a["wm"].append(wm)
                a["wr"].append(wr)
                a["c50"].append(qs[IDX_B50[0]] <= y <= qs[IDX_B50[1]])
                a["c95"].append(qs[IDX_B95[0]] <= y <= qs[IDX_B95[1]])
            else:
                valores += [None, None]
            hs.append(valores)
        if all(v is None for v in hs):
            fila["motivo"] = MOTIVO_HISTORIA
        else:
            fila["h"] = hs
        origenes.append(fila)

    # resumen por anio del objetivo y horizonte (2020 incluido, marcado aparte)
    resumen: dict[str, dict[str, dict]] = {}
    for (anio, h), a in sorted(acumulado.items()):
        wm, wr = float(np.mean(a["wm"])), float(np.mean(a["wr"]))
        resumen.setdefault(str(anio), {})[str(h)] = {
            "n": len(a["wm"]),
            "wis_modelo": _r(wm),
            "wis_referencia": _r(wr),
            "skill": round(1.0 - wm / wr, 3) if wr > 0 else None,
            "cobertura_50": round(float(np.mean(a["c50"])), 3),
            "cobertura_95": round(float(np.mean(a["c95"])), 3),
        }

    primera = next(f for f in origenes if "h" in f)
    artefacto = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente_serie": "opendengue_v1_3",
        "metodo": publicado["metodo"],
        "alcance_historia_desde": ALCANCE_HISTORIA,
        "horizontes": HORIZONTES,
        "anios_prueba": list(ANIOS_PRUEBA),
        "anio_excluido": ANIO_EXCLUIDO,
        "aviso_anio_excluido": AVISO_2020,
        "referencia_por_horizonte": {str(h): por_h[h]["decisivo"] for h in HORIZONTES},
        "primera_semana_con_prediccion": {
            "fecha": primera["fecha"], "anio": primera["anio"], "semana": primera["semana"],
        },
        "campos_horizonte": CAMPOS_HORIZONTE,
        "observado": [[serie.fecha[i].isoformat(), _r(serie.casos[i])] for i in range(t_real)],
        "origenes": origenes,
        "resumen_por_anio": resumen,
    }

    SALIDA.write_text(json.dumps(artefacto, ensure_ascii=False, separators=(",", ":")),
                      encoding="utf-8")
    print(f"artefacto -> {SALIDA} ({SALIDA.stat().st_size / 1024:.0f} KB)")
    print(f"  {len(origenes)} origenes; primera prediccion {primera['fecha']}")
    for anio, porh in resumen.items():
        r4 = porh.get(str(HORIZONTE_BACKTEST))
        if r4:
            print(f"  {anio} h={HORIZONTE_BACKTEST}: WIS {r4['wis_modelo']} vs {r4['wis_referencia']} "
                  f"skill {r4['skill']:+.3f} cob50 {r4['cobertura_50']} cob95 {r4['cobertura_95']}")


if __name__ == "__main__":
    main()
