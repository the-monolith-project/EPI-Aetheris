-- ============================================================================
-- EPI-Aetheris — Migración 0010
-- Respalda: ADR 0014 (enfoque dual Panorama / Análisis)
--
-- Agrega campos clínicos OPCIONALES a la tabla `alertas` (ADR 0013). Son
-- contenedores: quedan NULL hasta que el equipo de vigilancia los llene a
-- mano con fuente oficial (MINSAL/OPS). La vista pública muestra cada campo
-- solo si no es NULL; un valor ausente no rompe nada.
--
-- No inserta ni modifica filas demo (siguen con estos campos en NULL).
-- No regenera db/seed/seed_datos_reales.sql (ADR 0010).
-- ============================================================================

BEGIN;

ALTER TABLE alertas
    ADD COLUMN signos_alarma        TEXT,
    ADD COLUMN criterios_referencia TEXT,
    ADD COLUMN que_notificar        TEXT,
    ADD COLUMN definicion_caso      TEXT,
    ADD COLUMN contacto_vigilancia  TEXT;

COMMENT ON COLUMN alertas.signos_alarma IS
    'Opcional. Signos de alarma a buscar en consulta, redactados por el equipo con fuente MINSAL/OPS. NULL = no se muestra. Texto plano (el frontend escapa).';

COMMENT ON COLUMN alertas.criterios_referencia IS
    'Opcional. Criterios de referencia / ingreso según guía MINSAL vigente. NULL = no se muestra. Texto plano.';

COMMENT ON COLUMN alertas.que_notificar IS
    'Opcional. Qué notificar y en qué plazo (VIGEPES/SIBASI). NULL = no se muestra. Texto plano.';

COMMENT ON COLUMN alertas.definicion_caso IS
    'Opcional. Definición de caso vigente para este evento, atribuida a la fuente oficial. NULL = no se muestra. Texto plano.';

COMMENT ON COLUMN alertas.contacto_vigilancia IS
    'Opcional. A quién contactar en el SIBASI para reportar o consultar. Dato de contacto real provisto por el equipo, nunca inventado. NULL = no se muestra. Texto plano.';

COMMIT;
