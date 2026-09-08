"""
Verifica el descarte de semanas epidemiologicas parciales sin tocar Postgres
ni la API de Open-Meteo. El caso que motiva la guarda: una corrida al anio en
curso trae una semana de cola con solo 2-4 dias (el reanalisis ERA5 no cubre
los ~5 dias mas recientes), y una suma parcial de precipitacion es
indistinguible aguas abajo de una semana genuinamente seca.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cargar_clima import (  # noqa: E402
    DIAS_MINIMOS_SEMANA,
    descartar_semanas_incompletas,
)


def _semana(dias: int) -> list[float]:
    return [1.0] * dias


def test_descarta_semana_de_cola_parcial():
    grupos = {
        ("SV-SS", 2026, 34, "temp_media"): _semana(7),
        ("SV-SS", 2026, 35, "temp_media"): _semana(7),
        ("SV-SS", 2026, 36, "temp_media"): _semana(3),  # semana de cola
        ("SV-SS", 2026, 36, "precipitation_sum"): _semana(3),
    }
    completos, descartados = descartar_semanas_incompletas(grupos)

    assert descartados == 2
    assert ("SV-SS", 2026, 36, "temp_media") not in completos
    assert ("SV-SS", 2026, 36, "precipitation_sum") not in completos
    assert ("SV-SS", 2026, 34, "temp_media") in completos
    assert ("SV-SS", 2026, 35, "temp_media") in completos


def test_conserva_semanas_completas_y_el_umbral_es_inclusivo():
    grupos = {
        ("SV-LI", 2025, 10, "humedad_relativa_media"): _semana(7),
        ("SV-LI", 2025, 11, "humedad_relativa_media"): _semana(DIAS_MINIMOS_SEMANA),
        ("SV-LI", 2025, 12, "humedad_relativa_media"): _semana(DIAS_MINIMOS_SEMANA - 1),
    }
    completos, descartados = descartar_semanas_incompletas(grupos)

    assert descartados == 1
    assert ("SV-LI", 2025, 11, "humedad_relativa_media") in completos  # ==minimo se conserva
    assert ("SV-LI", 2025, 12, "humedad_relativa_media") not in completos


def test_sin_grupos_no_falla():
    completos, descartados = descartar_semanas_incompletas({})
    assert completos == {}
    assert descartados == 0
