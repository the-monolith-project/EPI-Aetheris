-- ============================================================================
-- EPI-Aetheris — Migración 0013
-- Respalda: ADR 0022 (alertas con alcance territorial)
--
-- Agrega alertas.departamentos (TEXT[]). NULL = alcance nacional; una lista
-- limita la alerta a esos departamentos (códigos ISO 3166-2). Las alertas
-- existentes quedan nacionales.
--
-- No regenera db/seed/seed_datos_reales.sql (ADR 0010).
-- ============================================================================

BEGIN;

ALTER TABLE alertas
    ADD COLUMN departamentos TEXT[];

ALTER TABLE alertas
    ADD CONSTRAINT alertas_departamentos_check
        CHECK (
            departamentos IS NULL
            OR (
                cardinality(departamentos) > 0
                AND departamentos <@ ARRAY[
                    'SV-AH', 'SV-CA', 'SV-CH', 'SV-CU', 'SV-LI', 'SV-MO', 'SV-PA',
                    'SV-SA', 'SV-SM', 'SV-SO', 'SV-SS', 'SV-SV', 'SV-UN', 'SV-US'
                ]::TEXT[]
            )
        );

COMMENT ON COLUMN alertas.departamentos IS
    'NULL = alerta nacional. Lista de códigos ISO 3166-2 (SV-AH..SV-US) = alerta limitada a esos departamentos. ADR 0022.';

COMMIT;
