"""Llaves de acceso (WebAuthn).

Se exige verificación de usuario (huella, PIN o rostro del dispositivo) y no se
pide atestación: no se necesita saber qué marca de llave es. Cada desafío vale
una sola vez y caduca en 5 minutos.
"""

from __future__ import annotations

import json
import secrets

from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import options_to_json
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from . import auditoria
from .config import ConfigCuentas
from .servicio import (
    ErrorCuentas,
    _control_espera,
    _exigir_nivel,
    _fallo_segundo_factor,
    _promover,
    _tras_factor_confirmado,
)
from .sesiones import Sesion

CADUCIDAD_DESAFIO_S = 300


def _guardar_desafio(conn, sesion: Sesion, tipo: str, valor: bytes) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE desafios SET usado_en = now() WHERE sesion_id = %s AND tipo = %s AND usado_en IS NULL",
            (sesion.id, tipo),
        )
        cur.execute(
            "INSERT INTO desafios (usuario_id, sesion_id, tipo, valor, caduca_en) "
            "VALUES (%s, %s, %s, %s, now() + make_interval(secs => %s))",
            (sesion.usuario_id, sesion.id, tipo, valor, CADUCIDAD_DESAFIO_S),
        )


def _consumir_desafio(conn, sesion: Sesion, tipo: str) -> bytes:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE desafios SET usado_en = now() WHERE id = ("
            "  SELECT id FROM desafios WHERE sesion_id = %s AND tipo = %s AND usado_en IS NULL "
            "  AND caduca_en > now() ORDER BY caduca_en DESC LIMIT 1 FOR UPDATE"
            ") RETURNING valor",
            (sesion.id, tipo),
        )
        fila = cur.fetchone()
    if fila is None:
        raise ErrorCuentas("desafio_invalido", "La solicitud caducó. Vuelve a intentarlo.", 400)
    return bytes(fila[0])


def _credenciales_existentes(conn, usuario_id: str) -> list[PublicKeyCredentialDescriptor]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT webauthn_credencial_id FROM factores_autenticacion "
            "WHERE usuario_id = %s AND tipo = 'webauthn' AND revocado_en IS NULL AND confirmado_en IS NOT NULL",
            (usuario_id,),
        )
        return [PublicKeyCredentialDescriptor(id=bytes(f[0])) for f in cur.fetchall()]


def opciones_registro(conn, config: ConfigCuentas, sesion: Sesion) -> dict:
    if sesion.nivel not in ("alta_pendiente", "completo"):
        raise ErrorCuentas("sesion_en_otro_paso", "Termina primero el ingreso.", 403)
    opciones = generate_registration_options(
        rp_id=config.rp_id,
        rp_name=config.rp_nombre,
        user_id=sesion.usuario_id.encode("ascii"),
        user_name=sesion.correo,
        user_display_name=sesion.nombre_visible,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=_credenciales_existentes(conn, sesion.usuario_id),
        challenge=secrets.token_bytes(32),
    )
    _guardar_desafio(conn, sesion, "webauthn_registro", opciones.challenge)
    return json.loads(options_to_json(opciones))


