# EPI-Aetheris — Fuentes de datos: evidencia y trampas de ingesta

> Referencia técnica profunda, no lectura por defecto. Consultar al construir o depurar el pipeline de ingesta. Las decisiones que se apoyan en esta evidencia están en `01-decisiones-cerradas.md`; aquí vive el detalle empírico que las sostiene, verificado contra datos reales descargados, no contra documentación de marketing ni memoria de entrenamiento (exigencia del Pilar 3, TMP-STC).

## Casos de dengue

### OpenDengue

`opendengue.org`, distribución en Figshare con DOI y licencia, v1.3. Verificado descargando y filtrando `Spatial_extract_V1_3.csv` (~2.8M filas):

| Nivel | Cobertura confirmada | Resolución temporal | Fuente interna |
|---|---|---|---|
| Admin0 (nacional) | 1978–2024 | Semanal desde 2018 | PAHO/PLISA |
| Admin1 (departamento) | **Solo 2000–2009** | Mensual | Project Tycho |
| Admin2 (municipio) | No existe | — | — |

Los 14 departamentos están cubiertos en Admin1, pero no hay una sola fila departamental posterior a 2009. Admin0 resuelve el nivel nacional sin problema (uso narrativo/exploratorio). Admin1 (2000–2009, mensual) es incompatible con un clasificador semanal — no se usa para validación retrospectiva (ver `01-decisiones-cerradas.md`, criterio de éxito).

### Boletines epidemiológicos del MINSAL (PDF, salud.gob.sv)

Tabla con texto extraíble (no requiere OCR), 14 departamentos, fuente citada "VIGEPES", actualizada semana a semana. **Ventana parseable confirmada: 2018–2023.**

**Dos esquemas de tabla, detectados por documento, nunca por rango de año** (el corte no es limpio en el límite 2020–2021; 2020 tardío ya trae el formato simplificado de Familia B):
- *Familia A:* título "Casos probables de dengue SE_X_ y tasas de incidencia... de casos confirmados de dengue SE_Y_, por departamento" — columnas Probable / Confirmado / Tasa. 2020 tiene mayor riesgo de desalineación en extracción de texto plano (celdas vacías observadas) — conviene extracción posicional.
- *Familia B:* título "Casos probables y confirmados de dengue por departamento, El Salvador [año]" — columnas Probable (semana actual) / Confirmado (semana−1), sin columna de tasa. Extracción limpia.
- **Detección correcta:** por presencia/ausencia de la columna "Tasa x 100.000" en el documento, nunca por año.

En ambas familias, "probable" y "confirmado" son **semanas epidemiológicas distintas** dentro de la misma fila — el desfase se lee del título de cada tabla, nunca se asume igual al número de semana del archivo.

**Trampas del dato fuente, confirmadas empíricamente (inspección manual de 10+ boletines):**

