#!/usr/bin/env python3
"""Descarga los boletines epidemiologicos del MINSAL correspondientes a 2018."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from minsal_common import descargar_boletines_del_anio

ANIO = 2018


def main() -> None:
    resumen = descargar_boletines_del_anio(ANIO)
    resumen.imprimir()
    if resumen.total_fallido:
        sys.exit(1)


if __name__ == "__main__":
    main()
