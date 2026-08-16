-- ============================================================================
-- EPI-Aetheris — Migración 0006
-- Respalda: ADR 0008 (fuente NOAA ONI -- predictor experimental)
-- ============================================================================

BEGIN;

INSERT INTO fuentes_datos (codigo, nombre, url_referencia, notas) VALUES
    ('noaa_oni', 'NOAA CPC - Oceanic Niño Index (ONI)', 'https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt',
     'Indice mensual (temporada movil de 3 meses) de anomalia de temperatura superficial del mar, region Nino 3.4. Predictor experimental (ADR 0008), no confirmado en produccion todavia. Se almacena bajo region SV (nacional) -- no tiene resolucion departamental. Variable en variables_ambientales: oni_anom (valor ANOM, no TOTAL).');

COMMIT;
