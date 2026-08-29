"""
Carga variables ambientales (Open-Meteo) por departamento a
variables_ambientales, y puebla coordenadas/elevacion en regiones como
efecto colateral (ADR 0003) -- ninguna carga anterior escribia esas
columnas, y este loader ya necesita lat/lon para llamar a la API y recibe
elevation en la misma respuesta.

Dos llamadas reales a archive-api.open-meteo.com, una por modelo -- nunca
best_match ni era5_seamless (ver docs/contexto/01-decisiones-cerradas.md):
- era5_land (fuente 'open_meteo_era5_land'): temperature_2m_max/min/mean,
  relative_humidity_2m_mean, dew_point_2m_mean.
- era5 (fuente 'open_meteo_era5', ADR 0006): precipitation_sum,
  precipitation_hours -- era5_land no sirve precipitacion.
Cada llamada trae los 14 departamentos en una sola peticion multi-ubicacion
(lat/lon separados por coma, mismo orden que centroides_departamentos.csv).

Guarda de precipitacion (trampa confirmada, ver hallazgos_precipitacion_
modelo.md): precipitation_hours puede venir 0.0 en vez de null cuando el
modelo no tiene el dato para ese dia -- se descarta junto con
precipitation_sum si ese viene null en la misma respuesta y mismo dia,
nunca se confia en precipitation_hours por si solo.

Agregacion diaria -> semana epidemiologica (sin agregacion nativa en la
API, ver semanas_epidemiologicas): media semanal para temp_max/temp_min/
temp_media/humedad_relativa_media/punto_rocio (variables de estado), suma
semanal para precipitation_sum/precipitation_hours (variables
acumulativas). Es una eleccion de implementacion, no una regla cerrada por
el equipo mas alla de "sumar/promediar diarios" -- revisar si se necesita
otro criterio (ej. maximo semanal del maximo diario).

No excluye 2020: la exclusion de 2020 es del training del clasificador,
no de la ingesta (punto E de docs/contexto/02-decisiones-abiertas.md) --
trae el rango continuo completo, igual que backend/ingestion/cargar_
opendengue.py.

Uso:
    python3 cargar_clima.py [--anio-inicio 2018] [--anio-fin 2024]
"""

from __future__ import annotations

import argparse
import csv
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import requests
from psycopg2.extras import execute_values

from db import get_connection

RAIZ = Path(__file__).parent
CENTROIDES_PATH = RAIZ / "geo" / "centroides_departamentos.csv"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

ANIO_INICIO_DEFAULT = 2018
ANIO_FIN_DEFAULT = 2024

VARIABLES_ERA5_LAND = [
    "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
    "relative_humidity_2m_mean", "dew_point_2m_mean",
]
VARIABLES_ERA5 = ["precipitation_sum", "precipitation_hours"]

# Nombre de columna Open-Meteo -> nombre de variable en variables_ambientales
# (catalogo cerrado, ver AGENTS.md -- usar exactamente estas cadenas).
MAPA_VARIABLE = {
    "temperature_2m_max": "temp_max",
    "temperature_2m_min": "temp_min",
    "temperature_2m_mean": "temp_media",
    "relative_humidity_2m_mean": "humedad_relativa_media",
    "dew_point_2m_mean": "punto_rocio",
    "precipitation_sum": "precipitation_sum",
    "precipitation_hours": "precipitation_hours",
}

AGREGACION = {
    "temp_max": "media",
    "temp_min": "media",
    "temp_media": "media",
    "humedad_relativa_media": "media",
    "punto_rocio": "media",
    "precipitation_sum": "suma",
    "precipitation_hours": "suma",
}

# variable -> codigo de fuentes_datos (ADR 0006). Nada en el esquema fuerza
# esta correspondencia -- es disciplina del loader, igual que clasificacion
# = 'total' en el ADR 0005.
FUENTE_POR_VARIABLE = {
    "temp_max": "open_meteo_era5_land",
    "temp_min": "open_meteo_era5_land",
    "temp_media": "open_meteo_era5_land",
    "humedad_relativa_media": "open_meteo_era5_land",
    "punto_rocio": "open_meteo_era5_land",
    "precipitation_sum": "open_meteo_era5",
    "precipitation_hours": "open_meteo_era5",
}


