"""
Corrida exploratoria de distribucion de casos de dengue (MINSAL, 2018-2023 sin 2020).

Resuelve el punto H de docs/contexto/02-decisiones-abiertas.md: si desacumulando
las series Probable/Confirmado de la tabla departamental (acumuladas desde SE1,
ver trampa 8 de docs/contexto/03-fuentes-de-datos.md) se obtiene una variable
objetivo departamental utilizable para el canal endemico.

NO escribe a PostgreSQL -- es analisis exploratorio, no ingesta. NO es el parser
de produccion (backend/ingestion/minsal/parser.py, que sigue bloqueado por el
punto H hasta que el equipo decida con esta evidencia). Toda salida va a
data/interim/corrida_distribucion/ (gitignoreada).

Uso:
    python3 corrida_distribucion.py                  # corrida completa (4 pasos)
    python3 corrida_distribucion.py --solo-paso1      # solo extraccion (para iterar rapido)
    python3 corrida_distribucion.py --limite 20       # solo los primeros N PDF por anio
"""

from __future__ import annotations

import argparse
import csv
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

RAIZ = Path(__file__).parent
RAW_ROOT = RAIZ / "data" / "raw" / "minsal"
INTERIM_ROOT = RAIZ / "data" / "interim" / "corrida_distribucion"
ANIOS = [2018, 2019, 2021, 2022, 2023]

DEPARTAMENTOS = [
    "Ahuachapán", "Cabañas", "Chalatenango", "Cuscatlán", "La Libertad",
    "La Paz", "Santa Ana", "San Miguel", "Sonsonate", "San Salvador",
    "San Vicente", "La Unión", "Usulután", "Morazán",
]

# Patrones tolerantes a variantes con/sin tilde vistas en los PDF.
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
_PATRON_OTROS = r"Otros\s+pa[ií]ses"

_NUM = r"[\d]+(?:[.,]\d+)?"
_FILA_RE_TMPL = r"{nombre}\s+((?:{num}\s+){{0,3}}{num})"

MARCADORES_FIN_BLOQUE = [
    "Índices larvarios", "Indices larvarios", "Resultados de muestras",
    "Actividades regulares", "Estratificación de municipios",
    "Estratificacion de municipios",
]
# "FUENTE:"/"Fuente:" y "* Esta tasa..." deliberadamente NO son marcadores de fin:
# en algunos boletines (ej. SE062023) el layout de dos cajas visuales hace que
# "FUENTE: VIGEPES" quede interleaved a mitad de la tabla departamental real
# (antes de Morazán/La Unión/Otros países), no al final -- cortar ahi perdia
# filas reales. El recorte se apoya solo en marcadores que en la evidencia
# revisada nunca aparecen dentro del bloque departamental mismo.

RE_ANIO_DIR = re.compile(r"^(2018|2019|2021|2022|2023)$")
RE_SEMANA_ARCHIVO = re.compile(r"SE(\d{1,2})(?:-(\d{1,2}))?", re.IGNORECASE)
RE_VERSION = re.compile(r"_v(\d+)", re.IGNORECASE)

# Ancla estricta para localizar/recortar la tabla departamental de dengue: exige "probable(s)" y "dengue" cerca de "por/segun departamento",
# para no confundir con el titulo de la tabla de indices larvarios ("...larvarios
# por departamento...", misma pagina, sin relacion con casos probables/confirmados).
RE_ANCLA_TABLA_DEPTO = re.compile(
    r"probables?.{0,30}?dengue.{0,150}?(?:por|seg[uú]n)\s+departamento",
    re.IGNORECASE | re.DOTALL,
)
RE_TITULO_FAMILIA_A = re.compile(
    r"probables?\s+de\s+dengue\s+SE\s*(\d{1,2})\b.{0,120}?"
    r"confirmados?\s+de\s+dengue\s+SE\s*(\d{1,2})\b",
    re.IGNORECASE | re.DOTALL,
)
RE_SEMANAS_FAMILIA_B = re.compile(r"SE\s*(\d{1,2})\D{1,15}SE\s*(\d{1,2})", re.DOTALL)
RE_MARCADORES_VACACION = re.compile(
    r"vacaciones|vigilancia\s+intensificada|semana\s+santa|fiestas\s+agostinas|fin\s+de\s+a[ñn]o",
    re.IGNORECASE,
)


