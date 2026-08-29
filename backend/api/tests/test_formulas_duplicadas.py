"""Regresion de las formulas duplicadas entre backend/api y backend/ingestion.

Issue #57 / pendiente operativo en docs/contexto/02-decisiones-abiertas.md:
idoneidad.py copia f_T, f_R, f_H, calcular_Iv y el Z-score leave-one-out
desde validar_leadtime_camino_ancho.py; presion.py copia ventana/pool/
percentil/bordes de categorizar desde corrida_canal_endemico_nacional.py.
No hay paquete compartido -- si alguien cambia el script de ingestion y
olvida el modulo de api, el mapa sirve una formula distinta a la validada.

Este test importa ambos pares y falla si constantes o resultados sobre
insumos sinteticos divergen. No toca Postgres.

Divergencias deliberadas (NO son fallo; estan documentadas en los
docstrings de api/idoneidad.py y api/presion.py):

  - Alerta binaria Z>=1.5 / lead time: solo en el script de validacion.
  - Cortes P75/P90, etiquetas alto/medio/bajo y PISO_OBSERVACIONES=12:
    solo en la corrida nacional. M3 usa P50/P75, baja/media/alta y piso
    de anios, por decision del coordinador (2026-08-21).
  - rango_percentil: solo existe en api/presion.py.

Extraer un paquete compartido sigue siendo decision abierta; este test
no la cierra.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
INGESTION_DIR = BACKEND_DIR / "ingestion"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(INGESTION_DIR))

from api import idoneidad as api_iv  # noqa: E402
from api import presion as api_presion  # noqa: E402
import corrida_canal_endemico_nacional as ing_canal  # noqa: E402
import validar_leadtime_camino_ancho as ing_iv  # noqa: E402


# Etiquetas de M3 (descriptivas) vs esquema p50_p75 de la corrida nacional.
# Misma convencion de bordes; vocabulario distinto a proposito.
_MAPA_CATEGORIA = {"baja": "bajo", "media": "medio", "alta": "alto"}


def _casi_igual(a: float | None, b: float | None, places: int = 9) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) < 10 ** (-places)


class ConstantesIdoneidadTest(unittest.TestCase):
    def test_constantes_de_iv_coinciden(self):
        self.assertEqual(api_iv.TMIN, ing_iv.TMIN)
        self.assertEqual(api_iv.TMAX, ing_iv.TMAX)
        self.assertEqual(api_iv.R0, ing_iv.R0)
        self.assertEqual(api_iv.K, ing_iv.K)
        self.assertEqual(api_iv.ANIOS_CLIMA, ing_iv.ANIOS_CLIMA)

    def test_c_norm_coincide(self):
        self.assertAlmostEqual(api_iv.C_NORM, ing_iv.C_NORM, places=12)


class FormulasIvTest(unittest.TestCase):
    def test_f_t_f_r_f_h_calcular_iv_sobre_grid(self):
        temperaturas = [-5.0, 16.0, 16.001, 22.0, 27.0, 32.0, 37.999, 38.0, 45.0]
        precipitaciones = [-10.0, 0.0, 15.0, 30.0, 45.0, 100.0, 200.0]
        humedades = [-5.0, 0.0, 25.0, 50.0, 80.0, 100.0, 120.0]
        for t in temperaturas:
            self.assertAlmostEqual(api_iv.f_T(t), ing_iv.f_T(t), places=12)
        for r in precipitaciones:
            self.assertAlmostEqual(api_iv.f_R(r), ing_iv.f_R(r), places=12)
        for h in humedades:
            self.assertAlmostEqual(api_iv.f_H(h), ing_iv.f_H(h), places=12)
        for t in temperaturas:
            for r in precipitaciones:
                for h in humedades:
                    self.assertAlmostEqual(
                        api_iv.calcular_Iv(t, r, h),
                        ing_iv.calcular_Iv(t, r, h),
                        places=12,
                    )


class SerieIvTest(unittest.TestCase):
    def test_serie_iv_y_acumulacion_de_precipitacion_coinciden(self):
        clima = {
            "SV-SS": {
                2019: {
                    1: {
                        "temp_media": 27.0,
                        "precipitation_sum": 10.0,
                        "humedad_relativa_media": 80.0,
                    },
                    2: {
                        "temp_media": 28.0,
                        "precipitation_sum": 20.0,
                        "humedad_relativa_media": 70.0,
                    },
                    3: {
                        "temp_media": 15.0,  # fuera de rango termico
                        "precipitation_sum": 5.0,
                        "humedad_relativa_media": 40.0,
                    },
                    4: {
                        "temp_media": 27.0,
                        "precipitation_sum": 10.0,
                        # humedad faltante: ambas series deben omitir la semana
                    },
                }
            },
            "SV-LI": {
                2022: {
                    10: {
                        "temp_media": 24.0,
                        "precipitation_sum": 0.0,
                        "humedad_relativa_media": 55.0,
                    },
                }
            },
        }
        api_serie = api_iv.calcular_serie_iv(clima)
        ing_serie = ing_iv.calcular_serie_Iv(clima)
        self.assertEqual(set(api_serie), set(ing_serie))
        for codigo in api_serie:
            self.assertEqual(set(api_serie[codigo]), set(ing_serie[codigo]))
            for anio in api_serie[codigo]:
                self.assertEqual(
                    set(api_serie[codigo][anio]), set(ing_serie[codigo][anio])
                )
                for semana, valor in api_serie[codigo][anio].items():
                    self.assertAlmostEqual(
                        valor, ing_serie[codigo][anio][semana], places=12
                    )
        self.assertNotIn(4, api_serie["SV-SS"][2019])
        self.assertNotIn(4, ing_serie["SV-SS"][2019])


class ZScoreLeaveOneOutTest(unittest.TestCase):
    def test_baseline_y_sigma_coinciden_con_el_detalle_del_script(self):
        # Corpus 2014-2024, semana exacta, sin ventana de vecinas.
        # 2022 semana 10 es un outlier; 2023 semana 10 tiene pool degenerado
        # (todos iguales salvo el anio excluido, que no entra).
        serie: dict[int, dict[int, float]] = {}
        for anio in range(2014, 2025):
            serie[anio] = {
                10: 0.10 + 0.01 * (anio - 2014),
                20: 0.50,
            }
        serie[2022][10] = 2.0
        # Semana 30 solo en 2 anios -> pool < 3 al evaluar cualquiera.
        serie[2018][30] = 0.3
        serie[2019][30] = 0.4
        serie[2022][30] = 0.9

        anios_evaluar = [2018, 2019, 2022]
        alertas = ing_iv.calcular_alertas_por_anio(serie, anios_evaluar)
        for anio in anios_evaluar:
            for semana, valor, mediana, desv, z in alertas[anio]["detalle"]:
                pool, med_api, desv_api = api_iv.calcular_baseline_semana(
                    serie, anio_excluir=anio, semana=semana
                )
                z_api = api_iv.calcular_sigma(valor, med_api, desv_api)
                self.assertTrue(
                    _casi_igual(med_api, mediana),
                    f"mediana {anio}/SE{semana}: api={med_api} ing={mediana}",
                )
                self.assertTrue(
                    _casi_igual(desv_api, desv),
                    f"desv {anio}/SE{semana}: api={desv_api} ing={desv}",
                )
                self.assertTrue(
                    _casi_igual(z_api, z),
                    f"z {anio}/SE{semana}: api={z_api} ing={z}",
                )
                pool_ing = [
                    serie[a][semana]
                    for a in api_iv.ANIOS_CLIMA
                    if a != anio and semana in serie.get(a, {})
                ]
                self.assertEqual(sorted(pool), sorted(pool_ing))


class ConstantesPresionTest(unittest.TestCase):
    def test_anios_base_ventana_y_piso_de_anios_coinciden(self):
        self.assertEqual(api_presion.ANIOS_BASE, ing_canal.ANIOS_BASE)
        self.assertEqual(api_presion.VENTANA, ing_canal.VENTANA)
        self.assertEqual(api_presion.PISO_ANIOS_MIN, ing_canal.PISO_ANIOS_MIN)
        self.assertNotIn(2020, api_presion.ANIOS_BASE)
        self.assertNotIn(2020, ing_canal.ANIOS_BASE)


class PercentilDuplicadoTest(unittest.TestCase):
    def test_percentil_coincide_en_listas_sinteticas(self):
        listas = (
            [1.0],
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [0.0, 0.0, 0.0, 4.0, 10.0],
            [10.0, 3.0, 7.0, 3.0, 1.0, 20.0],
        )
        for valores in listas:
            for p in (0.0, 0.25, 0.50, 0.75, 0.90, 1.0):
                self.assertAlmostEqual(
                    api_iv.percentil(valores, p),
                    ing_canal.percentil(valores, p),
                    places=12,
                    msg=f"percentil({valores!r}, {p})",
                )


class VentanaYPoolTest(unittest.TestCase):
    def _serie(self) -> dict[int, dict[int, float]]:
        return {
            2018: {1: 10.0, 2: 20.0, 9: 1.0, 10: 2.0, 11: 3.0, 51: 8.0, 52: 9.0},
            2019: {9: 9999.0, 10: 9999.0, 11: 9999.0},
            2020: {9: 5555.0, 10: 5555.0, 11: 5555.0},
            2021: {1: 30.0, 2: 40.0, 9: 4.0, 10: 5.0, 11: 6.0, 51: 18.0, 52: 19.0},
            2022: {1: 50.0, 2: 60.0, 9: 7.0, 10: 8.0, 11: 9.0, 51: 28.0, 52: 29.0},
            2023: {10: 11.0},
        }

    def test_semanas_en_ventana_coinciden(self):
        serie = self._serie()
        for anio, semanas in serie.items():
            for semana in (1, 10, 52, 53):
                api_vals = api_presion._semanas_en_ventana(semanas, semana)
                ing_vals = ing_canal._semanas_en_ventana(serie, anio, semana)
                self.assertEqual(
                    api_vals,
                    ing_vals,
                    msg=f"ventana {anio}/SE{semana}",
                )

    def test_construir_pool_coincide_incluyendo_anti_fuga_y_exclusion_2020(self):
        serie = self._serie()
        for anio_objetivo in (2018, 2019, 2021, 2022, 2023):
            for semana in (1, 10, 52):
                pool_api, anios_api = api_presion.construir_pool(
                    serie, anio_objetivo, semana
                )
                pool_ing, anios_ing = ing_canal.construir_pool(
                    serie, anio_objetivo, semana
                )
                self.assertEqual(anios_api, anios_ing, msg=f"{anio_objetivo}/SE{semana}")
                self.assertEqual(
                    sorted(pool_api),
                    sorted(pool_ing),
                    msg=f"{anio_objetivo}/SE{semana}",
                )
                self.assertNotIn(5555.0, pool_api)
                self.assertNotIn(5555.0, pool_ing)
                if anio_objetivo == 2019:
                    self.assertNotIn(9999.0, pool_api)
                    self.assertNotIn(9999.0, pool_ing)


class CategorizarVsClasificarTest(unittest.TestCase):
    def test_esquema_p50_p75_coincide_salvo_vocabulario(self):
        p50, p75, p90 = 5.0, 10.0, 20.0
        for valor in (4.9, 5.0, 5.1, 9.9, 10.0, 10.1, 19.9, 20.0, 20.1, 0.0, 100.0):
            categoria = api_presion.categorizar(valor, p50, p75)
            _, esquema_p50_p75 = ing_canal.clasificar(valor, p50, p75, p90)
            self.assertEqual(
                _MAPA_CATEGORIA[categoria],
                esquema_p50_p75,
                msg=f"valor={valor}",
            )


class CeldaPresionVsCorridaTest(unittest.TestCase):
    def test_pool_percentiles_y_categoria_p50_p75_sobre_serie_sintetica(self):
        serie = {
            2018: {9: 1.0, 10: 2.0, 11: 3.0},
            2019: {10: 11.5},
            2021: {9: 4.0, 10: 5.0, 11: 6.0},
            2022: {9: 7.0, 10: 8.0, 11: 9.0},
            2023: {9: 10.0, 10: 11.0, 11: 12.0},
        }
        resultado = api_presion.calcular_presion(serie, anio=2019, semana=10)
        pool, anios = ing_canal.construir_pool(serie, 2019, 10)
        self.assertEqual(resultado["n_obs_baseline"], len(pool))
        self.assertEqual(resultado["anios_baseline"], anios)
        p50 = ing_canal.percentil(pool, 0.50)
        p75 = ing_canal.percentil(pool, 0.75)
        p90 = ing_canal.percentil(pool, 0.90)
        self.assertAlmostEqual(resultado["p50_baseline"], round(p50, 1), places=1)
        self.assertAlmostEqual(resultado["p75_baseline"], round(p75, 1), places=1)
        _, esquema = ing_canal.clasificar(11.5, p50, p75, p90)
        self.assertEqual(_MAPA_CATEGORIA[resultado["categoria"]], esquema)


if __name__ == "__main__":
    unittest.main()
