-- ============================================================================
-- EPI-Aetheris — Migración 0005
-- Respalda: ADR 0007 (bitácora de boletines: nuevo estado sin_texto_extraible)
-- ============================================================================

BEGIN;

-- En PostgreSQL un CHECK no se modifica in place: se elimina y se recrea.
-- Nombre de la restricción confirmado en vivo contra el esquema real
-- (boletines_procesados_estado_check), no asumido.
ALTER TABLE boletines_procesados
    DROP CONSTRAINT boletines_procesados_estado_check;

ALTER TABLE boletines_procesados
    ADD CONSTRAINT boletines_procesados_estado_check
    CHECK (estado IN ('pendiente', 'ok', 'revision_manual', 'error', 'ausencia_esperada', 'sin_texto_extraible'));

COMMENT ON COLUMN boletines_procesados.estado IS
    'sin_texto_extraible: el boletín se abrió sin error pero no se encontró ninguna mención de "dengue" en el texto extraíble de ninguna página -- indicio de tabla departamental renderizada como imagen, no ausencia real de dato. Distinto de error (el parser encontró texto pero no pudo interpretarlo) y de ausencia_esperada (MINSAL no publicó tabla departamental esa semana por diseño). No cuenta como fallo del parser en la métrica de calidad de la ingesta -- es un hueco de cobertura conocido, pendiente de rescate vía OCR (tarjeta 26, ver ADR 0007).';

COMMIT;
