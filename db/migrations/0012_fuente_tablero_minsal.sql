-- ============================================================================
-- EPI-Aetheris — Migración 0012
-- Respalda: ADR 0021 (tablero de vigilancia de MINSAL como fuente, a partir
--           de capturas HAR hechas desde el navegador; quinto valor de
--           clasificacion: 'sospechoso')
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. casos_epidemiologicos.clasificacion admite 'sospechoso'
-- ============================================================================

-- Mismo procedimiento que 0003 y 0007: el CHECK se elimina y se recrea.
ALTER TABLE casos_epidemiologicos
    DROP CONSTRAINT casos_epidemiologicos_clasificacion_check;

ALTER TABLE casos_epidemiologicos
    ADD CONSTRAINT casos_epidemiologicos_clasificacion_check
    CHECK (clasificacion IN ('probable', 'confirmado', 'total', 'notificado', 'sospechoso'));

COMMENT ON COLUMN casos_epidemiologicos.clasificacion IS
    'probable/confirmado: series de laboratorio que MINSAL reporta por separado (tabla departamental de dengue en PDF; confirmados nacionales del tablero). total: conteo agregado de OpenDengue (case_definition_standardised = ''Total''), exclusivo de fuente_id = opendengue_v1_3 a nivel nacional. notificado: conteo sin desagregación probable/confirmado ni confirmación de laboratorio declarada (IRA, neumonías). sospechoso: casos sospechosos de dengue tal como los nombra el tablero de MINSAL ("Casos Sospechosos de Dengue"), exclusivo de fuente_id = minsal_tablero. No sumar conteo entre valores de clasificacion ni entre fuentes sin filtrar primero.';

-- ============================================================================
-- 2. Fuente: tablero de vigilancia de MINSAL
-- ============================================================================

INSERT INTO fuentes_datos (codigo, nombre, url_referencia, notas) VALUES
    ('minsal_tablero', 'Tablero de vigilancia epidemiológica MINSAL (Superset)', 'https://boletin.salud.gob.sv/',
     'Series nacionales semanales desde 2025, extraídas de capturas HAR que una persona guarda desde el navegador al abrir el tablero (ADR 0021). Ningún script hace peticiones al sitio. Cada captura es una foto del día: MINSAL puede revisar semanas ya publicadas. La serie es mucho más lisa que un conteo semanal crudo y se reinicia al cambiar de año; no se empalma con OpenDengue ni con los PDF sin tratarla como otra fuente. La semana 53 de 2025 no aparece publicada y queda sin dato.');

COMMIT;
