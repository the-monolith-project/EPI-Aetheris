"""Pruebas de las funciones puras de experimento_nowcast_candidatas.py: formulas de las
candidatas (contra las de los experimentos), regla de T con pendiente variable (contra la del
script congelado y contra Reglas), criterio de confirmacion y Holm. No necesitan Postgres."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import experimento_nowcast_candidatas as cd  # noqa: E402
import experimento_nowcast_peso_horizonte as ph  # noqa: E402
import experimento_nowcast_tendencia as ten  # noqa: E402
import experimento_nowcast_tendencia_seleccion as sel  # noqa: E402
from experimento_nowcast_corto_plazo import Serie  # noqa: E402

FORMA = np.linspace(-1.0, 1.0, 23)


def _q(centro: float, escala: float) -> np.ndarray:
    return np.expm1(np.log1p(centro) + escala * FORMA)


# --- formulas ---------------------------------------------------------------------


def test_mezcla_es_la_de_los_experimentos():
    m, t = _q(300.0, 0.4), _q(100.0, 0.2)
    for w in (0.0, 0.25, 0.5, 1.0):
        assert np.allclose(cd.mezcla(m, t, w), ph.mezcla(m, t, w), rtol=0, atol=1e-12)


def test_mediana_de_t_ancho_de_c_es_la_variante_de_los_experimentos():
    m, t = _q(300.0, 0.4), _q(100.0, 0.2)
    assert np.allclose(cd.mediana_de_t_ancho_de_c(m, t), ph.mezcla_centro_ancho(m, t, 0.0, 0.5), rtol=0, atol=1e-12)


def test_mediana_de_t_ancho_de_c_conserva_mediana_y_ancho():
    m, t = _q(300.0, 0.4), _q(100.0, 0.2)
    k2, c = cd.mediana_de_t_ancho_de_c(m, t), cd.mezcla(m, t, 0.5)
    assert k2[ph.IDX_MEDIANA] == pytest.approx(t[ph.IDX_MEDIANA])
    assert np.allclose(np.log1p(k2) - np.log1p(k2[ph.IDX_MEDIANA]), np.log1p(c) - np.log1p(c[ph.IDX_MEDIANA]))


def _serie_sintetica(semanas: int = 700, semilla: int = 3) -> Serie:
    rng = np.random.default_rng(semilla)
    fecha = np.array([date(2013, 12, 29) + timedelta(days=7 * k) for k in range(semanas)], dtype=object)
    z = np.log(100.0) + np.cumsum(rng.normal(0.0, 0.15, semanas))
    casos = np.expm1(z)
    return Serie(fecha=fecha, anio=np.array([f.year for f in fecha]), semana=np.arange(semanas) % 52 + 1,
                 doy=np.array([f.timetuple().tm_yday for f in fecha]), casos=casos, z=np.log1p(casos),
                 clima={}, oni=np.zeros(semanas))


def test_regla_con_pendiente_de_tres_semanas_es_la_del_script_congelado_y_la_de_reglas():
    s = _serie_sintetica()
    reglas = sel.Reglas(s)
    for o in (400, 520, 650):
        for h in (1, 4, 8):
            propio = cd.cuantiles_regla_v(s, o, h, 0.8, 3)
            assert np.allclose(propio, ten.cuantiles_regla(s, o, h, 0.8), rtol=0, atol=1e-9)
            assert np.allclose(propio, reglas.cuantiles(o, h, 0.8, 3), rtol=0, atol=1e-9)


def test_regla_con_pendiente_de_dos_semanas_es_la_de_reglas():
    s = _serie_sintetica()
    reglas = sel.Reglas(s)
    for o in (400, 520, 650):
        for h in (1, 4, 8):
            assert np.allclose(cd.cuantiles_regla_v(s, o, h, 0.8, 2), reglas.cuantiles(o, h, 0.8, 2), rtol=0, atol=1e-9)


def test_regla_no_usa_el_futuro():
    s = _serie_sintetica()
    base = cd.cuantiles_regla_v(s, 500, 4, 0.8, 2)
    s2 = _serie_sintetica()
    s2.casos[505:] *= 50.0
    s2.z = np.log1p(s2.casos)
    # los objetivos de los errores caen antes del origen, y el centro usa z[o] y z[o - v]
    assert np.allclose(base, cd.cuantiles_regla_v(s2, 500, 4, 0.8, 2), rtol=0, atol=1e-9)


# --- criterio ---------------------------------------------------------------------


def _fila(y: float, m: np.ndarray, t: np.ndarray, t2: np.ndarray | None = None, origen: str = "2026-09-20") -> dict:
    return {"origen": origen, "anio": 2026, "semana": 20, "y": y, "q_M0": m, "q_T": t, "q_C": cd.mezcla(m, t, 0.5),
            "q_T2": t if t2 is None else t2, "wis_ref_suavizada": 10.0}


def _filas_sinteticas(m: np.ndarray, t: np.ndarray, y: float, n: int = 12) -> dict[int, list[dict]]:
    base = date(2026, 9, 20)
    return {h: [_fila(y, m, t, origen=str(base + timedelta(days=7 * k))) for k in range(n)] for h in range(1, 9)}


def test_k1_y_k2_solo_cambian_sus_horizontes():
    m, t = _q(300.0, 0.4), _q(100.0, 0.2)
    f = _fila(100.0, m, t)
    for h in range(1, 9):
        q = cd.cuantiles_candidatas(f, h)
        assert np.array_equal(q["K1"], q["C"]) == (h not in (3, 4))
        assert np.array_equal(q["K2"], q["C"]) == (h not in (1, 2))
    q = cd.cuantiles_candidatas(f, 3)
    assert np.array_equal(q["C_por_tramos"], q["K1"])
    assert np.array_equal(cd.cuantiles_candidatas(f, 2)["C_por_tramos"], cd.cuantiles_candidatas(f, 2)["K2"])
    assert np.array_equal(cd.cuantiles_candidatas(f, 6)["C_por_tramos"], cd.cuantiles_candidatas(f, 6)["C"])


def test_se_confirman_k1_y_k2_si_t_acierta_y_m0_no():
    m, t = _q(300.0, 0.15), _q(100.0, 0.15)
    res = cd.evaluar_filas(_filas_sinteticas(m, t, y=100.0))
    dec = cd.decidir(res)
    assert dec["K1"]["confirmada"] and dec["K2"]["confirmada"]
    assert dec["K3"]["razon_media"] == pytest.approx(1.0)  # K3 usa el mismo T aqui: razon 1
    assert not dec["K3"]["confirmada"]  # sin ganancia no se confirma
    assert all(res["por_h"][h]["K1"]["razon_vs_C"] == pytest.approx(1.0) for h in (1, 2, 5, 6, 7, 8))


def test_no_se_confirman_si_m0_acierta_y_t_no():
    m, t = _q(100.0, 0.15), _q(300.0, 0.15)
    dec = cd.decidir(cd.evaluar_filas(_filas_sinteticas(m, t, y=100.0)))
    assert not dec["K1"]["confirmada"] and not dec["K2"]["confirmada"]
    assert dec["K1"]["razon_media"] > 1.0


def test_k2_conserva_el_ancho_de_c_y_su_cobertura():
    # T acierta la mediana pero su rango es angosto; K2 toma de T solo la mediana
    m, t = _q(300.0, 0.6), _q(100.0, 0.02)
    filas = _filas_sinteticas(m, t, y=101.0)
    res = cd.evaluar_filas(filas)
    dec = cd.decidir(res)
    assert dec["K2"]["c1_razon"] and dec["K2"]["c2_mayoria_de_horizontes"]
    assert dec["K2"]["cob95_candidata"] >= dec["K2"]["cob95_C"] - 0.03  # K2 conserva el ancho de C
    assert dec["K2"]["confirmada"]


def test_la_razon_exige_ganar_al_menos_un_uno_por_ciento():
    # ganancia minima: peso casi igual al de C no pasa el umbral de 0,99
    d = {"por_h": {h: {"C": {"n": 10, "dentro95": 10}, "K1": {"razon_vs_C": 0.995, "dentro95": 10},
                       "K2": {"razon_vs_C": 0.995, "dentro95": 10}, "K3": {"razon_vs_C": 0.995, "dentro95": 10}}
                   for h in range(1, 9)}}
    dec = cd.decidir(d)
    assert not dec["K1"]["c1_razon"] and dec["K1"]["c2_mayoria_de_horizontes"] and not dec["K1"]["confirmada"]


def test_la_cobertura_impide_la_confirmacion():
    por_h = {h: {"C": {"n": 20, "dentro95": 20}, "K1": {"razon_vs_C": 0.9, "dentro95": 16},
                 "K2": {"razon_vs_C": 0.9, "dentro95": 17}, "K3": {"razon_vs_C": 0.9, "dentro95": 17}}
             for h in range(1, 9)}
    dec = cd.decidir({"por_h": por_h})
    # K1: 32 de 40 = 0,80 contra 1,00; K2: 34 de 40 = 0,85 contra 1,00 (baja 0,15)
    assert dec["K1"]["c1_razon"] and not dec["K1"]["c3_cobertura"] and not dec["K1"]["confirmada"]
    assert not dec["K2"]["confirmada"]
    por_h[3]["K1"]["dentro95"] = por_h[4]["K1"]["dentro95"] = 20
    assert cd.decidir({"por_h": por_h})["K1"]["confirmada"]


def test_k3_exige_mas_de_la_mitad_de_los_horizontes():
    por_h = {}
    for h in range(1, 9):
        r = 0.9 if h <= 4 else 1.05  # gana en 4 de 8, razon media 0,975
        por_h[h] = {"C": {"n": 10, "dentro95": 10}, "K1": {"razon_vs_C": 1.0, "dentro95": 10},
                    "K2": {"razon_vs_C": 1.0, "dentro95": 10}, "K3": {"razon_vs_C": r, "dentro95": 10}}
    dec = cd.decidir({"por_h": por_h})
    assert dec["K3"]["c1_razon"] and not dec["K3"]["c2_mayoria_de_horizontes"] and not dec["K3"]["confirmada"]
    por_h[5]["K3"]["razon_vs_C"] = 0.9  # 5 de 8
    assert cd.decidir({"por_h": por_h})["K3"]["c2_mayoria_de_horizontes"]


def test_dm_y_holm_coinciden_con_los_del_experimento():
    rng = np.random.default_rng(5)
    d = rng.normal(0.1, 1.0, 60)
    assert cd.dm(d, 4) == sel.dm(d, 4)
    assert cd.dm(d[:5], 2) is None
    aj = cd.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert aj == {"a": pytest.approx(0.03), "c": pytest.approx(0.06), "b": pytest.approx(0.06)}


def test_origen_ok_pide_rezagos_y_objetivo_finitos():
    s = _serie_sintetica(100)
    assert cd.origen_ok(s, 50, 4)
    assert not cd.origen_ok(s, 5, 4)  # sin rezagos suficientes
    s.casos[54] = np.nan
    assert not cd.origen_ok(s, 50, 4)  # objetivo sin dato
    s.casos[54] = 10.0
    s.z[47] = np.nan
    assert not cd.origen_ok(s, 50, 4)  # rezago sin dato
