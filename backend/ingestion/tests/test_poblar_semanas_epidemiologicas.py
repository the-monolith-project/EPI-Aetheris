"""
Verifica generar_calendario sin tocar Postgres: sin huecos, sin semanas
repetidas, y el numero de semanas por anio coincide con lo que la propia
libreria epiweeks reporta (no un numero hardcodeado aqui).
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from epiweeks import Year  # noqa: E402

from poblar_semanas_epidemiologicas import generar_calendario  # noqa: E402

ANIO_INICIO = 2018
ANIO_FIN = 2023


def test_numero_de_semanas_coincide_con_epiweeks():
    filas = generar_calendario(ANIO_INICIO, ANIO_FIN)
    por_anio: dict[int, int] = {}
    for anio, semana, _inicio, _fin in filas:
        por_anio[anio] = por_anio.get(anio, 0) + 1

    for anio in range(ANIO_INICIO, ANIO_FIN + 1):
        esperado = Year(anio, system="cdc").totalweeks()
        assert por_anio[anio] == esperado, (
            f"{anio}: generar_calendario produjo {por_anio[anio]} semanas, "
            f"epiweeks.Year reporta {esperado}"
        )


def test_sin_huecos_ni_repetidas_por_anio():
    filas = generar_calendario(ANIO_INICIO, ANIO_FIN)
    por_anio: dict[int, list[int]] = {}
    for anio, semana, _inicio, _fin in filas:
        por_anio.setdefault(anio, []).append(semana)

    for anio, semanas in por_anio.items():
        assert sorted(semanas) == list(range(1, len(semanas) + 1)), (
            f"{anio}: semanas no son 1..N consecutivas sin huecos ni repetidas: {sorted(semanas)}"
        )


def test_cada_semana_dura_siete_dias():
    filas = generar_calendario(ANIO_INICIO, ANIO_FIN)
    for anio, semana, inicio, fin in filas:
        assert fin - inicio == timedelta(days=6), (
            f"{anio}-SE{semana}: fecha_inicio={inicio} fecha_fin={fin} no son 7 dias"
        )


def test_semanas_consecutivas_dentro_de_un_anio_son_contiguas():
    filas = generar_calendario(2023, 2023)
    filas_ordenadas = sorted(filas, key=lambda f: f[1])
    for (a1, s1, _i1, f1), (a2, s2, i2, _f2) in zip(filas_ordenadas, filas_ordenadas[1:]):
        assert i2 - f1 == timedelta(days=1), (
            f"{a1}-SE{s1} termina {f1}, {a2}-SE{s2} empieza {i2} — no son contiguas"
        )
