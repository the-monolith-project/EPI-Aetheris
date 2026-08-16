"""
Tarjeta 24 -- entrena y evalua el clasificador de riesgo nacional sobre el
dataset producido por construir_dataset_modelado.py (tarjeta 23).

Primera pasada (Hito 2): un solo anio de prueba, se acepta que el
resultado sea malo -- la meta es que el camino completo funcione, no que
acierte. Validacion temporal simple, ya cerrada en
docs/contexto/01-decisiones-cerradas.md: entrenar con los anios viejos,
probar contra el anio mas reciente de la ventana (2023). Nunca split
aleatorio de semanas entre anios -- eso dejaria al modelo ver el futuro.

Metrica decisiva ya cerrada: el modelo debe superar a la linea base
climatologica en F1 macro y en recall de la clase "alto", por anio de
prueba (ver 01-decisiones-cerradas.md, "Criterio de exito"). Con un solo
anio de prueba en esta pasada, "por anio" es un solo termino -- se amplia
cuando el dataset cubra mas anios de prueba.

Dos lineas base, ambas ya cerradas en su definicion:
- Climatologica: para una semana del anio de prueba, predice la clase que
  domina esa misma semana calendario en los anios de entrenamiento (moda);
  si esa semana nunca aparece en entrenamiento, usa la moda global de
  entrenamiento. Operacionalizacion propia del concepto "banda tipica
  historica" -- no esta escrita letra por letra en ningun documento
  cerrado, queda documentada aqui para que se pueda auditar o corregir.
- Persistencia: predice la etiqueta REAL de la semana anterior dentro del
  mismo anio de prueba. Declarada no desplegable en vivo (depende de una
  etiqueta que no existe para departamentos desde 2024) -- se calcula solo
  para esta comparacion retrospectiva, con las filas sin semana anterior
  disponible excluidas y contadas aparte, nunca imputadas.

Abierto, NO decidido aqui (no inventar): si el archivo del modelo se
versiona en git o se regenera al desplegar (tarjeta 24, texto original).
Por eso se guarda en data/interim/modelo/, ya excluido del repositorio --
decision reversible, no bloquea nada de lo que sigue.

Uso:
    python3 entrenar_clasificador.py
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support

from corrida_canal_endemico_nacional import ANIOS_BASE

RAIZ = Path(__file__).parent
DATASET_PATH = RAIZ / "data" / "interim" / "dataset_modelado" / "dataset_modelado.csv"
MODELO_DIR = RAIZ / "data" / "interim" / "modelo"
DOCS_DIR = RAIZ.parent.parent / "docs"

ANIO_PRUEBA_DEFAULT = max(ANIOS_BASE)  # 2023 -- "el mas reciente", validación temporal simple
CLASES = ["bajo", "medio", "alto"]


def cargar_dataset() -> list[dict]:
    if not DATASET_PATH.exists():
        raise SystemExit(
            f"No existe {DATASET_PATH}. Correr construir_dataset_modelado.py primero (tarjeta 23)."
        )
    with open(DATASET_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def columnas_feature(fila: dict) -> list[str]:
    return sorted(k for k in fila if k.endswith(("_lag1", "_lag2", "_media_movil4")))


def preparar_matrices(filas: list[dict], cols: list[str]) -> tuple[list[list[float]], list[str]]:
    X = [[float(fila[c]) for c in cols] for fila in filas]
    y = [fila["etiqueta_riesgo"] for fila in filas]
    return X, y


def baseline_climatologica(train: list[dict], test: list[dict]) -> list[str]:
    por_semana: dict[str, Counter] = {}
    global_c = Counter()
    for fila in train:
        semana = fila["semana_epi"]
        por_semana.setdefault(semana, Counter())[fila["etiqueta_riesgo"]] += 1
        global_c[fila["etiqueta_riesgo"]] += 1
    moda_global = global_c.most_common(1)[0][0]

    predicciones = []
    for fila in test:
        c = por_semana.get(fila["semana_epi"])
        predicciones.append(c.most_common(1)[0][0] if c else moda_global)
    return predicciones


def baseline_persistencia(test: list[dict]) -> tuple[list[str | None], list[str], list[bool]]:
    """Devuelve (predicciones, y_real, evaluable) alineadas fila a fila con
    `test` (ya ordenado por semana). evaluable=False donde no hay semana
    anterior contigua dentro del mismo año -- esas filas se excluyen del
    cálculo de métricas, nunca se imputan."""
    test_ordenado = sorted(test, key=lambda f: int(f["semana_epi"]))
    por_semana = {int(f["semana_epi"]): f["etiqueta_riesgo"] for f in test_ordenado}

    predicciones = []
    y_real = []
    evaluable = []
    for fila in test_ordenado:
        semana = int(fila["semana_epi"])
        anterior = por_semana.get(semana - 1)
        predicciones.append(anterior)
        y_real.append(fila["etiqueta_riesgo"])
        evaluable.append(anterior is not None)
    return predicciones, y_real, evaluable


def metricas(y_real: list[str], y_pred: list[str]) -> dict:
    f1_macro = f1_score(y_real, y_pred, labels=CLASES, average="macro", zero_division=0)
    precision, recall, f1_por_clase, soporte = precision_recall_fscore_support(
        y_real, y_pred, labels=CLASES, zero_division=0
    )
    n_alto_real = sum(1 for v in y_real if v == "alto")
    recall_alto = float(recall[CLASES.index("alto")]) if n_alto_real > 0 else None

    return {
        "f1_macro": float(f1_macro),
        "recall_alto": recall_alto,
        "n_alto_real": n_alto_real,
        "por_clase": {
            clase: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1_por_clase[i]),
                "soporte": int(soporte[i]),
            }
            for i, clase in enumerate(CLASES)
        },
        "matriz_confusion": confusion_matrix(y_real, y_pred, labels=CLASES).tolist(),
    }


def formatear_recall_alto(valor: float | None, n_alto_real: int) -> str:
    if valor is None:
        return f"N/A -- 0 casos reales de 'alto' en el conjunto evaluado ({n_alto_real} soporte)"
    return f"{valor:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--anio-prueba", type=int, default=None,
        help=(
            f"Año de prueba a evaluar (default: {ANIO_PRUEBA_DEFAULT}, el más reciente -- "
            "corrida de producción, sobrescribe los artefactos que usa /api/riesgo-nacional). "
            "Con cualquier otro valor, corrida exploratoria: escribe a archivos con sufijo "
            "_prueba<año>, sin tocar los artefactos de producción."
        ),
    )
    args = parser.parse_args()
    es_produccion = args.anio_prueba is None
    global ANIO_PRUEBA
    ANIO_PRUEBA = args.anio_prueba if args.anio_prueba is not None else ANIO_PRUEBA_DEFAULT
    sufijo = "" if es_produccion else f"_prueba{ANIO_PRUEBA}"

    filas = cargar_dataset()
    cols = columnas_feature(filas[0])

    train = [f for f in filas if int(f["anio"]) != ANIO_PRUEBA]
    test = [f for f in filas if int(f["anio"]) == ANIO_PRUEBA]

    if not train or not test:
        raise SystemExit(
            f"Split temporal vacío (train={len(train)}, test={len(test)}). "
            f"Revisar que el dataset cubra el año de prueba {ANIO_PRUEBA}."
        )

    X_train, y_train = preparar_matrices(train, cols)
    X_test, y_test = preparar_matrices(test, cols)

    modelo = RandomForestClassifier(
        n_estimators=300, random_state=42, class_weight="balanced"
    )
    modelo.fit(X_train, y_train)
    y_pred_modelo = modelo.predict(X_test).tolist()
    met_modelo = metricas(y_test, y_pred_modelo)

    y_pred_clima = baseline_climatologica(train, test)
    met_clima = metricas(y_test, y_pred_clima)

    pred_persist, y_real_persist, evaluable = baseline_persistencia(test)
    idx_eval = [i for i, ok in enumerate(evaluable) if ok]
    n_excluidas_persist = len(evaluable) - len(idx_eval)
    if idx_eval:
        met_persist = metricas(
            [y_real_persist[i] for i in idx_eval],
            [pred_persist[i] for i in idx_eval],
        )
    else:
        met_persist = None

    importancias = sorted(zip(cols, modelo.feature_importances_), key=lambda t: -t[1])

    supera_clima = bool(
        met_modelo["f1_macro"] > met_clima["f1_macro"]
        and met_modelo["recall_alto"] is not None
        and met_clima["recall_alto"] is not None
        and met_modelo["recall_alto"] > met_clima["recall_alto"]
    )

    MODELO_DIR.mkdir(parents=True, exist_ok=True)
    modelo_path = MODELO_DIR / f"clasificador_riesgo_nacional_v1{sufijo}.joblib"
    if es_produccion:
        joblib.dump({"modelo": modelo, "columnas_feature": cols, "clases": CLASES}, modelo_path)
    else:
        print(f"Corrida exploratoria (año de prueba {ANIO_PRUEBA} != {ANIO_PRUEBA_DEFAULT}) -- "
              f"NO se sobrescribe el modelo de producción que usa /api/riesgo-nacional. "
              f"Modelo de esta corrida no se guarda (solo el informe y las métricas).")

    metricas_path = MODELO_DIR / f"metricas_modelo{sufijo}.json"
    metricas_path.write_text(
        json.dumps(
            {
                "anio_prueba": ANIO_PRUEBA,
                "anios_entrenamiento": sorted(set(int(f["anio"]) for f in train)),
                "corte_percentil": "P75/P90",
                "f1_macro_modelo": met_modelo["f1_macro"],
                "recall_alto_modelo": met_modelo["recall_alto"],
                "n_alto_real_prueba": met_modelo["n_alto_real"],
                "f1_macro_baseline_climatologica": met_clima["f1_macro"],
                "recall_alto_baseline_climatologica": met_clima["recall_alto"],
                "supera_baseline_climatologica": supera_clima,
                "nota": (
                    (
                        "Recall de 'alto' no evaluable -- el año de prueba no tuvo semanas reales "
                        "'alto' con este corte, no es un fallo del modelo. "
                        f"Ver docs/entrenamiento-clasificador-riesgo-nacional{sufijo}.md."
                    ) if met_modelo["n_alto_real"] == 0 else (
                        f"Recall de 'alto' SI evaluable ({met_modelo['n_alto_real']} semanas reales "
                        f"en el año de prueba): {met_modelo['recall_alto']:.3f} para el modelo, "
                        f"{met_clima['recall_alto']:.3f} para la línea base climatológica. "
                        f"Ver docs/entrenamiento-clasificador-riesgo-nacional{sufijo}.md."
                    )
                ),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Entrenamiento: {len(train)} filas ({', '.join(str(a) for a in ANIOS_BASE if a != ANIO_PRUEBA)}).")
    print(f"Prueba: {len(test)} filas (año {ANIO_PRUEBA}).")
    print(f"Distribución real en prueba: {dict(Counter(y_test))}")
    print()
    print(f"MODELO       -- F1 macro: {met_modelo['f1_macro']:.3f}  |  "
          f"Recall 'alto': {formatear_recall_alto(met_modelo['recall_alto'], met_modelo['n_alto_real'])}")
    print(f"Base clima   -- F1 macro: {met_clima['f1_macro']:.3f}  |  "
          f"Recall 'alto': {formatear_recall_alto(met_clima['recall_alto'], met_clima['n_alto_real'])}")
    if met_persist:
        print(f"Base persist -- F1 macro: {met_persist['f1_macro']:.3f}  |  "
              f"Recall 'alto': {formatear_recall_alto(met_persist['recall_alto'], met_persist['n_alto_real'])} "
              f"({n_excluidas_persist} filas excluidas sin semana anterior)")
    else:
        print("Base persist -- no evaluable (ninguna fila con semana anterior contigua en el año de prueba).")

    print(f"\n¿Supera a la línea base climatológica en F1 macro Y recall de 'alto' (criterio decisivo)? "
          f"{'Sí' if supera_clima else 'No calculable o no' } "
          f"-- {ANIO_PRUEBA} tiene {met_modelo['n_alto_real']} semanas reales de 'alto', "
          f"así que el recall de 'alto' {'no es evaluable este año' if met_modelo['n_alto_real'] == 0 else 'sí es evaluable'}.")

    if es_produccion:
        print(f"\nModelo guardado -> {modelo_path} (NO versionado en git, ver docstring del script).")

    print("\nImportancia de variables (top 10):")
    for nombre, imp in importancias[:10]:
        print(f"  {nombre}: {imp:.4f}")

    docs_path = DOCS_DIR / f"entrenamiento-clasificador-riesgo-nacional{sufijo}.md"
    escribir_documento(
        cols, train, test, met_modelo, met_clima, met_persist, n_excluidas_persist,
        importancias, modelo_path, supera_clima, docs_path, es_produccion,
    )
    print(f"\nInforme consultable -> {docs_path}")


def escribir_documento(cols, train, test, met_modelo, met_clima, met_persist,
                        n_excluidas_persist, importancias, modelo_path, supera_clima,
                        docs_path: Path, es_produccion: bool) -> None:
    dist_test = Counter(f["etiqueta_riesgo"] for f in test)

    def tabla_metricas(met: dict) -> str:
        filas = ["| Clase | Precisión | Recall | F1 | Soporte |", "|---|---|---|---|---|"]
        for clase in CLASES:
            m = met["por_clase"][clase]
            filas.append(f"| {clase} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['soporte']} |")
        return "\n".join(filas)

    def tabla_matriz(met: dict) -> str:
        cm = met["matriz_confusion"]
        filas = ["| real \\ predicho | " + " | ".join(CLASES) + " |", "|---|" + "---|" * len(CLASES)]
        for i, clase in enumerate(CLASES):
            filas.append(f"| **{clase}** | " + " | ".join(str(v) for v in cm[i]) + " |")
        return "\n".join(filas)

    if es_produccion:
        artefacto_md = (
            f"Guardado en `{modelo_path.relative_to(modelo_path.parent.parent.parent.parent)}` — "
            "**no versionado en git** (vive bajo `data/interim/`, ya excluido). Si el archivo debe "
            "versionarse o regenerarse en cada despliegue sigue siendo una decisión abierta del "
            "coordinador (tarjeta 24) — no se resolvió aquí, se tomó el default reversible que no "
            "bloquea el resto de la cadena."
        )
    else:
        artefacto_md = (
            "**Corrida exploratoria — el modelo de este entrenamiento NO se guardó.** Este año de "
            "prueba es distinto al de producción, así que no se sobrescribió "
            "`clasificador_riesgo_nacional_v1.joblib` (el que usa `/api/riesgo-nacional`). Este "
            "informe es solo para evaluar la métrica decisiva con un año que sí tiene casos reales "
            "de \"alto\"; si se necesita el modelo de esta corrida más adelante, correr de nuevo el "
            "script con el mismo --anio-prueba."
        )

    if met_modelo["n_alto_real"] == 0:
        hallazgo_md = (
            f"**Hallazgo a declarar sin maquillar:** el año de prueba {ANIO_PRUEBA} no tiene ninguna semana "
            'etiquetada "alto" con el corte P75/P90 (todas las semanas cayeron en "bajo" o "medio" según la '
            'línea base de entrenamiento). Eso hace que el recall de "alto" — la métrica decisiva del criterio '
            "de éxito — no sea calculable este año de prueba, no porque el modelo falle en detectarlo sino "
            "porque no hay ningún caso real que detectar. No se debe citar esta corrida como evidencia de que "
            'el modelo funciona o falla en la clase alta; hace falta un año de prueba con casos reales de '
            '"alto" para que esa parte del criterio sea evaluable.'
        )
    else:
        hallazgo_md = (
            f"**Hallazgo a declarar sin maquillar:** el año de prueba {ANIO_PRUEBA} tiene "
            f"{met_modelo['n_alto_real']} semanas reales etiquetadas \"alto\" con el corte P75/P90 -- "
            f"el recall de \"alto\" del modelo fue **{formatear_recall_alto(met_modelo['recall_alto'], met_modelo['n_alto_real'])}** "
            "(la línea base climatológica obtuvo el mismo resultado). "
            + (
                "El modelo no acertó ni una sola de esas semanas reales de alto riesgo -- con los predictores "
                "y el corte actuales, el clima rezagado solo no está capturando la señal de brote severo en "
                "este año de prueba. No es un hallazgo menor: contradice directamente la promesa de "
                "anticipación del proyecto y debe citarse así en el informe, no suavizarse."
                if met_modelo["recall_alto"] == 0
                else "Revisar la matriz de confusión de abajo para ver en qué se equivocó exactamente."
            )
        )

    if met_modelo["n_alto_real"] == 0:
        veredicto_md = (
            f"con {met_modelo['n_alto_real']} semanas reales de \"alto\" en {ANIO_PRUEBA}, la mitad del "
            "criterio no es evaluable esta pasada (ver hallazgo arriba). Se necesita repetir esta "
            "evaluación cuando el conjunto de prueba incluya un año con semanas \"alto\" reales "
            "(ej. usando 2019 o 2022 como año de prueba en una pasada futura)."
        )
    else:
        veredicto_md = (
            f"con {met_modelo['n_alto_real']} semanas reales de \"alto\" en {ANIO_PRUEBA}, el criterio "
            f"sí es evaluable esta pasada: recall de \"alto\" del modelo = "
            f"{formatear_recall_alto(met_modelo['recall_alto'], met_modelo['n_alto_real'])}, de la línea "
            f"base climatológica = {formatear_recall_alto(met_clima['recall_alto'], met_clima['n_alto_real'])}."
        )

    persist_md = "No evaluable (ninguna fila con semana anterior contigua en el año de prueba)."
    if met_persist:
        persist_md = (
            f"F1 macro: {met_persist['f1_macro']:.3f} · "
            f"Recall 'alto': {formatear_recall_alto(met_persist['recall_alto'], met_persist['n_alto_real'])} "
            f"({n_excluidas_persist} filas excluidas por no tener semana anterior contigua)\n\n"
            + tabla_metricas(met_persist)
        )

    contenido = f"""# Entrenamiento del clasificador de riesgo nacional (tarjeta 24)

