# Experimento: ONI (El Niño) como predictor adicional (2026-08-16)

> Registro del experimento y su resultado, para no reintentarlo sin una hipótesis distinta. El
> índice ONI **sí quedó cargado en Postgres** (ADR 0008, migración `0006`, `variable_ambientales`
> con `variable='oni_anom'`, región `SV`) — lo que se descarta aquí es su uso como predictor del
> modelo de producción, no la carga del dato en sí, que sigue siendo real y verificada.

## Motivación

Dos hallazgos previos (ver `docs/experimento-ventana-climatica-ampliada.md` y el CHANGELOG,
entradas 2026-08-16) mostraron que el clima local rezagado no anticipa las semanas reales "alto"
en ningún año de prueba disponible (recall = 0.000 en 2019 y 2022). El índice ONI de NOAA
(anomalía de temperatura superficial del mar, escala oceánica) está documentado en la literatura
como factor asociado a brotes de dengue centroamericanos vía condiciones favorables a la cría del
vector durante El Niño. Verificado además con datos reales del proyecto: el promedio anual de ONI
correlaciona visualmente con los años de brote conocidos (2015 = 1.48, El Niño fuerte; 2019 = 0.65,
El Niño moderado; 2021-2022 = negativo, La Niña, años bajos) — una señal prometedora antes de
probarlo como feature.

## Cambio probado

`oni_anom` agregado a `VARIABLES_CLIMA` (mismos rezagos/media móvil que las 7 variables
climáticas ya existentes), en dos configuraciones:

1. Ventana de producción (2018-2023) + ONI.
2. Ventana ampliada (2014-2023, ver experimento de años) + ONI.

## Resultado

| Configuración | Año de prueba | Recall "alto" sin ONI | Recall "alto" con ONI |
|---|---|---|---|
| 2018-2023 | 2019 | 0.000 | 0.000 |
| 2018-2023 | 2022 | 0.000 | 0.000 |
| 2014-2023 | 2014 | **0.031** (único caso con señal) | **0.000** (regresión) |
| 2014-2023 | 2019 | 0.000 | 0.000 |
| 2014-2023 | 2022 | 0.000 | 0.000 |

**Sin mejora en ningún caso, y una regresión en el único caso donde antes había señal real** (2014
con la ventana ampliada pasó de acertar 1 de 32 semanas "alto" a no acertar ninguna). El F1 macro
del modelo en 2022 (ventana de producción) subió levemente hasta empatar con la línea base
climatológica (0.169→0.184), pero eso no cambia el veredicto del criterio decisivo.

## Interpretación

Esto no invalida la hipótesis de que El Niño esté asociado al riesgo real de dengue en El Salvador
— la correlación agregada anual (visible en los promedios de ONI por año) sigue siendo real y
consistente con la literatura. Lo que muestra el experimento es que, **agregado como una feature
más al mismo Random Forest con rezagos/medias móviles semanales**, no le da al modelo algo
utilizable para clasificar semanas individuales -- probablemente porque ONI varía muy poco
semana a semana dentro de un mismo mes (por diseño, es un índice mensual difundido igual a cada
semana, ver ADR 0008 punto C) y el modelo ya tiene 8 variables con la misma estructura de rezagos
sin encontrar la frontera de decisión. Es consistente con la conclusión ya escrita en el
experimento de ventana: el problema parece ser de **falta de señal accionable a resolución
semanal**, no de qué tan pocas o muchas variables climáticas se agreguen a la misma arquitectura.

## Qué NO se prueba con esto

No se probó ONI como variable de un modelo distinto (ej. una regresión a nivel anual/estacional en
vez de semanal, donde su resolución mensual encajaría mejor de forma nativa). Eso queda fuera de
alcance de este experimento -- no descarta que ONI sirva en un framing distinto del problema, sólo
que no sirve en el framing semanal actual.

## Reproducibilidad

```bash
python3 cargar_oni.py                                    # ya corrido, datos en Postgres
python3 construir_dataset_modelado.py --incluir-oni       # ventana de producción + ONI
python3 construir_dataset_modelado.py --anio-min 2014 --incluir-oni   # ventana ampliada + ONI
python3 entrenar_clasificador.py --incluir-oni --anio-prueba 2019
python3 entrenar_clasificador.py --anio-min 2014 --incluir-oni --anio-prueba 2014
```
