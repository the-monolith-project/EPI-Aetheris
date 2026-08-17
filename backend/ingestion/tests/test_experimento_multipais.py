"""
Prueba las tres trampas de experimento_multipais.py que exige la tarea
verificar "provocando el fallo", no solo leyendo el código:

  1. La guarda de precipitation_hours: una respuesta con precipitation_sum
     nulo debe hacer que esa fila se rechace, no que entre con 0.0.
  2. El reintento por 429 de Open-Meteo: debe reintentar con backoff en vez
     de fallar directo, y devolver el resultado una vez que el servidor
     responde 200.
  3. El retroceso de semanas al cruzar el límite de año: debe usar el número
     REAL de semanas del año anterior para ese país (51/52/53, varía por
     país-año), no un valor fijo ni el tamaño de un diccionario ya filtrado
     por disponibilidad de clima (el bug confirmado del script de
     referencia que acompañó la tarea).

Sin red, sin Postgres.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from experimento_multipais import (  # noqa: E402
    _solicitar_con_reintento,
    construir_clima_semanal,
    construir_features_semana,
    extraer_diario,
    retroceder_semana,
)


# ------------------------------------------------------- guarda de lluvia -
def test_precipitation_hours_se_rechaza_si_precipitation_sum_es_nulo():
    """Provoca el fallo: precipitation_hours viene 0.0 (no null) el mismo día
    en que precipitation_sum viene null -- el 0.0 es un cero fabricado por
    el modelo, no una observación real de cero horas de lluvia."""
    respuesta_era5 = {
        "daily": {
            "time": ["2023-06-01", "2023-06-02"],
            "precipitation_sum": [12.4, None],
            "precipitation_hours": [3.0, 0.0],  # dia 2: 0.0 fabricado
        }
    }
    diario = extraer_diario(["EL SALVADOR"], {"era5": [respuesta_era5]})

    assert diario[("EL SALVADOR", "2023-06-01")]["precipitation_sum"] == 12.4
    assert diario[("EL SALVADOR", "2023-06-01")]["precipitation_hours"] == 3.0

    dia2 = diario.get(("EL SALVADOR", "2023-06-02"), {})
    assert "precipitation_sum" not in dia2, "precipitation_sum nulo no debe generar entrada"
    assert "precipitation_hours" not in dia2, (
        "precipitation_hours=0.0 con precipitation_sum nulo debe rechazarse -- "
        "quedó un cero fabricado en vez de descartar la fila"
    )


def test_precipitation_hours_se_acepta_si_precipitation_sum_es_valido():
    respuesta_era5 = {
        "daily": {
            "time": ["2023-06-01"],
            "precipitation_sum": [0.0],  # cero REAL (no llovió), sum no es null
            "precipitation_hours": [0.0],
        }
    }
    diario = extraer_diario(["EL SALVADOR"], {"era5": [respuesta_era5]})
    assert diario[("EL SALVADOR", "2023-06-01")]["precipitation_hours"] == 0.0


def test_construir_clima_semanal_descarta_semana_con_pocos_dias_validos():
    """Con >2 de 7 días rechazados por la guarda, la semana no llega al piso
    de 5 días mínimos y toda la celda país-semana se descarta (no se agrega
    con menos días de los que declara tener)."""
    dias = [f"2023-06-{i:02d}" for i in range(1, 8)]
    precip_sum = [1.0, 1.0, 1.0, None, None, None, None]  # 4 de 7 dias nulos
    precip_hours = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    resp_era5 = {"daily": {"time": dias, "precipitation_sum": precip_sum, "precipitation_hours": precip_hours}}

    otras_vars = {v: [10.0] * 7 for v in [
        "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
        "relative_humidity_2m_mean", "dew_point_2m_mean",
    ]}
    resp_era5_land = {"daily": {"time": dias, **otras_vars}}

    diario = extraer_diario(
        ["EL SALVADOR"],
        {"era5_land": [resp_era5_land], "era5": [resp_era5]},
    )
    fechas_semana = {("EL SALVADOR", 2023, 22): "2023-06-01"}
    semanal = construir_clima_semanal(diario, fechas_semana, oni_por_mes=None)
    assert ("EL SALVADOR", 2023, 22) not in semanal, (
        "solo 3 de 7 días válidos de precipitación (< piso de 5) -- la celda debía descartarse"
    )


# ------------------------------------------------------------- reintento --
def test_reintenta_con_backoff_ante_429_y_devuelve_json_final(monkeypatch):
    """Provoca el fallo: simula dos respuestas 429 seguidas y confirma que
    reintenta con backoff (sin esperar de verdad) en vez de fallar directo,
    devolviendo el JSON de la respuesta 200 final."""
    sueños = []
    monkeypatch.setattr(time, "sleep", lambda s: sueños.append(s))

    resp_429 = MagicMock(status_code=429)
    resp_200 = MagicMock(status_code=200)
    resp_200.json.return_value = {"ok": True}

    sesion = MagicMock()
    sesion.get.side_effect = [resp_429, resp_429, resp_200]

    resultado = _solicitar_con_reintento({"latitude": "1"}, sesion=sesion)

    assert resultado == {"ok": True}
    assert sesion.get.call_count == 3
    assert sueños == [15, 30], "backoff esperado: 15s en el primer reintento, 30s en el segundo"


def test_agota_reintentos_y_levanta_systemexit(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    resp_429 = MagicMock(status_code=429)
    sesion = MagicMock()
    sesion.get.return_value = resp_429

    try:
        _solicitar_con_reintento({"latitude": "1"}, sesion=sesion)
        assert False, "debía levantar SystemExit tras agotar los 5 intentos"
    except SystemExit:
        pass
    assert sesion.get.call_count == 5


# ------------------------------------------------------- retroceso de semana
def test_retroceder_dentro_del_mismo_anio():
    n_semanas = {"EL SALVADOR": {2022: 52, 2023: 52}}
    assert retroceder_semana("EL SALVADOR", 2023, 10, 2, n_semanas) == (2023, 8)


def test_retroceder_cruza_limite_de_anio_con_53_semanas_reales():
    """El año anterior tiene 53 semanas (no 52) -- el resultado debe usar
    ese número real, no un valor fijo."""
    n_semanas = {"EL SALVADOR": {2020: 53, 2021: 52}}
    # semana 1 de 2021, retrocediendo 2 pasos: -> semana 53, 52 de 2020... paso a paso:
    # paso1: semana 1 -> <1 -> anio 2020, semana = 53 (semana "53" de 2020)
    # paso2: semana 53 -> 52
    assert retroceder_semana("EL SALVADOR", 2021, 1, 2, n_semanas) == (2020, 52)


def test_retroceder_usa_semanas_reales_no_longitud_de_clima_filtrado():
    """Reproduce el bug del script de referencia: si el número de semanas del
    año anterior se leyera de un diccionario de clima ya filtrado (que puede
    tener menos celdas que semanas reales, por huecos de cobertura), el
    resultado sería distinto e incorrecto. Aquí n_semanas viene de la serie
    de casos completa (51, no 52 ni un genérico 52 de respaldo)."""
    n_semanas = {"COLOMBIA": {2018: 51, 2019: 52}}
    assert retroceder_semana("COLOMBIA", 2019, 1, 1, n_semanas) == (2018, 51)


def test_retroceder_sin_datos_del_anio_anterior_devuelve_none():
    n_semanas = {"EL SALVADOR": {2019: 52}}
    assert retroceder_semana("EL SALVADOR", 2019, 1, 1, n_semanas) is None


# --------------------------------------------- integracion: construir_features
def test_construir_features_semana_encuentra_clima_de_semanas_previas():
    """Regresion: construir_features_semana debe consultar clima_semanal con
    la clave completa (pais, anio, semana) -- una version anterior perdia el
    pais al usar el resultado de retroceder_semana (que devuelve solo
    (anio, semana)) directo como clave contra un diccionario indexado por
    3-tupla, lo que descartaba EL 100% de las filas por 'falta de historia
    climatica' incluso con clima disponible."""
    variables = ["temp_max"]
    n_semanas = {"EL SALVADOR": {2022: 52, 2023: 52}}
    clima_semanal = {
        ("EL SALVADOR", 2023, s): {"temp_max": 30.0 + s} for s in range(1, 11)
    }
    feats = construir_features_semana("EL SALVADOR", 2023, 10, clima_semanal, n_semanas, variables)
    assert feats is not None, "debia encontrar clima de las semanas 6-9 (media movil) y 8-9 (lags)"
    assert feats["temp_max_lag1"] == 39.0  # semana 9
    assert feats["temp_max_lag2"] == 38.0  # semana 8
    assert feats["temp_max_media_movil4"] == sum(30.0 + s for s in range(6, 10)) / 4
