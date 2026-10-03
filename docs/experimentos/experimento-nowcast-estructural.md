# Experimento: modelo estructural del tablero (2026-10-03)

> Protocolo escrito el 2026-10-03, en la rama `feat/mejora-tablero-estructural`, antes de escribir
> o correr ningún script. Continúa `analisis-forma-serie-tablero.md` y `experimento-nowcast-theta-ets.md`.
> No toca la prueba prospectiva congelada (`experimento-nowcast-tendencia.md`, script
> `40b6ebb78fe670222966a225438155b83ada876d`), las candidatas K1 a K4, la web, el backend ni los
> artefactos de `backend/api/datos/`.

## Pregunta

El plan de mejora tenía un punto 2C: si la serie del tablero es el promedio de k semanas de
conteos crudos, el cambio de una semana a la siguiente es

y(t+1) = y(t) + (x(t+1) − x(t+1−k)) / k,

donde x son los conteos crudos. El término x(t+1−k) es la semana que sale de la ventana y ya
ocurrió. Un modelo que lo conociera sabría, antes de que pase, cuánto va a bajar o subir la serie
por lo que sale. Ni T ni C usan esa información. ¿Se puede aplicar ese modelo con los datos que hay, y
qué parte de la ganancia posible está al alcance?

## Por qué no se puede probar tal cual

Tres requisitos, que el modelo estructural necesita y los datos no cumplen:

1. La forma del filtro conocida y continua. El análisis de forma de la serie (Fase 0) descartó el
   promedio móvil causal de 4 o más semanas como descripción de la serie continua 2025-S1 a
   2026-S37, y atribuyó el salto del cambio de año y tres saltos de 2026 a algo distinto de un
   promedio de 6 o 7 semanas. El filtro no es identificable con lo capturado.
2. Los conteos crudos x. Un promedio móvil de k semanas deja sin determinar cualquier secuencia de
   período k y suma cero: sumada a x, da la misma y. Los conteos que salen de la ventana solo se
   recuperan hasta esa ambigüedad, salvo que se conozcan k semanas crudas contiguas como ancla, y
   cada redondeo de y a entero arrastra error a la ancla.
3. Validación fuera del sesgo. La historia hasta 2023 que usa el predictor es el promedio exacto de
   7 semanas de OpenDengue crudo. Cualquier modelo estructural validado en esos años acierta por
   construcción, igual que ocurrió con la ganancia de ETS, que desapareció en el tablero.

La comprobación de enteros (si k · y es entero) tampoco identifica k: todos los valores de
2022 a 2026 de la base son enteros y la fracción es 1,0 para todo k de 2 a 12.

## Estado de la información

- Los datos son los de la base: OpenDengue hasta 2024-S52 y el tablero de 2025-S1 a 2026-S37, de
  las capturas del 2026-09-27. Quien escribe este protocolo ya vio las series de 2023, 2024, 2025 y
  2026 (valores y gráficos de la Fase 0). Las pruebas de abajo son por eso descriptivas y de
  compuerta, no confirmatorias.
- Ninguna semana objetivo de 2026-S38 en adelante está en la base ni se mira. No se carga ninguna
  captura. No se calcula ningún pronóstico en este documento.

## Etapas

Cada etapa tiene una regla de parada escrita antes de verla. Las etapas posteriores a una parada no
se corren.

### E0a. ¿OpenDengue 2024 continúa el crudo de 2023? (descriptiva, sin decisión)

Es la única ocasión en que hay un ancla real: los conteos crudos de OpenDengue 2023 junto a una serie
ya promediada, la de 2024. Para cada k de 2 a 12 se plantea el programa lineal de la Fase 0: existen
conteos x(s) no negativos para las k − 1 semanas previas a 2024-S1 y las 52 de 2024, tales que el
promedio causal de k semanas queda a no más de 0,5 de cada valor publicado de 2024.

Tres variantes del pasado (las k − 1 semanas de 2023 anteriores a 2024-S1):

- P: fijo a los valores crudos de OpenDengue 2023.
- P': fijo, salvo las semanas con valor 0, que quedan libres y no negativas. Los ceros del cierre de
  año son casos que las vacaciones dejaron sin notificar y que pasan a la semana siguiente.
- L: todo libre y no negativo.

