-- ============================================================================
-- EPI-Aetheris — Migración 0003
-- Respalda: ADR 0005 (tercer valor de clasificacion: 'total', para la serie
--           nacional de OpenDengue, que no trae split probable/confirmado)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ADR 0005 — casos_epidemiologicos.clasificacion admite 'total'
-- ============================================================================

-- En Postgres un CHECK no se modifica in place: se elimina y se recrea. El
-- nombre de la restricción es autogenerado por el motor
-- (casos_epidemiologicos_clasificacion_check), verificado en vivo contra
-- 0001_init_schema.sql + 0002_bitacora_boletines_y_coordenadas_regiones.sql
-- sin modificar, no asumido (mismo criterio que el ADR 0004 para
-- boletines_procesados_estado_check).
ALTER TABLE casos_epidemiologicos
    DROP CONSTRAINT casos_epidemiologicos_clasificacion_check;

ALTER TABLE casos_epidemiologicos
    ADD CONSTRAINT casos_epidemiologicos_clasificacion_check
    CHECK (clasificacion IN ('probable', 'confirmado', 'total'));

COMMENT ON COLUMN casos_epidemiologicos.clasificacion IS
    'probable/confirmado: series de laboratorio que MINSAL reporta por separado en la tabla departamental. total: conteo agregado de OpenDengue (case_definition_standardised = ''Total'' en el CSV fuente), sin desglose por definición de caso -- no equivale a confirmado ni a probable, no sumar junto con esas dos series sin filtrar por clasificacion primero. Se puebla exclusivamente para fuente_id = opendengue_v1_3 a nivel nacional; nada en el esquema fuerza esa correspondencia, es responsabilidad del loader.';

-- ============================================================================
-- 2. Corrección de dato (no de esquema): fuentes_datos.notas para
-- opendengue_v1_3 seguía describiendo la fuente como "uso narrativo/
-- exploratorio", desactualizado desde el pivote "Opción C" (2026-08-09,
-- ver docs/contexto/01-decisiones-cerradas.md) -- esta serie es ahora la
-- variable objetivo del primer clasificador, no solo material narrativo.
-- ============================================================================

UPDATE fuentes_datos
SET notas = 'Variable objetivo del primer clasificador (nacional, decisión "Opción C", 2026-08-09) a nivel Admin0/semanal, 2018-2024. Uso narrativo/exploratorio para años fuera de la ventana de entrenamiento departamental (2020, 2024+). Admin1 solo 2000-2009, mensual, reservado para validación retrospectiva.'
WHERE codigo = 'opendengue_v1_3';

COMMIT;
