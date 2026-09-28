# 0021 - Tablero de vigilancia de MINSAL como fuente, a partir de capturas HAR

**Estado:** Aceptado (enmendado 2026-09-27)

## Contexto

MINSAL dejó de publicar boletines en PDF después de 2023. Los datos de 2024 en adelante están en un tablero Superset público (`boletin.salud.gob.sv`) que bloquea las peticiones automáticas. `backend/ingestion/minsal/common.py` prohíbe que scripts y agentes hagan peticiones a ese sitio.

Al abrir el tablero, el navegador descarga una respuesta JSON por gráfico (`POST /api/v1/chart/data`). Cada respuesta trae la consulta SQL, con el año escrito (`da.anio=2025`), y una fila por semana (`semana_mes` = "NN-Mes"). Una persona puede guardar todas esas respuestas en un archivo HAR desde las herramientas de desarrollo. Es el uso normal del sitio.

Las primeras capturas (2026-09-27) cubren 2025 completo (tablero 10) y 2026 hasta la semana 37 (tableros 04, 05 y 06, que leen los mismos datos). Solo hay series nacionales. No hay 2024 en ningún tablero encontrado.

Revisión de las series antes de cargarlas:

- Los totales cuadran entre vistas. Los confirmados semanales suman lo mismo que la cifra suelta del tablero (203 en 2025, 48 en 2026). La serie semanal de sospechosos de 2026 (4.786) coincide con el gráfico por grupo de edad (unos 4.750).
- La escala coincide con OpenDengue. Los sospechosos de 2025 (5.833) están al nivel de OpenDengue en 2021 y 2023, y el canal endémico que publica MINSAL para 2025 tiene la misma escala que los cuartiles de OpenDengue de 2014 a 2024.
- La serie es mucho más lisa que un conteo semanal crudo. Medida como la desviación de cada semana respecto a sus vecinas, en unidades de ruido de Poisson, da 0,28 en 2025 y 0,70 en 2026. OpenDengue da entre 1,2 y 8,3 de 2014 a 2023 y 0,26 en 2024. El tablero no dice qué proceso produce esa forma.
- Hay saltos al cambiar de año. Los sospechosos pasan de 39 en la semana 52 de 2025 a 214 en la semana 1 de 2026.
- El calendario coincide con `semanas_epidemiologicas`. Las etiquetas de mes de 2026 cuadran en las 37 semanas sin desfase y fallan entre 8 y 13 con una semana de desfase. La semana 53 de 2025 (28 de diciembre al 3 de enero) no aparece publicada.

## Decisión

**A. Fuente nueva:** `fuentes_datos.codigo = 'minsal_tablero'`.

**B. Quinto valor de `clasificacion`: `'sospechoso'`**, tomado tal cual del nombre que usa la fuente ("Casos Sospechosos de Dengue"), mismo criterio que `'total'` (ADR 0005). Los confirmados del tablero se cargan como `'confirmado'`; IRA y neumonías, como `'notificado'` (ADR 0011).

**C. Carga desde archivos, nunca desde el sitio.** `cargar_minsal_tablero.py` lee los HAR de `data/raw/minsal_tablero/` (no versionado, como los PDF; procedencia y sha256 en `data/README.md`). Toma el año de la consulta SQL y rechaza la respuesta si no hay un año único, si una semana se repite o si un valor no es entero.

**D. Una cifra por semana, la de la captura más reciente.** Si dos capturas difieren, el cargador lo informa como revisión de MINSAL. Las capturas viejas se conservan.

**E. Sin relleno.** La semana 53 de 2025 queda sin fila.

**F. Separada de las otras fuentes.** Las consultas que describen los PDF departamentales filtran por `minsal_pdf`, y las que leen OpenDengue por `opendengue_v1_3`. Con esta carga se añadió ese filtro a la antigüedad de IRA y neumonías (`api/vigilancia.py`) y a la cobertura respiratoria (`api/cobertura.py`), que antes contaban cualquier fuente.

## Consecuencias

- Hay datos de casos de 2025 y 2026 por primera vez, aunque solo nacionales.
- La serie del tablero no se puede empalmar con OpenDengue como si fuera la misma: tiene otra forma y no comparte ninguna semana con ella. Usarla en el nowcast exige validarla aparte (ADR 0020).
- OpenDengue 2024 tiene la misma forma lisa que el tablero, así que es probable que venga de la misma fuente. Eso afecta a 2024 como temporada de validación del nowcast y queda pendiente de revisar.
- Actualizar exige que una persona vuelva a capturar el tablero. No hay descarga programada.

## Migración

`db/migrations/0012_fuente_tablero_minsal.sql`: recrea el `CHECK` de `clasificacion` con `'sospechoso'`, actualiza su comentario e inserta la fuente `minsal_tablero`.

## Enmienda (2026-09-27): forma de la serie y uso en el nowcast

Dos puntos de las consecuencias quedaron resueltos con los experimentos de predicción
(`docs/experimentos/experimento-nowcast-mejora.md` y `experimento-nowcast-tendencia.md`).

* La definición es la misma. El `total` de OpenDengue en 2019 (27.470) coincide con los
  sospechosos nacionales que publicó MINSAL ese año, así que la diferencia con OpenDengue está en
  la forma, no en la definición.
* La forma es la de un promedio hacia atrás de 6 o 7 semanas. La consulta del tablero solo suma
  `total_casos` de `diagnosticos_acumulados`, así que el promedio viene de la tabla de MINSAL.
  Aplicado a los años crudos de OpenDengue, ese promedio deja la misma huella, y la caída de Semana
  Santa de 2026 aparece en la semana 13 sin adelantarse. El núcleo exacto no se puede recuperar.
  Pasa lo mismo con IRA y neumonías, y con OpenDengue 2024.
* Desde 2025-S1 el nowcast usa esta serie con un método propio, la mezcla del experimento de
  tendencia, en prueba con semanas publicadas desde 2026-S38 (enmienda de ADR 0020). La serie
  mixta es OpenDengue hasta 2024-S52 y el tablero desde 2025-S1, sin semanas compartidas.
* La serie nacional del sitio usa el mismo empalme. `GET /api/casos-nacional` devuelve el total
  de OpenDengue y, en las semanas posteriores a su última fila, los sospechosos del tablero, con
  `fuente` en cada fila para que la curva marque el tramo. La antigüedad de M4
  suma la serie `dengue_tablero_nacional`. Es una excepción acotada a la regla F: las consultas
  departamentales y las de IRA y neumonías siguen filtrando por `minsal_pdf`.
