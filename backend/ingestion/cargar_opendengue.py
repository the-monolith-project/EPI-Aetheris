"""
Carga la serie nacional semanal de OpenDengue a casos_epidemiologicos.

Filtra el extracto crudo (backend/ingestion/data/raw/opendengue/) a
resolucion nacional/semanal (S_res='Admin0', T_res='Week') y a
clasificacion='total' (ver docs/adr/0005-clasificacion-total-opendengue.md
-- OpenDengue no separa probable/confirmado, entrega un conteo agregado
distinto de las dos series de laboratorio de MINSAL).

Precondicion: semanas_epidemiologicas debe estar poblada para el rango de
anios cargado (poblar_semanas_epidemiologicas.py). La semana epidemiologica
de cada fila se resuelve por fecha_inicio exacta contra esa tabla, nunca
recalculada aqui -- evita cualquier desfase con lo que ya esta sembrado.

Uso:
    python3 cargar_opendengue.py [--anio-inicio 2018] [--anio-fin 2024]
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from psycopg2.extras import execute_values

from db import get_connection

RAIZ = Path(__file__).parent
CSV_PATH = RAIZ / "data" / "raw" / "opendengue" / "opendengue_el_salvador_v1_3.csv"

ANIO_INICIO_DEFAULT = 2018
ANIO_FIN_DEFAULT = 2024


def leer_serie_nacional_semanal(ruta: Path = CSV_PATH) -> list[tuple[str, int]]:
    """Devuelve [(fecha_inicio_iso, conteo), ...] para S_res=Admin0, T_res=Week.

    No filtra por el campo Year del CSV: ese año es el del calendario, no
    necesariamente el de la semana epidemiologica resuelta (ej. una semana
    que arranca el 29-dic puede pertenecer a la SE01 del anio siguiente). El
    filtro por rango de anios se aplica despues, sobre el anio epidemiologico
    ya resuelto contra semanas_epidemiologicas.
    """
    filas = []
    with open(ruta, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["S_res"] != "Admin0" or row["T_res"] != "Week":
                continue
            if row["case_definition_standardised"] != "Total":
                # No se ha visto otro valor en el corpus filtrado a SLV a esta
                # resolucion -- si aparece uno nuevo no se adivina que hacer.
                raise ValueError(
                    f"case_definition_standardised inesperado: "
                    f"{row['case_definition_standardised']!r} en fila con "
                    f"calendar_start_date={row['calendar_start_date']}"
                )
            filas.append((row["calendar_start_date"], int(row["dengue_total"])))
    return filas


def cargar(anio_inicio: int, anio_fin: int) -> int:
    filas = leer_serie_nacional_semanal()
    print(f"{len(filas)} filas semanales nacionales leidas del CSV (todo el historico disponible).")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM regiones WHERE codigo = 'SV'")
            fila = cur.fetchone()
            if fila is None:
                raise RuntimeError("No existe la region 'SV' (nacional) en la tabla regiones.")
            region_id = fila[0]

            cur.execute("SELECT id FROM tipos_evento WHERE codigo = 'dengue'")
            tipo_evento_id = cur.fetchone()[0]

            cur.execute("SELECT id FROM fuentes_datos WHERE codigo = 'opendengue_v1_3'")
            fuente_id = cur.fetchone()[0]

            cur.execute("SELECT fecha_inicio, anio, semana_epi FROM semanas_epidemiologicas")
            mapa_semanas = {row[0].isoformat(): (row[1], row[2]) for row in cur.fetchall()}

            valores = []
            sin_semana = []
            fuera_de_rango = 0
            for fecha_inicio, conteo in filas:
                semana = mapa_semanas.get(fecha_inicio)
                if semana is None:
                    sin_semana.append(fecha_inicio)
                    continue
                anio_epi, semana_epi = semana
                if not (anio_inicio <= anio_epi <= anio_fin):
                    fuera_de_rango += 1
                    continue
                valores.append((region_id, tipo_evento_id, anio_epi, semana_epi, "total", conteo, fuente_id))

            if sin_semana:
                print(
                    f"AVISO: {len(sin_semana)} filas sin semana epidemiologica resuelta "
                    f"-- ejecutar poblar_semanas_epidemiologicas.py para cubrir ese rango. "
                    f"Ejemplos: {sin_semana[:5]}"
                )
            print(f"{fuera_de_rango} filas resueltas fuera del rango {anio_inicio}-{anio_fin}, descartadas.")

            if not valores:
                print("Nada que insertar.")
                return 0

            execute_values(
                cur,
                """
                INSERT INTO casos_epidemiologicos
                    (region_id, tipo_evento_id, anio, semana_epi, clasificacion, conteo, fuente_id)
                VALUES %s
                ON CONFLICT (region_id, tipo_evento_id, anio, semana_epi, clasificacion, fuente_id)
                DO UPDATE SET conteo = EXCLUDED.conteo, fecha_ingesta = now()
                """,
                valores,
                page_size=len(valores),
            )
            # execute_values pagina en varios INSERT si supera page_size; sin
            # forzar una sola pagina, cur.rowcount solo refleja la ultima
            # pagina ejecutada, no el total (bug detectado probando esta
            # misma carga: 365 filas reales, 65 reportadas = tamano de la
            # ultima pagina de 100).
            insertadas = len(valores)
        conn.commit()
    finally:
        conn.close()

    return insertadas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anio-inicio", type=int, default=ANIO_INICIO_DEFAULT)
    parser.add_argument("--anio-fin", type=int, default=ANIO_FIN_DEFAULT)
    args = parser.parse_args()

    insertadas = cargar(args.anio_inicio, args.anio_fin)
    print(
        f"OK: {insertadas} filas insertadas/actualizadas en casos_epidemiologicos "
        f"(fuente=opendengue_v1_3, clasificacion=total, nivel nacional, {args.anio_inicio}-{args.anio_fin})."
    )


if __name__ == "__main__":
    main()
