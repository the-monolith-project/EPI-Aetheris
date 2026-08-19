"""Pruebas de independencia y configuracion de la Via 1."""

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
        "VIA_UNO_SEED_SQL",
        RAIZ_REPO / "db" / "seed" / "seed_datos_reales.sql",
    )
)
sys.path.insert(0, str(INGESTION))

import validar_via_menos_uno as base  # noqa: E402
import validar_via_uno as via  # noqa: E402


MUTACION_FUGA = os.environ.get("VIA_UNO_MUTACION_FUGA") == "1"


def _snapshot(filas, columnas):
    return tuple(
        (
            fila["anio"], fila["semana"], fila["etiqueta"],
            tuple(fila[columna] for columna in columnas),
        )
        for fila in filas
    )


class ViaUnoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifiesto = via.cargar_manifesto()
        cls.datos = base.cargar_datos(SEED, cls.manifiesto)
        cls.etiquetas, cls.dataset, cls.descartes, cls.firma = via.preparar(
            cls.datos, cls.manifiesto
        )
        cls.columnas = via.columnas_variantes(cls.manifiesto)

    def test_autorizacion_fuente_y_firma_estan_congeladas(self):
        self.assertEqual(
            self.manifiesto["autorizacion"]["aprobado_por"], "Eduardo"
        )
        self.assertEqual(base.sha256(SEED), self.manifiesto["fuente"]["seed_sha256"])
        self.assertEqual(
            via.validar_firma_previa(self.firma, self.manifiesto),
            "314e8662fd29c08b283a3fdfc9500591e821f633fb7d1e2cf193d648080d4e8c",
        )

    def test_variantes_tienen_tres_y_veinticuatro_predictores(self):
        self.assertEqual(len(self.columnas["solo_casos"]), 3)
        self.assertEqual(len(self.columnas["casos_mas_clima"]), 24)
        self.assertEqual(
            self.columnas["casos_mas_clima"][:3], self.columnas["solo_casos"]
        )

    def test_rezagos_que_entran_en_2020_descartan_cuatro_filas(self):
        descartadas = [
            clave
            for clave, motivo in self.descartes.items()
            if motivo == "rezago_casos_anio_excluido"
        ]
        self.assertEqual(descartadas, [(2021, 1), (2021, 2), (2021, 3), (2021, 4)])

    def test_semana_objetivo_no_entra_en_predictores(self):
        clave = (2022, 20)
        datos_alterados = copy.deepcopy(self.datos)
        datos_alterados.serie[clave[0]][clave[1]] += 1_000_000
        for variable in datos_alterados.clima[clave]:
            datos_alterados.clima[clave][variable] += 1_000_000
        original = via.construir_dataset(
            self.datos,
            {clave: self.etiquetas[clave]},
            self.manifiesto,
            incluir_semana_objetivo=MUTACION_FUGA,
        )[0]
        alterado = via.construir_dataset(
            datos_alterados,
            {clave: self.etiquetas[clave]},
            self.manifiesto,
            incluir_semana_objetivo=MUTACION_FUGA,
        )[0]
        self.assertEqual(
            _snapshot(original, self.columnas["casos_mas_clima"]),
            _snapshot(alterado, self.columnas["casos_mas_clima"]),
        )

    def test_casos_previos_si_modifican_predictores(self):
        clave = (2022, 20)
        anterior = base.claves_anteriores(self.datos, clave, 1)[0]
        datos_alterados = copy.deepcopy(self.datos)
        datos_alterados.serie[anterior[0]][anterior[1]] += 1_000_000
        original = via.construir_dataset(
            self.datos, {clave: self.etiquetas[clave]}, self.manifiesto
        )[0]
        alterado = via.construir_dataset(
            datos_alterados, {clave: self.etiquetas[clave]}, self.manifiesto
        )[0]
        self.assertNotEqual(
            _snapshot(original, self.columnas["solo_casos"]),
            _snapshot(alterado, self.columnas["solo_casos"]),
        )

    def test_casos_del_externo_no_modifican_entrenamiento(self):
        anio_externo = 2022
        datos_alterados = copy.deepcopy(self.datos)
        for semana in datos_alterados.serie[anio_externo]:
            datos_alterados.serie[anio_externo][semana] += 1_000_000
        anios = [2018, 2019, 2021, 2022]
        etiquetas_originales = base.construir_etiquetas(
            self.datos, self.manifiesto, anios
        )
        etiquetas_alteradas = base.construir_etiquetas(
            datos_alterados, self.manifiesto, anios
        )
        original = via.construir_dataset(
            self.datos, etiquetas_originales, self.manifiesto
        )[0]
        alterado = via.construir_dataset(
            datos_alterados, etiquetas_alteradas, self.manifiesto
        )[0]
        train_original = base.construir_fold(
            original, anio_externo, self.manifiesto
        )[0]
        train_alterado = base.construir_fold(
            alterado, anio_externo, self.manifiesto
        )[0]
        self.assertEqual(
            _snapshot(train_original, self.columnas["casos_mas_clima"]),
            _snapshot(train_alterado, self.columnas["casos_mas_clima"]),
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
        etiquetas_alteradas = base.construir_etiquetas(
            datos_alterados, self.manifiesto
        )
        alterado = via.construir_dataset(
            datos_alterados, etiquetas_alteradas, self.manifiesto
        )[0]
        fold_original = base.construir_fold(
            self.dataset, anio_externo, self.manifiesto
        )
        fold_alterado = base.construir_fold(
            alterado, anio_externo, self.manifiesto
        )
        self.assertEqual(
            _snapshot(fold_original[0], self.columnas["casos_mas_clima"]),
            _snapshot(fold_alterado[0], self.columnas["casos_mas_clima"]),
        )
        self.assertEqual(
            _snapshot(fold_original[1], self.columnas["casos_mas_clima"]),
            _snapshot(fold_alterado[1], self.columnas["casos_mas_clima"]),
        )

    def test_media_movil_de_casos_usa_exactamente_cuatro_semanas(self):
        fila = next(
            fila for fila in self.dataset
            if fila["anio"] == 2022 and fila["semana"] == 20
        )
        anteriores = base.claves_anteriores(self.datos, (2022, 20), 4)
        valores = [self.datos.serie[anio][semana] for anio, semana in anteriores]
        self.assertEqual(fila["casos_lag1"], valores[0])
        self.assertEqual(fila["casos_lag2"], valores[1])
        self.assertAlmostEqual(fila["casos_media_movil4"], sum(valores) / 4)

    def test_faltante_de_casos_excluye_sin_imputar(self):
        clave = (2022, 20)
        datos_alterados = copy.deepcopy(self.datos)
        anterior = base.claves_anteriores(datos_alterados, clave, 4)[2]
        del datos_alterados.serie[anterior[0]][anterior[1]]
        dataset, descartes = via.construir_dataset(
            datos_alterados, {clave: self.etiquetas[clave]}, self.manifiesto
        )
        self.assertEqual(dataset, [])
        self.assertEqual(descartes[clave], "sin_historia_casos")

    def test_persistencia_usa_semana_previa_aunque_su_fila_fue_descartada(self):
        train, test = base.construir_fold(self.dataset, 2021, self.manifiesto)
        predicciones = via.referencias(
            train, test, self.datos, self.manifiesto, self.etiquetas
        )
        self.assertEqual(test[0]["semana"], 5)
        self.assertEqual(
            predicciones["persistencia"][0], self.etiquetas[(2021, 4)].etiqueta
        )

    def test_configuracion_y_criterio_no_se_seleccionan(self):
        self.assertEqual(
            via.configuracion_modelo(self.manifiesto),
            {"n_estimators": 300, "class_weight": "balanced", "n_jobs": -1},
        )
        self.assertEqual(self.manifiesto["modelo"]["semillas_estabilidad"], list(range(10)))
        self.assertEqual(self.manifiesto["modelo"]["decision"], "predict_argmax")
        self.assertEqual(
            self.manifiesto["evaluacion"]["referencias"],
            ["climatologica", "constante_mayoritaria", "siempre_alto", "persistencia"],
        )

    def test_unico_fold_evaluable_no_tiene_alto_en_entrenamiento(self):
        evaluables = []
        for anio, firma in self.firma["folds"].items():
            if firma["distribucion_test"]["alto"]:
                evaluables.append(int(anio))
                self.assertEqual(firma["distribucion_train"]["alto"], 0)
        self.assertEqual(evaluables, [2022])


if __name__ == "__main__":
    unittest.main()
