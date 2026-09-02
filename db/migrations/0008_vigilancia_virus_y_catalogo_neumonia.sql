-- ============================================================================
-- EPI-Aetheris — Migración 0008
-- Respalda: ADR 0012 (tabla vigilancia_virus_respiratorios)
--           + catálogo tipos_evento 'neumonia' (dato, no esquema; ADR 0011
--             ya autoriza clasificacion='notificado' para este formato)
-- ============================================================================

BEGIN;

INSERT INTO tipos_evento (codigo, nombre, descripcion) VALUES
    ('neumonia', 'Neumonías',
     'Conteo semanal notificado por departamento (MINSAL, sin split probable/confirmado); serie publicada acumulada desde SE1, desacumulada por diferencia de cortes consecutivos. Exploración: backend/ingestion/corrida_respiratorios.py y docs/exploracion-neumonias-boletines-minsal.md.');

CREATE TABLE vigilancia_virus_respiratorios (
    id             BIGSERIAL PRIMARY KEY,
    region_id      INTEGER      NOT NULL REFERENCES regiones(id),
    anio           SMALLINT     NOT NULL,
    semana_epi     SMALLINT     NOT NULL,
    virus          VARCHAR(50)  NOT NULL,
    metrica        VARCHAR(40)  NOT NULL,
    valor          NUMERIC(12,4) NOT NULL,
    unidad         VARCHAR(20)  NOT NULL,
    fuente_id      INTEGER      NOT NULL REFERENCES fuentes_datos(id),
    boletin_id     INTEGER      REFERENCES boletines_procesados(id),
    fecha_ingesta  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    FOREIGN KEY (anio, semana_epi) REFERENCES semanas_epidemiologicas(anio, semana_epi),
    UNIQUE (region_id, anio, semana_epi, virus, metrica, fuente_id),
    CONSTRAINT vigilancia_virus_metrica_check
        CHECK (metrica IN ('muestras_analizadas', 'muestras_positivas', 'detecciones', 'positividad')),
    CONSTRAINT vigilancia_virus_unidad_check
        CHECK (unidad IN ('conteo', 'porcentaje'))
);

COMMENT ON TABLE vigilancia_virus_respiratorios IS
    'Vigilancia laboratorial/centinela de virus respiratorios (MINSAL). Unidad: muestras y detecciones, no casos clínicos. region_id es el país (SV, nivel_admin=0): la fuente no desagrega por departamento. virus es texto del loader (sin CHECK de nombres) para admitir virus nuevos sin migración. positividad se guarda como la publica la fuente, nunca recalculada en silencio. ADR 0012.';

COMMENT ON COLUMN vigilancia_virus_respiratorios.virus IS
    'todos | influenza | influenza_a_h1n1 | influenza_a_h3n2 | influenza_a_no_subtipificado | influenza_b | vsr | parainfluenza | adenovirus | covid_19 | otros. No CHECK: un virus nuevo no exige migración.';

COMMENT ON COLUMN vigilancia_virus_respiratorios.unidad IS
    'conteo o porcentaje. No mezclar: una positividad no se guarda como conteo.';

COMMIT;
