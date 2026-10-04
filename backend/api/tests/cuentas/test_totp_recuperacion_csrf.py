import pyotp
import pytest

from api.cuentas import csrf, recuperacion, totp


def test_cifrado_ida_y_vuelta(config):
    secreto = totp.nuevo_secreto()
    datos, version = totp.cifrar(config, secreto, "u-1")
    assert secreto.encode() not in datos
    assert totp.descifrar(config, datos, version, "u-1") == secreto


def test_cifrado_ligado_al_usuario(config):
    datos, version = totp.cifrar(config, totp.nuevo_secreto(), "u-1")
    with pytest.raises(ValueError):
        totp.descifrar(config, datos, version, "u-2")


def test_cifrado_manipulado(config):
    datos, version = totp.cifrar(config, totp.nuevo_secreto(), "u-1")
    roto = bytearray(datos)
    roto[-1] ^= 1
    with pytest.raises(ValueError):
        totp.descifrar(config, bytes(roto), version, "u-1")


def test_totp_acepta_y_no_repite():
    secreto = totp.nuevo_secreto()
    ahora = 1_800_000_000.0
    codigo = pyotp.TOTP(secreto).at(ahora)
    paso = totp.verificar(secreto, codigo, None, ahora)
    assert paso == int(ahora // 30)
    assert totp.verificar(secreto, codigo, paso, ahora) is None


def test_totp_tolera_un_paso_y_no_dos():
    secreto = totp.nuevo_secreto()
    ahora = 1_800_000_000.0
    assert totp.verificar(secreto, pyotp.TOTP(secreto).at(ahora - 30), None, ahora) is not None
    assert totp.verificar(secreto, pyotp.TOTP(secreto).at(ahora - 90), None, ahora) is None


@pytest.mark.parametrize("codigo", ["", "12345", "1234567", "abcdef", "12 34"])
def test_totp_formato_invalido(codigo):
    assert totp.verificar(totp.nuevo_secreto(), codigo, None) is None


def test_qr_es_svg(config):
    uri = totp.uri_aprovisionamiento(config, totp.nuevo_secreto(), "a@b.org")
    assert uri.startswith("otpauth://totp/")
    assert "<svg" in totp.qr_svg(uri)


def test_recuperacion_un_solo_uso(conn, crear_usuario):
    uid = crear_usuario()
    codigos = recuperacion.generar_lote(conn, uid)
    assert len(codigos) == 10 and len(set(codigos)) == 10
    assert recuperacion.consumir(conn, uid, codigos[0].lower())
    assert not recuperacion.consumir(conn, uid, codigos[0])
    assert recuperacion.restantes(conn, uid) == 9


def test_recuperacion_nuevo_lote_invalida_el_anterior(conn, crear_usuario):
    uid = crear_usuario()
    viejos = recuperacion.generar_lote(conn, uid)
    recuperacion.generar_lote(conn, uid)
    assert not recuperacion.consumir(conn, uid, viejos[1])


def test_recuperacion_no_sirve_para_otra_persona(conn, crear_usuario):
    a, b = crear_usuario(), crear_usuario()
    codigos = recuperacion.generar_lote(conn, a)
    assert not recuperacion.consumir(conn, b, codigos[0])


def test_csrf(config):
    t = csrf.token_para_sesion(config, "sesion-1")
    assert csrf.token_valido(config, "sesion-1", t)
    assert not csrf.token_valido(config, "sesion-2", t)
    assert not csrf.token_valido(config, "sesion-1", None)
    assert not csrf.token_valido(config, "sesion-1", "x" * 64)


def test_origen(config):
    assert csrf.origen_valido(config, "https://epi-aetheris.dev")
    assert csrf.origen_valido(config, "https://epi-aetheris.dev/")
    assert not csrf.origen_valido(config, None)
    assert not csrf.origen_valido(config, "https://epi-aetheris.dev.evil.example")
    assert not csrf.origen_valido(config, "http://epi-aetheris.dev")
