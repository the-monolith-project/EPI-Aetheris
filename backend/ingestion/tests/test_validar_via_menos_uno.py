"""Pruebas de independencia temporal y reglas de la Via -1.

Las pruebas usan exclusivamente el seed real versionado. La variable de
entorno ``VIA_MENOS_UNO_MUTACION_FUGA=1`` activa solo dentro de este archivo
una construccion deliberadamente contaminada para demostrar que la guarda de
independencia falla. No altera el script de ejecucion ni ningun dato en disco.
"""

from __future__ import annotations

import copy
import os
import sys
import unittest
from collections import Counter
from pathlib import Path


INGESTION = Path(__file__).resolve().parent.parent
RAIZ_REPO = INGESTION.parent.parent
SEED = Path(
    os.environ.get(
        "VIA_MENOS_UNO_SEED_SQL",
        RAIZ_REPO / "db" / "seed" / "seed_datos_reales.sql",
    )
)
sys.path.insert(0, str(INGESTION))

import validar_via_menos_uno as via  # noqa: E402


MUTACION_FUGA = os.environ.get("VIA_MENOS_UNO_MUTACION_FUGA") == "1"


def _snapshot(filas):
    columnas = via.columnas_predictores(ViaMenosUnoTest.manifiesto)
    return tuple(
        (
            fila["anio"],
            fila["semana"],
            fila["etiqueta"],
            fila["corte_inferior"],
            fila["corte_superior"],
            tuple(fila[columna] for columna in columnas),
        )
        for fila in filas
    )


def _dataset_hasta_fold(datos, anio_externo: int, contaminar: bool = False):
    anios = [
        anio
        for anio in ViaMenosUnoTest.manifiesto["etiqueta"]["anios_objetivo"]
        if anio <= anio_externo
    ]
    etiquetas = {}
    for anio in anios:
        historia = None
        if contaminar and anio < anio_externo:
            historia_limpia = list(
                via.historia_permitida(datos.serie, anio, ViaMenosUnoTest.manifiesto)
            )
            historia = [*historia_limpia, anio_externo]
        etiquetas.update(
            via.etiquetar_anio(datos.serie, anio, ViaMenosUnoTest.manifiesto, historia)
        )
    return via.construir_dataset(datos, etiquetas, ViaMenosUnoTest.manifiesto)[0]


class ViaMenosUnoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifiesto = via.cargar_manifesto()
        cls.datos = via.cargar_datos(SEED, cls.manifiesto)
        cls.etiquetas = via.construir_etiquetas(cls.datos, cls.manifiesto)
        objetivos = set(cls.manifiesto["etiqueta"]["anios_objetivo"])
        etiquetas_objetivo = {
            clave: resultado
            for clave, resultado in cls.etiquetas.items()
            if clave[0] in objetivos
        }
        cls.dataset, cls.descartes = via.construir_dataset(
            cls.datos, etiquetas_objetivo, cls.manifiesto
        )

    def test_sha_del_seed_coincide_con_manifiesto_congelado(self):
        self.assertEqual(
            via.sha256(SEED), self.manifiesto["fuente"]["seed_sha256"]
        )

    def test_firma_de_etiquetas_prospectivas(self):
        esperada = {
            2016: {"sin_etiqueta": 52},
            2017: {"sin_etiqueta": 52},
            2018: {"sin_etiqueta": 2, "bajo": 50},
            2019: {"sin_etiqueta": 2, "bajo": 48, "medio": 2},
            2021: {"bajo": 52},
            2022: {"bajo": 36, "medio": 11, "alto": 5},
            2023: {"bajo": 52},
            2024: {"bajo": 52},
        }
        observada = {}
        for anio in esperada:
            conteo = Counter(
                resultado.etiqueta or "sin_etiqueta"
                for clave, resultado in self.etiquetas.items()
                if clave[0] == anio
            )
            observada[anio] = dict(conteo)
        self.assertEqual(observada, esperada)

    def test_firma_de_folds_coincide_con_declaracion_previa(self):
        clases = self.manifiesto["evaluacion"]["clases"]
        for anio_externo in self.manifiesto["folds_externos"]:
            train, test = via.construir_fold(
                self.dataset, anio_externo, self.manifiesto
            )
            estado, _marcas = via.estado_fold(train, test, clases)
            via.validar_firma_fold(
                anio_externo, train, test, estado, self.manifiesto
            )

    def test_cambiar_casos_externo_no_modifica_entrenamiento(self):
        anio_externo = 2022
        datos_alterados = copy.deepcopy(self.datos)
        for semana in datos_alterados.serie[anio_externo]:
            datos_alterados.serie[anio_externo][semana] += 1_000_000

        original = _dataset_hasta_fold(
            self.datos, anio_externo, contaminar=MUTACION_FUGA
        )
        alterado = _dataset_hasta_fold(
            datos_alterados, anio_externo, contaminar=MUTACION_FUGA
        )
        train_original = via.construir_fold(
            original, anio_externo, self.manifiesto
        )[0]
        train_alterado = via.construir_fold(
            alterado, anio_externo, self.manifiesto
        )[0]
        self.assertEqual(_snapshot(train_original), _snapshot(train_alterado))

    def test_cambiar_clima_externo_no_modifica_features_de_entrenamiento(self):
        anio_externo = 2022
        datos_alterados = copy.deepcopy(self.datos)
        for clave, variables in datos_alterados.clima.items():
            if clave[0] == anio_externo:
                for variable in variables:
                    variables[variable] += 1_000_000

        original = _dataset_hasta_fold(self.datos, anio_externo)
        alterado = _dataset_hasta_fold(datos_alterados, anio_externo)
        train_original = via.construir_fold(
            original, anio_externo, self.manifiesto
        )[0]
        train_alterado = via.construir_fold(
            alterado, anio_externo, self.manifiesto
        )[0]
        self.assertEqual(_snapshot(train_original), _snapshot(train_alterado))

    def test_datos_posteriores_no_modifican_ninguna_parte_del_fold(self):
        anio_externo = 2022
        datos_alterados = copy.deepcopy(self.datos)
        for anio in (2023, 2024):
            for semana in datos_alterados.serie[anio]:
                datos_alterados.serie[anio][semana] += 1_000_000
        for clave, variables in datos_alterados.clima.items():
            if clave[0] > anio_externo:
                for variable in variables:
                    variables[variable] -= 1_000_000

        original = _dataset_hasta_fold(self.datos, anio_externo)
        alterado = _dataset_hasta_fold(datos_alterados, anio_externo)
        fold_original = via.construir_fold(original, anio_externo, self.manifiesto)
        fold_alterado = via.construir_fold(alterado, anio_externo, self.manifiesto)
        self.assertEqual(_snapshot(fold_original[0]), _snapshot(fold_alterado[0]))
        self.assertEqual(_snapshot(fold_original[1]), _snapshot(fold_alterado[1]))

    def test_historia_nunca_incluye_objetivo_ni_futuro(self):
        for resultado in self.etiquetas.values():
            self.assertTrue(all(anio < resultado.anio for anio in resultado.historia))
            self.assertNotIn(resultado.anio, resultado.historia)
            self.assertNotIn(2020, resultado.historia)

    def test_etiqueta_reutilizada_es_identica_entre_folds(self):
        filas_2018 = None
        for anio_externo in (2019, 2021, 2022, 2023, 2024):
            train, _test = via.construir_fold(
                self.dataset, anio_externo, self.manifiesto
            )
            observada = _snapshot([fila for fila in train if fila["anio"] == 2018])
            if filas_2018 is None:
                filas_2018 = observada
            else:
                self.assertEqual(observada, filas_2018)

    def test_ventana_de_etiqueta_no_cruza_anio_y_respeta_faltantes(self):
        borde = self.etiquetas[(2018, 1)]
        self.assertEqual(borde.n_observaciones, 8)
        self.assertIsNone(borde.etiqueta)
        self.assertTrue(all(semana in (1, 2) for _anio, semana in borde.pool_claves))

        interior = self.etiquetas[(2018, 2)]
        self.assertEqual(interior.n_observaciones, 12)
        self.assertIsNotNone(interior.etiqueta)

        serie_con_faltante = copy.deepcopy(self.datos.serie)
        del serie_con_faltante[2014][2]
        recalculada = via.etiquetar_anio(
            serie_con_faltante, 2018, self.manifiesto
        )[(2018, 2)]
        self.assertEqual(recalculada.n_observaciones, 11)
        self.assertIsNone(recalculada.etiqueta)
        self.assertEqual(recalculada.motivo, "sin_suficiencia_etiqueta")

    def test_rezagos_cruzan_anios_por_fecha_y_no_por_maximo_hardcodeado(self):
        anteriores_2015 = via.claves_anteriores(self.datos, (2015, 1), 4)
        anteriores_2016 = via.claves_anteriores(self.datos, (2016, 1), 4)
        semanas_por_anio = Counter(
            semana.anio for semana in self.datos.calendario.values()
        )
        self.assertEqual(set(semanas_por_anio.values()), {52, 53})
        self.assertEqual(anteriores_2015[0], (2014, 53))
        self.assertEqual(anteriores_2016[0], (2015, 52))
        self.assertEqual(
            self.datos.calendario[(2015, 1)].fecha_inicio
            - self.datos.calendario[(2014, 53)].fecha_inicio,
            via.timedelta(days=7),
        )
        self.assertEqual(
            self.datos.calendario[(2016, 1)].fecha_inicio
            - self.datos.calendario[(2015, 52)].fecha_inicio,
            via.timedelta(days=7),
        )

    def test_semana_objetivo_no_entra_en_sus_features(self):
        clave = (2022, 20)
        datos_alterados = copy.deepcopy(self.datos)
        for variable in datos_alterados.clima[clave]:
            datos_alterados.clima[clave][variable] += 1_000_000
        etiquetas = {
            clave: self.etiquetas[clave]
        }
        fila_original = via.construir_dataset(
            self.datos, etiquetas, self.manifiesto
        )[0]
        fila_alterada = via.construir_dataset(
            datos_alterados, etiquetas, self.manifiesto
        )[0]
        self.assertEqual(_snapshot(fila_original), _snapshot(fila_alterada))

    def test_clima_faltante_excluye_fila_sin_imputar_cero(self):
        clave_objetivo = (2021, 1)
        datos_alterados = copy.deepcopy(self.datos)
        clave_previa = via.claves_anteriores(datos_alterados, clave_objetivo, 1)[0]
        del datos_alterados.clima[clave_previa]["temp_max"]
        dataset, descartes = via.construir_dataset(
            datos_alterados,
            {clave_objetivo: self.etiquetas[clave_objetivo]},
            self.manifiesto,
        )
        self.assertEqual(dataset, [])
        self.assertEqual(descartes[clave_objetivo], "sin_historia_climatica")

    def test_anio_sin_alto_conserva_metricas_y_recall_no_evaluable(self):
        _train, test = via.construir_fold(self.dataset, 2024, self.manifiesto)
        y_real = [fila["etiqueta"] for fila in test]
        y_pred = ["alto"] * len(test)
        metricas = via.metricas_clasificacion(
            y_real,
            y_pred,
            self.manifiesto["evaluacion"]["clases"],
            [1.0] * len(test),
        )
        self.assertIsNone(metricas["recall_alto"])
        self.assertIsInstance(metricas["f1_macro"], float)
        self.assertEqual(metricas["falsos_positivos_alto"], len(test))
        self.assertEqual(len(metricas["matriz_confusion"]), 3)

    def test_configuracion_no_depende_del_externo(self):
        antes = via.configuracion_modelo(self.manifiesto)
        datos_alterados = copy.deepcopy(self.datos)
        datos_alterados.serie[2024][1] += 1_000_000
        despues = via.configuracion_modelo(self.manifiesto)
        self.assertEqual(antes, despues)
        self.assertEqual(
            self.manifiesto["modelo"]["seleccion_interna"],
            "ninguna_configuracion_unica_congelada",
        )

    def test_empate_climatologico_prefiere_moda_global_y_luego_orden_fijo(self):
        orden = self.manifiesto["evaluacion"]["orden_desempate"]
        self.assertEqual(via._moda(["bajo", "medio"], orden, "medio"), "medio")
        self.assertEqual(via._moda(["bajo", "medio"], orden, "alto"), "bajo")

    def test_2016_es_no_etiquetable_por_suficiencia(self):
        resultados = [
            resultado
            for clave, resultado in self.etiquetas.items()
            if clave[0] == 2016
        ]
        self.assertEqual(len(resultados), 52)
        self.assertTrue(all(resultado.etiqueta is None for resultado in resultados))
        self.assertTrue(
            all(resultado.motivo == "sin_suficiencia_etiqueta" for resultado in resultados)
        )
        self.assertEqual(
            via.historia_permitida(self.datos.serie, 2016, self.manifiesto),
            (2014, 2015),
        )

    def test_salida_esta_aislada_de_produccion_y_script_no_importa_db(self):
        self.assertEqual(
            via.SALIDA,
            INGESTION / "data" / "interim" / "via_menos_uno",
        )
        codigo = (INGESTION / "validar_via_menos_uno.py").read_text(encoding="utf-8")
        self.assertNotIn("psycopg2", codigo)
        self.assertNotIn("joblib.dump", codigo)


if __name__ == "__main__":
    unittest.main()
