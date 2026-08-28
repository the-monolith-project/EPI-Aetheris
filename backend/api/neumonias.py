"""
Endpoints descriptivos de Neumonías (ADR 0011 + catálogo 'neumonia').

No es un módulo de Camino Ancho. Capa 100% descriptiva: conteo semanal
'notificado' por departamento. Huecos = ausencia de fila, nunca cero.
"""

from __future__ import annotations

from collections import defaultdict

ANIOS_NEUMONIAS = [2018, 2019, 2021, 2022, 2023]

AVISO_HONESTIDAD_NEUMONIAS = (
    "Neumonías, boletines MINSAL 2018-2023 (sin 2020 en el corpus). Capa DESCRIPTIVA "
    "-- conteo semanal 'notificado' por departamento, sin split probable/confirmado "
    "(ADR 0011). No hay idoneidad, anomalía ni presión calculadas para neumonías. "
    "Los huecos son ausencias reales de la fuente (vacaciones, tabla-imagen, "
    "correcciones retroactivas excluidas), nunca ceros interpolados. Fuente: MINSAL PDF."
)


def cargar_neumonias_departamental(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                r.nombre,
                r.codigo,
                sum(c.conteo) AS notificado_total,
                count(*) AS semanas_con_dato,
                min(c.anio) AS primer_anio,
                max(c.anio) AS ultimo_anio
            FROM regiones r
            LEFT JOIN casos_epidemiologicos c
                ON c.region_id = r.id
                AND c.clasificacion = 'notificado'
                AND c.tipo_evento_id = (SELECT id FROM tipos_evento WHERE codigo = 'neumonia')
            WHERE r.nivel_admin = 1
            GROUP BY r.nombre, r.codigo
            ORDER BY r.nombre
            """
        )
        filas = cur.fetchall()
    return [
        {
            "nombre": nombre,
            "codigo": codigo,
            "notificado_total": int(notificado_total) if notificado_total is not None else 0,
            "semanas_con_dato": int(semanas_con_dato) if semanas_con_dato is not None else 0,
            "primer_anio": primer_anio,
            "ultimo_anio": ultimo_anio,
        }
        for nombre, codigo, notificado_total, semanas_con_dato, primer_anio, ultimo_anio in filas
    ]


def cargar_neumonias_departamento_temporal(conn, codigo: str) -> dict[int, dict[int, float]] | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, nombre FROM regiones WHERE nivel_admin = 1 AND codigo = %s",
            (codigo,),
        )
        fila_region = cur.fetchone()
        if fila_region is None:
            return None
        region_id, _nombre = fila_region
        cur.execute(
            """
            SELECT anio, semana_epi, conteo
            FROM casos_epidemiologicos
            WHERE region_id = %s AND clasificacion = 'notificado'
              AND tipo_evento_id = (SELECT id FROM tipos_evento WHERE codigo = 'neumonia')
            ORDER BY anio, semana_epi
            """,
            (region_id,),
        )
        filas = cur.fetchall()
    serie: dict[int, dict[int, float]] = defaultdict(dict)
    for anio, semana, conteo in filas:
        serie[anio][semana] = float(conteo)
    return dict(serie)


def cargar_heatmap_neumonias(conn, anio: int) -> list[dict]:
    """Matriz departamento × semana de un año. Semana sin fila = None, nunca 0."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.nombre, r.codigo, c.semana_epi, c.conteo
            FROM regiones r
            LEFT JOIN casos_epidemiologicos c
                ON c.region_id = r.id
                AND c.clasificacion = 'notificado'
                AND c.tipo_evento_id = (SELECT id FROM tipos_evento WHERE codigo = 'neumonia')
                AND c.anio = %s
            WHERE r.nivel_admin = 1
            ORDER BY r.nombre, c.semana_epi
            """,
            (anio,),
        )
        filas = cur.fetchall()
    por_depto: dict[str, dict] = {}
    for nombre, codigo, semana, conteo in filas:
        celda = por_depto.setdefault(
            codigo,
            {"nombre": nombre, "codigo": codigo, "semanas": {str(s): None for s in range(1, 53)}},
        )
        if semana is not None:
            celda["semanas"][str(int(semana))] = int(conteo)
    return list(por_depto.values())
