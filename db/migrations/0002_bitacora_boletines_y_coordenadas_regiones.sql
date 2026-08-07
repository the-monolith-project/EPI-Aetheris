-- ============================================================================
-- EPI-Aetheris — Migración 0002
-- Respalda: ADR 0004 (bitácora de boletines: llave natural, estados, trazabilidad)
--           y ADR 0003 (coordenadas de regiones para Open-Meteo)
-- No incluye: atribución de fuente climática (maestro, Sección 10.1 punto J) —
-- sin ADR aceptado todavía, no se empaqueta aquí.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ADR 0004 — boletines_procesados: llave natural e idempotencia
-- ============================================================================

ALTER TABLE boletines_procesados
    ADD COLUMN nombre_archivo TEXT NOT NULL UNIQUE,
    ADD COLUMN version         SMALLINT NOT NULL DEFAULT 1;

COMMENT ON COLUMN boletines_procesados.nombre_archivo IS
    'Identidad real de lo procesado: nombre del archivo tal como el parser lo abrió, verificable en disco sin acceso a red. Llave natural de la bitácora (UNIQUE) — el parser hace upsert sobre esta columna para que reprocesar el mismo archivo actualice la fila en vez de duplicarla. Distinta de url_origen, que es una cadena reconstruida a partir de este mismo nombre y no un dato observado.';

COMMENT ON COLUMN boletines_procesados.version IS
    'Sufijo de republicación extraído explícitamente del nombre de archivo por el parser (_v2 -> 2, _v3 -> 3, sin sufijo -> 1). Dentro del mismo (anio, semana_archivo), la fila con version más alta es la vigente para casos_epidemiologicos; las versiones anteriores se conservan en la bitácora para auditoría, no se sobrescriben ni se borran.';

-- 1.2 Nuevo estado: boletín existente sin tabla departamental (boletín de
-- vacaciones o de semanas combinadas), distinto de error y de revision_manual.
-- En Postgres un CHECK no se modifica in place: se elimina y se recrea. El
-- nombre de la restricción es autogenerado por el motor (boletines_procesados_estado_check),
-- verificado en vivo contra 0001_init_schema.sql sin modificar, no asumido.
ALTER TABLE boletines_procesados
    DROP CONSTRAINT boletines_procesados_estado_check;

ALTER TABLE boletines_procesados
    ADD CONSTRAINT boletines_procesados_estado_check
    CHECK (estado IN ('pendiente', 'ok', 'revision_manual', 'error', 'ausencia_esperada'));

COMMENT ON COLUMN boletines_procesados.estado IS
    'ausencia_esperada: el boletín se descargó y se abrió sin error, pero por diseño de MINSAL no trae tabla departamental (boletín de vacaciones) o cubre más de una semana en un solo archivo. No cuenta como fallo en la métrica de calidad de la ingesta. Distinto de error (el parser falló de forma inesperada) y de revision_manual (la tabla existe pero la suma departamental no cuadra contra el total nacional publicado).';

-- 1.3 semana_archivo: ya no es NOT NULL. Queda nula únicamente cuando no hay
-- una sola semana que registrar (boletín de semanas combinadas, o boletín de
-- vacaciones con nombre de archivo sin patrón SE\d+ reconocible).
ALTER TABLE boletines_procesados
    ALTER COLUMN semana_archivo DROP NOT NULL;

-- ============================================================================
-- 2. ADR 0004 — trazabilidad de boletín a fila de casos
-- ============================================================================

ALTER TABLE casos_epidemiologicos
    ADD COLUMN boletin_id INTEGER REFERENCES boletines_procesados(id);

COMMENT ON COLUMN casos_epidemiologicos.boletin_id IS
    'Boletín MINSAL concreto que produjo esta fila. Nullable: las filas con fuente OpenDengue no tienen boletín que referenciar. Permite aislar exactamente qué filas produjo un boletín que resulta mal parseado, sin depender de reconstruir la relación por (anio, semana_epi, fuente_id), que no es uno a uno con un archivo cuando hay republicaciones.';

CREATE INDEX idx_casos_boletin ON casos_epidemiologicos (boletin_id);

-- ============================================================================
-- 3. ADR 0003 — coordenadas de regiones para Open-Meteo
-- ============================================================================

ALTER TABLE regiones
    ADD COLUMN centroide_lat NUMERIC(9,6),
    ADD COLUMN centroide_lon NUMERIC(9,6),
    ADD COLUMN elevacion_m   NUMERIC(7,2);

COMMENT ON COLUMN regiones.centroide_lat IS
    'Latitud del punto representativo del polígono de mayor área del departamento (backend/ingestion/compute_centroides.py), no el centro de celda que devuelve ningún proveedor climático.';

COMMENT ON COLUMN regiones.centroide_lon IS
    'Longitud del punto representativo del polígono de mayor área del departamento.';

COMMENT ON COLUMN regiones.elevacion_m IS
    'Elevación del punto representativo del departamento según el DEM interno de Open-Meteo (no varía con el modelo climático pedido, pero sí depende de esa fuente). No es una medición topográfica del departamento.';

COMMIT;
