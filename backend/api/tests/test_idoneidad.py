"""Pruebas del motor de idoneidad biofisica (Iv) y del Z-score continuo
(Modulos 1 y 2 de "El Camino Ancho" v3, backend/api/idoneidad.py).

Solo matematica pura -- no toca Postgres. Sigue el mismo estilo unittest +
sys.path.insert que ya usa backend/ingestion/tests/ (ver
test_validar_via_cero.py), sin introducir un framework de pruebas nuevo.
"""

from __future__ import annotations

import statistics
import sys
import unittest
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_DIR))

import idoneidad as iv_mod  # noqa: E402


class FTTest(unittest.TestCase):
    def test_fuera_de_rango_es_cero_por_definicion(self):
        self.assertEqual(iv_mod.f_T(iv_mod.TMIN), 0.0)
        self.assertEqual(iv_mod.f_T(iv_mod.TMAX), 0.0)
        self.assertEqual(iv_mod.f_T(iv_mod.TMIN - 5), 0.0)
        self.assertEqual(iv_mod.f_T(iv_mod.TMAX + 5), 0.0)
        self.assertEqual(iv_mod.f_T(-10.0), 0.0)

    def test_dentro_de_rango_es_positivo_y_acotado(self):
        for t in (18.0, 22.0, 27.0, 30.0, 35.0):
            valor = iv_mod.f_T(t)
            self.assertGreater(valor, 0.0)
            self.assertLessEqual(valor, 1.0)

    def test_normalizacion_c_produce_maximo_igual_a_uno(self):
        # Grid fino sobre [Tmin, Tmax]: el maximo de f_T debe ser ~1.0 (por
        # construccion de C_NORM), no otro valor.
        maximo = 0.0
        t = iv_mod.TMIN
        while t <= iv_mod.TMAX:
            maximo = max(maximo, iv_mod.f_T(t))
            t += 0.01
        self.assertAlmostEqual(maximo, 1.0, places=2)


class FRTest(unittest.TestCase):
    def test_en_r0_vale_un_medio(self):
        # Logistica centrada en R0: f_R(R0) = 1/(1+e^0) = 0.5 exactamente.
        self.assertAlmostEqual(iv_mod.f_R(iv_mod.R0), 0.5, places=9)

    def test_monotona_creciente(self):
        valores = [iv_mod.f_R(r) for r in (0.0, 10.0, 20.0, 30.0, 40.0, 60.0, 100.0)]
        self.assertEqual(valores, sorted(valores))

    def test_acotada_en_cero_uno(self):
        for r in (-50.0, 0.0, 30.0, 200.0):
            valor = iv_mod.f_R(r)
            self.assertGreaterEqual(valor, 0.0)
            self.assertLessEqual(valor, 1.0)


class FHTest(unittest.TestCase):
    def test_cero_en_humedad_cero(self):
        self.assertEqual(iv_mod.f_H(0.0), 0.0)

    def test_uno_desde_cincuenta_en_adelante(self):
        self.assertEqual(iv_mod.f_H(50.0), 1.0)
        self.assertEqual(iv_mod.f_H(80.0), 1.0)
        self.assertEqual(iv_mod.f_H(100.0), 1.0)

    def test_rampa_lineal_a_mitad_de_camino(self):
        self.assertAlmostEqual(iv_mod.f_H(25.0), 0.5, places=9)

    def test_nunca_negativa(self):
        self.assertEqual(iv_mod.f_H(-10.0), 0.0)


class CalcularIvTest(unittest.TestCase):
    def test_cero_si_temperatura_fuera_de_rango(self):
        # f_T=0 hace Iv=0 sin importar precipitacion/humedad favorables.
        self.assertEqual(iv_mod.calcular_Iv(10.0, 100.0, 90.0), 0.0)
        self.assertEqual(iv_mod.calcular_Iv(40.0, 100.0, 90.0), 0.0)

    def test_cero_si_humedad_cero(self):
        self.assertEqual(iv_mod.calcular_Iv(27.0, 50.0, 0.0), 0.0)

    def test_no_es_cero_en_condiciones_favorables(self):
        valor = iv_mod.calcular_Iv(27.0, 40.0, 80.0)
        self.assertGreater(valor, 0.0)
        self.assertLessEqual(valor, 1.0)

    def test_no_negativo_ni_mayor_a_uno_en_grid_amplio(self):
        for t in range(-10, 51, 5):
            for r in range(-20, 201, 20):
                for h in range(-10, 101, 10):
                    valor = iv_mod.calcular_Iv(float(t), float(r), float(h))
                    self.assertGreaterEqual(valor, 0.0)
                    self.assertLessEqual(valor, 1.0 + 1e-9)

    def test_distribucion_no_degenerada_sobre_rango_climatico_realista(self):
        """Chequeo de cordura estilo validar_leadtime_camino_ancho.py: sobre
        un grid de condiciones climaticas plausibles para El Salvador (temp
        20-32C, precip acumulada 0-150mm/2sem, HR 40-95%), Iv no debe salir
        constante ni saturado en 0 o 1 -- si sale asi, la formula no
        distingue nada real y el chequeo debe fallar, no pasar en silencio."""
        valores = []
        for t in [20 + 0.5 * i for i in range(25)]:  # 20..32
            for r in [0, 15, 30, 45, 60, 90, 120, 150]:
                for h in [40, 50, 60, 70, 80, 90, 95]:
                    valores.append(iv_mod.calcular_Iv(t, r, h))

        desv = statistics.stdev(valores)
        frac_cero = sum(1 for v in valores if v < 0.01) / len(valores)
        frac_uno = sum(1 for v in valores if v > 0.99) / len(valores)

        self.assertGreater(desv, 1e-6, "Iv sale constante sobre un rango climatico realista")
        self.assertLessEqual(frac_cero, 0.95, "Iv esta degenerado en el extremo bajo")
        self.assertLessEqual(frac_uno, 0.95, "Iv esta degenerado en el extremo alto")


