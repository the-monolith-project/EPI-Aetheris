-- ============================================================================
-- EPI-Aetheris — Migración 0016
-- Respalda: ADR 0024 (cuentas de usuario y publicación con identidad)
--
-- Auditoría encadenada por hash. Una sola cadena para seguridad,
-- administración y contenido. La cadena la calcula un disparador, no la
-- aplicación: quien tenga acceso de escritura a la tabla no puede insertar una
-- fila con un hash propio ni alterar o borrar filas existentes.
-- ============================================================================

BEGIN;

CREATE SEQUENCE auditoria_id_seq;

CREATE TABLE auditoria (
    id           BIGINT PRIMARY KEY,
    en           TIMESTAMPTZ NOT NULL DEFAULT now(),
    categoria    TEXT NOT NULL
        CHECK (categoria IN ('seguridad', 'administracion', 'contenido', 'sistema')),
    actor_tipo   TEXT NOT NULL
        CHECK (actor_tipo IN ('usuario', 'sistema', 'token_legado', 'anonimo')),
    actor_id     UUID,
    sesion_id    UUID,
    accion       TEXT NOT NULL,
    objeto_tipo  TEXT,
    objeto_id    TEXT,
    -- Sin secretos, sin contraseñas ni códigos, sin contenido de piezas.
    detalle      JSONB NOT NULL DEFAULT '{}',
    red_truncada TEXT,
    hash_previo  BYTEA NOT NULL,
    hash         BYTEA NOT NULL
);

-- Bytes que entran al hash de una fila. Se usa tanto al insertar como al
-- verificar, para que las dos rutas no puedan divergir.
CREATE FUNCTION auditoria_contenido_hash(
    p_previo BYTEA, p_id BIGINT, p_en TIMESTAMPTZ, p_categoria TEXT,
    p_actor_tipo TEXT, p_actor_id UUID, p_sesion_id UUID, p_accion TEXT,
    p_objeto_tipo TEXT, p_objeto_id TEXT, p_detalle JSONB, p_red TEXT
) RETURNS BYTEA AS $$
    SELECT sha256(
        p_previo || convert_to(concat_ws('|',
            p_id::text,
            to_char(p_en AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
            p_categoria,
            p_actor_tipo,
            coalesce(p_actor_id::text, ''),
            coalesce(p_sesion_id::text, ''),
            p_accion,
            coalesce(p_objeto_tipo, ''),
            coalesce(p_objeto_id, ''),
            p_detalle::text,
            coalesce(p_red, '')
        ), 'UTF8')
    );
$$ LANGUAGE sql IMMUTABLE;

CREATE FUNCTION auditoria_encadenar() RETURNS trigger AS $$
DECLARE
    previo BYTEA;
BEGIN
    -- Un solo escritor a la vez: el orden de la cadena es el orden de los id.
    PERFORM pg_advisory_xact_lock(hashtext('epi_aetheris_auditoria'));
    -- El id se asigna después de tomar el candado, no por defecto de columna,
    -- para que el orden de id coincida con el orden de encadenado.
    NEW.id := nextval('auditoria_id_seq');
    SELECT a.hash INTO previo FROM auditoria a ORDER BY a.id DESC LIMIT 1;
    IF previo IS NULL THEN
        previo := decode(repeat('00', 32), 'hex');
    END IF;
    NEW.hash_previo := previo;
    NEW.hash := auditoria_contenido_hash(
        previo, NEW.id, NEW.en, NEW.categoria, NEW.actor_tipo, NEW.actor_id,
        NEW.sesion_id, NEW.accion, NEW.objeto_tipo, NEW.objeto_id, NEW.detalle,
        NEW.red_truncada
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auditoria_encadenado
    BEFORE INSERT ON auditoria
    FOR EACH ROW EXECUTE FUNCTION auditoria_encadenar();

CREATE FUNCTION auditoria_inmutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'La tabla auditoria es de solo inserción'
        USING ERRCODE = 'insufficient_privilege';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auditoria_sin_cambios
    BEFORE UPDATE OR DELETE ON auditoria
    FOR EACH ROW EXECUTE FUNCTION auditoria_inmutable();

CREATE TRIGGER auditoria_sin_truncar
    BEFORE TRUNCATE ON auditoria
    FOR EACH STATEMENT EXECUTE FUNCTION auditoria_inmutable();

-- Devuelve el id de la primera fila cuya cadena no cuadra, o NULL si toda la
-- cadena es válida. Recorre en orden de id.
CREATE FUNCTION auditoria_verificar() RETURNS BIGINT AS $$
DECLARE
    fila     auditoria%ROWTYPE;
    esperado BYTEA := decode(repeat('00', 32), 'hex');
BEGIN
    FOR fila IN SELECT * FROM auditoria ORDER BY id LOOP
        IF fila.hash_previo IS DISTINCT FROM esperado THEN
            RETURN fila.id;
        END IF;
        IF fila.hash IS DISTINCT FROM auditoria_contenido_hash(
            fila.hash_previo, fila.id, fila.en, fila.categoria, fila.actor_tipo,
            fila.actor_id, fila.sesion_id, fila.accion, fila.objeto_tipo,
            fila.objeto_id, fila.detalle, fila.red_truncada
        ) THEN
            RETURN fila.id;
        END IF;
        esperado := fila.hash;
    END LOOP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON TABLE auditoria IS
    'Registro de solo inserción, encadenado por hash mediante disparadores. Verificar con auditoria_verificar(). ADR 0024.';

COMMIT;
