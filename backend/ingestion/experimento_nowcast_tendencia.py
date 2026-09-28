"""
Experimento de prediccion de dengue con la serie suavizada del tablero
(docs/experimentos/experimento-nowcast-tendencia.md, firmado 2026-09-27).

La serie del tablero de MINSAL es un promedio de varias semanas; el modelo
publicado se entreno con datos crudos. Tres modelos sobre la serie mixta:

  M0  el modelo publicado, sin cambios (control).
  T   tendencia amortiguada en log1p, con los errores aprendidos de la historia
      promediada a 7 semanas. Componente de C; se reporta pero no compite.
  C   candidato: promedio por cuantil, en log1p, de M0 y T con peso fijo 0,5.

El criterio es contra la persistencia suavizada (errores de la historia
promediada); la persistencia limpia del experimento de mejora se reporta al lado.

La prueba es prospectiva: semanas objetivo desde 2026-S38, que no estaban
publicadas al firmar. Dos modos:

  --verificar   controles sobre 2024-2026 hasta 2026-S37 (ya vistos): M0 debe
                reproducir los cuantiles del experimento de mejora y T y C las
                cifras de la exploracion. Nunca mira una semana de prueba.
  --evaluar     la evaluacion firmada, una sola vez. Se niega a correr antes de
                que esten publicadas 20 semanas de prueba, si el script tiene
                cambios sin commit o si la evaluacion ya existe.

Uso:
    cd backend/ingestion
    POSTGRES_HOST=localhost nice -n 10 ../.venv/bin/python experimento_nowcast_tendencia.py --verificar
    POSTGRES_HOST=localhost nice -n 10 ../.venv/bin/python experimento_nowcast_tendencia.py --evaluar
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

import cargar_minsal_tablero as cmt
import experimento_nowcast_corto_plazo as exp
import experimento_nowcast_mejora as mej
import experimento_nowcast_tablero as tab
from experimento_nowcast_corto_plazo import ANIO_EXCLUIDO, CUANTILES, Serie, cobertura, wis
from nowcast_estimacion_dengue import ALCANCE_HISTORIA, HORIZONTES, IDX_B50, IDX_B95

from db import get_connection

# parametros firmados
K_HISTORIA = 7  # semanas del promedio con que se reescribe la historia hasta 2023
PHI = 0.8  # amortiguacion de la tendencia
V_PENDIENTE = 3  # semanas para medir la pendiente
PESO_M0 = 0.5
H_DECISIVOS = (4, 8)
COB95_MIN = 0.85
INICIO_PRUEBA = date(2026, 9, 20)  # 2026-S38, la primera semana no publicada al firmar
SEMANAS_PRUEBA = 20
PROCESOS = 4  # un hilo cada uno: la maquina se calienta con 8

DIR = Path(__file__).parent / "data" / "interim" / "nowcast"
SALIDA_VERIFICACION = DIR / "tendencia_verificacion.json"
SALIDA_PRUEBA = DIR / "tendencia_prueba.json"

# skill agrupado 2024-2026 contra la persistencia suavizada en la exploracion
# previa a la firma (M0, T, C); --verificar debe reproducirlo
EXPLORACION = {
    1: (-0.79, 0.19, -0.08), 2: (-0.33, 0.19, 0.09), 3: (-0.20, 0.16, 0.12), 4: (-0.19, 0.15, 0.12),
    5: (-0.05, 0.13, 0.17), 6: (0.05, 0.11, 0.19), 7: (0.12, 0.08, 0.20), 8: (0.19, 0.06, 0.21),
}
MODELOS = ("M0", "T", "C")


# --- historia promediada y reglas ------------------------------------------


def historia_promediada(serie: Serie) -> Serie:
    """Cada semana hasta 2023 pasa a ser el promedio de las K_HISTORIA semanas
    que terminan en ella, para que la historia tenga la forma del tablero. Los
    0 de OpenDengue entran como dato. Desde 2024 la serie ya viene promediada."""
    s = copy.deepcopy(serie)
    x = serie.casos
    prom = np.array([np.nanmean(x[max(0, t - K_HISTORIA + 1): t + 1]) for t in range(len(x))])
    s.casos = np.where(serie.anio <= 2023, prom, serie.casos)
    s.z = np.log1p(s.casos)
    return s


def _mediana_regla(s: Serie, t: np.ndarray | int, h: int, phi: float):
    # con phi = 0 es la persistencia, sobre los mismos pares que la tendencia
    return s.z[t] + (s.z[t] - s.z[t - V_PENDIENTE]) / V_PENDIENTE * sum(phi ** i for i in range(1, h + 1))


def cuantiles_regla(s: Serie, o: int, h: int, phi: float) -> np.ndarray | None:
    """Mediana de la regla mas los cuantiles empiricos de sus errores en los
    pares con objetivo anterior al origen, desde ALCANCE_HISTORIA y sin 2020."""
    centro = _mediana_regla(s, o, h, phi)
    if not np.isfinite(centro):
        return None
    ts = np.arange(V_PENDIENTE, s.T - h)
    ok = ((s.fecha[ts + h] < s.fecha[o]) & (s.anio[ts + h] >= ALCANCE_HISTORIA)
          & (s.anio[ts + h] != ANIO_EXCLUIDO)).astype(bool)
    ts = ts[ok]
    d = s.z[ts + h] - _mediana_regla(s, ts, h, phi)
    d = d[np.isfinite(d)]
    return np.clip(np.expm1(centro + np.quantile(d, CUANTILES)), 0, None)


# --- predicciones ------------------------------------------------------------


def _tarea(args: tuple) -> dict:
    """Un horizonte (y, en la sensibilidad por captura, un grupo de origenes).
    `serie` da los datos para predecir; `y_por_origen`, lo observado."""
    serie, h, origenes, y_por_origen, etiqueta = args
    threadpool_limits(1)
    tab._instalar_parches()
    afect = mej.semanas_afectadas(serie)
    prom = historia_promediada(serie)
    q0 = mej.cadena(serie, origenes, h, ("M0",))
    filas, sin_prediccion = [], 0
    for o in origenes:
        qt = cuantiles_regla(prom, o, h, PHI)
        rs = cuantiles_regla(prom, o, h, 0.0)
        if q0[o] is None or qt is None or rs is None:
            sin_prediccion += 1
            continue
        qs = {"M0": q0[o]["M0"], "T": qt}
        qs["C"] = mej._mezcla(qs["M0"], qs["T"], PESO_M0)
        y = y_por_origen[o]
        fila = {"origen": str(serie.fecha[o]), "objetivo": str(serie.fecha[o + h]),
                "anio": int(serie.anio[o + h]), "semana": int(serie.semana[o + h]), "y": y,
                "wis_ref_suavizada": wis(y, rs),
                "wis_ref_limpia": wis(y, mej.referencia("persistencia_rw", serie, o, h, afect))}
        for m in MODELOS:
            fila[f"q_{m}"] = qs[m].tolist()
            fila[f"wis_{m}"] = wis(y, qs[m])
        filas.append(fila)
    return {"h": h, "etiqueta": etiqueta, "filas": filas, "sin_prediccion": sin_prediccion}


def metricas(filas: list[dict], modelo: str, ref: str) -> dict:
    y = np.array([f["y"] for f in filas])
    qs = np.array([f[f"q_{modelo}"] for f in filas])
    w = np.mean([f[f"wis_{modelo}"] for f in filas])
    w_ref = np.mean([f[f"wis_ref_{ref}"] for f in filas])
    por_anio = {}
    for a in sorted({f["anio"] for f in filas}):
        fa = [f for f in filas if f["anio"] == a]
        por_anio[a] = round(float(1 - np.mean([f[f"wis_{modelo}"] for f in fa])
                                  / np.mean([f[f"wis_ref_{ref}"] for f in fa])), 3)
    return {
        "n": len(filas),
        "wis": float(w),
        "wis_referencia": float(w_ref),
        "skill": float(1 - w / w_ref),
        "skill_por_anio": por_anio,
        "cobertura_50": cobertura(y, qs, *IDX_B50),
        "cobertura_95": cobertura(y, qs, *IDX_B95),
        "bajo_mediana": float(np.mean(y < qs[:, len(CUANTILES) // 2])),
    }


def tablas(res: dict[int, dict], filtro=lambda f: True) -> dict:
    return {ref: {h: {m: metricas([f for f in r["filas"] if filtro(f)], m, ref) for m in MODELOS}
                  for h, r in sorted(res.items())}
            for ref in ("suavizada", "limpia")}


def imprimir(titulo: str, t: dict) -> None:
    print(f"\n{titulo}")
    print(f"{'h':>2} {'modelo':<6}{'n':>5}{'skill':>8}  por anio{'':<22}{'cob50':>7}{'cob95':>7}{'bajo':>7}{'WIS':>8}{'WIS ref':>8}")
    for h, porm in t.items():
        for m, r in porm.items():
            anios = " ".join(f"{a}:{v:+.2f}" for a, v in r["skill_por_anio"].items())
            print(f"{h:>2} {m:<6}{r['n']:>5}{r['skill']:>+8.2f}  {anios:<30}{r['cobertura_50']:>7.2f}"
                  f"{r['cobertura_95']:>7.2f}{r['bajo_mediana']:>7.2f}{r['wis']:>8.1f}{r['wis_referencia']:>8.1f}")


def correr(tareas: list[tuple]) -> list[dict]:
    with ProcessPoolExecutor(max_workers=PROCESOS) as ex:
        return list(ex.map(_tarea, tareas))


# --- verificacion (solo semanas ya vistas) ---------------------------------


def _origenes_en_fase(serie: Serie, h: int, anios_cadena: tuple[int, ...], anios_obj: tuple[int, ...]) -> list[int]:
    """Origenes de la cadena del experimento de mejora que cubrio `anios_obj`,
    desde el ultimo reajuste anterior al primer objetivo de esos anios. El
    modelo se reajusta cada CADENCIA_REAJUSTE origenes: arrancar en la misma
    fase reproduce los mismos cuantiles. Nunca incluye semanas de prueba."""
    lista = mej.origenes_de(serie, h, anios_cadena)
    reajustes, ultimo = [], -10_000
    for o in lista:
        if not reajustes or o - ultimo >= exp.CADENCIA_REAJUSTE:
            reajustes.append(o)
            ultimo = o
    primero = next(o for o in lista if serie.anio[o + h] in anios_obj)
    inicio = max(r for r in reajustes if r <= primero)
    return [o for o in lista if o >= inicio and serie.fecha[o + h] < INICIO_PRUEBA]


def verificar(serie: Serie) -> None:
    # 2024 salio de la cadena de la validacion (2019-2024); 2025-2026, de la confirmacion
    cadenas = ((mej.ANIOS_VALIDACION, (2024,)), (mej.ANIOS_CONFIRMACION, mej.ANIOS_CONFIRMACION))
    tareas = []
    for h in HORIZONTES:
        for anios_cadena, anios_obj in cadenas:
            os_ = _origenes_en_fase(serie, h, anios_cadena, anios_obj)
            tareas.append((serie, h, os_, {o: float(serie.casos[o + h]) for o in os_}, "verificacion"))
    exp.verificar_sin_fuga(serie, _origenes_en_fase(serie, 4, *cadenas[1]), 4, ALCANCE_HISTORIA)
    res: dict[int, dict] = {}
    for r in correr(tareas):
        d = res.setdefault(r["h"], {"h": r["h"], "filas": [], "sin_prediccion": 0})
        d["filas"] += [f for f in r["filas"] if f["anio"] >= 2024]
        d["sin_prediccion"] += r["sin_prediccion"]
    t = tablas(res)
    imprimir("Verificacion 2024-2026 (hasta 2026-S37), contra la persistencia suavizada", t["suavizada"])
    imprimir("Verificacion 2024-2026 (hasta 2026-S37), contra la persistencia limpia", t["limpia"])

    # M0 contra el experimento de mejora: 2024 de la validacion, 2025-2026 de la confirmacion
    val = json.loads(mej.SALIDA_VALIDACION.read_text(encoding="utf-8"))["detalle"]
    conf = json.loads(mej.SALIDA_CONFIRMACION.read_text(encoding="utf-8"))["detalle"]
    m0_igual, comparados = True, 0
    for h, r in res.items():
        previo = {f["origen"]: f["q_M0"] for f in val[str(h)]["filas"] + conf[str(h)]["filas"]}
        for f in r["filas"]:
            if f["origen"] in previo:
                comparados += 1
                m0_igual &= np.array_equal(np.array(f["q_M0"]), np.array(previo[f["origen"]]))
    print(f"\nM0 contra el experimento de mejora: {comparados} predicciones, "
          f"{'cuantiles identicos' if m0_igual else 'DISTINTOS'}")

    difs = {h: [abs(t["suavizada"][h][m]["skill"] - EXPLORACION[h][i]) for i, m in enumerate(MODELOS)]
            for h in HORIZONTES}
    explor_ok = all(d < 0.006 for v in difs.values() for d in v)
    print(f"T, C y M0 contra la exploracion: diferencia maxima de skill "
          f"{max(max(v) for v in difs.values()):.3f} ({'coincide' if explor_ok else 'NO COINCIDE'})")

    DIR.mkdir(parents=True, exist_ok=True)
    SALIDA_VERIFICACION.write_text(json.dumps({
        "tablas": t, "m0_identico_a_mejora": bool(m0_igual), "m0_comparados": comparados,
        "coincide_con_exploracion": bool(explor_ok), "detalle": res,
    }, default=str), encoding="utf-8")
    print(f"-> {SALIDA_VERIFICACION}")
    if not (m0_igual and explor_ok):
        raise SystemExit("La verificacion no reproduce lo esperado: revisar antes de congelar.")


# --- evaluacion firmada -----------------------------------------------------


def _script_sin_cambios() -> str:
    ruta = Path(__file__).resolve()
    estado = subprocess.run(["git", "status", "--porcelain", "--", str(ruta)], capture_output=True, text=True,
                            cwd=ruta.parent, check=True).stdout.strip()
    if estado:
        raise SystemExit("El script tiene cambios sin commit: la evaluacion usa el metodo congelado.")
    return subprocess.run(["git", "log", "-1", "--format=%H", "--", str(ruta)], capture_output=True, text=True,
                          cwd=ruta.parent, check=True).stdout.strip()


def _serie_segun_captura(serie: Serie, puntos: list, hasta: str) -> Serie:
    """La serie mixta con las semanas del tablero tal como estaban en las
    capturas hechas hasta `hasta`; lo no capturado queda como NaN."""
    s = copy.deepcopy(serie)
    elegidos, _ = cmt.combinar([p for p in puntos if p.capturado <= hasta])
    idx = {(int(a), int(w)): k for k, (a, w) in enumerate(zip(s.anio, s.semana))}
    s.casos[s.anio >= 2025] = np.nan
    for (_, _, a, w), p in elegidos.items():
        if (a, w) in idx:
            s.casos[idx[(a, w)]] = float(p.conteo)
    s.z = np.log1p(s.casos)
    return s


def evaluar(serie: Serie) -> None:
    if SALIDA_PRUEBA.exists():
        raise SystemExit(f"La evaluacion ya se corrio ({SALIDA_PRUEBA}); se mira una sola vez.")
    commit = _script_sin_cambios()
    publicadas = [k for k in range(serie.T) if serie.fecha[k] >= INICIO_PRUEBA and np.isfinite(serie.casos[k])]
    if len(publicadas) < SEMANAS_PRUEBA:
        raise SystemExit(f"Hay {len(publicadas)} semanas de prueba publicadas; el corte firmado es {SEMANAS_PRUEBA}.")
    prueba = set(publicadas[:SEMANAS_PRUEBA])
    print(f"semanas de prueba: {serie.fecha[min(prueba)]} a {serie.fecha[max(prueba)]}; script {commit[:10]}")

    origenes = {h: [o for o in range(serie.T - h) if o + h in prueba and tab.features_sin_hueco(serie, o, h) is not None]
                for h in HORIZONTES}
    y = {h: {o: float(serie.casos[o + h]) for o in origenes[h]} for h in HORIZONTES}
    exp.verificar_sin_fuga(serie, origenes[4], 4, ALCANCE_HISTORIA)
    res = {r["h"]: r for r in correr([(serie, h, origenes[h], y[h], "prueba") for h in HORIZONTES])}
    t = tablas(res)
    imprimir("Prueba, contra la persistencia suavizada (criterio)", t["suavizada"])
    imprimir("Prueba, contra la persistencia limpia", t["limpia"])
    sin_cambio = tablas(res, lambda f: 4 <= f["semana"] <= 49)
    imprimir("Sensibilidad: sin semanas objetivo de la 50 a la 3, contra la persistencia suavizada",
             sin_cambio["suavizada"])

    # revisiones de MINSAL: si cambiaron semanas que sirven de rezago, se repite
    # con los datos de la primera captura que incluye cada origen
    puntos = [p for ruta in sorted(cmt.DIR_CAPTURAS.glob("*.har")) for p in cmt.leer_captura(ruta)
              if (p.evento, p.clasificacion) == ("dengue", "sospechoso")]
    _, revisiones = cmt.combinar(puntos)
    print(f"\nrevisiones de MINSAL en dengue sospechoso: {len(revisiones)}")
    for linea in revisiones:
        print(f"  {linea}")
    segun_captura = None
    if revisiones:
        primera: dict[tuple[int, int], str] = {}
        for p in puntos:
            clave = (p.anio, p.semana)
            primera[clave] = min(primera.get(clave, p.capturado), p.capturado)
        tareas = []
        for h in HORIZONTES:
            grupos: dict[str, list[int]] = {}
            for o in origenes[h]:
                clave = (int(serie.anio[o]), int(serie.semana[o]))
                grupos.setdefault(primera.get(clave, max(primera.values())), []).append(o)
            for hasta, os_ in sorted(grupos.items()):
                tareas.append((_serie_segun_captura(serie, puntos, hasta), h, os_, y[h], hasta))
        por_h: dict[int, dict] = {}
        for r in correr(tareas):
            d = por_h.setdefault(r["h"], {"h": r["h"], "filas": [], "sin_prediccion": 0})
            d["filas"] += r["filas"]
            d["sin_prediccion"] += r["sin_prediccion"]
        segun_captura = tablas(por_h)
        imprimir("Sensibilidad: datos de la primera captura de cada origen, contra la persistencia suavizada",
                 segun_captura["suavizada"])

    cond = {h: {"skill_positivo": t["suavizada"][h]["C"]["skill"] > 0,
                "no_peor_que_M0": t["suavizada"][h]["C"]["wis"] <= t["suavizada"][h]["M0"]["wis"],
                "cobertura_95": t["suavizada"][h]["C"]["cobertura_95"] >= COB95_MIN}
            for h in H_DECISIVOS}
    confirmado = all(all(v.values()) for v in cond.values())
    for h in H_DECISIVOS:
        r = t["suavizada"][h]["C"]
        print(f"h = {h}: skill {r['skill']:+.3f}, WIS {r['wis']:.1f} (M0 {t['suavizada'][h]['M0']['wis']:.1f}), "
              f"cobertura 95 {r['cobertura_95']:.2f}")
    print(f"\nC: {'CONFIRMADO' if confirmado else 'no confirmado'} {cond}")

    SALIDA_PRUEBA.write_text(json.dumps({
        "commit_script": commit, "semanas_prueba": [str(serie.fecha[k]) for k in sorted(prueba)],
        "tablas": t, "sin_cambio_de_anio": sin_cambio, "revisiones": revisiones,
        "segun_primera_captura": segun_captura, "condiciones": cond, "confirmado": confirmado, "detalle": res,
    }, default=str), encoding="utf-8")
    print(f"-> {SALIDA_PRUEBA}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modo = ap.add_mutually_exclusive_group(required=True)
    modo.add_argument("--verificar", action="store_true")
    modo.add_argument("--evaluar", action="store_true")
    args = ap.parse_args()
    conn = get_connection()
    try:
        serie = tab.cargar_serie_mixta(conn)
    finally:
        conn.close()
    print(f"serie mixta: {serie.T} semanas, {serie.fecha[0]} a {serie.fecha[-1]}")
    if args.verificar:
        verificar(serie)
    else:
        evaluar(serie)


if __name__ == "__main__":
    main()