def verificar_registro(conn, config: ConfigCuentas, sesion: Sesion, credencial: dict, etiqueta: str) -> dict:
    if sesion.nivel not in ("alta_pendiente", "completo"):
        raise ErrorCuentas("sesion_en_otro_paso", "Termina primero el ingreso.", 403)
    desafio = _consumir_desafio(conn, sesion, "webauthn_registro")
    try:
        verificado = verify_registration_response(
            credential=credencial,
            expected_challenge=desafio,
            expected_rp_id=config.rp_id,
            expected_origin=config.origen_canonico,
            require_user_verification=True,
        )
    except (InvalidRegistrationResponse, ValueError, KeyError, TypeError) as exc:
        auditoria.registrar(
            conn, categoria="seguridad", accion="llave_registro_fallido", actor_id=sesion.usuario_id, sesion_id=sesion.id
        )
        raise ErrorCuentas("llave_invalida", "No se pudo registrar la llave de acceso.", 400) from exc
    transportes = [t for t in (credencial.get("response", {}).get("transports") or []) if isinstance(t, str)][:6]
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM factores_autenticacion WHERE webauthn_credencial_id = %s", (verificado.credential_id,))
        if cur.fetchone() is not None:
            raise ErrorCuentas("llave_repetida", "Esa llave ya está registrada.", 409)
        cur.execute(
            "INSERT INTO factores_autenticacion (usuario_id, tipo, etiqueta, webauthn_credencial_id, "
            "webauthn_clave_publica, webauthn_contador, webauthn_transportes, webauthn_respaldo_elegible, "
            "webauthn_respaldo_actual, confirmado_en) "
            "VALUES (%s, 'webauthn', %s, %s, %s, %s, %s, %s, %s, now())",
            (
                sesion.usuario_id,
                (etiqueta.strip() or "Llave de acceso")[:60],
                verificado.credential_id,
                verificado.credential_public_key,
                verificado.sign_count,
                transportes,
                verificado.credential_backed_up is not None and verificado.credential_device_type == "multi_device",
                bool(verificado.credential_backed_up),
            ),
        )
    return _tras_factor_confirmado(conn, config, sesion, "webauthn")


def opciones_ingreso(conn, config: ConfigCuentas, sesion: Sesion) -> dict:
    _exigir_nivel(sesion, "segundo_factor")
    permitidas = _credenciales_existentes(conn, sesion.usuario_id)
    if not permitidas:
        raise ErrorCuentas("sin_llaves", "Esta cuenta no tiene llaves de acceso.", 400)
    opciones = generate_authentication_options(
        rp_id=config.rp_id,
        challenge=secrets.token_bytes(32),
        allow_credentials=permitidas,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    _guardar_desafio(conn, sesion, "webauthn_ingreso", opciones.challenge)
    return json.loads(options_to_json(opciones))


def verificar_ingreso(conn, config: ConfigCuentas, sesion: Sesion, credencial: dict) -> str:
    _exigir_nivel(sesion, "segundo_factor")
    _control_espera(conn, config, sesion)
    desafio = _consumir_desafio(conn, sesion, "webauthn_ingreso")
    try:
        id_bruto = base64url_to_bytes(credencial["rawId"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ErrorCuentas("llave_invalida", "Respuesta de llave inválida.", 400) from exc
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, webauthn_clave_publica, webauthn_contador FROM factores_autenticacion "
            "WHERE usuario_id = %s AND tipo = 'webauthn' AND webauthn_credencial_id = %s "
            "AND revocado_en IS NULL AND confirmado_en IS NOT NULL FOR UPDATE",
            (sesion.usuario_id, id_bruto),
        )
        fila = cur.fetchone()
    if fila is None:
        _fallo_segundo_factor(conn, config, sesion, "llave_ingreso_fallido")
        raise ErrorCuentas("llave_invalida", "No se pudo verificar la llave de acceso.", 401)
    try:
        verificado = verify_authentication_response(
            credential=credencial,
            expected_challenge=desafio,
            expected_rp_id=config.rp_id,
            expected_origin=config.origen_canonico,
            credential_public_key=bytes(fila[1]),
            credential_current_sign_count=fila[2],
            require_user_verification=True,
        )
    except (InvalidAuthenticationResponse, ValueError, KeyError, TypeError) as exc:
        _fallo_segundo_factor(conn, config, sesion, "llave_ingreso_fallido")
        raise ErrorCuentas("llave_invalida", "No se pudo verificar la llave de acceso.", 401) from exc
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE factores_autenticacion SET webauthn_contador = %s, ultimo_uso_en = now() WHERE id = %s",
            (verificado.new_sign_count, fila[0]),
        )
    return _promover(conn, config, sesion, "webauthn")


__all__ = ["opciones_registro", "verificar_registro", "opciones_ingreso", "verificar_ingreso"]
