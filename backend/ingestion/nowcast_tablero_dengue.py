"""
Prediccion de dengue sobre la serie del tablero de MINSAL (desde 2025).

Desde 2025 la serie nacional es la de sospechosos del tablero, que MINSAL
publica como un promedio de varias semanas. El modelo de ADR 0020 se entreno
con los datos crudos de OpenDengue y con esa serie pierde contra la
persistencia de 1 a 5 semanas. Desde la primera semana del tablero la
prediccion publicada es la mezcla C de
docs/experimentos/experimento-nowcast-tendencia.md: promedio por cuantil, en
log1p, de ese modelo y una tendencia amortiguada. 2025 y 2026 se usaron para
elegir C; su prueba son las semanas que MINSAL publique desde 2026-S38
(enmienda del 2026-09-27 en ese documento).

El script no define ningun calculo: M0, T, C y la persistencia suavizada salen
de `experimento_nowcast_tendencia._tarea` (script congelado en 40b6ebb), con
las mismas cadenas que el experimento:

  - origenes cuyo objetivo ya esta publicado: la cadena de la confirmacion del
    experimento de mejora, la que reprodujo la verificacion;
  - origenes cuyo objetivo es una semana de prueba: la cadena de la evaluacion,
    que arranca en el primer origen de prueba de cada horizonte. El abanico
    publicado desde la ultima semana sale de las predicciones que se van a
    puntuar; como en nowcast_estimacion_dengue.py, sus rangos se ensanchan donde
    haga falta para no estrecharse al alargar el horizonte
    (`_monotona_en_horizonte`). Las medianas no cambian.

Entradas:
  backend/api/datos/nowcast_dengue_opendengue.json               nowcast_estimacion_dengue.py
  backend/api/datos/nowcast_dengue_retrospectivo_opendengue.json nowcast_retrospectivo_dengue.py
  data/interim/nowcast/retrospectivo_crudo.pkl                   cuantiles completos de esa corrida

Salidas (las que sirve la API):
  backend/api/datos/nowcast_dengue.json               abanico desde la ultima semana del tablero
                                                      y desempeno a 4 semanas en 2025-2026
  backend/api/datos/nowcast_dengue_retrospectivo.json el retrospectivo de OpenDengue mas los
                                                      origenes del tablero

Los origenes hasta 2024 conservan el modelo de ADR 0020; los que tenian
objetivos en 2025 ganan el WIS contra lo que el tablero publico despues.

Uso:
    cd backend/ingestion
    POSTGRES_HOST=localhost nice -n 10 ../.venv/bin/python nowcast_tablero_dengue.py
    # rehacer solo los JSON a partir de la ultima corrida (~15 min menos):
    POSTGRES_HOST=localhost ../.venv/bin/python nowcast_tablero_dengue.py --desde-crudo
"""

from __future__ import annotations

import argparse
import json
import pickle
from datetime import date, datetime, timezone

import numpy as np

import experimento_nowcast_mejora as mej
import experimento_nowcast_tablero as tab
import experimento_nowcast_tendencia as tend
from experimento_nowcast_corto_plazo import (
    IDX_MEDIANA,
    Serie,
    baseline_climatologia,
    baseline_persistencia,
    baseline_persistencia_estacional,
    cobertura,
    wis,
)
from nowcast_estimacion_dengue import (
    HORIZONTE_BACKTEST,
    HORIZONTES,
    IDX_B50,
    IDX_B95,
    SALIDA as BASE_PRINCIPAL,
    SEMANAS_CONTEXTO,
    _extender_serie_futuro,
    _monotona_en_horizonte,
    _paquete_cuantiles,
)
from nowcast_retrospectivo_dengue import ALCANCE_HISTORIA, CRUDO, MOTIVO_HISTORIA, SALIDA as BASE_RETRO, _r

from db import get_connection

SALIDA = BASE_PRINCIPAL.with_name("nowcast_dengue.json")
SALIDA_RETRO = BASE_PRINCIPAL.with_name("nowcast_dengue_retrospectivo.json")
CRUDO_TABLERO = CRUDO.with_name("tablero_crudo.pkl")

