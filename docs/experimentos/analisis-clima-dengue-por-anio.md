# Análisis exploratorio: clima y dengue año por año (2026-10-03)

> Protocolo escrito el 2026-10-03, en la rama `feat/clima-dengue-por-anio`, antes de escribir o
> correr ningún script. Continúa `experimento-nowcast-insumos.md` (ablación del clima). No toca la
> prueba prospectiva congelada (`experimento-nowcast-tendencia.md`, script
> `40b6ebb78fe670222966a225438155b83ada876d`), las candidatas K1 a K4, el predictor, el backend ni los
> artefactos de `backend/api/datos/`. Ninguna decisión de modelado depende de este análisis.

## Pregunta

La ablación del clima encontró que quitar el clima de M0 ayuda en unos años y perjudica en otros, sin
un efecto sostenido. Eduardo pidió convertir eso en algo que se pueda ver en el sitio: cómo se
relaciona el clima con el dengue en esta serie, año por año, y qué parte de esa relación es solo el
ciclo estacional compartido. Este análisis produce los números de ese material. La base solo tiene
El Salvador, de modo que el análisis describe esa serie y no puede dar causas ni comparar con otros
países.

## Estado de la información

- Quien escribe este protocolo ya vio, del experimento de insumos, el skill por año de las variantes
  I0 a I5 (cifras del `insumos.json`). Por eso A1 es una lectura de resultados ya conocidos, no una
  prueba.
- No ha visto ninguna correlación entre clima y casos, por año ni agrupada, ni el perfil anual de A4.
  A2 a A5 son cálculos nuevos.
- No se mira ninguna semana objetivo de 2026-S38 en adelante. No se carga ninguna captura.

## Datos

- Casos: OpenDengue nacional, clasificación `total` (sospechosos), semanal. Años de análisis: 2014 a
  2019 y 2021 a 2023 (9 años). 2020 se excluye por la pandemia, como en el resto de los experimentos.
  2024 se excluye de A2 a A5: su serie es ya un promedio de varias semanas hecho en origen (ver
  `analisis-forma-serie-tablero.md`) y desplaza el momento de los máximos, lo que contamina cualquier
  correlación con rezagos. Lo mismo vale para el tablero de 2025 y 2026.
- Las semanas con valor 0 en las vacaciones son casos no notificados que pasan a la semana siguiente.
  Se tratan como faltantes. El promedio de 4 semanas de abajo se calcula con las semanas con dato.
- Clima: las siete variables de `variables_ambientales` (`temp_media`, `temp_max`, `temp_min`,
  `precipitation_sum`, `precipitation_hours`, `humedad_relativa_media`, `punto_rocio`) como media simple
  de los 14 departamentos, y `oni_anom`, igual que `cargar_serie` del experimento de insumos. Es un
  reanálisis (Open-Meteo), no estaciones.

## Definiciones

- z(t): log1p del promedio de las 4 semanas que terminan en t (las que tienen dato). NaN si no hay
  ninguna.
- g(t) = z(t + 4) − z(t): crecimiento a 4 semanas. Se usa el origen t y el horizonte 4 porque son los de
  los rasgos de M0 (medias de 4 semanas) y los de la ablación.
- Semana del año: 1 a 52; la 53 se pliega a la 52.
- Climatología de una serie en un año Y: media de la misma semana del año en los otros 8 años de
  análisis, suavizada con una media móvil circular centrada de 5 semanas. No usa el año Y.
- Anomalía: valor menos la climatología del mismo año. Para el clima, la media de las 4 semanas que
  terminan en t (t − 3 a t, pudiendo caer en el año anterior) menos su climatología. Para g, g(t) menos
  la climatología de g. El ONI ya es una anomalía: se usa su valor en t, sin climatología.
- Un par (t, g) entra si t y t + 4 están en el año Y y ambos extremos tienen dato.

## Análisis (lista cerrada)

### A1. Aporte del clima al pronóstico por año (lectura, sin recalcular)

Del `insumos.json`, fase de validación, referencia persistencia limpia: el aporte del clima es
skill(I0) − skill(I2) y el del ONI es skill(I0) − skill(I1), por año de 2019, 2021, 2022, 2023 y 2024,
en h = 4 y h = 8. Positivo significa que el rasgo ayuda. Se reportan también los otros horizontes, y
las variantes I3 e I4 como contexto.

