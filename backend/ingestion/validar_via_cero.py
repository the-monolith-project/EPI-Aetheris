"""Vía 0: leave-one-country-out con validación temporal forward-chaining.

El experimento mantiene cada país externo completamente fuera del
entrenamiento y, para cada año externo, entrena únicamente con años objetivo
anteriores de los demás países. Lee dos fuentes crudas congeladas, no se
conecta a PostgreSQL y escribe solo bajo ``data/interim/via_cero``.

Antes de la primera corrida de modelos se debe ejecutar ``--solo-preparacion``
y registrar en el manifiesto la firma de folds observada. La corrida completa
rechaza una firma distinta de la congelada.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import sklearn
from epiweeks import Week
from sklearn.ensemble import RandomForestClassifier

from validar_via_menos_uno import (
    ResultadoEtiqueta,
    _criterio,
    _moda,
    _resumen_estabilidad,
    distribucion,
    etiquetar_anio,
    metricas_clasificacion,
    metricas_referencias,
    sha256,
)


RAIZ_INGESTION = Path(__file__).resolve().parent
RAIZ_REPO = RAIZ_INGESTION.parent.parent
MANIFESTO_CONGELADO = RAIZ_INGESTION / "via_cero_manifesto_congelado.json"
SALIDA_DEFAULT = RAIZ_INGESTION / "data" / "interim" / "via_cero"

Clave = tuple[str, int, int]


class ErrorViaCero(RuntimeError):
    """La fuente o la ejecución contradice la definición congelada."""


@dataclass
class DatosViaCero:
    serie: dict[str, dict[int, dict[int, float]]]
    fechas: dict[Clave, date]
    claves_por_fecha: dict[tuple[str, date], Clave]
    clima_semanal: dict[Clave, dict[str, float]]
    metadata: dict[str, Any]


def cargar_manifesto() -> dict[str, Any]:
    manifiesto = json.loads(MANIFESTO_CONGELADO.read_text(encoding="utf-8"))
    if manifiesto.get("version_manifesto") != 1 or manifiesto.get("via") != 0:
        raise ErrorViaCero("Versión de manifiesto no soportada")
    return manifiesto


def _ruta_default(manifiesto: dict[str, Any], fuente: str) -> Path:
    relativa = Path(manifiesto["fuentes"][fuente]["ruta_default"])
    if relativa.parts and relativa.parts[0] == "backend":
        return RAIZ_INGESTION.parent / Path(*relativa.parts[1:])
    return RAIZ_REPO / relativa


def _config_etiqueta(manifiesto: dict[str, Any]) -> dict[str, Any]:
    return {
        "fuente": {
            "casos": {
                "anio_historia_minimo": manifiesto["fuentes"]["casos"][
                    "anio_epidemiologico_minimo"
                ]
            }
        },
        "exclusiones": manifiesto["exclusiones"],
        "etiqueta": manifiesto["etiqueta"],
    }


def cargar_casos(ruta_csv: Path, manifiesto: dict[str, Any]) -> tuple[
    dict[str, dict[int, dict[int, float]]],
    dict[Clave, date],
    dict[tuple[str, date], Clave],
    dict[str, Any],
]:
    hash_observado = sha256(ruta_csv)
    hash_esperado = manifiesto["fuentes"]["casos"]["csv_sha256"]
    if hash_observado != hash_esperado:
        raise ErrorViaCero(
            "El SHA-256 del CSV de OpenDengue no coincide con el manifiesto: "
            f"esperado={hash_esperado}, observado={hash_observado}"
        )

    fuente = manifiesto["fuentes"]["casos"]
    filtros = fuente["filtros"]
    paises = tuple(manifiesto["fuentes"]["clima"]["orden_paises_descarga"])
    paises_set = set(paises)
    anio_min = int(fuente["anio_epidemiologico_minimo"])
    anio_max = int(fuente["anio_epidemiologico_maximo"])
    serie: dict[str, dict[int, dict[int, float]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    fechas: dict[Clave, date] = {}
    claves_por_fecha: dict[tuple[str, date], Clave] = {}
    anio_declarado_distinto = 0

    with ruta_csv.open(newline="", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            pais = fila["adm_0_name"]
            if pais not in paises_set:
                continue
            if any(fila[campo] != valor for campo, valor in filtros.items()):
                continue
            inicio = date.fromisoformat(fila["calendar_start_date"])
            fin = date.fromisoformat(fila["calendar_end_date"])
            if fin - inicio != timedelta(days=6):
                raise ErrorViaCero(f"Intervalo semanal inválido para {pais}: {inicio}..{fin}")
            semana = Week.fromdate(inicio)
            anio_epi, semana_epi = int(semana.year), int(semana.week)
            if not anio_min <= anio_epi <= anio_max:
                continue
            if int(fila["Year"]) != anio_epi:
                anio_declarado_distinto += 1
            clave = (pais, anio_epi, semana_epi)
            if clave in fechas:
                raise ErrorViaCero(f"Caso semanal duplicado: {clave}")
            valor = float(fila["dengue_total"])
            serie[pais][anio_epi][semana_epi] = valor
            fechas[clave] = inicio
            claves_por_fecha[(pais, inicio)] = clave

    faltantes = [pais for pais in paises if pais not in serie]
    if faltantes:
        raise ErrorViaCero(f"Países congelados sin serie semanal: {faltantes}")
    filas_por_pais = {
        pais: sum(len(semanas) for semanas in serie[pais].values()) for pais in paises
    }
    esperado_por_pais = fuente.get("filas_esperadas_por_pais")
    if esperado_por_pais is not None and any(
        cantidad != int(esperado_por_pais) for cantidad in filas_por_pais.values()
    ):
        raise ErrorViaCero(
            "La cobertura semanal por país difiere de la firma congelada: "
            f"{filas_por_pais}"
        )
    return (
        {pais: {anio: dict(semanas) for anio, semanas in anios.items()} for pais, anios in serie.items()},
        fechas,
        claves_por_fecha,
        {
            "filas": int(sum(filas_por_pais.values())),
            "filas_por_pais": filas_por_pais,
            "anio_declarado_distinto_del_epidemiologico": anio_declarado_distinto,
            "paises": list(paises),
        },
    )


def _extraer_diario(
    bruto: dict[str, Any], manifiesto: dict[str, Any]
) -> dict[tuple[str, date], dict[str, float]]:
    fuente = manifiesto["fuentes"]["clima"]
    paises = fuente["orden_paises_descarga"]
    diario: dict[tuple[str, date], dict[str, float]] = defaultdict(dict)
    for modelo, variables in fuente["modelos"].items():
        respuestas = bruto.get(modelo)
        if not isinstance(respuestas, list) or len(respuestas) != len(paises):
            raise ErrorViaCero(
                f"{modelo}: se esperaban {len(paises)} respuestas en el orden congelado"
            )
        for pais, respuesta in zip(paises, respuestas):
            datos = respuesta.get("daily", {})
            fechas = datos.get("time", [])
            if any(variable not in datos for variable in variables):
                raise ErrorViaCero(f"{modelo}/{pais}: faltan variables congeladas")
            if any(len(datos[variable]) != len(fechas) for variable in variables):
                raise ErrorViaCero(f"{modelo}/{pais}: longitudes diarias inconsistentes")
            suma_nula = None
            if "precipitation_sum" in variables:
                suma_nula = [valor is None for valor in datos["precipitation_sum"]]
            for indice, fecha_iso in enumerate(fechas):
                fecha = date.fromisoformat(fecha_iso)
                for variable in variables:
                    valor = datos[variable][indice]
                    if valor is None:
                        continue
                    if (
                        variable == "precipitation_hours"
                        and suma_nula is not None
                        and suma_nula[indice]
                    ):
                        continue
                    diario[(pais, fecha)][variable] = float(valor)
    return diario


def construir_clima_semanal(
    diario: dict[tuple[str, date], dict[str, float]],
    fechas: dict[Clave, date],
    manifiesto: dict[str, Any],
) -> tuple[dict[Clave, dict[str, float]], dict[str, int]]:
    variables = tuple(manifiesto["predictores"]["variables"])
    piso_dias = int(
        manifiesto["fuentes"]["clima"]["dias_minimos_por_semana_y_variable"]
    )
    acumulativas = {"precipitation_sum", "precipitation_hours"}
    salida: dict[Clave, dict[str, float]] = {}
    descartes: Counter[str] = Counter()
    for clave, inicio in fechas.items():
        pais = clave[0]
        por_variable: dict[str, list[float]] = defaultdict(list)
        for desplazamiento in range(7):
            valores = diario.get((pais, inicio + timedelta(days=desplazamiento)), {})
            for variable in variables:
                if variable in valores:
                    por_variable[variable].append(valores[variable])
        if any(len(por_variable[variable]) < piso_dias for variable in variables):
            descartes[pais] += 1
            continue
        salida[clave] = {
            variable: (
                float(sum(por_variable[variable]))
                if variable in acumulativas
                else float(sum(por_variable[variable]) / len(por_variable[variable]))
            )
            for variable in variables
        }
    return salida, dict(descartes)


def cargar_datos(
    ruta_casos: Path, ruta_clima: Path, manifiesto: dict[str, Any]
) -> DatosViaCero:
    serie, fechas, claves_por_fecha, metadata_casos = cargar_casos(
        ruta_casos, manifiesto
    )
    hash_clima = sha256(ruta_clima)
    esperado = manifiesto["fuentes"]["clima"]["json_sha256"]
    if hash_clima != esperado:
        raise ErrorViaCero(
            "El SHA-256 del clima no coincide con el manifiesto: "
            f"esperado={esperado}, observado={hash_clima}"
        )
    bruto = json.loads(ruta_clima.read_text(encoding="utf-8"))
    diario = _extraer_diario(bruto, manifiesto)
    clima_semanal, descartes_clima = construir_clima_semanal(
        diario, fechas, manifiesto
    )
    paises_con_clima = sorted({pais for pais, _anio, _semana in clima_semanal})
    esperados = sorted(manifiesto["paises_externos"])
    if paises_con_clima != esperados:
        raise ErrorViaCero(
            "Los países con clima completo difieren de la lista congelada: "
            f"esperados={esperados}, observados={paises_con_clima}"
        )
    return DatosViaCero(
        serie=serie,
        fechas=fechas,
        claves_por_fecha=claves_por_fecha,
        clima_semanal=clima_semanal,
        metadata={
            "casos": metadata_casos,
            "clima": {
                "celdas_semanales_completas": len(clima_semanal),
                "descartes_por_pais": descartes_clima,
                "paises_con_clima": paises_con_clima,
            },
        },
    )


def construir_etiquetas(
    datos: DatosViaCero, manifiesto: dict[str, Any]
) -> dict[Clave, ResultadoEtiqueta]:
    config = _config_etiqueta(manifiesto)
    salida: dict[Clave, ResultadoEtiqueta] = {}
    for pais in manifiesto["fuentes"]["clima"]["orden_paises_descarga"]:
        for anio in manifiesto["etiqueta"]["anios_objetivo"]:
            for (_anio, semana), resultado in etiquetar_anio(
                datos.serie[pais], int(anio), config
            ).items():
                salida[(pais, int(anio), semana)] = resultado
    return salida


def columnas_predictores(manifiesto: dict[str, Any]) -> list[str]:
    columnas: list[str] = []
    for variable in manifiesto["predictores"]["variables"]:
        columnas.extend(
            f"{variable}_lag{int(lag)}" for lag in manifiesto["predictores"]["lags"]
        )
        columnas.extend(
            f"{variable}_media_movil{int(ventana)}"
            for ventana in manifiesto["predictores"]["medias_moviles"]
        )
    return columnas


def construir_dataset(
    datos: DatosViaCero,
    etiquetas: dict[Clave, ResultadoEtiqueta],
    manifiesto: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[Clave, str]]:
    variables = tuple(manifiesto["predictores"]["variables"])
    lags = tuple(int(valor) for valor in manifiesto["predictores"]["lags"])
    ventanas = tuple(
        int(valor) for valor in manifiesto["predictores"]["medias_moviles"]
    )
    max_historia = max((*lags, *ventanas))
    paises_modelo = set(manifiesto["paises_externos"])
    filas: list[dict[str, Any]] = []
    descartes: dict[Clave, str] = {}

    for clave in sorted(
        etiquetas,
        key=lambda item: (
            manifiesto["fuentes"]["clima"]["orden_paises_descarga"].index(item[0]),
            datos.fechas[item],
        ),
    ):
        pais, anio, semana = clave
        if pais not in paises_modelo:
            continue
        resultado = etiquetas[clave]
        if resultado.etiqueta is None:
            descartes[clave] = resultado.motivo or "sin_etiqueta"
            continue
        inicio = datos.fechas[clave]
        claves_anteriores: list[Clave] = []
        for pasos in range(1, max_historia + 1):
            anterior = datos.claves_por_fecha.get(
                (pais, inicio - timedelta(days=7 * pasos))
            )
            if anterior is None:
                break
            claves_anteriores.append(anterior)
        if len(claves_anteriores) != max_historia or any(
            variable not in datos.clima_semanal.get(clave_anterior, {})
            for clave_anterior in claves_anteriores
            for variable in variables
        ):
            descartes[clave] = "sin_historia_climatica"
            continue

        features: dict[str, float] = {}
        for variable in variables:
            for lag in lags:
                features[f"{variable}_lag{lag}"] = datos.clima_semanal[
                    claves_anteriores[lag - 1]
                ][variable]
            for ventana in ventanas:
                valores = [
                    datos.clima_semanal[clave_anterior][variable]
                    for clave_anterior in claves_anteriores[:ventana]
                ]
                features[f"{variable}_media_movil{ventana}"] = float(
                    sum(valores) / ventana
                )
        filas.append(
            {
                "pais": pais,
                "anio": anio,
                "semana": semana,
                "fecha_inicio": inicio.isoformat(),
                "casos": resultado.casos,
                "etiqueta": resultado.etiqueta,
                "historia": resultado.historia,
                "n_observaciones": resultado.n_observaciones,
                "n_anios": resultado.n_anios,
                "corte_inferior": resultado.corte_inferior,
                "corte_superior": resultado.corte_superior,
                **features,
            }
        )
    return filas, descartes


def construir_fold(
    filas: Sequence[dict[str, Any]],
    pais_externo: str,
    anio_externo: int,
    manifiesto: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    objetivos = set(int(anio) for anio in manifiesto["etiqueta"]["anios_objetivo"])
    excluidos = set(int(anio) for anio in manifiesto["exclusiones"]["anios"])
    train = [
        fila
        for fila in filas
        if fila["pais"] != pais_externo
        and fila["anio"] in objetivos
        and fila["anio"] < anio_externo
        and fila["anio"] not in excluidos
    ]
    test = [
        fila
        for fila in filas
        if fila["pais"] == pais_externo and fila["anio"] == anio_externo
    ]
    orden_paises = {
        pais: indice for indice, pais in enumerate(manifiesto["paises_externos"])
    }
    train.sort(
        key=lambda fila: (
            fila["anio"],
            orden_paises[fila["pais"]],
            fila["fecha_inicio"],
        )
    )
    test.sort(key=lambda fila: fila["fecha_inicio"])
    return train, test


def estado_fold(
    train: Sequence[dict[str, Any]],
    test: Sequence[dict[str, Any]],
    clases: Sequence[str],
) -> tuple[str, list[str]]:
    clases_train = {fila["etiqueta"] for fila in train}
    if not test:
        estado = "sin_test"
    elif len(clases_train) < 2:
        estado = "no_entrenable"
    elif len(clases_train) < len(clases):
        estado = "entrenable_con_clase_ausente"
    else:
        estado = "entrenable"
    marcas: list[str] = []
    if test and not any(fila["etiqueta"] == "alto" for fila in test):
        marcas.append("recall_alto_no_evaluable")
    return estado, marcas


def construir_firma_folds(
    filas: Sequence[dict[str, Any]], manifiesto: dict[str, Any]
) -> dict[str, Any]:
    clases = manifiesto["evaluacion"]["clases"]
    folds: list[dict[str, Any]] = []
    for pais in manifiesto["paises_externos"]:
        for anio in manifiesto["folds"]["anios_externos"]:
            train, test = construir_fold(filas, pais, int(anio), manifiesto)
            estado, marcas = estado_fold(train, test, clases)
            folds.append(
                {
                    "pais_externo": pais,
                    "anio_externo": int(anio),
                    "estado": estado,
                    "marcas": marcas,
                    "n_train": len(train),
                    "n_test": len(test),
                    "distribucion_train": distribucion(
                        (fila["etiqueta"] for fila in train), clases
                    ),
                    "distribucion_test": distribucion(
                        (fila["etiqueta"] for fila in test), clases
                    ),
                }
            )
    return {"folds": folds}


def firma_sha256(firma: dict[str, Any]) -> str:
    import hashlib

    canonica = json.dumps(
        firma, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonica).hexdigest()


def validar_firma(firma: dict[str, Any], manifiesto: dict[str, Any]) -> None:
    esperada = manifiesto["folds"].get("firma_sha256")
    if not esperada:
        raise ErrorViaCero(
            "La firma de folds todavía no está congelada; ejecute --solo-preparacion"
        )
    observada = firma_sha256(firma)
    if observada != esperada:
        raise ErrorViaCero(
            "La firma de folds difiere de la congelada: "
            f"esperada={esperada}, observada={observada}"
        )


def referencias(
    train: Sequence[dict[str, Any]],
    test: Sequence[dict[str, Any]],
    manifiesto: dict[str, Any],
) -> dict[str, list[str | None]]:
    orden = manifiesto["evaluacion"]["orden_desempate"]
    por_semana: dict[int, list[str]] = defaultdict(list)
    for fila in train:
        por_semana[int(fila["semana"])].append(fila["etiqueta"])
    moda_global = _moda((fila["etiqueta"] for fila in train), orden)
    climatologica = [
        _moda(por_semana[fila["semana"]], orden, moda_global)
        if por_semana[fila["semana"]]
        else moda_global
        for fila in test
    ]
    por_fecha = {date.fromisoformat(fila["fecha_inicio"]): fila["etiqueta"] for fila in test}
    persistencia = []
    for fila in test:
        inicio = date.fromisoformat(fila["fecha_inicio"])
        anterior = inicio - timedelta(days=7)
        prediccion = por_fecha.get(anterior)
        if prediccion is not None and Week.fromdate(anterior).year != fila["anio"]:
            prediccion = None
        persistencia.append(prediccion)
    return {
        "climatologica": climatologica,
        "constante_mayoritaria": [moda_global] * len(test),
        "siempre_alto": ["alto"] * len(test),
        "persistencia": persistencia,
    }


def _matrices(
    filas: Sequence[dict[str, Any]], columnas: Sequence[str]
) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.asarray([[float(fila[columna]) for columna in columnas] for fila in filas]),
        np.asarray([fila["etiqueta"] for fila in filas]),
    )


def evaluar_fold(
    pais_externo: str,
    anio_externo: int,
    train: Sequence[dict[str, Any]],
    test: Sequence[dict[str, Any]],
    manifiesto: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    clases = manifiesto["evaluacion"]["clases"]
    columnas = columnas_predictores(manifiesto)
    estado, marcas = estado_fold(train, test, clases)
    resultado: dict[str, Any] = {
        "pais_externo": pais_externo,
        "anio_externo": anio_externo,
        "estado": estado,
        "marcas": marcas,
        "anios_entrenamiento": sorted({fila["anio"] for fila in train}),
        "paises_entrenamiento": sorted({fila["pais"] for fila in train}),
        "n_train": len(train),
        "n_test": len(test),
        "distribucion_train": distribucion(
            (fila["etiqueta"] for fila in train), clases
        ),
        "distribucion_test": distribucion(
            (fila["etiqueta"] for fila in test), clases
        ),
        "referencias": None,
        "semillas": {},
        "estabilidad": None,
        "exito_estable": None,
    }
    if estado == "sin_test" or not train:
        return resultado, []

    y_real = [fila["etiqueta"] for fila in test]
    pred_referencias = referencias(train, test, manifiesto)
    met_referencias = metricas_referencias(y_real, pred_referencias, clases)
    resultado["referencias"] = met_referencias
    predicciones: list[dict[str, Any]] = []

    if estado == "no_entrenable":
        for indice, fila in enumerate(test):
            predicciones.append(
                {
                    "pais_externo": pais_externo,
                    "anio_externo": anio_externo,
                    "semilla": "",
                    "tipo_semilla": "sin_modelo",
                    "fecha_inicio": fila["fecha_inicio"],
                    "semana": fila["semana"],
                    "etiqueta_real": fila["etiqueta"],
                    "pred_modelo": "",
                    "p_bajo": "",
                    "p_medio": "",
                    "p_alto": "",
                    **{
                        f"pred_{nombre}": valores[indice] or ""
                        for nombre, valores in pred_referencias.items()
                    },
                }
            )
        return resultado, predicciones

    X_train, y_train = _matrices(train, columnas)
    X_test, _y_test = _matrices(test, columnas)
    semillas_estabilidad = [
        int(valor) for valor in manifiesto["modelo"]["semillas_estabilidad"]
    ]
    semilla_referencia = int(manifiesto["modelo"]["semilla_referencia"])
    for semilla in [*semillas_estabilidad, semilla_referencia]:
        modelo = RandomForestClassifier(
            n_estimators=int(manifiesto["modelo"]["n_estimators"]),
            class_weight=manifiesto["modelo"]["class_weight"],
            n_jobs=int(manifiesto["modelo"]["n_jobs"]),
            random_state=semilla,
        )
        modelo.fit(X_train, y_train)
        pred_modelo = modelo.predict(X_test).tolist()
        probabilidades_crudas = modelo.predict_proba(X_test)
        indices = {clase: indice for indice, clase in enumerate(modelo.classes_)}
        probabilidades = {
            clase: (
                probabilidades_crudas[:, indices[clase]].astype(float).tolist()
                if clase in indices
                else [0.0] * len(test)
            )
            for clase in clases
        }
        metricas = metricas_clasificacion(
            y_real, pred_modelo, clases, probabilidades["alto"]
        )
        criterio = _criterio(metricas, met_referencias)
        resultado["semillas"][str(semilla)] = {
            "tipo": (
                "estabilidad"
                if semilla in semillas_estabilidad
                else "referencia_historica"
            ),
            "metricas": metricas,
            "criterio": criterio,
        }
        for indice, fila in enumerate(test):
            predicciones.append(
                {
                    "pais_externo": pais_externo,
                    "anio_externo": anio_externo,
                    "semilla": semilla,
                    "tipo_semilla": (
                        "estabilidad"
                        if semilla in semillas_estabilidad
                        else "referencia_historica"
                    ),
                    "fecha_inicio": fila["fecha_inicio"],
                    "semana": fila["semana"],
                    "etiqueta_real": fila["etiqueta"],
                    "pred_modelo": pred_modelo[indice],
                    "p_bajo": probabilidades["bajo"][indice],
                    "p_medio": probabilidades["medio"][indice],
                    "p_alto": probabilidades["alto"][indice],
                    **{
                        f"pred_{nombre}": valores[indice] or ""
                        for nombre, valores in pred_referencias.items()
                    },
                }
            )

    resultados_estabilidad = {
        str(semilla): resultado["semillas"][str(semilla)]
        for semilla in semillas_estabilidad
    }
    resultado["estabilidad"] = _resumen_estabilidad(resultados_estabilidad)
    exitos = [
        corrida["criterio"]["exito"] for corrida in resultados_estabilidad.values()
    ]
    resultado["exito_estable"] = (
        all(exito is True for exito in exitos)
        if all(exito is not None for exito in exitos)
        else None
    )
    return resultado, predicciones


def resumir_paises(
    folds: dict[str, dict[str, Any]], manifiesto: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    minimo = int(manifiesto["evaluacion"]["minimo_folds_evaluables_por_pais"])
    resumen: dict[str, Any] = {}
    for pais in manifiesto["paises_externos"]:
        propios = [fold for fold in folds.values() if fold["pais_externo"] == pais]
        evaluables = [fold for fold in propios if fold["exito_estable"] is not None]
        exitos = [fold for fold in evaluables if fold["exito_estable"] is True]
        if len(evaluables) < minimo:
            veredicto = "evidencia_insuficiente"
        elif len(exitos) == len(evaluables):
            veredicto = "transferencia_sostenida"
        else:
            veredicto = "transferencia_no_sostenida"
        resumen[pais] = {
            "folds_totales": len(propios),
            "folds_evaluables": len(evaluables),
            "folds_exito_estable": len(exitos),
            "anios_evaluables": [fold["anio_externo"] for fold in evaluables],
            "anios_exito_estable": [fold["anio_externo"] for fold in exitos],
            "veredicto": veredicto,
        }

    n_sostenidos = sum(
        datos["veredicto"] == "transferencia_sostenida" for datos in resumen.values()
    )
    if n_sostenidos <= 8:
        veredicto_via = "cerrar_multipais_por_falta_de_transferencia"
    elif n_sostenidos <= 11:
        veredicto_via = "inconcluso"
    else:
        veredicto_via = "transferencia_mayoritaria_confirmada"
    return resumen, {
        "paises_con_transferencia_sostenida": int(n_sostenidos),
        "paises_evaluados": len(manifiesto["paises_externos"]),
        "veredicto": veredicto_via,
    }


def ejecutar(
    datos: DatosViaCero,
    manifiesto: dict[str, Any],
) -> tuple[
    dict[Clave, ResultadoEtiqueta],
    list[dict[str, Any]],
    dict[Clave, str],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
]:
    etiquetas = construir_etiquetas(datos, manifiesto)
    dataset, descartes = construir_dataset(datos, etiquetas, manifiesto)
    firma = construir_firma_folds(dataset, manifiesto)
    validar_firma(firma, manifiesto)
    folds: dict[str, dict[str, Any]] = {}
    predicciones: list[dict[str, Any]] = []
    for pais in manifiesto["paises_externos"]:
        print(f"Evaluando país externo: {pais}", flush=True)
        for anio in manifiesto["folds"]["anios_externos"]:
            train, test = construir_fold(dataset, pais, int(anio), manifiesto)
            resultado, filas_prediccion = evaluar_fold(
                pais, int(anio), train, test, manifiesto
            )
            folds[f"{pais}|{anio}"] = resultado
            predicciones.extend(filas_prediccion)
    paises, conclusion = resumir_paises(folds, manifiesto)
    resultados = {
        "firma_folds_sha256": firma_sha256(firma),
        "folds": folds,
        "paises": paises,
        "conclusion": conclusion,
    }
    return etiquetas, dataset, descartes, resultados, predicciones, firma


def _escribir_csv(
    ruta: Path, filas: Sequence[dict[str, Any]], columnas: Sequence[str]
) -> None:
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)


def escribir_artefactos(
    salida: Path,
    ruta_casos: Path,
    ruta_clima: Path,
    manifiesto: dict[str, Any],
    datos: DatosViaCero,
    etiquetas: dict[Clave, ResultadoEtiqueta],
    dataset: list[dict[str, Any]],
    descartes: dict[Clave, str],
    resultados: dict[str, Any],
    predicciones: list[dict[str, Any]],
    firma: dict[str, Any],
) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    filas_etiquetas: list[dict[str, Any]] = []
    for clave in sorted(etiquetas, key=lambda item: (item[0], item[1], item[2])):
        pais, _anio, _semana = clave
        resultado = etiquetas[clave]
        fila = asdict(resultado)
        fila["pais"] = pais
        fila["fecha_inicio"] = datos.fechas[clave].isoformat()
        fila["historia"] = ",".join(str(anio) for anio in resultado.historia)
        fila["pool_claves"] = ",".join(
            f"{anio}-SE{semana:02d}" for anio, semana in resultado.pool_claves
        )
        filas_etiquetas.append(fila)
    _escribir_csv(
        salida / "etiquetas.csv",
        filas_etiquetas,
        [
            "pais",
            "anio",
            "semana",
            "fecha_inicio",
            "casos",
            "historia",
            "n_observaciones",
            "n_anios",
            "corte_inferior",
            "corte_superior",
            "etiqueta",
            "motivo",
            "pool_claves",
        ],
    )

    filas_dataset: list[dict[str, Any]] = []
    for fila in dataset:
        serializada = dict(fila)
        serializada["historia"] = ",".join(str(anio) for anio in fila["historia"])
        filas_dataset.append(serializada)
    _escribir_csv(
        salida / "dataset.csv",
        filas_dataset,
        [
            "pais",
            "anio",
            "semana",
            "fecha_inicio",
            "casos",
            "etiqueta",
            "historia",
            "n_observaciones",
            "n_anios",
            "corte_inferior",
            "corte_superior",
            *columnas_predictores(manifiesto),
        ],
    )
    _escribir_csv(
        salida / "predicciones.csv",
        predicciones,
        [
            "pais_externo",
            "anio_externo",
            "semilla",
            "tipo_semilla",
            "fecha_inicio",
            "semana",
            "etiqueta_real",
            "pred_modelo",
            "p_bajo",
            "p_medio",
            "p_alto",
            "pred_climatologica",
            "pred_constante_mayoritaria",
            "pred_siempre_alto",
            "pred_persistencia",
        ],
    )
    (salida / "metricas.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (salida / "firma_folds.json").write_text(
        json.dumps(firma, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    generado = datetime.now(timezone.utc).isoformat()
    ejecucion = {
        "generado_utc": generado,
        "comando": " ".join(sys.argv),
        "manifiesto_congelado": manifiesto,
        "hashes": {
            "casos_csv_sha256": sha256(ruta_casos),
            "clima_json_sha256": sha256(ruta_clima),
            "script_sha256": sha256(Path(__file__).resolve()),
            "manifiesto_congelado_sha256": sha256(MANIFESTO_CONGELADO),
            "firma_folds_sha256": firma_sha256(firma),
        },
        "rutas": {
            "casos_csv": str(ruta_casos.resolve()),
            "clima_json": str(ruta_clima.resolve()),
            "salida": str(salida.resolve()),
        },
        "entorno": {
            "python": sys.version.split()[0],
            "plataforma": platform.platform(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "fuente_observada": datos.metadata,
        "dataset": {
            "filas": len(dataset),
            "predictores": len(columnas_predictores(manifiesto)),
            "descartes": dict(Counter(descartes.values())),
        },
    }
    (salida / "manifiesto_ejecucion.json").write_text(
        json.dumps(ejecucion, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lineas = [
        "VIA 0 — LEAVE-ONE-COUNTRY-OUT + FORWARD-CHAINING",
        f"generado_utc={generado}",
        f"casos_sha256={ejecucion['hashes']['casos_csv_sha256']}",
        f"clima_sha256={ejecucion['hashes']['clima_json_sha256']}",
        f"firma_folds_sha256={ejecucion['hashes']['firma_folds_sha256']}",
        f"dataset={len(dataset)} filas, {len(columnas_predictores(manifiesto))} predictores",
        (
            "paises_transferencia_sostenida="
            f"{resultados['conclusion']['paises_con_transferencia_sostenida']}/"
            f"{resultados['conclusion']['paises_evaluados']}"
        ),
        f"veredicto={resultados['conclusion']['veredicto']}",
        "interpretacion=diagnostico_exploratorio_no_desempeno_final",
    ]
    (salida / "ejecucion.log").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def preparar(
    ruta_casos: Path, ruta_clima: Path, manifiesto: dict[str, Any]
) -> tuple[DatosViaCero, dict[Clave, ResultadoEtiqueta], list[dict[str, Any]], dict[Clave, str], dict[str, Any]]:
    datos = cargar_datos(ruta_casos, ruta_clima, manifiesto)
    etiquetas = construir_etiquetas(datos, manifiesto)
    dataset, descartes = construir_dataset(datos, etiquetas, manifiesto)
    firma = construir_firma_folds(dataset, manifiesto)
    return datos, etiquetas, dataset, descartes, firma


def main() -> None:
    manifiesto = cargar_manifesto()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--casos-csv", type=Path, default=_ruta_default(manifiesto, "casos")
    )
    parser.add_argument(
        "--clima-json", type=Path, default=_ruta_default(manifiesto, "clima")
    )
    parser.add_argument("--salida", type=Path, default=SALIDA_DEFAULT)
    parser.add_argument("--solo-preparacion", action="store_true")
    args = parser.parse_args()
    for ruta in (args.casos_csv, args.clima_json):
        if not ruta.is_file():
            raise SystemExit(f"No existe la fuente requerida: {ruta}")

    datos, etiquetas, dataset, descartes, firma = preparar(
        args.casos_csv, args.clima_json, manifiesto
    )
    hash_firma = firma_sha256(firma)
    estados = Counter(fold["estado"] for fold in firma["folds"])
    evaluables = sum(
        fold["distribucion_test"]["alto"] > 0 for fold in firma["folds"]
    )
    print(
        f"Preparación: {len(dataset)} filas, {len(columnas_predictores(manifiesto))} "
        f"predictores, {len(firma['folds'])} folds."
    )
    print(f"Estados: {dict(estados)}; folds con alto externo: {evaluables}")
    print(f"Firma SHA-256: {hash_firma}")
    if args.solo_preparacion:
        return

    validar_firma(firma, manifiesto)
    etiquetas, dataset, descartes, resultados, predicciones, firma = ejecutar(
        datos, manifiesto
    )
    escribir_artefactos(
        args.salida,
        args.casos_csv,
        args.clima_json,
        manifiesto,
        datos,
        etiquetas,
        dataset,
        descartes,
        resultados,
        predicciones,
        firma,
    )
    conclusion = resultados["conclusion"]
    print(
        "Resultado: "
        f"{conclusion['paises_con_transferencia_sostenida']}/"
        f"{conclusion['paises_evaluados']} países con transferencia sostenida."
    )
    print(f"Veredicto: {conclusion['veredicto']}")
    print(f"Artefactos: {args.salida}")


if __name__ == "__main__":
    main()
