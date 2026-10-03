# Análisis: qué filtro produce la forma de la serie del tablero (2026-10-03)

> Plan fijado el 2026-10-03, antes de correr el script, en la rama `feat/mejora-tablero-fase0`
> (sale de `feat/mejora-predictor-agente`). Es la Fase 0 del plan de mejora del predictor para
> la serie del tablero. Es un análisis descriptivo: no elige ni compara modelos, no cambia el
> predictor y no usa semanas objetivo desde 2026-S38.

## Pregunta

La serie semanal de casos sospechosos del tablero de MINSAL es mucho más lisa que un conteo
crudo (ADR 0021). El ADR 0021 la describe como un promedio hacia atrás de 6 o 7 semanas, y
dice que el núcleo exacto no se puede recuperar. Antes de suavizar la historia anterior a 2025
"como lo hace MINSAL", ¿se puede decir algo más preciso sobre ese filtro con lo que ya está
capturado?

## Exploración previa, declarada

Antes de fijar este plan se miró lo siguiente, y por eso el plan no es ciego:

- La serie de sospechosos de 2025 y 2026, que ya estaba a la vista en el ADR 0021.
- Una recursión sencilla que reconstruye los conteos crudos bajo un promedio móvil con
  ventana expansiva al inicio del año (x_t = x_(t-k) + k·(y_t − y_(t−1))). Con k de 3 a 10 dio
  conteos negativos en 2026 (entre 3 y 5 semanas con valor negativo, hasta −345) y entre 1 y 7
  en 2025. Era una exploración sin tolerancia de redondeo; este análisis la repite bien hecha.
- Un ajuste de los umbrales del corredor endémico del tablero (seguridad, alerta, epidemia) a
  cuartiles de OpenDengue crudo y suavizado: no reprodujo los umbrales (error logarítmico medio
  mínimo de 0,155 en 2025). Se repite con el espacio de búsqueda fijado abajo.

Los criterios de abajo se fijaron después de esa mirada pero antes de calcular nada con el
script. No se añaden pruebas después de ver los resultados.

## Datos

- Serie de sospechosos del tablero: `casos_epidemiologicos` con la fuente `minsal_tablero`,
  `clasificacion = 'sospechoso'`, 2025-S1 a 2026-S37 (89 semanas; 2025-S53 no está publicada).
  El script la lee de Postgres y, si no hay base, de `db/seed/seed_tablero_minsal.sql`.
- OpenDengue nacional, 2014 a 2024, `casos_epidemiologicos` con la fuente `opendengue_v1_3`.
- Umbrales del corredor endémico de 2025 y 2026, extraídos de las capturas HAR del tablero
  (`tablero-10` y `tablero-04`), guardados en el JSON de resultados para que el análisis se
  pueda repetir sin las capturas.

No se consulta el sitio de MINSAL. Las capturas son las que ya cargó una persona
(ADR 0021).

## A. ¿Puede ser un promedio móvil causal de k semanas?

Para k de 2 a 12 y para tres variantes del inicio de la serie:

- W1: ventana expansiva al comienzo de cada año (el promedio usa solo las semanas disponibles
  del propio año).
- W2: ventana completa con semanas previas desconocidas, libres y no negativas (cada año por
  separado).
- W3: la serie 2025-S1 a 2026-S37 como una sola, con 2025-S53 como semana desconocida y sin
  valor publicado.

Se plantea como factibilidad: ¿existen conteos crudos x ≥ 0 tales que el promedio de cada
ventana difiere de lo publicado en a lo sumo 0,5 (el redondeo a entero)? Entre las soluciones
factibles se minimiza el máximo semanal.

- Rechazado para ese k y esa variante si no hay solución factible.
- Plausible solo si el máximo semanal de la solución no supera R_k veces el máximo de la serie
  publicada, donde R_k es el mayor cociente entre el máximo semanal crudo y el máximo del
  promedio móvil causal de k semanas que se ve en un año de OpenDengue crudo de 2014 a 2023. Es
  decir, una solución que exige una semana más extrema que cualquier año real no cuenta como
  plausible.

## B. ¿Puede ser un promedio exponencial?

y_t = α·x_t + (1 − α)·y_(t−1), con α de 0,05 a 0,95 en pasos de 0,05 y la misma tolerancia de
0,5. Factible si todos los x_t despejados pueden ser no negativos dentro de la tolerancia.
Plausible con el mismo criterio de R_α, calculado con OpenDengue crudo.

## C. Perfil de saltos

Para cada serie, el valor absoluto del cambio semanal en escala logarítmica,
|log(y_t / y_(t−1))|, con la proporción de semanas por encima de 0,15 y de 0,30, y el máximo:

- tablero 2025, tablero 2026, y 2026 sin S1 a S4;
- OpenDengue 2024;
- OpenDengue crudo de 2014 a 2023, y filtrado con el promedio móvil causal de k de 3 a 8.

La pregunta es si saltos como los de 2026 (S1 a S3, S13, S19, S26) aparecen alguna vez en
OpenDengue filtrado. Si el tablero tiene más semanas con cambio mayor que 0,30 que cualquier
año filtrado de OpenDengue (por cada 36 semanas), se concluye que esos saltos no vienen del
suavizado de conteos crudos.

## D. Umbrales del corredor

Para los umbrales de 2025 y 2026 (seguridad, alerta, epidemia) se buscan, sobre OpenDengue,
los cuartiles semanales que mejor los reproducen, variando:

- la transformación: crudo, o promedio móvil causal o centrado de k de 2 a 10;
- los años: inicio entre 2014 y 2022, fin entre 2022 y 2024 (2023 y 2024 para los umbrales
  de 2026), con y sin 2020;
- el estadístico: cuartiles 25, 50 y 75.

Métrica: error logarítmico absoluto medio entre el umbral y el cuartil, sobre las 52 semanas.
Se considera una reproducción solo si el error es menor que 0,03. Si ninguna combinación llega
ahí, el resultado es inconcluso, no una refutación, porque el método de MINSAL puede ser otro.

## Qué habilita cada resultado

- Si hay un filtro (A o B) plausible para algún k o α, se reporta cuál y se usa para suavizar
  la historia en la Fase 1, junto con la sensibilidad a sus vecinos.
- Si ningún promedio móvil ni exponencial es plausible, el filtro exacto no es identificable
  con lo publicado. El suavizado de la historia pasa a ser una aproximación declarada como
  tal, con k = 6 y k = 7 como en el ADR 0021 y su sensibilidad, y la pregunta a MINSAL sobre
  cómo se calcula la serie queda como la vía segura.
- Si C muestra que los saltos de 2026 no aparecen en OpenDengue filtrado, la predicción debe
  tratarlos como un componente aparte (por ejemplo, riesgo de salto en el cambio de año), no
  como ruido que el suavizado explica.

## Reproducibilidad

```
cd backend/ingestion
python analisis_nowcast_forma_serie.py
```

Escribe `docs/agentes/mejora-predictor/resultados-nuevos/forma_serie_tablero.json`. Usa solo
datos hasta 2026-S37. No toca el script congelado de la prueba prospectiva, la API, el
frontend ni los artefactos de `backend/api/datos/`.
