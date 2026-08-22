"""
Carga a casos_epidemiologicos el conteo departamental de IRA ya desacumulado
por backend/ingestion/corrida_ira.py (ADR 0011, aceptado 2026-08-22).

Este script SI escribe a Postgres -- distinto de corrida_ira.py, que es
exploratorio y nunca toca la base de datos (misma separacion que
corrida_distribucion.py/minsal/parser.py para dengue). Lee
data/interim/corrida_ira/desacumulado_ira_semanal.csv (generado por
corrida_ira.py, gitignoreado) e inserta solo las filas seguras:

- Excluye toda fila con `nota` no vacia: huecos entre cortes ("sin dato
  semanal", NO se interpola), primeros cortes de cada anio (acumulado
  SE1-SEx, NO se inserta como una sola semana -- inyectaria una observacion
  varias veces mas grande que la real), y correcciones retroactivas
  (diferencia negativa, NO se clampea a cero). Ver docs/exploracion-ira-
  boletines-minsal.md, hallazgos 2 y 5.
- Verificado antes de escribir este loader: las 2742 filas sin nota tienen
  span == 1 semana en las 70 combinaciones (anio, departamento) del corpus,
  sin excepcion, y ninguna es negativa.

clasificacion='notificado' (ADR 0011): la tabla departamental de IRA no
separa probable/confirmado, es un solo conteo clinico por departamento.
boletin_id queda NULL para todas las filas -- este loader no construye una
bitacora tipo boletines_procesados para IRA (fuera de alcance de esta
carga; la bitacora exploratoria ya vive en
data/interim/corrida_ira/bitacora_ira.csv, no en Postgres).

Uso:
    python3 cargar_ira.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from psycopg2.extras import execute_values

from db import get_connection

RAIZ = Path(__file__).parent
CSV_PATH = RAIZ / "data" / "interim" / "corrida_ira" / "desacumulado_ira_semanal.csv"


def leer_filas_seguras() -> list[tuple[int, str, int, int]]:
    """(anio, departamento, semana, valor) solo para filas sin `nota` --
    ver docstring del modulo para por que las filas con nota se excluyen."""
    filas = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["nota"].strip():
                continue
            filas.append((int(r["anio"]), r["departamento"], int(r["semana"]), int(r["valor"])))
    return filas


def cargar(dry_run: bool = False) -> dict[str, int]:
    filas = leer_filas_seguras()
    conn = get_connection()
    contadores = {"leidas": len(filas), "insertadas": 0, "sin_region": 0}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM regiones WHERE nivel_admin = 1")
            region_id_por_nombre = {nombre: rid for rid, nombre in cur.fetchall()}
            if len(region_id_por_nombre) != 14:
                raise RuntimeError(
                    f"regiones (nivel_admin=1) trae {len(region_id_por_nombre)} filas, "
                    "se esperaban 14 departamentos."
                )

            cur.execute("SELECT id FROM tipos_evento WHERE codigo = 'ira'")
            fila = cur.fetchone()
            if fila is None:
                raise RuntimeError(
                    "tipos_evento no tiene 'ira' -- correr la migracion 0007 "
                    "(ADR 0011) antes de este loader."
                )
            tipo_evento_id = fila[0]

            cur.execute("SELECT id FROM fuentes_datos WHERE codigo = 'minsal_pdf'")
            fuente_id = cur.fetchone()[0]

            valores = []
            for anio, departamento, semana, valor in filas:
                region_id = region_id_por_nombre.get(departamento)
                if region_id is None:
                    contadores["sin_region"] += 1
                    continue
                valores.append(
                    (region_id, tipo_evento_id, anio, semana, "notificado", valor, fuente_id, None)
                )

            if contadores["sin_region"]:
                raise RuntimeError(
                    f"{contadores['sin_region']} filas con departamento no resuelto contra "
                    "regiones -- revisar nombres antes de insertar nada."
                )

            if dry_run:
                print(f"[dry-run] {len(valores)} filas listas para insertar, nada escrito.")
                return contadores

            if valores:
                execute_values(
                    cur,
                    """
                    INSERT INTO casos_epidemiologicos
                        (region_id, tipo_evento_id, anio, semana_epi, clasificacion, conteo, fuente_id, boletin_id)
                    VALUES %s
                    ON CONFLICT (region_id, tipo_evento_id, anio, semana_epi, clasificacion, fuente_id)
                    DO UPDATE SET conteo = EXCLUDED.conteo, fecha_ingesta = now()
                    """,
                    valores,
                    page_size=len(valores),
                )
                # page_size=len(valores): sin esto cur.rowcount solo refleja la
                # ultima pagina interna de execute_values (bug documentado en
                # CLAUDE.md, confirmado en vivo al cargar OpenDengue).
                contadores["insertadas"] = len(valores)
        conn.commit()
    finally:
        conn.close()
    return contadores


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="leer y validar sin escribir a Postgres")
    args = ap.parse_args()

    contadores = cargar(dry_run=args.dry_run)
    print(contadores)


if __name__ == "__main__":
    main()
