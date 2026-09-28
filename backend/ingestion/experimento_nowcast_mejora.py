"""
Experimento de mejora de la prediccion de dengue a 4-8 semanas
(docs/experimentos/experimento-nowcast-mejora.md, firmado 2026-09-27).

Tres modelos sobre la serie mixta (OpenDengue hasta 2024, tablero de MINSAL
desde 2025; ADR 0021), con el protocolo del ADR 0020:

  M0  el modelo publicado, sin cambios (control).
  M1  predice el cambio z[t+h] - z[t] en lugar del nivel, con una marca de
      vacaciones de la semana objetivo como feature adicional.
  M2  promedio por cuantil, en log, de M0 y la persistencia publicada, con el
      peso elegido en cada reajuste sobre los pares de calibracion.

Dos fases, en dos invocaciones:

  --fase validacion     objetivos 2019, 2021-2024; aplica el criterio firmado
                        y elige candidato. Incluye los controles de mutacion y
                        de repetibilidad a h = 4.
  --fase confirmacion   objetivos 2025-2026, solo para M0 y el candidato
                        elegido. Se niega a correr si la validacion no eligio
                        candidato o si la confirmacion ya existe.

Las nueve semanas con 0 casos de OpenDengue se usan como dato. La referencia
"limpia" no aprende de ellas ni de la semana siguiente a cada una.

Uso:
    cd backend/ingestion
    POSTGRES_HOST=localhost nice -n 10 ../.venv/bin/python experimento_nowcast_mejora.py --fase validacion
    POSTGRES_HOST=localhost nice -n 10 ../.venv/bin/python experimento_nowcast_mejora.py --fase confirmacion
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

import experimento_nowcast_corto_plazo as exp
import experimento_nowcast_tablero as tab
from experimento_nowcast_calibracion import MIN_CAL, MIN_PROPER, _ajustes_cqr_r, _fit_q
from experimento_nowcast_corto_plazo import ANIO_EXCLUIDO, CADENCIA_REAJUSTE, CUANTILES, Serie, cobertura, wis
from nowcast_estimacion_dengue import ALCANCE_HISTORIA, HORIZONTES, IDX_B50, IDX_B95, N_CAL, _qs_calibrado_cqr_r

from db import get_connection

ANIOS_VALIDACION = (2019, 2021, 2022, 2023, 2024)
ANIOS_CONFIRMACION = (2025, 2026)
H_DECISIVOS = (4, 8)
H_CONTROLES = 4
MIN_ANIOS_GANADOS = 4
BANDA_95 = (0.85, 0.99)
BANDA_50 = (0.35, 0.65)
PESOS_M2 = (0.0, 0.25, 0.5, 0.75, 1.0)
SEMILLA_MUTACION = 12345  # la del experimento original
PROCESOS = 4  # un hilo cada uno: la maquina se calienta con 8
CANDIDATOS = ("M1", "M2")
REFERENCIAS = ("persistencia_rw", "climatologia_estacional", "persistencia_estacional")

DIR = Path(__file__).parent / "data" / "interim" / "nowcast"
SALIDA_VALIDACION = DIR / "mejora_validacion.json"
SALIDA_CONFIRMACION = DIR / "mejora_confirmacion.json"


# --- semanas especiales ----------------------------------------------------


def _pascua(a: int) -> date:
    """Domingo de Pascua (algoritmo gregoriano anonimo)."""
    b, c = divmod(a, 100)
    d = a % 19
    e = (19 * d + b - b // 4 - (b - (b + 8) // 25 + 1) // 3 + 15) % 30
    f = (32 + 2 * (b % 4) + 2 * (c // 4) - e - c % 4) % 7
    g = (d + 11 * e + 22 * f) // 451
    mes, dia = divmod(e + f - 7 * g + 114, 31)
    return date(a, mes, dia + 1)


def marca_vacaciones(inicio: date) -> float:
    """1 si la semana (domingo a sabado) toca Semana Santa (domingo de Ramos a
    Pascua), fiestas agostinas (1-6 de agosto) o fin de anio (20 dic - 2 ene).
    Depende solo del calendario, asi que se conoce en el origen."""
    fin = inicio + timedelta(days=6)
    for a in {inicio.year - 1, inicio.year, fin.year}:
        p = _pascua(a)
        for ini_p, fin_p in ((p - timedelta(days=7), p), (date(a, 8, 1), date(a, 8, 6)),
                             (date(a, 12, 20), date(a + 1, 1, 2))):
            if inicio <= fin_p and fin >= ini_p:
                return 1.0
    return 0.0


def semanas_afectadas(serie: Serie) -> frozenset[int]:
    """Cada semana de OpenDengue con 0 casos notificados y la siguiente, que
    trae los casos de la anterior."""
    ceros = np.flatnonzero((serie.anio <= 2024) & (serie.casos == 0))
    return frozenset(int(k) for k in ceros) | frozenset(int(k) + 1 for k in ceros)


# --- referencias -----------------------------------------------------------
#
# Las de experimento_nowcast_tablero (las del ADR 0020, sin contar NaN), con la
# opcion de no aprender de un conjunto de semanas. Con `excluir` vacio dan la
# referencia publicada.


def _residuos(serie: Serie, o: int, h: int, excluir: frozenset[int]) -> np.ndarray:
    corte = serie.fecha[o]
    d = np.array([serie.z[t + h] - serie.z[t] for t in range(serie.T - h)
                  if serie.fecha[t + h] < corte
                  and serie.anio[t + h] != ANIO_EXCLUIDO
                  and serie.anio[t + h] >= ALCANCE_HISTORIA
                  and t not in excluir and t + h not in excluir])
    return d[np.isfinite(d)]


def _pool(serie: Serie, anio_obj: int, semana_obj: int, excluir: frozenset[int]) -> np.ndarray:
    m = ((serie.anio < anio_obj) & (serie.anio >= ALCANCE_HISTORIA) & (serie.anio != ANIO_EXCLUIDO)
         & (np.abs(serie.semana - semana_obj) <= 1) & np.isfinite(serie.casos))
    if excluir:
        m[list(excluir)] = False
    return serie.casos[m]


def referencia(nombre: str, serie: Serie, o: int, h: int, excluir: frozenset[int] = frozenset()) -> np.ndarray:
    tgt = o + h
    if nombre == "persistencia_rw":
        return np.clip(np.expm1(serie.z[o] + np.quantile(_residuos(serie, o, h, excluir), CUANTILES)), 0, None)
    p_t = _pool(serie, int(serie.anio[tgt]), int(serie.semana[tgt]), excluir)
    if nombre == "climatologia_estacional":
        if len(p_t) < 3:
            return np.full(len(CUANTILES), serie.casos[o])
        return np.clip(np.quantile(p_t, CUANTILES), 0, None)
    d = _residuos(serie, o, h, excluir)
    p_o = _pool(serie, int(serie.anio[o]), int(serie.semana[o]), excluir)
    ajuste = np.log1p(np.median(p_t)) - np.log1p(np.median(p_o)) if len(p_o) >= 3 and len(p_t) >= 3 else 0.0
    return np.clip(np.expm1(serie.z[o] + ajuste + np.quantile(d - np.median(d), CUANTILES)), 0, None)


# --- modelos ---------------------------------------------------------------


def _mezcla(q_m0: np.ndarray, q_rw: np.ndarray, w: float) -> np.ndarray:
    return np.clip(np.expm1(np.sort(w * np.log1p(q_m0) + (1 - w) * np.log1p(q_rw))), 0, None)


def _predecir(modelos: list, x: np.ndarray) -> np.ndarray:
    return np.sort(np.array([m.predict(x.reshape(1, -1))[0] for m in modelos]))


def cadena(serie: Serie, origenes: list[int], h: int, modelos: tuple[str, ...],
           mutar: bool = False) -> dict[int, dict | None]:
    """Cuantiles naturales (23) por origen y modelo, o None sin prediccion.

    M0 replica `nowcast_retrospectivo_dengue._cadena`: mismos pares, misma
    cadencia, mismo split (los N_CAL pares mas recientes calibran) y misma
    calibracion CQR-r. M1 y M2 se ajustan sobre los mismos pares en el mismo
    reajuste. `mutar` permuta las etiquetas de entrenamiento (control)."""
    rng = np.random.default_rng(SEMILLA_MUTACION)
    usar_m0 = "M0" in modelos or "M2" in modelos
    out: dict[int, dict | None] = {}
    est: dict | None = None
    ultimo = -10_000
    for o in origenes:
        if est is None or o - ultimo >= CADENCIA_REAJUSTE:
            X, Y, idx = tab.pares_sin_hueco(serie, o, h, ALCANCE_HISTORIA)
            if len(Y) < MIN_PROPER + MIN_CAL:
                out[o] = None
                continue
            assert max(serie.fecha[k] for k in idx) < serie.fecha[o], f"fuga en origen {o}"
            orden = np.argsort([serie.fecha[k] for k in idx])
            X, Y, idx = X[orden], Y[orden], idx[orden]
            z_t = X[:, 0]  # el primer rezago es z[t]
            D = Y - z_t
            X1 = np.column_stack([X, [marca_vacaciones(serie.fecha[k]) for k in idx]])
            if mutar:
                p = rng.permutation(len(Y))
                Y, D = Y[p], D[p]
            tr, ca = slice(0, len(Y) - N_CAL), slice(len(Y) - N_CAL, None)
            est = {}
            if usar_m0:
                est["m0"] = _fit_q(X[tr], Y[tr])
                q0 = np.sort(np.column_stack([m.predict(X[ca]) for m in est["m0"]]), axis=1)
                est["f0"] = _ajustes_cqr_r(q0, Y[ca])
            if "M1" in modelos:
                est["m1"] = _fit_q(X1[tr], D[tr])
                q1 = np.sort(np.column_stack([m.predict(X1[ca]) for m in est["m1"]]), axis=1) + z_t[ca, None]
                est["f1"] = _ajustes_cqr_r(q1, Y[ca])
            if "M2" in modelos:
                cuant_d = np.quantile(_residuos(serie, o, h, frozenset()), CUANTILES)
                y_ca = np.expm1(Y[ca])
                q0_cal = [_qs_calibrado_cqr_r(fila, est["f0"]) for fila in q0]
                q_rw = [np.clip(np.expm1(z + cuant_d), 0, None) for z in z_t[ca]]
                wis_w = [np.mean([wis(y, _mezcla(a, b, w)) for y, a, b in zip(y_ca, q0_cal, q_rw)])
                         for w in PESOS_M2]
                est["w"] = PESOS_M2[int(np.argmin(wis_w))]
            ultimo = o
        x = tab.features_sin_hueco(serie, o, h)
        if x is None:
            out[o] = None
            continue
        pred: dict = {}
        if usar_m0:
            q0o = _qs_calibrado_cqr_r(_predecir(est["m0"], x), est["f0"])
            if "M0" in modelos:
                pred["M0"] = q0o
        if "M1" in modelos:
            x1 = np.append(x, marca_vacaciones(serie.fecha[o + h]))
            pred["M1"] = _qs_calibrado_cqr_r(_predecir(est["m1"], x1) + serie.z[o], est["f1"])
        if "M2" in modelos:
            pred["M2"] = _mezcla(q0o, referencia("persistencia_rw", serie, o, h), est["w"])
            pred["w"] = est["w"]
        out[o] = pred
    return out


# --- evaluacion ------------------------------------------------------------


def origenes_de(serie: Serie, h: int, anios: tuple[int, ...]) -> list[int]:
    """Como `origenes_de_prueba` del ADR 0020, para los anios objetivo dados."""
    return [o for o in range(serie.T - h)
            if serie.anio[o] != ANIO_EXCLUIDO and serie.anio[o] >= ALCANCE_HISTORIA
            and serie.anio[o + h] in anios and np.isfinite(serie.casos[o + h])
            and tab.features_sin_hueco(serie, o, h) is not None]


def _tarea(args: tuple) -> dict:
    serie, h, anios, modelos, mutar, etiqueta = args
    threadpool_limits(1)
    tab._instalar_parches()
    afect = semanas_afectadas(serie)
    origenes = origenes_de(serie, h, anios)
    q = cadena(serie, origenes, h, modelos, mutar)
    filas = []
    for o in origenes:
        if q[o] is None:
            continue
        y = float(serie.casos[o + h])
        fila = {"origen": str(serie.fecha[o]), "anio": int(serie.anio[o + h]), "y": y,
                "afectada": (o + h) in afect}
        for m in modelos:
            fila[f"q_{m}"] = q[o][m].tolist()
            fila[f"wis_{m}"] = wis(y, q[o][m])
        if "w" in q[o]:
            fila["w_M2"] = q[o]["w"]
        if not mutar:
            for n in REFERENCIAS:
                fila[f"wis_pub_{n}"] = wis(y, referencia(n, serie, o, h))
                fila[f"wis_limpia_{n}"] = wis(y, referencia(n, serie, o, h, afect))
        filas.append(fila)
    return {"etiqueta": etiqueta, "h": h, "filas": filas, "sin_prediccion": len(origenes) - len(filas)}


def metricas(filas: list[dict], modelo: str, clave_ref: str, anios: tuple[int, ...]) -> dict:
    y = np.array([f["y"] for f in filas])
    qs = np.array([f[f"q_{modelo}"] for f in filas])
    por_anio = {}
    for a in anios:
        fa = [f for f in filas if f["anio"] == a]
        if fa:
            por_anio[a] = 1 - np.mean([f[f"wis_{modelo}"] for f in fa]) / np.mean([f[clave_ref] for f in fa])
    return {
        "n": len(filas),
        "wis": float(np.mean([f[f"wis_{modelo}"] for f in filas])),
        "wis_referencia": float(np.mean([f[clave_ref] for f in filas])),
        "skill_agrupado": float(1 - np.mean([f[f"wis_{modelo}"] for f in filas]) / np.mean([f[clave_ref] for f in filas])),
        "skill_por_anio": {a: round(float(v), 3) for a, v in por_anio.items()},
        "skill_medio": float(np.mean(list(por_anio.values()))) if por_anio else float("nan"),
        "anios_ganados": int(sum(v > 0 for v in por_anio.values())),
        "cobertura_50": float(cobertura(y, qs, *IDX_B50)),
        "cobertura_95": float(cobertura(y, qs, *IDX_B95)),
    }


def decisiva(filas: list[dict], familia: str) -> str:
    return min(REFERENCIAS, key=lambda n: np.mean([f[f"wis_{familia}_{n}"] for f in filas]))


def _en_banda(v: float, banda: tuple[float, float]) -> bool:
    return banda[0] <= v <= banda[1]


def _imprimir(titulo: str, tabla: dict, modelos: tuple[str, ...], anios: tuple[int, ...]) -> None:
    print(f"\n{titulo}")
    print(f"{'h':>2} {'modelo':<6} {'referencia':<24}" + "".join(f"{a:>7}" for a in anios)
          + f"{'medio':>7}{'gana':>6}{'cob50':>7}{'cob95':>7}{'WIS':>8}{'WIS ref':>8}")
    for h, porm in tabla.items():
        for m in modelos:
            r = porm[m]
            print(f"{h:>2} {m:<6} {r['referencia']:<24}"
                  + "".join(f"{r['skill_por_anio'].get(a, float('nan')):>7.2f}" for a in anios)
                  + f"{r['skill_medio']:>7.2f}{r['anios_ganados']:>4}/{len(anios)}"
                  f"{r['cobertura_50']:>7.2f}{r['cobertura_95']:>7.2f}{r['wis']:>8.1f}{r['wis_referencia']:>8.1f}")


def fase_validacion(serie: Serie) -> None:
    modelos = ("M0", "M1", "M2")
    tareas = [(serie, h, ANIOS_VALIDACION, modelos, False, "normal") for h in HORIZONTES]
    tareas += [(serie, H_CONTROLES, ANIOS_VALIDACION, modelos, True, "mutacion"),
               (serie, H_CONTROLES, ANIOS_VALIDACION, modelos, False, "repeticion")]
    # la garantia anti-fuga y su control negativo, como en el ADR 0020
    exp.verificar_sin_fuga(serie, origenes_de(serie, H_CONTROLES, ANIOS_VALIDACION), H_CONTROLES, ALCANCE_HISTORIA)
    with ProcessPoolExecutor(max_workers=PROCESOS) as ex:
        res = list(ex.map(_tarea, tareas))
    normal = {r["h"]: r for r in res if r["etiqueta"] == "normal"}

    tablas: dict[str, dict] = {}
    for familia in ("limpia", "pub"):
        for sufijo, filtro in (("", lambda f: True), ("_sin_afectadas", lambda f: not f["afectada"])):
            t = {}
            for h, r in normal.items():
                filas = [f for f in r["filas"] if filtro(f)]
                ref = decisiva(filas, familia)
                t[h] = {m: {"referencia": ref, **metricas(filas, m, f"wis_{familia}_{ref}", ANIOS_VALIDACION)}
                        for m in modelos}
            tablas[familia + sufijo] = t
    _imprimir("Validacion, referencia limpia (criterio)", tablas["limpia"], modelos, ANIOS_VALIDACION)
    _imprimir("Validacion, referencia publicada", tablas["pub"], modelos, ANIOS_VALIDACION)
    _imprimir("Sensibilidad: referencia limpia, sin puntuar las semanas afectadas",
              tablas["limpia_sin_afectadas"], modelos, ANIOS_VALIDACION)

    # M0 debe reproducir lo publicado (h = 4, referencia publicada)
    publicado = json.loads((Path(__file__).parent.parent / "api" / "datos" / "nowcast_dengue_opendengue.json")
                           .read_text(encoding="utf-8"))["desempeno"]["skill_por_anio"]
    m0 = tablas["pub"][4]["M0"]["skill_por_anio"]
    dif = max(abs(m0[int(a)] - v) for a, v in publicado.items())
    print(f"\nM0 contra lo publicado (h = 4): diferencia maxima de skill por anio {dif:.3f}")

    # controles
    mut = next(r for r in res if r["etiqueta"] == "mutacion")
    rep = next(r for r in res if r["etiqueta"] == "repeticion")
    controles = {"mutacion": {}, "repetible": True}
    for m in modelos:
        w_normal = np.mean([f[f"wis_{m}"] for f in normal[H_CONTROLES]["filas"]])
        w_mut = np.mean([f[f"wis_{m}"] for f in mut["filas"]])
        controles["mutacion"][m] = {"wis": float(w_normal), "wis_mutado": float(w_mut), "empeora": bool(w_mut > w_normal)}
        print(f"control de mutacion {m}: WIS {w_normal:.1f} -> {w_mut:.1f} con etiquetas permutadas")
        iguales = all(np.array_equal(a[f"q_{m}"], b[f"q_{m}"]) for a, b in zip(normal[H_CONTROLES]["filas"], rep["filas"]))
        controles["repetible"] &= iguales and len(normal[H_CONTROLES]["filas"]) == len(rep["filas"])
    print(f"repetibilidad (h = {H_CONTROLES}): {'identica' if controles['repetible'] else 'DISTINTA'}")
    controles_ok = controles["repetible"] and all(controles["mutacion"][m]["empeora"] for m in ("M0", "M1"))

    # criterio firmado
    veredicto = {}
    for c in CANDIDATOS:
        cond = {}
        for h in H_DECISIVOS:
            r, r0 = tablas["limpia"][h][c], tablas["limpia"][h]["M0"]
            cond[h] = {
                "skill_medio_positivo": r["skill_medio"] > 0,
                "gana_4_de_5": r["anios_ganados"] >= MIN_ANIOS_GANADOS,
                "cobertura_en_banda": _en_banda(r["cobertura_95"], BANDA_95) and _en_banda(r["cobertura_50"], BANDA_50),
                "no_peor_que_M0": r["wis"] <= r0["wis"],
            }
        veredicto[c] = {"condiciones": cond, "pasa": all(all(v.values()) for v in cond.values())}
        print(f"{c}: {'PASA' if veredicto[c]['pasa'] else 'no pasa'} {cond}")
    pasan = [c for c in CANDIDATOS if veredicto[c]["pasa"]]
    elegido = max(pasan, key=lambda c: tablas["limpia"][8][c]["skill_medio"]) if pasan and controles_ok else None
    if pasan and not controles_ok:
        print("Los controles fallaron: no se elige candidato hasta revisarlos.")
    print(f"\nCandidato elegido: {elegido or 'ninguno (resultado negativo)'}")

    SALIDA_VALIDACION.write_text(json.dumps({
        "tablas": tablas, "controles": controles, "veredicto": veredicto, "elegido": elegido,
        "referencia_decisiva": {h: {"limpia": tablas["limpia"][h]["M0"]["referencia"],
                                    "pub": tablas["pub"][h]["M0"]["referencia"]} for h in HORIZONTES},
        "diferencia_m0_publicado_h4": dif,
        "detalle": normal,
    }, default=str), encoding="utf-8")
    print(f"-> {SALIDA_VALIDACION}")


def fase_confirmacion(serie: Serie) -> None:
    if SALIDA_CONFIRMACION.exists():
        raise SystemExit(f"La confirmacion ya se corrio ({SALIDA_CONFIRMACION}); se mira una sola vez.")
    val = json.loads(SALIDA_VALIDACION.read_text(encoding="utf-8"))
    elegido = val["elegido"]
    if not elegido:
        raise SystemExit("La validacion no eligio candidato: no hay nada que confirmar.")
    modelos = ("M0", elegido)
    tareas = [(serie, h, ANIOS_CONFIRMACION, modelos, False, "normal") for h in HORIZONTES]
    with ProcessPoolExecutor(max_workers=PROCESOS) as ex:
        res = {r["h"]: r for r in ex.map(_tarea, tareas)}

    tablas = {}
    for familia in ("limpia", "pub"):
        t = {}
        for h, r in res.items():
            ref = val["referencia_decisiva"][str(h)][familia]  # la elegida en la validacion
            t[h] = {m: {"referencia": ref, **metricas(r["filas"], m, f"wis_{familia}_{ref}", ANIOS_CONFIRMACION)}
                    for m in modelos}
        tablas[familia] = t
    _imprimir("Confirmacion, referencia limpia (criterio)", tablas["limpia"], modelos, ANIOS_CONFIRMACION)
    _imprimir("Confirmacion, referencia publicada", tablas["pub"], modelos, ANIOS_CONFIRMACION)

    cond = {h: {"skill_agrupado_positivo": tablas["limpia"][h][elegido]["skill_agrupado"] > 0,
                "cobertura_95_en_banda": _en_banda(tablas["limpia"][h][elegido]["cobertura_95"], BANDA_95)}
            for h in H_DECISIVOS}
    confirmado = all(all(v.values()) for v in cond.values())
    for h in H_DECISIVOS:
        r = tablas["limpia"][h][elegido]
        print(f"h = {h}: skill agrupado {r['skill_agrupado']:.3f}, cobertura 95 {r['cobertura_95']:.2f}")
    print(f"\n{elegido}: {'CONFIRMADO' if confirmado else 'no confirmado'} {cond}")

    SALIDA_CONFIRMACION.write_text(json.dumps({
        "elegido": elegido, "tablas": tablas, "condiciones": cond, "confirmado": confirmado, "detalle": res,
    }, default=str), encoding="utf-8")
    print(f"-> {SALIDA_CONFIRMACION}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fase", choices=("validacion", "confirmacion"), required=True)
    args = ap.parse_args()
    conn = get_connection()
    try:
        serie = tab.cargar_serie_mixta(conn)
    finally:
        conn.close()
    DIR.mkdir(parents=True, exist_ok=True)
    afect = semanas_afectadas(serie)
    print(f"serie mixta: {serie.T} semanas, {serie.fecha[0]} a {serie.fecha[-1]}; "
          f"{len(afect)} semanas afectadas por notificacion desplazada")
    if args.fase == "validacion":
        fase_validacion(serie)
    else:
        fase_confirmacion(serie)


if __name__ == "__main__":
    main()
