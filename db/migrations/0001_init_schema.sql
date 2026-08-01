-- ============================================================================
-- EPI Aethery — Esquema de base de datos (PostgreSQL)
-- Capa de ingesta: variable objetivo + predictores ambientales
-- Diseño agnóstico al tipo de evento epidemiológico y a la región/país
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CATÁLOGOS BASE
-- ============================================================================

-- 1.1 Regiones (jerárquico: país -> departamento -> municipio)
CREATE TABLE regiones (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(10)  NOT NULL UNIQUE,      -- ej. 'SV', 'SV-AH'
    nombre          VARCHAR(100) NOT NULL,
    nivel_admin     SMALLINT     NOT NULL,              -- 0 = nacional (Admin0), 1 = departamento (Admin1), 2 = municipio (Admin2, reservado)
    pais            VARCHAR(2)   NOT NULL DEFAULT 'SV',
    region_padre_id INTEGER      REFERENCES regiones(id),
    activo          BOOLEAN      NOT NULL DEFAULT TRUE
);

COMMENT ON COLUMN regiones.codigo IS
    'Debe coincidir exactamente con la propiedad de identificación usada en el GeoJSON de límites administrativos que consume Leaflet. Verificar antes de usar como llave de unión en el mapa.';

-- 1.2 Tipos de evento (catálogo, no columna de texto libre, para mantener la abstracción agnóstica)
CREATE TABLE tipos_evento (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(50)  NOT NULL UNIQUE,           -- 'dengue'
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT
);

-- 1.3 Fuentes de datos (trazabilidad de origen para cada dato ingerido)
CREATE TABLE fuentes_datos (
    id             SERIAL PRIMARY KEY,
    codigo         VARCHAR(50)  NOT NULL UNIQUE,        -- 'opendengue_v1_3', 'minsal_pdf', 'open_meteo_era5_land'
    nombre         VARCHAR(150) NOT NULL,
    url_referencia TEXT,
    notas          TEXT
);

-- 1.4 Calendario de semanas epidemiológicas (referencia compartida entre casos y clima)
CREATE TABLE semanas_epidemiologicas (
    anio         SMALLINT NOT NULL,
    semana_epi   SMALLINT NOT NULL CHECK (semana_epi BETWEEN 1 AND 53),
    fecha_inicio DATE     NOT NULL,
    fecha_fin    DATE     NOT NULL,
    PRIMARY KEY (anio, semana_epi)
);

COMMENT ON TABLE semanas_epidemiologicas IS
    'Calendario de referencia (semana epidemiológica estándar PAHO/CDC, no necesariamente igual a la semana ISO 8601). Se puebla mediante script de generación de calendario en el pipeline de ingesta, no mediante este DDL. Permite agregar los datos diarios de clima a la misma unidad temporal que los casos, y sirve de llave foránea compartida.';

-- ============================================================================
-- 2. TABLAS DE HECHOS
-- ============================================================================

-- 2.1 Variable objetivo: casos por región, semana, tipo de evento y clasificación
CREATE TABLE casos_epidemiologicos (
    id             BIGSERIAL PRIMARY KEY,
    region_id      INTEGER     NOT NULL REFERENCES regiones(id),
    tipo_evento_id INTEGER     NOT NULL REFERENCES tipos_evento(id),
    anio           SMALLINT    NOT NULL,
    semana_epi     SMALLINT    NOT NULL,
    clasificacion  VARCHAR(20) NOT NULL CHECK (clasificacion IN ('probable', 'confirmado')),
    conteo         INTEGER     NOT NULL CHECK (conteo >= 0),
    fuente_id      INTEGER     NOT NULL REFERENCES fuentes_datos(id),
    fecha_ingesta  TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (anio, semana_epi) REFERENCES semanas_epidemiologicas(anio, semana_epi),
    UNIQUE (region_id, tipo_evento_id, anio, semana_epi, clasificacion, fuente_id)
);

COMMENT ON COLUMN casos_epidemiologicos.semana_epi IS
    'Semana epidemiológica real a la que corresponde el dato, no necesariamente la semana del nombre del archivo de origen. Para boletines MINSAL, "probable" y "confirmado" de una misma fila suelen corresponder a semanas distintas y deben insertarse como dos filas separadas.';

-- 2.2 Predictores ambientales: variables por región y semana
CREATE TABLE variables_ambientales (
    id            BIGSERIAL PRIMARY KEY,
    region_id     INTEGER      NOT NULL REFERENCES regiones(id),
    anio          SMALLINT     NOT NULL,
    semana_epi    SMALLINT     NOT NULL,
    variable      VARCHAR(50)  NOT NULL,                -- 'temp_max', 'temp_min', 'temp_media', 'precipitation_sum', 'precipitation_hours', 'humedad_relativa_media', 'punto_rocio', 'et0_fao'
    valor         NUMERIC(10,3) NOT NULL,
    fuente_id     INTEGER      NOT NULL REFERENCES fuentes_datos(id),
    fecha_ingesta TIMESTAMPTZ  NOT NULL DEFAULT now(),
    FOREIGN KEY (anio, semana_epi) REFERENCES semanas_epidemiologicas(anio, semana_epi),
    UNIQUE (region_id, anio, semana_epi, variable, fuente_id)
);

