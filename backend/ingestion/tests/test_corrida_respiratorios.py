"""
Pruebas del protocolo de exploración respiratoria (corrida_respiratorios.py)
contra extractos de texto REALES de boletines MINSAL. Ningún número es
inventado. No toca Postgres ni requiere pdfplumber.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from corrida_respiratorios import (  # noqa: E402
    ResultadoNeumonia,
    ResultadoVirus,
    analizar_texto_pagina_neumonias,
    analizar_texto_pagina_virus,
    desacumular_neumonias,
    detectar_reimpresiones_neumonias,
    extraer_metricas_lab,
    parsear_nombre,
    parsear_numero,
    parsear_numero_lab,
    procesar_boletin_neumonias,
    procesar_boletin_virus,
)

FIXTURES = Path(__file__).parent / "fixtures" / "minsal"


def _texto(slug: str) -> str:
    return (FIXTURES / slug).read_text(encoding="utf-8")


def _neu(slug: str, anio: int, nombre: str) -> ResultadoNeumonia:
    ruta = Path(str(anio)) / nombre
    anio_p, semana, version = parsear_nombre(ruta)
    r = ResultadoNeumonia(
        archivo=nombre, anio=anio_p, semana_archivo=semana, version=version, estado="pendiente",
    )
    return analizar_texto_pagina_neumonias(_texto(slug), r)


def _vir(slug: str, anio: int, nombre: str) -> ResultadoVirus:
    ruta = Path(str(anio)) / nombre
    anio_p, semana, version = parsear_nombre(ruta)
    r = ResultadoVirus(
        archivo=nombre, anio=anio_p, semana_archivo=semana, version=version, estado="pendiente",
    )
    return analizar_texto_pagina_virus(_texto(slug), r)


def _metrica(r: ResultadoVirus, codigo: str):
    return next(m for m in r.metricas if m.codigo == codigo)


# ---------------------------------------------------------------------------
# Andamiaje compartido
# ---------------------------------------------------------------------------

def test_parsear_numero_coma_y_punto_de_miles():
    assert parsear_numero("2,733") == 2733
    assert parsear_numero("22.337") == 22337
    assert parsear_numero("701") == 701


def test_parsear_numero_lab_porcentaje():
    assert parsear_numero_lab("8.75%") == 8.75
    assert parsear_numero_lab("16%") == 16
    assert parsear_numero_lab("6.67%") == 6.67


def test_anio_sale_de_la_carpeta_no_del_texto():
    anio, semana, version = parsear_nombre(Path("2023") / "Boletin_epidemiologico_SE012023.pdf")
    assert anio == 2023
    assert semana == "01"
    assert version == 1


# ---------------------------------------------------------------------------
# Neumonías — fixtures reales
# ---------------------------------------------------------------------------

def test_neumonias_2018_lado_a_lado_corte_se2():
    r = _neu(
        "SE01-02-2018.pagina_tabla_neumonias.txt",
        2018,
        "Boletin_epidemiologico_SE01-02-2018.pdf",
    )
    assert r.estado == "ok"
    assert r.semana_corte == 2
    assert r.fuente_semana == "titulo_tabla"
    assert len(r.filas) == 14
    ss = next(f for f in r.filas if f.departamento == "San Salvador")
    assert ss.total_acum == 172
    assert r.total_impreso == 701
    assert r.validacion_cuadra is True


def test_neumonias_semana_del_titulo_no_de_la_narrativa():
    r = _neu(
        "SE032018.pagina_tabla_neumonias.txt",
        2018,
        "Boletin_epidemiologico_SE032018.pdf",
    )
    assert r.estado == "ok"
    assert r.semana_corte == 3
    assert r.fuente_semana == "titulo_tabla"
    ss = next(f for f in r.filas if f.departamento == "San Salvador")
    assert ss.total_acum == 259
    assert r.total_impreso == 1142


def test_neumonias_2023_pagina_propia_sin_titulo():
    r = _neu(
        "SE012023.pagina_tabla_neumonias.txt",
        2023,
        "Boletin_epidemiologico_SE012023.pdf",
    )
    assert r.estado == "ok"
    assert r.layout == "pagina_propia"
    assert r.semana_corte == 1
    assert r.fuente_semana == "pie_estratificacion"
    ss = next(f for f in r.filas if f.departamento == "San Salvador")
    assert ss.total_acum == 101
    assert r.total_impreso == 488


def test_neumonias_separador_punto_2023():
    r = _neu(
        "SE522023.pagina_tabla_neumonias.txt",
        2023,
        "Boletin_epidemiologico_SE522023.pdf",
    )
    assert r.estado == "ok_discrepancia_minima"
    assert r.semana_corte == 52
    ss = next(f for f in r.filas if f.departamento == "San Salvador")
    assert ss.total_acum == 5667
    assert r.suma14 == 22336
    assert r.total_impreso == 22337
    assert r.diff_total == -1


def test_neumonias_tabla_imagen_no_se_rellena():
    r = _neu(
        "SE012019.pagina_tabla_neumonias.txt",
        2019,
        "Boletin_epidemiologico_SE012019.pdf",
    )
    assert r.estado == "sin_filas_sospecha_imagen"
    assert r.filas == []
    assert r.suma14 is None


def test_neumonias_vacaciones_es_ausencia_esperada():
    texto = (FIXTURES / "SE142023-Semana-Santa.texto_completo.txt").read_text(encoding="utf-8")
    paginas = [(i, p) for i, p in enumerate(texto.split("\f"))]
    r = procesar_boletin_neumonias(
        Path("2023") / "Boletin_epidemiologico_SE142023-Semana-Santa.pdf",
        paginas,
    )
    assert r.estado == "ausencia_esperada_vacacion"
    assert r.filas == []


def test_desacumulacion_neumonias_diff_y_primer_corte():
    r2 = _neu("SE01-02-2018.pagina_tabla_neumonias.txt", 2018, "Boletin_epidemiologico_SE01-02-2018.pdf")
    r3 = _neu("SE032018.pagina_tabla_neumonias.txt", 2018, "Boletin_epidemiologico_SE032018.pdf")
    puntos, negativas = desacumular_neumonias([r2, r3])
    assert negativas == []
    p2 = next(p for p in puntos if p.departamento == "San Salvador" and p.semana == 2)
    p3 = next(p for p in puntos if p.departamento == "San Salvador" and p.semana == 3)
    assert p2.valor == 172
    assert "acumulado SE1-SE2" in p2.nota
    assert p3.valor == 259 - 172


def test_neumonias_reimpresion_2019_se34_igual_se33():
    r33 = _neu(
        "SE332019.pagina_tabla_neumonias.txt",
        2019,
        "Boletin_epidemiologico_SE332019.pdf",
    )
    r34 = _neu(
        "SE342019_v2.pagina_tabla_neumonias.txt",
        2019,
        "Boletin_epidemiologico_SE342019_v2.pdf",
    )
    assert r33.estado == "ok"
    assert r34.estado == "ok"
    ss33 = next(f for f in r33.filas if f.departamento == "San Salvador")
    ss34 = next(f for f in r34.filas if f.departamento == "San Salvador")
    assert ss33.total_acum == ss34.total_acum == 5871
    n = detectar_reimpresiones_neumonias([r33, r34])
    assert n == 1
    assert r33.estado == "ok"
    assert r34.estado == "revision_manual"
    assert "reimpresa" in r34.nota


def test_neumonias_2023_tabla_departamental_con_titulo():
    r = _neu(
        "SE252023.pagina_tabla_neumonias.txt",
        2023,
        "Boletin_epidemiologico_SE252023.pdf",
    )
    assert r.estado == "ok"
    assert r.layout == "pagina_propia"
    assert r.semana_corte == 25
    ss = next(f for f in r.filas if f.departamento == "San Salvador")
    assert ss.total_acum == 2733
    assert r.total_impreso == 10618


def test_desacumulacion_hueco_sin_interpolar():
    r3 = _neu("SE032018.pagina_tabla_neumonias.txt", 2018, "Boletin_epidemiologico_SE032018.pdf")
    r9 = _neu("SE092018.pagina_tabla_neumonias.txt", 2018, "Boletin_epidemiologico_SE092018.pdf")
    puntos, _ = desacumular_neumonias([r3, r9])
    ss = [p for p in puntos if p.departamento == "San Salvador"]
    for semana in range(4, 10):
        p = next(p for p in ss if p.semana == semana)
        assert p.valor is None
        assert "hueco" in p.nota


# ---------------------------------------------------------------------------
# Vigilancia de virus — fixtures reales
# ---------------------------------------------------------------------------

def test_virus_2018_tres_columnas_sin_covid():
    r = _vir(
        "SE01-02-2018.pagina_vigilancia_virus.txt",
        2018,
        "Boletin_epidemiologico_SE01-02-2018.pdf",
    )
    assert r.estado == "ok"
    assert r.granularidad == "nacional"
    assert r.unidad_observacion == "muestras_laboratorio_centinela"
    assert r.tiene_covid is False
    muestras = _metrica(r, "muestras_analizadas")
    assert muestras.valores == [73, 45, 26]
    assert muestras.unidad == "conteo"
    vsr = _metrica(r, "vsr")
    assert vsr.anio_actual == 0
    flu_b = _metrica(r, "influenza_b")
    assert flu_b.semana == 1
    pos = _metrica(r, "positividad_virus")
    assert pos.unidad == "porcentaje"
    assert pos.anio_actual == 2


def test_virus_2023_dos_columnas_con_covid():
    r = _vir(
        "SE252023.pagina_vigilancia_virus.txt",
        2023,
        "Boletin_epidemiologico_SE252023.pdf",
    )
    assert r.estado == "ok"
    assert r.tiene_covid is True
    muestras = _metrica(r, "muestras_analizadas")
    assert muestras.anio_previo == 492
    assert muestras.anio_actual == 380
    assert muestras.semana is None
    covid = _metrica(r, "covid_19")
    assert covid.anio_actual == 10
    flu_b = _metrica(r, "influenza_b")
    assert flu_b.anio_actual == 47
    vsr = _metrica(r, "vsr")
    assert vsr.anio_actual == 15


def test_virus_covid_sin_valor_no_se_fabrica():
    r = _vir(
        "SE522023.pagina_vigilancia_virus.txt",
        2023,
        "Boletin_epidemiologico_SE522023.pdf",
    )
    assert r.estado == "ok"
    covid = _metrica(r, "covid_19")
    assert covid.valores == []
    assert "sin valores extraibles" in r.nota
    muestras = _metrica(r, "muestras_analizadas")
    assert muestras.anio_actual == 1040
    vsr = _metrica(r, "vsr")
    assert vsr.anio_actual == 206


def test_virus_vacaciones_es_ausencia_esperada():
    texto = (FIXTURES / "SE142023-Semana-Santa.texto_completo.txt").read_text(encoding="utf-8")
    paginas = [(i, p) for i, p in enumerate(texto.split("\f"))]
    r = procesar_boletin_virus(
        Path("2023") / "Boletin_epidemiologico_SE142023-Semana-Santa.pdf",
        paginas,
    )
    assert r.estado == "ausencia_esperada_vacacion"


def test_extraer_metricas_no_convierte_positividad_en_conteo():
    bloque = _texto("SE01-02-2018.pagina_vigilancia_virus.txt")
    metricas = extraer_metricas_lab(bloque)
    pos = next(m for m in metricas if m.codigo == "positividad_virus")
    assert pos.unidad == "porcentaje"
    muestras = next(m for m in metricas if m.codigo == "muestras_analizadas")
    assert muestras.unidad == "conteo"
