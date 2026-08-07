"""
Verifica que build_geo_departamentos.DEPARTAMENTOS no diverja del catalogo
sembrado en db/migrations/0001_init_schema.sql.

DEPARTAMENTOS es un espejo hardcodeado de esa migracion (ver comentario en
build_geo_departamentos.py) porque el build no depende de tener Postgres
levantado. Este test es la guarda contra el espejo desactualizandose: si la
migracion cambia un nombre o un codigo y el script no se actualiza, este
test falla en vez de dejar que la union nombre-normalizado falle (o, peor,
una silenciosa coincidencia).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from build_geo_departamentos import DEPARTAMENTOS  # noqa: E402

MIGRACION_PATH = (
    Path(__file__).parent.parent.parent.parent / "db" / "migrations" / "0001_init_schema.sql"
)

# Coincide con cada fila del segundo INSERT INTO regiones (departamentos,
# nivel_admin = 1): ('SV-AH', 'Ahuachapán',    1, 'SV', ...)
FILA_DEPARTAMENTO_RE = re.compile(r"\('(SV-[A-Z]{2})',\s*'([^']+)',\s*1,")


def _departamentos_sembrados_en_migracion() -> dict[str, str]:
    texto = MIGRACION_PATH.read_text(encoding="utf-8")
    filas = FILA_DEPARTAMENTO_RE.findall(texto)
    return {nombre: codigo for codigo, nombre in filas}


def test_departamentos_coincide_con_migracion():
    sembrados = _departamentos_sembrados_en_migracion()
    assert sembrados, (
        f"no se extrajo ninguna fila de {MIGRACION_PATH} — revisar si el "
        "regex FILA_DEPARTAMENTO_RE sigue coincidiendo con el formato del INSERT"
    )
    assert DEPARTAMENTOS == sembrados, (
        "DEPARTAMENTOS en build_geo_departamentos.py quedo desactualizado "
        "respecto a db/migrations/0001_init_schema.sql:\n"
        f"  solo en el script:    {sorted(set(DEPARTAMENTOS) - set(sembrados))}\n"
        f"  solo en la migracion: {sorted(set(sembrados) - set(DEPARTAMENTOS))}\n"
        f"  codigo distinto:      {sorted(k for k in set(DEPARTAMENTOS) & set(sembrados) if DEPARTAMENTOS[k] != sembrados[k])}"
    )


def test_catorce_departamentos():
    assert len(DEPARTAMENTOS) == 14
