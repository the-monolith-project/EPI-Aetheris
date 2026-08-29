"""Via 1: casos previos frente a casos previos mas clima.

Conserva la etiqueta y los folds limpios de la Via -1. La ejecucion completa
se rechaza hasta que la firma de preparacion quede congelada en el manifiesto.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier

import validar_via_menos_uno as base


RAIZ_INGESTION = Path(__file__).resolve().parent
RAIZ_REPO = RAIZ_INGESTION.parent.parent
MANIFESTO_CONGELADO = RAIZ_INGESTION / "via_uno_manifesto_congelado.json"
SEED_DEFAULT = RAIZ_REPO / "db" / "seed" / "seed_datos_reales.sql"
SALIDA_DEFAULT = RAIZ_INGESTION / "data" / "interim" / "via_uno"

Clave = base.Clave
DatosFuente = base.DatosFuente
ResultadoEtiqueta = base.ResultadoEtiqueta
ErrorProtocolo = base.ErrorProtocolo


def cargar_manifesto() -> dict[str, Any]:
    manifiesto = json.loads(MANIFESTO_CONGELADO.read_text(encoding="utf-8"))
    if manifiesto.get("version_manifesto") != 1 or manifiesto.get("via") != 1:
        raise ErrorProtocolo("Version o via de manifiesto no soportada")
    if manifiesto.get("autorizacion", {}).get("aprobado_por") != "Eduardo":
        raise ErrorProtocolo("La Via 1 no tiene autorizacion previa registrada")
    return manifiesto


def columnas_clima(manifiesto: dict[str, Any]) -> list[str]:
    columnas: list[str] = []
    for variable in manifiesto["predictores"]["variables"]:
        columnas.extend(
            f"{variable}_lag{int(lag)}"
            for lag in manifiesto["predictores"]["clima"]["lags"]
        )
        columnas.extend(
            f"{variable}_media_movil{int(ventana)}"
            for ventana in manifiesto["predictores"]["clima"]["medias_moviles"]
        )
    return columnas


def columnas_variantes(manifiesto: dict[str, Any]) -> dict[str, list[str]]:
    casos = list(manifiesto["predictores"]["casos"]["columnas"])
    clima = columnas_clima(manifiesto)
    if len(casos) != 3 or len(clima) != 21:
        raise ErrorProtocolo("La firma de columnas de la Via 1 no es 3 y 24")
    return {
        "solo_casos": casos,
        "casos_mas_clima": [*casos, *clima],
    }


def construir_dataset(
    datos: DatosFuente,
    etiquetas: dict[Clave, ResultadoEtiqueta],
    manifiesto: dict[str, Any],
    *,
    incluir_semana_objetivo: bool = False,
) -> tuple[list[dict[str, Any]], dict[Clave, str]]:
    filas: list[dict[str, Any]] = []
    descartes: dict[Clave, str] = {}
    variables = tuple(manifiesto["predictores"]["variables"])
    excluidos = set(int(anio) for anio in manifiesto["exclusiones"]["anios"])

    for clave, resultado in sorted(etiquetas.items()):
        if resultado.etiqueta is None:
            descartes[clave] = resultado.motivo or "sin_etiqueta"
            continue
        anteriores = base.claves_anteriores(datos, clave, 4)
        if anteriores is None:
            descartes[clave] = "sin_historia_previa"
            continue
        if incluir_semana_objetivo:
            anteriores = (clave, *anteriores[:-1])
        if any(anio in excluidos for anio, _semana in anteriores):
            descartes[clave] = "rezago_casos_anio_excluido"
            continue
        casos_previos: list[float] = []
        for anio, semana in anteriores:
            valor = datos.serie.get(anio, {}).get(semana)
            if valor is None:
                descartes[clave] = "sin_historia_casos"
                break
            casos_previos.append(float(valor))
        if clave in descartes:
            continue
        if any(
            variable not in datos.clima.get(clave_anterior, {})
            for clave_anterior in anteriores
            for variable in variables
        ):
            descartes[clave] = "sin_historia_climatica"
            continue

        features: dict[str, float] = {
            "casos_lag1": casos_previos[0],
            "casos_lag2": casos_previos[1],
            "casos_media_movil4": float(sum(casos_previos) / 4.0),
        }
        for variable in variables:
            for lag in manifiesto["predictores"]["clima"]["lags"]:
                features[f"{variable}_lag{int(lag)}"] = float(
                    datos.clima[anteriores[int(lag) - 1]][variable]
                )
            for ventana in manifiesto["predictores"]["clima"]["medias_moviles"]:
                features[f"{variable}_media_movil{int(ventana)}"] = float(
                    sum(
                        datos.clima[anterior][variable]
                        for anterior in anteriores[: int(ventana)]
                    )
                    / int(ventana)
                )

        filas.append(
            {
                "anio": resultado.anio,
                "semana": resultado.semana,
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


def referencias(
    train: Sequence[dict[str, Any]],
    test: Sequence[dict[str, Any]],
    datos: DatosFuente,
    manifiesto: dict[str, Any],
    etiquetas: dict[Clave, ResultadoEtiqueta],
) -> dict[str, list[str | None]]:
    predicciones = base.referencias(train, test, datos, manifiesto)
    etiqueta_por_clave = {
        clave: resultado.etiqueta
        for clave, resultado in etiquetas.items()
        if resultado.etiqueta is not None
    }
    persistencia: list[str | None] = []
    for fila in test:
        clave = (int(fila["anio"]), int(fila["semana"]))
        indice = datos.indice_calendario[clave]
        anterior = datos.orden_calendario[indice - 1] if indice > 0 else None
        if anterior is None or anterior[0] != clave[0]:
            persistencia.append(None)
        else:
            persistencia.append(etiqueta_por_clave.get(anterior))
    predicciones["persistencia"] = persistencia
    return predicciones


def construir_firma_previa(
    dataset: Sequence[dict[str, Any]],
    descartes: dict[Clave, str],
    manifiesto: dict[str, Any],
) -> dict[str, Any]:
    clases = manifiesto["evaluacion"]["clases"]
    columnas = columnas_variantes(manifiesto)
    folds: dict[str, Any] = {}
    for anio in manifiesto["folds_externos"]:
        train, test = base.construir_fold(dataset, int(anio), manifiesto)
        estado, marcas = base.estado_fold(train, test, clases)
        folds[str(anio)] = {
            "estado": estado,
            "marcas": marcas,
            "n_train": len(train),
            "n_test": len(test),
            "distribucion_train": base.distribucion(
                (fila["etiqueta"] for fila in train), clases
            ),
            "distribucion_test": base.distribucion(
                (fila["etiqueta"] for fila in test), clases
            ),
        }
    return {
        "filas": len(dataset),
        "columnas_variantes": columnas,
        "descartes": {
            motivo: sum(valor == motivo for valor in descartes.values())
            for motivo in sorted(set(descartes.values()))
        },
        "folds": folds,
    }


def hash_firma_previa(firma: dict[str, Any]) -> str:
    contenido = json.dumps(
        firma, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(contenido).hexdigest()


def validar_firma_previa(firma: dict[str, Any], manifiesto: dict[str, Any]) -> str:
    observado = hash_firma_previa(firma)
    esperado = manifiesto["firma_previa_sha256"]
    if esperado == "POR_CONGELAR_ANTES_DEL_PRIMER_MODELO":
        raise ErrorProtocolo("Falta congelar la firma con --solo-preparar")
    if observado != esperado:
        raise ErrorProtocolo(
            f"Firma previa distinta: esperada={esperado}, observada={observado}"
        )
    return observado


def configuracion_modelo(manifiesto: dict[str, Any]) -> dict[str, Any]:
    modelo = manifiesto["modelo"]
    return {
        "n_estimators": int(modelo["n_estimators"]),
        "class_weight": modelo["class_weight"],
        "n_jobs": int(modelo["n_jobs"]),
    }


def evaluar_variante(
    nombre: str,
    columnas: Sequence[str],
    train: Sequence[dict[str, Any]],
    test: Sequence[dict[str, Any]],
    estado: str,
    pred_referencias: dict[str, list[str | None]],
    manifiesto: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    clases = manifiesto["evaluacion"]["clases"]
    y_real = [fila["etiqueta"] for fila in test]
    met_referencias = base.metricas_referencias(y_real, pred_referencias, clases)
    resultado: dict[str, Any] = {
        "columnas": list(columnas),
        "n_predictores": len(columnas),
        "referencias": met_referencias,
        "semillas": {},
        "estabilidad": None,
    }
    filas_prediccion: list[dict[str, Any]] = []
    semillas_estabilidad = [
        int(valor) for valor in manifiesto["modelo"]["semillas_estabilidad"]
    ]
    semilla_referencia = int(manifiesto["modelo"]["semilla_referencia"])
    semillas = [*semillas_estabilidad, semilla_referencia]
    if estado == "no_entrenable":
        for indice, fila in enumerate(test):
            filas_prediccion.append(
                {
                    "variante": nombre,
                    "semilla": "",
                    "tipo_semilla": "sin_modelo",
                    "anio": fila["anio"],
                    "semana": fila["semana"],
                    "etiqueta_real": fila["etiqueta"],
                    "pred_modelo": "",
                    "p_bajo": "",
                    "p_medio": "",
                    "p_alto": "",
                    **{
                        f"pred_{referencia}": valores[indice] or ""
                        for referencia, valores in pred_referencias.items()
                    },
                }
            )
        return resultado, filas_prediccion

    X_train, y_train = base._matrices(train, columnas)
    X_test, _y_test = base._matrices(test, columnas)
    for semilla in semillas:
        modelo = RandomForestClassifier(
            random_state=semilla, **configuracion_modelo(manifiesto)
        )
        modelo.fit(X_train, y_train)
        pred_modelo = modelo.predict(X_test).tolist()
        proba_cruda = modelo.predict_proba(X_test)
        indices = {clase: indice for indice, clase in enumerate(modelo.classes_)}
        probabilidades = {
            clase: (
                proba_cruda[:, indices[clase]].astype(float).tolist()
                if clase in indices
                else [0.0] * len(test)
            )
            for clase in clases
        }
        metricas = base.metricas_clasificacion(
            y_real, pred_modelo, clases, probabilidades["alto"]
        )
        criterio = base._criterio(metricas, met_referencias)
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
            filas_prediccion.append(
                {
                    "variante": nombre,
                    "semilla": semilla,
                    "tipo_semilla": resultado["semillas"][str(semilla)]["tipo"],
                    "anio": fila["anio"],
                    "semana": fila["semana"],
                    "etiqueta_real": fila["etiqueta"],
                    "pred_modelo": pred_modelo[indice],
                    "p_bajo": probabilidades["bajo"][indice],
                    "p_medio": probabilidades["medio"][indice],
                    "p_alto": probabilidades["alto"][indice],
                    **{
                        f"pred_{referencia}": valores[indice] or ""
                        for referencia, valores in pred_referencias.items()
                    },
                }
            )
    estabilidad = base._resumen_estabilidad(
        {
            str(semilla): resultado["semillas"][str(semilla)]
            for semilla in semillas_estabilidad
        }
    )
    exitos = [
        resultado["semillas"][str(semilla)]["criterio"]["exito"]
        for semilla in semillas_estabilidad
    ]
    estabilidad["exito_estable"] = (
        None if any(valor is None for valor in exitos) else all(exitos)
    )
    resultado["estabilidad"] = estabilidad
    return resultado, filas_prediccion


def preparar(
    datos: DatosFuente, manifiesto: dict[str, Any]
) -> tuple[
    dict[Clave, ResultadoEtiqueta],
    list[dict[str, Any]],
    dict[Clave, str],
    dict[str, Any],
]:
    etiquetas = base.construir_etiquetas(datos, manifiesto)
    objetivos = set(int(anio) for anio in manifiesto["etiqueta"]["anios_objetivo"])
    etiquetas_objetivo = {
        clave: resultado
        for clave, resultado in etiquetas.items()
        if clave[0] in objetivos
    }
    dataset, descartes = construir_dataset(datos, etiquetas_objetivo, manifiesto)
    firma = construir_firma_previa(dataset, descartes, manifiesto)
    return etiquetas, dataset, descartes, firma


def ejecutar(
    datos: DatosFuente,
    etiquetas: dict[Clave, ResultadoEtiqueta],
    dataset: Sequence[dict[str, Any]],
    manifiesto: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    resultados: dict[str, Any] = {"folds": {}}
    predicciones: list[dict[str, Any]] = []
    variantes = columnas_variantes(manifiesto)
    clases = manifiesto["evaluacion"]["clases"]
    for anio in manifiesto["folds_externos"]:
        train, test = base.construir_fold(dataset, int(anio), manifiesto)
        estado, marcas = base.estado_fold(train, test, clases)
        pred_referencias = referencias(
            train, test, datos, manifiesto, etiquetas
        )
        fold: dict[str, Any] = {
            "anio_externo": int(anio),
            "estado": estado,
            "marcas": marcas,
            "anios_entrenamiento": sorted({fila["anio"] for fila in train}),
            "n_train": len(train),
            "n_test": len(test),
            "distribucion_train": base.distribucion(
                (fila["etiqueta"] for fila in train), clases
            ),
            "distribucion_test": base.distribucion(
                (fila["etiqueta"] for fila in test), clases
            ),
            "variantes": {},
        }
        for nombre, columnas in variantes.items():
            resultado, filas = evaluar_variante(
                nombre,
                columnas,
                train,
                test,
                estado,
                pred_referencias,
                manifiesto,
            )
            fold["variantes"][nombre] = resultado
            for fila in filas:
                fila["anio_externo"] = int(anio)
            predicciones.extend(filas)
        resultados["folds"][str(anio)] = fold

    evaluables = [
        fold
        for fold in resultados["folds"].values()
        if fold["distribucion_test"]["alto"] > 0
    ]
    resumen_variantes: dict[str, Any] = {}
    for nombre in variantes:
        exitos = sum(
            fold["variantes"][nombre]["estabilidad"] is not None
            and fold["variantes"][nombre]["estabilidad"]["exito_estable"] is True
            for fold in evaluables
        )
        resumen_variantes[nombre] = {
            "folds_evaluables": len(evaluables),
            "folds_con_exito_estable": int(exitos),
            "exito_de_via": bool(evaluables and exitos == len(evaluables)),
        }

    clima_justificado = False
    if evaluables:
        clima_justificado = any(
            fold["variantes"]["casos_mas_clima"]["estabilidad"]["exito_estable"]
            is True
            and fold["variantes"]["solo_casos"]["estabilidad"]["exito_estable"]
            is not True
            for fold in evaluables
        ) or all(
            fold["variantes"]["casos_mas_clima"]["estabilidad"]["f1_macro"]["min"]
            >= fold["variantes"]["solo_casos"]["estabilidad"]["f1_macro"]["max"]
            + 0.05
            and fold["variantes"]["casos_mas_clima"]["estabilidad"]["recall_alto"]["min"]
            >= fold["variantes"]["solo_casos"]["estabilidad"]["recall_alto"]["max"]
            for fold in evaluables
        )
    resultados["conclusion"] = {
        "variantes": resumen_variantes,
        "clima_sobre_casos_justificado": bool(clima_justificado),
        "adoptar": False,
        "recomendacion": "no_adoptar_via_uno",
        "interpretacion": manifiesto["interpretacion"],
    }
    return resultados, predicciones


def _escribir_csv(
    ruta: Path, filas: Sequence[dict[str, Any]], columnas: Sequence[str]
) -> None:
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)


def escribir_artefactos(
    salida: Path,
    seed_sql: Path,
    manifiesto: dict[str, Any],
    datos: DatosFuente,
    etiquetas: dict[Clave, ResultadoEtiqueta],
    dataset: Sequence[dict[str, Any]],
    descartes: dict[Clave, str],
    firma: dict[str, Any],
    resultados: dict[str, Any],
    predicciones: Sequence[dict[str, Any]],
) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    filas_etiquetas: list[dict[str, Any]] = []
    for resultado in etiquetas.values():
        fila = asdict(resultado)
        fila["historia"] = ",".join(str(anio) for anio in resultado.historia)
        fila["pool_claves"] = ",".join(
            f"{anio}-SE{semana:02d}" for anio, semana in resultado.pool_claves
        )
        filas_etiquetas.append(fila)
    _escribir_csv(
        salida / "etiquetas.csv",
        filas_etiquetas,
        [
            "anio", "semana", "casos", "historia", "n_observaciones",
            "n_anios", "corte_inferior", "corte_superior", "etiqueta",
            "motivo", "pool_claves",
        ],
    )

    columnas_dataset = columnas_variantes(manifiesto)["casos_mas_clima"]
    filas_dataset: list[dict[str, Any]] = []
    for fila in dataset:
        serializada = dict(fila)
        serializada["historia"] = ",".join(str(anio) for anio in fila["historia"])
        filas_dataset.append(serializada)
    _escribir_csv(
        salida / "dataset.csv",
        filas_dataset,
        [
            "anio", "semana", "casos", "etiqueta", "historia",
            "n_observaciones", "n_anios", "corte_inferior",
            "corte_superior", *columnas_dataset,
        ],
    )
    _escribir_csv(
        salida / "predicciones.csv",
        predicciones,
        [
            "anio_externo", "variante", "semilla", "tipo_semilla", "anio",
            "semana", "etiqueta_real", "pred_modelo", "p_bajo", "p_medio",
            "p_alto", "pred_climatologica", "pred_constante_mayoritaria",
            "pred_siempre_alto", "pred_persistencia",
        ],
    )
    for nombre, contenido in (
        ("metricas.json", resultados),
        ("firma_previa.json", firma),
    ):
        (salida / nombre).write_text(
            json.dumps(contenido, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    manifiesto_ejecucion = {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "comando": " ".join(sys.argv),
        "manifiesto_congelado": manifiesto,
        "hashes": {
            "seed_sql_sha256": base.sha256(seed_sql),
            "script_sha256": base.sha256(Path(__file__).resolve()),
            "manifiesto_congelado_sha256": base.sha256(MANIFESTO_CONGELADO),
            "firma_previa_sha256": hash_firma_previa(firma),
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
            "variantes": {
                nombre: len(columnas)
                for nombre, columnas in columnas_variantes(manifiesto).items()
            },
            "descartes": {
                motivo: sum(valor == motivo for valor in descartes.values())
                for motivo in sorted(set(descartes.values()))
            },
        },
        "rutas": {
            "seed_sql": str(seed_sql.resolve()),
            "script": str(Path(__file__).resolve()),
            "salida": str(salida.resolve()),
        },
    }
    (salida / "manifiesto_ejecucion.json").write_text(
        json.dumps(manifiesto_ejecucion, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lineas = [
        "VIA 1 — CASOS PREVIOS COMO PREDICTOR",
        f"generado_utc={manifiesto_ejecucion['generado_utc']}",
        f"firma_previa_sha256={hash_firma_previa(firma)}",
        f"dataset={len(dataset)} filas",
    ]
    for anio, fold in resultados["folds"].items():
        for nombre, variante in fold["variantes"].items():
            estabilidad = variante["estabilidad"]
            resumen = "sin modelo" if estabilidad is None else (
                f"F1 {estabilidad['f1_macro']['min']:.3f}.."
                f"{estabilidad['f1_macro']['max']:.3f}"
            )
            lineas.append(f"fold={anio} variante={nombre} {resumen}")
    lineas.append("recomendacion=no_adoptar_via_uno")
    (salida / "ejecucion.log").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-sql", type=Path, default=SEED_DEFAULT)
    parser.add_argument("--salida", type=Path, default=SALIDA_DEFAULT)
    parser.add_argument("--solo-preparar", action="store_true")
    args = parser.parse_args()
    manifiesto = cargar_manifesto()
    datos = base.cargar_datos(args.seed_sql, manifiesto)
    etiquetas, dataset, descartes, firma = preparar(datos, manifiesto)
    if args.solo_preparar:
        print(json.dumps(firma, ensure_ascii=False, indent=2))
        print(f"firma_previa_sha256={hash_firma_previa(firma)}")
        print("No se ajusto ningun modelo.")
        return
    validar_firma_previa(firma, manifiesto)
    resultados, predicciones = ejecutar(datos, etiquetas, dataset, manifiesto)
    escribir_artefactos(
        args.salida, args.seed_sql, manifiesto, datos, etiquetas, dataset,
        descartes, firma, resultados, predicciones,
    )
    print(f"OK: Via 1 ejecutada con {len(dataset)} filas.")
    print(json.dumps(resultados["conclusion"], ensure_ascii=False, indent=2))
    print(f"Artefactos: {args.salida}")


if __name__ == "__main__":
    main()
