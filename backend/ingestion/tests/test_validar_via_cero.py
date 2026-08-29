"""Pruebas de independencia espacial y temporal de la Vía 0.

Usan las dos fuentes reales congeladas. Si los datos crudos no están
disponibles, la suite se omite con una explicación porque ``data/raw`` no se
versiona. ``VIA_CERO_MUTACION_FUGA=1`` contamina deliberadamente el fold al
reintroducir el país externo y debe hacer fallar la prueba espacial.
"""

from __future__ import annotations

import copy
import os
import sys
import unittest
from collections import defaultdict
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path


INGESTION = Path(__file__).resolve().parent.parent
CASOS = Path(
    os.environ.get(
        "VIA_CERO_CASOS_CSV",
        INGESTION / "data" / "raw" / "opendengue" / "Temporal_extract_PAHO_V1_3.csv",
    )
)
CLIMA = Path(
    os.environ.get(
        "VIA_CERO_CLIMA_JSON",
        INGESTION / "data" / "raw" / "opendengue" / "clima_multipais_openmeteo.json",
    )
)
sys.path.insert(0, str(INGESTION))

import validar_via_cero as via  # noqa: E402


MUTACION_FUGA = os.environ.get("VIA_CERO_MUTACION_FUGA") == "1"


def _snapshot(filas, manifiesto):
    columnas = via.columnas_predictores(manifiesto)
    return tuple(
        (
            fila["pais"],
            fila["anio"],
            fila["semana"],
            fila["etiqueta"],
            fila["corte_inferior"],
            fila["corte_superior"],
            tuple(fila[columna] for columna in columnas),
        )
        for fila in filas
    )


def _train(filas, pais_externo, anio_externo, manifiesto):
    if MUTACION_FUGA:
        objetivos = set(manifiesto["etiqueta"]["anios_objetivo"])
        return sorted(
            [
                fila
                for fila in filas
                if fila["anio"] in objetivos and fila["anio"] < anio_externo
            ],
            key=lambda fila: (fila["anio"], fila["pais"], fila["fecha_inicio"]),
        )
    return via.construir_fold(
        filas, pais_externo, anio_externo, manifiesto
    )[0]


class ViaCeroTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CASOS.is_file() or not CLIMA.is_file():
            raise unittest.SkipTest(
                "La Vía 0 requiere las fuentes reales no versionadas de OpenDengue y Open-Meteo"
            )
        cls.manifiesto = via.cargar_manifesto()
        cls.datos, cls.etiquetas, cls.dataset, cls.descartes, cls.firma = via.preparar(
            CASOS, CLIMA, cls.manifiesto
        )

    def test_hashes_de_fuentes_coinciden_con_manifiesto(self):
        self.assertEqual(
            via.sha256(CASOS),
            self.manifiesto["fuentes"]["casos"]["csv_sha256"],
        )
        self.assertEqual(
            via.sha256(CLIMA),
            self.manifiesto["fuentes"]["clima"]["json_sha256"],
        )

    def test_calendario_se_resuelve_desde_fecha_y_no_desde_year(self):
        for pais in self.manifiesto["fuentes"]["clima"]["orden_paises_descarga"]:
            clave = (pais, 2014, 1)
            self.assertEqual(self.datos.fechas[clave], date(2013, 12, 29))
            self.assertEqual(sum(len(v) for v in self.datos.serie[pais].values()), 574)
        self.assertEqual(
            self.datos.metadata["casos"]["filas"],
            self.manifiesto["fuentes"]["casos"]["filas_esperadas_en_18_paises"],
        )

    def test_paises_sin_superficie_quedan_fuera_sin_imputacion(self):
        observados = set(self.datos.metadata["clima"]["paises_con_clima"])
        self.assertEqual(observados, set(self.manifiesto["paises_externos"]))
        for pais in self.manifiesto["exclusiones"][
            "paises_sin_cobertura_climatica_de_superficie"
        ]:
            self.assertFalse(any(clave[0] == pais for clave in self.datos.clima_semanal))

    def test_firma_y_dimensiones_de_preparacion_estan_congeladas(self):
        resumen = self.manifiesto["folds"]["firma_resumen"]
        self.assertEqual(len(self.dataset), resumen["filas_dataset"])
        self.assertEqual(len(via.columnas_predictores(self.manifiesto)), resumen["predictores"])
        self.assertEqual(len(self.firma["folds"]), resumen["folds"])
        self.assertEqual(
            sum(fold["estado"] == "entrenable" for fold in self.firma["folds"]),
            resumen["entrenables"],
        )
        self.assertEqual(
            sum(fold["distribucion_test"]["alto"] > 0 for fold in self.firma["folds"]),
            resumen["folds_con_alto_externo"],
        )
        self.assertEqual(
            via.firma_sha256(self.firma), self.manifiesto["folds"]["firma_sha256"]
        )

    def test_historia_de_etiqueta_nunca_incluye_objetivo_futuro_ni_2020(self):
        for resultado in self.etiquetas.values():
            self.assertTrue(all(anio < resultado.anio for anio in resultado.historia))
            self.assertNotIn(resultado.anio, resultado.historia)
            self.assertNotIn(2020, resultado.historia)

    def test_dataset_no_contiene_2020_y_usa_solo_objetivos_congelados(self):
        anios = {fila["anio"] for fila in self.dataset}
        self.assertNotIn(2020, anios)
        self.assertEqual(anios, set(self.manifiesto["etiqueta"]["anios_objetivo"]))

    def test_fold_excluye_pais_externo_y_anios_no_anteriores(self):
        pais, anio = "EL SALVADOR", 2022
        train, test = via.construir_fold(self.dataset, pais, anio, self.manifiesto)
        self.assertTrue(train)
        self.assertTrue(test)
        self.assertTrue(all(fila["pais"] != pais for fila in train))
        self.assertTrue(all(fila["anio"] < anio for fila in train))
        self.assertTrue(all(fila["pais"] == pais and fila["anio"] == anio for fila in test))

    def test_cambiar_casos_del_pais_externo_no_modifica_entrenamiento(self):
        pais, anio_externo = "EL SALVADOR", 2022
        serie = copy.deepcopy(self.datos.serie)
        for anio in (2018, 2019, 2021):
            for semana in serie[pais][anio]:
                serie[pais][anio][semana] += 1_000_000 + semana
        datos_alterados = replace(self.datos, serie=serie)
        etiquetas_alteradas = via.construir_etiquetas(datos_alterados, self.manifiesto)
        dataset_alterado = via.construir_dataset(
            datos_alterados, etiquetas_alteradas, self.manifiesto
        )[0]
        original = _train(self.dataset, pais, anio_externo, self.manifiesto)
        alterado = _train(dataset_alterado, pais, anio_externo, self.manifiesto)
        self.assertEqual(_snapshot(original, self.manifiesto), _snapshot(alterado, self.manifiesto))

    def test_cambiar_casos_del_anio_externo_no_modifica_entrenamiento(self):
        anio_externo = 2022
        serie = copy.deepcopy(self.datos.serie)
        for pais in self.manifiesto["paises_externos"]:
            for semana in serie[pais][anio_externo]:
                serie[pais][anio_externo][semana] += 1_000_000
        datos_alterados = replace(self.datos, serie=serie)
        etiquetas_alteradas = via.construir_etiquetas(datos_alterados, self.manifiesto)
        dataset_alterado = via.construir_dataset(
            datos_alterados, etiquetas_alteradas, self.manifiesto
        )[0]
        original = via.construir_fold(
            self.dataset, "EL SALVADOR", anio_externo, self.manifiesto
        )[0]
        alterado = via.construir_fold(
            dataset_alterado, "EL SALVADOR", anio_externo, self.manifiesto
        )[0]
        self.assertEqual(_snapshot(original, self.manifiesto), _snapshot(alterado, self.manifiesto))

    def test_cambiar_clima_del_pais_externo_no_modifica_entrenamiento(self):
        pais, anio_externo = "EL SALVADOR", 2022
        clima = dict(self.datos.clima_semanal)
        for clave, valores in list(clima.items()):
            if clave[0] == pais:
                clima[clave] = {variable: valor + 1_000_000 for variable, valor in valores.items()}
        datos_alterados = replace(self.datos, clima_semanal=clima)
        dataset_alterado = via.construir_dataset(
            datos_alterados, self.etiquetas, self.manifiesto
        )[0]
        original = via.construir_fold(
            self.dataset, pais, anio_externo, self.manifiesto
        )[0]
        alterado = via.construir_fold(
            dataset_alterado, pais, anio_externo, self.manifiesto
        )[0]
        self.assertEqual(_snapshot(original, self.manifiesto), _snapshot(alterado, self.manifiesto))

    def test_cambiar_clima_del_anio_externo_no_modifica_entrenamiento(self):
        pais_externo, anio_externo = "EL SALVADOR", 2022
        clima = dict(self.datos.clima_semanal)
        for clave, valores in list(clima.items()):
            if clave[1] == anio_externo:
                clima[clave] = {variable: valor - 1_000_000 for variable, valor in valores.items()}
        datos_alterados = replace(self.datos, clima_semanal=clima)
        dataset_alterado = via.construir_dataset(
            datos_alterados, self.etiquetas, self.manifiesto
        )[0]
        original = via.construir_fold(
            self.dataset, pais_externo, anio_externo, self.manifiesto
        )[0]
        alterado = via.construir_fold(
            dataset_alterado, pais_externo, anio_externo, self.manifiesto
        )[0]
        self.assertEqual(_snapshot(original, self.manifiesto), _snapshot(alterado, self.manifiesto))

    def test_semana_objetivo_no_entra_en_sus_features(self):
        clave = ("EL SALVADOR", 2022, 20)
        clima = dict(self.datos.clima_semanal)
        clima[clave] = {
            variable: valor + 1_000_000
            for variable, valor in clima[clave].items()
        }
        alterados = replace(self.datos, clima_semanal=clima)
        original = via.construir_dataset(
            self.datos, {clave: self.etiquetas[clave]}, self.manifiesto
        )[0]
        cambiado = via.construir_dataset(
            alterados, {clave: self.etiquetas[clave]}, self.manifiesto
        )[0]
        self.assertEqual(_snapshot(original, self.manifiesto), _snapshot(cambiado, self.manifiesto))

    def test_clima_previo_si_modifica_features_de_la_semana_objetivo(self):
        clave = ("EL SALVADOR", 2022, 20)
        inicio = self.datos.fechas[clave]
        previa = self.datos.claves_por_fecha[(clave[0], inicio - timedelta(days=7))]
        clima = dict(self.datos.clima_semanal)
        clima[previa] = {
            variable: valor + 1_000_000
            for variable, valor in clima[previa].items()
        }
        alterados = replace(self.datos, clima_semanal=clima)
        original = via.construir_dataset(
            self.datos, {clave: self.etiquetas[clave]}, self.manifiesto
        )[0]
        cambiado = via.construir_dataset(
            alterados, {clave: self.etiquetas[clave]}, self.manifiesto
        )[0]
        self.assertNotEqual(_snapshot(original, self.manifiesto), _snapshot(cambiado, self.manifiesto))

    def test_clima_faltante_descarta_fila_sin_imputar_cero(self):
        clave = ("EL SALVADOR", 2022, 20)
        inicio = self.datos.fechas[clave]
        previa = self.datos.claves_por_fecha[(clave[0], inicio - timedelta(days=7))]
        clima = dict(self.datos.clima_semanal)
        valores = dict(clima[previa])
        del valores[self.manifiesto["predictores"]["variables"][0]]
        clima[previa] = valores
        alterados = replace(self.datos, clima_semanal=clima)
        filas, descartes = via.construir_dataset(
            alterados, {clave: self.etiquetas[clave]}, self.manifiesto
        )
        self.assertEqual(filas, [])
        self.assertEqual(descartes[clave], "sin_historia_climatica")

    def test_cuatro_referencias_y_recall_na_sin_perder_metricas(self):
        fold = next(
            fold
            for fold in self.firma["folds"]
            if fold["distribucion_test"]["alto"] == 0
        )
        train, test = via.construir_fold(
            self.dataset,
            fold["pais_externo"],
            fold["anio_externo"],
            self.manifiesto,
        )
        predicciones = via.referencias(train, test, self.manifiesto)
        self.assertEqual(set(predicciones), set(self.manifiesto["evaluacion"]["referencias"]))
        metricas = via.metricas_referencias(
            [fila["etiqueta"] for fila in test],
            predicciones,
            self.manifiesto["evaluacion"]["clases"],
        )
        for referencia in metricas.values():
            self.assertIsNone(referencia["metricas"]["recall_alto"])
            self.assertIsInstance(referencia["metricas"]["f1_macro"], float)
            self.assertIn("matriz_confusion", referencia["metricas"])

    def test_configuracion_no_contiene_seleccion_ni_barrido(self):
        self.assertEqual(self.manifiesto["folds"]["seleccion_interna"], "ninguna_configuracion_fija")
        self.assertEqual(self.manifiesto["modelo"]["decision"], "argmax_predict")
        self.assertEqual(self.manifiesto["modelo"]["semillas_estabilidad"], list(range(10)))
        self.assertEqual(self.manifiesto["modelo"]["n_estimators"], 300)
        self.assertEqual(self.manifiesto["modelo"]["n_jobs"], -1)

    def test_cada_anio_externo_tiene_firmas_de_entrenamiento_no_vacias(self):
        por_anio = defaultdict(set)
        for fold in self.firma["folds"]:
            firma = tuple(fold["distribucion_train"].items())
            por_anio[fold["anio_externo"]].add(firma)
        # Las distribuciones varían porque cada fold retira un país distinto,
        # pero todos los años congelados deben producir entrenamiento real.
        self.assertEqual(set(por_anio), set(self.manifiesto["folds"]["anios_externos"]))
        self.assertTrue(all(firmas for firmas in por_anio.values()))


if __name__ == "__main__":
    unittest.main()