INICIO_TABLERO = date(2024, 12, 29)  # 2025-S1, primera semana del tablero en la serie mixta
ANIOS_TABLERO = (2025, 2026)
MOTIVO_HUECO = "hueco_en_serie"
REFERENCIA = "persistencia_suavizada"
METODO = ("Mezcla por cuantil, en log1p y con peso 0,5, del modelo de ADR 0020 "
          "(HistGradientBoosting quantile + CQR-r) y una tendencia amortiguada")
NOTA_ALCANCE = (
    "Desde 2025 la serie es la del tablero de MINSAL, que publica cada semana como "
    "un promedio de varias. La predicción combina el modelo validado con OpenDengue "
    "y una tendencia amortiguada. 2025 y 2026 sirvieron para elegir ese método; la "
    "prueba con semanas nuevas empieza en la semana 38 de 2026."
)

BASELINES = {
    "persistencia_rw": baseline_persistencia,
    "climatologia_estacional": baseline_climatologia,
    "persistencia_estacional": baseline_persistencia_estacional,
}


def _num(v: float) -> float | None:
    return _r(v) if np.isfinite(v) else None


def cargar(conn) -> tuple[Serie, int]:
    """Serie mixta extendida con las semanas futuras, con el calendario
    epidemiologico real en esas semanas cuando la base ya lo tiene."""
    serie = tab.cargar_serie_mixta(conn)
    ext, t_real = _extender_serie_futuro(serie, max(HORIZONTES))
    cur = conn.cursor()
    cur.execute(
        "SELECT fecha_inicio, anio, semana_epi FROM semanas_epidemiologicas "
        "WHERE fecha_inicio > %s ORDER BY fecha_inicio LIMIT %s",
        (serie.fecha[-1], max(HORIZONTES)),
    )
    for k, (f, a, w) in enumerate(cur.fetchall()):
        assert f == ext.fecha[t_real + k], f"calendario distinto en {f}"
        ext.anio[t_real + k], ext.semana[t_real + k] = a, w
    return ext, t_real


def predecir(serie: Serie, t_real: int) -> dict[tuple[int, int], dict]:
    """(origen, h) -> fila de `tend._tarea` con q_C y la persistencia suavizada."""
    i_prueba = int(np.searchsorted(serie.fecha, tend.INICIO_PRUEBA))
    tareas = []
    for h in HORIZONTES:
        vistos = tend._origenes_en_fase(serie, h, mej.ANIOS_CONFIRMACION, mej.ANIOS_CONFIRMACION)
        prueba = [o for o in range(i_prueba - h, t_real)
                  if tab.features_sin_hueco(serie, o, h) is not None]
        for origenes in (vistos, prueba):
            y = {o: float(serie.casos[o + h]) for o in origenes}
            tareas.append((serie, h, origenes, y, "tablero"))
    idx = {str(f): k for k, f in enumerate(serie.fecha)}
    pred: dict[tuple[int, int], dict] = {}
    for r in tend.correr(tareas):
        for f in r["filas"]:
            f["h"] = r["h"]
            pred[(idx[f["origen"]], r["h"])] = f
    return pred


def _valores(q: np.ndarray, wm: float | None, wr: float | None) -> list:
    q = np.sort(q)
    return [_r(q[IDX_MEDIANA]), _r(q[IDX_B50[0]]), _r(q[IDX_B50[1]]),
            _r(q[IDX_B95[0]]), _r(q[IDX_B95[1]]), wm, wr]


def _resumen(filas: list[dict]) -> dict:
    y = np.array([f["y"] for f in filas])
    qs = np.array([f["q_C"] for f in filas])
    wm = float(np.mean([f["wis_C"] for f in filas]))
    wr = float(np.mean([f["wis_ref_suavizada"] for f in filas]))
    return {
        "n": len(filas),
        "wis_modelo": _r(wm),
        "wis_referencia": _r(wr),
        "skill": round(1.0 - wm / wr, 3) if wr > 0 else None,
        "cobertura_50": round(cobertura(y, qs, *IDX_B50), 3),
        "cobertura_95": round(cobertura(y, qs, *IDX_B95), 3),
    }