> Generado por `backend/ingestion/entrenar_clasificador.py`. Primera pasada del Hito 2 (2026-08-15) —
> se acepta un resultado malo esta semana; la meta es que la cadena de datos a pantalla funcione.
> No reescribir a mano — regenerar corriendo el script sobre el dataset actualizado.

## Configuración

- **Entrenamiento:** {len(train)} filas, años {', '.join(str(a) for a in sorted(set(int(f['anio']) for f in train)))}.
- **Prueba:** {len(test)} filas, año {ANIO_PRUEBA} (validación temporal simple, cerrada en `docs/contexto/01-decisiones-cerradas.md`).
- **Predictores:** {len(cols)} variables de clima rezagado (rezago 1, rezago 2, media móvil 4 semanas — 7 variables climáticas). Ningún dato de casos entra como predictor (decisión cerrada 2026-08-09).
- **Corte de etiqueta:** P75/P90 (cerrado 2026-08-15 — no es el que reproduce el canal endémico OPS/PAHO verificado, que da P50/P75; ver `docs/contexto/01-decisiones-cerradas.md`).
- **Modelo:** `RandomForestClassifier` (scikit-learn), 300 árboles, `class_weight="balanced"`, semilla fija 42.
- **Distribución real del año de prueba ({ANIO_PRUEBA}):** {dict(dist_test)}.

