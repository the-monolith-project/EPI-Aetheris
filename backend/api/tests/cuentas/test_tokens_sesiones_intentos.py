from datetime import datetime, timedelta, timezone

from api.cuentas import intentos, sesiones, tokens


# --- tokens de un solo uso -------------------------------------------------

def test_token_se_consume_una_vez(conn, crear_usuario):
    uid = crear_usuario()
    t = tokens.emitir(conn, proposito="restablecer_clave", usuario_id=uid, caduca_s=1800)
    assert tokens.consumir(conn, proposito="restablecer_clave", token=t).usuario_id == uid
    assert tokens.consumir(conn, proposito="restablecer_clave", token=t) is None


def test_token_de_otro_proposito_no_sirve(conn, crear_usuario):
    uid = crear_usuario()
    t = tokens.emitir(conn, proposito="restablecer_clave", usuario_id=uid, caduca_s=1800)
    assert tokens.consumir(conn, proposito="verificar_correo", token=t) is None


def test_token_caducado(conn, crear_usuario):
    uid = crear_usuario()
    t = tokens.emitir(conn, proposito="restablecer_clave", usuario_id=uid, caduca_s=-1)
    assert tokens.consumir(conn, proposito="restablecer_clave", token=t) is None


def test_token_nuevo_deja_sin_efecto_al_anterior(conn, crear_usuario):
    uid = crear_usuario()
    viejo = tokens.emitir(conn, proposito="restablecer_clave", usuario_id=uid, caduca_s=1800)
    nuevo = tokens.emitir(conn, proposito="restablecer_clave", usuario_id=uid, caduca_s=1800)
    assert tokens.consumir(conn, proposito="restablecer_clave", token=viejo) is None
    assert tokens.consumir(conn, proposito="restablecer_clave", token=nuevo) is not None


def test_token_no_se_guarda_en_claro(conn, crear_usuario):
    uid = crear_usuario()
    t = tokens.emitir(conn, proposito="restablecer_clave", usuario_id=uid, caduca_s=1800)
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM tokens_un_solo_uso WHERE encode(token_hash, 'escape') LIKE %s", (f"%{t}%",))
        assert cur.fetchone()[0] == 0


# --- sesiones ----------------------------------------------------------------

def _crear(conn, config, uid, **kw):
    kw.setdefault("nivel", "completo")
    kw.setdefault("metodos", ["clave", "totp"])
    return sesiones.crear(conn, config, usuario_id=uid, **kw)


def test_sesion_ida_y_vuelta(conn, config, crear_usuario):
    uid = crear_usuario(roles=("publicador",))
    token, sid = _crear(conn, config, uid)
    s = sesiones.obtener(conn, config, token)
    assert s.id == sid and s.usuario_id == uid
    assert s.roles == {"publicador"} and s.nivel == "completo"


def test_sesion_token_desconocido_o_vacio(conn, config):
    assert sesiones.obtener(conn, config, "no-existe") is None
    assert sesiones.obtener(conn, config, None) is None


def test_sesion_no_guarda_el_token(conn, config, crear_usuario):
    uid = crear_usuario()
    token, _ = _crear(conn, config, uid)
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM sesiones WHERE encode(token_hash, 'escape') LIKE %s", (f"%{token}%",))
        assert cur.fetchone()[0] == 0


def test_sesion_inactividad_publica_y_admin(conn, config, crear_usuario):
    pub, adm = crear_usuario(roles=("publicador",)), crear_usuario(roles=("administrador",))
    tp, sp = _crear(conn, config, pub)
    ta, sa = _crear(conn, config, adm)
    hace_15 = datetime.now(timezone.utc) - timedelta(minutes=15)
    with conn.cursor() as cur:
        cur.execute("UPDATE sesiones SET ultima_actividad_en = %s WHERE id IN (%s, %s)", (hace_15, sp, sa))
    assert sesiones.obtener(conn, config, tp) is not None  # límite público: 20 min
    assert sesiones.obtener(conn, config, ta) is None  # límite admin: 10 min


