"""
Carga el indice ONI (Oceanic Nino Index) de NOAA CPC como predictor
experimental (ADR 0008, migracion 0006) -- no confirmado en produccion
todavia. Descarga en vivo (sin credenciales, texto plano):

    https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt

Formato real (verificado en vivo antes de escribir el parser): columnas
SEAS (temporada movil de 3 letras, ej. "DJF"), YR, TOTAL, ANOM. Cada
temporada representa el mes CENTRAL de una ventana de 3 meses, y YR es el
anio calendario de ese mes central (confirmado: "DJF 1950" = dic1949 +
ene1950 + feb1950, YR=1950 = anio de enero). Se guarda ANOM (la anomalia,
que es lo que se usa para clasificar fase El Nino/Neutral/La Nina), no
TOTAL.

Resolucion mensual -> semanal: el mismo valor mensual se aplica a cada
semana epidemiologica cuyo fecha_inicio caiga en ese mes calendario. Esto
es una asignacion de resolucion honesta (el dato real no tiene mas detalle
que mensual, se declara tal cual), NO una interpolacion ni un reparto de
una cantidad acumulable -- ver ADR 0008, punto C, para la distincion
explicita con el caso de OpenDengue Admin1 (que si se fraccionara
fabricaria dato).

Se guarda bajo region SV (nacional) -- ONI no tiene resolucion
departamental, no tiene sentido repetirlo 14 veces.

Uso:
    python3 cargar_oni.py
"""

from __future__ import annotations

import argparse

import requests

from db import get_connection

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

# SEAS (temporada de 3 letras) -> mes central (1-12). Verificado contra el
# propio archivo de NOAA, no asumido de memoria.
MES_CENTRAL = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}


def descargar_oni() -> dict[tuple[int, int], float]:
    """Devuelve {(anio_calendario, mes_calendario): anom}."""
    resp = requests.get(ONI_URL, timeout=30)
    resp.raise_for_status()
    lineas = resp.text.splitlines()

    anom_por_mes: dict[tuple[int, int], float] = {}
    for linea in lineas[1:]:  # la primera es el encabezado "SEAS YR TOTAL ANOM"
        partes = linea.split()
        if len(partes) != 4:
            continue
        seas, yr, _total, anom = partes
        mes = MES_CENTRAL.get(seas)
        if mes is None:
            continue
        anom_por_mes[(int(yr), mes)] = float(anom)
    return anom_por_mes


def cargar(anio_inicio: int, anio_fin: int) -> int:
    anom_por_mes = descargar_oni()
    print(f"{len(anom_por_mes)} valores mensuales ONI descargados "
          f"({min(anom_por_mes)[0]}-{max(anom_por_mes)[0]}).")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM regiones WHERE codigo = 'SV'")
            region_id = cur.fetchone()[0]

            cur.execute("SELECT id FROM fuentes_datos WHERE codigo = 'noaa_oni'")
            fila = cur.fetchone()
            if fila is None:
                raise RuntimeError(
                    "No existe fuentes_datos.codigo='noaa_oni' -- correr "
                    "db/migrations/0006_fuente_noaa_oni.sql primero (ADR 0008)."
                )
            fuente_id = fila[0]

            cur.execute(
                "SELECT anio, semana_epi, fecha_inicio FROM semanas_epidemiologicas "
                "WHERE anio BETWEEN %s AND %s",
                (anio_inicio, anio_fin),
            )
            semanas = cur.fetchall()

            valores = []
            sin_dato = 0
            for anio_epi, semana_epi, fecha_inicio in semanas:
                clave = (fecha_inicio.year, fecha_inicio.month)
                anom = anom_por_mes.get(clave)
                if anom is None:
                    sin_dato += 1
                    continue
                valores.append((region_id, anio_epi, semana_epi, "oni_anom", anom, fuente_id))

            if sin_dato:
                print(f"AVISO: {sin_dato} semanas sin valor ONI disponible (mes calendario "
                      f"fuera del rango publicado por NOAA) -- no rellenadas.")

            if not valores:
                print("Nada que insertar.")
                return 0

            from psycopg2.extras import execute_values

            execute_values(
                cur,
                """
                INSERT INTO variables_ambientales
                    (region_id, anio, semana_epi, variable, valor, fuente_id)
                VALUES %s
                ON CONFLICT (region_id, anio, semana_epi, variable, fuente_id)
                DO UPDATE SET valor = EXCLUDED.valor, fecha_ingesta = now()
                """,
                valores,
                page_size=len(valores),
            )
            insertadas = len(valores)
        conn.commit()
    finally:
        conn.close()

    return insertadas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anio-inicio", type=int, default=2014)
    parser.add_argument("--anio-fin", type=int, default=2024)
    args = parser.parse_args()

    insertadas = cargar(args.anio_inicio, args.anio_fin)
    print(f"OK: {insertadas} filas insertadas/actualizadas en variables_ambientales "
          f"(variable=oni_anom, fuente=noaa_oni, region=SV, {args.anio_inicio}-{args.anio_fin}).")


if __name__ == "__main__":
    main()