{hallazgo_md}

## Modelo — métricas por clase

F1 macro: **{met_modelo['f1_macro']:.3f}** · Recall 'alto': **{formatear_recall_alto(met_modelo['recall_alto'], met_modelo['n_alto_real'])}**

{tabla_metricas(met_modelo)}

### Matriz de confusión (modelo)

{tabla_matriz(met_modelo)}

## Línea base climatológica

F1 macro: **{met_clima['f1_macro']:.3f}** · Recall 'alto': **{formatear_recall_alto(met_clima['recall_alto'], met_clima['n_alto_real'])}**

{tabla_metricas(met_clima)}

*Definición operacional (no está en `01-decisiones-cerradas.md` letra por letra, documentada aquí para
poder auditarla o corregirla): para cada semana del año de prueba, predice la clase que más veces
apareció esa misma semana calendario en los años de entrenamiento; si esa semana nunca apareció en
entrenamiento, usa la clase más frecuente en todo el conjunto de entrenamiento.*

## Línea base de persistencia (no desplegable en vivo — solo referencia retrospectiva)

{persist_md}

## ¿Supera el modelo a la línea base climatológica? (criterio decisivo, `01-decisiones-cerradas.md`)

**{'Sí' if supera_clima else 'No'}.** El criterio exige superar la
climatológica en F1 macro **y** en recall de "alto", por año de prueba — {veredicto_md}

## Importancia de variables (top 10, Random Forest)

| Variable | Importancia |
|---|---|
{chr(10).join(f"| {nombre} | {imp:.4f} |" for nombre, imp in importancias[:10])}

## Artefacto del modelo

{artefacto_md}
"""
    docs_path.write_text(contenido, encoding="utf-8")


if __name__ == "__main__":
    main()