COMMENT ON TABLE variables_ambientales IS
    'Nombrada "ambientales" y no "climáticas" para dejar espacio a otros predictores no climáticos si el proyecto escala (ej. índice vectorial), sin requerir una tabla nueva.';

-- ============================================================================
-- 3. AUDITORÍA / CONTROL DE CALIDAD
-- ============================================================================

-- 3.1 Registro de procesamiento de boletines MINSAL (chequeo de cuadre departamental vs. total nacional)
CREATE TABLE boletines_procesados (
    id                                SERIAL PRIMARY KEY,
    anio                              SMALLINT    NOT NULL,
    semana_archivo                    SMALLINT    NOT NULL,   -- semana según el nombre del archivo, puede diferir de la semana real de los datos
    url_origen                        TEXT        NOT NULL,
    familia_esquema                   VARCHAR(1)  CHECK (familia_esquema IN ('A', 'B')),
    suma_departamental_probable       INTEGER,
    suma_departamental_confirmado     INTEGER,
    total_nacional_publicado_probable INTEGER,
    total_nacional_publicado_confirmado INTEGER,
    validacion_cuadra                 BOOLEAN,
    estado                            VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                                       CHECK (estado IN ('pendiente', 'ok', 'revision_manual', 'error')),
    fecha_procesado                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    notas                             TEXT
);

COMMENT ON TABLE boletines_procesados IS
    'Bitácora de ingesta por boletín. Si la suma de los 14 departamentos no coincide con el total nacional publicado en el mismo boletín, el registro debe marcarse en estado revision_manual en vez de ingerirse silenciosamente.';

-- ============================================================================
-- 4. ÍNDICES
-- ============================================================================

CREATE INDEX idx_casos_region_periodo ON casos_epidemiologicos (region_id, anio, semana_epi);
CREATE INDEX idx_casos_tipo_evento    ON casos_epidemiologicos (tipo_evento_id);
CREATE INDEX idx_ambientales_region_periodo ON variables_ambientales (region_id, anio, semana_epi);
CREATE INDEX idx_ambientales_variable ON variables_ambientales (variable);

-- ============================================================================
-- 5. DATOS SEMILLA (catálogos estáticos)
-- ============================================================================

INSERT INTO regiones (codigo, nombre, nivel_admin, pais) VALUES
    ('SV',    'El Salvador',   0, 'SV'),
    ('SV-AH', 'Ahuachapán',    1, 'SV'),
    ('SV-CA', 'Cabañas',       1, 'SV'),
    ('SV-CH', 'Chalatenango',  1, 'SV'),
    ('SV-CU', 'Cuscatlán',     1, 'SV'),
    ('SV-LI', 'La Libertad',   1, 'SV'),
    ('SV-PA', 'La Paz',        1, 'SV'),
    ('SV-SA', 'Santa Ana',     1, 'SV'),
    ('SV-SM', 'San Miguel',    1, 'SV'),
    ('SV-SO', 'Sonsonate',     1, 'SV'),
    ('SV-SS', 'San Salvador',  1, 'SV'),
    ('SV-SV', 'San Vicente',   1, 'SV'),
    ('SV-UN', 'La Unión',      1, 'SV'),
    ('SV-US', 'Usulután',      1, 'SV'),
    ('SV-MO', 'Morazán',       1, 'SV');

INSERT INTO tipos_evento (codigo, nombre, descripcion) VALUES
    ('dengue', 'Dengue', 'Caso piloto del proyecto. La tabla existe como catálogo para permitir agregar otras enfermedades sin cambios de esquema.');

INSERT INTO fuentes_datos (codigo, nombre, url_referencia, notas) VALUES
    ('opendengue_v1_3',     'OpenDengue - Spatial Extract V1.3', 'https://opendengue.org', 'Uso narrativo/exploratorio a nivel nacional (Admin0), 2018-2024. Admin1 solo 2000-2009, reservado para validación retrospectiva.'),
    ('minsal_pdf',           'Boletines epidemiológicos MINSAL (PDF)', 'https://www.salud.gob.sv', 'Fuente departamental para entrenamiento, ventana 2018-2023 excluyendo 2020. Dos familias de esquema de tabla (A: 2018-2020, B: 2021-2023).'),
    ('open_meteo_era5_land', 'Open-Meteo - ERA5-Land / Best Match', 'https://open-meteo.com', 'API gratuita alojada, sin self-hosting. Modelo fijado a era5_land/best_match por resolución espacial.');

COMMIT;
