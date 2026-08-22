"""
Suite pytest del parser exploratorio de IRA (corrida_ira.py), contra
extractos de texto REALES de boletines MINSAL (ver
tests/fixtures/minsal/README.md -- solo texto extraido, nunca PDFs). Ningun
numero es inventado: todos salen de boletines publicos y estan verificados
contra la bitacora de la corrida exploratoria (data/interim/corrida_ira/).

Cubre las trampas especificas de IRA encontradas en la exploracion
(docs/exploracion-ira-boletines-minsal.md):
  1. Separador de miles inconsistente (coma/punto/ninguno) y el malformado
     "1363,652" (primera coma de millares perdida).
  2. Semana de corte leida del titulo de la TABLA, nunca de la narrativa
     (que repite la semana anterior en 2018).
  3. La narrativa con numeros pegados a nombres de departamento no contamina
     las filas (bloque recortado desde el titulo/encabezado).
  4. Tabla renderizada como imagen -> sospecha explicita, nunca filas vacias
     rellenadas.
  5. Tabla departamental reimpresa/rezagada (SE10/2018 == SE09/2018).
  6. Desacumulacion: diffs, huecos sin interpolar, correcciones negativas
     excluidas (nunca clampeadas a cero).
  7. Variantes de titulo ("de IRA por grupo de edad y departamento").

No toca Postgres ni requiere los PDFs ni pdfplumber: todo corre sobre fixtures.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from corrida_ira import (  # noqa: E402
    ResultadoIRA,
    analizar_texto_pagina,
    desacumular,
    detectar_reimpresiones,
    parsear_nombre,
    parsear_numero,
)

FIXTURES = Path(__file__).parent / "fixtures" / "minsal"


def _resultado_desde_fixture(slug: str, anio: int, nombre_archivo: str) -> ResultadoIRA:
    """Reproduce lo que procesar_boletin hace tras la I/O de pdfplumber."""
    texto = (FIXTURES / f"{slug}.pagina_tabla_ira.txt").read_text(encoding="utf-8")
    ruta_simulada = Path(str(anio)) / nombre_archivo
    anio_parseado, semana_archivo, version = parsear_nombre(ruta_simulada)
    r = ResultadoIRA(
        archivo=nombre_archivo, anio=anio_parseado, semana_archivo=semana_archivo,
        version=version, estado="pendiente",
    )
    return analizar_texto_pagina(texto, r)


def _fila(r: ResultadoIRA, departamento: str):
    return next(f for f in r.filas if f.departamento == departamento)


# ---------------------------------------------------------------------------
# 1. Separadores de miles inconsistentes (hallazgo 3 del brief + malformados)
# ---------------------------------------------------------------------------

def test_parsear_numero_coma_de_miles():
    assert parsear_numero("33,360") == 33360


def test_parsear_numero_punto_de_miles():
    assert parsear_numero("1.574.872") == 1574872


def test_parsear_numero_sin_separador():
    assert parsear_numero("19460") == 19460


def test_parsear_numero_decimal_corto():
    assert parsear_numero("3.4") == 3.4


def test_parsear_numero_miles_malformado():
    # SE38/2018 imprime "Total general 1363,652" (la primera coma de 1,363,652
    # se perdio) -- debe leerse como millares, no como 1363 ni como decimal.
    assert parsear_numero("1363,652") == 1363652


def test_total_malformado_cuadra_con_suma_de_celdas():
    r = _resultado_desde_fixture("SE382018", 2018, "Boletin_epidemiologico_SE382018.pdf")
    assert r.estado == "ok"
    assert r.total_impreso == 1363652
    assert r.suma14 == 1363652
    assert r.validacion_cuadra is True


# ---------------------------------------------------------------------------
# 2/3. Semana de corte del titulo de la tabla; narrativa no contamina
# ---------------------------------------------------------------------------

def test_semana_del_titulo_de_tabla_no_de_la_narrativa():
    # La narrativa de SE03/2018 repite "SE 2-2018" (texto rezagado de la
    # semana anterior); el titulo de la tabla dice "SE-03 de 2018".
    r = _resultado_desde_fixture("SE032018", 2018, "Boletin_epidemiologico_SE032018.pdf")
    assert r.estado == "ok"
    assert r.semana_corte == 3
    assert r.fuente_semana == "titulo_tabla"
    assert r.total_impreso == 88099


def test_narrativa_con_numeros_de_departamento_no_contamina():
    # La narrativa de SE01-02/2018 dice "...Chalatenango 1,377, San Salvador
    # 1,005 y Usulutan 1,001" (tasas) ANTES de la tabla; la fila real de la
    # tabla es "Chalatenango 2,823 1,377".
    r = _resultado_desde_fixture("SE01-02-2018", 2018, "Boletin_epidemiologico_SE01-02-2018.pdf")
    assert r.estado == "ok"
    assert _fila(r, "Chalatenango").total_acum == 2823
    assert r.semana_corte == 2  # boletin combinado SE1+SE2: el corte del acumulador es SE2
    assert r.total_impreso == 54543


def test_variante_de_titulo_2019():
    # SE43/2019 titula "Casos y tasas de IRA por grupo de edad y
    # departamento, SE-43 de 2019" (otro orden de palabras).
    r = _resultado_desde_fixture("SE432019_v3", 2019, "Boletin_epidemiologico_SE432019_v3.pdf")
    assert r.estado == "ok"
    assert r.semana_corte == 43
    assert _fila(r, "San Salvador").total_acum == 593152


# ---------------------------------------------------------------------------
# Layouts: lado a lado (2018-2022) y pagina propia (2023)
# ---------------------------------------------------------------------------

def test_layout_lado_a_lado_2019():
    r = _resultado_desde_fixture("SE522019_v2", 2019, "Boletin_epidemiologico_SE522019_v2.pdf")
    assert r.estado == "ok"
    assert r.layout == "lado_a_lado"
    assert _fila(r, "San Salvador").total_acum == 700913
    assert r.total_impreso == 1951867
    assert r.semana_corte == 52


def test_layout_pagina_propia_2023_sin_titulo():
    # SE01/2023: la tabla departamental esta en pagina propia SIN titulo y con
    # el encabezado de columna equivocado ("Grupo de edad" -- error de
    # plantilla de MINSAL, las filas son departamentos). La semana sale del
    # pie de estratificacion de la misma pagina.
    r = _resultado_desde_fixture("SE012023", 2023, "Boletin_epidemiologico_SE012023.pdf")
    assert r.estado == "ok"
    assert _fila(r, "San Salvador").total_acum == 11295
    assert r.total_impreso == 33360
    assert r.semana_corte == 1
    assert r.fuente_semana == "pie_estratificacion"


def test_discrepancia_minima_2023():
    # SE52/2023 (separador punto): las 14 celdas impresas suman 1,574,871 y el
    # total impreso dice 1,574,872 (verificado a mano) -- inconsistencia
    # interna del boletin. Las celdas se conservan y la discrepancia queda
    # registrada; nunca se "corrige" ninguna celda para forzar el cuadre.
    r = _resultado_desde_fixture("SE522023", 2023, "Boletin_epidemiologico_SE522023.pdf")
    assert r.estado == "ok_discrepancia_minima"
    assert _fila(r, "San Salvador").total_acum == 615619
    assert r.suma14 == 1574871
    assert r.total_impreso == 1574872
    assert r.diff_total == -1


# ---------------------------------------------------------------------------
# 4. Tabla como imagen -> sospecha explicita, nunca se rellena
# ---------------------------------------------------------------------------

def test_tabla_imagen_es_sospecha_no_dato():
    # SE01/2019: el titulo de la tabla es texto extraible pero las filas no
    # (tabla renderizada como imagen). 0 filas, ningun valor fabricado.
    r = _resultado_desde_fixture("SE012019", 2019, "Boletin_epidemiologico_SE012019.pdf")
    assert r.estado == "sin_filas_sospecha_imagen"
    assert r.filas == []
    assert r.suma14 is None


# ---------------------------------------------------------------------------
# 5. Tabla reimpresa/rezagada (SE10/2018 == SE09/2018)
# ---------------------------------------------------------------------------

def test_reimpresion_detectada():
    r09 = _resultado_desde_fixture("SE092018", 2018, "Boletin_epidemiologico_SE092018.pdf")
    r10 = _resultado_desde_fixture("SE102018", 2018, "Boletin_epidemiologico_SE102018.pdf")
    assert r09.estado == "ok"
    # Los 14 valores de SE10 son identicos a los de SE09 (San Salvador 119,670
    # en ambos): el corte posterior se reclasifica, el anterior se conserva.
    n = detectar_reimpresiones([r09, r10])
    assert n == 1
    assert r09.estado == "ok"
    assert r10.estado == "revision_manual"
    assert "reimpresa" in r10.nota


# ---------------------------------------------------------------------------
# 6. Desacumulacion: diff, hueco sin interpolar, correccion negativa excluida
# ---------------------------------------------------------------------------

def _resultados_2018_consecutivos() -> list[ResultadoIRA]:
    return [
        _resultado_desde_fixture("SE01-02-2018", 2018, "Boletin_epidemiologico_SE01-02-2018.pdf"),
        _resultado_desde_fixture("SE032018", 2018, "Boletin_epidemiologico_SE032018.pdf"),
    ]


def test_desacumulacion_diff_consecutivo():
    puntos, negativas = desacumular(_resultados_2018_consecutivos())
    # San Salvador: acumulado 17,958 (SE2) -> 29,535 (SE3); la incidencia de
    # SE3 es la diferencia real entre cortes consecutivos.
    p3 = next(p for p in puntos if p.departamento == "San Salvador" and p.semana == 3)
    assert p3.valor == 29535 - 17958
    assert negativas == []


def test_desacumulacion_primer_corte_multisemana_marcado():
    puntos, _ = desacumular(_resultados_2018_consecutivos())
    # El primer corte del anio (SE2, boletin combinado SE1+SE2) es acumulado
    # desde SE1: se conserva el valor pero marcado, nunca se divide entre
    # semanas (dividir fabricaria datos).
    p2 = next(p for p in puntos if p.departamento == "San Salvador" and p.semana == 2)
    assert p2.valor == 17958
    assert "acumulado SE1-SE2" in p2.nota


def test_desacumulacion_hueco_sin_interpolar():
    resultados = [
        _resultado_desde_fixture("SE032018", 2018, "Boletin_epidemiologico_SE032018.pdf"),
        _resultado_desde_fixture("SE092018", 2018, "Boletin_epidemiologico_SE092018.pdf"),
    ]
    puntos, _ = desacumular(resultados)
    # Entre los cortes SE3 y SE9 no hay boletin en este par: las semanas 4-9
    # quedan sin dato (None), nunca se reparte la diferencia entre ellas.
    ss = [p for p in puntos if p.departamento == "San Salvador"]
    for semana in range(4, 10):
        p = next(p for p in ss if p.semana == semana)
        assert p.valor is None
        assert "hueco" in p.nota


def test_desacumulacion_correccion_negativa_excluida():
    # Correccion retroactiva real del corpus (correcciones_negativas_ira.csv
    # de la corrida: Cuscatlan, acumulado 2022 SE46 48,199 -> SE47 47,434,
    # diff -765): el diff negativo se excluye de la serie (None), nunca se
    # clampea a cero.
    r_a = ResultadoIRA(archivo="a", anio=2022, semana_archivo="46", version=1,
                       estado="ok", semana_corte=46)
    r_b = ResultadoIRA(archivo="b", anio=2022, semana_archivo="47", version=1,
                       estado="ok", semana_corte=47)
    from corrida_ira import FilaIRA
    r_a.filas = [FilaIRA("Cuscatlán", 48199, None)]
    r_b.filas = [FilaIRA("Cuscatlán", 47434, None)]
    puntos, negativas = desacumular([r_a, r_b])
    p47 = next(p for p in puntos if p.semana == 47)
    assert p47.valor is None
    assert "correccion retroactiva" in p47.nota
    assert len(negativas) == 1
    assert negativas[0]["diferencia"] == 47434 - 48199


# ---------------------------------------------------------------------------
# Anio del nombre de archivo, nunca del texto (trampa 1 de dengue, vigente)
# ---------------------------------------------------------------------------

def test_anio_del_nombre_no_del_texto():
    anio, semana, version = parsear_nombre(
        Path("2023") / "Boletin_epidemiologico_SE012023.pdf")
    assert anio == 2023
    assert semana == "01"
    assert version == 1
