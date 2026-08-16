# Entrenamiento del clasificador de riesgo nacional (tarjeta 24)

> Generado por `backend/ingestion/entrenar_clasificador.py`. Primera pasada del Hito 2 (2026-08-15) —
> se acepta un resultado malo esta semana; la meta es que la cadena de datos a pantalla funcione.
> No reescribir a mano — regenerar corriendo el script sobre el dataset actualizado.

## Configuración

- **Entrenamiento:** 200 filas, años 2018, 2019, 2021, 2022.
- **Prueba:** 50 filas, año 2023 (validación temporal simple, cerrada en `docs/contexto/01-decisiones-cerradas.md`).
- **Predictores:** 21 variables de clima rezagado (rezago 1, rezago 2, media móvil 4 semanas — 7 variables climáticas). Ningún dato de casos entra como predictor (decisión cerrada 2026-08-09).
- **Corte de etiqueta:** P75/P90 (cerrado 2026-08-15 — no es el que reproduce el canal endémico OPS/PAHO verificado, que da P50/P75; ver `docs/contexto/01-decisiones-cerradas.md`).
- **Modelo:** `RandomForestClassifier` (scikit-learn), 300 árboles, `class_weight="balanced"`, semilla fija 42.
- **Distribución real del año de prueba (2023):** {'bajo': 50}.

**Hallazgo a declarar sin maquillar:** el año de prueba 2023 no tiene ninguna semana etiquetada "alto" con el corte P75/P90 (todas las semanas cayeron en "bajo" o "medio" según la línea base de entrenamiento). Eso hace que el recall de "alto" — la métrica decisiva del criterio de éxito — no sea calculable este año de prueba, no porque el modelo falle en detectarlo sino porque no hay ningún caso real que detectar. No se debe citar esta corrida como evidencia de que el modelo funciona o falla en la clase alta; hace falta un año de prueba con casos reales de "alto" para que esa parte del criterio sea evaluable.

## Modelo — métricas por clase

F1 macro: **0.265** · Recall 'alto': **N/A -- 0 casos reales de 'alto' en el conjunto evaluado (0 soporte)**

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 1.000 | 0.660 | 0.795 | 50 |
| medio | 0.000 | 0.000 | 0.000 | 0 |
| alto | 0.000 | 0.000 | 0.000 | 0 |

### Matriz de confusión (modelo)

| real \ predicho | bajo | medio | alto |
|---|---|---|---|
| **bajo** | 33 | 1 | 16 |
| **medio** | 0 | 0 | 0 |
| **alto** | 0 | 0 | 0 |

## Línea base climatológica

F1 macro: **0.333** · Recall 'alto': **N/A -- 0 casos reales de 'alto' en el conjunto evaluado (0 soporte)**

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 1.000 | 1.000 | 1.000 | 50 |
| medio | 0.000 | 0.000 | 0.000 | 0 |
| alto | 0.000 | 0.000 | 0.000 | 0 |

*Definición operacional (no está en `01-decisiones-cerradas.md` letra por letra, documentada aquí para
poder auditarla o corregirla): para cada semana del año de prueba, predice la clase que más veces
apareció esa misma semana calendario en los años de entrenamiento; si esa semana nunca apareció en
entrenamiento, usa la clase más frecuente en todo el conjunto de entrenamiento.*

## Línea base de persistencia (no desplegable en vivo — solo referencia retrospectiva)

F1 macro: 0.333 · Recall 'alto': N/A -- 0 casos reales de 'alto' en el conjunto evaluado (0 soporte) (1 filas excluidas por no tener semana anterior contigua)

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 1.000 | 1.000 | 1.000 | 49 |
| medio | 0.000 | 0.000 | 0.000 | 0 |
| alto | 0.000 | 0.000 | 0.000 | 0 |

## ¿Supera el modelo a la línea base climatológica? (criterio decisivo, `01-decisiones-cerradas.md`)

**No.** El criterio exige superar la
climatológica en F1 macro **y** en recall de "alto", por año de prueba — con 0 semanas reales de "alto" en 2023, la mitad del criterio no es evaluable esta pasada (ver hallazgo arriba). Se necesita repetir esta evaluación cuando el conjunto de prueba incluya un año con semanas "alto" reales (ej. usando 2019 o 2022 como año de prueba en una pasada futura).

## Importancia de variables (top 10, Random Forest)

| Variable | Importancia |
|---|---|
| temp_max_media_movil4 | 0.0611 |
| temp_min_media_movil4 | 0.0566 |
| temp_max_lag2 | 0.0537 |
| punto_rocio_media_movil4 | 0.0535 |
| humedad_relativa_media_lag2 | 0.0524 |
| temp_media_lag1 | 0.0517 |
| humedad_relativa_media_lag1 | 0.0513 |
| temp_media_media_movil4 | 0.0506 |
| precipitation_sum_media_movil4 | 0.0491 |
| punto_rocio_lag1 | 0.0490 |

## Artefacto del modelo

Guardado en `data/interim/modelo/clasificador_riesgo_nacional_v1.joblib` — **no versionado en git** (vive bajo `data/interim/`, ya excluido). Si el archivo debe versionarse o regenerarse en cada despliegue sigue siendo una decisión abierta del coordinador (tarjeta 24) — no se resolvió aquí, se tomó el default reversible que no bloquea el resto de la cadena.
