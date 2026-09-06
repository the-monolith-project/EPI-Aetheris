# Entrenamiento del clasificador de riesgo nacional (tarjeta 24)

> Generado por `backend/ingestion/entrenar_clasificador.py`. Primera pasada del Hito 2 (2026-08-15) —
> se acepta un resultado malo esta semana; la meta es que la cadena de datos a pantalla funcione.
> No reescribir a mano — regenerar corriendo el script sobre el dataset actualizado.

## Configuración

- **Entrenamiento:** 200 filas, años 2018, 2019, 2021, 2023.
- **Prueba:** 50 filas, año 2022 (validación temporal simple, cerrada en `docs/contexto/01-decisiones-cerradas.md`).
- **Predictores:** 24 variables de clima rezagado (rezago 1, rezago 2, media móvil 4 semanas — 7 variables climáticas). Ningún dato de casos entra como predictor (decisión cerrada 2026-08-09).
- **Corte de etiqueta:** P75/P90 (cerrado 2026-08-15 — no es el que reproduce el canal endémico OPS/PAHO verificado, que da P50/P75; ver `docs/contexto/01-decisiones-cerradas.md`).
- **Modelo:** `RandomForestClassifier` (scikit-learn), 300 árboles, `class_weight="balanced"`, semilla fija 42.
- **Distribución real del año de prueba (2022):** {'alto': 22, 'medio': 9, 'bajo': 19}.

**Hallazgo a declarar sin maquillar:** el año de prueba 2022 tiene 22 semanas reales etiquetadas "alto" con el corte P75/P90 -- el recall de "alto" del modelo fue **0.000** (la línea base climatológica obtuvo el mismo resultado). El modelo no acertó ni una sola de esas semanas reales de alto riesgo -- con los predictores y el corte actuales, el clima rezagado solo no está capturando la señal de brote severo en este año de prueba. No es un hallazgo menor: contradice directamente la promesa de anticipación del proyecto y debe citarse así en el informe, no suavizarse.

## Modelo — métricas por clase

F1 macro: **0.184** · Recall 'alto': **0.000**

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 0.380 | 1.000 | 0.551 | 19 |
| medio | 0.000 | 0.000 | 0.000 | 9 |
| alto | 0.000 | 0.000 | 0.000 | 22 |

### Matriz de confusión (modelo)

| real \ predicho | bajo | medio | alto |
|---|---|---|---|
| **bajo** | 19 | 0 | 0 |
| **medio** | 9 | 0 | 0 |
| **alto** | 22 | 0 | 0 |

## Línea base climatológica

F1 macro: **0.184** · Recall 'alto': **0.000**

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 0.380 | 1.000 | 0.551 | 19 |
| medio | 0.000 | 0.000 | 0.000 | 9 |
| alto | 0.000 | 0.000 | 0.000 | 22 |

*Definición operacional (no está en `01-decisiones-cerradas.md` letra por letra, documentada aquí para
poder auditarla o corregirla): para cada semana del año de prueba, predice la clase que más veces
apareció esa misma semana calendario en los años de entrenamiento; si esa semana nunca apareció en
entrenamiento, usa la clase más frecuente en todo el conjunto de entrenamiento.*

## Línea base de persistencia (no desplegable en vivo — solo referencia retrospectiva)

F1 macro: 0.894 · Recall 'alto': 0.952 (1 filas excluidas por no tener semana anterior contigua)

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 1.000 | 0.947 | 0.973 | 19 |
| medio | 0.778 | 0.778 | 0.778 | 9 |
| alto | 0.909 | 0.952 | 0.930 | 21 |

## ¿Supera el modelo a la línea base climatológica? (criterio decisivo, `01-decisiones-cerradas.md`)

**No.** El criterio exige superar la
climatológica en F1 macro **y** en recall de "alto", por año de prueba — con 22 semanas reales de "alto" en 2022, el criterio sí es evaluable esta pasada: recall de "alto" del modelo = 0.000, de la línea base climatológica = 0.000.

## Importancia de variables (top 10, Random Forest)

| Variable | Importancia |
|---|---|
| oni_anom_media_movil4 | 0.1710 |
| oni_anom_lag2 | 0.1399 |
| oni_anom_lag1 | 0.1177 |
| humedad_relativa_media_media_movil4 | 0.0401 |
| punto_rocio_media_movil4 | 0.0387 |
| temp_min_media_movil4 | 0.0376 |
| temp_max_media_movil4 | 0.0353 |
| precipitation_hours_media_movil4 | 0.0332 |
| humedad_relativa_media_lag2 | 0.0331 |
| punto_rocio_lag1 | 0.0325 |

## Artefacto del modelo

**Corrida exploratoria — el modelo de este entrenamiento NO se guardó.** El año de prueba y/o el corte de percentil son distintos a los de producción, así que no se sobrescribió `clasificador_riesgo_nacional_v1.joblib` (el que usa `/api/riesgo-nacional`). Si se necesita el modelo de esta corrida más adelante, correr de nuevo el script con los mismos `--anio-prueba`/`--corte`.
