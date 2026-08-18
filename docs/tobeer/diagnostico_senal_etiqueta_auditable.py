"""Diagnostico auditable: por que el clasificador nacional no supera su criterio.

Version ampliada del diagnostico original. Misma logica y mismos resultados;
lo que cambia es que ahora emite TODO lo necesario para auditarlo sin
confiar en el que lo corrio:

  - matriz de confusion de cada modelo evaluado
  - metricas por clase (precision / recall / F1 / soporte)
  - aciertos absolutos "X de Y" al lado de cada recall
  - probabilidades por fila volcadas a CSV
  - semillas, hiperparametros y versiones de dependencias
  - un JSON con todos los resultados, para diff contra una re-corrida

Los cuatro analisis que Isaac pidio por separado estan todos aca:
  seccion 3 -> umbral / AUC          (el AUC = 0,23)
  seccion 4 -> comparacion de algoritmos (RF, GB, ET, LogReg)
  seccion 5 -> pool de percentiles no pareado por semana
  seccion 6 -> preliminar de etiqueta intra-anual (Via 2)

No entrena nada de produccion, no escribe a Postgres, no toca los
artefactos del modelo. Lee db/seed/seed_datos_reales.sql directamente, asi
que corre en un clon limpio sin la base levantada.

Uso:
    python3 diagnostico_senal_etiqueta_auditable.py \
        --seed-sql db/seed/seed_datos_reales.sql \
        --salida ./salida_diagnostico
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.base import clone
from sklearn.ensemble import (ExtraTreesClassifier, GradientBoostingClassifier,
                              RandomForestClassifier)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix,
                             f1_score, recall_score, roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Parametros. Identicos a produccion (corrida_canal_endemico_nacional.py /
# construir_dataset_modelado.py). Si estos divergen, el diagnostico deja de
# hablar del modelo que se entrega -- por eso van explicitos y se imprimen.
# ---------------------------------------------------------------------------
ANIOS_BASE = [2018, 2019, 2021, 2022, 2023]
VENTANA = 1
PISO_OBSERVACIONES = 12
PISO_ANIOS_MIN = 3
CORTE_PRODUCCION = (0.75, 0.90)
LAGS = (1, 2)
VENTANAS_MEDIA_MOVIL = (4,)
VARIABLES_CLIMA = ["temp_max", "temp_min", "temp_media",
                   "humedad_relativa_media", "punto_rocio",
                   "precipitation_sum", "precipitation_hours"]
CLASES = ["bajo", "medio", "alto"]

HIPERPARAMETROS_RF = {"n_estimators": 300, "class_weight": "balanced"}
SEMILLA_REFERENCIA = 42
SEMILLAS = list(range(10))


# ---------------------------------------------------------------------------
# Lectura del volcado versionado
# ---------------------------------------------------------------------------
def _bloque(texto: str, tabla: str) -> list[str]:
    lineas = texto.split("\n")
    ini = None
    for i, linea in enumerate(lineas):
        if linea.startswith("COPY public.%s " % tabla):
            ini = i + 1
        elif ini is not None and linea == "\\.":
            return lineas[ini:i]
    return []


def cargar(ruta_seed: Path):
    texto = ruta_seed.read_text(encoding="utf-8")

    # Casos nacionales: clasificacion='total' (OpenDengue Admin0, ADR 0005).
    serie: dict[int, dict[int, float]] = defaultdict(dict)
    for linea in _bloque(texto, "casos_epidemiologicos"):
        campos = linea.split("\t")
        if campos[5] == "total":
            serie[int(campos[3])][int(campos[4])] = float(campos[6])

    # Clima: promedio simple de los 14 departamentos (cerrado 2026-08-15).
    # La region nacional se identifica por ser la unica con oni_anom, en vez
    # de hardcodear un id que puede cambiar entre volcados.
    filas_va = _bloque(texto, "variables_ambientales")
    regiones_nacionales = {l.split("\t")[1] for l in filas_va
                           if l.split("\t")[4] == "oni_anom"}
    acumulado = defaultdict(list)
    for linea in filas_va:
        campos = linea.split("\t")
        if campos[4] == "oni_anom" or campos[1] in regiones_nacionales:
            continue
        acumulado[(int(campos[2]), int(campos[3]), campos[4])].append(float(campos[5]))
    clima: dict[tuple[int, int], dict[str, float]] = defaultdict(dict)
    for (anio, semana, variable), valores in acumulado.items():
        clima[(anio, semana)][variable] = sum(valores) / len(valores)
    return serie, clima


# ---------------------------------------------------------------------------
# Etiqueta y features
# ---------------------------------------------------------------------------
def percentil(valores, p):
    v = sorted(valores)
    if len(v) == 1:
        return v[0]
    pos = p * (len(v) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)


def etiquetar_canal(serie, corte=CORTE_PRODUCCION):
    """Canal endemico de produccion: pool pareado por semana calendario,
    el anio etiquetado nunca entra en su propia linea base."""
    salida = {}
    for anio in ANIOS_BASE:
        for semana in sorted(serie.get(anio, {})):
            pool, n_anios = [], 0
            for otro in ANIOS_BASE:
                if otro == anio or otro not in serie:
                    continue
                vecinas = [serie[otro][w]
                           for w in range(semana - VENTANA, semana + VENTANA + 1)
                           if w in serie[otro]]
                if vecinas:
                    n_anios += 1
                    pool.extend(vecinas)
            if len(pool) < PISO_OBSERVACIONES or n_anios < PISO_ANIOS_MIN:
                continue
            c1, c2 = percentil(pool, corte[0]), percentil(pool, corte[1])
            valor = serie[anio][semana]
            salida[(anio, semana)] = ("alto" if valor > c2
                                      else "medio" if valor > c1 else "bajo")
    return salida


def _retroceder(anio, semana, k, clima):
    """Retrocede k semanas cruzando el limite de anio. El anio anterior puede
    tener 51, 52 o 53 semanas, asi que se consulta cuantas hay realmente."""
    a, s = anio, semana
    for _ in range(k):
        s -= 1
        if s < 1:
            a -= 1
            s = max((w for (y, w) in clima if y == a), default=52)
    return (a, s)


def construir_dataset(serie, clima, etiquetas):
    filas = []
    for (anio, semana), etiqueta in sorted(etiquetas.items()):
        feat, ok = {}, True
        for lag in LAGS:
            clave = _retroceder(anio, semana, lag, clima)
            if clave not in clima or any(v not in clima[clave] for v in VARIABLES_CLIMA):
                ok = False
                break
            for variable in VARIABLES_CLIMA:
                feat["%s_lag%d" % (variable, lag)] = clima[clave][variable]
        if not ok:
            continue
        for ventana in VENTANAS_MEDIA_MOVIL:
            acc = defaultdict(list)
            for k in range(1, ventana + 1):
                clave = _retroceder(anio, semana, k, clima)
                if clave not in clima:
                    ok = False
                    break
                for variable in VARIABLES_CLIMA:
                    if variable in clima[clave]:
                        acc[variable].append(clima[clave][variable])
            if not ok:
                break
            for variable in VARIABLES_CLIMA:
                if len(acc[variable]) != ventana:
                    ok = False
                    break
                feat["%s_media_movil%d" % (variable, ventana)] = (
                    sum(acc[variable]) / ventana)
        if not ok:
            continue
        filas.append({"anio": anio, "semana": semana,
                      "casos": serie[anio][semana], "etiqueta": etiqueta, **feat})
    return filas


# ---------------------------------------------------------------------------
# Evaluacion con salida auditable
# ---------------------------------------------------------------------------
def columnas(filas):
    return [k for k in filas[0] if k not in ("anio", "semana", "casos", "etiqueta")]


def matriz(filas, cols):
    return (np.array([[f[c] for c in cols] for f in filas]),
            np.array([f["etiqueta"] for f in filas]))


def linea_base_climatologica(train, test):
    """Clase modal de esa semana calendario en los anios de entrenamiento."""
    por_semana = defaultdict(list)
    for f in train:
        por_semana[f["semana"]].append(f["etiqueta"])
    modal_global = Counter(f["etiqueta"] for f in train).most_common(1)[0][0]
    return [Counter(por_semana[f["semana"]]).most_common(1)[0][0]
            if por_semana[f["semana"]] else modal_global for f in test]


def aciertos_absolutos(y_real, y_pred, clase="alto"):
    """Devuelve (aciertos, soporte). El recall solo es interpretable junto
    a estos dos numeros: 0,009 sobre 109 es UN acierto."""
    real = np.array(y_real) == clase
    return int((real & (np.array(y_pred) == clase)).sum()), int(real.sum())


def imprimir_confusion(y_real, y_pred, titulo):
    presentes = [c for c in CLASES if c in set(y_real) | set(y_pred)]
    cm = confusion_matrix(y_real, y_pred, labels=presentes)
    print("    %s" % titulo)
    print("      real \\ pred   " + "".join("%8s" % c for c in presentes))
    for i, clase in enumerate(presentes):
        print("      %-13s" % clase + "".join("%8d" % v for v in cm[i]))
    return {"etiquetas": presentes, "matriz": cm.tolist()}


def imprimir_por_clase(y_real, y_pred, indent="      "):
    rep = classification_report(y_real, y_pred, labels=CLASES,
                                output_dict=True, zero_division=0)
    print("%sclase    precision   recall      F1    soporte" % indent)
    for clase in CLASES:
        d = rep[clase]
        print("%s%-8s %9.3f %8.3f %7.3f %10d"
              % (indent, clase, d["precision"], d["recall"], d["f1-score"],
                 int(d["support"])))
    return {c: rep[c] for c in CLASES}


def evaluar(filas, anio_prueba, cols, modelo=None, semilla=SEMILLA_REFERENCIA):
    train = [f for f in filas if f["anio"] != anio_prueba]
    test = [f for f in filas if f["anio"] == anio_prueba]
    X_tr, y_tr = matriz(train, cols)
    X_te, y_te = matriz(test, cols)
    if modelo is None:
        modelo = RandomForestClassifier(random_state=semilla, **HIPERPARAMETROS_RF)
    ajustado = clone(modelo).fit(X_tr, y_tr)
    pred = ajustado.predict(X_te)
    base = linea_base_climatologica(train, test)
    hay_alto = "alto" in set(y_te)
    rec = lambda y, p: recall_score(y, p, labels=["alto"], average="macro",
                                    zero_division=0)
    aciertos_m, soporte = aciertos_absolutos(y_te, pred)
    aciertos_b, _ = aciertos_absolutos(y_te, base)
    return {
        "anio_prueba": anio_prueba,
        "n_train": len(train), "n_test": len(test),
        "soporte_alto": soporte,
        "f1_macro_modelo": float(f1_score(y_te, pred, average="macro", zero_division=0)),
        "f1_macro_base": float(f1_score(y_te, base, average="macro", zero_division=0)),
        "recall_alto_modelo": float(rec(y_te, pred)) if hay_alto else None,
        "recall_alto_base": float(rec(y_te, base)) if hay_alto else None,
        "aciertos_alto_modelo": aciertos_m,
        "aciertos_alto_base": aciertos_b,
        "distribucion_predicha": dict(Counter(pred)),
        "_modelo": ajustado, "_y_te": y_te, "_X_te": X_te,
        "_pred": pred, "_base": base, "_test": test,
    }


def linea_resumen(res, etiqueta):
    if res["recall_alto_modelo"] is None:
        return ("  %-14s no evaluable (0 semanas 'alto' reales en el anio)"
                % etiqueta)
    return ("  %-14s F1 %.3f vs base %.3f | recall alto %.3f (%d de %d) vs base %.3f (%d de %d)  %s"
            % (etiqueta, res["f1_macro_modelo"], res["f1_macro_base"],
               res["recall_alto_modelo"], res["aciertos_alto_modelo"], res["soporte_alto"],
               res["recall_alto_base"], res["aciertos_alto_base"], res["soporte_alto"],
               "SUPERA" if (res["f1_macro_modelo"] > res["f1_macro_base"]
                            and res["recall_alto_modelo"] > res["recall_alto_base"])
               else "no supera"))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-sql", type=Path, required=True)
    ap.add_argument("--salida", type=Path, default=Path("./salida_diagnostico"))
    args = ap.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    resultados = {"generado": datetime.now(timezone.utc).isoformat()}

    print("=" * 78)
    print("ENTORNO Y PARAMETROS")
    print("=" * 78)
    entorno = {
        "python": sys.version.split()[0],
        "plataforma": platform.platform(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "comando": " ".join(sys.argv),
        "seed_sql": str(args.seed_sql.resolve()),
        "seed_sql_bytes": args.seed_sql.stat().st_size,
    }
    for k, v in entorno.items():
        print("  %-16s %s" % (k, v))
    print()
    parametros = {
        "anios_base": ANIOS_BASE, "ventana_pool": VENTANA,
        "piso_observaciones": PISO_OBSERVACIONES, "piso_anios_min": PISO_ANIOS_MIN,
        "corte_percentiles": list(CORTE_PRODUCCION), "lags": list(LAGS),
        "ventanas_media_movil": list(VENTANAS_MEDIA_MOVIL),
        "variables_clima": VARIABLES_CLIMA,
        "hiperparametros_rf": HIPERPARAMETROS_RF,
        "semilla_referencia": SEMILLA_REFERENCIA, "semillas": SEMILLAS,
    }
    for k, v in parametros.items():
        print("  %-22s %s" % (k, v))
    resultados["entorno"] = entorno
    resultados["parametros"] = parametros

    serie, clima = cargar(args.seed_sql)
    etiquetas = etiquetar_canal(serie)
    filas = construir_dataset(serie, clima, etiquetas)
    cols = columnas(filas)
    print("\n  dataset replicado: %d filas, %d predictores" % (len(filas), len(cols)))
    resultados["dataset"] = {"filas": len(filas), "predictores": len(cols),
                             "columnas": cols}

    # -------------------------------------------------------------- 1 -----
    print("\n" + "=" * 78)
    print("1. LA ETIQUETA MIDE EL ANIO, NO LA SEMANA")
    print("=" * 78)
    totales, n_altos, por_anio = [], [], {}
    for anio in ANIOS_BASE:
        c = Counter(f["etiqueta"] for f in filas if f["anio"] == anio)
        total = sum(serie[anio].values())
        totales.append(total)
        n_altos.append(c["alto"])
        por_anio[anio] = {"total_anual": total, "bajo": c["bajo"],
                          "medio": c["medio"], "alto": c["alto"]}
        print("  %d  total anual=%7.0f   bajo=%2d  medio=%2d  alto=%2d"
              % (anio, total, c["bajo"], c["medio"], c["alto"]))
    correlacion = float(np.corrcoef(totales, n_altos)[0, 1])
    print("  correlacion(total anual, semanas 'alto') = %.3f" % correlacion)
    print("  anios con al menos una semana 'alto': %d de %d"
          % (sum(1 for n in n_altos if n), len(ANIOS_BASE)))
    resultados["efecto_anio"] = {"por_anio": por_anio,
                                 "correlacion_total_vs_nalto": correlacion}

    # -------------------------------------------------------------- 2 -----
    print("\n" + "=" * 78)
    print("2. RESULTADO ACTUAL DE PRODUCCION (argmax, RandomForest)")
    print("=" * 78)
    resultados["produccion"] = {}
    for anio in ANIOS_BASE:
        res = evaluar(filas, anio, cols)
        print(linea_resumen(res, "anio %d" % anio))
        if res["soporte_alto"] > 0 or anio in (2019, 2022, 2023):
            cm = imprimir_confusion(res["_y_te"], res["_pred"],
                                    "matriz de confusion (modelo):")
            porclase = imprimir_por_clase(res["_y_te"], res["_pred"])
            cm_base = imprimir_confusion(res["_y_te"], res["_base"],
                                         "matriz de confusion (linea base):")
            resultados["produccion"][str(anio)] = {
                k: v for k, v in res.items() if not k.startswith("_")}
            resultados["produccion"][str(anio)]["confusion_modelo"] = cm
            resultados["produccion"][str(anio)]["confusion_base"] = cm_base
            resultados["produccion"][str(anio)]["por_clase_modelo"] = porclase
            print()

    # -------------------------------------------------------------- 3 -----
    print("=" * 78)
    print("3. UMBRAL / AUC  -- el analisis que dio AUC = 0,23")
    print("   Si el AUC esta por debajo de 0,5 el ordenamiento de las")
    print("   probabilidades esta invertido: ningun umbral lo rescata.")
    print("=" * 78)
    resultados["auc"] = {}
    volcado_prob = ["anio,semana,etiqueta_real,pred_argmax,p_bajo,p_medio,p_alto"]
    for anio in [2019, 2022]:
        res = evaluar(filas, anio, cols)
        modelo = res["_modelo"]
        idx = list(modelo.classes_).index("alto")
        P = modelo.predict_proba(res["_X_te"])
        p_alto = P[:, idx]
        real_bin = (res["_y_te"] == "alto").astype(int)
        auc = float(roc_auc_score(real_bin, p_alto))
        print("  %d  AUC = %.3f   P(alto): max=%.3f  media=%.3f  min=%.3f   soporte alto = %d"
              % (anio, auc, p_alto.max(), p_alto.mean(), p_alto.min(), res["soporte_alto"]))
        print("      clases del modelo: %s" % list(modelo.classes_))
        # barrido de umbral, para dejar constancia de que ninguno funciona
        print("      barrido de umbral (recall alto / precision alto / F1 macro):")
        barrido = []
        for t in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
            pred_t = np.where(p_alto > t, "alto", res["_pred"])
            ac, sop = aciertos_absolutos(res["_y_te"], pred_t)
            r = recall_score(res["_y_te"], pred_t, labels=["alto"],
                             average="macro", zero_division=0)
            pr = (ac / max((pred_t == "alto").sum(), 1))
            f1m = f1_score(res["_y_te"], pred_t, average="macro", zero_division=0)
            print("        t=%.2f  recall=%.3f (%d de %d)  precision=%.3f  F1 macro=%.3f"
                  % (t, r, ac, sop, pr, f1m))
            barrido.append({"umbral": t, "recall_alto": float(r),
                            "aciertos": ac, "soporte": sop,
                            "precision_alto": float(pr), "f1_macro": float(f1m)})
        resultados["auc"][str(anio)] = {
            "auc": auc, "p_alto_max": float(p_alto.max()),
            "p_alto_media": float(p_alto.mean()),
            "clases_modelo": list(modelo.classes_), "barrido_umbral": barrido}
        for fila, pr_, pred_ in zip(res["_test"], P, res["_pred"]):
            orden = {c: pr_[i] for i, c in enumerate(modelo.classes_)}
            volcado_prob.append("%d,%d,%s,%s,%.6f,%.6f,%.6f"
                                % (fila["anio"], fila["semana"], fila["etiqueta"],
                                   pred_, orden.get("bajo", 0.0),
                                   orden.get("medio", 0.0), orden.get("alto", 0.0)))
        print()
    (args.salida / "probabilidades_por_fila.csv").write_text(
        "\n".join(volcado_prob) + "\n", encoding="utf-8")
    print("  probabilidades por fila -> %s"
          % (args.salida / "probabilidades_por_fila.csv"))

    # -------------------------------------------------------------- 4 -----
    print("\n" + "=" * 78)
    print("4. COMPARACION DE ALGORITMOS")
    print("=" * 78)
    modelos = {
        "RandomForest": RandomForestClassifier(random_state=SEMILLA_REFERENCIA,
                                               **HIPERPARAMETROS_RF),
        "GradientBoosting": GradientBoostingClassifier(random_state=SEMILLA_REFERENCIA),
        "ExtraTrees": ExtraTreesClassifier(n_estimators=300, class_weight="balanced",
                                           random_state=SEMILLA_REFERENCIA),
        "LogisticRegression": make_pipeline(
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=2000)),
    }
    resultados["algoritmos"] = {}
    for nombre, modelo in modelos.items():
        resultados["algoritmos"][nombre] = {}
        print("  --- %s ---" % nombre)
        for anio in [2019, 2022]:
            res = evaluar(filas, anio, cols, modelo=modelo)
            print(linea_resumen(res, "anio %d" % anio))
            cm = imprimir_confusion(res["_y_te"], res["_pred"], "matriz:")
            resultados["algoritmos"][nombre][str(anio)] = {
                k: v for k, v in res.items() if not k.startswith("_")}
            resultados["algoritmos"][nombre][str(anio)]["confusion"] = cm
        print()

    # -------------------------------------------------------------- 5 -----
    print("=" * 78)
    print("5. POOL DE PERCENTILES NO PAREADO POR SEMANA")
    print("   (pool = todas las semanas de los otros anios, no solo w-1,w,w+1)")
    print("=" * 78)
    resultados["pool_no_pareado"] = {}
    for corte in [(0.75, 0.90), (0.50, 0.75)]:
        clave_corte = "P%d_P%d" % (corte[0] * 100, corte[1] * 100)
        print("  --- corte %s ---" % clave_corte.replace("_", "/"))
        etiquetas_alt = {}
        for anio in ANIOS_BASE:
            pool = [v for otro in ANIOS_BASE if otro != anio
                    for v in serie[otro].values()]
            c1, c2 = percentil(pool, corte[0]), percentil(pool, corte[1])
            for semana, valor in serie[anio].items():
                etiquetas_alt[(anio, semana)] = ("alto" if valor > c2
                                                 else "medio" if valor > c1 else "bajo")
        filas_alt = [dict(f, etiqueta=etiquetas_alt[(f["anio"], f["semana"])])
                     for f in filas]
        for anio in ANIOS_BASE:
            c = Counter(f["etiqueta"] for f in filas_alt if f["anio"] == anio)
            print("      %d  distribucion: %s" % (anio, dict(c)))
        resultados["pool_no_pareado"][clave_corte] = {}
        for anio in ANIOS_BASE:
            res = evaluar(filas_alt, anio, cols)
            print(linea_resumen(res, "anio %d" % anio))
            resultados["pool_no_pareado"][clave_corte][str(anio)] = {
                k: v for k, v in res.items() if not k.startswith("_")}
        print()

    # -------------------------------------------------------------- 6 -----
    print("=" * 78)
    print("6. PRELIMINAR DE LA VIA 2 -- etiqueta relativa al propio anio")
    print("   'alto' = semana en el 25%% superior de SU MISMO anio (P50/P75).")
    print("   REABRE ESTATUTOS CERRADOS. No adoptar sin decision del coordinador.")
    print("=" * 78)
    filas_intra = []
    for anio in ANIOS_BASE:
        valores = [f["casos"] for f in filas if f["anio"] == anio]
        c1, c2 = percentil(valores, 0.50), percentil(valores, 0.75)
        for f in filas:
            if f["anio"] == anio:
                filas_intra.append(dict(
                    f, etiqueta="alto" if f["casos"] > c2
                    else ("medio" if f["casos"] > c1 else "bajo")))
    for anio in ANIOS_BASE:
        c = Counter(f["etiqueta"] for f in filas_intra if f["anio"] == anio)
        print("  %d  distribucion: %s" % (anio, dict(c)))
    print("\n  Resultados sobre %d semillas (%s):" % (len(SEMILLAS), SEMILLAS))
    resultados["via2_intra_anual"] = {}
    for anio in ANIOS_BASE:
        f1s, recalls, aciertos, supera = [], [], [], 0
        ref = None
        for semilla in SEMILLAS:
            res = evaluar(filas_intra, anio, cols, semilla=semilla)
            f1s.append(res["f1_macro_modelo"])
            recalls.append(res["recall_alto_modelo"])
            aciertos.append(res["aciertos_alto_modelo"])
            supera += int(res["f1_macro_modelo"] > res["f1_macro_base"]
                          and res["recall_alto_modelo"] > res["recall_alto_base"])
            ref = res
        print("  %d  F1 %.3f+-%.3f vs base %.3f | recall alto %.3f+-%.3f (%d-%d de %d) vs base %.3f | supera %d/%d"
              % (anio, float(np.mean(f1s)), float(np.std(f1s)), ref["f1_macro_base"],
                 float(np.mean(recalls)), float(np.std(recalls)),
                 min(aciertos), max(aciertos), ref["soporte_alto"],
                 ref["recall_alto_base"], supera, len(SEMILLAS)))
        resultados["via2_intra_anual"][str(anio)] = {
            "f1_media": float(np.mean(f1s)), "f1_desv": float(np.std(f1s)),
            "f1_base": ref["f1_macro_base"],
            "recall_media": float(np.mean(recalls)), "recall_desv": float(np.std(recalls)),
            "recall_base": ref["recall_alto_base"],
            "aciertos_min": min(aciertos), "aciertos_max": max(aciertos),
            "soporte_alto": ref["soporte_alto"],
            "supera_en_semillas": supera, "semillas_totales": len(SEMILLAS),
            "f1_por_semilla": [float(x) for x in f1s],
            "recall_por_semilla": [float(x) for x in recalls],
        }
    print("\n  ADVERTENCIA: 10 semillas miden la variabilidad del algoritmo,")
    print("  NO la de haber observado estos 5 anios y no otros. Un 7/10 no es")
    print("  un resultado que se sostenga solo.")

    ruta_json = args.salida / "resultados_diagnostico.json"
    ruta_json.write_text(json.dumps(resultados, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    print("\n  resultados completos -> %s" % ruta_json)


if __name__ == "__main__":
    main()