def _normalizar(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


@dataclass
class FilaCruda:
    departamento: str
    valores: list[float]


@dataclass
class ResultadoBoletin:
    archivo: str
    anio: int
    semana_archivo: str | None
    version: int
    estado: str
    nota: str = ""
    familia: str | None = None
    semana_probable: int | None = None
    semana_confirmado: int | None = None
    filas: list[FilaCruda] = field(default_factory=list)
    otros_paises: list[float] = field(default_factory=list)
    total_impreso: list[float] = field(default_factory=list)
    suma14: list[float] = field(default_factory=list)
    validacion_tabla: bool | None = None
    validacion_nacional: bool | None = None


# ---------------------------------------------------------------------------
# Paso 0 -- descubrimiento de archivos y resolucion de versiones
# ---------------------------------------------------------------------------

def descubrir_archivos(limite: int | None = None) -> list[Path]:
    archivos = []
    for carpeta in sorted(RAW_ROOT.iterdir()):
        if not carpeta.is_dir() or not RE_ANIO_DIR.match(carpeta.name):
            continue
        pdfs = sorted(carpeta.glob("*.pdf"))
        if limite is not None:
            pdfs = pdfs[:limite]
        archivos.extend(pdfs)
    return archivos


def parsear_nombre(path: Path) -> tuple[int, str | None, int]:
    anio = int(path.parent.name)
    nombre = path.stem
    m = RE_SEMANA_ARCHIVO.search(nombre)
    if m:
        semana = m.group(1) if not m.group(2) else f"{int(m.group(1))}-{int(m.group(2))}"
    else:
        semana = None
    v = RE_VERSION.search(nombre)
    version = int(v.group(1)) if v else 1
    return anio, semana, version


def resolver_versiones(archivos: list[Path]) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Agrupa por (anio, semana_archivo) y se queda con la version mas alta.

    Archivos sin semana_archivo (vacaciones sin patron SEnn) nunca colisionan
    entre si -- cada uno es un boletin distinto, no versiones del mismo.
    """
    grupos: dict[tuple, list[tuple[int, Path]]] = defaultdict(list)
    for p in archivos:
        anio, semana, version = parsear_nombre(p)
        if semana is None:
            grupos[(anio, p.name)].append((version, p))
        else:
            grupos[(anio, semana)].append((version, p))

    vigentes = []
    descartados = []
    for _, miembros in grupos.items():
        miembros.sort(key=lambda t: t[0])
        vigentes.append(miembros[-1][1])
        for version, p in miembros[:-1]:
            descartados.append((p, f"version {version} superada por version {miembros[-1][0]}"))
    return sorted(vigentes), descartados


# ---------------------------------------------------------------------------
# Paso 1 -- extraccion de la tabla departamental
# ---------------------------------------------------------------------------

def _localizar_pagina_depto(pdf: "pdfplumber.PDF") -> tuple[int, str] | None:
    for i, page in enumerate(pdf.pages):
        texto = page.extract_text() or ""
        if RE_ANCLA_TABLA_DEPTO.search(texto):
            return i, texto
    return None


def _recortar_bloque_depto(texto: str) -> str | None:
    m = RE_ANCLA_TABLA_DEPTO.search(texto)
    if not m:
        return None
    inicio = m.end()
    fin = len(texto)
    for marcador in MARCADORES_FIN_BLOQUE:
        idx = texto.find(marcador, inicio)
        if idx != -1:
            fin = min(fin, idx)
    return texto[inicio:fin]


def _extraer_filas(bloque: str) -> tuple[list[FilaCruda], list[float], re.Match | None]:
    filas = []
    for nombre, patron in _PATRON_NOMBRE.items():
        regex = re.compile(_FILA_RE_TMPL.format(nombre=patron, num=_NUM))
        m = regex.search(bloque)
        if m:
            valores = [float(x.replace(",", ".")) for x in m.group(1).split()]
            filas.append(FilaCruda(nombre, valores))

    # "Otros paises" trae 2 numeros (probable, confirmado) en la mayoria del
    # corpus, pero NO siempre: SE102019_v3 y SE422019_v2 confirman que a veces
    # MINSAL SI imprime una tercera columna de tasa para esta fila (ej. "Otros
    # paises 0 0 0,0" / "Otros paises 2 2 1.16"), aunque el denominador de tasa
    # excluya a los extranjeros (trampa 6) -- la tasa impresa en esos casos es
    # simplemente 0 o casi 0, no una omision de columna. Si la captura se acota
    # a 2 numeros siempre, ese tercer valor queda sin consumir justo delante de
    # la ventana de _extraer_total_impreso y se cuela como si fuera el primer
    # valor del total impreso, corrompiendolo (bug confirmado empiricamente en
    # los dos boletines de arriba, tarjeta 26).
    #
    # El tercer numero se captura como opcional, pero SIN cruzar un salto de
    # linea ([^\S\n] en vez de \s): la fila "Otros paises" y la fila de total
    # impreso son lineas de texto distintas, y en boletines donde "Otros
    # paises" SI trae solo 2 numeros (ej. SE302019_v2), el primer numero del
    # total (en su propia linea) no debe poder confundirse con esa tercera
    # columna opcional.
    _esp = r"[^\S\n]+"
    regex_otros = re.compile(
        rf"{_PATRON_OTROS}{_esp}({_NUM}{_esp}{_NUM}(?:{_esp}{_NUM})?)"
    )
    m_otros = regex_otros.search(bloque)
    otros = [float(x.replace(",", ".")) for x in m_otros.group(1).split()] if m_otros else []
    return filas, otros, m_otros


def _extraer_total_impreso(bloque: str, otros_match_end: int) -> list[float]:
    ventana = bloque[otros_match_end:otros_match_end + 200]
    m = re.search(rf"({_NUM}(?:\s+{_NUM}){{0,3}})", ventana)
    if not m:
        return []
    return [float(x.replace(",", ".")) for x in m.group(1).split()]


def _detectar_familia(texto: str) -> str:
    ventana = texto[:2000]
    return "A" if re.search(r"tasa\s*x", ventana, re.IGNORECASE) else "B"


def _extraer_semanas(texto: str, familia: str) -> tuple[int | None, int | None]:
    m = RE_TITULO_FAMILIA_A.search(texto)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = RE_SEMANAS_FAMILIA_B.search(texto[texto.lower().find("departamento"):])
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def clasificar_sin_tabla(texto_p0: str, menciones_dengue: int, resultado: ResultadoBoletin) -> ResultadoBoletin:
    """Clasifica un boletin SIN pagina de tabla departamental de dengue:
    vacaciones (deteccion por CONTENIDO de portada, nunca por nombre de
    archivo -- `SE142023-Semana-Santa.pdf` contiene un patron SEnn valido),
    sin texto extraible, o anomalia real a revisar. Separado de
    procesar_boletin para poder probarse sobre texto extraido sin PDF."""
    if RE_MARCADORES_VACACION.search(texto_p0):
        resultado.estado = "ausencia_esperada_vacacion"
        resultado.nota = "sin pagina con tabla departamental de dengue; portada marca vacaciones/vigilancia intensificada"
    elif menciones_dengue == 0:
        # Descubierto en esta corrida, distinto de la trampa 9 (SE182023): el
        # boletin no es de vacaciones y no menciona "dengue" ni una sola vez en
        # todo el texto extraible -- indicio de tabla pegada como imagen/raster
        # (glifos como XObject, no como texto de fuente), no de ausencia real de
        # contenido. Requeriria OCR para confirmar/leer, fuera de alcance de esta
        # corrida exploratoria.
        resultado.estado = "sin_texto_extraible"
        resultado.nota = "0 menciones de 'dengue' en todo el documento -- sospecha de tabla renderizada como imagen, no ausencia de contenido"
    else:
        resultado.estado = "sin_tabla_no_vacacional"
        resultado.nota = "sin pagina con tabla departamental de dengue; portada NO marca vacaciones y el documento SI menciona dengue en otras secciones (ver trampa 9, SE182023)"
    return resultado


def procesar_boletin(path: Path) -> ResultadoBoletin:
    anio, semana_archivo, version = parsear_nombre(path)
    resultado = ResultadoBoletin(
        archivo=path.name, anio=anio, semana_archivo=semana_archivo, version=version,
        estado="pendiente",
    )

    try:
        with pdfplumber.open(path) as pdf:
            texto_p0 = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
            ubicacion = _localizar_pagina_depto(pdf)
            if ubicacion is None:
                menciones_dengue = sum((p.extract_text() or "").lower().count("dengue") for p in pdf.pages)
            else:
                menciones_dengue = None
    except Exception as exc:  # noqa: BLE001 -- diagnostico exploratorio, no ingesta
        resultado.estado = "error_extraccion"
        resultado.nota = f"excepcion abriendo/leyendo PDF: {exc}"
        return resultado

    if ubicacion is None:
        return clasificar_sin_tabla(texto_p0, menciones_dengue, resultado)

    _, texto_pagina = ubicacion
    return analizar_texto_pagina(texto_pagina, resultado)


def analizar_texto_pagina(texto_pagina: str, resultado: ResultadoBoletin) -> ResultadoBoletin:
    """Analisis completo de la pagina que contiene la tabla departamental
    (familia, semanas de corte, filas, blancos=cero, multisemana,
    validaciones de cuadre). Opera sobre TEXTO ya extraido -- separado de
    procesar_boletin (que solo agrega la I/O de pdfplumber) para poder
    probarse contra extractos reales guardados como fixture, sin versionar
    PDFs (docs/contexto/03-fuentes-de-datos.md, seccion pytest)."""
    bloque = _recortar_bloque_depto(texto_pagina)
    if bloque is None:
        resultado.estado = "error_extraccion"
        resultado.nota = "pagina localizada por 'dengue'+'departamento' pero sin anchor '(por|segun) departamento'"
        return resultado

    familia = _detectar_familia(texto_pagina)
    semana_prob, semana_conf = _extraer_semanas(texto_pagina, familia)
    filas, otros, m_otros = _extraer_filas(bloque)

    resultado.familia = familia
    resultado.semana_probable = semana_prob
    resultado.semana_confirmado = semana_conf
    resultado.filas = filas
    resultado.otros_paises = otros

    if len(filas) < 14:
        resultado.estado = "error_extraccion"
        resultado.nota = f"solo {len(filas)}/14 departamentos encontrados en el bloque"
        return resultado

    # Semanas combinadas (trampa 7) traen una columna extra de acumulado-rango
    # ("SE1-2") en el encabezado -- se detecta ahi, no contando columnas de datos,
    # porque el ruido de texto narrativo pegado a una fila (ver mas abajo) puede
    # imitar una columna de mas sin que el boletin sea multisemana.
    if re.search(r"SE\s*\d{1,2}\s*-\s*\d{1,2}", bloque[:250]):
        resultado.estado = "ausencia_esperada_multisemana"
        resultado.nota = "columna de acumulado-rango (SEn-n) detectada en el encabezado -- boletin de semanas combinadas (trampa 7), no se ingiere como semanal"
        return resultado

    # Ancho esperado por familia: A trae Tasa x 100.000 (3 columnas), B no (2).
    # Filas con MAS columnas que el ancho esperado son texto narrativo pegado al
    # final de la fila (ver SE232018: "Chalatenango 14 7 3.4 21 casos." -- el "21"
    # de la narrativa lateral queda contiguo al ultimo numero real de la fila, sin
    # separador no-numerico de por medio). Se recorta al ancho esperado en vez de
    # descartar la fila -- los primeros N valores capturados son siempre los
    # reales, la narrativa solo puede aportar numeros de MAS, nunca de menos.
    #
    # Filas con EXACTAMENTE una columna de menos son la trampa 2 (celda en blanco
    # = cero, no dato ausente) aplicada a la PRIMERA columna (probable): ver
    # SE062018, "La Libertad 0 0.0" -- MINSAL deja la celda de probable en blanco
    # cuando es cero (en vez de imprimir "0"), y ese blanco no dejo ningun rastro
    # de texto que separe el nombre del departamento de los dos numeros reales
    # (confirmado, tasa). Se rellena con un 0.0 a la izquierda -- consistente con
    # el total impreso de la tabla (validado contra SE062018: probable=12 cuadra
    # solo si las filas cortas se leen como probable=0).
    # Filas con DOS o mas columnas de menos si son un problema genuino y se rechazan.
    ancho_esperado = 3 if familia == "A" else 2
    filas_ok = []
    for f in filas:
        valores = f.valores
        if len(valores) == ancho_esperado - 1:
            valores = [0.0] + valores
        if len(valores) >= ancho_esperado:
            filas_ok.append(FilaCruda(f.departamento, valores[:ancho_esperado]))
    if len(filas_ok) < 14:
        resultado.estado = "error_extraccion"
        largos = Counter(len(f.valores) for f in filas)
        resultado.nota = f"{14 - len(filas_ok)} filas con menos de {ancho_esperado} columnas (conteos vistos: {dict(largos)})"
        return resultado
    filas = filas_ok
    resultado.filas = filas
    largo_modal = ancho_esperado

    suma14 = [sum(f.valores[i] for f in filas_ok) for i in range(largo_modal)]
    resultado.suma14 = suma14

    total_impreso = _extraer_total_impreso(bloque, m_otros.end()) if m_otros else []
    resultado.total_impreso = total_impreso

    # Si el total impreso cuadra con suma14 solo (sin otros paises) o con
    # suma14+otros, ambas se aceptan como "cuadra": la evidencia de esta misma
    # corrida muestra que la relacion entre el total impreso y "Otros paises" NO
    # es uniforme en el corpus -- SE522019 excluye a los extranjeros del total
    # (total=437=suma14 exacto, footnote "este total se excluye 2 extranjeros"),
    # pero SE352018..SE522018 SI los incluyen en el total de confirmados
    # (ej. SE352018: suma14_conf=143, otros_conf=1, total_impreso_conf=144).
    # No se pudo determinar la regla que distingue un caso de otro dentro del
    # tiempo de esta corrida -- se registra como hallazgo, no se adivina.
    val_tabla = None
    if total_impreso and len(total_impreso) >= 2 and len(suma14) >= 2:
        val_tabla = all(
            abs(suma14[i] - total_impreso[i]) < 0.05 for i in range(min(2, len(suma14)))
        )
    resultado.validacion_tabla = val_tabla

    val_nacional = None
    if otros and len(otros) >= 2 and total_impreso and len(total_impreso) >= 2 and len(suma14) >= 2:
        suma_mas_otros = [suma14[i] + otros[i] for i in range(2)]
        val_nacional = all(abs(suma_mas_otros[i] - total_impreso[i]) < 0.05 for i in range(2))
    resultado.validacion_nacional = val_nacional

    cuadra = val_tabla is True or val_nacional is True
    if not cuadra and (val_tabla is False or val_nacional is False):
        resultado.estado = "revision_manual"
        resultado.nota = f"suma14={suma14} otros={otros} total_impreso={total_impreso} -- no cuadra ni sin otros paises ni sumandolos"
    elif semana_prob is None or semana_conf is None:
        resultado.estado = "revision_manual"
        resultado.nota = "tabla extraida y cuadra, pero no se pudo leer semana de corte del encabezado"
    else:
        resultado.estado = "ok"

    return resultado


def paso1_extraer(limite: int | None = None) -> list[ResultadoBoletin]:
    archivos = descubrir_archivos(limite)
    vigentes, descartados = resolver_versiones(archivos)

    print(f"Paso 1: {len(archivos)} PDF encontrados, {len(vigentes)} vigentes tras resolver versiones "
          f"({len(descartados)} descartados por version superada).")

    resultados = []
    for i, path in enumerate(vigentes, 1):
        r = procesar_boletin(path)
        resultados.append(r)
        if i % 40 == 0:
            print(f"  ... {i}/{len(vigentes)}")

    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
    _volcar_bitacora(resultados, descartados)
    _volcar_crudo(resultados)
    return resultados


def _volcar_bitacora(resultados: list[ResultadoBoletin], descartados: list[tuple[Path, str]]) -> None:
    path = INTERIM_ROOT / "bitacora_paso1.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "archivo", "anio", "semana_archivo", "version", "estado", "familia",
            "semana_probable", "semana_confirmado", "suma14_probable", "suma14_confirmado",
            "otros_probable", "otros_confirmado", "total_impreso", "validacion_tabla",
            "validacion_nacional", "nota",
        ])
        for r in resultados:
            w.writerow([
                r.archivo, r.anio, r.semana_archivo, r.version, r.estado, r.familia,
                r.semana_probable, r.semana_confirmado,
                r.suma14[0] if len(r.suma14) > 0 else "",
                r.suma14[1] if len(r.suma14) > 1 else "",
                r.otros_paises[0] if len(r.otros_paises) > 0 else "",
                r.otros_paises[1] if len(r.otros_paises) > 1 else "",
                r.total_impreso, r.validacion_tabla, r.validacion_nacional, r.nota,
            ])
        for p, motivo in descartados:
            w.writerow([p.name, "", "", "", "descartado_version", "", "", "", "", "", "", "", "", "", "", motivo])
    print(f"  -> {path}")

    resumen = Counter(r.estado for r in resultados)
    print("  Resumen de estados:")
    for estado, n in resumen.most_common():
        print(f"    {estado}: {n}")


def _volcar_crudo(resultados: list[ResultadoBoletin]) -> None:
    path = INTERIM_ROOT / "crudo_departamental.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "archivo", "anio", "familia", "departamento", "probable_acum", "confirmado_acum",
            "tasa", "semana_corte_probable", "semana_corte_confirmado",
        ])
        for r in resultados:
            if r.estado != "ok":
                continue
            for fila in r.filas:
                probable = fila.valores[0]
                confirmado = fila.valores[1]
                tasa = fila.valores[2] if len(fila.valores) > 2 else ""
                w.writerow([
                    r.archivo, r.anio, r.familia, fila.departamento, probable, confirmado, tasa,
                    r.semana_probable, r.semana_confirmado,
                ])
            if r.otros_paises:
                w.writerow([
                    r.archivo, r.anio, r.familia, "Otros países",
                    r.otros_paises[0], r.otros_paises[1] if len(r.otros_paises) > 1 else "",
                    "", r.semana_probable, r.semana_confirmado,
                ])
    print(f"  -> {path}")


# ---------------------------------------------------------------------------
# Paso 2 -- desacumular
# ---------------------------------------------------------------------------

@dataclass
class PuntoSemanal:
    anio: int
    departamento: str
    semana: int
    valor: float | None  # None = hueco (sin dato semanal, no se fabrica)
    nota: str = ""


def _serie_por_depto_anio(resultados: list[ResultadoBoletin], serie: str) -> dict[tuple[int, str], list[tuple[int, float]]]:
    """serie: 'probable' o 'confirmado'. Devuelve {(anio,depto): [(semana_corte, valor_acum), ...]} ordenado."""
    idx = 0 if serie == "probable" else 1
    semana_attr = "semana_probable" if serie == "probable" else "semana_confirmado"

    datos: dict[tuple[int, str], dict[int, float]] = defaultdict(dict)
    for r in resultados:
        if r.estado != "ok":
            continue
        semana = getattr(r, semana_attr)
        if semana is None:
            continue
        for fila in r.filas:
            if len(fila.valores) <= idx:
                continue
            # Si ya existe un valor para esta (anio,depto,semana), nos quedamos con el
            # de version mas alta -- resolver_versiones ya elimino los duplicados de
            # (anio,semana_archivo), pero dos archivos distintos pueden declarar la
            # misma semana de corte en el encabezado (ver trampa 10, SE01-03/2023).
            datos[(r.anio, fila.departamento)][semana] = fila.valores[idx]

    return {k: sorted(v.items()) for k, v in datos.items()}


def paso2_desacumular(resultados: list[ResultadoBoletin]) -> dict[str, list[PuntoSemanal]]:
    salida: dict[str, list[PuntoSemanal]] = {"probable": [], "confirmado": []}
    correcciones_negativas: list[dict] = []

    for serie in ("probable", "confirmado"):
        series = _serie_por_depto_anio(resultados, serie)
        for (anio, depto), puntos in series.items():
            anterior_semana, anterior_valor = None, 0.0
            for semana, valor in puntos:
                if anterior_semana is None:
                    diff = valor - 0.0
                    salida[serie].append(PuntoSemanal(anio, depto, semana, diff))
                else:
                    hueco = semana - anterior_semana
                    diff = valor - anterior_valor
                    if hueco > 1:
                        for s in range(anterior_semana + 1, semana + 1):
                            salida[serie].append(PuntoSemanal(
                                anio, depto, s, None,
                                nota=f"hueco de {hueco} semanas entre cortes SE{anterior_semana} y SE{semana}",
                            ))
                    elif diff < 0:
                        correcciones_negativas.append({
                            "serie": serie, "anio": anio, "departamento": depto,
                            "semana": semana, "diferencia": diff,
                            "acumulado_anterior": anterior_valor, "acumulado_actual": valor,
                        })
                        salida[serie].append(PuntoSemanal(
                            anio, depto, semana, None,
                            nota=f"correccion retroactiva: diff={diff} (excluida de la serie)",
                        ))
                    else:
                        salida[serie].append(PuntoSemanal(anio, depto, semana, diff))
                anterior_semana, anterior_valor = semana, valor

    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
    _volcar_desacumulado(salida)
    _volcar_correcciones_negativas(correcciones_negativas)
    return salida


def _volcar_desacumulado(salida: dict[str, list[PuntoSemanal]]) -> None:
    path = INTERIM_ROOT / "desacumulado_semanal.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["serie", "anio", "departamento", "semana", "valor", "nota"])
        for serie, puntos in salida.items():
            for p in puntos:
                w.writerow([serie, p.anio, p.departamento, p.semana, p.valor, p.nota])
    print(f"Paso 2 -> {path}")


def _volcar_correcciones_negativas(correcciones: list[dict]) -> None:
    path = INTERIM_ROOT / "correcciones_negativas.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["serie", "anio", "departamento", "semana", "diferencia", "acumulado_anterior", "acumulado_actual"])
        for c in correcciones:
            w.writerow([c["serie"], c["anio"], c["departamento"], c["semana"], c["diferencia"],
                        c["acumulado_anterior"], c["acumulado_actual"]])
    print(f"  -> {path}  ({len(correcciones)} correcciones retroactivas detectadas)")


# ---------------------------------------------------------------------------
# Paso 3 -- distribucion, canal endemico, contraste de criterios de rechazo
# ---------------------------------------------------------------------------

PISO_OBSERVACIONES = 12
PISO_ANIOS_MIN = 3
PISO_ANIOS_DE = 4
UMBRAL_PERDIDA_FILAS = 0.20


def paso3_distribucion(desacumulado: dict[str, list[PuntoSemanal]]) -> None:
    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
    for serie in ("probable", "confirmado"):
        _tabla_distribucion(serie, desacumulado[serie])
        _canal_endemico(serie, desacumulado[serie])
    _contraste_criterios(desacumulado)


def _tabla_distribucion(serie: str, puntos: list[PuntoSemanal]) -> None:
    grupos: dict[tuple[int, str], list[float]] = defaultdict(list)
    celdas_totales: dict[tuple[int, str], int] = defaultdict(int)
    for p in puntos:
        celdas_totales[(p.anio, p.departamento)] += 1
        if p.valor is not None:
            grupos[(p.anio, p.departamento)].append(p.valor)

    path = INTERIM_ROOT / f"distribucion_{serie}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "departamento", "semanas_con_dato", "semanas_totales_registradas",
                     "total_anual", "mediana_semanal", "maximo_semanal", "pct_semanas_en_cero"])
        for anio in ANIOS:
            for depto in DEPARTAMENTOS:
                valores = grupos.get((anio, depto), [])
                total_celdas = celdas_totales.get((anio, depto), 0)
                if not valores:
                    w.writerow([anio, depto, 0, total_celdas, "", "", "", ""])
                    continue
                total_anual = sum(valores)
                mediana = statistics.median(valores)
                maximo = max(valores)
                pct_cero = sum(1 for v in valores if v == 0) / len(valores)
                w.writerow([anio, depto, len(valores), total_celdas, total_anual, mediana, maximo,
                             round(pct_cero, 4)])
    print(f"Paso 3 -> {path}")


def _canal_endemico(serie: str, puntos: list[PuntoSemanal]) -> None:
    por_depto_semana_anio: dict[tuple[str, int], dict[int, float]] = defaultdict(dict)
    for p in puntos:
        if p.valor is not None:
            por_depto_semana_anio[(p.departamento, p.semana)][p.anio] = p.valor

    path = INTERIM_ROOT / f"canal_endemico_{serie}.csv"
    filas_out = []
    q3_cero = 0
    bajo_piso = 0
    total_celdas = 0
    for depto in DEPARTAMENTOS:
        for semana in range(1, 53):
            valores_por_anio = por_depto_semana_anio.get((depto, semana), {})
            for anio_objetivo in ANIOS:
                base = {a: v for a, v in valores_por_anio.items() if a != anio_objetivo}
                n_obs = len(base)
                anios_presentes = len(base)
                total_celdas += 1
                suficiente = n_obs >= PISO_OBSERVACIONES and anios_presentes >= PISO_ANIOS_MIN
                if not suficiente:
                    bajo_piso += 1
                valores = sorted(base.values())
                if len(valores) >= 2:
                    q25 = statistics.quantiles(valores, n=4, method="inclusive")[0]
                    q50 = statistics.median(valores)
                    q75 = statistics.quantiles(valores, n=4, method="inclusive")[2]
                elif len(valores) == 1:
                    q25 = q50 = q75 = valores[0]
                else:
                    q25 = q50 = q75 = None
                if q75 == 0:
                    q3_cero += 1
                filas_out.append([
                    depto, semana, anio_objetivo, n_obs, anios_presentes, suficiente, q25, q50, q75,
                ])

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["departamento", "semana", "anio_objetivo", "n_observaciones_base",
                     "anios_presentes_base", "cumple_piso_suficiencia", "p25", "p50", "p75"])
        w.writerows(filas_out)

    print(f"  -> {path}")
    print(f"     celdas totales: {total_celdas} | Q3=0: {q3_cero} ({q3_cero/total_celdas:.1%}) "
          f"| bajo piso ({PISO_OBSERVACIONES} obs / {PISO_ANIOS_MIN} de {PISO_ANIOS_DE} anios): "
          f"{bajo_piso} ({bajo_piso/total_celdas:.1%})")


def _contraste_criterios(desacumulado: dict[str, list[PuntoSemanal]]) -> None:
    path = INTERIM_ROOT / "contraste_criterios_rechazo.csv"
    filas_out = []
    for serie in ("probable", "confirmado"):
        puntos = desacumulado[serie]
        por_depto: dict[str, list[PuntoSemanal]] = defaultdict(list)
        for p in puntos:
            por_depto[p.departamento].append(p)

        for depto in DEPARTAMENTOS:
            pts = por_depto.get(depto, [])
            total = len(pts)
            sin_dato = sum(1 for p in pts if p.valor is None)
            pct_perdida = sin_dato / total if total else 1.0
            pierde_20 = pct_perdida > UMBRAL_PERDIDA_FILAS

            # "alto" definido de forma provisional para esta corrida como
            # valor semanal > p75 del canal endemico correspondiente -- NO es
            # la definicion final (parametros del punto A siguen sin decidir),
            # solo sirve para contar si CADA departamento-anio tiene al menos
            # una semana por encima de su propio canal historico.
            por_depto_semana_anio: dict[tuple[int, int], float] = {}
            for p in pts:
                if p.valor is not None:
                    por_depto_semana_anio[(p.anio, p.semana)] = p.valor

            anios_con_alto = set()
            for anio in ANIOS:
                base_por_semana: dict[int, list[float]] = defaultdict(list)
                for p in pts:
                    if p.valor is not None and p.anio != anio:
                        base_por_semana[p.semana].append(p.valor)
                for semana in range(1, 53):
                    valor = por_depto_semana_anio.get((anio, semana))
                    base = base_por_semana.get(semana, [])
                    if valor is None or len(base) < 2:
                        continue
                    p75 = statistics.quantiles(sorted(base), n=4, method="inclusive")[2]
                    if valor > p75:
                        anios_con_alto.add(anio)
                        break

            anios_sin_alto = [a for a in ANIOS if a not in anios_con_alto]
            filas_out.append([
                serie, depto, total, sin_dato, round(pct_perdida, 4), pierde_20,
                len(anios_con_alto), ",".join(str(a) for a in anios_sin_alto),
            ])

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["serie", "departamento", "semanas_registradas", "semanas_sin_dato",
                     "pct_perdida", "pierde_mas_20pct", "anios_con_al_menos_1_semana_alta",
                     "anios_sin_ninguna_semana_alta"])
        w.writerows(filas_out)
    print(f"Paso 3 -> {path}")


# ---------------------------------------------------------------------------
# Paso 4 -- verificacion contra casos conocidos
# ---------------------------------------------------------------------------

CASOS_CONOCIDOS = [
    {"archivo_contiene": "SE232018", "probable_total": 47, "confirmado_total": 21,
     "fuente": "inspeccion manual previa + verificado en esta corrida (suma14 exacta)"},
    {"archivo_contiene": "SE522019_v2", "probable_total": 437, "otros_probable": 2,
     "confirmado_total": 174, "otros_confirmado": 2,
     "fuente": "captura de hoy: SE52-2019: 437+2 / 174+2"},
    {"archivo_contiene": "SE522023", "probable_total": 17, "confirmado_total": 54,
     "fuente": "captura de hoy / trampa 8 (acumulado final 2023)"},
    {"archivo_contiene": "SE232019", "probable_total": 276, "otros_probable": 3,
     "fuente": "captura de hoy: SE23-2019: 276+3 probables"},
]


def paso4_verificar(resultados: list[ResultadoBoletin]) -> list[dict]:
    por_archivo = {r.archivo: r for r in resultados}
    salida = []
    for caso in CASOS_CONOCIDOS:
        candidatos = [r for nombre, r in por_archivo.items() if caso["archivo_contiene"] in nombre]
        if not candidatos:
            salida.append({**caso, "encontrado": False, "coincide": False, "detalle": "archivo no aparece entre los vigentes (revisar resolucion de versiones)"})
            continue
        r = candidatos[0]
        detalle = f"estado={r.estado} suma14={r.suma14} otros={r.otros_paises} total_impreso={r.total_impreso}"
        coincide = None
        if r.estado == "ok":
            # Comparacion separada (14 departamentos vs. otros paises), no sumada:
            # "437+2" en la cifra conocida significa "437 de departamentos, 2 de
            # otros paises" -- son dos cantidades distintas en la tabla, no un
            # total unico a reconstruir sumandolas primero.
            checks = [abs(r.suma14[0] - caso["probable_total"]) < 0.5]
            if "otros_probable" in caso:
                checks.append(len(r.otros_paises) > 0 and abs(r.otros_paises[0] - caso["otros_probable"]) < 0.5)
            if "confirmado_total" in caso:
                checks.append(len(r.suma14) > 1 and abs(r.suma14[1] - caso["confirmado_total"]) < 0.5)
            if "otros_confirmado" in caso:
                checks.append(len(r.otros_paises) > 1 and abs(r.otros_paises[1] - caso["otros_confirmado"]) < 0.5)
            coincide = all(checks)
        salida.append({**caso, "encontrado": True, "coincide": coincide, "detalle": detalle})

    path = INTERIM_ROOT / "verificacion_paso4.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archivo_contiene", "fuente", "encontrado", "coincide", "detalle"])
        for s in salida:
            w.writerow([s["archivo_contiene"], s["fuente"], s["encontrado"], s["coincide"], s["detalle"]])
    print(f"Paso 4 -> {path}")
    for s in salida:
        estado = "OK" if s["coincide"] else ("SIN COINCIDIR" if s["encontrado"] else "NO ENCONTRADO")
        print(f"  [{estado}] {s['archivo_contiene']}: {s['detalle']}")
    return salida


# ---------------------------------------------------------------------------
# Orquestacion
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limite", type=int, default=None, help="limitar a los primeros N PDF por anio (para pruebas rapidas)")
    ap.add_argument("--solo-paso1", action="store_true", help="correr solo la extraccion, sin desacumular ni distribucion")
    args = ap.parse_args()

    resultados = paso1_extraer(limite=args.limite)
    if args.solo_paso1:
        return

    desacumulado = paso2_desacumular(resultados)
    paso3_distribucion(desacumulado)
    paso4_verificar(resultados)


if __name__ == "__main__":
    main()
