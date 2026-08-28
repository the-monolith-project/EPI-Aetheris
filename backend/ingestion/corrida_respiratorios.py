"""
Corrida exploratoria de Neumonías y de vigilancia centinela de virus
respiratorios (Influenza, VSR, SARS-CoV-2 y otros) en boletines MINSAL.

NO escribe a PostgreSQL. Salida en data/interim/corrida_respiratorios/
(gitignoreada). Neumonías y vigilancia de virus se exploran por separado:
no se asume el mismo contrato de datos ni se reutiliza casos_epidemiologicos
desde aquí.

Uso:
    python3 corrida_respiratorios.py
    python3 corrida_respiratorios.py --solo-neumonias
    python3 corrida_respiratorios.py --solo-virus
    python3 corrida_respiratorios.py --limite 10
    python3 corrida_respiratorios.py --solo-paso1
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).parent
RAW_ROOT = RAIZ / "data" / "raw" / "minsal"
INTERIM_ROOT = RAIZ / "data" / "interim" / "corrida_respiratorios"

DEPARTAMENTOS = [
    "Ahuachapán", "Cabañas", "Chalatenango", "Cuscatlán", "La Libertad",
    "La Paz", "Santa Ana", "San Miguel", "Sonsonate", "San Salvador",
    "San Vicente", "La Unión", "Usulután", "Morazán",
]
_PATRON_NOMBRE = {
    "Ahuachapán": r"Ahuachap[aá]n",
    "Cabañas": r"Caba[ñn]as",
    "Chalatenango": r"Chalatenango",
    "Cuscatlán": r"Cuscatl[aá]n",
    "La Libertad": r"La\s+Libertad",
    "La Paz": r"La\s+Paz",
    "Santa Ana": r"Santa\s+Ana",
    "San Miguel": r"San\s+Miguel",
    "Sonsonate": r"Sonsonate",
    "San Salvador": r"San\s+Salvador",
    "San Vicente": r"San\s+Vicente",
    "La Unión": r"La\s+Uni[oó]n",
    "Usulután": r"Usulut[aá]n",
    "Morazán": r"Moraz[aá]n",
}
_PATRON_OTROS = r"Otros\s+[Pp]a[ií]ses"

RE_ANIO_DIR = re.compile(r"^(20\d{2})$")
RE_SEMANA_ARCHIVO = re.compile(r"SE(\d{1,2})(?:-(\d{1,2}))?", re.IGNORECASE)
RE_VERSION = re.compile(r"_v(\d+)", re.IGNORECASE)
RE_MARCADORES_VACACION = re.compile(
    r"vacaciones|vigilancia\s+intensificada|semana\s+santa|fiestas\s+agostinas|fin\s+de\s+a[ñn]o",
    re.IGNORECASE,
)

_NUM = r"\d+(?:[.,]\d{3})+|\d+(?:[.,]\d{1,2})?"

ESTADOS_USABLES = {"ok", "ok_discrepancia_minima"}


def parsear_numero(token: str) -> float:
    """Misma heurística que corrida_ira.py: grupos de 3 dígitos = miles."""
    token = token.strip()
    if re.fullmatch(r"\d+(?:[.,]\d{3})+", token):
        return float(re.sub(r"[.,]", "", token))
    return float(token.replace(",", "."))


def parsear_numero_lab(token: str) -> float:
    return parsear_numero(token.strip().rstrip("%"))


def parsear_nombre(path: Path) -> tuple[int, str | None, int]:
    anio = int(path.parent.name)
    m = RE_SEMANA_ARCHIVO.search(path.stem)
    if m:
        semana = m.group(1) if not m.group(2) else f"{int(m.group(1))}-{int(m.group(2))}"
    else:
        semana = None
    v = RE_VERSION.search(path.stem)
    return anio, semana, int(v.group(1)) if v else 1


def descubrir_archivos(limite: int | None = None) -> list[Path]:
    archivos = []
    if not RAW_ROOT.exists():
        return archivos
    for carpeta in sorted(RAW_ROOT.iterdir()):
        if not carpeta.is_dir() or not RE_ANIO_DIR.match(carpeta.name):
            continue
        pdfs = sorted(carpeta.glob("*.pdf"))
        if limite is not None:
            pdfs = pdfs[:limite]
        archivos.extend(pdfs)
    return archivos


def resolver_versiones(archivos: list[Path]) -> tuple[list[Path], list[tuple[Path, str]]]:
    grupos: dict[tuple, list[tuple[int, Path]]] = defaultdict(list)
    for p in archivos:
        anio, semana, version = parsear_nombre(p)
        clave = (anio, semana) if semana is not None else (anio, p.name)
        grupos[clave].append((version, p))
    vigentes, descartados = [], []
    for miembros in grupos.values():
        miembros.sort(key=lambda t: t[0])
        vigentes.append(miembros[-1][1])
        for version, p in miembros[:-1]:
            descartados.append((p, f"version {version} superada por version {miembros[-1][0]}"))
    return sorted(vigentes), descartados


# ---------------------------------------------------------------------------
# Neumonías
# ---------------------------------------------------------------------------

RE_MARCA_NEUMONIA = re.compile(r"neumon[ií]as?", re.IGNORECASE)
RE_OTRA_ENFERMEDAD_NEU = re.compile(
    r"\bIRAS?\b|dengue|zika|chikungun|diarreica|rotavirus|IRAG|aguda\s+grave",
    re.IGNORECASE,
)
RE_TITULO_TABLA_NEU = re.compile(
    r"Casos\s+y\s+[Tt]asas\s+por\s+(?:grupo\s+de\s+edad\s+y\s+)?[Dd]epartamento\s+de\s+NEUMON[IÍ]AS?"
    r".{0,80}?SE\s*-?\s*(\d{1,2})(?:\s*-\s*(\d{1,2})\b(?!\d))?[\s,.-]*(?:de\s+)?(\d{4})?",
    re.IGNORECASE | re.DOTALL,
)
RE_ENCABEZADO_NEU = re.compile(
    r"Departamentos?\s+Total(?:\s+general)?\s+Tasa",
    re.IGNORECASE,
)
RE_TITULO_SECCION_NEU = re.compile(
    r"Neumon[ií]as?[\s,]+El\s+Salvador[\s,]+SE\s*-?\s*0?(\d{1,2})"
    r"(?:\s*-\s*(\d{1,2})\b(?!\d))?[\s,.-]*(?:de\s+)?(\d{4})?",
    re.IGNORECASE | re.DOTALL,
)
RE_PIE_NEU = re.compile(
    r"neumon[ií]as?.{0,40}?SE\s*(\d{1,2})(?:\s*-\s*(\d{1,2})\b(?!\d))?[\s,.-]*(\d{4})",
    re.IGNORECASE | re.DOTALL,
)
MARCADORES_FIN_NEU = [
    "Estratificación", "Estratificacion",
    "Ministerio de Salud / Dirección",
    "Ministerio de Salud / Direccion",
]


@dataclass
class FilaNeumonia:
    departamento: str
    total_acum: float
    tasa: float | None


@dataclass
class ResultadoNeumonia:
    archivo: str
    anio: int
    semana_archivo: str | None
    version: int
    estado: str
    nota: str = ""
    layout: str | None = None
    semana_corte: int | None = None
    fuente_semana: str | None = None
    anio_titulo: int | None = None
    pagina: int | None = None
    filas: list[FilaNeumonia] = field(default_factory=list)
    otros_paises: list[float] = field(default_factory=list)
    totales_bloque: list[float] = field(default_factory=list)
    total_impreso: float | None = None
    suma14: float | None = None
    validacion_cuadra: bool | None = None
    diff_total: float | None = None
    titulo_exacto: str = ""


def _semana_de_grupos(m: re.Match) -> tuple[int, int | None]:
    semana = int(m.group(2)) if m.group(2) else int(m.group(1))
    anio = int(m.group(3)) if m.lastindex and m.group(3) and m.group(3).isdigit() else None
    return semana, anio


def _extraer_semana_titulo_neu(texto: str) -> tuple[int | None, int | None, str | None]:
    for regex, fuente in (
        (RE_TITULO_TABLA_NEU, "titulo_tabla"),
        (RE_PIE_NEU, "pie_estratificacion"),
        (RE_TITULO_SECCION_NEU, "titulo_seccion"),
    ):
        m = regex.search(texto)
        if m:
            semana, anio = _semana_de_grupos(m)
            return semana, anio, fuente
    return None, None, None


def _recortar_bloque_neu(texto: str) -> str:
    m = RE_TITULO_TABLA_NEU.search(texto)
    if m:
        inicio = m.start()
    else:
        m2 = RE_ENCABEZADO_NEU.search(texto)
        inicio = m2.start() if m2 else 0
    fin = len(texto)
    for marcador in MARCADORES_FIN_NEU:
        idx = texto.find(marcador, inicio + 1)
        if idx != -1:
            fin = min(fin, idx)
    return texto[inicio:fin]


def _extraer_filas_neu(bloque: str) -> tuple[list[FilaNeumonia], list[float]]:
    _esp = r"[^\S\n]+"
    filas = []
    for nombre, patron in _PATRON_NOMBRE.items():
        regex = re.compile(rf"{patron}{_esp}({_NUM})(?:{_esp}({_NUM}))?")
        m = regex.search(bloque)
        if m:
            total = parsear_numero(m.group(1))
            tasa = parsear_numero(m.group(2)) if m.group(2) else None
            filas.append(FilaNeumonia(nombre, total, tasa))
    regex_otros = re.compile(rf"{_PATRON_OTROS}(?:{_esp}({_NUM}))?(?:{_esp}({_NUM}))?")
    m_otros = regex_otros.search(bloque)
    otros = [parsear_numero(g) for g in (m_otros.groups() if m_otros else []) if g]
    return filas, otros


def _extraer_totales_neu(bloque: str) -> list[tuple[float, float | None]]:
    _esp = r"[^\S\n]+"
    totales = []
    for m in re.finditer(rf"Total(?:{_esp}general)?{_esp}({_NUM})(?:{_esp}({_NUM}))?", bloque):
        total = parsear_numero(m.group(1))
        tasa = parsear_numero(m.group(2)) if m.group(2) else None
        totales.append((total, tasa))
    return totales


def analizar_texto_pagina_neumonias(texto_pagina: str, resultado: ResultadoNeumonia) -> ResultadoNeumonia:
    m_titulo = RE_TITULO_TABLA_NEU.search(texto_pagina)
    resultado.titulo_exacto = re.sub(r"\s+", " ", m_titulo.group(0)).strip() if m_titulo else ""
    resultado.layout = (
        "pagina_propia"
        if (m_titulo and "grupo de edad" not in m_titulo.group(0).lower()) or (
            not m_titulo and RE_ENCABEZADO_NEU.search(texto_pagina)
        )
        else "lado_a_lado"
    )
    semana, anio_titulo, fuente_semana = _extraer_semana_titulo_neu(texto_pagina)
    resultado.semana_corte = semana
    resultado.anio_titulo = anio_titulo
    resultado.fuente_semana = fuente_semana

    bloque = _recortar_bloque_neu(texto_pagina)
    filas, otros = _extraer_filas_neu(bloque)
    resultado.filas = filas
    resultado.otros_paises = otros

    if len(filas) < 14:
        if len(filas) == 0:
            resultado.estado = "sin_filas_sospecha_imagen"
            resultado.nota = (
                "pagina de neumonias localizada (titulo presente) pero 0 filas "
                "departamentales en el texto extraible -- sospecha de tabla-imagen"
            )
        else:
            resultado.estado = "error_extraccion"
            resultado.nota = f"solo {len(filas)}/14 departamentos encontrados en el bloque"
        return resultado

    totales = _extraer_totales_neu(bloque)
    resultado.totales_bloque = [t for t, _ in totales]
    suma14 = sum(f.total_acum for f in filas)
    resultado.suma14 = suma14

    if totales:
        candidatos = [suma14] + ([suma14 + otros[0]] if otros else [])
        diffs = [(abs(c - t), c - t, t) for t, _ in totales for c in candidatos]
        diffs.sort()
        resultado.diff_total = diffs[0][1]
        resultado.total_impreso = diffs[0][2]
        resultado.validacion_cuadra = diffs[0][0] < 0.5

    if resultado.validacion_cuadra is False and abs(resultado.diff_total or 0) <= 3:
        resultado.estado = "ok_discrepancia_minima"
        resultado.nota = (
            f"total impreso difiere de la suma de celdas en {resultado.diff_total:+.0f} "
            "(inconsistencia interna del boletin, celdas conservadas)"
        )
    elif resultado.validacion_cuadra is False:
        resultado.estado = "revision_manual"
        resultado.nota = (
            f"suma14={suma14:.0f} otros={otros} totales_bloque={resultado.totales_bloque} "
            "-- no cuadra con ningun total impreso"
        )
        return resultado
    elif semana is None:
        resultado.estado = "revision_manual"
        resultado.nota = "tabla extraida pero no se pudo leer la semana de corte"
        return resultado
    else:
        resultado.estado = "ok"

    if (
        semana is not None
        and resultado.semana_archivo is not None
        and "-" not in str(resultado.semana_archivo)
        and semana != int(resultado.semana_archivo)
    ):
        resultado.estado = "revision_manual"
        resultado.nota = (
            f"semana del {fuente_semana} (SE{semana}) difiere de la del nombre de "
            f"archivo (SE{resultado.semana_archivo})"
            + (f"; {resultado.nota}" if resultado.nota else "")
        )
    return resultado


def _localizar_pagina_neumonias(paginas: list[tuple[int, str]]) -> tuple[int, str] | None:
    _esp = r"[^\S\n]+"
    mejor = None
    for i, texto in paginas:
        if not RE_MARCA_NEUMONIA.search(texto):
            continue
        con_titulo = bool(RE_TITULO_TABLA_NEU.search(texto) or RE_ENCABEZADO_NEU.search(texto))
        n_filas = sum(
            1 for patron in _PATRON_NOMBRE.values()
            if re.search(rf"{patron}{_esp}(?:{_NUM})", texto)
        )
        if n_filas >= 10 and RE_OTRA_ENFERMEDAD_NEU.search(texto) and not con_titulo:
            continue
        if n_filas >= 10 and (con_titulo or not RE_OTRA_ENFERMEDAD_NEU.search(texto)):
            return i, texto
        if con_titulo and mejor is None:
            mejor = (i, texto)
    return mejor


def procesar_boletin_neumonias(path: Path, texto_paginas: list[tuple[int, str]] | None = None) -> ResultadoNeumonia:
    anio, semana_archivo, version = parsear_nombre(path)
    resultado = ResultadoNeumonia(
        archivo=path.name, anio=anio, semana_archivo=semana_archivo,
        version=version, estado="pendiente",
    )
    if texto_paginas is None:
        import pdfplumber
        try:
            with pdfplumber.open(path) as pdf:
                texto_paginas = [(i, p.extract_text() or "") for i, p in enumerate(pdf.pages)]
        except Exception as exc:  # noqa: BLE001
            resultado.estado = "error_extraccion"
            resultado.nota = f"excepcion abriendo/leyendo PDF: {exc}"
            return resultado

    candidata = _localizar_pagina_neumonias(texto_paginas)
    if candidata is None:
        texto_p0 = texto_paginas[0][1] if texto_paginas else ""
        if RE_MARCADORES_VACACION.search(texto_p0):
            resultado.estado = "ausencia_esperada_vacacion"
            resultado.nota = "sin tabla departamental de neumonias; portada marca vacaciones"
        elif not any(RE_MARCA_NEUMONIA.search(t) for _, t in texto_paginas):
            resultado.estado = "sin_texto_extraible"
            resultado.nota = "0 menciones de neumonias en todo el documento"
        else:
            resultado.estado = "sin_tabla_neumonias"
            resultado.nota = "el documento menciona neumonias pero no hay tabla departamental extraible"
        return resultado

    i, texto = candidata
    resultado.pagina = i + 1
    return analizar_texto_pagina_neumonias(texto, resultado)


def detectar_reimpresiones_neumonias(resultados: list[ResultadoNeumonia]) -> int:
    por_anio: dict[int, list[ResultadoNeumonia]] = defaultdict(list)
    for r in resultados:
        if r.estado in ESTADOS_USABLES and r.semana_corte is not None:
            por_anio[r.anio].append(r)
    n = 0
    for lista in por_anio.values():
        lista.sort(key=lambda r: r.semana_corte)
        for previo, actual in zip(lista, lista[1:]):
            v_previo = {f.departamento: f.total_acum for f in previo.filas}
            v_actual = {f.departamento: f.total_acum for f in actual.filas}
            if v_previo == v_actual:
                actual.estado = "revision_manual"
                actual.nota = (
                    f"los 14 valores departamentales son identicos a los del corte "
                    f"SE{previo.semana_corte} ({previo.archivo}) -- tabla reimpresa/rezagada"
                )
                n += 1
    return n


@dataclass
class PuntoSemanal:
    anio: int
    departamento: str
    semana: int
    valor: float | None
    nota: str = ""


def desacumular_neumonias(resultados: list[ResultadoNeumonia]) -> tuple[list[PuntoSemanal], list[dict]]:
    series: dict[tuple[int, str], dict[int, float]] = defaultdict(dict)
    for r in resultados:
        if r.estado not in ESTADOS_USABLES or r.semana_corte is None:
            continue
        for fila in r.filas:
            series[(r.anio, fila.departamento)][r.semana_corte] = fila.total_acum

    puntos: list[PuntoSemanal] = []
    negativas: list[dict] = []
    for (anio, depto), por_semana in series.items():
        anterior_semana, anterior_valor = None, 0.0
        for semana, valor in sorted(por_semana.items()):
            if anterior_semana is None:
                nota = "" if semana == 1 else (
                    f"primer corte del anio en SE{semana}: acumulado SE1-SE{semana}, "
                    "no incidencia de una semana"
                )
                puntos.append(PuntoSemanal(anio, depto, semana, valor, nota))
            else:
                diff = valor - anterior_valor
                if semana - anterior_semana > 1:
                    for s in range(anterior_semana + 1, semana + 1):
                        puntos.append(PuntoSemanal(
                            anio, depto, s, None,
                            nota=f"hueco entre cortes SE{anterior_semana} y SE{semana} -- sin dato semanal",
                        ))
                elif diff < 0:
                    negativas.append({
                        "anio": anio, "departamento": depto, "semana": semana,
                        "diferencia": diff, "acumulado_anterior": anterior_valor,
                        "acumulado_actual": valor,
                    })
                    puntos.append(PuntoSemanal(
                        anio, depto, semana, None,
                        nota=f"correccion retroactiva: diff={diff:.0f} (excluida de la serie)",
                    ))
                else:
                    puntos.append(PuntoSemanal(anio, depto, semana, diff))
            anterior_semana, anterior_valor = semana, valor
    return puntos, negativas


# ---------------------------------------------------------------------------
# Vigilancia centinela / laboratorial de virus
# ---------------------------------------------------------------------------

RE_MARCA_VIRUS = re.compile(
    r"vigilancia\s+centinela\s+de\s+influenza|vigilancia\s+laboratorial\s+para\s+virus"
    r"|virus\s+respiratorios",
    re.IGNORECASE,
)
RE_INICIO_TABLA_LAB = re.compile(
    r"(?:Tabla\s*1\.\s*-?\s*Resumen\s+de\s+resultados\s+de\s+Vigilancia\s+Laboratorial"
    r"|Vigilancia\s+Laboratorial\s+para\s+virus\s+respiratorios"
    r"|Total\s+de\s+muestras\s+analizadas)",
    re.IGNORECASE,
)
RE_SEMANA_LAB = re.compile(
    r"(?:Vigilancia\s+Laboratorial|Resumen\s+de\s+resultados).{0,200}?SE\s*(\d{1,2})",
    re.IGNORECASE | re.DOTALL,
)
RE_SEMANA_CENTINELA = re.compile(
    r"Vigilancia\s+centinela\s+de\s+influenza.{0,80}?SE\s*(\d{1,2})",
    re.IGNORECASE | re.DOTALL,
)

# codigo, patron de etiqueta, unidad. Orden: etiquetas largas primero.
METRICAS_LAB: list[tuple[str, str, str]] = [
    ("muestras_analizadas", r"Total\s+de\s+muestras\s+analizadas", "conteo"),
    ("muestras_positivas", r"Muestras\s+positivas\s+a\s+virus\s+respiratorios", "conteo"),
    ("influenza_total", r"Total\s+de\s+virus\s+de\s+influenza\s*\(\s*A\s*y\s*B\s*\)", "conteo"),
    ("influenza_a_h1n1", r"Influenza\s+A\s*\(\s*H1N1\s*\)(?:pdm2009|\*)?", "conteo"),
    ("influenza_a_no_subtipificado", r"Influenza\s+A\s+no\s+sub[- ]?tipificado", "conteo"),
    ("influenza_a_h3n2", r"Influenza\s+A\s+H3N2\*?", "conteo"),
    ("influenza_b", r"Influenza\s+B\*?\*?", "conteo"),
    ("otros_virus_total", r"Total\s+de\s+otros\s+virus\s+respiratorios", "conteo"),
    ("parainfluenza", r"Parainfluenza", "conteo"),
    ("vsr", r"Virus\s+Sincitial\s+Respiratorio\s*\(\s*VSR\s*\)", "conteo"),
    ("adenovirus", r"Adenovirus", "conteo"),
    ("covid_19", r"COVID\s*[- ]?19(?:\s*\(\s*SE\s*\d+\s*\))?", "conteo"),
    ("positividad_virus", r"Positividad\s+acumulada\s+para\s+virus\s+respiratorios", "porcentaje"),
    ("positividad_influenza", r"Positividad\s+acumulada\s+para\s+Influenza", "porcentaje"),
    ("positividad_vsr", r"Positividad\s+acumulada\s+para\s+VSR", "porcentaje"),
]


@dataclass
class MetricaVirus:
    codigo: str
    unidad: str
    valores: list[float]
    anio_previo: float | None
    anio_actual: float | None
    semana: float | None


@dataclass
class ResultadoVirus:
    archivo: str
    anio: int
    semana_archivo: str | None
    version: int
    estado: str
    nota: str = ""
    pagina: int | None = None
    semana_corte: int | None = None
    fuente_semana: str | None = None
    n_columnas: int | None = None
    granularidad: str = "nacional"
    unidad_observacion: str = "muestras_laboratorio_centinela"
    metricas: list[MetricaVirus] = field(default_factory=list)
    virus_presentes: list[str] = field(default_factory=list)
    tiene_covid: bool | None = None
    tiene_departamento: bool = False


def _interpretar_columnas(valores: list[float]) -> tuple[float | None, float | None, float | None]:
    if len(valores) >= 3:
        return valores[0], valores[1], valores[2]
    if len(valores) == 2:
        return valores[0], valores[1], None
    if len(valores) == 1:
        return None, valores[0], None
    return None, None, None


def extraer_metricas_lab(bloque: str) -> list[MetricaVirus]:
    plano = re.sub(r"\s+", " ", bloque)
    metricas: list[MetricaVirus] = []
    for codigo, patron, unidad in METRICAS_LAB:
        m = re.search(patron, plano, re.IGNORECASE)
        if not m:
            continue
        resto = plano[m.end(): m.end() + 120]
        vals: list[float] = []
        for tok in resto.strip().split():
            if tok.startswith("(") or re.fullmatch(r"\(SE\d+\)", tok, re.I):
                continue
            if re.fullmatch(r"\d+(?:[.,]\d+)?%?", tok):
                vals.append(parsear_numero_lab(tok))
                if len(vals) == 3:
                    break
            else:
                break
        previo, actual, semana = _interpretar_columnas(vals)
        metricas.append(MetricaVirus(
            codigo=codigo, unidad=unidad, valores=vals,
            anio_previo=previo, anio_actual=actual, semana=semana,
        ))
    return metricas


def _recortar_bloque_lab(texto: str) -> str:
    m = RE_INICIO_TABLA_LAB.search(texto)
    inicio = m.start() if m else 0
    fin = len(texto)
    for marcador in (
        "Fuente: VIGEPES",
        "Fuente:VIGEPES",
        "Ministerio de Salud / Dirección",
        "Ministerio de Salud / Direccion",
    ):
        idx = texto.find(marcador, inicio + 40)
        if idx != -1:
            fin = min(fin, idx)
    return texto[inicio:fin]


def analizar_texto_pagina_virus(texto_pagina: str, resultado: ResultadoVirus) -> ResultadoVirus:
    m_se = RE_SEMANA_LAB.search(texto_pagina) or RE_SEMANA_CENTINELA.search(texto_pagina)
    if m_se:
        resultado.semana_corte = int(m_se.group(1))
        resultado.fuente_semana = "titulo_tabla_lab"

    bloque = _recortar_bloque_lab(texto_pagina)
    metricas = extraer_metricas_lab(bloque)
    resultado.metricas = metricas
    resultado.n_columnas = max((len(m.valores) for m in metricas), default=0) or None
    resultado.virus_presentes = [
        m.codigo for m in metricas
        if m.unidad == "conteo" and m.codigo not in (
            "muestras_analizadas", "muestras_positivas", "influenza_total", "otros_virus_total"
        )
        and any(v and v > 0 for v in (m.anio_actual, m.semana) if v is not None)
    ]
    covid = next((m for m in metricas if m.codigo == "covid_19"), None)
    resultado.tiene_covid = covid is not None
    resultado.tiene_departamento = bool(
        re.search(r"Ahuachap[aá]n.{0,20}\d", texto_pagina, re.I)
        and "centinela" in texto_pagina.lower()
        and RE_ENCABEZADO_NEU.search(texto_pagina) is None
    )

    muestras = next((m for m in metricas if m.codigo == "muestras_analizadas"), None)
    if muestras is None or not muestras.valores:
        resultado.estado = "revision_manual"
        resultado.nota = "pagina de vigilancia localizada pero no se leyeron muestras analizadas"
        return resultado

    resultado.estado = "ok"
    if covid is not None and not covid.valores:
        resultado.nota = "etiqueta COVID-19 presente sin valores extraibles (no se fabrica)"
    return resultado


def _localizar_pagina_virus(paginas: list[tuple[int, str]]) -> tuple[int, str] | None:
    mejor = None
    for i, texto in paginas:
        if RE_INICIO_TABLA_LAB.search(texto) and re.search(r"muestras\s+analizadas", texto, re.I):
            return i, texto
        if RE_MARCA_VIRUS.search(texto) and mejor is None:
            mejor = (i, texto)
    return mejor


def procesar_boletin_virus(path: Path, texto_paginas: list[tuple[int, str]] | None = None) -> ResultadoVirus:
    anio, semana_archivo, version = parsear_nombre(path)
    resultado = ResultadoVirus(
        archivo=path.name, anio=anio, semana_archivo=semana_archivo,
        version=version, estado="pendiente",
    )
    if texto_paginas is None:
        import pdfplumber
        try:
            with pdfplumber.open(path) as pdf:
                texto_paginas = [(i, p.extract_text() or "") for i, p in enumerate(pdf.pages)]
        except Exception as exc:  # noqa: BLE001
            resultado.estado = "error_extraccion"
            resultado.nota = f"excepcion abriendo/leyendo PDF: {exc}"
            return resultado

    candidata = _localizar_pagina_virus(texto_paginas)
    if candidata is None:
        texto_p0 = texto_paginas[0][1] if texto_paginas else ""
        if RE_MARCADORES_VACACION.search(texto_p0):
            resultado.estado = "ausencia_esperada_vacacion"
            resultado.nota = "sin tabla laboratorial de virus; portada marca vacaciones"
        elif not any(RE_MARCA_VIRUS.search(t) for _, t in texto_paginas):
            resultado.estado = "sin_texto_extraible"
            resultado.nota = "0 menciones de vigilancia centinela/laboratorial de virus"
        else:
            resultado.estado = "sin_tabla_virus"
            resultado.nota = "menciona vigilancia de virus pero no hay tabla laboratorial extraible"
        return resultado

    i, texto = candidata
    resultado.pagina = i + 1
    if not RE_INICIO_TABLA_LAB.search(texto) and not re.search(r"muestras\s+analizadas", texto, re.I):
        resultado.estado = "sin_filas_sospecha_imagen"
        resultado.nota = "seccion de vigilancia presente sin tabla de muestras extraible"
        return resultado
    return analizar_texto_pagina_virus(texto, resultado)


# ---------------------------------------------------------------------------
# Volcado
# ---------------------------------------------------------------------------

def _asegurar_interim() -> None:
    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)


def volcar_bitacora(
    neumonias: list[ResultadoNeumonia],
    virus: list[ResultadoVirus],
    descartados: list[tuple[Path, str]],
) -> None:
    _asegurar_interim()
    path = INTERIM_ROOT / "bitacora_respiratorios.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "seccion", "archivo", "anio", "semana_archivo", "version", "estado",
            "pagina", "semana_corte", "layout_o_columnas", "nota",
        ])
        for r in neumonias:
            w.writerow([
                "neumonias", r.archivo, r.anio, r.semana_archivo, r.version, r.estado,
                r.pagina, r.semana_corte, r.layout, r.nota,
            ])
        for r in virus:
            w.writerow([
                "virus", r.archivo, r.anio, r.semana_archivo, r.version, r.estado,
                r.pagina, r.semana_corte, r.n_columnas, r.nota,
            ])
        for p, motivo in descartados:
            w.writerow(["descartado_version", p.name, "", "", "", "descartado_version",
                        "", "", "", motivo])
    print(f"  -> {path}")


def volcar_inventario_neumonias(resultados: list[ResultadoNeumonia]) -> None:
    _asegurar_interim()
    path = INTERIM_ROOT / "inventario_neumonias.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "archivo", "anio", "estado", "layout", "pagina", "semana_corte",
            "fuente_semana", "titulo_exacto", "suma14", "total_impreso",
            "diff_total", "validacion_cuadra", "n_filas", "nota",
        ])
        for r in resultados:
            w.writerow([
                r.archivo, r.anio, r.estado, r.layout, r.pagina, r.semana_corte,
                r.fuente_semana, r.titulo_exacto,
                f"{r.suma14:.0f}" if r.suma14 is not None else "",
                f"{r.total_impreso:.0f}" if r.total_impreso is not None else "",
                f"{r.diff_total:+.0f}" if r.diff_total is not None else "",
                r.validacion_cuadra, len(r.filas), r.nota,
            ])
    crudo = INTERIM_ROOT / "crudo_neumonias_departamental.csv"
    with open(crudo, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archivo", "anio", "estado", "semana_corte", "departamento", "total_acum", "tasa"])
        for r in resultados:
            if r.estado not in ESTADOS_USABLES:
                continue
            for fila in r.filas:
                w.writerow([r.archivo, r.anio, r.estado, r.semana_corte, fila.departamento,
                            f"{fila.total_acum:.0f}", fila.tasa])
    print(f"  -> {path}")
    print(f"  -> {crudo}")


def volcar_inventario_virus(resultados: list[ResultadoVirus]) -> None:
    _asegurar_interim()
    path = INTERIM_ROOT / "inventario_vigilancia_virus.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "archivo", "anio", "estado", "pagina", "semana_corte", "n_columnas",
            "granularidad", "unidad_observacion", "metrica", "unidad",
            "anio_previo", "anio_actual", "semana", "tiene_covid", "nota",
        ])
        for r in resultados:
            if not r.metricas:
                w.writerow([
                    r.archivo, r.anio, r.estado, r.pagina, r.semana_corte, r.n_columnas,
                    r.granularidad, r.unidad_observacion, "", "", "", "", "",
                    r.tiene_covid, r.nota,
                ])
                continue
            for m in r.metricas:
                w.writerow([
                    r.archivo, r.anio, r.estado, r.pagina, r.semana_corte, r.n_columnas,
                    r.granularidad, r.unidad_observacion, m.codigo, m.unidad,
                    m.anio_previo, m.anio_actual, m.semana, r.tiene_covid, r.nota,
                ])
    print(f"  -> {path}")


def volcar_desacumulado_neumonias(puntos: list[PuntoSemanal], negativas: list[dict]) -> None:
    _asegurar_interim()
    path = INTERIM_ROOT / "desacumulado_neumonias.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "departamento", "semana", "valor", "nota"])
        for p in sorted(puntos, key=lambda x: (x.anio, x.departamento, x.semana)):
            w.writerow([p.anio, p.departamento, p.semana,
                        f"{p.valor:.0f}" if p.valor is not None else "", p.nota])
    path2 = INTERIM_ROOT / "correcciones_negativas_neumonias.csv"
    with open(path2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "departamento", "semana", "diferencia", "acumulado_anterior", "acumulado_actual"])
        for c in negativas:
            w.writerow([c["anio"], c["departamento"], c["semana"], f"{c['diferencia']:.0f}",
                        f"{c['acumulado_anterior']:.0f}", f"{c['acumulado_actual']:.0f}"])
    print(f"  -> {path}")
    print(f"  -> {path2}  ({len(negativas)} correcciones retroactivas)")


def volcar_resumen(neumonias: list[ResultadoNeumonia], virus: list[ResultadoVirus]) -> None:
    _asegurar_interim()
    cortes_neu = Counter()
    for r in neumonias:
        if r.estado in ESTADOS_USABLES:
            cortes_neu[r.anio] += 1
    cortes_vir = Counter()
    covid_por_anio = Counter()
    for r in virus:
        if r.estado in ESTADOS_USABLES:
            cortes_vir[r.anio] += 1
            if r.tiene_covid:
                covid_por_anio[r.anio] += 1
    resumen = {
        "pdf_neumonias": len(neumonias),
        "pdf_virus": len(virus),
        "estados_neumonias": dict(Counter(r.estado for r in neumonias)),
        "estados_virus": dict(Counter(r.estado for r in virus)),
        "cortes_usables_neumonias_por_anio": {str(k): v for k, v in sorted(cortes_neu.items())},
        "cortes_usables_virus_por_anio": {str(k): v for k, v in sorted(cortes_vir.items())},
        "boletines_con_etiqueta_covid_por_anio": {str(k): v for k, v in sorted(covid_por_anio.items())},
        "anios_en_filesystem": sorted({r.anio for r in neumonias} | {r.anio for r in virus}),
        "anio_2020_presente": (RAW_ROOT / "2020").exists(),
        "unidad_virus": "muestras_laboratorio_centinela (nacional); no son casos clinicos departamentales",
        "unidad_neumonias": "conteo notificado departamental (candidato a desacumular si la serie es acumulada)",
    }
    path = INTERIM_ROOT / "resumen_cobertura.json"
    path.write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  -> {path}")
    print("  Estados neumonias:", resumen["estados_neumonias"])
    print("  Estados virus:", resumen["estados_virus"])


def _abrir_pdf(path: Path) -> list[tuple[int, str]] | None:
    import pdfplumber
    try:
        with pdfplumber.open(path) as pdf:
            return [(i, p.extract_text() or "") for i, p in enumerate(pdf.pages)]
    except Exception as exc:  # noqa: BLE001
        print(f"  error leyendo {path.name}: {exc}")
        return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limite", type=int, default=None)
    ap.add_argument("--solo-paso1", action="store_true")
    ap.add_argument("--solo-neumonias", action="store_true")
    ap.add_argument("--solo-virus", action="store_true")
    args = ap.parse_args()

    hacer_neu = not args.solo_virus
    hacer_vir = not args.solo_neumonias

    archivos = descubrir_archivos(args.limite)
    vigentes, descartados = resolver_versiones(archivos)
    print(
        f"Descubrimiento: {len(archivos)} PDF, {len(vigentes)} vigentes "
        f"({len(descartados)} descartados por version)."
    )

    neumonias: list[ResultadoNeumonia] = []
    virus: list[ResultadoVirus] = []
    for i, path in enumerate(vigentes, 1):
        paginas = _abrir_pdf(path)
        if paginas is None:
            anio, semana_archivo, version = parsear_nombre(path)
            if hacer_neu:
                r = ResultadoNeumonia(
                    archivo=path.name, anio=anio, semana_archivo=semana_archivo,
                    version=version, estado="error_extraccion",
                    nota="no se pudo abrir el PDF",
                )
                neumonias.append(r)
            if hacer_vir:
                virus.append(ResultadoVirus(
                    archivo=path.name, anio=anio, semana_archivo=semana_archivo,
                    version=version, estado="error_extraccion",
                    nota="no se pudo abrir el PDF",
                ))
            continue
        if hacer_neu:
            neumonias.append(procesar_boletin_neumonias(path, paginas))
        if hacer_vir:
            virus.append(procesar_boletin_virus(path, paginas))
        if i % 20 == 0:
            print(f"  ... {i}/{len(vigentes)}")

    if hacer_neu:
        n_re = detectar_reimpresiones_neumonias(neumonias)
        if n_re:
            print(f"Reimpresiones de neumonias reclasificadas: {n_re}")
        volcar_inventario_neumonias(neumonias)

    if hacer_vir:
        volcar_inventario_virus(virus)

    volcar_bitacora(neumonias, virus, descartados)
    volcar_resumen(neumonias, virus)

    if args.solo_paso1 or not hacer_neu:
        return

    puntos, negativas = desacumular_neumonias(neumonias)
    volcar_desacumulado_neumonias(puntos, negativas)


if __name__ == "__main__":
    main()
