-- ============================================================================
-- EPI-Aetheris — Migración 0015
-- Respalda: ADR 0024 (cuentas de usuario y publicación con identidad)
--
-- Sesiones de servidor, desafíos de segundo factor, contadores de intentos de
-- ingreso y bandeja de salida de correo.
-- ============================================================================

BEGIN;

CREATE TABLE sesiones (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- SHA-256 del identificador opaco de la cookie; el valor en claro no se guarda.
    token_hash                BYTEA NOT NULL UNIQUE,
    usuario_id                UUID NOT NULL REFERENCES usuarios (id),
    creada_en                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    ultima_actividad_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    caduca_absoluta_en        TIMESTAMPTZ NOT NULL,
    autenticacion_reciente_en TIMESTAMPTZ,
    -- 'segundo_factor': la contraseña ya se verificó y falta el segundo factor;
    -- no concede ningún permiso y caduca en minutos.
    nivel                     TEXT NOT NULL
        CHECK (nivel IN ('alta_pendiente', 'segundo_factor', 'completo')),
    metodos                   TEXT[] NOT NULL DEFAULT '{}'
        CHECK (metodos <@ ARRAY['clave', 'totp', 'webauthn', 'recuperacion']::TEXT[]),
    agente_resumen            TEXT,
    red_truncada              TEXT,
    revocada_en               TIMESTAMPTZ,
    revocada_motivo           TEXT
);

CREATE INDEX sesiones_usuario_vigentes ON sesiones (usuario_id) WHERE revocada_en IS NULL;

-- Desafíos de WebAuthn: un solo uso, caducan en minutos.
CREATE TABLE desafios (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios (id),
    sesion_id  UUID REFERENCES sesiones (id),
    tipo       TEXT NOT NULL CHECK (tipo IN ('webauthn_registro', 'webauthn_ingreso')),
    valor      BYTEA NOT NULL,
    caduca_en  TIMESTAMPTZ NOT NULL,
    usado_en   TIMESTAMPTZ
);

-- clave: HMAC del correo normalizado o de la IP. Sobrevive a reinicios, a
-- diferencia del límite en memoria de slowapi.
CREATE TABLE intentos_ingreso (
    clave           BYTEA NOT NULL,
    ventana_inicio  TIMESTAMPTZ NOT NULL,
    fallos          INT NOT NULL DEFAULT 0,
    bloqueado_hasta TIMESTAMPTZ,
    PRIMARY KEY (clave, ventana_inicio)
);

-- Bandeja de salida: registra qué se envió y a quién. No guarda el cuerpo ni
-- el token de los mensajes con enlace; para esos, un envío fallido se resuelve
-- emitiendo un token nuevo, no reintentando el mismo.
CREATE TABLE correos_salientes (
    id                  BIGSERIAL PRIMARY KEY,
    plantilla           TEXT NOT NULL,
    destinatario        TEXT NOT NULL,
    usuario_id          UUID REFERENCES usuarios (id),
    estado              TEXT NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'enviado', 'fallido')),
    intentos            INT NOT NULL DEFAULT 0,
    error_codigo        TEXT,
    contexto            JSONB NOT NULL DEFAULT '{}',
    creado_en           TIMESTAMPTZ NOT NULL DEFAULT now(),
    enviado_en          TIMESTAMPTZ
);

CREATE INDEX correos_salientes_pendientes ON correos_salientes (creado_en)
    WHERE estado = 'pendiente';

COMMIT;