def test_sesion_vida_absoluta(conn, config, crear_usuario):
    uid = crear_usuario()
    token, sid = _crear(conn, config, uid)
    with conn.cursor() as cur:
        cur.execute("UPDATE sesiones SET caduca_absoluta_en = now() - interval '1 second' WHERE id = %s", (sid,))
    assert sesiones.obtener(conn, config, token) is None


def test_sesion_de_cuenta_suspendida(conn, config, crear_usuario):
    uid = crear_usuario()
    token, _ = _crear(conn, config, uid)
    with conn.cursor() as cur:
        cur.execute("UPDATE usuarios SET estado = 'suspendido' WHERE id = %s", (uid,))
    assert sesiones.obtener(conn, config, token) is None


def test_rotar_invalida_el_token_anterior_y_promueve(conn, config, crear_usuario):
    uid = crear_usuario(roles=("revisor",))
    token, sid = _crear(conn, config, uid, nivel="segundo_factor", metodos=["clave"])
    nuevo = sesiones.rotar(conn, config, sid, nivel="completo", agregar_metodo="totp", reautenticar=True)
    assert sesiones.obtener(conn, config, token) is None
    s = sesiones.obtener(conn, config, nuevo)
    assert s.nivel == "completo" and s.metodos == ("clave", "totp")
    assert sesiones.reautenticada(s, config, datetime.now(timezone.utc))
    # La sesión intermedia vivía 5 min; al promoverla recupera la vida de una completa.
    with conn.cursor() as cur:
        cur.execute("SELECT caduca_absoluta_en > now() + interval '1 hour' FROM sesiones WHERE id = %s", (sid,))
        assert cur.fetchone()[0]


def test_limite_de_sesiones_cierra_las_mas_antiguas(conn, config, crear_usuario):
    uid = crear_usuario()
    emitidas = []
    for _ in range(config.max_sesiones + 2):
        emitidas.append(_crear(conn, config, uid)[0])
    vivas = [t for t in emitidas if sesiones.obtener(conn, config, t) is not None]
    assert len(vivas) == config.max_sesiones
    assert emitidas[0] not in vivas and emitidas[1] not in vivas


def test_revocar_todas_con_excepcion(conn, config, crear_usuario):
    uid = crear_usuario()
    t1, s1 = _crear(conn, config, uid)
    t2, _ = _crear(conn, config, uid)
    assert sesiones.revocar_todas(conn, uid, "cambio_de_clave", excepto=s1) == 1
    assert sesiones.obtener(conn, config, t1) is not None
    assert sesiones.obtener(conn, config, t2) is None


def test_sin_reautenticacion_reciente(conn, config, crear_usuario):
    uid = crear_usuario()
    token, _ = _crear(conn, config, uid)
    assert not sesiones.reautenticada(sesiones.obtener(conn, config, token), config, datetime.now(timezone.utc))


# --- intentos de ingreso ----------------------------------------------------

def test_bloqueo_tras_el_maximo_de_fallos(conn, config):
    k = intentos.clave(config, "correo", "Alguien@Ejemplo.org")
    assert intentos.segundos_de_espera(config, conn, k) == 0
    for _ in range(config.max_fallos_cuenta - 1):
        intentos.registrar_fallo(config, conn, k)
    assert intentos.segundos_de_espera(config, conn, k) == 0
    intentos.registrar_fallo(config, conn, k)
    assert intentos.segundos_de_espera(config, conn, k) > 0


def test_la_clave_no_distingue_mayusculas(config):
    assert intentos.clave(config, "correo", "A@x.org") == intentos.clave(config, "correo", "a@X.org")
    assert intentos.clave(config, "correo", "a@x.org") != intentos.clave(config, "ip", "a@x.org")


def test_limpiar_levanta_el_bloqueo(conn, config):
    k = intentos.clave(config, "correo", "otro@ejemplo.org")
    for _ in range(config.max_fallos_cuenta):
        intentos.registrar_fallo(config, conn, k)
    intentos.limpiar(conn, k)
    assert intentos.segundos_de_espera(config, conn, k) == 0
