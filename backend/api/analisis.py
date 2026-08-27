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


def _iso_o_none(valor):
    return valor.isoformat() if valor is not None else None


def cargar_procedencia_observacion(
    conn,
    *,
    anio: int,
    semana: int,
    departamento_codigo: str,
    serie: str,
) -> dict | None:
    """Devuelve trazabilidad almacenada para una celda epidemiologica.

    ``None`` significa que el codigo departamental no existe. Una region
    valida sin filas devuelve ``disponible=False`` y ``registros=[]``; no se
    fabrica una fuente para un dato ausente.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT nombre
            FROM regiones
            WHERE nivel_admin = 1 AND codigo = %s
            """,
            (departamento_codigo,),
        )
        fila_region = cursor.fetchone()
        if fila_region is None:
            return None

        cursor.execute(
            """
            SELECT
                c.conteo,
                c.fecha_ingesta,
                f.codigo,
                f.nombre,
                f.url_referencia,
                b.anio,
                b.semana_archivo,
                b.nombre_archivo,
                b.url_origen,
                b.estado,
                b.validacion_cuadra,
                b.fecha_procesado
            FROM casos_epidemiologicos c
            JOIN regiones r ON r.id = c.region_id
            JOIN tipos_evento t ON t.id = c.tipo_evento_id
            JOIN fuentes_datos f ON f.id = c.fuente_id
            LEFT JOIN boletines_procesados b ON b.id = c.boletin_id
            WHERE r.codigo = %s
              AND r.nivel_admin = 1
              AND t.codigo = 'dengue'
              AND c.anio = %s
              AND c.semana_epi = %s
              AND c.clasificacion = %s
            ORDER BY f.codigo, b.nombre_archivo NULLS LAST
            """,
            (departamento_codigo, anio, semana, serie),
        )
        filas = cursor.fetchall()

    registros = []
    for (
        conteo,
        fecha_ingesta,
        fuente_codigo,
        fuente_nombre,
        fuente_url,
        boletin_anio,
        boletin_semana,
        boletin_archivo,
        boletin_url,
        estado_extraccion,
        validacion_cuadra,
        fecha_procesado,
    ) in filas:
        boletin = None
        if boletin_archivo is not None:
            boletin = {
                "anio": boletin_anio,
                "semana_archivo": boletin_semana,
                "nombre_archivo": boletin_archivo,
                "url_origen": boletin_url,
                "estado_extraccion": estado_extraccion,
                "validacion_cuadra": validacion_cuadra,
                "fecha_procesado": _iso_o_none(fecha_procesado),
            }
        registros.append(
            {
                "conteo": int(conteo),
                "fecha_ingesta": _iso_o_none(fecha_ingesta),
                "fuente": {
                    "codigo": fuente_codigo,
                    "nombre": fuente_nombre,
                    "url_referencia": fuente_url,
                },
                "boletin": boletin,
            }
        )

    return {
        "anio": anio,
        "semana_epi": semana,
        "serie": serie,
        "departamento_codigo": departamento_codigo,
        "departamento_nombre": fila_region[0],
        "disponible": bool(registros),
        "conteo_observado": sum(registro["conteo"] for registro in registros)
        if registros
        else None,
        "registros": registros,
    }


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