### A2. Cuánto del ciclo es estacional (descriptiva)

Para cada variable climática y para z: fracción de la varianza semanal explicada por 3 armónicos
anuales (R² de una regresión con intercepto, sen y cos de 1, 2 y 3 ciclos por año), sobre los 9 años.
Para cada variable, correlación entre su climatología (52 valores, sobre los 9 años) y la climatología
de z desplazada 0 a 16 semanas hacia adelante; se reporta el desplazamiento con la mayor correlación y
su valor.

### A3. Asociación entre la anomalía climática y el crecimiento, por año

Para cada año Y, cada una de las 8 variables (7 climáticas y ONI): correlación de Pearson entre la
anomalía climática en t y la anomalía de g(t). Intervalo del 95 % por bootstrap de bloques móviles
(longitud 8 semanas, 2000 remuestreos, semilla 20261003) sobre los pares del año. Son 72 estimaciones
y se reportan todas. No se usa ningún valor p ni se elige una variable por su resultado.

Agrupado: la misma correlación sobre los pares de los 9 años juntos, con el bootstrap de bloques hecho
dentro de cada año (cada año conserva su número de pares). Es un resumen, no un contraste.

### A4. Perfil de cada año (descriptiva)

Por año: casos totales, semana y valor del máximo de z, media anual de cada variable climática y su
anomalía respecto de la climatología de los otros 8 años, ONI medio. Además, correlación de rangos de
Spearman entre los casos totales del año y cada anomalía media anual, con n = 9. Con n = 9 la
correlación es un dato descriptivo; no se reporta su significación y el texto no la usa como prueba.

### A5. Consistencia entre años

Derivada de A3, sin cálculo nuevo. Para cada variable: años con r > 0, años con r < 0, años cuyo
intervalo excluye 0 y el rango de r. Una variable se llama consistente si tiene el mismo signo en al
menos 8 de los 9 años y el intervalo agrupado excluye 0. Cualquier otra se llama variable según el año.
La regla queda fijada aquí para que la etiqueta no dependa de lo que se vea.

## Qué se puede decir con cada resultado

- Si ninguna variable es consistente, el material dice que en esta serie la asociación del clima con
  el crecimiento a 4 semanas cambia de signo o de tamaño entre años, y muestra los 9 años. No da una
  causa.
- Si alguna variable es consistente, el material la nombra, con su tamaño y su intervalo, y dice que es
  una asociación lineal de esta serie que el modelo no convirtió en una ganancia sostenida (A1).
- A2 se presenta como contexto: qué parte del clima y de los casos es estación. Una variable casi toda
  estacional repite lo que ya aportan los armónicos del modelo.
- Ninguna frase del material afirma por qué El Salvador difiere de otros lugares, ni que difiera. Las
  explicaciones posibles (serotipos, inmunidad poblacional, control vectorial, notificación) no se
  observan en la base y se nombran, si se nombran, como no medidas.
- Cada panel del material usa solo cifras del archivo de salida de este análisis y de `insumos.json`.

## Límites

- Nueve años y un solo país. Los intervalos de A3 suponen que los bloques de 8 semanas capturan la
  dependencia temporal; con 45 pares por año es una aproximación.
- La correlación es lineal y mide una variable a la vez. No detecta interacciones, umbrales ni rezagos
  distintos de la ventana de 4 semanas.
- El clima es la media de 14 departamentos de un reanálisis; los casos son el total nacional de
  sospechosos con demoras de notificación y artefactos de vacaciones.
- El resultado depende de que se haya excluido 2020 y 2024 en adelante; no se prueba otra exclusión.

## Reproducibilidad

- Script `backend/ingestion/analisis_clima_por_anio.py`, con pruebas en
  `backend/ingestion/tests/test_clima_por_anio.py`, que se escriben y se confirman en un commit
  anterior a la primera corrida. Lee Postgres; no consulta ningún sitio externo.
- Salida: `docs/agentes/mejora-predictor/resultados-nuevos/clima_por_anio.json`. Los resultados y su
  lectura se añaden a este documento en una sección posterior, sin modificar lo de arriba; un cambio
  al protocolo después de ver resultados se anota como enmienda con fecha y motivo.
