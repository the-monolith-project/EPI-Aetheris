# Entrenamiento del clasificador de riesgo nacional (tarjeta 24)

> Generado por `backend/ingestion/entrenar_clasificador.py`. Primera pasada del Hito 2 (2026-08-15) —
> se acepta un resultado malo esta semana; la meta es que la cadena de datos a pantalla funcione.
> No reescribir a mano — regenerar corriendo el script sobre el dataset actualizado.

## Configuración

- **Entrenamiento:** 412 filas, años 2014, 2015, 2016, 2017, 2018, 2021, 2022, 2023.
- **Prueba:** 52 filas, año 2019 (validación temporal simple, cerrada en `docs/contexto/01-decisiones-cerradas.md`).
- **Predictores:** 24 variables de clima rezagado (rezago 1, rezago 2, media móvil 4 semanas — 7 variables climáticas). Ningún dato de casos entra como predictor (decisión cerrada 2026-08-09).
- **Corte de etiqueta:** P75/P90 (cerrado 2026-08-15 — no es el que reproduce el canal endémico OPS/PAHO verificado, que da P50/P75; ver `docs/contexto/01-decisiones-cerradas.md`).
- **Modelo:** `RandomForestClassifier` (scikit-learn), 300 árboles, `class_weight="balanced"`, semilla fija 42.
- **Distribución real del año de prueba (2019):** {'bajo': 27, 'medio': 24, 'alto': 1}.

**Hallazgo a declarar sin maquillar:** el año de prueba 2019 tiene 1 semanas reales etiquetadas "alto" con el corte P75/P90 -- el recall de "alto" del modelo fue **0.000** (la línea base climatológica obtuvo el mismo resultado). El modelo no acertó ni una sola de esas semanas reales de alto riesgo -- con los predictores y el corte actuales, el clima rezagado solo no está capturando la señal de brote severo en este año de prueba. No es un hallazgo menor: contradice directamente la promesa de anticipación del proyecto y debe citarse así en el informe, no suavizarse.

## Modelo — métricas por clase

F1 macro: **0.257** · Recall 'alto': **0.000**

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 0.529 | 1.000 | 0.692 | 27 |
| medio | 1.000 | 0.042 | 0.080 | 24 |
| alto | 0.000 | 0.000 | 0.000 | 1 |

### Matriz de confusión (modelo)

| real \ predicho | bajo | medio | alto |
|---|---|---|---|
| **bajo** | 27 | 0 | 0 |
| **medio** | 23 | 1 | 0 |
| **alto** | 1 | 0 | 0 |

## Línea base climatológica

F1 macro: **0.228** · Recall 'alto': **0.000**

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 0.519 | 1.000 | 0.684 | 27 |
| medio | 0.000 | 0.000 | 0.000 | 24 |
| alto | 0.000 | 0.000 | 0.000 | 1 |

*Definición operacional (no está en `01-decisiones-cerradas.md` letra por letra, documentada aquí para
poder auditarla o corregirla): para cada semana del año de prueba, predice la clase que más veces
apareció esa misma semana calendario en los años de entrenamiento; si esa semana nunca apareció en
entrenamiento, usa la clase más frecuente en todo el conjunto de entrenamiento.*

## Línea base de persistencia (no desplegable en vivo — solo referencia retrospectiva)

F1 macro: 0.613 · Recall 'alto': 0.000 (1 filas excluidas por no tener semana anterior contigua)

| Clase | Precisión | Recall | F1 | Soporte |
|---|---|---|---|---|
| bajo | 0.923 | 0.923 | 0.923 | 26 |
| medio | 0.917 | 0.917 | 0.917 | 24 |
| alto | 0.000 | 0.000 | 0.000 | 1 |

## ¿Supera el modelo a la línea base climatológica? (criterio decisivo, `01-decisiones-cerradas.md`)

**No.** El criterio exige superar la
climatológica en F1 macro **y** en recall de "alto", por año de prueba — con 1 semanas reales de "alto" en 2019, el criterio sí es evaluable esta pasada: recall de "alto" del modelo = 0.000, de la línea base climatológica = 0.000.

## Importancia de variables (top 10, Random Forest)

| Variable | Importancia |
|---|---|
| oni_anom_lag1 | 0.1001 |
| oni_anom_lag2 | 0.0882 |
| oni_anom_media_movil4 | 0.0878 |
| temp_media_media_movil4 | 0.0559 |
| temp_min_media_movil4 | 0.0482 |
| punto_rocio_media_movil4 | 0.0473 |
| temp_media_lag1 | 0.0443 |
| temp_min_lag1 | 0.0414 |
| precipitation_hours_media_movil4 | 0.0382 |
| temp_min_lag2 | 0.0362 |

## Artefacto del modelo

**Corrida exploratoria — el modelo de este entrenamiento NO se guardó.** El año de prueba y/o el corte de percentil son distintos a los de producción, así que no se sobrescribió `clasificador_riesgo_nacional_v1.joblib` (el que usa `/api/riesgo-nacional`). Si se necesita el modelo de esta corrida más adelante, correr de nuevo el script con los mismos `--anio-prueba`/`--corte`.