Se reporta, por k y variante, si es factible y, si lo es, el ancho de identificación de la suma
de los conteos crudos de las k últimas semanas de 2024 (mínimo y máximo por programa lineal, relativos al
valor de 2024-S52). Si L es factible y P' no, el crudo de 2023 no es el insumo de la serie de 2024
(otra fuente o otro corte). No hay regla de parada: describe el insumo y no decide nada.

### E0b. Ancho de identificación en el régimen que importa (compuerta)

Se calcula, para el tablero, cuánta de la información de la semana que sale de la ventana queda
determinada por los datos, aun si el filtro fuese exactamente un promedio causal de k semanas.

Para cada año del tablero por separado (el pasado de k − 1 semanas libre y no negativo), cada k de 2
a 12 y cada origen t de la lista de abajo, con los datos del año hasta t:

- Factibilidad del programa lineal con tolerancia 0,5 (la de la Fase 0).
- Para h = 4, la suma S de los conteos crudos de las h semanas más antiguas de la ventana, es decir
  x(t−k+1) + … + x(t−k+h). Es la cantidad que el modelo estructural necesita saber. Su mínimo y
  su máximo se obtienen por programa lineal. El error de identificación del pronóstico a h = 4 es

  e_id = (máximo de S − mínimo de S) / (2 · k · y(t)).

- Orígenes: 2026-S20 a 2026-S37, para la compuerta. Los de 2025-S20 a 2025-S51, como contraste.

Magnitud contra la que se compara: m4, la mediana de |y(t+4) − y(t)| / y(t) sobre los pares dentro
del mismo año con dato en los dos extremos, en 2025 y 2026 (semanas ya vistas). Es cuánto se mueve la
serie en 4 semanas, que es lo que un pronosticador tiene que explicar.

Compuerta. Sea G el conjunto de k de 4 a 9 que son factibles con el año completo en 2025 y en 2026
(se mira solo la factibilidad; el criterio de plausibilidad de la Fase 0 no se repite). La
compuerta se supera si algún k de G cumple que la mediana de e_id sobre los orígenes 2026-S20 a
2026-S37 es menor o igual que 0,25 · m4.

Por qué esa regla: es una condición necesaria. Si ni la cota optimista de identificación (el
programa lineal da el rango máximo posible, sin ninguna otra suposición) cabe en una cuarta parte
del movimiento de la serie, el término que sale de la ventana no se puede usar. Superarla deja
abierta una prueba de pronóstico y no anticipa su resultado.

La probabilidad previa de superarla es baja, por la ambigüedad de período k de arriba. La
restricción de no negatividad puede apretar el rango cuando los conteos son pequeños, y por eso se
mide en vez de suponerse.

### E1. Prueba de pronóstico (condicional)

Solo si se supera la compuerta de E0b. Se escribe entonces un protocolo propio, firmado antes de
cualquier script, con una versión del modelo estructural que reconstruya los conteos de la ventana
con una regularización fija, la compare contra T y C con la regla de cambio del experimento de
tendencia (ganancia media de skill mayor o igual que 0,005 y al menos 3 de 5 años) y la confirme en
2024 y en 2025 a 2026-S37. Nada de eso se define ni se corre aquí.

## Qué habilita cada resultado

- Si E0b no supera la compuerta, el modelo estructural se descarta con los datos disponibles. Se
  reabre solo si llega información que identifique el filtro: capturas semanales que conserven todas
  las versiones del tablero, o la respuesta de MINSAL sobre cómo calcula la serie. Se cierra el
  punto 2C del plan con esa conclusión.
- Si la supera, se redacta el protocolo de E1. El sitio no cambia por este experimento en ningún caso.
- E0a no habilita nada por sí sola.

## Reproducibilidad

- Script `backend/ingestion/analisis_nowcast_estructural.py`, con pruebas en
  `backend/ingestion/tests/test_estructural.py`. Se escriben y se commitean antes de correr.
- Reutiliza `cargar` y la tolerancia de `analisis_nowcast_forma_serie.py`. Lee Postgres, solo hasta
  2026-S37; no consulta el sitio de MINSAL.
- Salida: `docs/agentes/mejora-predictor/resultados-nuevos/estructural_identificacion.json`.
- Se corre una sola vez con estos criterios. Los resultados y las conclusiones se agregan al final de
  este documento.
