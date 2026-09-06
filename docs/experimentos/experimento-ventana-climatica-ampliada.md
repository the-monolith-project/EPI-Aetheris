# Experimento descartado: ventana de rezago climático ampliada (2026-08-16)

> Registro del experimento y su resultado negativo, para que nadie lo reintente sin una hipótesis
> distinta. El código vigente usa la ventana original (rezago 1-2 semanas + media móvil de 4
> semanas) -- ver `backend/ingestion/construir_dataset_modelado.py`, `VENTANAS_MEDIA_MOVIL`.

## Motivación

Las corridas de evaluación con año de prueba 2019 y 2022 (los únicos dos años de la ventana con
semanas reales etiquetadas "alto") mostraron que el clasificador obtenía **recall de "alto" = 0.000**
en ambos -- empatado con la línea base climatológica, es decir, ninguno de los dos detecta el brote.
Hipótesis a probar: la ventana de rezago era demasiado corta (1-4 semanas) para el ciclo
mosquito-transmisión, que típicamente acumula condiciones climáticas favorables durante 2-3 meses,
no 1.

## Cambio probado

`VENTANAS_MEDIA_MOVIL` de `(4,)` a `(4, 8, 12)` semanas, manteniendo los rezagos simples de 1 y 2
semanas sin cambio. Esto pasó de 21 a 35 columnas de predictores (7 variables climáticas × (2 rezagos
+ 3 medias móviles)).

## Resultado

| Año de prueba | Recall "alto" -- ventana original | Recall "alto" -- ventana ampliada |
|---|---|---|
| 2019 | 0.000 | 0.000 |
| 2022 | 0.000 | 0.000 |

**Sin cambio en la métrica que se quería mover.** Efectos colaterales, todos negativos o neutros:

- F1 macro del modelo de producción (año de prueba 2023) **empeoró**: 0,265 → 0,21.
- F1 macro en 2022 mejoró levemente (0,169 → 0,194, supera a la climatológica en esa sola métrica),
  pero no cambia el veredicto del criterio decisivo porque el recall de "alto" sigue en 0.000.
- Se perdieron más semanas al inicio de 2018 por necesitar 12 semanas de historia previa (11
  descartadas por historia climática insuficiente, contra 3 con la ventana original).

## Conclusión

La hipótesis de "ventana muy corta" queda **descartada** por evidencia, no por intuición. El
estancamiento en recall = 0.000 para la clase "alto" en los dos años reales de prueba disponibles es
consistente con una explicación estructural, no de ingeniería de features: el predictor del modelo es
**únicamente clima rezagado** (decisión cerrada 2026-08-09, `docs/contexto/01-decisiones-cerradas.md`)
-- sin autocorrelación de casos, sin momentum epidémico. La línea base de persistencia (predice la
etiqueta real de la semana anterior) sí acierta con recall alto (0,929 en 2019, 0,952 en 2022),
precisamente porque explota esa autocorrelación que el modelo de producción tiene prohibido usar. Un
brote severo puede tener una dinámica que el clima solo, a esta resolución semanal y sin señal de
casos, no está anticipando.

**No reabrir este experimento sin una hipótesis distinta** (ej. otra familia de modelo, otras
variables no climáticas, o revisar si el corte P75/P90 en sí mismo hace la clase "alto" demasiado
rara para aprenderse con ~200 filas de entrenamiento). Ampliar más la ventana de rezago no es un
camino prometedor por sí solo, ya se probó.

## Reproducibilidad

```bash
# Ventana ampliada (para replicar este experimento si hiciera falta):
# 1. Editar VENTANAS_MEDIA_MOVIL = (4, 8, 12) en construir_dataset_modelado.py
# 2. python3 construir_dataset_modelado.py
# 3. python3 entrenar_clasificador.py --anio-prueba 2019
# 4. python3 entrenar_clasificador.py --anio-prueba 2022
# (no sobrescribe el modelo de producción -- ver entrenar_clasificador.py, es_produccion)
```
