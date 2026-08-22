-- ============================================================================
-- EPI-Aetheris — Migración 0007
-- Respalda: ADR 0011 (cuarto valor de clasificacion: 'notificado', para
--           conteos departamentales sin split probable/confirmado -- IRA es
--           el primer caso, misma tabla-formato de neumonías/EDAS/zika-chik)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ADR 0011 — casos_epidemiologicos.clasificacion admite 'notificado'
-- ============================================================================

-- Mismo criterio que la migración 0003 (ADR 0005): en Postgres un CHECK no
-- se modifica in place, se elimina y se recrea. Nombre de la restricción
-- verificado en vivo contra 0003_clasificacion_total_opendengue.sql (que ya
-- la dejó en casos_epidemiologicos_clasificacion_check), no asumido.
ALTER TABLE casos_epidemiologicos
    DROP CONSTRAINT casos_epidemiologicos_clasificacion_check;

ALTER TABLE casos_epidemiologicos
    ADD CONSTRAINT casos_epidemiologicos_clasificacion_check
    CHECK (clasificacion IN ('probable', 'confirmado', 'total', 'notificado'));

COMMENT ON COLUMN casos_epidemiologicos.clasificacion IS
    'probable/confirmado: series de laboratorio que MINSAL reporta por separado en la tabla departamental de dengue. total: conteo agregado de OpenDengue (case_definition_standardised = ''Total'' en el CSV fuente), sin desglose por definición de caso -- exclusivo de fuente_id = opendengue_v1_3 a nivel nacional. notificado: conteo departamental sin desagregación probable/confirmado ni confirmación de laboratorio declarada -- término que la propia fuente MINSAL usa ("eventos de notificación"); primer caso es IRA (ADR 0011), formato compartido con neumonías/EDAS/zika-chikungunya en el mismo boletín. No sumar conteo entre valores de clasificacion sin filtrar primero.';

-- ============================================================================
-- 2. Catálogo del evento IRA (dato, no esquema -- no requiere ADR aparte,
--    ver ADR 0011). Ningún caso de IRA se inserta en casos_epidemiologicos
--    en esta migración: la ingesta es una tarea separada, todavía no
--    encargada.
-- ============================================================================

INSERT INTO tipos_evento (codigo, nombre, descripcion) VALUES
    ('ira', 'Infección Respiratoria Aguda',
     'Conteo semanal notificado por departamento (MINSAL, sin split probable/confirmado); serie publicada acumulada desde SE1, desacumulada por diferencia de cortes consecutivos. Exploración validada en backend/ingestion/corrida_ira.py y docs/exploracion-ira-boletines-minsal.md.');

COMMIT;