def _observadas(pred: dict, i_tablero: int, h: int | None = None) -> list[dict]:
    """Filas de C con objetivo ya publicado, desde la primera semana del tablero."""
    return [f for (o, hh), f in sorted(pred.items())
            if o >= i_tablero and (h is None or hh == h) and np.isfinite(f["y"])]


def principal(serie: Serie, t_real: int, pred: dict, i_tablero: int) -> dict:
    ancla = t_real - 1
    qs = []
    for h in HORIZONTES:
        f = pred.get((ancla, h))
        if f is None:
            raise SystemExit(f"Sin prediccion desde la ultima semana a h={h}: revisar clima y huecos.")
        qs.append(np.sort(f["q_C"]))
    qs = np.array(qs)
    q_mono = _monotona_en_horizonte(qs[:, IDX_MEDIANA], qs)
    estimacion = []
    for k, h in enumerate(HORIZONTES):
        t = ancla + h
        estimacion.append({"h": h, "fecha": serie.fecha[t].isoformat(), "anio": int(serie.anio[t]),
                           "semana": int(serie.semana[t]), **_paquete_cuantiles(q_mono[k])})

    filas = _observadas(pred, i_tablero, HORIZONTE_BACKTEST)
    puntos = []
    for f in sorted(filas, key=lambda f: f["objetivo"]):
        q = np.sort(f["q_C"])
        puntos.append({
            "fecha": f["objetivo"], "anio": f["anio"], "observado": _r(f["y"]),
            "mediana": _r(q[IDX_MEDIANA]),
            "banda_50": [_r(q[IDX_B50[0]]), _r(q[IDX_B50[1]])],
            "banda_95": [_r(q[IDX_B95[0]]), _r(q[IDX_B95[1]])],
        })
    total = _resumen(filas)
    por_anio = {a: _resumen([f for f in filas if f["anio"] == a]) for a in ANIOS_TABLERO}
    desempeno = {
        "horizonte": HORIZONTE_BACKTEST,
        "baseline": REFERENCIA,
        "wis_modelo": total["wis_modelo"],
        "wis_baseline": total["wis_referencia"],
        "reduccion_wis": total["skill"],
        "skill_medio_por_anio": round(float(np.mean([r["skill"] for r in por_anio.values()])), 3),
        "skill_por_anio": {a: r["skill"] for a, r in por_anio.items()},
        "anios_ganados": sum(1 for r in por_anio.values() if r["skill"] >= 0),
        "n_anios": len(por_anio),
        "cobertura_50": total["cobertura_50"],
        "cobertura_95": total["cobertura_95"],
        "dentro_de_muestra": True,
    }
    obs = range(max(0, t_real - SEMANAS_CONTEXTO), t_real)
    return {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente_serie": "minsal_tablero",
        "metodo": METODO,
        "alcance_historia_desde": ALCANCE_HISTORIA,
        "ancla": {"fecha": serie.fecha[ancla].isoformat(), "anio": int(serie.anio[ancla]),
                  "semana": int(serie.semana[ancla]), "casos": _r(serie.casos[ancla])},
        "horizontes": HORIZONTES,
        "observado": [{"fecha": serie.fecha[i].isoformat(), "casos": _num(serie.casos[i])} for i in obs],
        "estimacion": estimacion,
        "backtest": {"horizonte": HORIZONTE_BACKTEST, "anios": list(ANIOS_TABLERO), "puntos": puntos},
        "desempeno": desempeno,
        "prueba": _prueba(serie),
        "nota_alcance": NOTA_ALCANCE,
    }


