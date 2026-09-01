"""
Lectura de cobertura de la ingesta respiratoria.

No es M4 (confianza de vigilancia): no hay fórmula aprobada. Solo cuenta
semanas con fila en Postgres y adjunta las notas ya documentadas en la
exploración de 264 PDF. Hueco ≠ cero.
"""

from __future__ import annotations

ANIOS = [2018, 2019, 2021, 2022, 2023]
SEMANAS_NOMINALES = 52

# Hechos de la corrida exploratoria sobre el corpus congelado 2018-2019 y
# 2021-2023 (docs/exploracion-*-boletines-minsal.md), no umbrales nuevos.
# Si se incorporan 2020 o 2024+, regenerar estas constantes desde esa
# exploración; no reutilizar los recuentos de tablas-imagen / vacaciones.
NOTAS_NEUMONIAS = {
    "tablas_imagen": 25,
    "ausencia_vacacion": 18,
    "sin_texto_extraible": 4,
    "reimpresiones": ["SE34/2019_v2 = SE33/2019 (14 valores idénticos)"],
    "correcciones_negativas_excluidas": 23,
    "cortes_usables_exploracion": {"2018": 46, "2019": 22, "2021": 50, "2022": 48, "2023": 49},
    "fuente_informe": "docs/exploracion-neumonias-boletines-minsal.md",
    "nota_corpus": (
        "Constantes del corpus histórico congelado 2018-2019 y 2021-2023. "
        "Si se incorporan 2020 o 2024+, regenerarlas desde la nueva exploración."
    ),
}
NOTAS_VIRUS = {
    "tablas_imagen": 3,
    "sin_texto_extraible": 5,
    "covid_19_solo_en": 2023,
    "anio_2020_descargado": False,
    "granularidad": "nacional",
    "unidad": "muestras / detecciones / positividad (no casos clínicos)",
    "fuente_informe": "docs/exploracion-vigilancia-virus-boletines-minsal.md",
    "nota_corpus": (
        "Constantes del corpus histórico congelado 2018-2019 y 2021-2023. "
        "Si se incorporan 2020 o 2024+, regenerarlas desde la nueva exploración."
    ),
}
NOTAS_IRA = {
    "fuente_informe": "docs/exploracion-ira-boletines-minsal.md",
    "nota": "Misma ventana 2018-2023 sin 2020; tablas-imagen en 2019 temprana.",
}

AVISO_COBERTURA = (
    "Cobertura descriptiva de lo cargado y de lo que la exploración encontró "
    "en 264 boletines MINSAL. No es un índice de confianza de vigilancia (M4): "
    "esa fórmula no está aprobada. Semanas sin fila son huecos, nunca ceros."
)


def _semanas_por_anio(conn, tipo_codigo: str) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT anio, count(DISTINCT semana_epi)
            FROM casos_epidemiologicos
            WHERE clasificacion = 'notificado'
              AND tipo_evento_id = (SELECT id FROM tipos_evento WHERE codigo = %s)
            GROUP BY anio
            ORDER BY anio
            """,
            (tipo_codigo,),
        )
        return {str(anio): int(n) for anio, n in cur.fetchall()}


def _filas_evento(conn, tipo_codigo: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*)
            FROM casos_epidemiologicos
            WHERE clasificacion = 'notificado'
              AND tipo_evento_id = (SELECT id FROM tipos_evento WHERE codigo = %s)
            """,
            (tipo_codigo,),
        )
        return int(cur.fetchone()[0])


def _virus_por_anio(conn) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT anio, count(DISTINCT semana_epi)
            FROM vigilancia_virus_respiratorios
            GROUP BY anio
            ORDER BY anio
            """
        )
        return {str(anio): int(n) for anio, n in cur.fetchall()}


def cargar_cobertura(conn) -> dict:
    ira = _semanas_por_anio(conn, "ira")
    neu = _semanas_por_anio(conn, "neumonia")
    vir = _virus_por_anio(conn)
    return {
        "aviso": AVISO_COBERTURA,
        "procedencia": "MINSAL, boletines epidemiológicos PDF 2018-2019 y 2021-2023",
        "anios": ANIOS,
        "semanas_nominales_por_anio": SEMANAS_NOMINALES,
        "ira": {
            "filas_cargadas": _filas_evento(conn, "ira"),
            "semanas_con_dato_por_anio": {str(a): ira.get(str(a), 0) for a in ANIOS},
            "notas": NOTAS_IRA,
        },
        "neumonias": {
            "filas_cargadas": _filas_evento(conn, "neumonia"),
            "semanas_con_dato_por_anio": {str(a): neu.get(str(a), 0) for a in ANIOS},
            "notas": NOTAS_NEUMONIAS,
        },
        "virus": {
            "filas_cargadas": _virus_count(conn),
            "semanas_con_dato_por_anio": {str(a): vir.get(str(a), 0) for a in ANIOS},
            "notas": NOTAS_VIRUS,
        },
    }


def _virus_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM vigilancia_virus_respiratorios")
        return int(cur.fetchone()[0])
