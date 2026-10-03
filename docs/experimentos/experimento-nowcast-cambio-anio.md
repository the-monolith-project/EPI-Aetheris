# Experimento: el cambio de año en la predicción del tablero (2026-10-03)

> Protocolo fijado el 2026-10-03, antes de escribir el script, en la rama
> `feat/mejora-tablero-cambio-anio` (sale de `feat/mejora-tablero-ch`). Línea de calendario del
> plan de mejora de la predicción para la serie del tablero de MINSAL. No toca la web, el
> backend, los artefactos de `backend/api/datos/` ni el script congelado de la prueba prospectiva.

## Pregunta

Los 40 fallos del rango del 95 % de C en 2026 se reparten así: 19 en las semanas objetivo 1 a 4
(el salto de 39 a 214 casos al cambiar de año, con el origen antes del salto) y 18 en las
semanas 19 a 23 (una caída de 98 a 56 que se mantiene cinco semanas y no coincide con
vacaciones), más 3 sueltos. Solo el primer grupo es de calendario.

1. ¿El cambio de año tiene una regularidad en la historia que un modelo pueda aprender, o el salto
   de 2026 queda fuera de lo visto?
2. En los años que no sirvieron para diagnosticar el problema (2019, 2021 a 2024), ¿fallan C, M0 o
   T más en las semanas del cambio de año o de vacaciones que en el resto?
3. Si fallan, ¿una regla de calendario definida de antemano corrige la cobertura sin encarecer el
   resto del año?

## Exploración previa, declarada

Antes de fijar este protocolo se miró:

- El análisis de cobertura de 2026 (`analisis-cobertura-2026.md`): fallos por semana objetivo y
  por lado. Las semanas 1 a 4 suman 19 fallos, todos por arriba; las semanas 19 a 23 suman 18,
  todos por abajo.
- La serie mixta (OpenDengue hasta 2024, tablero desde 2025) en las semanas 47 a 50 y 1 a 5 de
  cada cambio de año. Cociente entre la media de las semanas 1 a 3 y la media de las semanas 47 a
  50 del año anterior, en conteos crudos:

| cambio | media 47 a 50 | media 1 a 3 | cociente | semana 1 sobre media 47 a 50 |
|---|---|---|---|---|
| 2014 a 2015 | 304,2 | 336,7 | 1,11 | 0,49 |
| 2015 a 2016 | 834,2 | 380,7 | 0,46 | 0,46 |
| 2016 a 2017 | 68,8 | 62,3 | 0,91 | 0,65 |
| 2017 a 2018 | 63,5 | 54,3 | 0,86 | 1,65 |
| 2018 a 2019 | 152,2 | 121,7 | 0,80 | 0,63 |
| 2019 a 2020 | 251,0 | 146,0 | 0,58 | 0,46 |
| 2020 a 2021 | 50,5 | 40,3 | 0,80 | 0,71 |
| 2021 a 2022 | 137,8 | 161,7 | 1,17 | 1,10 |
| 2022 a 2023 | 64,5 | 69,7 | 1,08 | 0,95 |
| 2023 a 2024 | 117,5 | 87,0 | 0,74 | 0,64 |
| 2024 a 2025 | 116,0 | 80,7 | 0,70 | 0,65 |
| 2025 a 2026 | 59,0 | 176,7 | 2,99 | 3,63 |

- Los experimentos previos sobre vacaciones: la marca de calendario como variable de M0 (M1, no
  pasa), los ceros de vacaciones repartidos como insumo de M0 (I5, no pasa) y la comparación sin
  puntuar las 17 semanas afectadas por ceros (ningún veredicto cambia).

Lo que se ve antes de correr nada: de 2014 a 2025 el cociente va de 0,46 a 1,17 y el de la
semana 1 llega a 1,65 como máximo; 2026 está en 2,99 y 3,63. Lo que se repite en la historia es
una baja al empezar el año, que M0 ve por las variables de semana del año. Con eso, lo esperable
es que no haya una regla de calendario que aprender del cambio de año. El protocolo existe para
comprobarlo con un criterio fijado de antemano y para dejar lista una regla si la historia dice
otra cosa.

## Datos

- Serie mixta de `cargar_serie_mixta` (OpenDengue hasta 2024, tablero desde 2025; la semana 53 de
  2025 sigue sin dato). El año 2026 tiene 52 semanas en el calendario de la base, así que el
  hueco no se repite en el cambio a 2027.
- Parte A: la serie cruda y la historia de T (promedio causal de 7 semanas hasta 2023, el tablero
  tal cual).
- Partes B y C: las predicciones de M0 guardadas en `rangos.json` (fase A: objetivos de 2019,
  2021, 2022 y 2023 contra la historia suavizada; fase B: 2024 como H1 y 2025 a 2026-S37 como
  H2), con T y C reconstruidos con `Reglas`, igual que en el experimento del peso por horizonte
  (`datos_validacion` y `cargar_b`). Se excluye 2020 como en todos los experimentos anteriores.
- La "historia" de las partes B y C es 2019, 2021, 2022, 2023 y 2024. H2 queda fuera de B porque
  contiene el problema; solo se reporta en C, rotulado dentro de muestra.
- Ningún dato desde 2026-S38.

## Tramos de semanas objetivo, fijados antes de medir

- FA, cambio de año: la semana epidemiológica de la semana objetivo es 1, 2 o 3. Es el tramo que
  señalaron el ADR 0020 y el análisis de cobertura.
