"""Pruebas del motor de presion epidemiologica relativa (Modulo 3 de "El
Camino Ancho", backend/api/presion.py).

Solo logica pura -- no toca Postgres. Los numeros de estas pruebas son
valores arbitrarios para verificar el algoritmo (percentiles, ventanas,
anti-fuga), NO datos epidemiologicos: la verificacion contra datos MINSAL
reales vive en test_endpoints_presion.py, que corre contra la base ya
cargada. Mismo estilo unittest + sys.path.insert que test_idoneidad.py.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from api import presion  # noqa: E402
from api.idoneidad import percentil  # noqa: E402


def _serie(por_anio: dict[int, dict[int, float]]) -> dict[int, dict[int, float]]:
    """Alias declarativo: anio -> semana -> conteo."""
    return por_anio


class ConstruirPoolTest(unittest.TestCase):
    def test_anti_fuga_el_anio_descrito_nunca_esta_en_su_pool(self):
        # El anio objetivo (2019) tiene un valor extremo en la ventana; si se
        # fugara al pool, el maximo del pool lo delataria.
        serie = _serie({
            2018: {9: 1.0, 10: 2.0, 11: 3.0},
            2019: {9: 9999.0, 10: 9999.0, 11: 9999.0},
            2021: {9: 4.0, 10: 5.0, 11: 6.0},
            2022: {9: 7.0, 10: 8.0, 11: 9.0},
        })
        pool, anios = presion.construir_pool(serie, anio_objetivo=2019, semana=10)
        self.assertEqual(anios, 3)
        self.assertNotIn(9999.0, pool)
        self.assertEqual(sorted(pool), [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])

    def test_2020_jamas_aporta_al_pool_aunque_este_en_la_serie(self):
        # 2020 esta excluido de ANIOS_BASE (colapso de vigilancia real); si
        # la serie cargada lo trae, el pool no debe tocarlo.
        serie = _serie({
            2018: {10: 1.0},
            2020: {9: 5555.0, 10: 5555.0, 11: 5555.0},
            2021: {10: 2.0},
            2022: {10: 3.0},
        })
        pool, anios = presion.construir_pool(serie, anio_objetivo=2019, semana=10)
        self.assertNotIn(5555.0, pool)
        self.assertEqual(anios, 3)

    def test_ventana_mas_menos_uno_sin_wrap_en_semana_1(self):
        # Semana 1: la ventana es {1, 2} -- no existe "semana 0" y no se
        # envuelve hacia la ultima semana del anio anterior.
        serie = _serie({
            2018: {1: 10.0, 2: 20.0, 52: 999.0},
            2021: {1: 30.0, 2: 40.0, 52: 888.0},
            2022: {1: 50.0, 2: 60.0, 52: 777.0},
        })
        pool, _ = presion.construir_pool(serie, anio_objetivo=2019, semana=1)
        self.assertEqual(sorted(pool), [10.0, 20.0, 30.0, 40.0, 50.0, 60.0])

    def test_ventana_mas_menos_uno_sin_wrap_en_ultima_semana(self):
        # Ultima semana del anio: la ventana no toma la semana 1 del anio
        # siguiente (los pools son por anio, semana 53 inexistente se omite).
        serie = _serie({
            2018: {1: 999.0, 51: 10.0, 52: 20.0},
            2021: {1: 888.0, 51: 30.0, 52: 40.0},
            2022: {1: 777.0, 51: 50.0, 52: 60.0},
        })
        pool, _ = presion.construir_pool(serie, anio_objetivo=2019, semana=52)
        self.assertEqual(sorted(pool), [10.0, 20.0, 30.0, 40.0, 50.0, 60.0])

    def test_anios_presentes_cuenta_anios_distintos_no_semanas(self):
        # Un solo anio con 3 semanas en ventana: 3 observaciones pero 1 anio.
        serie = _serie({2018: {9: 1.0, 10: 2.0, 11: 3.0}})
        pool, anios = presion.construir_pool(serie, anio_objetivo=2019, semana=10)
        self.assertEqual(len(pool), 3)
        self.assertEqual(anios, 1)


class CalcularPresionTest(unittest.TestCase):
    def _serie_suficiente(self) -> dict[int, dict[int, float]]:
        # 4 anios base (leave-one-out de 2019) con observaciones en la
        # ventana de la semana 10 -- pool de 12 valores 1..12.
        return _serie({
            2018: {9: 1.0, 10: 2.0, 11: 3.0},
            2021: {9: 4.0, 10: 5.0, 11: 6.0},
            2022: {9: 7.0, 10: 8.0, 11: 9.0},
            2023: {9: 10.0, 10: 11.0, 11: 12.0},
            2019: {10: 11.5},
        })

    def test_pool_suficiente_calcula_percentil_y_categoria(self):
        r = presion.calcular_presion(self._serie_suficiente(), anio=2019, semana=10)
        self.assertEqual(r["casos_observados"], 11.5)
        self.assertEqual(r["n_obs_baseline"], 12)
        self.assertEqual(r["anios_baseline"], 4)
        self.assertNotIn("nota", r)
        # Pool 1..12: P50=6.5, P75=9.25 (interpolacion lineal inclusive).
        self.assertAlmostEqual(r["p50_baseline"], 6.5, places=1)
        self.assertAlmostEqual(r["p75_baseline"], 9.2, places=1)
        self.assertEqual(r["categoria"], "alta")  # 11.5 > P75
        # 11.5 cae entre 11 y 12 (indices 10 y 11 de 0..11): rango ~95.5.
        self.assertAlmostEqual(r["percentil"], 95.5, places=1)

    def test_celda_insuficiente_devuelve_null_con_nota_no_un_valor(self):
        # Solo 2 de los 4 anios leave-one-out aportan: bajo el piso de 3.
        serie = _serie({
            2018: {10: 1.0},
            2021: {10: 2.0},
            2019: {10: 50.0},
        })
        r = presion.calcular_presion(serie, anio=2019, semana=10)
        self.assertIsNone(r["percentil"])
        self.assertIsNone(r["categoria"])
        self.assertIsNone(r["p50_baseline"])
        self.assertIsNone(r["p75_baseline"])
        self.assertEqual(r["nota"], presion.NOTA_INSUFICIENTE)
        # La observacion real se reporta igual -- lo que falta es el
        # baseline, no el dato.
        self.assertEqual(r["casos_observados"], 50.0)

    def test_tres_anios_bastan_aunque_haya_pocas_semanas(self):
        # El piso cuenta anios distintos, no observaciones: 3 anios con una
        # sola semana cada uno cumplen.
        serie = _serie({
            2018: {10: 1.0},
            2021: {10: 2.0},
            2022: {10: 3.0},
            2019: {10: 2.5},
        })
        r = presion.calcular_presion(serie, anio=2019, semana=10)
        self.assertIsNotNone(r["percentil"])
        self.assertEqual(r["anios_baseline"], 3)
        # Pool [1,2,3]: P50=2, P75=2.5; 2.5 == P75 cae hacia abajo -> media.
        self.assertEqual(r["categoria"], "media")

    def test_sin_observacion_devuelve_null_con_nota_distinta(self):
        serie = _serie({
            2018: {10: 1.0},
            2021: {10: 2.0},
            2022: {10: 3.0},
        })
        r = presion.calcular_presion(serie, anio=2019, semana=10)
        self.assertIsNone(r["casos_observados"])
        self.assertIsNone(r["percentil"])
        self.assertEqual(r["nota"], presion.NOTA_SIN_OBSERVACION)

    def test_series_probable_y_confirmado_no_se_mezclan(self):
        # calcular_presion opera sobre UNA serie a la vez; la separacion se
        # verifica dandole series distintas y comprobando resultados
        # independientes (el endpoint las pasa por separado, ver main.py).
        probable = _serie({
            2018: {10: 100.0}, 2021: {10: 200.0}, 2022: {10: 300.0},
            2019: {10: 400.0},
        })
        confirmado = _serie({
            2018: {10: 1.0}, 2021: {10: 2.0}, 2022: {10: 3.0},
            2019: {10: 0.0},
        })
        r_prob = presion.calcular_presion(probable, anio=2019, semana=10)
        r_conf = presion.calcular_presion(confirmado, anio=2019, semana=10)
        self.assertEqual(r_prob["categoria"], "alta")
        self.assertEqual(r_conf["categoria"], "baja")
        self.assertEqual(r_prob["casos_observados"], 400.0)
        self.assertEqual(r_conf["casos_observados"], 0.0)


class CategorizarTest(unittest.TestCase):
    def test_bordes_caen_hacia_abajo_como_en_la_corrida_nacional(self):
        # Igualdad exacta con el corte cae a la categoria inferior -- misma
        # convencion que corrida_canal_endemico_nacional.clasificar.
        self.assertEqual(presion.categorizar(5.0, p50=5.0, p75=10.0), "baja")
        self.assertEqual(presion.categorizar(10.0, p50=5.0, p75=10.0), "media")
        self.assertEqual(presion.categorizar(10.1, p50=5.0, p75=10.0), "alta")
        self.assertEqual(presion.categorizar(4.9, p50=5.0, p75=10.0), "baja")
        self.assertEqual(presion.categorizar(7.0, p50=5.0, p75=10.0), "media")


class RangoPercentilTest(unittest.TestCase):
    def test_es_la_inversa_de_percentil(self):
        pool = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
        for p in (0.0, 0.25, 0.5, 0.75, 1.0):
            valor = percentil(pool, p)
            self.assertAlmostEqual(presion.rango_percentil(pool, valor), 100.0 * p, places=6)

    def test_satura_fuera_del_rango_del_pool(self):
        pool = [10.0, 20.0, 30.0]
        self.assertEqual(presion.rango_percentil(pool, 5.0), 0.0)
        self.assertEqual(presion.rango_percentil(pool, 99.0), 100.0)

    def test_empates_usan_punto_medio(self):
        # Pool con empate triple en 5.0 (indices 1, 2, 3 de 0..4): punto
        # medio = indice 2 -> 50%.
        pool = [1.0, 5.0, 5.0, 5.0, 9.0]
        self.assertAlmostEqual(presion.rango_percentil(pool, 5.0), 50.0, places=6)

    def test_pool_de_un_solo_valor(self):
        self.assertEqual(presion.rango_percentil([7.0], 7.0), 50.0)
        self.assertEqual(presion.rango_percentil([7.0], 3.0), 0.0)
        self.assertEqual(presion.rango_percentil([7.0], 9.0), 100.0)

    def test_empate_largo_de_ceros_al_inicio(self):
        # Caso caliente en M3: muchas semanas con 0 casos. El tramo de ceros
        # ocupa indices 0..3 de 0..5 -> punto medio indice 1.5 -> 30%.
        pool = [0.0, 0.0, 0.0, 0.0, 4.0, 10.0]
        self.assertAlmostEqual(presion.rango_percentil(pool, 0.0), 100.0 * 1.5 / 5.0, places=6)

    def test_empate_interno_multiple(self):
        # Empate en 3.0 sobre indices 2..5 de 0..7 -> punto medio 3.5 -> 50%.
        pool = [1.0, 2.0, 3.0, 3.0, 3.0, 3.0, 4.0, 5.0]
        self.assertAlmostEqual(presion.rango_percentil(pool, 3.0), 50.0, places=6)


if __name__ == "__main__":
    unittest.main()
