"""Via 2: etiqueta relativa al propio anio con folds forward-chaining.

La etiqueta usa P50/P75 del anio completo y por ello la evaluacion es
reconstructiva, no prospectiva. Los predictores siguen siendo solo clima.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import sklearn

import validar_via_menos_uno as base
import validar_via_uno as via_uno


RAIZ_INGESTION = Path(__file__).resolve().parent
RAIZ_REPO = RAIZ_INGESTION.parent.parent
MANIFESTO_CONGELADO = RAIZ_INGESTION / "via_dos_manifesto_congelado.json"
SEED_DEFAULT = RAIZ_REPO / "db" / "seed" / "seed_datos_reales.sql"
SALIDA_DEFAULT = RAIZ_INGESTION / "data" / "interim" / "via_dos"

Clave = base.Clave
DatosFuente = base.DatosFuente
ErrorProtocolo = base.ErrorProtocolo


@dataclass(frozen=True)
class ResultadoEtiquetaIntra:
    anio: int
    semana: int
    casos: float
    historia: tuple[int, ...]
    n_observaciones: int
    n_anios: int
    corte_inferior: float
    corte_superior: float
    etiqueta: str
    motivo: None
    pool_claves: tuple[Clave, ...]


def cargar_manifesto() -> dict[str, Any]:
    manifiesto = json.loads(MANIFESTO_CONGELADO.read_text(encoding="utf-8"))
    if manifiesto.get("version_manifesto") != 1 or manifiesto.get("via") != 2:
        raise ErrorProtocolo("Version o via de manifiesto no soportada")
    if manifiesto.get("autorizacion", {}).get("aprobado_por") != "Eduardo":
        raise ErrorProtocolo("La Via 2 no tiene autorizacion previa registrada")
    if manifiesto["etiqueta"].get("prospectiva") is not False:
        raise ErrorProtocolo("La Via 2 debe declararse no prospectiva")
    return manifiesto


def etiquetar_intra_anual(
    datos: DatosFuente,
    manifiesto: dict[str, Any],
    *,
    contaminar_con_anio: int | None = None,
) -> dict[Clave, ResultadoEtiquetaIntra]:
    p_inferior, p_superior = [
        float(valor) for valor in manifiesto["etiqueta"]["percentiles"]
    ]
    salida: dict[Clave, ResultadoEtiquetaIntra] = {}
    for anio in manifiesto["etiqueta"]["anios_objetivo"]:
        semanas = datos.serie.get(int(anio), {})
        if len(semanas) != 52:
            raise ErrorProtocolo(
                f"La etiqueta intraanual requiere 52 semanas completas en {anio}"
            )
        pool_claves = tuple((int(anio), semana) for semana in sorted(semanas))
        valores = [semanas[semana] for _anio, semana in pool_claves]
        if contaminar_con_anio is not None and int(anio) < contaminar_con_anio:
            valores.extend(datos.serie[contaminar_con_anio].values())
        corte_inferior = base.percentil_lineal_inclusivo(valores, p_inferior)
        corte_superior = base.percentil_lineal_inclusivo(valores, p_superior)
        for _anio, semana in pool_claves:
            casos = float(semanas[semana])
            etiqueta = (
                "alto"
                if casos > corte_superior
                else "medio"
                if casos > corte_inferior
                else "bajo"
            )
            salida[(int(anio), semana)] = ResultadoEtiquetaIntra(
                anio=int(anio),
                semana=semana,
                casos=casos,
                historia=(),
                n_observaciones=len(valores),
                n_anios=1,
                corte_inferior=float(corte_inferior),
                corte_superior=float(corte_superior),
                etiqueta=etiqueta,
                motivo=None,
                pool_claves=pool_claves,
            )
    return salida


def construir_firma_previa(
    etiquetas: dict[Clave, ResultadoEtiquetaIntra],
    dataset: Sequence[dict[str, Any]],
    descartes: dict[Clave, str],
    manifiesto: dict[str, Any],
) -> dict[str, Any]:
    clases = manifiesto["evaluacion"]["clases"]
    por_anio: dict[str, Any] = {}
    for anio in manifiesto["etiqueta"]["anios_objetivo"]:
        resultados = [
            resultado
            for clave, resultado in etiquetas.items()
            if clave[0] == int(anio)
        ]
        por_anio[str(anio)] = {
            "corte_p50": resultados[0].corte_inferior,
            "corte_p75": resultados[0].corte_superior,
            "distribucion": base.distribucion(
                (resultado.etiqueta for resultado in resultados), clases
            ),
        }
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
        "columnas": base.columnas_predictores(manifiesto),
        "etiquetas_por_anio": por_anio,
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


def preparar(
    datos: DatosFuente, manifiesto: dict[str, Any]
) -> tuple[
    dict[Clave, ResultadoEtiquetaIntra],
    list[dict[str, Any]],
    dict[Clave, str],
    dict[str, Any],
]:
    etiquetas = etiquetar_intra_anual(datos, manifiesto)
    dataset, descartes = base.construir_dataset(datos, etiquetas, manifiesto)
    firma = construir_firma_previa(etiquetas, dataset, descartes, manifiesto)
    return etiquetas, dataset, descartes, firma


def ejecutar(
    datos: DatosFuente,
    dataset: Sequence[dict[str, Any]],
    manifiesto: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    resultados: dict[str, Any] = {"folds": {}}
    predicciones: list[dict[str, Any]] = []
    columnas = base.columnas_predictores(manifiesto)
    clases = manifiesto["evaluacion"]["clases"]
    for anio in manifiesto["folds_externos"]:
        train, test = base.construir_fold(dataset, int(anio), manifiesto)
        estado, marcas = base.estado_fold(train, test, clases)
        pred_referencias = base.referencias(train, test, datos, manifiesto)
        modelo, filas = via_uno.evaluar_variante(
            "solo_clima_intraanual",
            columnas,
            train,
            test,
            estado,
            pred_referencias,
            manifiesto,
        )
        for fila in filas:
            fila["anio_externo"] = int(anio)
        predicciones.extend(filas)
        resultados["folds"][str(anio)] = {
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
            "modelo": modelo,
        }
    exitos = sum(
        fold["modelo"]["estabilidad"] is not None
        and fold["modelo"]["estabilidad"]["exito_estable"] is True
        for fold in resultados["folds"].values()
    )
    cumple = exitos == len(resultados["folds"])
    resultados["conclusion"] = {
        "folds_externos": len(resultados["folds"]),
        "folds_con_exito_estable": int(exitos),
        "cumple_criterio_de_via": cumple,
        "adoptar": False,
        "recomendacion": (
            "someter_a_decision_del_coordinador"
            if cumple
            else "no_adoptar_via_dos"
        ),
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
    etiquetas: dict[Clave, ResultadoEtiquetaIntra],
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
        fila["historia"] = ""
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
    columnas = base.columnas_predictores(manifiesto)
    filas_dataset: list[dict[str, Any]] = []
    for fila in dataset:
        serializada = dict(fila)
        serializada["historia"] = ""
        filas_dataset.append(serializada)
    _escribir_csv(
        salida / "dataset.csv",
        filas_dataset,
        [
            "anio", "semana", "casos", "etiqueta", "historia",
            "n_observaciones", "n_anios", "corte_inferior",
            "corte_superior", *columnas,
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
            "predictores": len(columnas),
            "columnas": columnas,
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
        "VIA 2 — ETIQUETA RELATIVA AL PROPIO ANIO",
        f"generado_utc={manifiesto_ejecucion['generado_utc']}",
        f"firma_previa_sha256={hash_firma_previa(firma)}",
        f"dataset={len(dataset)} filas, {len(columnas)} predictores",
    ]
    for anio, fold in resultados["folds"].items():
        estabilidad = fold["modelo"]["estabilidad"]
        lineas.append(
            f"fold={anio} F1={estabilidad['f1_macro']['min']:.3f}.."
            f"{estabilidad['f1_macro']['max']:.3f} "
            f"exito_estable={estabilidad['exito_estable']}"
        )
    lineas.append("interpretacion=retrospectiva_no_prospectiva")
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
    resultados, predicciones = ejecutar(datos, dataset, manifiesto)
    escribir_artefactos(
        args.salida, args.seed_sql, manifiesto, datos, etiquetas, dataset,
        descartes, firma, resultados, predicciones,
    )
    print(f"OK: Via 2 ejecutada con {len(dataset)} filas.")
    print(json.dumps(resultados["conclusion"], ensure_ascii=False, indent=2))
    print(f"Artefactos: {args.salida}")


if __name__ == "__main__":
    main()
