"""
Suite pytest del pipeline de ingesta MINSAL (extraccion + desacumulacion),
contra extractos de texto REALES de los boletines de referencia (ver
tests/fixtures/minsal/README.md -- solo texto extraido, nunca PDFs, regla de
docs/contexto/03-fuentes-de-datos.md). Ningun numero de estas pruebas es
inventado: todos salen de boletines publicos de MINSAL y estan verificados
contra la bitacora de la corrida exploratoria validada (verificacion 4/4).

Cubre, en orden de valor (instruccion de la tarea, 2026-08-21):
  1. Desacumulacion de series (diffs, correcciones negativas excluidas --
     nunca clampeadas a cero -- y huecos registrados sin interpolar).
  2. Deteccion de formato Familia A/B por documento, no por rango de anio.
  3. Blancos = cero, nunca NULL ni fila saltada.
  4. Semanas combinadas y boletines de feriado detectados por contenido y
     registrados como ausencia esperada.
  5. Anio derivado del nombre/carpeta del archivo, nunca del texto.
  6. Reconciliacion con ambas convenciones de "Otros paises".

No toca Postgres ni requiere los PDFs: todo corre sobre los fixtures.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from corrida_distribucion import (  # noqa: E402
    RE_ANCLA_TABLA_DEPTO,
    RE_MARCADORES_VACACION,
    ResultadoBoletin,
    analizar_texto_pagina,
    clasificar_sin_tabla,
    parsear_nombre,
    paso2_desacumular,
    resolver_versiones,
)
from minsal.parser import MAPA_ESTADO, _validacion_cuadra  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "minsal"


def _resultado_desde_fixture(slug: str, anio: int, nombre_archivo: str) -> ResultadoBoletin:
    """Reproduce lo que procesar_boletin hace tras la I/O de pdfplumber:
    parsear el nombre y analizar el texto de la pagina de la tabla."""
    texto = (FIXTURES / f"{slug}.pagina_tabla.txt").read_text(encoding="utf-8")
    ruta_simulada = Path(str(anio)) / nombre_archivo  # carpeta = anio, como en data/raw/minsal/
    anio_parseado, semana_archivo, version = parsear_nombre(ruta_simulada)
    r = ResultadoBoletin(
        archivo=nombre_archivo, anio=anio_parseado, semana_archivo=semana_archivo,
        version=version, estado="pendiente",
    )
    return analizar_texto_pagina(texto, r)


def _fila(resultado: ResultadoBoletin, departamento: str):
    return next(f for f in resultado.filas if f.departamento == departamento)


# ---------------------------------------------------------------------------
# 1. Desacumulacion -- la logica mas peligrosa de romper silenciosamente
# ---------------------------------------------------------------------------


def _desacumular_par(r1: ResultadoBoletin, r2: ResultadoBoletin) -> dict:
    salida = paso2_desacumular([r1, r2])
    return salida


def test_diff_normal_entre_cortes_consecutivos():
    # SE232018 (corte probable SE21) y SE242018 (corte SE22): el valor
    # semanal de SE22 debe ser exactamente acum(SE22) - acum(SE21), por
    # departamento -- verificado contra los acumulados reales de ambas tablas.
    r1 = _resultado_desde_fixture("SE232018", 2018, "Boletin_epidemiologico_SE232018.pdf")
    r2 = _resultado_desde_fixture("SE242018", 2018, "Boletin_epidemiologico_SE242018.pdf")
    assert r1.estado == "ok" and r2.estado == "ok"
    assert (r1.semana_probable, r2.semana_probable) == (21, 22)

    salida = _desacumular_par(r1, r2)
    acum1 = {f.departamento: f.valores[0] for f in r1.filas}
    acum2 = {f.departamento: f.valores[0] for f in r2.filas}

    puntos_se22 = {p.departamento: p for p in salida["probable"] if p.semana == 22}
    assert len(puntos_se22) == 14
    for depto, p in puntos_se22.items():
        assert p.valor == acum2[depto] - acum1[depto]

    # Ancla literal: la suma nacional real pasa de 47 a 57 probables --
    # el total semanal desacumulado de SE22 es 10.
    assert sum(p.valor for p in puntos_se22.values()) == 10.0


def test_primer_corte_de_la_serie_arranca_desde_cero():
    # El primer corte disponible de un (anio, depto) es acumulado desde SE1:
    # su valor semanal-equivalente es el acumulado tal cual (diff contra 0),
    # no un hueco ni un NULL.
    r1 = _resultado_desde_fixture("SE232018", 2018, "Boletin_epidemiologico_SE232018.pdf")
    salida = paso2_desacumular([r1])
    puntos = {p.departamento: p for p in salida["probable"] if p.semana == 21}
    assert puntos["Chalatenango"].valor == _fila(r1, "Chalatenango").valores[0]


def test_correccion_retroactiva_negativa_se_excluye_no_se_clampea():
    # Correccion retroactiva REAL de MINSAL (correcciones_negativas.csv de la
    # corrida validada): Chalatenango probable acumulado 62 (corte SE33,
    # boletin SE352018) -> 61 (corte SE34, boletin SE362018), diff = -1.
    r1 = _resultado_desde_fixture("SE352018", 2018, "Boletin_epidemiologico_SE352018.pdf")
    r2 = _resultado_desde_fixture("SE362018", 2018, "Boletin_epidemiologico_SE362018.pdf")
    assert _fila(r1, "Chalatenango").valores[0] == 62.0
    assert _fila(r2, "Chalatenango").valores[0] == 61.0

    salida = _desacumular_par(r1, r2)
    punto = next(
        p for p in salida["probable"] if p.departamento == "Chalatenango" and p.semana == 34
    )
    # Excluida de la serie: valor None con nota explicita -- NUNCA un 0
    # fabricado (clampear a cero inventaria una semana sin casos que MINSAL
    # no reporto).
    assert punto.valor is None
    assert "correccion retroactiva" in punto.nota
    assert "-1" in punto.nota

    # Los departamentos sin correccion se desacumulan normal en ese par:
    # Ahuachapan 6 -> 7 = +1.
    punto_ah = next(
        p for p in salida["probable"] if p.departamento == "Ahuachapán" and p.semana == 34
    )
    assert punto_ah.valor == 1.0


def test_hueco_entre_cortes_se_registra_sin_interpolar_ni_repartir():
    # Hueco real de 2019: tras el corte probable SE36 (boletin SE382019) el
    # siguiente corte disponible es SE50 (boletin SE522019_v2) -- 14 semanas
    # sin boletin con tabla. Deben salir como intervalo sin dato, jamas
    # repartidas ni interpoladas.
    r1 = _resultado_desde_fixture("SE382019", 2019, "Boletin_epidemiologico_SE382019.pdf")
    r2 = _resultado_desde_fixture("SE522019_v2", 2019, "Boletin_epidemiologico_SE522019_v2.pdf")
    assert (r1.semana_probable, r2.semana_probable) == (36, 50)

    salida = _desacumular_par(r1, r2)
    santa_ana = [p for p in salida["probable"] if p.departamento == "Santa Ana"]
    en_hueco = [p for p in santa_ana if 37 <= p.semana <= 50]

    # Todo el intervalo (37..50 inclusive, 14 semanas) queda sin dato, con
    # nota de hueco -- el acumulado real subio 55 -> 62 en Santa Ana y esos
    # 7 casos NO se reparten entre las semanas del hueco.
    assert len(en_hueco) == 14
    assert all(p.valor is None for p in en_hueco)
    assert all("hueco" in p.nota for p in en_hueco)


# ---------------------------------------------------------------------------
# 2. Familia A vs B -- por documento, nunca por rango de anio
# ---------------------------------------------------------------------------


def test_familia_a_detectada_por_columna_tasa():
    r = _resultado_desde_fixture("SE232018", 2018, "Boletin_epidemiologico_SE232018.pdf")
    assert r.familia == "A"
    # Familia A: 3 columnas por fila (probable, confirmado, tasa).
    assert all(len(f.valores) == 3 for f in r.filas)


def test_familia_b_detectada_por_ausencia_de_tasa():
    r = _resultado_desde_fixture("SE522023", 2023, "Boletin_epidemiologico_SE522023.pdf")
    assert r.familia == "B"
    assert all(len(f.valores) == 2 for f in r.filas)
    # Caso de referencia verificado a mano: 17 probables / 54 confirmados.
    assert r.suma14 == [17.0, 54.0]


def test_familia_se_decide_por_documento_no_por_anio():
    # Dos boletines del MISMO rango tardio (2019 es A, 2023 es B) -- la
    # deteccion sale del contenido de cada documento ("Tasa x" presente o
    # no), no de una regla por anio (trampa documentada: el split no es
    # limpio por anio y no debe inferirse de un rango).
    r_2019 = _resultado_desde_fixture("SE522019_v2", 2019, "Boletin_epidemiologico_SE522019_v2.pdf")
    r_2023 = _resultado_desde_fixture("SE012023", 2023, "Boletin_epidemiologico_SE012023.pdf")
    assert r_2019.familia == "A"
    assert r_2023.familia == "B"


# ---------------------------------------------------------------------------
# 3. Blancos = cero, nunca NULL ni fila saltada
# ---------------------------------------------------------------------------


def test_celda_en_blanco_se_lee_como_cero():
    # SE062018: la celda "probable" de La Libertad esta EN BLANCO en el PDF
    # ("La Libertad 0 0.0" -- solo confirmado y tasa). Debe leerse como
    # probable=0, sin saltar la fila, y los 14 departamentos deben estar.
    r = _resultado_desde_fixture("SE062018", 2018, "Boletin_epidemiologico_SE062018.pdf")
    assert r.estado == "ok"
    assert len(r.filas) == 14

    la_libertad = _fila(r, "La Libertad")
    assert la_libertad.valores[0] == 0.0  # blanco -> 0, no NULL, no fila perdida

    # Chequeo aritmetico de que el 0 es la lectura correcta y no un invento:
    # el total impreso de probables (12) solo cuadra con blanco=0.
    assert r.suma14[0] == 12.0
    assert r.validacion_tabla is True


# ---------------------------------------------------------------------------
# 4. Semanas combinadas y feriados -- por contenido, como ausencia esperada
# ---------------------------------------------------------------------------


def test_boletin_multisemana_es_ausencia_esperada_no_se_divide():
    # 2018 publico SE1+SE2 combinadas en un solo archivo. Ni se ingiere como
    # una semana normal (duplicaria magnitud) ni se divide (fabricaria
    # datos): ausencia esperada.
    r = _resultado_desde_fixture("SE01-02-2018", 2018, "Boletin_epidemiologico_SE01-02-2018.pdf")
    assert r.estado == "ausencia_esperada_multisemana"
    assert r.suma14 == []  # nada extraido como si fuera semanal
    assert MAPA_ESTADO[r.estado] == "ausencia_esperada"


def test_feriado_se_detecta_por_contenido_no_por_nombre_de_archivo():
    nombre = "Boletin_epidemiologico_SE142023-Semana-Santa.pdf"
    # El nombre contiene un patron SEnn perfectamente valido -- si la
    # deteccion fuera por nombre, este boletin pasaria por uno semanal.
    _, semana_archivo, _ = parsear_nombre(Path("2023") / nombre)
    assert semana_archivo == "14"

    # Por CONTENIDO: ninguna pagina del boletin contiene el ancla de la
    # tabla departamental de dengue...
    completo = (FIXTURES / "SE142023-Semana-Santa.texto_completo.txt").read_text(encoding="utf-8")
    assert all(not RE_ANCLA_TABLA_DEPTO.search(pagina) for pagina in completo.split("\f"))

    # ...y la portada marca vacaciones -> ausencia esperada, no error de
    # extraccion.
    portada = (FIXTURES / "SE142023-Semana-Santa.portada.txt").read_text(encoding="utf-8")
    assert RE_MARCADORES_VACACION.search(portada)
    r = ResultadoBoletin(archivo=nombre, anio=2023, semana_archivo="14", version=1, estado="pendiente")
    r = clasificar_sin_tabla(portada, menciones_dengue=5, resultado=r)
    assert r.estado == "ausencia_esperada_vacacion"
    assert MAPA_ESTADO[r.estado] == "ausencia_esperada"


def test_sin_texto_extraible_es_distinto_de_vacacion():
    # 0 menciones de "dengue" en todo el documento y portada sin marca de
    # vacaciones -> sin_texto_extraible (ADR 0007), un estado distinto de la
    # ausencia esperada.
    r = ResultadoBoletin(archivo="x.pdf", anio=2019, semana_archivo="23", version=1, estado="pendiente")
    r = clasificar_sin_tabla("Boletin epidemiologico semana 23", menciones_dengue=0, resultado=r)
    assert r.estado == "sin_texto_extraible"
    assert MAPA_ESTADO[r.estado] == "sin_texto_extraible"


# ---------------------------------------------------------------------------
# 5. Anio del nombre/carpeta del archivo, nunca del texto del documento
# ---------------------------------------------------------------------------


def test_anio_se_deriva_del_archivo_aunque_el_texto_diga_otro():
    # Trampa confirmada: SE012023.pdf dice "El Salvador 2022" en el titulo
    # de su tabla (arrastre de plantilla). El texto real del fixture lo
    # contiene -- y aun asi el anio registrado debe ser 2023.
    texto = (FIXTURES / "SE012023.pagina_tabla.txt").read_text(encoding="utf-8")
    assert "2022" in texto

    r = _resultado_desde_fixture("SE012023", 2023, "Boletin_epidemiologico_SE012023.pdf")
    assert r.anio == 2023


def test_version_mas_alta_gana_sin_depender_del_orden():
    # Republicaciones _vN son correcciones del mismo boletin: gana la
    # version mas alta, con precedencia explicita (no orden de directorio).
    rutas = [
        Path("2019/Boletin_epidemiologico_SE392019_v4.pdf"),
        Path("2019/Boletin_epidemiologico_SE392019.pdf"),
        Path("2019/Boletin_epidemiologico_SE392019_v2.pdf"),
    ]
    vigentes, descartados = resolver_versiones(rutas)
    assert [p.name for p in vigentes] == ["Boletin_epidemiologico_SE392019_v4.pdf"]
    assert len(descartados) == 2
    # Mismo resultado con el orden invertido.
    vigentes_inv, _ = resolver_versiones(list(reversed(rutas)))
    assert vigentes == vigentes_inv


# ---------------------------------------------------------------------------
# 6. Reconciliacion: ambas convenciones de "Otros paises" deben pasar
# ---------------------------------------------------------------------------


def test_total_publicado_que_excluye_otros_paises_cuadra():
    # SE522019_v2 (footnote explicito del boletin: el total excluye a los 2
    # extranjeros): suma14 = total impreso, sin sumar "Otros paises".
    r = _resultado_desde_fixture("SE522019_v2", 2019, "Boletin_epidemiologico_SE522019_v2.pdf")
    assert r.estado == "ok"
    assert r.suma14[:2] == [437.0, 174.0]  # caso de referencia verificado a mano
    assert r.otros_paises[:2] == [2.0, 2.0]
    assert r.validacion_tabla is True
    assert _validacion_cuadra(r) is True


def test_total_publicado_que_incluye_otros_paises_tambien_cuadra():
    # SE352018 (convencion opuesta, confirmada en 2018): confirmados
    # suma14=143 + otros=1 = total impreso 144. Solo cuadra sumando otros.
    r = _resultado_desde_fixture("SE352018", 2018, "Boletin_epidemiologico_SE352018.pdf")
    assert r.estado == "ok"
    assert r.validacion_tabla is False
    assert r.validacion_nacional is True
    assert _validacion_cuadra(r) is True


def test_mismatch_en_ambas_convenciones_va_a_revision_manual_no_se_ingiere():
    # Si NINGUNA de las dos convenciones cuadra, el boletin queda en
    # revision_manual -- nunca ingesta silenciosa. Se fuerza el caso
    # alterando el total impreso de un fixture real en memoria (el texto del
    # fixture no se toca).
    texto = (FIXTURES / "SE522023.pagina_tabla.txt").read_text(encoding="utf-8")
    texto_roto = re.sub(r"Total 17 54", "Total 99 99", texto)
    assert texto_roto != texto  # el ancla del total existia tal cual
    r = ResultadoBoletin(
        archivo="Boletin_epidemiologico_SE522023.pdf", anio=2023,
        semana_archivo="52", version=1, estado="pendiente",
    )
    r = analizar_texto_pagina(texto_roto, r)
    assert r.estado == "revision_manual"
    assert _validacion_cuadra(r) is False
    assert MAPA_ESTADO[r.estado] == "revision_manual"
