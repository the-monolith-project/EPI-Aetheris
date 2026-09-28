"""
Series nacionales de IRA y neumonías del tablero de MINSAL (ADR 0021).

Conteo semanal notificado de todo el país desde 2025-S1, cargado desde
capturas del tablero con `clasificacion = 'notificado'` (ADR 0011). El tablero
no publica datos por departamento, así que estas series no se cruzan con las
departamentales de los boletines (2018-2023).

Tampoco se empalman con la suma de los departamentos de los boletines: muchas
semanas no traen los 14 departamentos, y en neumonías esa suma promedia 500-780
por semana según el año, frente a 130-430 en el tablero, sin que se haya
comprobado si es la misma definición. Una semana sin fila (la 53 de 2025) es
una semana que el tablero no publicó, nunca un cero.
"""

from __future__ import annotations

# Nombre del evento en la URL -> tipos_evento.codigo
EVENTOS_TABLERO = {"ira": "ira", "neumonias": "neumonia"}

AVISO_TABLERO_RESPIRATORIO = (
    "Conteo semanal notificado en todo el país según el tablero de MINSAL, "
    "desde 2025. El tablero publica cada semana como un promedio de varias. "
    "Las semanas que no publica quedan sin dato."
)

MOTIVO_TABLERO_AUSENTE = (
    "La serie nacional del tablero de MINSAL no está cargada en este despliegue."
)


def cargar_serie_tablero_nacional(conn, tipo_evento: str) -> list[dict]:
    """Semanas del tablero para `tipo_evento` ('ira' o 'neumonia'), en orden.
    Lista vacía si no hay capturas cargadas."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.fecha_inicio, c.anio, c.semana_epi, c.conteo
            FROM casos_epidemiologicos c
            JOIN regiones r ON r.id = c.region_id
            JOIN tipos_evento t ON t.id = c.tipo_evento_id
            JOIN fuentes_datos f ON f.id = c.fuente_id
            JOIN semanas_epidemiologicas s
                ON s.anio = c.anio AND s.semana_epi = c.semana_epi
            WHERE r.codigo = 'SV'
              AND t.codigo = %s
              AND c.clasificacion = 'notificado'
              AND f.codigo = 'minsal_tablero'
            ORDER BY c.anio, c.semana_epi
            """,
            (tipo_evento,),
        )
        filas = cur.fetchall()

    return [
        {
            "semana_inicio": fecha_inicio.isoformat(),
            "anio": anio,
            "semana_epi": semana_epi,
            "conteo": conteo,
        }
        for fecha_inicio, anio, semana_epi, conteo in filas
    ]
