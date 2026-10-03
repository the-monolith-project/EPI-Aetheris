# Análisis exploratorio: El Salvador frente a 18 países de las Américas (2026-10-03)

> Protocolo escrito el 2026-10-03, en la rama `feat/clima-dengue-por-anio`, antes de escribir o
> correr ningún script. Continúa `analisis-clima-dengue-por-anio.md` y el experimento multipaís del
> clasificador (`experimento-multipais.md`, hoy en el repo STC; última versión aquí en `ef698c8^`).
> No toca la prueba prospectiva congelada, las candidatas K1 a K4, el predictor, el backend ni los
> artefactos de `backend/api/datos/`. Ninguna decisión de modelado depende de este análisis.

## Pregunta

El experimento multipaís midió que la anomalía anual de casos de El Salvador correlaciona +0,280 con
la señal regional de 18 países, la más baja de todos. Esa cifra existe en un documento histórico y no
se ha reproducido ni ampliado. Este análisis la reproduce con los datos de entonces y la acompaña con
lo que permiten los mismos datos: el perfil de cada país, la incertidumbre de la medida, su
estabilidad, la asociación semanal entre el clima y el crecimiento de los casos medida igual que en
El Salvador, y el ciclo medio de casos y clima. El objetivo es dejar registradas las cifras con las
que cualquier lector pueda ubicar a El Salvador frente a los otros países. No se busca explicar por qué
difiere.

## Estado de la información

- Quien escribe este protocolo ya vio, de este conjunto de datos, las cifras reproducidas en un ensayo
  previo a este protocolo: con la definición de P2 salen 0,453 de correlación media entre países,
  51,8 % del primer componente, +0,280 para El Salvador (el menor de 18), 0,952 Colombia, 0,908
  Guatemala y 0,868 Honduras, iguales a las del documento histórico. Se probaron cuatro definiciones de
  anomalía (log1p del total anual estandarizado, total crudo, razón a la media y rangos); solo la
  primera reproduce las cifras y es la que se fija. La señal regional es la media de las anomalías de
  los 18 países, El Salvador incluido.
- No ha visto ninguna otra cifra de P1, P3, P4 ni de los intervalos y sensibilidades de P2.
- El análisis del clima de El Salvador por año (`analisis-clima-dengue-por-anio.md`) ya está hecho y es
  una entrada de este: sus valores para El Salvador son el contraste de P3.

## Datos

- Casos: `Temporal_extract_PAHO_V1_3.csv` del repositorio de OpenDengue
  (`https://github.com/OpenDengue/master-repo`, `assets/Temporal_extract_PAHO_V1_3.zip`), filas
  `S_res = Admin0` y `T_res = Week`, años 2014 a 2024, columna `dengue_total`. No se versiona. La
  salida guarda su SHA-256. Los 18 países son los que tienen al menos 45 semanas en cada uno de los 11
  años. Hay 16 con clima de superficie completo.
- Clima: Open-Meteo, un punto por país (`CENTROIDES` de `experimento_multipais.py`), diario de 2013 a
  2024, modelos `era5_land` (temperatura, humedad y punto de rocío) y `era5` (lluvia y horas de lluvia),
  del caché de ese experimento. No se versiona. La salida guarda su SHA-256. Bermuda e Islas Vírgenes
  (EE. UU.) devuelven nulo en las 5 variables de superficie y solo tienen las 2 de lluvia.
- ONI: `oni_anom` semanal de la base (la misma serie para todos los países).
- Años de análisis semanal: 2014 a 2019 y 2021 a 2023, los mismos 9 de El Salvador. Los totales anuales
  de P2 usan los 11 años (replicación) y los 9 (sensibilidad).

## Construcción semanal

Las funciones son las de `analisis_clima_por_anio.py` (importadas, no reescritas). Para cada país:

- Rejilla de semanas por fecha de inicio (`calendar_start_date`); las semanas ausentes quedan como
  faltantes. El año de una semana es el de su columna `Year`. La semana del año es
  `min((día del año − 1) // 7 + 1, 52)` a partir de la fecha de inicio, que difiere a lo sumo en una
  semana de la numeración epidemiológica de cada país.
- z: log1p del promedio de las 4 semanas que terminan en t, incluyendo las semanas con cero. A
  diferencia del análisis de El Salvador, los ceros no se tratan como faltantes porque en los países de
  baja incidencia son ceros reales. El Salvador se recalcula así para que la comparación sea de la
  misma construcción.
- Clima semanal: suma de 7 días para `precipitation_sum` y `precipitation_hours`, media para las demás,
  con al menos 5 días con dato; si no, faltante.
- Anomalías, climatología sin el año evaluado, g y pares: como en El Salvador (horizonte 4, ventana
  de 4 semanas, suavizado de 5 semanas, bloque de 8, 2000 remuestreos, semilla 20261003 más el índice
  del país y el año).
- ONI: el valor de la semana epidemiológica de El Salvador que contiene la fecha de inicio.

## Análisis (lista cerrada)

### P1. Perfil de cada país (descriptiva)

Por país: punto de clima, semanas por año, total anual 2014 a 2024, casos semanales medios y fracción
de semanas con cero (años de análisis), R² de 3 armónicos de z, semana del máximo del ciclo medio de
z, desviación estándar entre años del log1p del total anual, y cociente entre el total del año mayor
y la mediana de los totales.

### P2. Señal regional (replicación y ampliación)

