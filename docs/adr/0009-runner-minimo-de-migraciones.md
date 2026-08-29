# 0009 - Runner mínimo de migraciones con tabla `schema_migrations`

**Estado:** Aceptado

## Contexto

`docker-entrypoint-initdb.d` corre todo `db/migrations/*.sql` una sola vez, sobre volumen vacío, en orden alfabético — sin tracking de qué se aplicó ya sobre una base en ejecución. Numerar los archivos es una convención, no un sistema de migraciones (`docs/contexto/02-decisiones-abiertas.md`, punto C). Hasta ahora eso se resolvía con `docker compose down -v` + reingesta completa cada vez que se agregaba una migración — aceptable mientras la base estaba vacía o con datos de prueba desechables (confirmado en el changelog del 2026-08-11: las migraciones `0002`-`0004` tuvieron que aplicarse recreando el volumen porque nunca se habían aplicado sobre el existente).

Esa condición ya no se cumple. Verificado en vivo contra la base del entorno de desarrollo (2026-08-16): **6.379 filas en `casos_epidemiologicos`, 56.924 en `variables_ambientales`, 264 boletines procesados** en `boletines_procesados` — producto del parser de producción MINSAL (264 PDF, incluye OCR puntual) y de la carga de clima (rate-limited contra Open-Meteo). Reconstruir ese estado ya no es gratis: cuesta horas, no minutos. Cualquier migración nueva desde ahora en adelante fuerza esa reconstrucción si se sigue con el flujo de "volumen limpio + reingesta". El punto C queda decidido: se implementa el runner mínimo, no se documenta la convención manual como definitiva.

## Decisión

**A. Tabla `schema_migrations`**, con columnas `filename` (PK, texto), `checksum` (sha256 del contenido del archivo al momento de aplicarse) y `applied_at` (timestamp). Registra qué archivos de `db/migrations/` ya corrieron contra la base actual.

**B. Esta tabla NO se crea vía un archivo de migración numerado.** La crea directamente el propio script (`db/aplicar_migraciones.py`) en su paso de arranque (`--bootstrap`). Motivo: evitar la paradoja de arranque — la tabla que registra qué migraciones corrieron no puede depender del mecanismo que ella misma habilita para saber si ya corrió. Es infraestructura del runner, no parte del dominio versionado en `db/migrations/`. Igual queda bajo este ADR porque agrega una tabla real a la base (mismo criterio del estatuto "ADR antes de cambio de esquema").

**C. Arranque (`--bootstrap`), un único uso por base:** crea `schema_migrations` si no existe y, solo en ese caso, siembra como "ya aplicados" (sin ejecutarlos) todos los archivos `.sql` presentes hoy en `db/migrations/` (`0001`-`0006`). Se apoya en una garantía estructural, no en una suposición: `docker-entrypoint-initdb.d` corre automáticamente sobre cualquier volumen nuevo antes de que exista oportunidad de invocar este script, así que en cualquier entorno donde el script se ejecute, los archivos presentes en ese momento ya están aplicados por construcción. Si la tabla ya existe, `--bootstrap` se niega a re-sembrar (evita duplicar o pisar aplicaciones reales).

**D. Corrida normal (sin flags):** aplica, en orden alfabético y cada uno en su propia transacción, solo los archivos `.sql` que no estén todavía en `schema_migrations`. Si el checksum de un archivo ya registrado cambió desde que se aplicó, imprime una advertencia y sigue — no bloquea, porque no hay forma de "reaplicar" una migración ya corrida sin una migración de reversión explícita, fuera de alcance de un runner mínimo.

**E. Ejecución desde el host**, no dentro del contenedor `backend`. `POSTGRES_HOST=db` en `.env` resuelve solo dentro de la red Docker del proyecto; el puerto 5432 ya está publicado al host (`docker-compose.yml`), así que el script usa `localhost` por defecto, no la variable de entorno existente — evita una ambigüedad de dos convenciones de host bajo el mismo nombre.

## Consecuencias

* Positivo: una migración nueva desde ahora se aplica en segundos contra la base real, sin perder los datos de producción ya cargados.
* Positivo: alcance deliberadamente mínimo — sin reversión (`down`), sin generador de plantillas, sin dependencias nuevas (usa `psycopg2`/`python-dotenv`, ya en `backend/requirements.txt`). No es Alembic ni Flyway; es lo justo para no perder el trabajo de ingesta ya hecho.
* Negativo: el arranque (`--bootstrap`) asume que los archivos presentes en `db/migrations/` en ese momento ya están aplicados. Es cierto en cualquier entorno levantado con `docker-compose up`, pero sería falso — y silenciosamente incorrecto, sin error visible — contra una base modificada por fuera de ese flujo. No se agrega una verificación para ese caso porque no es un escenario que ocurra en este proyecto (un solo stack Docker compartido, ver la nota de multi-agente en `AGENTS.md`).
* Negativo: sin mecanismo de reversión. Una migración mal escrita que ya se aplicó se corrige con una migración nueva que deshace el cambio, no con un `down` automático.
* Neutral: `db/migrations/*.sql` sigue siendo la fuente de verdad del esquema para un volumen nuevo (vía `docker-entrypoint-initdb.d`); el runner solo cubre el caso de un volumen ya inicializado.

## Migración

Ninguna en `db/migrations/` — ver punto B. Implementación en `db/aplicar_migraciones.py`.