- V, vacaciones: la semana objetivo tiene la marca de `marca_vacaciones` del experimento de
  mejora (Semana Santa, fiestas agostinas, 20 de diciembre a 2 de enero).
- R, resto: ni FA ni V.

Un par origen-horizonte pertenece a los tramos de su semana objetivo. FA y V pueden coincidir en
una semana; R los excluye a ambos. No se añaden tramos después de ver resultados.

## Parte A. ¿Es el salto una regularidad de calendario?

Descriptiva, sin predictor. Para cada cambio de año de 2015 a 2026 se calcula

D = log1p(media de las semanas 1 a 3 del año) menos log1p(media de las semanas 47 a 50 del año
anterior),

en la serie cruda y en la historia de T. La referencia nula son las ventanas de la misma forma
(cuatro semanas, un hueco de dos, tres semanas) contenidas en las semanas 4 a 46 de un mismo año
de 2015 a 2025, es decir, sin cruzar fin de año ni vacaciones de diciembre. Se reporta, por
cambio de año, D y su percentil en la referencia nula, el número de cambios con cada signo y la
mediana de los percentiles.

2026 queda fuera de lo visto si su D supera al máximo de los 11 cambios anteriores y su
percentil en la referencia nula es mayor que 0,99. Esta parte no decide ninguna corrección:
informa si el salto de 2026 se parece a algo de la historia.

## Parte B. Cobertura por tramo en la historia

Para C (peso 0,5), M0 y T, en cada tramo y por grupo de horizontes (h = 1 a 2, 3 a 4, 5 a 8), con
los pares de la historia (2019, 2021 a 2024) agrupados: n de pares y de semanas objetivo,
cobertura del 95 % y del 50 %, fallos por arriba y por abajo, y el cociente entre el error
absoluto medio de la mediana (en `log1p`) del tramo y el de R. Para decidir se usa C con todos
los horizontes juntos.

Hay una deficiencia que justifica una regla en el tramo FA o V si, para C, se cumplen las tres:

- B1: cobertura del 95 % menor o igual que 0,85, el mínimo que exige la prueba prospectiva.
- B2: prueba de permutación a una cola, con p menor o igual que 0,10 tras ajustar por Holm entre
  FA y V. En cada año se sortean, entre sus semanas objetivo, tantas semanas como tiene el tramo
  (2000 permutaciones, semilla 20261003) y se calcula la cobertura agrupada; p es la fracción de
  sorteos con cobertura menor o igual que la observada.
- B3: al menos 75 % de los fallos del tramo salen del mismo lado.

Potencia: FA tiene unas 15 semanas objetivo en la historia (tres por año, cinco años) y V unas
treinta. La prueba solo detecta deficiencias grandes. Un resultado negativo significa que no hay
evidencia en la historia, no que el efecto no exista.

## Parte C. Regla de ensanchamiento por calendario (condicionada)

Solo se corre para un tramo que cumpla B1, B2 y B3. Si ninguno los cumple, C no se corre y la
conclusión es que la historia no respalda una regla de calendario.

Candidata: en los pares cuya semana objetivo está en el tramo, los cuantiles del lado donde se
concentran los fallos se alejan de la mediana en escala `log1p`, q' = mediana + f · (q menos
mediana), con f en {1,25; 1,5; 2}. La mediana y el otro lado no cambian. Se elige el menor f con
el que la cobertura del 95 % agrupada del tramo en 2019, 2021, 2022 y 2023 llega a 0,93 o más;
si ninguno llega, no hay candidata.

Condiciones para pasar a la Fase 4:

- (a) existe f según la regla anterior;
- (b) el WIS medio de todos los pares de esa validación (no solo del tramo) no sube más de 0,5 %
  respecto a C;
- (c) en 2024 (H1) la cobertura del 95 % del tramo no baja respecto a C y su WIS no sube más de
  5 %.

H2 (2025 a 2026-S37) se reporta, rotulado dentro de muestra, sin criterio: contiene el episodio
que originó la pregunta y no puede confirmarlo.

## Controles y pruebas

- `q_T` y `q_C_R0` guardados se reproducen con `Reglas` (los controles del experimento del peso
  por horizonte).
- Pruebas unitarias sin base de datos: asignación de tramos (semanas 1 a 3, marca de vacaciones,
  solapamiento y resto), estadístico D sobre una serie sintética con cociente conocido, percentil
  en la referencia nula, permutación (con todos los pares cubiertos la cobertura permutada es
  1 y p es 1), ensanchamiento (con f = 1 devuelve C; no toca la mediana ni el otro lado; conserva
  el orden de los cuantiles).

## Qué se decide y qué no

- Se decide si la historia respalda un problema de calendario y, solo entonces, si hay una regla
  de ensanchamiento candidata para firmarla en la Fase 4 como predicción paralela.
- No se cambia nada de la web ni del backend, y el salto de 2026 no se usa para elegir ningún
  parámetro.
- La caída de las semanas 19 a 23 no se trata aquí: no hay calendario que la explique. Queda como
  limitación de cobertura, igual que el límite alto.
- Documentar en la Biblioteca que el rango puede quedar corto al cambiar de año es una decisión
  aparte.

## Salidas

- Script `backend/ingestion/experimento_nowcast_cambio_anio.py` (`--control`, `--parte-a`,
  `--parte-b`, `--parte-c`), commiteado con sus pruebas antes de correrlo.
- Pruebas `backend/ingestion/tests/test_cambio_anio.py`.
- Resultados en `docs/agentes/mejora-predictor/resultados-nuevos/cambio_anio.json`.
