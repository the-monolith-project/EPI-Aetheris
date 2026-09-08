"""Consulta y escritura de alertas de campo (ADR 0013, ADR 0015).

Las filas las redacta el equipo de vigilancia. No se calculan desde
M1/M2/M3 ni desde el clasificador retirado.
"""

from __future__ import annotations

import os
import secrets
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

TIPOS_ALERTA = ("dengue", "respiratorio")
NIVELES_ALERTA = ("informativo", "atencion", "intensificacion")
ETIQUETAS_ALERTA = ("test", "simulacro", "historica")

AVISO_HONESTIDAD_ALERTAS = (
    "Alertas redactadas por el equipo de vigilancia del proyecto (INSAMT, Equipo 4) "
    "a partir de datos públicos históricos (MINSAL, OpenDengue, Open-Meteo). No "
    "reemplazan los lineamientos del MINSAL ni el criterio clínico."
)

_COLUMNAS = (
    "id, tipo, nivel, titulo, contexto, indicaciones, fuente, autor, "
    "vigente_desde, vigente_hasta, activa, etiqueta, "
    "signos_alarma, criterios_referencia, que_notificar, "
    "definicion_caso, contacto_vigilancia"
)

_CAMPOS_CLINICOS = (
    "signos_alarma",
    "criterios_referencia",
    "que_notificar",
    "definicion_caso",
    "contacto_vigilancia",
)

_CAMPOS_ESCRITURA = (
    "tipo",
    "nivel",
    "titulo",
    "contexto",
    "indicaciones",
    "fuente",
    "autor",
    "vigente_desde",
    "vigente_hasta",
    "activa",
    "etiqueta",
    *_CAMPOS_CLINICOS,
)


def _iso(valor: date | None) -> str | None:
    if valor is None:
        return None
    return valor.isoformat()


def _fila_publica(fila: tuple) -> dict:
    (
        ident,
        tipo,
        nivel,
        titulo,
        contexto,
        indicaciones,
        fuente,
        autor,
        vigente_desde,
        vigente_hasta,
        activa,
        etiqueta,
        signos_alarma,
        criterios_referencia,
        que_notificar,
        definicion_caso,
        contacto_vigilancia,
    ) = fila
    return {
        "id": int(ident),
        "tipo": tipo,
        "nivel": nivel,
        "titulo": titulo,
        "contexto": contexto,
        "indicaciones": indicaciones,
        "fuente": fuente,
        "autor": autor,
        "vigente_desde": _iso(vigente_desde),
        "vigente_hasta": _iso(vigente_hasta),
        "activa": bool(activa),
        "etiqueta": etiqueta,
        # Campos clínicos opcionales (ADR 0014). NULL en BD -> None en el JSON;
        # el frontend omite el bloque cuando el valor es None.
        "signos_alarma": signos_alarma,
        "criterios_referencia": criterios_referencia,
        "que_notificar": que_notificar,
        "definicion_caso": definicion_caso,
        "contacto_vigilancia": contacto_vigilancia,
    }


def _etiqueta_normalizada(valor: str | None) -> str | None:
    if valor is None:
        return None
    recortada = valor.strip()
    if recortada == "":
        return None
    return recortada


class AlertaCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: str
    nivel: str
    titulo: str
    contexto: str
    indicaciones: str
    fuente: str
    autor: str
    vigente_desde: date
    vigente_hasta: date | None = None
    activa: bool = True
    etiqueta: str | None = None
    signos_alarma: str | None = None
    criterios_referencia: str | None = None
    que_notificar: str | None = None
    definicion_caso: str | None = None
    contacto_vigilancia: str | None = None

    @field_validator("tipo")
    @classmethod
    def _tipo(cls, valor: str) -> str:
        if valor not in TIPOS_ALERTA:
            raise ValueError("tipo debe ser dengue o respiratorio")
        return valor

    @field_validator("nivel")
    @classmethod
    def _nivel(cls, valor: str) -> str:
        if valor not in NIVELES_ALERTA:
            raise ValueError(
                "nivel debe ser informativo, atencion o intensificacion"
            )
        return valor

    @field_validator("etiqueta")
    @classmethod
    def _etiqueta(cls, valor: str | None) -> str | None:
        normalizada = _etiqueta_normalizada(valor)
        if normalizada is None:
            return None
        if normalizada not in ETIQUETAS_ALERTA:
            raise ValueError("etiqueta debe ser test, simulacro o historica")
        return normalizada

    @field_validator(
        "titulo", "contexto", "indicaciones", "fuente", "autor"
    )
    @classmethod
    def _no_vacio(cls, valor: str) -> str:
        recortado = valor.strip()
        if not recortado:
            raise ValueError("el campo es obligatorio")
        return recortado


