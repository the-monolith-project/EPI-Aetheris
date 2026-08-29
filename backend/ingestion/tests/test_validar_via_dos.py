"""Pruebas de independencia y semantica de la Via 2."""

from __future__ import annotations

import copy
import os
import sys
import unittest
from pathlib import Path


INGESTION = Path(__file__).resolve().parent.parent
RAIZ_REPO = INGESTION.parent.parent
SEED = Path(
    os.environ.get(
        "VIA_DOS_SEED_SQL",
        RAIZ_REPO / "db" / "seed" / "seed_datos_reales.sql",
    )
)
sys.path.insert(0, str(INGESTION))

import validar_via_dos as via  # noqa: E402
import validar_via_menos_uno as base  # noqa: E402
import validar_via_uno as via_uno  # noqa: E402


MUTACION_FUGA = os.environ.get("VIA_DOS_MUTACION_FUGA") == "1"


def _snapshot(filas, columnas):
    return tuple(
        (
            fila["anio"], fila["semana"], fila["etiqueta"],
            fila["corte_inferior"], fila["corte_superior"],
            tuple(fila[columna] for columna in columnas),
        )
        for fila in filas
    )


class ViaDosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifiesto = via.cargar_manifesto()
        cls.datos = base.cargar_datos(SEED, cls.manifiesto)
        cls.etiquetas, cls.dataset, cls.descartes, cls.firma = via.preparar(
            cls.datos, cls.manifiesto
        )
        cls.columnas = base.columnas_predictores(cls.manifiesto)

    def test_autorizacion_fuente_y_firma_estan_congeladas(self):
        self.assertEqual(
            self.manifiesto["autorizacion"]["aprobado_por"], "Eduardo"
        )
        self.assertEqual(base.sha256(SEED), self.manifiesto["fuente"]["seed_sha256"])
        self.assertEqual(
            via.validar_firma_previa(self.firma, self.manifiesto),
            "658b193b94ad5038e9131b13a2cc4d3730e573cd503c1418fc83031c1da82614",
        )

    def test_dataset_tiene_312_filas_y_21_predictores(self):
        self.assertEqual(len(self.dataset), 312)
        self.assertEqual(len(self.columnas), 21)
        self.assertEqual(self.descartes, {})

    def test_cada_anio_tiene_distribucion_intraanual_congelada(self):
        for firma in self.firma["etiquetas_por_anio"].values():
            self.assertEqual(
                firma["distribucion"], {"bajo": 26, "medio": 13, "alto": 13}
            )

    def test_cortes_p50_p75_reproducen_percentil_lineal(self):
        for anio in self.manifiesto["etiqueta"]["anios_objetivo"]:
            valores = list(self.datos.serie[anio].values())
            firma = self.firma["etiquetas_por_anio"][str(anio)]
            self.assertEqual(
                firma["corte_p50"], base.percentil_lineal_inclusivo(valores, 0.5)
            )
            self.assertEqual(
                firma["corte_p75"], base.percentil_lineal_inclusivo(valores, 0.75)
            )

    def test_etiqueta_usa_el_anio_completo_y_se_declara_retrospectiva(self):
        resultado = self.etiquetas[(2024, 1)]
        self.assertEqual(len(resultado.pool_claves), 52)
        self.assertTrue(all(anio == 2024 for anio, _semana in resultado.pool_claves))
        self.assertFalse(self.manifiesto["etiqueta"]["prospectiva"])
        self.assertTrue(self.manifiesto["etiqueta"]["requiere_anio_completo"])

    def test_casos_del_externo_no_modifican_etiquetas_de_train(self):
        anio_externo = 2022
        datos_alterados = copy.deepcopy(self.datos)
        for semana in datos_alterados.serie[anio_externo]:
            datos_alterados.serie[anio_externo][semana] += 1_000_000
        contaminante = anio_externo if MUTACION_FUGA else None
        etiquetas_originales = via.etiquetar_intra_anual(
            self.datos,
            self.manifiesto,
            contaminar_con_anio=contaminante,
        )
        etiquetas_alteradas = via.etiquetar_intra_anual(
            datos_alterados,
            self.manifiesto,
            contaminar_con_anio=contaminante,
        )
        original = base.construir_dataset(
            self.datos, etiquetas_originales, self.manifiesto
        )[0]
        alterado = base.construir_dataset(
            datos_alterados, etiquetas_alteradas, self.manifiesto
        )[0]
        train_original = base.construir_fold(
            original, anio_externo, self.manifiesto
        )[0]
        train_alterado = base.construir_fold(
            alterado, anio_externo, self.manifiesto
        )[0]
        self.assertEqual(
            _snapshot(train_original, self.columnas),
            _snapshot(train_alterado, self.columnas),
        )

    def test_semana_objetivo_no_entra_en_features_climaticas(self):
        clave = (2022, 20)
        datos_alterados = copy.deepcopy(self.datos)
        for variable in datos_alterados.clima[clave]:
            datos_alterados.clima[clave][variable] += 1_000_000
        original = base.construir_dataset(
            self.datos, {clave: self.etiquetas[clave]}, self.manifiesto
        )[0]
        alterado = base.construir_dataset(
            datos_alterados, {clave: self.etiquetas[clave]}, self.manifiesto
        )[0]
        self.assertEqual(
            _snapshot(original, self.columnas), _snapshot(alterado, self.columnas)
        )

    def test_datos_posteriores_no_modifican_fold(self):
        anio_externo = 2022
        datos_alterados = copy.deepcopy(self.datos)
        for anio in (2023, 2024):
            for semana in datos_alterados.serie[anio]:
                datos_alterados.serie[anio][semana] += 1_000_000
        for clave, valores in datos_alterados.clima.items():
            if clave[0] > anio_externo:
                for variable in valores:
                    valores[variable] -= 1_000_000
        etiquetas_alteradas = via.etiquetar_intra_anual(
            datos_alterados, self.manifiesto
        )
        dataset_alterado = base.construir_dataset(
            datos_alterados, etiquetas_alteradas, self.manifiesto
        )[0]
        fold_original = base.construir_fold(
            self.dataset, anio_externo, self.manifiesto
        )
        fold_alterado = base.construir_fold(
            dataset_alterado, anio_externo, self.manifiesto
        )
        self.assertEqual(
            _snapshot(fold_original[0], self.columnas),
            _snapshot(fold_alterado[0], self.columnas),
        )
        self.assertEqual(
            _snapshot(fold_original[1], self.columnas),
            _snapshot(fold_alterado[1], self.columnas),
        )

    def test_todos_los_folds_son_forward_chaining_y_entrenables(self):
        for anio, firma in self.firma["folds"].items():
            self.assertEqual(firma["estado"], "entrenable")
            self.assertEqual(firma["distribucion_test"]["alto"], 13)
            train, _test = base.construir_fold(
                self.dataset, int(anio), self.manifiesto
            )
            self.assertTrue(all(fila["anio"] < int(anio) for fila in train))

    def test_cuatro_referencias_y_argmax_permanecen_fijos(self):
        self.assertEqual(
            self.manifiesto["evaluacion"]["referencias"],
            ["climatologica", "constante_mayoritaria", "siempre_alto", "persistencia"],
        )
        self.assertEqual(self.manifiesto["modelo"]["decision"], "predict_argmax")
        self.assertEqual(self.manifiesto["modelo"]["semillas_estabilidad"], list(range(10)))
        self.assertEqual(
            via_uno.configuracion_modelo(self.manifiesto),
            {"n_estimators": 300, "class_weight": "balanced", "n_jobs": -1},
        )

    def test_preliminar_retroactivo_no_se_presenta_como_comparacion_directa(self):
        self.assertEqual(
            self.manifiesto["comparacion_preliminar"]["estado"],
            "no_directamente_comparable",
        )


if __name__ == "__main__":
    unittest.main()
