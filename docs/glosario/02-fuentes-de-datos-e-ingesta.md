# Rama 2 · Fuentes de datos e ingesta

Vocabulario del camino que recorre un dato desde la institución que lo publica hasta una fila de la base: qué fuentes usa el proyecto, cómo están hechos los boletines de MINSAL, qué trampas traen y cómo las trata la ingesta.

**Para quién es.** Para quien abre un script de `backend/ingestion/`, una fila de `boletines_procesados` o un ADR de fuentes y necesita saber qué significa cada palabra antes de fiarse de una cifra.

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris), **Dónde** (archivo, ADR o endpoint) y **Ojo** (errores frecuentes). Las expansiones de siglas que el repositorio no da se marcan como «de uso general».

**Ramas vecinas.** Los conceptos de salud pública están en [`01-epidemiologia-y-vigilancia.md`](01-epidemiologia-y-vigilancia.md); las fuentes climáticas y oceánicas (Open-Meteo, ONI) y el punto representativo de cada departamento, en [`03-clima-y-ambiente.md`](03-clima-y-ambiente.md); las tablas y migraciones, en [`07-base-de-datos-y-migraciones.md`](07-base-de-datos-y-migraciones.md); las tarjetas y los ADR, en [`10-proceso-gobernanza-y-documentacion.md`](10-proceso-gobernanza-y-documentacion.md).

<!-- INDICE:INICIO -->

## Índice alfabético (74 entradas)

