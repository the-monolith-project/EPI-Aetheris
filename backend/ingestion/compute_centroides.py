#!/usr/bin/env python3
"""
Calcula un punto representativo por departamento a partir del GeoJSON ya
horneado con codigo (web/public/geo/slv-adm1.geojson) — no del GeoJSON
fuente sin procesar, porque codigo es la llave con la que se va a guardar
cada coordenada.

Corre una sola vez; su salida es una tabla de 14 filas. shapely es una
dependencia de desarrollo (requirements-dev.txt), no entra a la imagen de
produccion.

Dos trampas:

1. Geometrica: La Unión y Usulután tienen geometria compleja (islas en el
   golfo de Fonseca / bahia de Jiquilisco). Un centroide aritmetico sobre
   el conjunto se corre hacia el mar. Se toma el poligono de mayor area
   (si la geometria es MultiPolygon) y se saca de ahi un punto
   representativo (`representative_point()`), que shapely garantiza
   interior al poligono — el centroide no, si la forma es concava.

2. De orden: GeoJSON guarda [longitud, latitud]; Open-Meteo espera
   latitud y longitud por separado. Invertir el orden no truena, produce
   coordenadas validas de otro punto del planeta. Cada punto calculado se
   valida contra la caja de El Salvador antes de aceptarse.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from shapely.geometry import shape

GEOJSON_PATH = (
    Path(__file__).parent.parent.parent / "web" / "public" / "geo" / "slv-adm1.geojson"
)
OUTPUT_PATH = Path(__file__).parent / "geo" / "centroides_departamentos.csv"

# Caja delimitadora de El Salvador (con margen), no un bounding box exacto.
LAT_MIN, LAT_MAX = 13.1, 14.5
LON_MIN, LON_MAX = -90.2, -87.6


def punto_representativo(geometry: dict) -> tuple[float, float]:
    geom = shape(geometry)
    poligono = max(geom.geoms, key=lambda g: g.area) if geom.geom_type == "MultiPolygon" else geom
    punto = poligono.representative_point()
    lat, lon = punto.y, punto.x

    assert LAT_MIN <= lat <= LAT_MAX, f"latitud fuera de El Salvador: {lat}"
    assert LON_MIN <= lon <= LON_MAX, f"longitud fuera de El Salvador: {lon}"

    return lat, lon


def main() -> None:
    geojson = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))

    filas = []
    for feature in geojson["features"]:
        codigo = feature["properties"]["codigo"]
        nombre = feature["properties"]["shapeName"]
        lat, lon = punto_representativo(feature["geometry"])
        filas.append(
            {
                "codigo": codigo,
                "nombre": nombre,
                "lat": f"{lat:.6f}",
                "lon": f"{lon:.6f}",
                "geom_type": feature["geometry"]["type"],
            }
        )

    filas.sort(key=lambda f: f["codigo"])

    assert len(filas) == 14, f"esperaba 14 departamentos, obtuve {len(filas)}"

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["codigo", "nombre", "lat", "lon", "geom_type"])
        writer.writeheader()
        writer.writerows(filas)

    print(f"OK: {len(filas)} puntos representativos -> {OUTPUT_PATH}")
    for fila in filas:
        print(f"  {fila['codigo']}  {fila['lat']}, {fila['lon']}  ({fila['geom_type']})")


if __name__ == "__main__":
    main()
