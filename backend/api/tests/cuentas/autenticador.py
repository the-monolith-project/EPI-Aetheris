"""Autenticador WebAuthn de pruebas: una llave ES256 en software que produce
respuestas de registro (atestación 'none') y de ingreso como las de un navegador."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import struct

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec


def b64u(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).decode().rstrip("=")


class Autenticador:
    def __init__(self, rp_id: str, origen: str):
        self.rp_id, self.origen = rp_id, origen
        self.clave = ec.generate_private_key(ec.SECP256R1())
        self.id = os.urandom(32)
        self.contador = 0

    def _cose(self) -> bytes:
        n = self.clave.public_key().public_numbers()
        return cbor2.dumps({1: 2, 3: -7, -1: 1, -2: n.x.to_bytes(32, "big"), -3: n.y.to_bytes(32, "big")})

    def _cliente(self, tipo: str, desafio: str, origen: str | None) -> bytes:
        return json.dumps(
            {"type": tipo, "challenge": desafio, "origin": origen or self.origen, "crossOrigin": False}
        ).encode()

    def registrar(self, desafio_b64: str, *, flags: int = 0x45, origen: str | None = None) -> dict:
        datos = hashlib.sha256(self.rp_id.encode()).digest() + bytes([flags]) + struct.pack(">I", self.contador)
        datos += bytes(16) + struct.pack(">H", len(self.id)) + self.id + self._cose()
        objeto = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": datos})
        return {
            "id": b64u(self.id), "rawId": b64u(self.id), "type": "public-key", "clientExtensionResults": {},
            "response": {
                "clientDataJSON": b64u(self._cliente("webauthn.create", desafio_b64, origen)),
                "attestationObject": b64u(objeto), "transports": ["internal"],
            },
        }

    def ingresar(self, desafio_b64: str, *, flags: int = 0x05, contador: int | None = None, origen: str | None = None) -> dict:
        self.contador = self.contador + 1 if contador is None else contador
        datos = hashlib.sha256(self.rp_id.encode()).digest() + bytes([flags]) + struct.pack(">I", self.contador)
        cliente = self._cliente("webauthn.get", desafio_b64, origen)
        firma = self.clave.sign(datos + hashlib.sha256(cliente).digest(), ec.ECDSA(hashes.SHA256()))
        return {
            "id": b64u(self.id), "rawId": b64u(self.id), "type": "public-key", "clientExtensionResults": {},
            "response": {
                "clientDataJSON": b64u(cliente), "authenticatorData": b64u(datos),
                "signature": b64u(firma), "userHandle": None,
            },
        }