@dataclass
class Departamento:
    codigo: str
    nombre: str
    lat: float
    lon: float


def leer_departamentos() -> list[Departamento]:
    deptos = []
    with open(CENTROIDES_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            deptos.append(Departamento(row["codigo"], row["nombre"], float(row["lat"]), float(row["lon"])))
    return deptos


def llamar_open_meteo(deptos: list[Departamento], modelo: str, variables: list[str],
                       fecha_inicio: str, fecha_fin: str) -> list[dict]:
    params = {
        "latitude": ",".join(f"{d.lat:.6f}" for d in deptos),
        "longitude": ",".join(f"{d.lon:.6f}" for d in deptos),
        "start_date": fecha_inicio,
        "end_date": fecha_fin,
        "daily": ",".join(variables),
        "timezone": "America/El_Salvador",
        "models": modelo,
    }
    # El limite gratuito es generoso (ver docs/contexto/01-decisiones-cerradas.md,
    # ~2200 llamadas ponderadas estimadas contra 10000/dia), pero el rate
    # limit por minuto se dispara con pocas llamadas seguidas -- confirmado
    # en vivo probando este mismo loader. Reintento con backoff simple en
    # vez de fallar sobre un 429.
    for intento in range(5):
        resp = requests.get(ARCHIVE_URL, params=params, timeout=180)
        if resp.status_code != 429:
            break
        espera = 15 * (intento + 1)
        print(f"  429 Too Many Requests -- esperando {espera}s antes de reintentar "
              f"({intento + 1}/5)...")
        time.sleep(espera)
    resp.raise_for_status()
    datos = resp.json()
    # Con >1 ubicacion la API devuelve una lista en el mismo orden en que se
    # pidieron las coordenadas -- siempre aplica aqui, se piden los 14
    # departamentos juntos en una sola llamada.
    if isinstance(datos, dict):
        datos = [datos]
    return datos


@dataclass
class PuntoDiario:
    codigo: str
    fecha: str
    variable: str
    valor: float


def extraer_puntos_diarios(deptos: list[Departamento], respuesta: list[dict],
                            variables: list[str]) -> list[PuntoDiario]:
    puntos = []
    for depto, resultado in zip(deptos, respuesta):
        diario = resultado["daily"]
        fechas = diario["time"]

        sum_nula = None
        if "precipitation_sum" in diario:
            sum_nula = [v is None for v in diario["precipitation_sum"]]

        for var_openmeteo in variables:
            valores = diario[var_openmeteo]
            variable = MAPA_VARIABLE[var_openmeteo]
            for i, (fecha, valor) in enumerate(zip(fechas, valores)):
                if valor is None:
                    continue
                if var_openmeteo == "precipitation_hours" and sum_nula and sum_nula[i]:
                    continue
                puntos.append(PuntoDiario(depto.codigo, fecha, variable, float(valor)))
    return puntos


def construir_mapa_fecha_a_semana(conn) -> dict[str, tuple[int, int]]:
    with conn.cursor() as cur:
        cur.execute("SELECT anio, semana_epi, fecha_inicio, fecha_fin FROM semanas_epidemiologicas")
        calendario = cur.fetchall()

    mapa: dict[str, tuple[int, int]] = {}
    un_dia = timedelta(days=1)
    for anio, semana_epi, f_ini, f_fin in calendario:
        d = f_ini
        clave_semana = (anio, semana_epi)
        while d <= f_fin:
            mapa[d.isoformat()] = clave_semana
            d += un_dia
    return mapa


def agregar_a_semana(puntos: list[PuntoDiario],
                      mapa_fecha_a_semana: dict[str, tuple[int, int]]) -> dict[tuple[str, int, int, str], list[float]]:
    grupos: dict[tuple[str, int, int, str], list[float]] = defaultdict(list)
    sin_semana = set()
    for p in puntos:
        semana = mapa_fecha_a_semana.get(p.fecha)
        if semana is None:
            sin_semana.add(p.fecha)
            continue
        anio, semana_epi = semana
        grupos[(p.codigo, anio, semana_epi, p.variable)].append(p.valor)

    if sin_semana:
        print(
            f"AVISO: {len(sin_semana)} fechas sin semana epidemiologica resuelta "
            f"-- ejecutar poblar_semanas_epidemiologicas.py para ese rango. "
            f"Ejemplos: {sorted(sin_semana)[:5]}"
        )
    return grupos


def cargar(anio_inicio: int, anio_fin: int) -> int:
    deptos = leer_departamentos()
    fecha_inicio = date(anio_inicio, 1, 1).isoformat()
    fecha_fin = date(anio_fin, 12, 31).isoformat()

    print(f"Llamando Open-Meteo (era5_land, 5 variables, {len(deptos)} departamentos, "
          f"{fecha_inicio} a {fecha_fin})...")
    resp_era5_land = llamar_open_meteo(deptos, "era5_land", VARIABLES_ERA5_LAND, fecha_inicio, fecha_fin)
    print(f"Llamando Open-Meteo (era5, 2 variables, {len(deptos)} departamentos)...")
    resp_era5 = llamar_open_meteo(deptos, "era5", VARIABLES_ERA5, fecha_inicio, fecha_fin)

    puntos = extraer_puntos_diarios(deptos, resp_era5_land, VARIABLES_ERA5_LAND)
    puntos += extraer_puntos_diarios(deptos, resp_era5, VARIABLES_ERA5)
    print(f"{len(puntos)} observaciones diarias válidas extraídas (tras la guarda de precipitación).")

    conn = get_connection()
    try:
        mapa_fecha_a_semana = construir_mapa_fecha_a_semana(conn)
        grupos = agregar_a_semana(puntos, mapa_fecha_a_semana)

        with conn.cursor() as cur:
            cur.execute("SELECT codigo, id FROM regiones WHERE nivel_admin = 1")
            region_id_por_codigo = dict(cur.fetchall())

            cur.execute("SELECT codigo, id FROM fuentes_datos")
            fuente_id_por_codigo = dict(cur.fetchall())

            elevacion_por_codigo = {d.codigo: r["elevation"] for d, r in zip(deptos, resp_era5_land)}
            for depto in deptos:
                cur.execute(
                    "UPDATE regiones SET centroide_lat = %s, centroide_lon = %s, elevacion_m = %s "
                    "WHERE codigo = %s",
                    (depto.lat, depto.lon, elevacion_por_codigo[depto.codigo], depto.codigo),
                )

            valores_insert = []
            for (codigo, anio, semana_epi, variable), vals in grupos.items():
                region_id = region_id_por_codigo.get(codigo)
                if region_id is None:
                    continue
                fuente_id = fuente_id_por_codigo[FUENTE_POR_VARIABLE[variable]]
                valor_final = sum(vals) if AGREGACION[variable] == "suma" else sum(vals) / len(vals)
                valores_insert.append((region_id, anio, semana_epi, variable, round(valor_final, 3), fuente_id))

            if not valores_insert:
                print("Nada que insertar.")
                return 0

            execute_values(
                cur,
                """
                INSERT INTO variables_ambientales
                    (region_id, anio, semana_epi, variable, valor, fuente_id)
                VALUES %s
                ON CONFLICT (region_id, anio, semana_epi, variable, fuente_id)
                DO UPDATE SET valor = EXCLUDED.valor, fecha_ingesta = now()
                """,
                valores_insert,
                page_size=len(valores_insert),
            )
        conn.commit()
    finally:
        conn.close()

    return len(valores_insert)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anio-inicio", type=int, default=ANIO_INICIO_DEFAULT)
    parser.add_argument("--anio-fin", type=int, default=ANIO_FIN_DEFAULT)
    args = parser.parse_args()

    insertadas = cargar(args.anio_inicio, args.anio_fin)
    print(
        f"OK: {insertadas} filas insertadas/actualizadas en variables_ambientales "
        f"(7 variables × 14 departamentos, {args.anio_inicio}-{args.anio_fin})."
    )


if __name__ == "__main__":
    main()
