"""
Carga a casos_epidemiologicos el conteo departamental de Neumonías ya
desacumulado por corrida_respiratorios.py (ADR 0011 + catálogo 'neumonia'
en migración 0008).

Lee data/interim/corrida_respiratorios/desacumulado_neumonias.csv e inserta
solo filas seguras (nota vacía, span de 1 semana). --dry-run no escribe.

Uso:
    python3 cargar_neumonias.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path



RAIZ = Path(__file__).parent
CSV_PATH = RAIZ / "data" / "interim" / "corrida_respiratorios" / "desacumulado_neumonias.csv"


def leer_filas_seguras() -> list[tuple[int, str, int, int]]:
    filas = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["nota"].strip():
                continue
            if not r["valor"].strip():
                continue
            filas.append((int(r["anio"]), r["departamento"], int(r["semana"]), int(float(r["valor"]))))
    return filas


def cargar(dry_run: bool = False) -> dict[str, int]:
    from psycopg2.extras import execute_values

    from db import get_connection

    filas = leer_filas_seguras()
    conn = get_connection()
    contadores = {"leidas": len(filas), "insertadas": 0, "sin_region": 0}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM regiones WHERE nivel_admin = 1")
            region_id_por_nombre = {nombre: rid for rid, nombre in cur.fetchall()}
            if len(region_id_por_nombre) != 14:
                raise RuntimeError(
                    f"regiones (nivel_admin=1) trae {len(region_id_por_nombre)} filas, se esperaban 14."
                )

            cur.execute("SELECT id FROM tipos_evento WHERE codigo = 'neumonia'")
            fila = cur.fetchone()
            if fila is None:
                raise RuntimeError("tipos_evento no tiene 'neumonia' -- correr la migracion 0008.")
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
                    f"{contadores['sin_region']} filas con departamento no resuelto -- nada insertado."
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
                contadores["insertadas"] = len(valores)
        conn.commit()
    finally:
        conn.close()
    return contadores


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    print(cargar(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