1. **El año impreso dentro del PDF no es confiable.** `SE012023.pdf` tiene título de tabla "El Salvador 2022" pese a ser SE01/2023 por nombre y URL. El año se deriva siempre del nombre de archivo/metadato de índice, nunca del texto interno; cualquier discrepancia interno-vs-archivo se marca para revisión, no se confía en ninguno de los dos silenciosamente.
2. **Celdas en blanco significan cero**, no dato ausente — ingerir como `0`, nunca `NULL`, nunca fila omitida.
3. **"Otros países" es una fila real** que no mapea a ningún `regiones.codigo` y está excluida del total nacional publicado — separarla antes de sumar; los 14 departamentos deben igualar el total exactamente (base del chequeo `boletines_procesados.validacion_cuadra`).
4. **Republicaciones con sufijo de versión** (`_v2`…`_v4`) son correcciones del *mismo* boletín, no boletines distintos — reprocesar debe sobrescribir, con precedencia explícita por versión más alta, nunca por orden de recorrido del directorio (ver ADR 0004 en `01-decisiones-cerradas.md`).
5. **El nombre de archivo no detecta boletines de vacaciones.** `SE142023-Semana-Santa.pdf` matchea un patrón `SE\d+` válido y aun así no trae tabla departamental — detectar por contenido (ausencia del ancla de tabla departamental), no por nombre. Semana Santa es móvil (SE13 en 2018, SE16 en 2019, SE13 en 2021, SE15 en 2022, SE14 en 2023) — la detección por semana fija no funciona en ningún caso.
6. **En Familia A, la columna de tasa no corresponde a "probable".** El título declara probables de una semana y tasa de incidencia de *confirmados* de otra. Despejar población dividiendo probables entre tasa produce un número plausible y sin sentido. Fórmula correcta: `población = confirmados(SE_Y) / tasa(SE_Y) × 100.000`, donde `SE_Y` es la semana que el encabezado declara para la serie de confirmados. Sin verificar todavía si la tasa es semanal o acumulada al año — chequear encabezado/nota al pie por documento. Despejar con las filas de mayor conteo confirmado (con conteos chicos el error relativo se dispara) y validar que el denominador sea constante dentro de cada departamento-año.
7. **Boletines que cubren más de una semana** (confirmado: SE01+SE02 de 2018 combinadas en un archivo). No repartir el conteo entre semanas (fabricación) ni ingerir como una sola semana (duplica la magnitud y contamina cualquier línea base). Se detecta por encabezado (rango de dos semanas) y se registra como `ausencia_esperada` para cada una de las dos semanas, igual que un boletín de vacaciones.

**Verificación pendiente — desfase de una semana en los huecos de vacaciones:** los huecos registrados no coinciden con las semanas de feriado calculadas, están desplazados en uno (ej. Semana Santa 2018 en SE13, boletín faltante SE51/SE12). Explicación probable: el boletín de la semana N se publica durante la N+1. Sin verificar si en 2021–2023 el dato ausente es el de la semana del nombre de archivo o el de la anterior — se resuelve leyendo el encabezado de tres PDF. Mientras no se resuelva, no precalcular ninguna tabla de huecos por semana.

**Validación cruzada gratuita:** la suma de los 14 departamentos coincide con el total nacional publicado en la misma tabla (verificado en SE34/2022: 37 probables y 55 confirmados, exacto). El pipeline debe usar esto como chequeo automático — mismatch → `revision_manual`, nunca ingesta silenciosa.

**Cobertura real de publicación** (verificado contra páginas índice oficiales por año):
- 2018: faltan SE12 y SE51 (no elaborados, nota oficial MINSAL). SE01+SE02 combinadas.
- 2019: faltan SE15, SE31, SE51 (no elaborados, nota oficial).
- 2020–2023: las 52 semanas tienen archivo.
- **Boletines de vacaciones (Semana Santa, Fiestas Agostinas, Fin de Año — 3/año) nunca traen tabla departamental**, en ningún año de la ventana — confirmado leyendo Fiestas Agostinas 2019 (resumen nacional agregado interanual, sin desagregación geográfica) y por evidencia indirecta de tamaño en Fin de Año 2022 (273 KB vs. ~8 MB de un boletín semanal normal). Esto reduce la cobertura departamental real a **~49/52 semanas por año** en toda la ventana 2018–2023.

**Nombres de archivo irregulares** (sufijos de versión, semanas combinadas, nombres libres en vacaciones) — no diseñar el scraper sobre plantilla fija de URL; usar como entrada la página índice oficial por año.

**Mecanismo de descarga automatizada** (confirmado empíricamente): sitio en WordPress + WordPress Download Manager 3.1.15. Sin bloqueo Cloudflare/WAF en `salud.gob.sv` (el header `cf-ray` solo indica CDN/proxy). Distinto del subdominio `boletin.salud.gob.sv` (dashboard 2024+), confirmado bloqueado por Cloudflare Bot Management (`__cf_bm`) — descartado como fuente automatizable, uso solo para validación visual manual.

