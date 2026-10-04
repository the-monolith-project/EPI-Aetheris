-- ============================================================================
-- EPI-Aetheris — Migración 0014
-- Respalda: ADR 0024 (cuentas de usuario y publicación con identidad)
--
-- Identidad: instituciones, usuarios, roles, credenciales, factores de
-- autenticación, códigos de recuperación, invitaciones y tokens de un solo
-- uso. Solo tablas nuevas: no toca alertas ni ninguna tabla existente.
--
-- Los identificadores de personas son UUID aleatorios (gen_random_uuid es
-- nativo desde Postgres 13) para no revelar cuántas cuentas hay. Los valores
-- secretos (tokens, códigos) se guardan solo como hash.
-- ============================================================================

BEGIN;

CREATE TABLE instituciones (
    id                  BIGSERIAL PRIMARY KEY,
    nombre              TEXT NOT NULL UNIQUE,
    tipo                TEXT NOT NULL
        CHECK (tipo IN ('minsal', 'sibasi', 'hospital', 'universidad', 'organismo', 'otro')),
    dominios_correo     TEXT[] NOT NULL DEFAULT '{}',
    sitio_web           TEXT,
    verificada_en       TIMESTAMPTZ,
    verificada_por      UUID,
    verificacion_metodo TEXT,
    activa              BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT instituciones_dominios_minusculas
        CHECK (array_to_string(dominios_correo, ',') = lower(array_to_string(dominios_correo, ','))),
    CONSTRAINT instituciones_verificacion_completa
        CHECK (verificada_en IS NULL OR verificacion_metodo IS NOT NULL)
);

CREATE TABLE usuarios (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correo                    TEXT NOT NULL,
    correo_verificado_en      TIMESTAMPTZ,
    nombre_visible            TEXT NOT NULL
        CHECK (char_length(nombre_visible) BETWEEN 2 AND 120),
    cargo                     TEXT CHECK (cargo IS NULL OR char_length(cargo) <= 120),
    institucion_id            BIGINT REFERENCES instituciones (id),
    -- 'sistema' es solo el autor de las alertas heredadas: sin credenciales.
    estado                    TEXT NOT NULL
        CHECK (estado IN ('invitado', 'activo', 'suspendido', 'baja', 'sistema')),
    identidad_metodo          TEXT,
    identidad_verificada_en   TIMESTAMPTZ,
    identidad_verificada_por  UUID REFERENCES usuarios (id),
    terminos_version          TEXT,
    terminos_aceptados_en     TIMESTAMPTZ,
    creado_en                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    creado_por                UUID REFERENCES usuarios (id),
    ultimo_ingreso_en         TIMESTAMPTZ,
    baja_en                   TIMESTAMPTZ,
    baja_motivo               TEXT,
    CONSTRAINT usuarios_activo_con_correo_verificado
        CHECK (estado <> 'activo' OR correo_verificado_en IS NOT NULL),
    CONSTRAINT usuarios_activo_con_terminos
        CHECK (estado <> 'activo' OR terminos_aceptados_en IS NOT NULL)
);

-- El correo es único sin distinguir mayúsculas. No se usa citext para no
-- depender de una extensión más.
CREATE UNIQUE INDEX usuarios_correo_unico ON usuarios (lower(correo));

ALTER TABLE instituciones
    ADD CONSTRAINT instituciones_verificada_por_fk
        FOREIGN KEY (verificada_por) REFERENCES usuarios (id);

CREATE TABLE usuarios_roles (
    id           BIGSERIAL PRIMARY KEY,
    usuario_id   UUID NOT NULL REFERENCES usuarios (id),
    rol          TEXT NOT NULL CHECK (rol IN ('publicador', 'revisor', 'administrador')),
    -- NULL solo en el alta inicial por línea de órdenes.
    otorgado_por UUID REFERENCES usuarios (id),
    otorgado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revocado_en  TIMESTAMPTZ
);

CREATE UNIQUE INDEX usuarios_roles_vigente_unico
    ON usuarios_roles (usuario_id, rol) WHERE revocado_en IS NULL;

-- Nadie se otorga un rol a sí mismo.
CREATE FUNCTION usuarios_roles_sin_autootorgamiento() RETURNS trigger AS $$
BEGIN
    IF NEW.otorgado_por IS NOT NULL AND NEW.otorgado_por = NEW.usuario_id THEN
        RAISE EXCEPTION 'Una persona no puede otorgarse un rol a sí misma'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER usuarios_roles_autootorgamiento
    BEFORE INSERT ON usuarios_roles
    FOR EACH ROW EXECUTE FUNCTION usuarios_roles_sin_autootorgamiento();

