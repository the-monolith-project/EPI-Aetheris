import pytest

from api.cuentas import llaves, servicio, sesiones
from api.cuentas.servicio import ErrorCuentas

from .autenticador import Autenticador
from .test_servicio import CLAVE, _aceptar, _admin_sesion, _invitar


@pytest.fixture
def llave(config):
    return Autenticador(config.rp_id, config.origen_canonico)


def _administrador_en_alta(conn, config, crear_usuario):
    admin = _admin_sesion(conn, config, crear_usuario)
    _, token, _ = _invitar(conn, config, admin, correo="ana.admin@ejemplo.org", roles=("administrador",))
    _, sesion = _aceptar(conn, config, token, nombre_visible="Ana Admin")
    return sesion


def _registrar(conn, config, sesion, llave, **kw):
    opciones = llaves.opciones_registro(conn, config, sesion)
    return llaves.verificar_registro(conn, config, sesion, llave.registrar(opciones["challenge"], **kw), "Llave de la oficina")


def test_administrador_se_activa_con_llave(conn, config, crear_usuario, llave):
    sesion = _administrador_en_alta(conn, config, crear_usuario)
    resultado = _registrar(conn, config, sesion, llave)
    assert resultado["activada"] and len(resultado["codigos_recuperacion"]) == 10
    nuevo = servicio.promover_alta(conn, config, sesion)
    assert sesiones.obtener(conn, config, nuevo).nivel == "completo"


def test_opciones_exigen_verificacion_de_usuario(conn, config, crear_usuario):
    sesion = _administrador_en_alta(conn, config, crear_usuario)
    opciones = llaves.opciones_registro(conn, config, sesion)
    assert opciones["authenticatorSelection"]["userVerification"] == "required"
    assert opciones["attestation"] == "none" and opciones["rp"]["id"] == config.rp_id


def test_registro_sin_verificacion_de_usuario_se_rechaza(conn, config, crear_usuario, llave):
    sesion = _administrador_en_alta(conn, config, crear_usuario)
    with pytest.raises(ErrorCuentas) as e:
        _registrar(conn, config, sesion, llave, flags=0x41)  # presencia sin UV
    assert e.value.codigo == "llave_invalida"


def test_registro_con_otro_origen_se_rechaza(conn, config, crear_usuario, llave):
    sesion = _administrador_en_alta(conn, config, crear_usuario)
    with pytest.raises(ErrorCuentas):
        _registrar(conn, config, sesion, llave, origen="https://epi-aetheris.dev.evil.example")


def test_el_desafio_vale_una_vez(conn, config, crear_usuario, llave):
    sesion = _administrador_en_alta(conn, config, crear_usuario)
    opciones = llaves.opciones_registro(conn, config, sesion)
    credencial = llave.registrar(opciones["challenge"])
    llaves.verificar_registro(conn, config, sesion, credencial, "x")
    with pytest.raises(ErrorCuentas) as e:
        llaves.verificar_registro(conn, config, sesion, credencial, "x")
    assert e.value.codigo == "desafio_invalido"


def test_desafio_caducado(conn, config, crear_usuario, llave):
    sesion = _administrador_en_alta(conn, config, crear_usuario)
    opciones = llaves.opciones_registro(conn, config, sesion)
    with conn.cursor() as cur:
        cur.execute("UPDATE desafios SET caduca_en = now() - interval '1 second'")
    with pytest.raises(ErrorCuentas) as e:
        llaves.verificar_registro(conn, config, sesion, llave.registrar(opciones["challenge"]), "x")
    assert e.value.codigo == "desafio_invalido"


def test_la_misma_llave_no_se_registra_dos_veces(conn, config, crear_usuario, llave):
    sesion = _administrador_en_alta(conn, config, crear_usuario)
    _registrar(conn, config, sesion, llave)
    with pytest.raises(ErrorCuentas) as e:
        _registrar(conn, config, sesion, llave)
    assert e.value.codigo == "llave_repetida"


def _con_llave(conn, config, crear_usuario, llave):
    sesion = _administrador_en_alta(conn, config, crear_usuario)
    _registrar(conn, config, sesion, llave)
    servicio.promover_alta(conn, config, sesion)
    sesiones.revocar_todas(conn, sesion.usuario_id, "prueba")
    return sesion


def _segundo_paso(conn, config):
    _, s = servicio.ingresar(conn, config, correo="ana.admin@ejemplo.org", contrasena=CLAVE, ip=None, agente=None)
    return s


def test_ingreso_con_llave(conn, config, crear_usuario, llave):
    _con_llave(conn, config, crear_usuario, llave)
    s = _segundo_paso(conn, config)
    opciones = llaves.opciones_ingreso(conn, config, s)
    assert opciones["userVerification"] == "required" and len(opciones["allowCredentials"]) == 1
    nuevo = llaves.verificar_ingreso(conn, config, s, llave.ingresar(opciones["challenge"]))
    final = sesiones.obtener(conn, config, nuevo)
    assert final.nivel == "completo" and final.usa_llave


def test_ingreso_con_contador_que_no_avanza_se_rechaza(conn, config, crear_usuario, llave):
    _con_llave(conn, config, crear_usuario, llave)
    s = _segundo_paso(conn, config)
    o = llaves.opciones_ingreso(conn, config, s)
    llaves.verificar_ingreso(conn, config, s, llave.ingresar(o["challenge"], contador=5))
    s2 = _segundo_paso(conn, config)
    o2 = llaves.opciones_ingreso(conn, config, s2)
    with pytest.raises(ErrorCuentas):  # contador 3 < 5: posible llave clonada
        llaves.verificar_ingreso(conn, config, s2, llave.ingresar(o2["challenge"], contador=3))


def test_ingreso_con_llave_ajena(conn, config, crear_usuario, llave):
    _con_llave(conn, config, crear_usuario, llave)
    s = _segundo_paso(conn, config)
    o = llaves.opciones_ingreso(conn, config, s)
    intrusa = Autenticador(config.rp_id, config.origen_canonico)
    with pytest.raises(ErrorCuentas) as e:
        llaves.verificar_ingreso(conn, config, s, intrusa.ingresar(o["challenge"]))
    assert e.value.codigo == "llave_invalida"


def test_ingreso_sin_verificacion_de_usuario(conn, config, crear_usuario, llave):
    _con_llave(conn, config, crear_usuario, llave)
    s = _segundo_paso(conn, config)
    o = llaves.opciones_ingreso(conn, config, s)
    with pytest.raises(ErrorCuentas):
        llaves.verificar_ingreso(conn, config, s, llave.ingresar(o["challenge"], flags=0x01))


def test_opciones_de_ingreso_fuera_del_paso(conn, config, crear_usuario):
    admin = _admin_sesion(conn, config, crear_usuario)
    _, token, _ = _invitar(conn, config, admin)
    _, sesion = _aceptar(conn, config, token)
    with pytest.raises(ErrorCuentas):  # una sesión de alta no está en el paso de segundo factor
        llaves.opciones_ingreso(conn, config, sesion)
