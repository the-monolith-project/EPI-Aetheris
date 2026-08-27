#!/usr/bin/env python3
"""
Genera web/public/geo/slv-adm1.geojson a partir del GeoJSON ADM1 de
geoBoundaries (fuente local pineada, ver SOURCE_PATH), con el codigo de
regiones.codigo horneado en cada feature.

Se ejecuta una sola vez en tiempo de construccion (no en cada arranque del
frontend). El resultado es el archivo que Leaflet consume directamente,
uniendo por igualdad estricta sobre la propiedad `codigo` — ninguna logica
de normalizacion de texto vive en el frontend.

Motivo: shapeISO viene vacio en las 14 features de este boundary (ver
docs/adr/0002-join-mapa-geojson-por-nombre.md), asi que la union real se
hace aqui, una vez, contra shapeName normalizado.

No descarga nada por si sola: trabaja sobre el GeoJSON crudo ya commiteado
en SOURCE_PATH, para que el build no dependa de que geoboundaries.org este
en linea. Actualizar esa fuente es un paso manual y explicito, no algo que
corra en cada build:

    curl -sL "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/\
gbOpen/SLV/ADM1/geoBoundaries-SLV-ADM1_simplified.geojson" \
        -o backend/ingestion/geo/slv-adm1-source.geojson

El commit `9469f09` es el que fija docs/adr/0002-join-mapa-geojson-por-nombre.md
(boundaryID SLV-ADM1-98794003, build Dec 2023). Si se actualiza a una version
mas nueva de geoBoundaries, revisar el diff del archivo fuente y repetir la
verificacion 14-a-14 antes de volver a correr este script, y anotar el cambio
de version en el ADR.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

SOURCE_PATH = Path(__file__).parent / "geo" / "slv-adm1-source.geojson"

OUTPUT_PATH = (
    Path(__file__).parent.parent.parent / "web" / "public" / "geo" / "slv-adm1.geojson"
)

# El pin de version que fija docs/adr/0002-join-mapa-geojson-por-nombre.md no es
# solo un comentario: se verifica contra el contenido real de SOURCE_PATH antes
# de unir. shapeID trae el numero de boundaryID como prefijo (confirmado en las
# 14 features del archivo commiteado), asi que si alguien reemplaza SOURCE_PATH
# por un boundary distinto (otro pais, otro nivel admin, u otra version cuyo
# shapeID cambie de esquema), la verificacion falla en vez de unir con datos que
# ya no son los que este ADR dice haber verificado.
BOUNDARY_ID = "SLV-ADM1-98794003"
_BOUNDARY_GROUP, _BOUNDARY_TYPE, _BOUNDARY_NUM = BOUNDARY_ID.split("-")

# Fuente de verdad: db/migrations/0001_init_schema.sql (seccion 5, INSERT INTO
# regiones). Si esa migracion cambia nombres o codigos, actualizar aqui tambien.
DEPARTAMENTOS = {
    "Ahuachapán": "SV-AH",
    "Cabañas": "SV-CA",
    "Chalatenango": "SV-CH",
    "Cuscatlán": "SV-CU",
    "La Libertad": "SV-LI",
    "La Paz": "SV-PA",
    "Santa Ana": "SV-SA",
    "San Miguel": "SV-SM",
    "Sonsonate": "SV-SO",
    "San Salvador": "SV-SS",
    "San Vicente": "SV-SV",
    "La Unión": "SV-UN",
    "Usulután": "SV-US",
    "Morazán": "SV-MO",
}

_PREFIJO_RE = re.compile(r"^Departamento de\s+", re.IGNORECASE)


def normalizar(nombre: str) -> str:
    sin_prefijo = _PREFIJO_RE.sub("", nombre)
    sin_diacriticos = "".join([
        c
        for c in unicodedata.normalize("NFD", sin_prefijo)
        if unicodedata.category(c) != "Mn"
    ])
    return re.sub(r"\s+", " ", sin_diacriticos.lower().strip())


def _verificar_boundary_pineado(geojson: dict) -> None:
    desajustados = [
        f["properties"].get("shapeID")
        for f in geojson["features"]
        if f["properties"].get("shapeGroup") != _BOUNDARY_GROUP
        or f["properties"].get("shapeType") != _BOUNDARY_TYPE
        or not str(f["properties"].get("shapeID", "")).startswith(_BOUNDARY_NUM)
    ]
    if desajustados:
        print(
            f"ERROR: {SOURCE_PATH} no corresponde al boundary pineado {BOUNDARY_ID}.",
            file=sys.stderr,
        )
        print(f"  shapeID que no coinciden: {desajustados}", file=sys.stderr)
        print(
            "  Si se reemplazo SOURCE_PATH a proposito (version nueva de "
            "geoBoundaries), actualizar BOUNDARY_ID aqui y el pin en el ADR.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    por_nombre_normalizado = {normalizar(nombre): codigo for nombre, codigo in DEPARTAMENTOS.items()}

    geojson = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    _verificar_boundary_pineado(geojson)

    sin_match = []
    for feature in geojson["features"]:
        shape_name = feature["properties"]["shapeName"]
        codigo = por_nombre_normalizado.get(normalizar(shape_name))
        if codigo is None:
            sin_match.append(shape_name)
            continue
        feature["properties"]["codigo"] = codigo

    features_totales = len(geojson["features"])
    codigos_asignados = {f["properties"].get("codigo") for f in geojson["features"]}
    codigos_asignados.discard(None)

    if sin_match or features_totales != len(DEPARTAMENTOS) or len(codigos_asignados) != len(DEPARTAMENTOS):
        print("ERROR: la union nombre-normalizado no dio 14 a 14.", file=sys.stderr)
        print(f"  features en el GeoJSON: {features_totales}", file=sys.stderr)
        print(f"  regiones esperadas:     {len(DEPARTAMENTOS)}", file=sys.stderr)
        print(f"  codigos asignados:      {len(codigos_asignados)}", file=sys.stderr)
        if sin_match:
            print(f"  shapeName sin match:    {sin_match}", file=sys.stderr)
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(geojson, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"OK: {features_totales} departamentos con codigo asignado -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