- **0-9** — [2020 excluido](#2020-excluido)
- **A** — [Acumulado con rango en el título](#acumulado-con-rango-en-el-título) · [Acumulado desde SE1](#acumulado-desde-se1) · [ausencia_esperada](#ausencia_esperada)
- **B** — [Bitácora de boletines (boletines_procesados)](#bitácora-de-boletines-boletines_procesados) · [Bloqueo del tablero y regla de no consultarlo](#bloqueo-del-tablero-y-regla-de-no-consultarlo) · [Boletín de semanas combinadas](#boletín-de-semanas-combinadas) · [Boletín de vacaciones](#boletín-de-vacaciones) · [Boletín reimpreso](#boletín-reimpreso) · [Boletines epidemiológicos de MINSAL (PDF)](#boletines-epidemiológicos-de-minsal-pdf)
- **C** — [Capa cruda y capa intermedia](#capa-cruda-y-capa-intermedia) · [Captura HAR](#captura-har) · [case_definition_standardised](#case_definition_standardised) · [Caso de referencia verificado a mano](#caso-de-referencia-verificado-a-mano) · [Cobertura real de publicación](#cobertura-real-de-publicación) · [Convención de «Otros países»](#convención-de-otros-países) · [Corrección retroactiva](#corrección-retroactiva) · [Corrida exploratoria, parser de producción y cargador](#corrida-exploratoria-parser-de-producción-y-cargador) · [Cuadre (validacion_cuadra)](#cuadre-validacion_cuadra)
- **D** — [Desacumulación](#desacumulación) · [Desfase de una semana en los huecos de vacaciones](#desfase-de-una-semana-en-los-huecos-de-vacaciones) · [Disposición lado a lado](#disposición-lado-a-lado) · [Dry-run](#dry-run)
- **E** — [Errores de plantilla de MINSAL](#errores-de-plantilla-de-minsal) · [Estados de la bitácora](#estados-de-la-bitácora)
- **F** — [Familia A y Familia B](#familia-a-y-familia-b) · [Firma de bytes %PDF](#firma-de-bytes-pdf) · [Fixture de texto extraído](#fixture-de-texto-extraído) · [Fuente de datos (fuentes_datos)](#fuente-de-datos-fuentes_datos)
- **G** — [geoBoundaries (gbOpen)](#geoboundaries-gbopen) · [GeoJSON departamental](#geojson-departamental) · [Guarda de colisión de clave](#guarda-de-colisión-de-clave)
- **H** — [Hueco departamental posterior a 2023](#hueco-departamental-posterior-a-2023) · [Hueco entre cortes](#hueco-entre-cortes)
- **I** — [Idempotencia y upsert](#idempotencia-y-upsert) · [Ingesta](#ingesta) · [Inventario de vigilancia de virus](#inventario-de-vigilancia-de-virus)
- **N** — [Narrativa rezagada](#narrativa-rezagada) · [Nombres de archivo irregulares](#nombres-de-archivo-irregulares)
- **O** — [OCR](#ocr) · [OpenDengue](#opendengue)
- **P** — [Página índice oficial](#página-índice-oficial) · [Pie de estratificación](#pie-de-estratificación) · [Pin del límite (BOUNDARY_ID)](#pin-del-límite-boundary_id) · [Positividad publicada, no recalculada](#positividad-publicada-no-recalculada) · [Primer corte del año](#primer-corte-del-año)
- **R** — [Resolución de la semana por calendar_start_date](#resolución-de-la-semana-por-calendar_start_date) · [Revisión de MINSAL (la captura más reciente gana)](#revisión-de-minsal-la-captura-más-reciente-gana) · [Revisión manual documentada (REVISIONES_MANUALES)](#revisión-manual-documentada-revisiones_manuales) · [revision_manual](#revision_manual) · [Ruta directa y ruta de respaldo](#ruta-directa-y-ruta-de-respaldo)
- **S** — [Semana 53 sin fila](#semana-53-sin-fila) · [Separador de miles inconsistente](#separador-de-miles-inconsistente) · [Serie mixta (empalme)](#serie-mixta-empalme) · [Serie suavizada del tablero](#serie-suavizada-del-tablero) · [Series nacionales de IRA y neumonías del tablero](#series-nacionales-de-ira-y-neumonías-del-tablero) · [shapeName y shapeISO](#shapename-y-shapeiso) · [Sin relleno (nunca fabricar)](#sin-relleno-nunca-fabricar) · [sin_texto_extraible](#sin_texto_extraible) · [Sospechoso (serie nacional del tablero)](#sospechoso-serie-nacional-del-tablero)
- **T** — [Tabla de vigilancia laboratorial de virus](#tabla-de-vigilancia-laboratorial-de-virus) · [Tabla departamental](#tabla-departamental) · [Tabla departamental de IRA](#tabla-departamental-de-ira) · [Tabla departamental de neumonías](#tabla-departamental-de-neumonías) · [Tablero de vigilancia de MINSAL (Superset)](#tablero-de-vigilancia-de-minsal-superset) · [Texto extraíble y tabla-imagen](#texto-extraíble-y-tabla-imagen) · [Total impreso y cuadre](#total-impreso-y-cuadre) · [Trampas de las fuentes (catálogo)](#trampas-de-las-fuentes-catálogo) · [Trazabilidad (boletin_id)](#trazabilidad-boletin_id)
- **U** — [Unión por nombre normalizado](#unión-por-nombre-normalizado)
- **V** — [Ventana 2018–2023 (ventana parseable)](#ventana-20182023-ventana-parseable) · [Ventana de alcance frente a límite de la fuente](#ventana-de-alcance-frente-a-límite-de-la-fuente) · [Verificación 4/4](#verificación-44) · [Versión de boletín (_v2, _v3, _v4)](#versión-de-boletín-_v2-_v3-_v4)

<!-- INDICE:FIN -->

## 1. Las fuentes y su procedencia

### Fuente de datos (`fuentes_datos`)

**Qué es.** El origen declarado de cada cifra.

**En el proyecto.** Es una tabla catálogo (`codigo` único, `nombre`, `url_referencia`, `notas`) a la que apuntan `casos_epidemiologicos`, `variables_ambientales` y `vigilancia_virus_respiratorios` mediante `fuente_id`. Hay seis códigos:

| Código | Qué aporta | Alta |
|---|---|---|
| `opendengue_v1_3` | Serie nacional semanal de dengue | migración `0001` |
| `minsal_pdf` | Tablas departamentales de los boletines en PDF | migración `0001` |
| `open_meteo_era5_land` | Temperatura, humedad y punto de rocío | migración `0001` |
| `open_meteo_era5` | Precipitación | migración `0004` ([ADR 0006](../adr/0006-atribucion-fuente-climatica-era5.md)) |
| `noaa_oni` | Índice oceánico ONI | migración `0006` ([ADR 0008](../adr/0008-fuente-noaa-oni.md)) |
| `minsal_tablero` | Series nacionales del tablero de MINSAL | migración `0012` ([ADR 0021](../adr/0021-fuente-tablero-minsal.md)) |

**Ojo.** Nada en el esquema obliga a que una variable o una clasificación se cargue con la fuente correcta; esa correspondencia es disciplina del cargador ([ADR 0005](../adr/0005-clasificacion-total-opendengue.md), [ADR 0006](../adr/0006-atribucion-fuente-climatica-era5.md)). Las consultas que describen los PDF filtran por `minsal_pdf` y las de OpenDengue por `opendengue_v1_3`, para no mezclar definiciones.

### OpenDengue

**Qué es.** Proyecto abierto que reúne y estandariza series de dengue de ministerios de salud y las distribuye en extractos versionados, con DOI y licencia.

**En el proyecto.** Fuente de la serie **nacional semanal** (`clasificacion = 'total'`, fuente `opendengue_v1_3`). Se usa la versión 1.3, extracto de máxima resolución espacial (`Spatial_extract_V1_3`), distribuido en Figshare con el DOI `10.6084/m9.figshare.24259573`. Se obtuvo el 2026-08-04 y el CSV original, de unos 2,8 millones de filas de todos los países, se filtró a El Salvador (`ISO_A0 == "SLV"`, 2.208 filas) sin otra limpieza. Cobertura confirmada: nivel nacional (Admin0) de 1978 a 2024, semanal completa desde 2014 (más una fila parcial en 2013); nivel departamental (Admin1) solo de 2000 a 2009 y mensual; Admin2 no existe. El extracto termina en la semana del 2024-12-22. La fuente interna es PAHO/PLISA para Admin0 y Project Tycho para Admin1 (referencia técnica de fuentes).

**Dónde.** `backend/ingestion/cargar_opendengue.py`; procedencia en `backend/ingestion/data/README.md`.

**Ojo.** `data/README.md` dice que la resolución semanal empieza en 2018; la corrección (desde 2014) se hizo al cargar la serie, y el filtro 2018–2024 de la carga es una decisión de alcance, no un límite de la fuente (la carga vigente son 574 semanas, 2014–2024). Además, la definición de caso de OpenDengue **no** es la de laboratorio de MINSAL ([`total`](01-epidemiologia-y-vigilancia.md#total)), y sus cifras no coinciden al peso con las de MINSAL: 2018 tiene 8.448 casos cargados frente a 8.443 en el boletín SE52, y 2022, 16.542 frente a 16.529. La diferencia se documenta y no se fuerza a cuadrar.

### `case_definition_standardised`

**Qué es.** Columna del CSV de OpenDengue con la definición de caso estandarizada de cada fila.

**En el proyecto.** Para El Salvador, a resolución nacional y semanal, vale `'Total'` en el 100 % de las 574 filas: OpenDengue no publica un desglose probable y confirmado para este país. Por eso la serie se guarda como `clasificacion = 'total'` (ADR 0005) y el cargador levanta un error si aparece otro valor, en vez de adivinar qué hacer.

**Dónde.** `backend/ingestion/cargar_opendengue.py`, [ADR 0005](../adr/0005-clasificacion-total-opendengue.md).

### Resolución de la semana por `calendar_start_date`

**Qué es.** El CSV de OpenDengue trae `calendar_start_date` y `calendar_end_date` (siempre de domingo a sábado, coherente con la semana MMWR) pero no un número de semana.

**En el proyecto.** La semana se resuelve por **coincidencia exacta** de `calendar_start_date` con `semanas_epidemiologicas.fecha_inicio`, nunca recalculándola con `epiweeks` sobre el CSV. El filtro por rango de años se aplica después, sobre el año epidemiológico ya resuelto, porque el campo `Year` del CSV es calendario: una semana que arranca el 29 de diciembre puede ser la SE01 del año siguiente.

**Ojo.** Exige que `poblar_semanas_epidemiologicas.py` haya corrido antes; si no, el cargador avisa de las filas sin semana resuelta. Ver [`semanas_epidemiologicas`](07-base-de-datos-y-migraciones.md#semanas_epidemiologicas).

### Boletines epidemiológicos de MINSAL (PDF)

**Qué es.** Informe semanal en PDF que el Ministerio de Salud publicó en `salud.gob.sv` hasta 2023.

**En el proyecto.** Es la fuente `minsal_pdf`, la única con desglose **departamental** de dengue, IRA y neumonías. El corpus son **264 PDF** de 2018, 2019, 2021, 2022 y 2023 (2020 no se descargó). Cada boletín trae una tabla departamental de 14 departamentos con la fuente citada «VIGEPES», y otras tablas del mismo documento: IRA, neumonías, la vigilancia laboratorial de virus y, según el boletín, otras enfermedades (parotiditis, fiebre tifoidea, zika, chikungunya, EDAS; esta última sigla, de uso general, corresponde a enfermedades diarreicas agudas y el repositorio no la expande). MINSAL dejó de publicarlos después de 2023 ([ADR 0021](../adr/0021-fuente-tablero-minsal.md)).

**Dónde.** `backend/ingestion/minsal/` (descarga y parser), `backend/ingestion/data/raw/minsal/{año}/` (no versionado) y `backend/ingestion/data/README.md`.

**Ojo.** Los PDF no se versionan; del PDF solo se guarda texto extraído, como [fixture](#fixture-de-texto-extraído). El proyecto no republica los boletines, solo usa cifras agregadas (cláusula 6 de los términos de uso).

### Tablero de vigilancia de MINSAL (Superset)

**Qué es.** Tablero público, hecho con Apache Superset (plataforma de tableros de código abierto; el repositorio solo dice «tablero Superset»), en `boletin.salud.gob.sv/superset/dashboard/{id}/?standalone=1`. Desde 2024 MINSAL publica ahí en lugar de en PDF.

**En el proyecto.** Es la fuente `minsal_tablero`, con **solo series nacionales**: dengue sospechoso, dengue confirmado, IRA y neumonías. Las primeras capturas (2026-09-27) cubren 2025 completo (tablero 10, S1–S52) y 2026 hasta la S37 (tableros 04, 05 y 06, que leen los mismos datos aunque su rótulo diga otra fecha). No hay 2024 en ningún tablero encontrado. No hay descarga programada: actualizar exige que una persona vuelva a capturar el tablero.

**Dónde.** [ADR 0021](../adr/0021-fuente-tablero-minsal.md), `backend/ingestion/cargar_minsal_tablero.py`, `backend/ingestion/data/README.md`.

### Captura HAR

**Qué es.** Un archivo HAR (HTTP Archive, expansión de uso general) es el registro que las herramientas de desarrollo del navegador guardan de las peticiones y respuestas de una sesión.

**En el proyecto.** Es la vía por la que entran los datos del tablero. Una persona abre el tablero, exporta el HAR y `cargar_minsal_tablero.py` lo lee. Cada respuesta `POST /api/v1/chart/data` trae la consulta SQL, con el año escrito (`da.anio=2025`), y una fila por semana (`semana_mes` con el formato «NN-Mes»). El nombre del archivo lleva el tablero y la hora UTC de la captura (`tablero-10_20260927T0542Z.har`) y `data/README.md` registra el sha256 de cada una.

**Ojo.** El cargador **falla y no carga** si la consulta no trae un año único, si una semana se repite o si un valor no es entero: «mejor no cargar que cargar mal». Las capturas nuevas se guardan sin borrar las anteriores.

### Bloqueo del tablero y regla de no consultarlo

**Qué es.** El subdominio del tablero rechaza las peticiones automáticas (la referencia técnica de fuentes lo atribuye a la gestión de bots de Cloudflare).

**En el proyecto.** `backend/ingestion/minsal/common.py` prohíbe que scripts y agentes de código del repositorio hagan peticiones a `boletin.salud.gob.sv`. Abrirlo en un navegador y guardar lo que el propio sitio descarga es el uso normal del sitio, y esos archivos sí pueden ser fuente ([ADR 0021](../adr/0021-fuente-tablero-minsal.md)). Es distinto de `www.salud.gob.sv`, donde se descargaron los PDF.

### geoBoundaries (gbOpen)

**Qué es.** Proyecto abierto de límites administrativos del mundo (gbOpen es su colección de licencia abierta).

**En el proyecto.** Fuente de la geometría de los 14 departamentos: `SLV` nivel `ADM1`, `boundaryID` `SLV-ADM1-98794003`, con datos de OpenStreetMap obtenidos a través de osm-boundaries.com (versión de diciembre de 2023). Se usa la variante simplificada (`simplifiedGeometryGeoJSON`, unos 117 KB), suficiente para Leaflet a escala departamental. La licencia que reporta esa capa es **CC BY-SA 2.0**, no el CC BY 4.0 genérico del proyecto.

**Dónde.** [ADR 0002](../adr/0002-join-mapa-geojson-por-nombre.md), `backend/ingestion/geo/slv-adm1-source.geojson`, `backend/ingestion/build_geo_departamentos.py`.

**Ojo.** El ADR 0002 y la Biblioteca 04 de este repositorio hablan de atribución pendiente, pero la cláusula 6 de los términos de uso ya declara los límites de geoBoundaries con licencia CC BY-SA 2.0.

### GeoJSON departamental

**Qué es.** Formato abierto que describe geometrías geográficas en JSON.

**En el proyecto.** Hay dos archivos: el **fuente** (`backend/ingestion/geo/slv-adm1-source.geojson`, versionado tal como se descargó, sin tocar) y el **derivado** (`web/public/geo/slv-adm1.geojson`), al que el build le añade la propiedad `codigo` (por ejemplo `SV-AH`). El derivado se regenera con `build_geo_departamentos.py`; no se edita a mano.

### `shapeName` y `shapeISO`

**Qué es.** Propiedades de cada feature del GeoJSON de geoBoundaries: el nombre (`shapeName`) y el código ISO (`shapeISO`).

**En el proyecto.** `shapeISO` viene **vacío** en las 14 features y `shapeName` es inconsistente: la mayoría lleva el prefijo «Departamento de » y dos no (`La Libertad` y `San Vicente`). Por eso la unión con `regiones` no puede hacerse por código sino por nombre normalizado.

### Unión por nombre normalizado

**Qué es.** Emparejar los departamentos del mapa con los de la base comparando sus nombres una vez limpiados.

**En el proyecto.** Se hace **una sola vez, en Python, al construir el mapa**: se quita el prefijo «Departamento de » (sin distinguir mayúsculas), se aplica `unicodedata.normalize('NFD')` para eliminar los diacríticos, se pasa a minúsculas y se colapsan los espacios. El script aborta con código de salida distinto de cero si la unión no da **14 a 14**. El frontend no normaliza nada: une por igualdad estricta sobre `properties.codigo`, para no reimplementar la normalización en dos lenguajes.

**Dónde.** [ADR 0002](../adr/0002-join-mapa-geojson-por-nombre.md); `backend/ingestion/tests/test_build_geo_departamentos.py` compara el catálogo del script con los `INSERT INTO regiones` de la migración `0001`.

### Pin del límite (`BOUNDARY_ID`)

**Qué es.** Fijar una versión exacta de un dato externo y comprobar en cada build que el archivo que se usa corresponde a esa versión.

**En el proyecto.** El archivo fuente está pineado al commit `9469f09` de geoBoundaries y `build_geo_departamentos.py` verifica en cada corrida que las 14 features tengan `shapeID` con el prefijo `98794003`, `shapeGroup` `SLV` y `shapeType` `ADM1`. Si el archivo deja de corresponder, el build falla. El script no descarga nada de la red: actualizar el límite exige reemplazar el archivo a mano.

## 2. Cobertura temporal y años

### Ventana 2018–2023 (ventana parseable)

**Qué es.** El rango de años de los boletines PDF que el parser puede leer.

**En el proyecto.** Es 2018 a 2023 **sin 2020**: cinco carpetas (2018, 2019, 2021, 2022 y 2023) con 264 PDF. Desde 2024 no hay PDF; la serie nacional de OpenDengue llega hasta 2024 y el tablero cubre 2025 y 2026, sin desglose departamental.

**Ojo.** La ventana es de **entrenamiento y de alcance**, no un límite de todas las fuentes: el clima y OpenDengue se cargan también fuera de ella ([Ventana de alcance frente a límite de la fuente](#ventana-de-alcance-frente-a-límite-de-la-fuente)).

### 2020 excluido

**Qué es.** La ausencia deliberada del año 2020 en la ventana departamental.

**En el proyecto.** `AGENTS.md` lo justifica por el subregistro real durante la pandemia de covid-19 y por el riesgo de extracción (las tablas de 2020 tienen mayor riesgo de desalineación en texto plano). Es una exclusión de ventana de entrenamiento: **no se filtra 2020 durante la ingesta** de las demás fuentes. La serie nacional de OpenDengue sí muestra 2020, con una nota explicativa.

**Ojo.** No es un hueco a «arreglar» ([Subregistro y subnotificación](01-epidemiologia-y-vigilancia.md#subregistro-y-subnotificación)).

### Cobertura real de publicación

**Qué es.** Qué semanas tienen realmente boletín y cuáles traen tabla departamental, verificado contra las páginas índice oficiales de cada año.

**En el proyecto.**

| Año | Semanas sin boletín o combinadas |
|---|---|
| 2018 | Faltan SE12 y SE51 (no elaborados, nota oficial de MINSAL); SE01 y SE02 vienen combinadas en un solo archivo |
| 2019 | Faltan SE15, SE31 y SE51 (no elaborados, nota oficial) |
| 2020–2023 | Las 52 semanas tienen archivo |

Además, los tres **boletines de vacaciones** de cada año (Semana Santa, Fiestas Agostinas y Fin de Año) nunca traen tabla departamental. La cobertura departamental efectiva ronda entonces las 49 de 52 semanas por año.

**Ojo.** «Sin tabla» no implica «vacaciones»: en 2023 `SE182023.pdf` es una semana normal sin tabla de dengue, así que la cobertura de 2023 es 48 de 52 ([trampa 9](#trampas-de-las-fuentes-catálogo)). El motivo de cada ausencia se verifica boletín por boletín, nunca desde el calendario de feriados.

### Hueco departamental posterior a 2023

**Qué es.** La falta de una fuente automatizable de casos por departamento después de 2023.

**En el proyecto.** La serie departamental termina en 2023 y la nacional de OpenDengue en diciembre de 2024. El tablero aporta 2025 y 2026, pero solo a nivel nacional. Es un riesgo reconocido y sin resolver. Como el clima sí llega hasta el año en curso ([ADR 0018](../adr/0018-extension-capa-climatica-presente.md)), todo lo que depende de casos queda anclado a la última semana con casos observados y M4 publica esa distancia como [antigüedad](05-modulos-descriptivos-y-alertas.md#antigüedad-m4).

### Ventana de alcance frente a límite de la fuente

**Qué es.** La diferencia entre el rango que el proyecto decide cargar y el rango que la fuente realmente ofrece.

**En el proyecto.** El filtro 2018–2024 de `cargar_opendengue.py` es de alcance; la fuente tiene datos nacionales desde 1978. Del mismo modo, `cargar_clima.py` **no excluye 2020**: esa exclusión es del entrenamiento y no de la ingesta, así que el clima se trae en rango continuo.

## 3. Anatomía de un boletín

### Familia A y Familia B

**Qué es.** Los dos esquemas de la tabla departamental de dengue que aparecen en los boletines.

**En el proyecto.**

| | Familia A | Familia B |
|---|---|---|
| Título | «Casos probables de dengue SE_X_ y tasas de incidencia… de casos confirmados de dengue SE_Y_, por departamento» | «Casos probables y confirmados de dengue por departamento, El Salvador [año]» |
| Columnas | Probable, Confirmado, Tasa | Probable, Confirmado, sin tasa |
| Años típicos | 2018–2020 | 2021–2023 |
| Extracción | Mayor riesgo de desalineación en texto plano, sobre todo en 2020 | Limpia |

**Ojo.** El esquema se detecta **por documento, mirando si existe la columna «Tasa x 100.000»**, nunca por año: el corte no es limpio en el límite 2020–2021 y 2020 tardío ya trae el formato simplificado. El valor se guarda en `boletines_procesados.familia_esquema`.

### Tabla departamental

**Qué es.** La tabla del boletín con una fila por departamento.

**En el proyecto.** Trae los 14 departamentos, más una fila «Otros países» y un total nacional impreso. Se localiza con una **ancla** de texto: se exigen «probable(s)» y «dengue» cerca de «por» o «según departamento», para no confundirla con la tabla de índices larvarios, que también dice «por departamento» en la misma página.

**Dónde.** `RE_ANCLA_TABLA_DEPTO` en `backend/ingestion/corrida_distribucion.py`.

### Acumulado desde SE1

**Qué es.** Un conteo que suma todo lo ocurrido desde la primera semana del año hasta la semana de corte.

**En el proyecto.** Los valores Probable y Confirmado de la tabla departamental (en las dos familias), y también los de IRA y neumonías, son **acumulados desde SE1**, no incidencia semanal. Se verificó porque el total nacional de cada tabla de 2023 es monótono no decreciente durante todo el año. Usarlos como conteo semanal corrompería la variable: una curva siempre creciente. Se corrige con la [desacumulación](#desacumulación).

**Ojo.** El título de cada tabla declara el **corte del acumulado** de cada serie, no la semana puntual de un conteo; por eso Probable y Confirmado pueden tener cortes distintos en la misma fila ([Semana de archivo, semana de corte y semana real](01-epidemiologia-y-vigilancia.md#semana-de-archivo-semana-de-corte-y-semana-real)).

### Total impreso y cuadre

**Qué es.** El total nacional que el propio boletín imprime al pie de la tabla, comparado con la suma de sus filas.

**En el proyecto.** La suma de los 14 departamentos (más «Otros países» según la convención) debe coincidir con el total impreso: es una validación cruzada gratuita. Si no cuadra en ninguna de las dos convenciones, el boletín va a `revision_manual` y no se ingiere en silencio. Un ejemplo verificado a mano: SE34 de 2022 cuadra exacto con 37 probables y 55 confirmados. El resultado se guarda en `validacion_cuadra` junto con `suma_departamental_*` y `total_nacional_publicado_*` (ver [`boletines_procesados`](07-base-de-datos-y-migraciones.md#boletines_procesados)).

**Ojo.** Existe una segunda validación cuando el PDF trae la tabla de situación acumulada: 14 departamentos más «Otros países» debe igualar esa cifra (por ejemplo SE23/2019: 276 + 3 = 279).

### Convención de «Otros países»

**Qué es.** El modo en que un boletín trata la fila «Otros países» al imprimir el total.

**En el proyecto.** No es uniforme. SE52/2019 la **excluye** del total impreso (con nota al pie: «437 = suma de 14 departamentos»). Los boletines de SE35 a SE52 de 2018 la **incluyen** en el total de confirmados (SE35/2018: suma de 14 = 143, otros = 1, total impreso = 144). El validador de cuadre prueba **ambas convenciones por boletín** y registra cuál cuadró; con una convención fija, seis boletines de 2018 se habrían marcado `revision_manual` por error del validador y no del dato. Ver [Fila «Otros países»](01-epidemiologia-y-vigilancia.md#fila-otros-países).

### Boletín de vacaciones

**Qué es.** Boletín de las semanas de descanso (Semana Santa, Fiestas Agostinas, Fin de Año), que no trae tabla departamental.

**En el proyecto.** Son tres por año y se detectan **por contenido** (ausencia de la ancla de tabla departamental y portada de vacación), nunca por el nombre del archivo: `SE142023-Semana-Santa.pdf` contiene un patrón `SE14` válido y aun así no trae tabla. Semana Santa es móvil (SE13 en 2018, SE16 en 2019, SE13 en 2021, SE15 en 2022, SE14 en 2023), así que ninguna regla por semana fija sirve. Se registra como `ausencia_esperada`.

### Boletín de semanas combinadas

**Qué es.** Un boletín que cubre dos semanas en un solo archivo.

**En el proyecto.** El caso confirmado es SE01+SE02 de 2018. No se reparte el conteo entre las dos semanas (sería fabricar dato) ni se ingiere como una sola (duplicaría la magnitud). Se detecta por el encabezado (rango de dos semanas o columna extra de acumulado-rango) y se registra como `ausencia_esperada`, con `semana_archivo` nula.

### Versión de boletín (`_v2`, `_v3`, `_v4`)

**Qué es.** Sufijo de un archivo republicado con correcciones.

**En el proyecto.** Es el mismo boletín, no otro distinto. La precedencia es explícita: dentro del mismo `(año, semana_archivo)` la **versión más alta** es la vigente, y se lee del sufijo del nombre, nunca de la fecha de modificación ni del orden en que el sistema de archivos entregue los nombres. `resolver_versiones()` implementa la regla y `boletines_procesados.version` la guarda (ADR 0004).

**Ojo.** En esta primera versión solo el archivo vigente de cada semana genera fila de bitácora; las versiones descartadas no la tienen todavía, aunque el ADR 0004 las contempla como auditoría.

### Boletín reimpreso

**Qué es.** Un boletín cuya tabla departamental es idéntica a la del corte anterior.

**En el proyecto.** En IRA y neumonías hay casos reales: la tabla de SE10/2018 repite los 14 valores de SE09 (San Salvador 119.670 en ambas) mientras la tabla de grupos de edad del mismo boletín ya trae datos nuevos. Ingerirla en su semana declarada fabricaría una semana con cero casos seguida de otra doble. `detectar_reimpresiones` la reclasifica a `revision_manual`. En neumonías ocurre con SE34/2019 (San Salvador 5.871 en SE33 y SE34).

### Texto extraíble y tabla-imagen

**Qué es.** Un PDF tiene texto extraíble si sus letras son caracteres; si la tabla es una imagen (raster), el texto no se puede extraer.

**En el proyecto.** Tres boletines de 2019 (`SE232019`, `SE322019`, `SE352019_v2`) dieron cero menciones de «dengue» en el texto extraíble y se sospechó tabla-imagen. Un OCR exhaustivo de las 35 páginas de cada uno **descartó** la hipótesis: la tabla departamental de dengue no existe ni como texto ni como imagen ([trampa 11](#trampas-de-las-fuentes-catálogo)). En IRA y neumonías sí hay títulos de tabla con cero filas extraíbles (por ejemplo SE01/2019), que se registran como **sospecha de imagen** y nunca se rellenan.

### OCR

**Qué es.** Reconocimiento óptico de caracteres: convertir una imagen de texto en texto.

**En el proyecto.** Se instaló `pytesseract` con `pdf2image` (idioma `spa`) con confirmación explícita de la coordinación, y se corrió una sola vez sobre esos tres boletines. Quedan instalados **pero sin uso** en el parser de producción: ningún boletín del corpus de 264 PDF necesitó OCR.

### Firma de bytes `%PDF`

**Qué es.** Los primeros bytes de un archivo PDF válido son `%PDF`.

**En el proyecto.** `minsal/common.py` valida cada descarga por esa firma (`PDF_SIGNATURE`) y no por el `Content-Type`, que el sitio devuelve siempre como `application/octet-stream` y no confirma nada.

### Ruta directa y ruta de respaldo

**Qué es.** Los dos mecanismos de descarga de los PDF de `salud.gob.sv`, un sitio WordPress con el plugin WordPress Download Manager.

**En el proyecto.** La **ruta directa** (preferida) extrae del HTML de la página índice de cada año las URLs reales `.../wp-content/uploads/download-manager-files/{nombre}.pdf`. La **ruta de respaldo** usa el enlace `data-downloadurl` de la página individual de cada boletín, con el patrón `?wpdmdl={ID}`. La directa se sostuvo en los cinco años. Entre peticiones hay una pausa de 1,5 s (`REQUEST_PAUSE_SECONDS`).

**Dónde.** `backend/ingestion/minsal/common.py` y `descargar_{año}.py`.

### Página índice oficial

**Qué es.** La página de cada año, `www.salud.gob.sv/boletines-epidemiologicos-{año}/`, que lista los boletines publicados.

**En el proyecto.** Es la entrada del descargador. No se diseñó un scraper sobre una plantilla fija de URL porque los nombres de archivo son irregulares. También es la referencia de la [cobertura real de publicación](#cobertura-real-de-publicación). Su URL se guarda en `boletines_procesados.url_origen` como metadato descriptivo.

### Nombres de archivo irregulares

**Qué es.** Variaciones del nombre de un boletín que impiden una plantilla única.

**En el proyecto.** Hay sufijos de versión (`_v2`), semanas combinadas (`SE01-02-2018`) y nombres libres en las semanas de vacaciones (`SE142023-Semana-Santa`). El patrón `SE(\d{1,2})(?:-(\d{1,2}))?` extrae la semana cuando existe; si el nombre no la trae, `semana_archivo` queda nula.

### Separador de miles inconsistente

**Qué es.** Los boletines no escriben los miles de forma uniforme.

**En el proyecto.** En IRA la coma es el separador en 2018–2022 y en SE01/2023 («33,360»), y el punto en SE52/2023 («1.574.872»); la tasa a veces sale sin separador («19460»). El parser aplica una heurística: un número con **grupos de tres dígitos** es un entero con miles. También hay totales malformados: «1363,652» (se perdió la primera coma) se lee 1.363.652 y se comprueba contra la suma de los departamentos.

### Errores de plantilla de MINSAL

**Qué es.** Rótulos del boletín que no corresponden a su contenido, por arrastre de plantillas.

**En el proyecto.** Casos documentados: la tabla nacional de IRA por grupo de edad de 2023 dice «Probable/Confirmado» pero su segunda columna es la **tasa por 100.000** (en SE01/2023 el «Total» es 485, la tasa nacional, imposible como suma de casos); las páginas de IRA de las primeras semanas de 2023 traen el encabezado «Grupo de edad» sobre filas que son departamentos; y el encabezado de años de la tabla de virus de SE01/2023 imprime 2021/2022 en un boletín de 2023. Ninguno se interpreta por su rótulo sino por su contenido.

### Narrativa rezagada

**Qué es.** El texto corrido del boletín repite datos de la semana anterior.

**En el proyecto.** En SE03/2018 la narrativa dice «SE 2-2018» y el título de la tabla dice «SE-03 de 2018». La semana de corte se lee **solo del título de la tabla** (o del pie de estratificación) y las filas se buscan solo dentro del bloque que empieza en ese título, porque la narrativa incluye números pegados a nombres de departamento («…Chalatenango 1,377, San Salvador 1,005…») que no son filas.

### Disposición lado a lado

**Qué es.** Formato en el que dos tablas comparten la página.

**En el proyecto.** En 2018–2022 la tabla departamental de IRA está al lado de la de grupos de edad y el texto extraído intercala filas de ambas; en 2023 la tabla departamental ocupa una página propia. Cambia la estrategia de extracción, no el dato.

## 4. Trampas de las fuentes

### Trampas de las fuentes (catálogo)

**Qué es.** Lista numerada de las 11 particularidades de los boletines, confirmadas por inspección manual de 10 o más boletines y por la corrida sobre los 264 PDF. En el código y en los ADR se cita por número («trampa 8»).

**En el proyecto.**

| N.º | Trampa | Cómo se trata |
|---|---|---|
| 1 | El **año impreso** dentro del PDF no es confiable (`SE012023.pdf` titula la tabla «El Salvador 2022») | El año sale siempre del nombre o la carpeta del archivo; cualquier discrepancia se marca para revisión |
| 2 | Las **celdas en blanco** significan cero | Se ingieren como `0`, nunca `NULL` ni fila omitida |
| 3 | «**Otros países**» es una fila real, y el total impreso a veces la incluye y a veces no | El validador prueba ambas [convenciones](#convención-de-otros-países) |
| 4 | Las **republicaciones** `_v2`…`_v4` son el mismo boletín | Gana la versión más alta ([Versión de boletín](#versión-de-boletín-_v2-_v3-_v4)) |
| 5 | El **nombre de archivo** no detecta boletines de vacaciones | Se detectan por contenido |
| 6 | En Familia A la **columna de tasa** no corresponde a «probable» sino a confirmados de otra semana | `población = confirmados(SE_Y) / tasa(SE_Y) × 100.000`; ver [Denominador](01-epidemiologia-y-vigilancia.md#denominador-poblacional-y-censo-2024) |
| 7 | Boletines que cubren **más de una semana** (SE01+SE02 de 2018) | No se reparte ni se ingiere como una semana: `ausencia_esperada` |
| 8 | Probable y Confirmado son **acumulados desde SE1** | [Desacumulación](#desacumulación) |
| 9 | **`SE182023.pdf` sin tabla de dengue** sin ser vacaciones; el mismo patrón en `SE282019_v2` y `SE292019_v2` | El boletín sí trae tablas departamentales de otras enfermedades; se reclasifica a `ausencia_esperada` |
| 10 | **SE01, SE02 y SE03 de 2023** declaran el mismo encabezado `Probable SE1` / `Confirmado SE1` (arrastre de plantilla) | Guarda explícita de colisión de clave antes de escribir |
| 11 | Tres boletines de 2019 (`SE232019`, `SE322019`, `SE352019_v2`) **sin texto de «dengue»**; se sospechó tabla-imagen | El OCR exhaustivo la descartó: `ausencia_esperada` |

**Ojo.** La trampa 6 lleva una salvedad abierta: no se verificó si la tasa es semanal o acumulada al año, y conviene despejar con las filas de mayor conteo confirmado (con conteos chicos el error relativo se dispara) y comprobar que el denominador sea constante dentro de cada departamento y año. La trampa 10 se resolvió con una guarda, no con igualdad estricta entre encabezado y nombre de archivo, porque `SE132023.pdf` declara legítimamente SE14/SE13 (+1 sobre el nombre).

### Desfase de una semana en los huecos de vacaciones

**Qué es.** Observación pendiente de verificar: los huecos registrados no coinciden con las semanas de feriado calculadas, sino que están desplazados en uno (Semana Santa 2018 en SE13, boletín faltante SE51/SE12).

**En el proyecto.** La explicación probable es que el boletín de la semana N se publica durante la N+1. Mientras no se lea el encabezado de tres PDF de 2021–2023, la referencia técnica de fuentes indica **no precalcular ninguna tabla de huecos por semana**.

## 5. De la fuente a la tabla: la ingesta

### Ingesta

**Qué es.** El proceso que lleva un dato de su fuente a la base.

**En el proyecto.** Cada fuente pasa por tres etapas con scripts distintos: obtener el archivo crudo (`descargar_*.py`, captura HAR), extraerlo y validarlo (una **corrida exploratoria** o el **parser**), y cargarlo (`cargar_*.py`). El principio rector es «nunca fabricar»: un dato que no se puede leer se registra como ausente, no se rellena.

**Dónde.** `backend/ingestion/`.

### Capa cruda y capa intermedia

**Qué es.** `data/raw/` guarda lo descargado tal cual; `data/interim/` guarda lo extraído antes de normalizar.

**En el proyecto.** El parser vuelca la tabla cruda de cada boletín (incluida la columna de tasa de Familia A, aunque no se use aguas abajo) en `data/interim/`, para que los 264 PDF se lean una sola vez. **Ninguna de las dos carpetas se versiona**: los PDF y los derivados de la ingesta son datos, no código. Las excepciones son deliberadas, están enumeradas en `.gitignore` y no deben «corregirse»:

- `backend/ingestion/geo/slv-adm1-source.geojson`.
- `db/seed/seed_datos_reales.sql` ([ADR 0010](../adr/0010-versionar-volcado-de-datos-reales.md)).
- Los artefactos precomputados del nowcast en `backend/api/datos/` ([ADR 0020](../adr/0020-nowcast-corto-plazo.md)).
- `dataset_modelado.csv`, `clasificador_riesgo_nacional_v1.joblib` y `metricas_modelo.json`, evidencia del [clasificador retirado](04-estadistica-y-modelado.md#clasificador-de-riesgo-retirado): código muerto documentado, no algo a extender.

### Corrida exploratoria, parser de producción y cargador

**Qué es.** Tres tipos de script con responsabilidades separadas.

**En el proyecto.** Una **corrida exploratoria** (`corrida_distribucion.py`, `corrida_ira.py`, `corrida_respiratorios.py`) extrae, desacumula y valida sobre los 264 PDF **sin escribir en PostgreSQL** y vuelca a `data/interim/`. El **parser de producción** (`minsal/parser.py`) reutiliza esa extracción y desacumulación sin reescribirlas y sí escribe la bitácora y los casos de dengue. Un **cargador** (`cargar_ira.py`, `cargar_neumonias.py`, `cargar_vigilancia_respiratoria.py`, `cargar_opendengue.py`, `cargar_clima.py`, `cargar_oni.py`, `cargar_minsal_tablero.py`) lee un resultado ya validado e inserta filas.

**Ojo.** Que una corrida exploratoria no escriba en la base es una garantía de diseño: por eso IRA y neumonías necesitan un segundo paso (el cargador lee el CSV desacumulado de la corrida).

### Desacumulación

**Qué es.** Convertir una serie acumulada desde SE1 en una serie de conteos semanales, restando cortes consecutivos.

**En el proyecto.** Para cada `(año, departamento)` el conteo de la semana N es `acumulado(N) − acumulado(N−1)`. Las reglas son cuatro y no se negocian:

1. Un **hueco** entre cortes (falta un boletín) deja el intervalo completo sin dato semanal; **nunca se reparte** el acumulado.
2. Una diferencia **negativa** es una corrección retroactiva de MINSAL: se registra aparte y se excluye de la serie, **nunca se lleva a cero**.
3. El **primer corte** del año, si no es SE1, es un acumulado de varias semanas y se marca con nota; no se divide.
4. La versión más alta de cada boletín es la vigente.

**Dónde.** `paso2_desacumular` en `backend/ingestion/corrida_distribucion.py`; `desacumular` en `corrida_ira.py` y `desacumular_neumonias` en `corrida_respiratorios.py`.

**Ojo.** Fue validada por diferencias entre boletines consecutivos sobre los 264 PDF y verificada 4 de 4 contra casos inspeccionados a mano ([Verificación 4/4](#verificación-44)).

### Hueco entre cortes

**Qué es.** Semanas sin boletín (o sin tabla) entre dos cortes disponibles.

**En el proyecto.** El intervalo se registra como `PuntoSemanal` con valor `None` y una nota («hueco de N semanas entre cortes SEa y SEb»). Se omite al cargar: en la base **no hay fila**, y un hueco no es un cero ([Hueco (sin dato) frente a cero](01-epidemiologia-y-vigilancia.md#hueco-sin-dato-frente-a-cero)).

### Corrección retroactiva

**Qué es.** Un acumulado que baja de un boletín al siguiente porque MINSAL corrigió cifras ya publicadas.

**En el proyecto.** Se detectan como diferencias negativas. En el corpus de dengue hay **19**, todas de magnitud −1 o −2; el ejemplo verificado es Chalatenango, probable acumulado 62→61 entre los cortes SE33 y SE34 de 2018 (`SE362018`). Se registran aparte (`correcciones_negativas.csv`) y se excluyen de la serie.

### Primer corte del año

**Qué es.** El primer boletín disponible de cada año en una serie acumulada.

**En el proyecto.** Si es SE1, su acumulado es el conteo de esa semana. Si no lo es, el valor abarca varias semanas y queda marcado con nota («primer corte del año en SEn: acumulado SE1–SEn»). En IRA y neumonías esas filas **no se cargan**, porque inyectarían una observación varias veces mayor que la real.

### Idempotencia y upsert

**Qué es.** Una carga es idempotente si repetirla no duplica ni cambia el resultado.

**En el proyecto.** Los cargadores usan `INSERT … ON CONFLICT … DO UPDATE` sobre la llave única de cada tabla. La bitácora usa `nombre_archivo` como llave natural (ADR 0004), así que reprocesar un boletín actualiza su fila en vez de duplicarla. `execute_values` se llama con `page_size=len(valores)` porque, si no, `cur.rowcount` solo refleja la última página interna (un bug detectado con 365 filas reales, de las que se reportaron 65).

### Bitácora de boletines (`boletines_procesados`)

**Qué es.** Registro de auditoría con una fila por boletín procesado.

**En el proyecto.** Guarda `nombre_archivo` (llave natural única), `version`, `anio`, `semana_archivo` (nula si no hay una semana única), `url_origen`, `familia_esquema`, las sumas departamentales y los totales impresos, `validacion_cuadra`, `estado` y `notas`. Sirve para medir la calidad de la ingesta y para saber qué filas produjo cada boletín. Ver [`boletines_procesados`](07-base-de-datos-y-migraciones.md#boletines_procesados).

### Estados de la bitácora

**Qué es.** Los seis valores permitidos de `boletines_procesados.estado`.

**En el proyecto.**

| Estado | Significado | En la métrica de calidad |
|---|---|---|
| `pendiente` | Valor por defecto al registrar el boletín, todavía sin procesar | — |
| `ok` | Tabla extraída y suma departamental cuadrada | Éxito |
| `revision_manual` | La tabla existe pero la suma no cuadra en ninguna convención, o hay una anomalía que alguien debe mirar | Requiere intervención humana |
| `error` | El parser falló de forma inesperada sobre un boletín que debería traer tabla | Fallo del parser |
| `ausencia_esperada` | Se abrió sin error pero no trae tabla departamental de dengue esa semana | No cuenta como fallo |
| `sin_texto_extraible` | Sin ninguna mención de «dengue» en el texto extraíble | Se cuenta aparte, como hueco de cobertura conocido |

**Ojo.** Los estados exploratorios `ausencia_esperada_vacacion` y `ausencia_esperada_multisemana` colapsan a `ausencia_esperada` en producción (la distinción queda en `notas`); `sin_tabla_no_vacacional` (trampa 9) mapea por defecto a `revision_manual`, pero `REVISIONES_MANUALES` la reclasifica. `error_extraccion` mapea a `error`. La tabla de mapeo es `MAPA_ESTADO` en `parser.py`. Tras la revisión de la tarjeta 26 ningún boletín del corpus de dengue quedó en `revision_manual` ni en `sin_texto_extraible`.

### `ausencia_esperada`

**Qué es.** Estado del boletín que se abrió sin error pero no trae tabla departamental de dengue esa semana.

**En el proyecto.** Se creó (ADR 0004) para vacaciones y semanas combinadas, y su definición operativa se extendió a «la tabla departamental de dengue específicamente no se publicó esa semana», sin tocar el `CHECK`. No infla la tasa de fallos ni sugiere que alguien deba intervenir.

### `sin_texto_extraible`

**Qué es.** Sexto estado de la bitácora, agregado por el [ADR 0007](../adr/0007-bitacora-boletines-estado-sin-texto-extraible.md) (migración `0005`).

**En el proyecto.** Describe un boletín abierto sin error en cuyo texto extraíble no aparece «dengue», indicio de tabla-imagen. Se contaba aparte, como hueco de cobertura conocido, pendiente de OCR. Tras el OCR de la tarjeta 26 los tres boletines afectados se reclasificaron a `ausencia_esperada`.

### `revision_manual`

**Qué es.** Estado de un boletín que un humano debe mirar.

**En el proyecto.** Se usa cuando la tabla existe y se extrajo pero la suma departamental no cuadra contra el total impreso en ninguna convención, o cuando aparece una anomalía real (por ejemplo una reimpresión). Nunca se ingiere en silencio.

### Revisión manual documentada (`REVISIONES_MANUALES`)

**Qué es.** Diccionario de `parser.py` con los boletines cuya clasificación automática se corrigió tras revisarlos a mano.

**En el proyecto.** Tiene siete entradas, cada una con la evidencia que la respalda: `SE232019`, `SE322019` y `SE352019_v2` (OCR exhaustivo), `SE182023`, `SE282019_v2` y `SE292019_v2` (el boletín sí trae tablas de otras enfermedades pero dengue no publicó desglose departamental) y `SE302019_v2` (discrepancia real y mínima de MINSAL). Se aplica antes de desacumular, para que un `ok` sí alimente la serie.

**Ojo.** No es una lista para silenciar advertencias: cada entrada documenta la evidencia puntual. `SE302019_v2` se acepta como `ok` con `validacion_cuadra = false`: probable cuadra exacto (386) y confirmado difiere en un caso (suma 88, impreso 89), y no se descartan 14 filas reales por una diferencia de 1 en un total que no es el dato que se ingiere.

### Cuadre (`validacion_cuadra`)

**Qué es.** Columna booleana de `boletines_procesados` que indica si la suma departamental coincide con el total nacional impreso.

**En el proyecto.** Es verdadera si cuadra la tabla o el resumen nacional; falsa si no cuadra ninguno; nula si no se pudo evaluar. Fuera del caso `SE302019_v2`, un `false` lleva el boletín a `revision_manual`. Dos boletines de 2019 (`SE102019_v3`, `SE422019_v2`) se marcaron mal por un bug del parser (la fila «Otros países» a veces trae una tercera columna de tasa, «0 0 0,0», que se colaba en el total impreso) y quedaron recuperados como `ok`.

### Trazabilidad (`boletin_id`)

**Qué es.** Columna de `casos_epidemiologicos` que apunta al boletín que produjo cada fila.

**En el proyecto.** Se puebla solo para `fuente_id = minsal_pdf` (nula para OpenDengue y para los cargadores de IRA y neumonías). Con ella, `SELECT * FROM casos_epidemiologicos WHERE boletin_id = ?` responde qué filas produjo un boletín mal parseado. En la primera carga completa quedó trazada al 100 % (5.805 filas). La procedencia sigue la regla «el último gana» de `_serie_por_depto_anio`, la misma que usa la desacumulación.

### Fixture de texto extraído

**Qué es.** Archivo de prueba con el texto que `pdfplumber.extract_text()` saca de la página de un boletín.

**En el proyecto.** Regla del proyecto: **guardar solo el texto extraído, nunca los PDF**. Los `.txt` están en `backend/ingestion/tests/fixtures/minsal/` (extraídos el 2026-08-21 y el 2026-08-28), sin ningún valor editado a mano, y cada uno documenta en su README por qué está ahí (celda en blanco, «Otros países» incluido o excluido, corrección retroactiva, año engañoso, semanas combinadas…). Hay fixtures de dengue, IRA, neumonías y vigilancia de virus; las páginas del texto completo se separan con `\f` (salto de página).

### Caso de referencia verificado a mano

**Qué es.** Boletín cuyos totales se comprobaron manualmente contra el PDF y sirve de ancla de pruebas.

**En el proyecto.** `SE232018` (suma de 14 = 47 probables y 21 confirmados, Familia A), `SE522019_v2` (437+2 y 174+2, con «Otros países» excluido y nota al pie) y `SE522023` (17 y 54, Familia B). `SE232019` se validó por el cruce aritmético de la trampa 8, no por lectura directa de tabla.

### Verificación 4/4

**Qué es.** Resultado de la corrida exploratoria contra los cuatro casos conocidos inspeccionados a mano.

**En el proyecto.** La corrida reproduce los cuatro casos de referencia sin diferencias, y a partir de eso se promovió a producción. No debe leerse como «4 de 4 boletines del corpus» sino como cuatro comprobaciones puntuales.

### Dry-run

**Qué es.** Ejecución de un script que hace todo el cálculo pero no escribe.

**En el proyecto.** `--dry-run` en `parser.py`, `cargar_ira.py`, `cargar_minsal_tablero.py` y `cargar_vigilancia_respiratoria.py`: corre extracción y desacumulación, imprime el resumen y termina sin tocar la base.

### Sin relleno (nunca fabricar)

**Qué es.** Principio no negociable: no se inventa, interpola ni reparte un dato.

**En el proyecto.** Se aplica en todas las etapas: semanas ausentes no se insertan (hueco, no cero); las correcciones negativas no se llevan a cero; el primer corte tardío no se divide; la semana 53 de 2025 del tablero queda sin fila; la precipitación con cero falso se descarta; el rezago ERA5 de unos 5 días se declara y no se rellena con pronóstico. Ver [Solo datos agregados y sin datos personales](10-proceso-gobernanza-y-documentacion.md#solo-datos-agregados-y-sin-datos-personales) para el otro principio de datos.

### Guarda de colisión de clave

**Qué es.** Comprobación antes de escribir de que dos boletines no reclaman la misma clave `(año, semana_epi)`.

**En el proyecto.** Nace de la trampa 10: tres boletines de 2023 declaran el mismo corte. No es una igualdad estricta entre encabezado y nombre de archivo, porque hay casos legítimos con desfase. La regla ya cerrada sigue en pie: la semana se lee del encabezado, no del nombre.

## 6. La serie del tablero y su empalme

### Sospechoso (serie nacional del tablero)

**Qué es.** Número de casos sospechosos de dengue por semana que publica el tablero de MINSAL.

**En el proyecto.** Se guarda con `clasificacion = 'sospechoso'`, con el nombre que usa la fuente («Casos Sospechosos de Dengue»). Tiene la **misma definición** que el `total` de OpenDengue: el total de OpenDengue de 2019 (27.470) coincide con los sospechosos nacionales que publicó MINSAL ese año. Ver [`sospechoso`](01-epidemiologia-y-vigilancia.md#sospechoso).

### Serie suavizada del tablero

**Qué es.** La forma «lisa» de la serie del tablero: cada semana se parece mucho a sus vecinas.

**En el proyecto.** Medida como la desviación de cada semana respecto a sus vecinas, en unidades de ruido de Poisson, da 0,28 en 2025 y 0,70 en 2026, frente a entre 1,2 y 8,3 de OpenDengue de 2014 a 2023. La enmienda del ADR 0021 concluye que la forma es la de un **promedio hacia atrás de 6 o 7 semanas**, que viene de la tabla de MINSAL (la consulta solo suma `total_casos` de `diagnosticos_acumulados`); aplicado a los años crudos de OpenDengue deja la misma huella, y la caída de Semana Santa de 2026 aparece en la semana 13 sin adelantarse. El núcleo exacto no se puede recuperar. Pasa lo mismo con IRA, neumonías y OpenDengue 2024.

**Ojo.** La definición es la misma, pero la **forma** no: no se empalma la serie del tablero con OpenDengue como si fuera idéntica, y usarla en el nowcast exige validarla aparte ([Nowcast](04-estadistica-y-modelado.md#nowcast-de-dengue)).

### Serie mixta (empalme)

**Qué es.** La serie nacional que une OpenDengue y el tablero.

**En el proyecto.** Es OpenDengue hasta 2024-S52 y el tablero desde 2025-S1, **sin semanas compartidas**. `GET /api/casos-nacional` devuelve el total de OpenDengue y, en las semanas posteriores a su última fila, los sospechosos del tablero, con un campo `fuente` en cada fila para que la curva marque el tramo. La antigüedad de M4 suma la serie `dengue_tablero_nacional`. Es una excepción acotada a la regla de separar fuentes: las consultas departamentales siguen filtrando por `minsal_pdf`.

### Revisión de MINSAL (la captura más reciente gana)

**Qué es.** MINSAL puede modificar semanas que ya había publicado.

**En el proyecto.** Si dos capturas difieren, `cargar_minsal_tablero.py` **usa una cifra por semana, la de la captura más reciente**, e informa las diferencias como revisión de MINSAL. Las capturas viejas se conservan.

### Semana 53 sin fila

**Qué es.** La semana 53 de 2025 (28 de diciembre al 3 de enero) no aparece publicada en el tablero.

**En el proyecto.** Queda sin fila: no se rellena ni se estima. Ver [Semana 53](01-epidemiologia-y-vigilancia.md#semana-53).

### Series nacionales de IRA y neumonías del tablero

**Qué es.** Series propias, desde 2025-S1, que no se empalman con la suma de los departamentos de los boletines.

**En el proyecto.** `GET /api/ira/nacional` y `GET /api/neumonias/nacional` devuelven solo las filas del tablero; la antigüedad de M4 suma `ira_tablero_nacional` y `neumonias_tablero_nacional`. No se empalman porque muchas semanas de 2018–2023 no traen los 14 departamentos y, en neumonías, esa suma promedia entre 500 y 780 por semana según el año, frente a 130–430 en el tablero, sin que se haya comprobado que sea la misma definición. El observatorio respiratorio las muestra en una curva aparte, con una línea por año.

## 7. Datos respiratorios en la ingesta

### Tabla departamental de IRA

**Qué es.** Tabla de los boletines con `Departamento | Total | Tasa x 100 mil`.

**En el proyecto.** Es **un solo conteo clínico** por departamento, sin desglose probable y confirmado (verificado en todo el corpus), acumulado desde SE1 y desacumulado por diferencia de cortes. Se carga con `clasificacion = 'notificado'` ([ADR 0011](../adr/0011-clasificacion-ira-departamental.md)): 2.742 filas de 2018–2023, sin 2020, en 14 departamentos. `cargar_ira.py` inserta solo las **filas seguras** (sin nota) y verificó que las 2.742 tienen un tramo de una semana en las 70 combinaciones año-departamento. `boletin_id` queda nulo porque la bitácora de IRA vive en `data/interim/`.

### Tabla departamental de neumonías

**Qué es.** Tabla `Departamento | Total | Tasa x 100 mil`, acumulada desde SE1 y con un solo conteo.

**En el proyecto.** Reutiliza `casos_epidemiologicos` con `tipo_evento = 'neumonia'` y `clasificacion = 'notificado'`: 2.749 filas en la foto del seed. Comparte la familia de trampas de IRA (imagen en 2019 temprana, vacaciones, la reimpresión SE34/2019 y discrepancias de ±1 en 2023, por ejemplo celdas que suman 22.336 con total impreso 22.337).

### Tabla de vigilancia laboratorial de virus

**Qué es.** Tabla **nacional** de los boletines con muestras, detecciones por virus y positividad.

**En el proyecto.** No es un conteo clínico y no tiene desglose departamental, así que no entra a `casos_epidemiologicos`: se persiste en `vigilancia_virus_respiratorios`, una tabla EAV (una fila por virus y métrica) con `unidad` `conteo` o `porcentaje` ([ADR 0012](../adr/0012-persistencia-vigilancia-virus-respiratorios.md)). 3.028 filas en la foto del seed. COVID-19 aparece como fila solo en 2023, con el rótulo `COVID 19` y no «SARS-CoV-2», y en SE52/2023 sin valores extraíbles: no se fabrica.

### Inventario de vigilancia de virus

**Qué es.** El archivo intermedio `inventario_vigilancia_virus.csv` que produce la corrida exploratoria de virus.

**En el proyecto.** `cargar_vigilancia_respiratoria.py` lo lee, se queda con las filas en estado `ok` y traduce cada métrica del boletín a un `(virus, metrica, unidad)` mediante `MAPA_METRICA`. Los conteos usan la columna de semana cuando la tabla la trae y, si no, desacumulan el acumulado del año (con las mismas reglas que IRA).

### Positividad publicada, no recalculada

**Qué es.** Porcentaje de muestras positivas.

**En el proyecto.** Se guarda **tal como la publica la fuente**, sin recalcularla en silencio. Un porcentaje nunca se guarda como `conteo`. Ver [Positividad](01-epidemiologia-y-vigilancia.md#positividad).

### Pie de estratificación

**Qué es.** Nota al pie de algunas páginas de IRA y neumonías que trae la semana.

**En el proyecto.** En las primeras semanas de 2023 la tabla departamental está en página propia sin título y la semana de corte sale del pie de estratificación (por ejemplo «SE 1»).

### Acumulado con rango en el título

**Qué es.** Rótulo de tabla con un rango de semanas.

**En el proyecto.** En SE52/2021 el título dice «SE01-52 2021»: el corte es el **segundo** número. En IRA la fila «Otros países» existe en 2021–2023 pero, en lo observado, vacía; si trajera valores, la reconciliación probaría ambas convenciones como en dengue.
