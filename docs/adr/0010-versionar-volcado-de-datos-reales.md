# 0010 - Versionar un volcado de los datos reales ya cargados

**Estado:** Aceptado

## Contexto

El proyecto promete que cualquiera clone el repositorio, levante con un comando (`docker compose up`) y obtenga el sistema funcionando, con costo de replicación cercano a cero (ver `AGENTS.md`, invariantes de infraestructura). Pero `backend/ingestion/data/raw/` (264 boletines MINSAL) y `backend/ingestion/data/interim/` no se versionan por regla explícita — así que hoy quien clona obtiene una base vacía: sin datos hasta correr manualmente el pipeline completo de ingesta (parser MINSAL + Open-Meteo, con rate-limits ya confirmados) o el runner de migraciones no alcanza a llenarla, porque las migraciones son esquema, no datos.

Se evaluaron tres salidas (`docs/contexto/02-decisiones-abiertas.md`, punto C original antes de dividirse):

1. Versionar un volcado (`pg_dump`) de la base ya poblada.
2. Versionar solo el extracto nacional de OpenDengue (candidato ya reconocido, <0,5 MB).
3. Que el arranque ejecute la descarga completa desde las fuentes originales.

**Medido antes de decidir, no asumido:** un volcado `--data-only` de las tablas realmente pobladas por ingesta (excluyendo las que ya siembran las propias migraciones — ver punto B) pesa **4,4 MB en texto plano**, sin un solo PDF crudo. La opción 2 deja el mapa departamental y el clasificador sin datos reales al clonar — el sistema arranca pero no queda "funcionando" en el sentido que promete el repositorio. La opción 3 es fiel al principio de "nada fabricado", pero es lenta (Open-Meteo tiene rate-limit por minuto ya confirmado en producción) y frágil (depende de que las fuentes originales sigan disponibles igual que hoy, incluyendo los 264 PDF de MINSAL).

## Decisión

**A. Se versiona un volcado `pg_dump --data-only` de los datos reales ya cargados**, en `db/seed/seed_datos_reales.sql`. Es dato público real ya verificado (mismo origen que documenta `docs/contexto/03-fuentes-de-datos.md`), no un dataset sintético — no viola el estatuto de "nunca fabricar, simular o sintetizar un dataset". Mismo principio ya aceptado para `backend/ingestion/geo/slv-adm1-source.geojson` (ADR 0002): dato descargado pero pequeño, estático y necesario para que el build no dependa de red.

**B. El volcado excluye `regiones`, `tipos_evento` y `fuentes_datos`.** Esas tres tablas de catálogo ya se siembran completas dentro de las propias migraciones (`0001`, `0004`, `0006` insertan sus filas vía `INSERT INTO`), verificado en vivo: cargar solo `0001`-`0006` sobre un volumen limpio ya deja `regiones`=15, `tipos_evento`=1, `fuentes_datos`=5 filas. Incluirlas en el volcado de datos provocaba conflicto de llave primaria al cargar sobre un volumen nuevo. El volcado contiene únicamente `semanas_epidemiologicas`, `boletines_procesados`, `casos_epidemiologicos` y `variables_ambientales` — las tablas que sí dependen de ingesta real.

**C. El volcado excluye `schema_migrations`.** Esa tabla la crea el propio `db/aplicar_migraciones.py` en su paso `--bootstrap` (ADR 0009), no `docker-entrypoint-initdb.d` — no existe todavía en el momento en que el volcado se carga sobre un volumen nuevo, así que intentar poblarla ahí rompería la carga. Quien clona sigue el flujo ya documentado: levantar el stack (migraciones + volcado) y después correr `--bootstrap` si va a aplicar migraciones nuevas.