- Anomalía anual: log1p del total anual, estandarizado dentro de cada país con los 11 años. Señal
  regional: media de las anomalías de los 18 países.
- Por país: correlación con la señal regional (incluye al propio país), con la señal de los otros 17
  países, y la matriz de correlaciones de a pares. Correlación media entre pares, parte de la varianza
  del primer componente y correlación de la señal con el ONI anual (media de las semanas de cada año).
- Intervalo del 95 % de la correlación de cada país con la señal: bootstrap sobre los años (2000
  remuestreos con reposición de los pares anomalía y señal de cada año).
- Estabilidad de El Salvador: su correlación al quitar cada año de los 11, y al quitar cada otro país de
  la señal; mínimo y máximo.
- Subconjunto centroamericano: Guatemala, Honduras, Nicaragua, Costa Rica, Panamá y El Salvador. Para
  cada uno, correlación con la media de los otros cinco.
- Sensibilidad: las mismas correlaciones con los 9 años de análisis.
- Verificación: el script se detiene si no reproduce, con diferencia menor que 0,0015, la correlación
  media entre pares (0,453), la parte del primer componente (0,518), y las correlaciones de El Salvador
  (0,280), Colombia (0,952), Guatemala (0,908) y Honduras (0,868); y si El Salvador no es el menor de
  los 18. La correlación con el ONI se verifica contra 0,517 con tolerancia de 0,015.

### P3. Asociación entre la anomalía climática y el crecimiento, por país

Cada país con las variables que tenga: las 7 climáticas (2 en las dos islas sin clima de superficie) y
el ONI. Misma estadística que A3: correlación de Pearson entre la anomalía climática en t y la
anomalía del crecimiento a 4 semanas, por año y agrupada, con intervalo del 95 % por bootstrap de
bloques. Un año de un país es evaluable si su total anual es al menos 100 casos y tiene al menos 30
pares completos. Un país tiene estimación agrupada si tiene al menos 5 años evaluables.

Etiqueta de consistencia: un país y una variable son consistentes si el signo de r es el mismo en
todos los años evaluables salvo a lo sumo uno y el intervalo agrupado excluye el cero; si no, variable
según el año. Sin estimación agrupada, no evaluable. Se reportan todos los países y todas las
variables, sin elegir.

### P4. Ciclo medio por país

Por país y variable climática: R² de 3 armónicos de la variable, y desfase de 0 a 16 semanas con la
mayor correlación entre la climatología de la variable y la de z desplazada hacia adelante, con esa
correlación y una marca si el máximo está en el borde (16). Se guardan las 52 semanas de la climatología
de z y de cada variable para dibujar.

### P5. Corridas anteriores del clasificador (lectura, sin recalcular)

De los resultados guardados de las corridas A (solo El Salvador, entrenando con los otros países), B
(regional) y C (regional con ONI): por corrida y año, soporte real de la clase alto, F1 y recall de alto
del modelo y de la climatología (medias sobre las semillas), semillas en que el modelo supera a la
climatología y semillas totales. Se citan con su procedencia (experimento del 2026-08-16, script
`experimento_multipais.py`).

### P6. Posición de El Salvador (derivada, sin cálculo nuevo)

Posición de El Salvador entre los países evaluables en: correlación con la señal regional, correlación
con los otros 17, desviación entre años, R² estacional, y correlación agrupada de la lluvia en mm y del
ONI con el crecimiento. Se reporta la posición y el número de países, de menor a mayor.

## Qué se puede decir con cada resultado

- El sitio puede afirmar que El Salvador tiene la menor correlación con la señal regional de los 18
  países solo si lo es en la medida principal y en la sensibilidad de 9 años. Si no, reporta la
  posición en cada una. En ambos casos muestra el intervalo.
- Las posiciones de P6 y las asociaciones de P3 se presentan como descripción de estos datos. Ninguna
  frase afirma una causa de las diferencias entre países. Las explicaciones posibles (serotipos,
  inmunidad, control vectorial, definición de caso, notificación, demografía) no se observan y se
  nombran, si se nombran, como no medidas.
- Los países de baja incidencia, o de gran extensión donde un punto no representa el clima (Brasil,
  México, Estados Unidos, Colombia, Bolivia), se marcan en la salida.

## Límites

- Un punto de clima por país. Para países grandes no representa el territorio.
- Las series de la OPS no tienen la misma definición de caso en todos los países; el campo
  `case_definition_standardised` de la fuente es `Total`, sin más detalle.
- Once años anuales: las correlaciones con la señal tienen intervalos amplios.
- Los años 2020 y 2024 se mantienen en los totales anuales de P2 (replicación) y quedan fuera del
  análisis semanal. La serie de El Salvador de 2024 es un promedio de varias semanas hecho en origen.
- La semana del año se calcula por fecha y puede diferir en una de la de cada país.
- P5 no se recalcula: las corridas anteriores no se vuelven a ejecutar.

## Reproducibilidad

- Script `backend/ingestion/analisis_clima_multipais.py`, con pruebas en
  `backend/ingestion/tests/test_clima_multipais.py`, que se escriben y se confirman en un commit
  anterior a la primera corrida. Lee Postgres (solo el ONI) y los dos archivos locales; no consulta ningún
  sitio externo.
- Salida: `docs/agentes/mejora-predictor/resultados-nuevos/clima_multipais.json`. Los resultados y
  su lectura se añaden a este documento en una sección posterior; un cambio al protocolo después de ver
  resultados se anota como enmienda con fecha y motivo.
