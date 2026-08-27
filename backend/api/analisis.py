"""Orquestacion del dataset analitico anual de dengue.

Este modulo no define metodologia epidemiologica nueva. Reutiliza los
motores y cargadores existentes de M1/M2 (``idoneidad.py``) y M3
(``presion.py``) para entregar, en una sola lectura, las 53 semanas de cada
departamento. Los huecos permanecen como ``None`` y las series probable y
confirmado nunca se fusionan.
"""

from __future__ import annotations

from .idoneidad import (
    ANIOS_CLIMA,
    calcular_baseline_semana,
    calcular_serie_iv,
    calcular_sigma,
    cargar_clima_departamentos,
)
from .presion import (
    ANIOS_BASE,
    SERIES,
    calcular_presion,
    cargar_casos_departamentales,
)

ANIOS_ANALISIS_DENGUE = tuple(ANIOS_BASE)
SEMANAS_EPIDEMIOLOGICAS = tuple(range(1, 54))

NOTA_SIN_CLIMA = "sin datos climaticos completos para esta semana/año en este departamento"


def construir_dataset_dengue(conn, anio: int) -> dict:
    """Construye el dataset anual sin duplicar los calculos de M1/M2/M3."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT codigo, nombre FROM regiones WHERE nivel_admin = 1 ORDER BY nombre"
        )
        departamentos = cursor.fetchall()

    anios_casos = sorted(set(ANIOS_BASE) | {anio})
    casos = cargar_casos_departamentales(conn, anios=anios_casos)
    clima = cargar_clima_departamentos(conn, anios=ANIOS_CLIMA)
    serie_iv = calcular_serie_iv(clima)

    salida_departamentos = []
    for codigo, nombre in departamentos:
        iv_departamento = serie_iv.get(codigo, {})
        casos_departamento = casos.get(codigo, {})
        semanas = []

        for semana in SEMANAS_EPIDEMIOLOGICAS:
            iv = iv_departamento.get(anio, {}).get(semana)
            _, mediana, desviacion = calcular_baseline_semana(
                iv_departamento,
                anio_excluir=anio,
                semana=semana,
            )
            sigma = calcular_sigma(iv, mediana, desviacion) if iv is not None else None

            presiones = {
                serie: calcular_presion(
                    casos_departamento.get(serie, {}),
                    anio=anio,
                    semana=semana,
                )
                for serie in SERIES
            }

            fila = {
                "semana_epi": semana,
                "probable": presiones["probable"]["casos_observados"],
                "confirmado": presiones["confirmado"]["casos_observados"],
                "iv": round(iv, 4) if iv is not None else None,
                "anomaly_sigma": round(sigma, 4) if sigma is not None else None,
                "presion_probable": presiones["probable"],
                "presion_confirmado": presiones["confirmado"],
            }
            if iv is None:
                fila["nota_clima"] = NOTA_SIN_CLIMA
            semanas.append(fila)

        salida_departamentos.append(
            {
                "codigo": codigo,
                "nombre": nombre,
                "semanas": semanas,
            }
        )

    return {
        "anio": anio,
        "anios_disponibles": list(ANIOS_ANALISIS_DENGUE),
        "series": list(SERIES),
        "departamentos": salida_departamentos,
    }
