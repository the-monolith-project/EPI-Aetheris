# Entrenamiento del clasificador de riesgo nacional (tarjeta 24)

> Generado por `backend/ingestion/entrenar_clasificador.py`. Primera pasada del Hito 2 (2026-08-15) —
> se acepta un resultado malo esta semana; la meta es que la cadena de datos a pantalla funcione.
> No reescribir a mano — regenerar corriendo el script sobre el dataset actualizado.

## Configuración

- **Entrenamiento:** 197 filas, años 2018, 2019, 2021, 2023.
- **Prueba:** 50 filas, año 2022 (validación temporal simple, cerrada en `docs/contexto/01-decisiones-cerradas.md`).
- **Predictores:** 21 variables de clima rezagado (rezago 1, rezago 2, media móvil 4 semanas — 7 variables climáticas). Ningún dato de casos entra como predictor (decisión cerrada 2026-08-09).
- **Corte de etiqueta:** P50/P75 (EXPLORATORIO -- no es el corte de producción; ver más abajo).
- **Modelo:** `RandomForestClassifier` (scikit-learn), 300 árboles, `class_weight="balanced"`, semilla fija 42.
- **Distribución real del año de prueba (2022):** {'alto': 31, 'medio': 9, 'bajo': 10}.

**Hallazgo a declarar sin maquillar:** el año de prueba 2022 tiene 31 semanas reales etiquetadas "alto" con el corte P50/P75 -- el recall de "alto" del modelo fue **0.065** (la línea base climatológica obtuvo el mismo resultado). Revisar la matriz de confusión de abajo para ver en qué se equivocó exactamente.

## Modelo — métricas por clase

F1 macro: **0.103** · Recall 'alto': **0.065**

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 0.135 | 0.500 | 0.213 | 10 |
| medio | 0.000 | 0.000 | 0.000 | 9 |
| alto | 0.182 | 0.065 | 0.095 | 31 |

### Matriz de confusión (modelo)

| real \ predicho | bajo | medio | alto |
|---|---|---|---|
| **bajo** | 5 | 0 | 5 |
| **medio** | 5 | 0 | 4 |
| **alto** | 27 | 2 | 2 |

## Línea base climatológica

F1 macro: **0.061** · Recall 'alto': **0.000**

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 0.111 | 0.500 | 0.182 | 10 |
| medio | 0.000 | 0.000 | 0.000 | 9 |
| alto | 0.000 | 0.000 | 0.000 | 31 |

*Definición operacional (no está en `01-decisiones-cerradas.md` letra por letra, documentada aquí para
poder auditarla o corregirla): para cada semana del año de prueba, predice la clase que más veces
apareció esa misma semana calendario en los años de entrenamiento; si esa semana nunca apareció en
entrenamiento, usa la clase más frecuente en todo el conjunto de entrenamiento.*

## Línea base de persistencia (no desplegable en vivo — solo referencia retrospectiva)

F1 macro: 0.868 · Recall 'alto': 1.000 (1 filas excluidas por no tener semana anterior contigua)

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 0.889 | 0.800 | 0.842 | 10 |
| medio | 0.778 | 0.778 | 0.778 | 9 |
| alto | 0.968 | 1.000 | 0.984 | 30 |

## ¿Supera el modelo a la línea base climatológica? (criterio decisivo, `01-decisiones-cerradas.md`)

**Sí.** El criterio exige superar la
climatológica en F1 macro **y** en recall de "alto", por año de prueba — con 31 semanas reales de "alto" en 2022, el criterio sí es evaluable esta pasada: recall de "alto" del modelo = 0.065, de la línea base climatológica = 0.000.

## Importancia de variables (top 10, Random Forest)

| Variable | Importancia |
|---|---|
| temp_min_media_movil4 | 0.0633 |
| punto_rocio_media_movil4 | 0.0611 |
| temp_max_media_movil4 | 0.0611 |
| temp_media_media_movil4 | 0.0606 |
| humedad_relativa_media_media_movil4 | 0.0572 |
| precipitation_sum_lag1 | 0.0561 |
| precipitation_sum_media_movil4 | 0.0484 |
| precipitation_hours_media_movil4 | 0.0470 |
| humedad_relativa_media_lag2 | 0.0459 |
| precipitation_hours_lag1 | 0.0445 |

## Artefacto del modelo

**Corrida exploratoria — el modelo de este entrenamiento NO se guardó.** El año de prueba y/o el corte de percentil son distintos a los de producción, así que no se sobrescribió `clasificador_riesgo_nacional_v1.joblib` (el que usa `/api/riesgo-nacional`). Si se necesita el modelo de esta corrida más adelante, correr de nuevo el script con los mismos `--anio-prueba`/`--corte`.