def _prueba(serie: Serie) -> dict:
    k = int(np.searchsorted(serie.fecha, tend.INICIO_PRUEBA))
    return {
        "inicio": {"fecha": tend.INICIO_PRUEBA.isoformat(), "anio": int(serie.anio[k]), "semana": int(serie.semana[k])},
        "semanas": tend.SEMANAS_PRUEBA,
        "horizontes_decisivos": list(tend.H_DECISIVOS),
        "referencia": REFERENCIA,
    }


def retrospectivo(serie: Serie, t_real: int, pred: dict, i_tablero: int) -> dict:
    base = json.loads(BASE_RETRO.read_text(encoding="utf-8"))
    base_principal = json.loads(BASE_PRINCIPAL.read_text(encoding="utf-8"))
    # el crudo lo escribe nowcast_retrospectivo_dengue.py en esta misma maquina
    crudo = pickle.loads(CRUDO.read_bytes())

    # la base de OpenDengue termina justo antes del tablero y coincide con la serie mixta
    assert len(base["observado"]) == i_tablero, "la base no termina en 2024-S52"
    for k, (f, c) in enumerate(base["observado"]):
        assert f == serie.fecha[k].isoformat() and c == _r(serie.casos[k]), f"observado distinto en {f}"
    assert base_principal["ancla"]["fecha"] == serie.fecha[i_tablero - 1].isoformat()
    for k, fila in enumerate(base["origenes"]):
        for h, v in zip(HORIZONTES, fila.get("h", [])):
            if v is not None:
                q = np.sort(crudo[h]["q"][k])
                assert v[:5] == _valores(q, None, None)[:5], f"el crudo no es el de la base en {fila['fecha']}"

    def referencia(o: int, h: int, y: float) -> float:
        nombre = base["referencia_por_horizonte"][str(h)]
        return wis(y, np.sort(BASELINES[nombre](serie, [o], h, ALCANCE_HISTORIA)["qs"][0]))

    origenes = base["origenes"]
    # origenes de OpenDengue cuyo objetivo cae en el tablero: WIS contra lo publicado despues
    for k, fila in enumerate(origenes):
        for j, (h, v) in enumerate(zip(HORIZONTES, fila.get("h", []))):
            t = k + h
            if v is not None and t >= i_tablero and np.isfinite(serie.casos[t]):
                y = float(serie.casos[t])
                fila["h"][j] = _valores(crudo[h]["q"][k], _r(wis(y, np.sort(crudo[h]["q"][k]))), _r(referencia(k, h, y)))

    # la ultima semana de OpenDengue era el ancla: su abanico es la estimacion publicada
    o = i_tablero - 1
    hs = []
    for e in base_principal["estimacion"]:
        t, q = o + e["h"], np.array(e["cuantiles"])
        y = float(serie.casos[t])
        hs.append(_valores(q, _r(wis(y, q)), _r(referencia(o, e["h"], y))) if np.isfinite(y)
                  else _valores(q, None, None))
    origenes.append({"fecha": serie.fecha[o].isoformat(), "anio": int(serie.anio[o]),
                     "semana": int(serie.semana[o]), "h": hs})

    # origenes del tablero con C; la ultima semana es la estimacion del artefacto principal
    for o in range(i_tablero, t_real - 1):
        fila = {"fecha": serie.fecha[o].isoformat(), "anio": int(serie.anio[o]), "semana": int(serie.semana[o])}
        hs = []
        for h in HORIZONTES:
            f = pred.get((o, h))
            if f is None:
                hs.append(None)
            elif np.isfinite(f["y"]):
                hs.append(_valores(np.array(f["q_C"]), _r(f["wis_C"]), _r(f["wis_ref_suavizada"])))
            else:
                hs.append(_valores(np.array(f["q_C"]), None, None))
        if all(v is None for v in hs):
            assert tab.features_sin_hueco(serie, o, 1) is None, f"origen {serie.fecha[o]} sin prediccion"
            fila["motivo"] = MOTIVO_HUECO
        else:
            fila["h"] = hs
        origenes.append(fila)

    resumen = dict(base["resumen_por_anio"])
    filas = _observadas(pred, i_tablero)
    for a in ANIOS_TABLERO:
        resumen[str(a)] = {}
        for h in HORIZONTES:
            fa = [f for f in filas if f["anio"] == a and f["h"] == h]
            if fa:
                resumen[str(a)][str(h)] = _resumen(fa)

    return {
        **base,
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fuente_serie": "opendengue_v1_3+minsal_tablero",
        "observado": [[serie.fecha[i].isoformat(), _num(serie.casos[i])] for i in range(t_real)],
        "origenes": origenes,
        "resumen_por_anio": resumen,
        "tablero": {
            "inicio": {"fecha": INICIO_TABLERO.isoformat(), "anio": int(serie.anio[i_tablero]),
                       "semana": int(serie.semana[i_tablero])},
            "metodo": METODO,
            "referencia": REFERENCIA,
            "anios": list(ANIOS_TABLERO),
            "prueba": _prueba(serie),
        },
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--desde-crudo", action="store_true",
                   help="reutiliza las predicciones de la ultima corrida en vez de recalcularlas")
    args = p.parse_args()
    for ruta in (BASE_PRINCIPAL, BASE_RETRO, CRUDO):
        if not ruta.exists():
            raise SystemExit(f"Falta {ruta}: correr antes nowcast_estimacion_dengue.py y nowcast_retrospectivo_dengue.py.")
    conn = get_connection()
    try:
        serie, t_real = cargar(conn)
    finally:
        conn.close()
    i_tablero = int(np.searchsorted(serie.fecha, INICIO_TABLERO))
    assert serie.fecha[i_tablero] == INICIO_TABLERO

    if args.desde_crudo:
        # lo escribe este mismo script en esta maquina
        guardado = pickle.loads(CRUDO_TABLERO.read_bytes())
        if guardado["ultima"] != serie.fecha[t_real - 1].isoformat():
            raise SystemExit("La serie tiene semanas nuevas desde la ultima corrida: correr sin --desde-crudo.")
        pred = guardado["pred"]
    else:
        pred = predecir(serie, t_real)
        CRUDO_TABLERO.write_bytes(pickle.dumps({"ultima": serie.fecha[t_real - 1].isoformat(), "pred": pred}))

    art = principal(serie, t_real, pred, i_tablero)
    retro = retrospectivo(serie, t_real, pred, i_tablero)
    SALIDA.write_text(json.dumps(art, indent=2, ensure_ascii=False), encoding="utf-8")
    SALIDA_RETRO.write_text(json.dumps(retro, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"artefacto -> {SALIDA}")
    print(f"  ancla {art['ancla']['fecha']}  casos={art['ancla']['casos']}")
    for e in art["estimacion"]:
        print(f"  h={e['h']}  mediana={e['mediana']:8.1f}  "
              f"50%[{e['banda_50'][0]:.0f}, {e['banda_50'][1]:.0f}]  "
              f"95%[{e['banda_95'][0]:.0f}, {e['banda_95'][1]:.0f}]")
    d = art["desempeno"]
    print(f"  h={d['horizonte']} en 2025-2026 (anios usados para elegir C): WIS {d['wis_modelo']} vs "
          f"{d['wis_baseline']} ({d['baseline']}), skill {d['reduccion_wis']:+.3f}, "
          f"por anio {d['skill_por_anio']}, cob50={d['cobertura_50']} cob95={d['cobertura_95']}")
    print(f"retrospectivo -> {SALIDA_RETRO} ({SALIDA_RETRO.stat().st_size / 1024:.0f} KB), "
          f"{len(retro['origenes'])} origenes")
    for a in ANIOS_TABLERO:
        for h in (1, 4, 8):
            r = retro["resumen_por_anio"][str(a)].get(str(h))
            if r:
                print(f"  {a} h={h}: n={r['n']} skill {r['skill']:+.3f} cob50 {r['cobertura_50']} cob95 {r['cobertura_95']}")


if __name__ == "__main__":
    main()