**D. Mecanismo de carga: archivo montado individualmente**, no una carpeta completa. `docker-entrypoint-initdb.d` de la imagen oficial de Postgres solo procesa archivos en el nivel superior de esa ruta (no recorre subcarpetas) — por eso `db/seed/seed_datos_reales.sql` se monta como archivo suelto dentro de `/docker-entrypoint-initdb.d/`, junto a los `.sql` de `db/migrations/`, en vez de montar `db/seed/` como subcarpeta (que Postgres ignoraría en silencio). El nombre (`seed_...`, sin prefijo numérico) ordena alfabéticamente después de `0001`-`0006` porque `'0' < 's'` en ASCII — se ejecuta último, con el esquema ya completo.

**E. Generado con `--disable-triggers`.** `regiones` tiene una referencia a sí misma (departamento → país vía `region_padre_id`) que `pg_dump` señala como advertencia de "restricción circular"; `--disable-triggers` evita que la carga falle por orden de FK durante el `COPY`. No aplica en la práctica a este volcado (esa tabla está excluida — ver punto B), pero se deja la bandera por si el volcado vuelve a incluir alguna tabla con auto-referencia en el futuro.

**F. Verificado de punta a punta antes de aceptarse**, mismo criterio que toda migración nueva: contenedor Postgres 15 descartable, `0001`→`0006`→`seed_datos_reales.sql` en secuencia, conteos de fila comparados 1:1 contra la base de desarrollo real (264/6.379/56.924/679/15/1/5, exactos), sin conflicto de FK ni de secuencia. `SELECT pg_catalog.setval(...)` de las tablas de hechos confirmado correcto tras la carga.

**G. No se automatiza la regeneración.** El volcado es una foto de un momento (original: 2026-08-17; regenerado 2026-09-01 para incluir la ingesta respiratoria); no se recalcula en cada commit ni hay hook que lo mantenga sincronizado con la base de desarrollo. Regenerarlo es una acción manual (`pg_dump ... > db/seed/seed_datos_reales.sql`, mismos flags que este ADR documenta) cuando el equipo decida que vale la pena una foto más reciente — no antes de cada PR.

**H. Enmienda 2026-09-01 — hechos respiratorios.** El volcado incluye también `vigilancia_virus_respiratorios` (ADR 0012). Sigue excluyendo catálogos (`regiones`, `tipos_evento`, `fuentes_datos`) y `schema_migrations`. `tipos_evento` gana `ira` (migración `0007`) y `neumonia` (`0008`) antes de cargar el seed; los `tipo_evento_id` del volcado corresponden a ese orden de un volumen limpio (dengue=1, ira=2, neumonia=3), no al orden accidental de la base de desarrollo. Recuentos verificados en la foto: Neumonías 2.749, vigilancia viral 3.028, IRA 2.742.

## Consecuencias

* Positivo: `git clone` + `docker compose up` deja el sistema funcionando con datos reales, sin depender de que las 264 páginas de MINSAL o el rate-limit de Open-Meteo cooperen — resuelve la contradicción del estatuto de reproducibilidad.
* Positivo: 4,4 MB es trivial para el repositorio (el `.git` ya es más pesado que eso solo por el historial de código).
* Negativo: el volcado queda desactualizado apenas se cargue un boletín o una semana de clima más — quien necesite el dato más reciente igual debe correr el pipeline real. Es una foto de arranque rápido, no un espejo en vivo de la base.
* Negativo: cada regeneración del volcado es un diff de texto grande y opaco en el historial de git (miles de líneas `COPY`) — aceptado, es el costo de versionar datos en texto plano en vez de un formato binario, y prioriza que el archivo sea auditable con `diff`/`grep` sobre que el historial de git quede compacto.
* Neutral: no cambia nada del mecanismo de migraciones (ADR 0009) ni de las reglas de exclusión de `data/raw/`/`data/interim/` — es un artefacto nuevo y distinto, en su propia carpeta (`db/seed/`), con su propia regla explícita.

## Migración

Ninguna en `db/migrations/` — no es un cambio de esquema. Artefacto de datos en `db/seed/seed_datos_reales.sql`, cableado en `docker-compose.yml` (montaje de archivo individual junto a `db/migrations/`).
