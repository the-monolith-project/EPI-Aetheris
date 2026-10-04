"""Segundo factor con TOTP (RFC 6238): 6 dígitos, 30 s, SHA-1.

El secreto se guarda cifrado con AES-256-GCM, con el id del usuario como dato
asociado para que un secreto copiado a otra fila no descifre. Cada código
válido avanza `totp_ultimo_paso`, así un código ya usado no sirve de nuevo
dentro de su ventana.
"""

from __future__ import annotations

import io
import os
import time

import pyotp
import segno
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import ConfigCuentas

PASO_S = 30
DIGITOS = 6
TOLERANCIA_PASOS = 1


def nuevo_secreto() -> str:
    return pyotp.random_base32(length=32)


def cifrar(config: ConfigCuentas, secreto: str, usuario_id: str) -> tuple[bytes, int]:
    nonce = os.urandom(12)
    cifrado = AESGCM(config.clave_cifrado_vigente).encrypt(nonce, secreto.encode("ascii"), usuario_id.encode("ascii"))
    return nonce + cifrado, config.version_cifrado


def descifrar(config: ConfigCuentas, datos: bytes, version: int, usuario_id: str) -> str:
    clave = config.claves_cifrado.get(version)
    if clave is None:
        raise ValueError("clave de cifrado desconocida")
    datos = bytes(datos)
    try:
        return AESGCM(clave).decrypt(datos[:12], datos[12:], usuario_id.encode("ascii")).decode("ascii")
    except InvalidTag as exc:
        raise ValueError("secreto TOTP ilegible") from exc


def uri_aprovisionamiento(config: ConfigCuentas, secreto: str, correo: str) -> str:
    return pyotp.TOTP(secreto, digits=DIGITOS, interval=PASO_S).provisioning_uri(
        name=correo, issuer_name=config.emisor_totp
    )


def qr_svg(uri: str) -> str:
    """QR como SVG en línea. Se genera en el servidor para no cargar una
    biblioteca de códigos QR en el navegador."""
    salida = io.BytesIO()
    segno.make(uri, error="m").save(salida, kind="svg", scale=4, border=2, xmldecl=False, svgns=True)
    return salida.getvalue().decode("utf-8")


def verificar(secreto: str, codigo: str, ultimo_paso: int | None, ahora: float | None = None) -> int | None:
    """Devuelve el paso aceptado, o None. Un paso no mayor al último usado se
    rechaza aunque el código sea correcto."""
    codigo = codigo.strip().replace(" ", "")
    if len(codigo) != DIGITOS or not codigo.isdigit():
        return None
    totp = pyotp.TOTP(secreto, digits=DIGITOS, interval=PASO_S)
    paso_actual = int((time.time() if ahora is None else ahora) // PASO_S)
    aceptado: int | None = None
    # Se recorren todos los pasos para no variar el tiempo según cuál acierte.
    for paso in range(paso_actual - TOLERANCIA_PASOS, paso_actual + TOLERANCIA_PASOS + 1):
        if pyotp.utils.strings_equal(totp.at(paso * PASO_S), codigo) and aceptado is None:
            aceptado = paso
    if aceptado is None:
        return None
    if ultimo_paso is not None and aceptado <= ultimo_paso:
        return None
    return aceptado