- *Ruta directa (preferida):* la página índice de cada año expone en el HTML las URLs reales (`salud.gob.sv/wp-content/uploads/download-manager-files/{nombre}.pdf`). Un fetch entrega todas las URLs de la temporada.
- *Ruta de respaldo:* la página individual de cada boletín trae el enlace real en `data-downloadurl` (clase `wpdm-download-link download-on-click`), patrón `?wpdmdl={ID}` (el parámetro `refresh` no es necesario).
- *Validación de archivo:* usar firma de bytes (`%PDF` al inicio), no `Content-Type` (siempre `application/octet-stream`, no confirma nada).
- **Cerrado:** la ruta directa se sostuvo en los cinco años de la ventana. Descarga histórica completa ejecutada: **264 PDF** en `backend/ingestion/data/raw/minsal/{2018,2019,2021,2022,2023}/` (2020 no descargado, excluido de la ventana de entrenamiento). La variación de tamaño entre años no resultó bloqueante.

**Límites administrativos (geometría del mapa):** El Salvador tiene 14 departamentos (Admin1), 48 municipios (Admin2), 266 distritos (Admin3) — geoBoundaries gbOpen SLV ADM1 (`boundaryID SLV-ADM1-98794003`, fuente OSM vía osm-boundaries.com, build dic. 2023). **`shapeISO` viene vacío en las 14 features** — `regiones.codigo` (ISO 3166-2:SV) no sirve como llave de unión con el mapa. La unión real es por `shapeName` normalizado (quitar prefijo "Departamento de ", NFD sin diacríticos, minúsculas, espacios colapsados) contra `regiones.nombre` — 14-a-14 exacto, sin sobrantes. Resuelto en tiempo de construcción y horneado en el GeoJSON (`backend/ingestion/build_geo_departamentos.py`, ver `docs/adr/0002-join-mapa-geojson-por-nombre.md`); el frontend compara por igualdad estricta, sin normalización en TypeScript. Aborta si la unión no da 14 a 14. El `boundaryLicense` de esta boundary específica es "CC BY-SA 2.0" (no el CC BY 4.0 genérico de geoBoundaries) — pendiente decidir qué texto de licencia mostrar en la ficha de atribuciones.

## Clima — Open-Meteo

`open-meteo.com`. Auditado contra documentación oficial vigente (`/en/docs`, `/pricing`, `/terms`) y el repositorio de código (`open-meteo/open-meteo`, `open-meteo/open-data`), incluyendo hilos de mantenedores. No fue posible ejecutar una llamada real al endpoint (bloqueada por `robots.txt` para la herramienta de fetch disponible en la auditoría original) — verificación contra documentación oficial en vivo, no contra memoria de entrenamiento.

**Modelo por variable, cobertura y evidencia de la decisión:** ver tabla y razonamiento en `01-decisiones-cerradas.md`. Detalle adicional de verificación aquí:

- **Cobertura temporal:** ERA5 desde 1940 (0,25°, ~25 km), ERA5-Land desde 1950 (0,1°, ~11 km), ECMWF IFS desde 2017 (9 km). La ventana de entrenamiento (2018, 2019, 2021–2023) está cubierta cómodamente por los tres.
- **Trampa confirmada del cero falso:** bajo `era5_land`, en un día de lluvia real (2023-06-05, 12,5 mm según otro modelo), `precipitation_sum` da `null` correctamente pero `precipitation_hours` da `0.0` — cero fabricado. Guarda de pipeline en `01-decisiones-cerradas.md`.
- **Variables en agregación diaria:** temperatura máxima/mínima/media, humedad relativa media, punto de rocío bajo `era5_land`; precipitación acumulada y horas de lluvia bajo `era5`. Sin agregación semanal nativa en la API — solo horaria y diaria, el pipeline construye la semana epidemiológica sumando/promediando diarios.
- **Límites de uso gratuito:** 600 llamadas/min, 5.000/hora, 10.000/día, 300.000/mes. Peor caso estimado (si el peso se multiplicara por ubicación): la descarga histórica completa para 14 departamentos ronda ~2.200 llamadas ponderadas contra el techo de 10.000/día — sobra margen. No documentado si el conteo fraccional (más de 10 variables o más de 2 semanas por ubicación) se multiplica al combinar ubicaciones en una sola petición — conviene una llamada de prueba pequeña antes de programar la ingesta completa.
- **Uso no comercial:** términos oficiales listan explícitamente "investigación pública realizada en instituciones públicas" y "contenido educativo" como uso no comercial calificado — un proyecto de bachillerato técnico de institución pública, en feria técnica, sin publicidad ni suscripciones, encaja directamente.
- **Formato de respuesta:** JSON ancho (una columna por variable, `time` compartido) — requiere `melt`/`unpivot` a `(región, periodo, variable, valor)`. Multi-location devuelve un array de objetos por ubicación, en el mismo orden en que se dieron las coordenadas, cada uno con `latitude`/`longitude`/`elevation`/`utc_offset_seconds`/`daily` propios. `elevation` no depende del modelo/variable pedido (confirmado: `era5_land` y `best_match` devuelven la misma elevación para el mismo punto) — una sola llamada la puebla. `utc_offset_seconds` confirma que los agregados diarios caen en hora local cuando se fija `timezone=America/El_Salvador`, no UTC — necesario para que los rezagos semanales no queden corridos un día. La coordenada que devuelve la API es el centro de la celda de grilla efectivamente usada, no necesariamente la pedida — la relación coordenada↔departamento debe guardarse en el pipeline, no asumirse.

### Coordenadas por departamento (insumo para las llamadas a Open-Meteo)

Punto representativo del polígono de mayor área por departamento (`shapely.representative_point()`, no centroide aritmético — La Unión y Usulután tienen geometría costera/insular compleja donde un centroide naive puede caer en agua), calculado sobre el GeoJSON ya horneado con el código de departamento (`backend/ingestion/compute_centroides.py`), con aserciones de caja geográfica para detectar una inversión de latitud/longitud (no produce error, produce clima de otro lugar del planeta). Distancia verificada entre punto solicitado y centro de celda real: 1,8–6,5 km. Persistido en `regiones.centroide_lat/lon/elevacion_m` (ADR 0003, ver `01-decisiones-cerradas.md`) — deliberadamente **no** el centro de celda que devuelve la API, que es detalle de fuente/modelo, no identidad de la región.

## Cobertura temporal real por fuente (resumen para diseño de ingesta)

| Ventana | Nacional | Departamental |
|---|---|---|
| 2018–2019 | OpenDengue Admin0 | MINSAL PDF, Familia A, con huecos puntuales (2–3 semanas/año) |
| 2020 | OpenDengue Admin0 | MINSAL PDF, Familia A, riesgo de desalineación — **no descargado** (excluido de entrenamiento) |
| 2021–2023 | OpenDengue Admin0 | MINSAL PDF, Familia B, limpio y consistente |
| 2024–presente | OpenDengue Admin0 | Sin fuente automatizable (dashboard bloqueado por Cloudflare) |

El hueco 2024–presente a nivel departamental es riesgo real, no resuelto.

## Capa de datos intermedia

El parser vuelca la tabla cruda extraída de cada boletín (incluida la columna de tasa de Familia A, siempre conservada aunque no se use downstream) en `backend/ingestion/data/interim/` antes de normalizar — así los 264 PDF se leen una sola vez y todo lo demás trabaja sobre esa capa. `data/interim/` debe estar gitignoreada igual que `data/raw/` — verificar que siga así antes de commitear código de ingesta.

**Regla de datos en el repositorio:** los PDF descargados y cualquier artefacto derivado de la ingesta son datos, no código, y no se versionan (excepción deliberada: `backend/ingestion/geo/slv-adm1-source.geojson`, documentada en el `CLAUDE.md` de la raíz — no la "corrija" quitándola del control de versiones).

## Pendiente, sin avance registrado

Pytest para el pipeline de ingesta no existe todavía. Tres boletines inspeccionados manualmente con cifras conocidas (`SE232018`, `SE522019_v2`, `SE522023`) están disponibles como casos de referencia una vez que arranque ese trabajo.
