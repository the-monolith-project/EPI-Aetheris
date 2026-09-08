"""
Puebla semanas_epidemiologicas con el calendario de semana epidemiologica
PAHO/CDC (MMWR), no ISO 8601 -- ver comentario de la tabla en
db/migrations/0001_init_schema.sql. Ambas tablas de hechos (casos_epidemiologicos,
variables_ambientales) tienen FK compuesta (anio, semana_epi) hacia esta tabla,
asi que debe poblarse antes de cualquier ingesta de casos o clima.

Uso:
    python3 poblar_semanas_epidemiologicas.py [--anio-inicio 2018] [--anio-fin AÑO_EN_CURSO+1]
"""

from __future__ import annotations

import argparse
from datetime import date

from epiweeks import Year
from psycopg2.extras import execute_values

from db import get_connection

ANIO_INICIO_DEFAULT = 2018
# Sigue al calendario real, no un tope fijo: cargar_clima.py usa
# date.today().year como default y resuelve cada dia contra esta tabla; un
# tope hardcodeado deja las fechas del anio nuevo sin semana resuelta (se
# descartan en silencio). El +1 cubre las primeras semanas del anio
# siguiente cuando se corre a fin de diciembre. Poblar un anio futuro de mas
# es inocuo (ON CONFLICT DO NOTHING).
ANIO_FIN_DEFAULT = date.today().year + 1


def generar_calendario(anio_inicio: int, anio_fin: int) -> list[tuple[int, int, date, date]]:
    filas = []
    for anio in range(anio_inicio, anio_fin + 1):
        for w in Year(anio, system="cdc").iterweeks():
            filas.append((anio, w.week, w.startdate(), w.enddate()))
    return filas


def poblar(anio_inicio: int, anio_fin: int) -> int:
    filas = generar_calendario(anio_inicio, anio_fin)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO semanas_epidemiologicas (anio, semana_epi, fecha_inicio, fecha_fin)
                VALUES %s
                ON CONFLICT (anio, semana_epi) DO NOTHING
                """,
                filas,
                page_size=len(filas),
            )
            insertadas = cur.rowcount
        conn.commit()
    finally:
        conn.close()

    return insertadas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anio-inicio", type=int, default=ANIO_INICIO_DEFAULT)
    parser.add_argument("--anio-fin", type=int, default=ANIO_FIN_DEFAULT)
    args = parser.parse_args()

    insertadas = poblar(args.anio_inicio, args.anio_fin)
    print(f"OK: {insertadas} semanas insertadas ({args.anio_inicio}-{args.anio_fin}).")


if __name__ == "__main__":
    main()
