-- ============================================================================
-- EPI-Aetheris — Migración 0004
-- Respalda: ADR 0006 (segunda fila de catálogo open_meteo_era5, para
-- atribuir precipitation_sum/precipitation_hours a su modelo real -- era5,
-- no era5_land, que no sirve precipitación)
-- ============================================================================

BEGIN;

INSERT INTO fuentes_datos (codigo, nombre, url_referencia, notas) VALUES
    ('open_meteo_era5', 'Open-Meteo - ERA5', 'https://open-meteo.com',
     'Unico modelo usado para precipitation_sum/precipitation_hours (era5_land no sirve precipitacion). Resolucion 0,25 grados -- La Libertad y San Salvador comparten celda, aceptado deliberadamente (ver docs/contexto/01-decisiones-cerradas.md).');

COMMIT;