class BaselineYSigmaTest(unittest.TestCase):
    def test_pool_insuficiente_devuelve_none(self):
        # Solo 2 anios distintos de anio_excluir en el corpus -> pool < 3.
        serie = {2020: {10: 0.4}, 2021: {10: 0.5}, 2022: {10: 0.6}}
        pool, mediana, desv = iv_mod.calcular_baseline_semana(
            serie, anio_excluir=2022, semana=10, anios_corpus=[2020, 2021, 2022]
        )
        self.assertEqual(len(pool), 2)
        self.assertIsNone(mediana)
        self.assertIsNone(desv)

    def test_anio_evaluado_nunca_entra_en_su_propio_baseline(self):
        serie = {a: {5: float(a - 2000)} for a in range(2014, 2025)}
        pool, mediana, desv = iv_mod.calcular_baseline_semana(
            serie, anio_excluir=2020, semana=5, anios_corpus=list(range(2014, 2025))
        )
        self.assertNotIn(20.0, pool)  # valor de 2020 (2020-2000=20) excluido
        self.assertEqual(len(pool), 10)

    def test_sigma_none_si_baseline_insuficiente(self):
        self.assertIsNone(iv_mod.calcular_sigma(0.5, None, None))

    def test_sigma_none_si_desviacion_degenerada(self):
        self.assertIsNone(iv_mod.calcular_sigma(0.5, 0.5, 0.0))

    def test_sigma_correcto_sobre_ejemplo_conocido(self):
        # pool [0.2, 0.4, 0.6] -> mediana 0.4, desv poblacional-muestral via
        # statistics.stdev = 0.2. valor=0.6 -> z=(0.6-0.4)/0.2=1.0
        pool = [0.2, 0.4, 0.6]
        mediana = statistics.median(pool)
        desv = statistics.stdev(pool)
        z = iv_mod.calcular_sigma(0.6, mediana, desv)
        self.assertAlmostEqual(z, 1.0, places=6)


class PercentilTest(unittest.TestCase):
    def test_percentil_25_50_75_sobre_lista_conocida(self):
        valores = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertAlmostEqual(iv_mod.percentil(valores, 0.5), 3.0, places=9)
        self.assertAlmostEqual(iv_mod.percentil(valores, 0.0), 1.0, places=9)
        self.assertAlmostEqual(iv_mod.percentil(valores, 1.0), 5.0, places=9)

    def test_lista_de_un_solo_valor(self):
        self.assertEqual(iv_mod.percentil([7.5], 0.25), 7.5)


class SerieIvYAcumulacionPrecipitacionTest(unittest.TestCase):
    def test_semana_uno_no_envuelve_al_anio_anterior(self):
        clima = {
            "SV-SS": {
                2019: {
                    1: {"temp_media": 27.0, "precipitation_sum": 10.0, "humedad_relativa_media": 80.0},
                }
            }
        }
        serie = iv_mod.calcular_serie_iv(clima)
        # Semana 1 no tiene semana 0 -- debe usar solo su propio valor de
        # precipitacion (10.0), no fallar ni inventar un vecino.
        esperado = iv_mod.calcular_Iv(27.0, 10.0, 80.0)
        self.assertAlmostEqual(serie["SV-SS"][2019][1], esperado, places=9)

    def test_semana_falta_variable_se_omite_sin_imputar(self):
        clima = {
            "SV-SS": {
                2019: {
                    5: {"temp_media": 27.0, "precipitation_sum": 10.0},  # falta humedad_relativa_media
                }
            }
        }
        serie = iv_mod.calcular_serie_iv(clima)
        self.assertNotIn(5, serie.get("SV-SS", {}).get(2019, {}))

    def test_acumulacion_a_dos_semanas_suma_semana_anterior(self):
        clima = {
            "SV-SS": {
                2019: {
                    5: {"temp_media": 27.0, "precipitation_sum": 10.0, "humedad_relativa_media": 80.0},
                    6: {"temp_media": 27.0, "precipitation_sum": 20.0, "humedad_relativa_media": 80.0},
                }
            }
        }
        serie = iv_mod.calcular_serie_iv(clima)
        esperado_semana_6 = iv_mod.calcular_Iv(27.0, 30.0, 80.0)  # 20 + 10 de la semana anterior
        self.assertAlmostEqual(serie["SV-SS"][2019][6], esperado_semana_6, places=9)


if __name__ == "__main__":
    unittest.main()
