"""
Carga vigilancia_virus_respiratorios desde el inventario exploratorio
(ADR 0012). Lee inventario_vigilancia_virus.csv (gitignoreado).

Conteos: si la fuente trajo columna de semana, se usa; si no, se desacumula
el acumulado del año actual (hueco / corrección negativa / primer corte
tardío = no insertar). Positividad: se guarda el valor publicado, sin
recalcular. --dry-run no escribe.

Uso:
    python3 cargar_vigilancia_respiratoria.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path



RAIZ = Path(__file__).parent
CSV_PATH = RAIZ / "data" / "interim" / "corrida_respiratorios" / "inventario_vigilancia_virus.csv"

MAPA_METRICA = {
    "muestras_analizadas": ("todos", "muestras_analizadas", "conteo"),
    "muestras_positivas": ("todos", "muestras_positivas", "conteo"),
    "influenza_total": ("influenza", "detecciones", "conteo"),
    "influenza_a_h1n1": ("influenza_a_h1n1", "detecciones", "conteo"),
    "influenza_a_no_subtipificado": ("influenza_a_no_subtipificado", "detecciones", "conteo"),
    "influenza_a_h3n2": ("influenza_a_h3n2", "detecciones", "conteo"),
    "influenza_b": ("influenza_b", "detecciones", "conteo"),
    "otros_virus_total": ("otros", "detecciones", "conteo"),
    "parainfluenza": ("parainfluenza", "detecciones", "conteo"),
    "vsr": ("vsr", "detecciones", "conteo"),
    "adenovirus": ("adenovirus", "detecciones", "conteo"),
    "covid_19": ("covid_19", "detecciones", "conteo"),
    "positividad_virus": ("todos", "positividad", "porcentaje"),
    "positividad_influenza": ("influenza", "positividad", "porcentaje"),
    "positividad_vsr": ("vsr", "positividad", "porcentaje"),
}


def _f(v: str) -> float | None:
    if v is None or str(v).strip() == "":
        return None
    return float(v)


def leer_inventario(path: Path = CSV_PATH) -> list[dict]:
    filas = []
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("estado") != "ok":
                continue
            if not r.get("metrica") or r["metrica"] not in MAPA_METRICA:
                continue
            if not r.get("semana_corte"):
                continue
            filas.append(r)
    return filas


def construir_filas_carga(inventario: list[dict]) -> list[tuple]:
    """(anio, semana, virus, metrica, valor, unidad). Sin nota de exclusión."""
    positividad: list[tuple] = []
    series: dict[tuple, dict[int, tuple[float | None, float | None]]] = defaultdict(dict)

    for r in inventario:
        if r.get("estado") not in (None, "ok"):
            continue
        if r.get("metrica") not in MAPA_METRICA:
            continue
        virus, metrica, unidad = MAPA_METRICA[r["metrica"]]
        anio = int(r["anio"])
        semana = int(r["semana_corte"])
        actual = _f(r.get("anio_actual"))
        sem_col = _f(r.get("semana"))
        if unidad == "porcentaje":
            if actual is None:
                continue
            positividad.append((anio, semana, virus, metrica, actual, unidad))
            continue
        series[(anio, virus, metrica, unidad)][semana] = (actual, sem_col)

    out: list[tuple] = list(positividad)
    for (anio, virus, metrica, unidad), por_semana in series.items():
        anterior_semana, anterior_acum = None, None
        for semana in sorted(por_semana):
            actual, sem_col = por_semana[semana]
            if sem_col is not None:
                out.append((anio, semana, virus, metrica, sem_col, unidad))
                anterior_semana, anterior_acum = semana, actual
                continue
            if actual is None:
                continue
            if anterior_semana is None:
                if semana == 1:
                    out.append((anio, semana, virus, metrica, actual, unidad))
                anterior_semana, anterior_acum = semana, actual
                continue
            if semana - anterior_semana > 1:
                anterior_semana, anterior_acum = semana, actual
                continue
            diff = actual - (anterior_acum or 0)
            if diff < 0:
                anterior_semana, anterior_acum = semana, actual
                continue
            out.append((anio, semana, virus, metrica, diff, unidad))
            anterior_semana, anterior_acum = semana, actual
    unicos: dict[tuple, tuple] = {}
    for fila in out:
        unicos[fila[:4]] = fila
    return list(unicos.values())


def cargar(dry_run: bool = False) -> dict[str, int]:
    from psycopg2.extras import execute_values

    from db import get_connection

    filas = construir_filas_carga(leer_inventario())
    contadores = {"leidas": len(filas), "insertadas": 0}
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM regiones WHERE codigo = 'SV' AND nivel_admin = 0")
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("no existe region nacional SV")
            region_id = row[0]
            cur.execute("SELECT id FROM fuentes_datos WHERE codigo = 'minsal_pdf'")
            fuente_id = cur.fetchone()[0]

            valores = [
                (region_id, anio, semana, virus, metrica, valor, unidad, fuente_id, None)
                for anio, semana, virus, metrica, valor, unidad in filas
            ]
            if dry_run:
                print(f"[dry-run] {len(valores)} filas listas para insertar, nada escrito.")
                return contadores
            if valores:
                execute_values(
                    cur,
                    """
                    INSERT INTO vigilancia_virus_respiratorios
                        (region_id, anio, semana_epi, virus, metrica, valor, unidad, fuente_id, boletin_id)
                    VALUES %s
                    ON CONFLICT (region_id, anio, semana_epi, virus, metrica, fuente_id)
                    DO UPDATE SET valor = EXCLUDED.valor, unidad = EXCLUDED.unidad, fecha_ingesta = now()
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
