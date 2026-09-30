# Rama 7 · Base de datos y migraciones

Vocabulario del esquema PostgreSQL de EPI-Aetheris: las tablas y sus columnas, los valores controlados (`clasificacion`, `estado`), cómo se versiona el esquema (migraciones, runner, `schema_migrations`) y cómo se reproduce la base con el volcado de datos reales (seed).

**Para quién es.** Para quien lee `db/migrations/`, escribe una consulta SQL contra la base o levanta el proyecto desde un clon limpio y necesita saber qué es cada tabla, qué significa cada valor y por qué las migraciones se escriben como se escriben.

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris, con los nombres exactos), **Dónde** (archivo, ADR o migración) y **Ojo** (errores frecuentes). Las expansiones de siglas que el repositorio no da se marcan como «de uso general».

**Ramas vecinas.** Qué significa cada fuente y cada serie está en [`02-fuentes-de-datos-e-ingesta.md`](02-fuentes-de-datos-e-ingesta.md); cómo la API consulta estas tablas, en [`06-backend-y-api.md`](06-backend-y-api.md); el despliegue en Render y `docker-compose`, en [`08-infraestructura-despliegue-y-repositorio.md`](08-infraestructura-despliegue-y-repositorio.md); la regla «ADR antes de migración», en [`10-proceso-gobernanza-y-documentacion.md`](10-proceso-gobernanza-y-documentacion.md).

<!-- INDICE:INICIO -->

## Índice alfabético (43 entradas)