class AlertaParche(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: str | None = None
    nivel: str | None = None
    titulo: str | None = None
    contexto: str | None = None
    indicaciones: str | None = None
    fuente: str | None = None
    autor: str | None = None
    vigente_desde: date | None = None
    vigente_hasta: date | None = None
    activa: bool | None = None
    etiqueta: str | None = Field(default=None)
    signos_alarma: str | None = None
    criterios_referencia: str | None = None
    que_notificar: str | None = None
    definicion_caso: str | None = None
    contacto_vigilancia: str | None = None

    @field_validator("tipo")
    @classmethod
    def _tipo(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        if valor not in TIPOS_ALERTA:
            raise ValueError("tipo debe ser dengue o respiratorio")
        return valor

    @field_validator("nivel")
    @classmethod
    def _nivel(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        if valor not in NIVELES_ALERTA:
            raise ValueError(
                "nivel debe ser informativo, atencion o intensificacion"
            )
        return valor

    @field_validator("etiqueta")
    @classmethod
    def _etiqueta(cls, valor: str | None) -> str | None:
        normalizada = _etiqueta_normalizada(valor)
        if normalizada is None:
            return None
        if normalizada not in ETIQUETAS_ALERTA:
            raise ValueError("etiqueta debe ser test, simulacro o historica")
        return normalizada


def extraer_bearer(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    partes = authorization.split(None, 1)
    if len(partes) != 2 or partes[0].lower() != "bearer":
        return None
    token = partes[1].strip()
    return token or None


def comprobar_token_escritura(authorization: str | None) -> tuple[int, str] | None:
    """None si autorizado; si no, (status, detail). Lee el env en cada llamada."""
    esperado = os.environ.get("ALERTAS_TOKEN") or ""
    if esperado.strip() == "":
        return (
            503,
            "Escritura de alertas no configurada (ALERTAS_TOKEN ausente).",
        )
    recibido = extraer_bearer(authorization)
    if recibido is None:
        return (401, "No autenticado")
    try:
        coincide = secrets.compare_digest(recibido, esperado)
    except (TypeError, ValueError):
        coincide = False
    if not coincide:
        return (401, "No autenticado")
    return None


def listar_alertas(
    conn,
    tipo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    incluir_inactivas: bool = False,
    incluir_etiquetadas: bool = False,
) -> list[dict]:
    """Lista alertas con filtros opcionales combinados con AND.

    Por defecto: activa=TRUE y etiqueta IS NULL (contrato público de ADR 0013).
    `tipo` ya debe ser None o un valor de TIPOS_ALERTA.
    `desde`/`hasta` filtran por solapamiento con la vigencia, no por igualdad.
    """
    sql = f"""
        SELECT {_COLUMNAS}
        FROM alertas
        WHERE TRUE
    """
    params: list = []
    if not incluir_inactivas:
        sql += " AND activa = TRUE"
    if not incluir_etiquetadas:
        sql += " AND etiqueta IS NULL"
    if tipo is not None:
        sql += " AND tipo = %s"
        params.append(tipo)
    if desde is not None:
        sql += " AND (vigente_hasta IS NULL OR vigente_hasta >= %s)"
        params.append(desde)
    if hasta is not None:
        sql += " AND vigente_desde <= %s"
        params.append(hasta)
    sql += " ORDER BY vigente_desde DESC, id DESC"

    with conn.cursor() as cur:
        cur.execute(sql, tuple(params))
        filas = cur.fetchall()
    return [_fila_publica(fila) for fila in filas]


def listar_alertas_activas(conn, tipo: str | None = None) -> list[dict]:
    """Filas con activa=TRUE y sin etiqueta. Conserva el contrato de ADR 0013."""
    return listar_alertas(conn, tipo=tipo)


def leer_ultima_revision(conn) -> str | None:
    """Fecha de la revisión más reciente del equipo (incluye inactivas)."""
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(vigente_desde) FROM alertas")
        (valor,) = cur.fetchone()
    return _iso(valor)


def consultar_alertas_publicas(
    conn,
    tipo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    incluir_inactivas: bool = False,
    incluir_etiquetadas: bool = False,
) -> dict:
    """Cuerpo del GET público: aviso, última revisión y lista filtrada."""
    return {
        "aviso": AVISO_HONESTIDAD_ALERTAS,
        "ultima_revision": leer_ultima_revision(conn),
        "alertas": listar_alertas(
            conn,
            tipo=tipo,
            desde=desde,
            hasta=hasta,
            incluir_inactivas=incluir_inactivas,
            incluir_etiquetadas=incluir_etiquetadas,
        ),
    }


def _leer_por_id(conn, ident: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {_COLUMNAS} FROM alertas WHERE id = %s",
            (ident,),
        )
        fila = cur.fetchone()
    if fila is None:
        return None
    return _fila_publica(fila)


def crear_alerta(conn, cuerpo: AlertaCrear) -> dict:
    columnas = [
        "tipo",
        "nivel",
        "titulo",
        "contexto",
        "indicaciones",
        "fuente",
        "autor",
        "vigente_desde",
        "vigente_hasta",
        "activa",
        "etiqueta",
        *_CAMPOS_CLINICOS,
    ]
    valores = [getattr(cuerpo, col) for col in columnas]
    placeholders = ", ".join(["%s"] * len(columnas))
    nombres = ", ".join(columnas)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO alertas ({nombres})
            VALUES ({placeholders})
            RETURNING {_COLUMNAS}
            """,
            tuple(valores),
        )
        fila = cur.fetchone()
    return _fila_publica(fila)


def parchear_alerta(conn, ident: int, cuerpo: AlertaParche) -> dict | None:
    datos = cuerpo.model_dump(exclude_unset=True)
    if not datos:
        return _leer_por_id(conn, ident)
    asignaciones = []
    valores = []
    for campo, valor in datos.items():
        if campo not in _CAMPOS_ESCRITURA:
            continue
        asignaciones.append(f"{campo} = %s")
        valores.append(valor)
    if not asignaciones:
        return _leer_por_id(conn, ident)
    valores.append(ident)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE alertas
            SET {", ".join(asignaciones)}
            WHERE id = %s
            RETURNING {_COLUMNAS}
            """,
            tuple(valores),
        )
        fila = cur.fetchone()
    if fila is None:
        return None
    return _fila_publica(fila)
