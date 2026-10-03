"""Pruebas del calendario de las semanas futuras que anexa
`_extender_serie_futuro` (nowcast_estimacion_dengue.py). Las semanas futuras
deben seguir el calendario epidemiologico MMWR (OPS/CDC), el mismo de
`semanas_epidemiologicas` y del entrenamiento, no el ISO. El anio de la semana
objetivo es un feature del modelo, de modo que un cruce de anio mal etiquetado
cambia una entrada y no solo un rotulo. No necesitan Postgres."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest
from epiweeks import Week, Year

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experimento_nowcast_corto_plazo import Serie  # noqa: E402
from nowcast_estimacion_dengue import _extender_serie_futuro  # noqa: E402


def _serie_hasta(ultima: date, T: int = 30) -> Serie:
    """Serie sintetica de T semanas (domingos) que termina en `ultima`."""
    fecha = np.array([ultima - timedelta(days=7 * (T - 1 - k)) for k in range(T)], dtype=object)
    semanas = [Week.fromdate(f, system="cdc") for f in fecha]
    anio = np.array([w.year for w in semanas], dtype=int)
    semana = np.array([w.week for w in semanas], dtype=int)
    doy = np.array([f.timetuple().tm_yday for f in fecha], dtype=int)
    casos = np.full(T, 50.0)
    clima = {"temp": np.full(T, 25.0)}
    return Serie(fecha, anio, semana, doy, casos, np.log1p(casos), clima, np.zeros(T))


def _etiquetas_futuras(ultima: date, n: int = 8) -> list[tuple[int, int]]:
    ext, t_real = _extender_serie_futuro(_serie_hasta(ultima), n)
    return [(int(ext.anio[t_real + k]), int(ext.semana[t_real + k])) for k in range(n)]


def test_cruce_de_anio_de_opendengue_2024_a_2025():
    # OpenDengue V1.3 termina en 2024-12-22; el 29 de diciembre ya es 2025-S1
    etiquetas = _etiquetas_futuras(date(2024, 12, 22))
    assert etiquetas[:3] == [(2025, 1), (2025, 2), (2025, 3)]
    assert etiquetas[-1] == (2025, 8)


def test_el_calendario_iso_no_coincide_con_el_epidemiologico_en_ese_cruce():
    # documenta por que no se usa isocalendar: el domingo 2024-12-29 es ISO 2024-S52
    d = date(2024, 12, 29)
    assert d.isocalendar()[:2] == (2024, 52)
    assert (Week.fromdate(d, system="cdc").year, Week.fromdate(d, system="cdc").week) == (2025, 1)


def test_anio_con_53_semanas_epidemiologicas():
    # MMWR 2020 tiene 53 semanas: el 27 de diciembre es 2020-S53
    assert _etiquetas_futuras(date(2020, 12, 20), n=3) == [(2020, 53), (2021, 1), (2021, 2)]
    # y 2025 tambien: el 28 de diciembre es 2025-S53
    assert _etiquetas_futuras(date(2025, 12, 21), n=3) == [(2025, 53), (2026, 1), (2026, 2)]


def test_anio_con_52_semanas_epidemiologicas():
    # 2023 tiene 52 semanas: la ultima empieza el 24 de diciembre
    assert _etiquetas_futuras(date(2023, 12, 17), n=3) == [(2023, 52), (2024, 1), (2024, 2)]


@pytest.mark.parametrize("ultima", [date(2014, 12, 21), date(2019, 12, 22), date(2022, 12, 18), date(2026, 12, 20)])
def test_cada_semana_futura_coincide_con_epiweeks(ultima):
    ext, t_real = _extender_serie_futuro(_serie_hasta(ultima), 8)
    for k in range(8):
        w = Week.fromdate(ext.fecha[t_real + k], system="cdc")
        assert (int(ext.anio[t_real + k]), int(ext.semana[t_real + k])) == (w.year, w.week)


def test_etiquetas_consecutivas_de_2013_a_2030():
    # cada semana avanza una, o pasa a la 1 del anio siguiente justo despues de la ultima
    ultima = date(2013, 1, 6)
    ext, t_real = _extender_serie_futuro(_serie_hasta(ultima, T=10), 17 * 52)
    pares = [(int(a), int(s)) for a, s in zip(ext.anio[t_real:], ext.semana[t_real:])]
    previo = (int(ext.anio[t_real - 1]), int(ext.semana[t_real - 1]))
    for actual in pares:
        if actual[0] == previo[0]:
            assert actual[1] == previo[1] + 1
        else:
            assert actual == (previo[0] + 1, 1)
            assert previo[1] == Year(previo[0], system="cdc").totalweeks()
        previo = actual


def test_lo_demas_de_la_serie_extendida_no_cambia():
    serie = _serie_hasta(date(2024, 12, 22))
    ext, t_real = _extender_serie_futuro(serie, 8)
    assert t_real == serie.T and ext.T == serie.T + 8
    assert list(ext.fecha[:t_real]) == list(serie.fecha)
    for campo in ("anio", "semana", "doy", "casos", "z", "oni"):
        assert np.array_equal(getattr(ext, campo)[:t_real], getattr(serie, campo), equal_nan=True), campo
    # las semanas futuras: domingos consecutivos, conteo NaN, doy de la fecha
    assert all((ext.fecha[t_real + k] - ext.fecha[t_real + k - 1]).days == 7 for k in range(8))
    assert np.isnan(ext.casos[t_real:]).all() and np.isnan(ext.z[t_real:]).all()
    assert [int(d) for d in ext.doy[t_real:]] == [f.timetuple().tm_yday for f in ext.fecha[t_real:]]