CREATE TABLE credenciales_clave (
    usuario_id     UUID PRIMARY KEY REFERENCES usuarios (id),
    hash           TEXT NOT NULL,
    pepper_version SMALLINT NOT NULL,
    cambiada_en    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE factores_autenticacion (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id                UUID NOT NULL REFERENCES usuarios (id),
    tipo                      TEXT NOT NULL CHECK (tipo IN ('totp', 'webauthn')),
    etiqueta                  TEXT NOT NULL CHECK (char_length(etiqueta) BETWEEN 1 AND 60),
    totp_secreto_cifrado      BYTEA,
    totp_clave_version        SMALLINT,
    totp_ultimo_paso          BIGINT,
    webauthn_credencial_id    BYTEA UNIQUE,
    webauthn_clave_publica    BYTEA,
    webauthn_contador         BIGINT,
    webauthn_transportes      TEXT[],
    webauthn_respaldo_elegible BOOLEAN,
    webauthn_respaldo_actual  BOOLEAN,
    creado_en                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Un factor recién creado no vale hasta que la persona demuestra que lo
    -- tiene con un primer código.
    confirmado_en             TIMESTAMPTZ,
    ultimo_uso_en             TIMESTAMPTZ,
    revocado_en               TIMESTAMPTZ,
    CONSTRAINT factores_totp_completo
        CHECK (tipo <> 'totp' OR (totp_secreto_cifrado IS NOT NULL AND totp_clave_version IS NOT NULL)),
    CONSTRAINT factores_webauthn_completo
        CHECK (tipo <> 'webauthn' OR (
            webauthn_credencial_id IS NOT NULL
            AND webauthn_clave_publica IS NOT NULL
            AND webauthn_contador IS NOT NULL
        ))
);

CREATE INDEX factores_autenticacion_usuario ON factores_autenticacion (usuario_id)
    WHERE revocado_en IS NULL AND confirmado_en IS NOT NULL;

CREATE TABLE codigos_recuperacion (
    id         BIGSERIAL PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios (id),
    hash       BYTEA NOT NULL UNIQUE,
    lote       UUID NOT NULL,
    creado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    usado_en   TIMESTAMPTZ
);

CREATE INDEX codigos_recuperacion_usuario ON codigos_recuperacion (usuario_id)
    WHERE usado_en IS NULL;

CREATE TABLE invitaciones (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correo                TEXT NOT NULL,
    institucion_id        BIGINT REFERENCES instituciones (id),
    roles_propuestos      TEXT[] NOT NULL
        CHECK (cardinality(roles_propuestos) > 0
               AND roles_propuestos <@ ARRAY['publicador', 'revisor', 'administrador']::TEXT[]),
    token_hash            BYTEA NOT NULL UNIQUE,
    invitado_por          UUID REFERENCES usuarios (id),
    creada_en             TIMESTAMPTZ NOT NULL DEFAULT now(),
    caduca_en             TIMESTAMPTZ NOT NULL,
    aceptada_en           TIMESTAMPTZ,
    usuario_id            UUID REFERENCES usuarios (id),
    revocada_en           TIMESTAMPTZ,
    -- Qué se hizo, fuera del correo invitado, para verificar a la persona.
    nota_verificacion     TEXT NOT NULL CHECK (char_length(nota_verificacion) >= 10),
    -- Obligatoria cuando el dominio del correo no está en la institución.
    justificacion_dominio TEXT
);

CREATE INDEX invitaciones_correo ON invitaciones (lower(correo));

CREATE TABLE tokens_un_solo_uso (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposito      TEXT NOT NULL
        CHECK (proposito IN ('restablecer_clave', 'verificar_correo', 'recuperar_factor', 'cancelar_recuperacion')),
    usuario_id     UUID NOT NULL REFERENCES usuarios (id),
    correo_destino TEXT,
    token_hash     BYTEA NOT NULL UNIQUE,
    caduca_en      TIMESTAMPTZ NOT NULL,
    usado_en       TIMESTAMPTZ,
    creado_en      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX tokens_un_solo_uso_usuario ON tokens_un_solo_uso (usuario_id, proposito)
    WHERE usado_en IS NULL;

COMMENT ON TABLE usuarios IS
    'Cuentas de personas que publican o administran. No hay cuentas de lectores. ADR 0024.';
COMMENT ON TABLE invitaciones IS
    'El alta es solo por invitación de un administrador. token_hash es SHA-256 del token; el token en claro no se guarda.';

COMMIT;
