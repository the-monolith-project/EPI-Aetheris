import pytest

from api.cuentas import contrasenas
from api.cuentas.config import ConfigCuentas


def test_hash_y_verificacion(config):
    hash_, version = contrasenas.hashear(config, "una clave bastante larga")
    assert version == 2
    assert hash_.startswith("$argon2id$")
    assert contrasenas.verificar(config, "una clave bastante larga", hash_, version)
    assert not contrasenas.verificar(config, "otra clave bastante larga", hash_, version)


def test_normalizacion_nfkc(config):
    # "ﬁ" (ligadura) y "fi" son la misma contraseña tras NFKC.
    hash_, version = contrasenas.hashear(config, "ﬁnal de la historia")
    assert contrasenas.verificar(config, "final de la historia", hash_, version)


def test_cuenta_inexistente_no_verifica(config):
    assert not contrasenas.verificar(config, "lo que sea que ponga", None, None)


def test_pimienta_desconocida_no_verifica(config):
    hash_, _ = contrasenas.hashear(config, "una clave bastante larga")
    assert not contrasenas.verificar(config, "una clave bastante larga", hash_, 99)


def test_hash_cambia_con_la_pimienta(config):
    hash_, version = contrasenas.hashear(config, "una clave bastante larga")
    otra = ConfigCuentas(
        pimientas={2: b"\x09" * 32}, version_pimienta=2, claves_cifrado=config.claves_cifrado,
        version_cifrado=1, origen_canonico=config.origen_canonico, rp_id=config.rp_id,
    )
    assert not contrasenas.verificar(otra, "una clave bastante larga", hash_, version)


def test_requiere_rehash_si_cambia_la_pimienta_vigente(config):
    hash_, _ = contrasenas.hashear(config, "una clave bastante larga")
    assert contrasenas.requiere_rehash(config, hash_, 1)
    assert not contrasenas.requiere_rehash(config, hash_, 2)


@pytest.mark.parametrize(
    "clave,fragmento",
    [
        ("corta", "al menos 12"),
        ("x" * 129, "no puede pasar de 128"),
        ("aaaaaaaaaaaaaaaa", "repite"),
    ],
)
def test_politica_rechaza(clave, fragmento):
    with pytest.raises(contrasenas.ContrasenaInvalida, match=fragmento):
        contrasenas.validar_politica(clave)


def test_politica_rechaza_datos_personales():
    with pytest.raises(contrasenas.ContrasenaInvalida, match="nombre"):
        contrasenas.validar_politica("MariaLopez-2026-clave", datos_personales=("marialopez",))


def test_politica_acepta_frase_larga():
    assert contrasenas.validar_politica("correcto caballo bateria grapa") == "correcto caballo bateria grapa"


def test_hibp_detecta_sufijo():
    # SHA-1 de "password" = 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
    def consulta(prefijo):
        assert prefijo == "5BAA6"
        return "0000000000000000000000000000000000A:0\r\n1E4C9B93F3F0682250B6CF8331B7EE68FD8:3861493\r\n"

    assert contrasenas.esta_filtrada("password", consulta)


def test_hibp_ignora_relleno():
    def consulta(prefijo):
        return "1E4C9B93F3F0682250B6CF8331B7EE68FD8:0\r\n"

    assert not contrasenas.esta_filtrada("password", consulta)


def test_hibp_sin_servicio_no_bloquea():
    def consulta(prefijo):
        raise TimeoutError

    assert not contrasenas.esta_filtrada("password", consulta)