- **A** — [ADR antes de migración](#adr-antes-de-migración) · [alertas](#alertas)
- **B** — [boletines_procesados](#boletines_procesados) · [--bootstrap](#--bootstrap)
- **C** — [Carga en una sola invocación de psql](#carga-en-una-sola-invocación-de-psql) · [casos_epidemiologicos](#casos_epidemiologicos) · [clasificacion](#clasificacion) · [COMMENT ON](#comment-on) · [conteo](#conteo) · [Costo de reingesta](#costo-de-reingesta)
- **D** — [--disable-triggers y superusuario](#--disable-triggers-y-superusuario) · [Diseño agnóstico a evento y región](#diseño-agnóstico-a-evento-y-región) · [docker-entrypoint-initdb.d](#docker-entrypoint-initdbd)
- **E** — [EAV (entidad–atributo–valor)](#eav-entidadatributovalor)
- **F** — [familia_esquema](#familia_esquema) · [fecha_ingesta](#fecha_ingesta) · [fuentes_datos](#fuentes_datos)
- **G** — [generar_seed.sh](#generar_seedsh)
- **L** — [Llave primaria, foránea, UNIQUE y CHECK](#llave-primaria-foránea-unique-y-check)
- **M** — [Migración](#migración) · [Migración de solo datos](#migración-de-solo-datos)
- **N** — [nivel_admin](#nivel_admin)
- **P** — [PostgreSQL 15](#postgresql-15) · [preDeployCommand](#predeploycommand) · [psql y pg_dump](#psql-y-pg_dump) · [psycopg2.extras.execute_values](#psycopg2extrasexecute_values)
- **R** — [Recrear un CHECK](#recrear-un-check) · [regiones](#regiones) · [Runner de migraciones (aplicar_migraciones.py)](#runner-de-migraciones-aplicar_migracionespy)
- **S** — [schema_migrations](#schema_migrations) · [semanas_epidemiologicas](#semanas_epidemiologicas) · [SERIAL y BIGSERIAL](#serial-y-bigserial) · [setval](#setval) · [Sin reversión (down)](#sin-reversión-down) · [SQLSTATE 42P01 (UndefinedTable)](#sqlstate-42p01-undefinedtable)
- **T** — [Tabla catálogo y tabla de hechos](#tabla-catálogo-y-tabla-de-hechos) · [tipos_evento](#tipos_evento) · [to_regclass](#to_regclass) · [Transacción (BEGIN … COMMIT)](#transacción-begin--commit)
- **U** — [Upsert (ON CONFLICT … DO UPDATE)](#upsert-on-conflict--do-update)
- **V** — [variables_ambientales](#variables_ambientales) · [vigilancia_virus_respiratorios](#vigilancia_virus_respiratorios) · [Volcado versionado (seed)](#volcado-versionado-seed)

<!-- INDICE:FIN -->

## 1. Ideas generales del esquema

### PostgreSQL 15

**Qué es.** Sistema de bases de datos relacional de código abierto.

**En el proyecto.** Versión 15: la imagen `postgres:15-alpine` en `docker-compose` y `postgresMajorVersion: "15"` en Render. El acceso desde Python es con `psycopg2` y SQL directo, sin ORM.

### Diseño agnóstico a evento y región

**Qué es.** Un esquema que no fija columnas por enfermedad ni por país.

**En el proyecto.** Es el aporte de ingeniería declarado: **catálogos, no columnas fijas**. La enfermedad es una fila de `tipos_evento`, el lugar una fila de `regiones`, el origen una fila de `fuentes_datos`. Ampliar a IRA y neumonías no exigió columnas nuevas, solo filas de catálogo y un valor nuevo de `clasificacion`.

### Tabla catálogo y tabla de hechos

**Qué es.** Un catálogo lista entidades estables (con pocas filas); una tabla de hechos guarda las observaciones (muchas filas).

**En el proyecto.** **Catálogos:** `regiones`, `tipos_evento`, `fuentes_datos` y `semanas_epidemiologicas`. **Hechos:** `casos_epidemiologicos`, `variables_ambientales` y `vigilancia_virus_respiratorios`. **Auditoría:** `boletines_procesados`. **Contenido humano:** `alertas`. **Infraestructura:** `schema_migrations`.

### EAV (entidad–atributo–valor)

**Qué es.** Modelo en el que cada observación es una fila `(entidad, atributo, valor)` en lugar de una columna por atributo (de uso general).

**En el proyecto.** `variables_ambientales` guarda `(región, periodo, variable, valor)` y `vigilancia_virus_respiratorios` guarda `(virus × métrica)`. Así un predictor o un virus nuevo no exige migración. El nombre «ambientales» y no «climáticas» deja espacio a predictores no climáticos.

### Llave primaria, foránea, `UNIQUE` y `CHECK`

**Qué es.** Restricciones que garantizan la integridad: la primaria identifica una fila; la foránea referencia otra tabla; `UNIQUE` prohíbe duplicados; `CHECK` limita los valores (de uso general).

**En el proyecto.** Casi cada tabla de hechos tiene una restricción `UNIQUE` sobre su llave natural, que es lo que hace posible el upsert idempotente (por ejemplo `UNIQUE (region_id, tipo_evento_id, anio, semana_epi, clasificacion, fuente_id)`). Los `CHECK` fijan los valores controlados de `clasificacion`, `estado`, `familia_esquema`, `metrica`, `unidad`, `tipo`, `nivel`, `etiqueta` y `departamentos`.

### `SERIAL` y `BIGSERIAL`

**Qué es.** Tipos de columna con un contador automático (entero de 4 u 8 bytes).

**En el proyecto.** Catálogos y bitácora usan `SERIAL`; las tablas de hechos grandes y `alertas`, `BIGSERIAL`.

### `COMMENT ON`

**Qué es.** Sentencia que adjunta un comentario a una tabla o columna dentro de la propia base.

**En el proyecto.** Es la forma de trasladar una precisión al propio esquema: por ejemplo `regiones.elevacion_m` lleva un comentario que aclara que **no** es una medición topográfica, y `clasificacion` explica qué significa cada valor.

### Transacción (`BEGIN … COMMIT`)

**Qué es.** Un bloque de sentencias que se aplica entero o no se aplica.

**En el proyecto.** Cada archivo de migración va envuelto en `BEGIN;` y `COMMIT;`, y el runner aplica cada uno en **su propia transacción**: si falla, no queda a medias.

## 2. Tablas

### `regiones`

**Qué es.** Catálogo jerárquico de lugares: país, departamento y (reservado) municipio.

**En el proyecto.** Columnas: `id`, `codigo` (único, hasta 10 caracteres, p. ej. `SV`, `SV-AH`), `nombre`, `nivel_admin`, `pais` (`SV`), `region_padre_id` (autorreferencia: el departamento apunta al país) y `activo`. Tiene **15 filas**: `SV` (nivel 0) y los 14 departamentos (nivel 1). El nivel 2 (municipio) está **reservado y sin filas**. Las migraciones posteriores añadieron `centroide_lat`, `centroide_lon` y `elevacion_m` (migración `0002`).

**Ojo.** `regiones.codigo` es la llave que une con el mapa, pero el GeoJSON de origen traía `shapeISO` vacío: ver [Unión por nombre normalizado](02-fuentes-de-datos-e-ingesta.md#unión-por-nombre-normalizado).

### `tipos_evento`

**Qué es.** Catálogo de las enfermedades o eventos que se vigilan.

**En el proyecto.** Tres filas: `dengue` (migración `0001`), `ira` (`0007`, «Infección Respiratoria Aguda») y `neumonia` (`0008`, «Neumonías»). Una fila nueva es dato y no esquema, así que no requiere ADR propio.

### `fuentes_datos`

**Qué es.** Catálogo de fuentes con `codigo`, `nombre`, `url_referencia` y `notas`.

**En el proyecto.** Seis filas: `opendengue_v1_3`, `minsal_pdf`, `open_meteo_era5_land`, `open_meteo_era5`, `noaa_oni` y `minsal_tablero`. La tabla completa con la migración de cada una está en [Fuente de datos](02-fuentes-de-datos-e-ingesta.md#fuente-de-datos-fuentes_datos). Como es un catálogo abierto, agregar una fila no toca columnas ni restricciones.

### `semanas_epidemiologicas`

**Qué es.** Calendario de referencia de semanas epidemiológicas, compartido entre casos y clima.

**En el proyecto.** Llave primaria `(anio, semana_epi)` con `semana_epi` entre 1 y 53, más `fecha_inicio` y `fecha_fin`. Sigue el calendario **PAHO/CDC (MMWR)**, no ISO 8601, y **no se puebla con el DDL** sino con `poblar_semanas_epidemiologicas.py` (librería `epiweeks`). Las dos tablas de hechos tienen una clave foránea compuesta `(anio, semana_epi)` hacia ella, así que **debe poblarse antes de cualquier ingesta**. Sirve para agregar el clima diario a la misma unidad temporal que los casos.

**Ojo.** Si falta un año, sus fechas quedan sin semana resuelta y el cargador de clima las avisa y las descarta; por eso el default de `--anio-fin` es el año en curso más uno (poblar un año de más es inocuo: `ON CONFLICT DO NOTHING`). El volcado tiene 679 filas de esta tabla en su primera versión.

### `casos_epidemiologicos`

**Qué es.** Tabla de hechos con la **variable objetivo**: casos por región, semana, tipo de evento y clasificación.

**En el proyecto.** Columnas: `id`, `region_id`, `tipo_evento_id`, `anio`, `semana_epi`, [`clasificacion`](#clasificacion), `conteo` (entero no negativo), `fuente_id`, `boletin_id` (nula si no viene de un boletín) y `fecha_ingesta`. La restricción `UNIQUE (region_id, tipo_evento_id, anio, semana_epi, clasificacion, fuente_id)` es la llave de los upserts. `semana_epi` es la semana **real** a la que corresponde el dato, no la del nombre del archivo.

**Ojo.** Sumar `conteo` agrupando solo por `(región, año, semana)` **sin filtrar por `clasificacion`** mezcla definiciones de caso distintas: siempre se filtra por la serie que se necesita.

### `variables_ambientales`

**Qué es.** Tabla de hechos de los predictores ambientales por región y semana.

**En el proyecto.** Columnas: `region_id`, `anio`, `semana_epi`, `variable` (texto libre, sin `CHECK`), `valor` (`NUMERIC(10,3)`), `fuente_id` y `fecha_ingesta`; llave única `(region_id, anio, semana_epi, variable, fuente_id)`. Las variables vigentes son `temp_max`, `temp_min`, `temp_media`, `precipitation_sum`, `precipitation_hours`, `humedad_relativa_media`, `punto_rocio` y `oni_anom` ([Variable ambiental](03-clima-y-ambiente.md#variable-ambiental)).

**Ojo.** Como `variable` no tiene `CHECK`, **un error de escritura crea una segunda serie en silencio**. El comentario original mencionaba `et0_fao`, pero esa variable quedó fuera de alcance.

### `boletines_procesados`

**Qué es.** Bitácora de ingesta: una fila por boletín MINSAL procesado.

**En el proyecto.** Columnas: `id`, `nombre_archivo` (**llave natural única**, migración `0002`), `version`, `anio`, `semana_archivo` (nula si no hay una semana única), `url_origen`, `familia_esquema` (`A` o `B`), `suma_departamental_probable`, `suma_departamental_confirmado`, `total_nacional_publicado_probable`, `total_nacional_publicado_confirmado`, `validacion_cuadra`, `estado`, `fecha_procesado` y `notas`. Los seis valores de `estado` y su significado están en [Estados de la bitácora](02-fuentes-de-datos-e-ingesta.md#estados-de-la-bitácora). Tiene 264 filas en la primera versión del volcado.

**Ojo.** `fecha_procesado` es el timestamp de **nuestra** corrida del parser, no la fecha de publicación del boletín: por eso M4 no puede medir latencia real de reporte.

### `vigilancia_virus_respiratorios`

**Qué es.** Tabla de hechos de la vigilancia laboratorial de virus respiratorios.

**En el proyecto.** Columnas: `region_id` (siempre `SV`), `anio`, `semana_epi`, `virus`, `metrica`, `valor` (`NUMERIC(12,4)`), `unidad`, `fuente_id`, `boletin_id` (nula en la primera carga) y `fecha_ingesta`; llave única `(region_id, anio, semana_epi, virus, metrica, fuente_id)`. `virus` es texto controlado por el cargador (`todos`, `influenza`, `influenza_a_h1n1`, `influenza_a_h3n2`, `influenza_a_no_subtipificado`, `influenza_b`, `vsr`, `parainfluenza`, `adenovirus`, `covid_19`, `otros`) y **no tiene `CHECK`**, para admitir un virus nuevo sin migración. `metrica` está restringida a `muestras_analizadas`, `muestras_positivas`, `detecciones` y `positividad`, y `unidad` a `conteo` o `porcentaje`.

**Ojo.** Un porcentaje **nunca** se guarda como `conteo`.

### `alertas`

**Qué es.** Tabla de las alertas de campo redactadas por el equipo de vigilancia.

**En el proyecto.** Creada por la migración `0009` ([ADR 0013](../adr/0013-alertas-de-campo-humanas.md)): `id`, `tipo`, `nivel`, `titulo`, `contexto`, `indicaciones`, `fuente`, `autor`, `vigente_desde`, `vigente_hasta` y `activa`. Después se le añadieron los cinco campos clínicos (`0010`), la `etiqueta` (`0011`) y `departamentos TEXT[]` con su `CHECK` de los 14 códigos (`0013`). La migración `0009` **inserta** dos alertas de demostración (una de dengue, una respiratoria) y una inactiva; el contenido lo siembran las migraciones, no el volcado.

**Ojo.** Ver el detalle de campos y reglas en [Alerta de campo](05-modulos-descriptivos-y-alertas.md#alerta-de-campo).

### `schema_migrations`

**Qué es.** Tabla que registra qué migraciones ya se aplicaron a una base.

**En el proyecto.** `filename` (llave primaria), `checksum` (sha256 del contenido al aplicarse) y `applied_at`. **No la crea una migración numerada** sino el propio runner en su paso `--bootstrap`, para evitar la paradoja de arranque ([ADR 0009](../adr/0009-runner-minimo-de-migraciones.md)).

## 3. Columnas y valores controlados

### `clasificacion`

**Qué es.** Columna de `casos_epidemiologicos` que dice **qué definición de caso** representa la fila.

**En el proyecto.** Cinco valores, cada uno agregado por una migración y un ADR:

| Valor | Origen | Migración |
|---|---|---|
| `probable` | Tabla departamental de MINSAL (laboratorio) | `0001` |
| `confirmado` | Tabla departamental de MINSAL y confirmados nacionales del tablero | `0001` |
| `total` | Serie nacional de OpenDengue | `0003` (ADR 0005) |
| `notificado` | Conteo notificado de IRA y neumonías, sin desglose de laboratorio | `0007` (ADR 0011) |
| `sospechoso` | «Casos Sospechosos de Dengue» del tablero | `0012` (ADR 0021) |

Ver el significado epidemiológico de cada uno en la [rama 1](01-epidemiologia-y-vigilancia.md#7-cómo-nombra-y-cuenta-los-casos-el-proyecto).

**Ojo.** Las definiciones **no son intercambiables** y nunca se suman. El valor `total` se puebla solo para `fuente_id = opendengue_v1_3` a nivel nacional, pero **nada en el esquema lo fuerza**: es disciplina del cargador.

### `conteo`

**Qué es.** Entero no negativo con el número de casos.

**En el proyecto.** Para los boletines es el valor **desacumulado** de la semana. Una semana sin fila es un hueco, no un cero.

### `nivel_admin`

**Qué es.** Nivel de la jerarquía administrativa.

**En el proyecto.** 0 nacional, 1 departamento, 2 municipio (reservado). Casi todas las consultas filtran `nivel_admin = 1` para obtener los departamentos.

### `fecha_ingesta`

**Qué es.** Marca de tiempo (`TIMESTAMPTZ`) de cuándo se cargó o actualizó la fila.

**En el proyecto.** Los upsert la actualizan con `now()` en cada `ON CONFLICT DO UPDATE`.

### `familia_esquema`

**Qué es.** Columna de `boletines_procesados` con la familia de tabla del boletín.

**En el proyecto.** Restringida a `A` o `B`. Ver [Familia A y Familia B](02-fuentes-de-datos-e-ingesta.md#familia-a-y-familia-b).

## 4. Migraciones

### Migración

**Qué es.** Archivo SQL que lleva el esquema de un estado al siguiente.

**En el proyecto.** Están en `db/migrations/` con el nombre `NNNN_descripcion.sql` (cuatro dígitos). Una migración agrega columnas, restricciones o tablas, o inserta filas de catálogo. **No cambia datos ingeridos** salvo la corrección puntual de `0003`.

| Migración | Qué hace | ADR |
|---|---|---|
| `0001` | Esquema inicial y catálogos (15 regiones, `dengue`, tres fuentes) | — (el ADR 0001 es la plantilla) |
| `0002` | Bitácora: `nombre_archivo` único, `version`, estado `ausencia_esperada`, `semana_archivo` nula, `boletin_id`; coordenadas de `regiones` | 0004, 0003 |
| `0003` | `clasificacion = 'total'` y corrección de la nota de OpenDengue | 0005 |
| `0004` | Fuente `open_meteo_era5` | 0006 |
| `0005` | Estado `sin_texto_extraible` | 0007 |
| `0006` | Fuente `noaa_oni` | 0008 |
| `0007` | `clasificacion = 'notificado'` y tipo de evento `ira` | 0011 |
| `0008` | Tabla `vigilancia_virus_respiratorios` y tipo de evento `neumonia` | 0012 |
| `0009` | Tabla `alertas` con tres alertas de demostración | 0013 |
| `0010` | Cinco campos clínicos opcionales en `alertas` | 0014 |
| `0011` | `etiqueta` y contenido clínico transcrito | 0015 |
| `0012` | `clasificacion = 'sospechoso'` y fuente `minsal_tablero` | 0021 |
| `0013` | `alertas.departamentos` | 0022 |

**Ojo.** Numerar los archivos no constituye un sistema de migraciones: el runner es lo que sabe qué se aplicó ya.

### ADR antes de migración

**Qué es.** Regla de proceso: **un cambio de esquema exige un ADR aceptado antes de escribir la migración**, sin excepción por conveniencia de empaquetado.

**En el proyecto.** Por eso cada migración cita el ADR que la respalda y el ADR nunca incluye su propia migración. Las filas de catálogo (dato) no lo exigen. Ver [ADR](10-proceso-gobernanza-y-documentacion.md#adr-architecture-decision-record).

### `docker-entrypoint-initdb.d`

**Qué es.** Carpeta de la imagen oficial de Postgres cuyos `.sql` se ejecutan **una sola vez, en orden alfabético, sobre un volumen vacío**.

**En el proyecto.** `docker-compose` monta `./db/migrations` en ella y el `seed_datos_reales.sql` como **archivo suelto**, porque Postgres solo procesa archivos del nivel superior (ignora subcarpetas). Como `'0' < 's'` en ASCII, el volcado se ejecuta **último**, con el esquema ya completo.

**Ojo.** Esa carpeta no sabe qué se aplicó ya en una base en marcha: una migración agregada después no se aplica sola. Para eso existe el runner.

### Runner de migraciones (`aplicar_migraciones.py`)

**Qué es.** Script mínimo que aplica solo las migraciones pendientes ([ADR 0009](../adr/0009-runner-minimo-de-migraciones.md)).

**En el proyecto.** Se ejecuta desde el host (`python db/aplicar_migraciones.py`) o como `preDeployCommand` en Render. Aplica, **en orden alfabético y cada una en su propia transacción**, los archivos `NNNN_*.sql` (ignora otros `.sql` y los de 0 bytes) que aún no estén en `schema_migrations`. Si el checksum de un archivo ya aplicado cambió, imprime un **aviso** y sigue, porque no hay forma de reaplicar sin una migración de reversión. Es deliberadamente mínimo: sin reversión (`down`), sin generador de plantillas, sin dependencias nuevas; no es Alembic ni Flyway.

**Ojo.** Lee las mismas variables `POSTGRES_*` que el backend. Si `POSTGRES_HOST` vale exactamente `db`, lo trata como `localhost`, porque ese nombre solo resuelve dentro de la red de Docker. Ya no existe `MIGRACIONES_POSTGRES_HOST`.

### `--bootstrap`

**Qué es.** Paso de arranque del runner, de **un único uso por base**.

**En el proyecto.** Crea `schema_migrations` y **siembra como ya aplicados, sin ejecutarlos**, todos los archivos presentes (`INSERT` de su nombre y checksum). Supone que esos archivos ya corrieron por construcción (por `docker-entrypoint-initdb.d`). Si la tabla ya existe, se niega a re-sembrar.

**Ojo.** Esa suposición sería falsa, y silenciosamente, contra una base modificada por fuera del flujo normal. Por eso en Render el primer despliegue exige **aplicar el DDL a mano** antes de `--bootstrap` ([Primer despliegue](08-infraestructura-despliegue-y-repositorio.md#primer-despliegue-pasos-manuales-una-sola-vez)).

### `preDeployCommand`

**Qué es.** Comando que Render ejecuta en una instancia de la imagen recién construida, **antes de conmutar el tráfico**.

**En el proyecto.** `python db/aplicar_migraciones.py`. Si falla, el despliegue no avanza y sigue viva la versión anterior.

### Recrear un `CHECK`

**Qué es.** En PostgreSQL un `CHECK` no se modifica en su lugar: se elimina y se vuelve a crear.

**En el proyecto.** Es el patrón de las migraciones `0002`, `0003`, `0005`, `0007` y `0012`. El nombre de la restricción es autogenerado por el motor (`boletines_procesados_estado_check`, `casos_epidemiologicos_clasificacion_check`) y **se verificó en vivo** contra una base desechable en lugar de asumirlo.

### Migración de solo datos

**Qué es.** Una migración que inserta filas de catálogo y no cambia la estructura.

**En el proyecto.** Es el caso de `0004` y `0006` (una fila de `fuentes_datos`) y de partes de `0007` y `0008` (filas de `tipos_evento`). No requiere un cambio de estructura, pero sigue el proceso de ADR previo cuando la decisión de forma vale la pena dejarla registrada.

### Sin reversión (`down`)

**Qué es.** El runner no sabe deshacer una migración.

**En el proyecto.** Una migración mal escrita que ya se aplicó se corrige con **una migración nueva** que deshace el cambio.

### Costo de reingesta

**Qué es.** Lo que cuesta reconstruir la base si un cambio de esquema exige empezar de cero.

**En el proyecto.** Mientras la base estaba vacía, cualquier cambio costaba `docker compose down -v` y una reingesta gratuita. Con 6.379 filas de casos, 56.924 de variables y 264 boletines procesados (2026-08-16), reconstruir cuesta horas y no minutos: es la razón de existir del runner.

## 5. Volcado de datos reales

### Volcado versionado (seed)

**Qué es.** Un `pg_dump --data-only` de las tablas pobladas por ingesta, guardado en `db/seed/seed_datos_reales.sql` ([ADR 0010](../adr/0010-versionar-volcado-de-datos-reales.md)).

**En el proyecto.** Es lo que permite que un tercero haga `git clone` y `docker compose up` y obtenga el sistema funcionando **con datos reales**, sin depender de que las 264 páginas de MINSAL ni el límite de Open-Meteo cooperen. Es dato público real ya verificado, no un dataset sintético. Su primera versión pesó **4,4 MB** de texto plano (hoy unos 5,7 MB) y no contiene ningún PDF. Es **una foto de un momento** (original 2026-08-17; regenerado 2026-09-01 para incluir lo respiratorio y saneado 2026-09-06), no un espejo: queda desactualizado apenas se carga un boletín o una semana de clima más.

**Qué incluye y qué excluye.**

- **Incluye:** `semanas_epidemiologicas`, `boletines_procesados`, `casos_epidemiologicos`, `variables_ambientales` y `vigilancia_virus_respiratorios`.
- **Excluye** `regiones`, `tipos_evento` y `fuentes_datos` (las siembran las migraciones; incluirlas provocaba conflicto de llave primaria), `schema_migrations` (la crea el runner) y `alertas*` (las insertan las migraciones `0009`–`0011`).

**Conteos de la primera foto (2026-08-16/17).** 264 boletines, 6.379 casos, 56.924 variables ambientales, 679 semanas, 15 regiones, 1 tipo de evento y 5 fuentes, con el catálogo de esa fecha; en la foto respiratoria, 2.749 filas de neumonías, 3.028 de vigilancia viral y 2.742 de IRA.

**Conteos del volcado actual (contados el 2026-09-30).** 264 boletines; 11.870 filas de casos (2.934 `probable` y 2.871 `confirmado` de MINSAL, 574 `total` de OpenDengue y 5.491 `notificado`, de IRA y neumonías); 65.450 filas de variables ambientales (9.268 por cada una de las 7 variables climáticas más 574 de `oni_anom`, de 2014 a 2026); 3.028 filas de vigilancia viral y 679 semanas.

**Ojo.** Como el volcado es una foto, una foto local puede diferir de otra. La Vía −1 fijó su fuente canónica con el SHA-256 del seed. **El seed no incluye el tablero de MINSAL**: desde un clon limpio solo puede regenerarse la base de M0 del nowcast.

### `generar_seed.sh`

**Qué es.** Script que regenera el volcado (`db/generar_seed.sh`).

**En el proyecto.** Corre `pg_dump --data-only --disable-triggers` con las exclusiones anteriores y **post-procesa** la salida con `grep -vE` para quitar las líneas `ALTER TABLE … DISABLE/ENABLE TRIGGER ALL;` (issue #82). Falla si queda alguna. Regenerarlo es **una acción manual**, no automática ni por PR; no se hace con `pg_dump … > seed_datos_reales.sql` a pelo.

### `--disable-triggers` y superusuario

**Qué es.** Bandera de `pg_dump` que emite instrucciones para desactivar triggers durante la carga.

**En el proyecto.** Esas líneas exigen superusuario y `aetheris_user` en el Postgres gestionado de Render **no lo es**, así que abortaban la carga entera con `permission denied: "RI_ConstraintTrigger_..." is a system trigger`. Se quitan en el post-proceso; las claves foráneas se validan igual porque el dump ordena las tablas por dependencia.

### Carga en una sola invocación de `psql`

**Qué es.** Forma de cargar el seed sin que se «filtre» estado entre archivos.

**En el proyecto.** `psql "$CONN" -X --single-transaction -v ON_ERROR_STOP=1 -q -f db/seed/seed_datos_reales.sql`. `-X` no lee `~/.psqlrc`; `--single-transaction` con `ON_ERROR_STOP` hace rollback de toda la carga si algo falla, no un seed a medias. El dump ejecuta `SELECT pg_catalog.set_config('search_path', '', false)` y eso **persiste** en la sesión: un segundo `-f` en la misma invocación no encuentra tablas en `public` salvo que use nombres calificados. Por eso el seed va **en su propia invocación**.

### `setval`

**Qué es.** Función de PostgreSQL que fija el siguiente valor de una secuencia.

**En el proyecto.** El volcado incluye `SELECT pg_catalog.setval(...)` de las tablas de hechos; se comprobó que quedan correctos tras la carga, para que las inserciones nuevas no choquen con los ids ya cargados.

## 6. SQL y herramientas de línea de comandos

### Upsert (`ON CONFLICT … DO UPDATE`)

**Qué es.** Insertar una fila o, si ya existe por la llave única, actualizarla.

**En el proyecto.** Es el mecanismo de idempotencia de todos los cargadores. Ver [Idempotencia y upsert](02-fuentes-de-datos-e-ingesta.md#idempotencia-y-upsert).

### `psql` y `pg_dump`

**Qué es.** El cliente interactivo y la herramienta de volcado de PostgreSQL.

**En el proyecto.** `psql` aplica el DDL y el seed contra la base gestionada de Render; `pg_dump` genera el volcado. Ambos se usan **desde el host**, no dentro de ningún contenedor, en el primer despliegue.

### SQLSTATE `42P01` (`UndefinedTable`)

**Qué es.** Código de error de PostgreSQL para «relación inexistente».

**En el proyecto.** La API lo distingue de un fallo de conexión: una tabla ausente responde `disponible: false` en lugar de 500. Ver [Degradación elegante](06-backend-y-api.md#degradación-elegante).

### `to_regclass`

**Qué es.** Función de PostgreSQL que devuelve el identificador de una tabla o `NULL` si no existe.

**En el proyecto.** El runner la usa (`to_regclass('schema_migrations') IS NOT NULL`) para saber si la tabla de migraciones ya existe.

### `psycopg2.extras.execute_values`

**Qué es.** Función para insertar muchas filas en pocas sentencias.

**En el proyecto.** Los cargadores la llaman con `page_size=len(valores)`: sin eso, `cur.rowcount` solo refleja la última página interna.
