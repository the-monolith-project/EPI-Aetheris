"""
Corrida exploratoria de Infeccion Respiratoria Aguda (IRA) departamental
(boletines MINSAL, 2018-2023 sin 2020).

Explora la tabla departamental de IRA que los mismos boletines PDF ya usados
para dengue publican semana a semana (junto con neumonias, EDAS, zika/chik).
Es dato real, publico, ya descargado -- nada se fabrica.

NO escribe a PostgreSQL -- es analisis exploratorio, no ingesta (mismo patron
que corrida_distribucion.py, el parser exploratorio validado de dengue). Toda
salida va a data/interim/corrida_ira/ (gitignoreada). La decision de esquema
que haria falta para ingerir IRA de verdad (la tabla IRA no trae split
probable/confirmado y el CHECK de casos_epidemiologicos.clasificacion solo
admite 'probable'/'confirmado'/'total') es del coordinador via ADR, no de este
script -- ver docs/adr/ (borrador propuesto) y docs/exploracion-ira-boletines-minsal.md.

Hallazgos de formato que este parser incorpora (evidencia: ver el informe):

- La tabla departamental de IRA es UN solo conteo por departamento
  (Total + Tasa x 100 mil), sin split probable/confirmado. El encabezado
  "Probable/Confirmado" de la tabla NACIONAL por grupo de edad (2023) es un
  error de plantilla de MINSAL: su segunda columna es la tasa x100mil (el
  "Total" de esa columna es 485 en SE01/2023 = la tasa nacional publicada,
  imposible como suma de casos).
- Es acumulado desde SE1 (misma trampa 8 que dengue): se desacumula por
  diferencia entre cortes consecutivos, huecos quedan como sin-dato (nunca
  se interpola) y diffs negativos se excluyen (nunca se clampean a cero).
- Dos familias de layout: 2018-2022 tabla lado-a-lado con la de grupos de
  edad (el texto extraido intercala filas de ambas); 2023 tabla departamental
  en pagina propia. En SE01-SE0x/2023 esa pagina no trae titulo propio y su
  encabezado de columna dice "Grupo de edad" aunque las filas son
  departamentos (otro error de plantilla de MINSAL).
- La narrativa sobre la tabla repite texto de la semana ANTERIOR (SE03/2018
  dice "SE 2-2018" en la narrativa y "SE-03 de 2018" en el titulo de la
  tabla) e incluye numeros pegados a nombres de departamento
  ("...Chalatenango 1,377, San Salvador 1,005..."): la semana de corte se lee
  SOLO del titulo de la tabla (o del pie de estratificacion) y las filas se
  buscan SOLO dentro del bloque que empieza en ese titulo.
- El separador de miles NO es consistente: coma en 2018-2022 y SE01/2023
  ("33,360"), punto en SE52/2023 ("1.574.872"); la tasa a veces sale sin
  separador ("19460"). Se parsea por heuristica de grupos de 3 digitos.
- Algunos boletines tienen la tabla IRA renderizada como imagen (titulo
  presente, cero filas extraibles): se registran como sospecha de imagen,
  nunca se rellenan.
- "Otros paises" existe como fila en 2021-2023 pero (en lo observado) sin
  valores; si algun boletin trajera valores, la reconciliacion prueba ambas
  convenciones (incluido/excluido del total), como en dengue.

Uso:
    python3 corrida_ira.py                  # corrida completa (extraer + desacumular + verificar)
    python3 corrida_ira.py --solo-paso1     # solo extraccion
    python3 corrida_ira.py --limite 10      # solo los primeros N PDF por anio
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).parent
RAW_ROOT = RAIZ / "data" / "raw" / "minsal"
INTERIM_ROOT = RAIZ / "data" / "interim" / "corrida_ira"
ANIOS = [2018, 2019, 2021, 2022, 2023]

# Duplicado deliberado de corrida_distribucion.py (no hay paquete compartido
# entre scripts exploratorios; misma convencion que el percentil duplicado
# entre backend/api e ingestion): lista canonica de departamentos y patrones
# tolerantes a variantes con/sin tilde vistas en los PDF (2018 imprime
# "Usulutan"/"Morazan" sin tilde; 2019+ con tilde).
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

RE_ANIO_DIR = re.compile(r"^(2018|2019|2021|2022|2023)$")
RE_SEMANA_ARCHIVO = re.compile(r"SE(\d{1,2})(?:-(\d{1,2}))?", re.IGNORECASE)
RE_VERSION = re.compile(r"_v(\d+)", re.IGNORECASE)
RE_MARCADORES_VACACION = re.compile(
    r"vacaciones|vigilancia\s+intensificada|semana\s+santa|fiestas\s+agostinas|fin\s+de\s+a[ñn]o",
    re.IGNORECASE,
)

# Numero con separador de miles opcional (coma O punto -- inconsistente en el
# corpus, hallazgo 3 del brief) o decimal corto. "19460" (sin separador)
# tambien es valido, igual que el malformado "1363,652" (MINSAL pierde la
# primera coma de millares en SE38/43/49-2018 y SE44-2022: son 1,363,652 etc.,
# verificado contra la suma de los 14 departamentos del mismo boletin).
_NUM = r"\d+(?:[.,]\d{3})+|\d+(?:[.,]\d{1,2})?"

# Marcador de pagina IRA. "aguda(s)" sin "grave" -- IRAG (infeccion
# respiratoria aguda GRAVE) es otro evento con su propio corredor endemico.
RE_MARCA_IRA = re.compile(r"\bIRAS?\b|[Rr]espiratorias?\s+[Aa]gudas?|Infecci[oó]n\s+[Rr]espiratoria")
RE_OTRA_ENFERMEDAD = re.compile(r"dengue|zika|chikungun|neumon[ií]a|diarreica|rotavirus|IRAG|aguda\s+grave", re.IGNORECASE)

# Titulo de la tabla (autoridad para la semana de corte -- la narrativa de la
# pagina repite la semana anterior, hallazgo empirico SE03/2018):
#   2018:  "Casos y Tasas por grupo de edad y Departamento de IRAS, SE-02 de 2018"
#   2019:  "Casos y tasas por grupo de edad y departamento de IRAS, El Salvador, SE-52- 2019"
#   2021+: "Casos y tasas por grupo de edad y departamento de IRAS, El Salvador, SE1 2021"
#          (SE52/2021 declara rango "SE01-52 2021": el corte es el SEGUNDO numero)
#   2023:  "Casos y tasas por departamento de IRA, El Salvador, SE 52 2023"
#   2019 (SE43): "Casos y tasas de IRA por grupo de edad y departamento, SE-43 de 2019"
#          (variante con "de IRA" antes de "por" -- mismo contenido, otro orden)
RE_TITULO_TABLA = re.compile(
    r"(?:Casos\s+y\s+[Tt]asas\s+por\s+(?:grupo\s+de\s+edad\s+y\s+)?[Dd]epartamento\s+de\s+IRAS?\b"
    r"|Casos\s+y\s+[Tt]asas\s+de\s+IRAS?\s+por\s+grupo\s+de\s+edad\s+y\s+departamento\b)"
    r".{0,60}?SE\s*-?\s*(\d{1,2})(?:\s*-\s*(\d{1,2})\b(?!\d))?[\s,.-]*(?:de\s+)?(\d{4})",
    re.DOTALL,
)
# Encabezado de columnas de la(s) tabla(s) -- inicio de bloque cuando la
# pagina no trae titulo (SE39/2018 va directo de la narrativa a la tabla;
# la pagina propia de 2023 temprana no tiene titulo). "Grupo de edad" incluido
# porque en 2023 temprana MINSAL rotula asi la tabla DEPARTAMENTAL (error de
# plantilla, las filas son departamentos).
RE_ENCABEZADO_COLUMNAS = re.compile(
    r"(?:Departamentos?|Grupos?\s+de\s+[Ee]dad)\s+Total(?:\s+general)?\s+Tasa"
)
# Titulo de seccion ("Infeccion respiratoria aguda, El Salvador, SE 39-2018"):
# ULTIMO recurso para la semana de corte -- en 2018 este texto repite a veces
# la semana ANTERIOR (SE03/2018 dice "SE 2-2018"), por eso solo se usa si no
# hay titulo de tabla ni pie de estratificacion, y el resultado se contrasta
# contra la semana del nombre de archivo.
RE_TITULO_SECCION = re.compile(
    r"[Ii]nfecci[oó]n(?:es)?\s+respiratorias?\s+agudas?(?:\s*\(IRA\))?[\s,]+El\s+Salvador[\s,]+"
    r"SE\s*-?\s*0?(\d{1,2})(?:\s*-\s*(\d{1,2})\b(?!\d))?[\s,.-]*(?:de\s+)?(\d{4})",
    re.DOTALL,
)
# Pie de la seccion de estratificacion, en la MISMA pagina que la tabla
# departamental de 2023 temprana (que no trae titulo propio):
#   "... de infecciones respiratorias agudas, El Salvador SE 1, 2023."
RE_PIE_ESTRATIFICACION = re.compile(
    r"infecciones\s+respiratorias\s+agudas.{0,40}?SE\s*(\d{1,2})(?:\s*-\s*(\d{1,2})\b(?!\d))?[\s,.-]*(\d{4})",
    re.DOTALL,
)

MARCADORES_FIN_BLOQUE = [
    "Estratificación", "Estratificacion",
    "Ministerio de Salud / Dirección",
    "Ministerio de Salud / Direccion",
]


def parsear_numero(token: str) -> float:
    """Heuristica de separadores (hallazgo 3 del brief: coma y punto conviven
    como separador de miles en el mismo corpus): grupos de exactamente 3
    digitos tras el separador = miles ("33,360", "1.574.872" -> 33360,
    1574872); un solo separador con 1-2 decimales = decimal ("3.4" -> 3.4)."""
    token = token.strip()
    # \d+ (no \d{1,3}) a proposito: acepta el malformado "1363,652" (millares
    # con la primera coma perdida, ver _NUM). La ambiguedad con un decimal de
    # 3 cifras no aplica a este corpus: los conteos son enteros y las tasas
    # decimales observadas traen 1-2 decimales.
    if re.fullmatch(r"\d+(?:[.,]\d{3})+", token):
        return float(re.sub(r"[.,]", "", token))
    return float(token.replace(",", "."))


@dataclass
class FilaIRA:
    departamento: str
    total_acum: float
    tasa: float | None


@dataclass
class ResultadoIRA:
    archivo: str
    anio: int
    semana_archivo: str | None
    version: int
    estado: str
    nota: str = ""
    layout: str | None = None          # "lado_a_lado" (2018-2022) | "pagina_propia" (2023)
    semana_corte: int | None = None    # leida del titulo de la tabla, nunca de la narrativa
    fuente_semana: str | None = None   # titulo_tabla | pie_estratificacion | titulo_seccion
    anio_titulo: int | None = None     # solo para auditar; el anio vigente sale del nombre/carpeta
    pagina: int | None = None
    filas: list[FilaIRA] = field(default_factory=list)
    otros_paises: list[float] = field(default_factory=list)
    totales_bloque: list[float] = field(default_factory=list)
    total_impreso: float | None = None  # el total contra el que cuadro (o el mas cercano)
    suma14: float | None = None
    validacion_cuadra: bool | None = None
    diff_total: float | None = None     # suma14 - total mas cercano


# ---------------------------------------------------------------------------
# Paso 0 -- descubrimiento y resolucion de versiones (mismo patron que dengue)
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
    """El anio sale SIEMPRE de la carpeta (trampa 1 de dengue, vigente tambien
    en IRA: la pagina de estratificacion de SE01/2022 dice '2021' en su
    titulo). La semana del nombre es solo referencia -- el corte real se lee
    del titulo de la tabla."""
    anio = int(path.parent.name)
    m = RE_SEMANA_ARCHIVO.search(path.stem)
    if m:
        semana = m.group(1) if not m.group(2) else f"{int(m.group(1))}-{int(m.group(2))}"
    else:
        semana = None
    v = RE_VERSION.search(path.stem)
    return anio, semana, int(v.group(1)) if v else 1


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
# Paso 1 -- localizar y extraer la tabla departamental de IRA
# ---------------------------------------------------------------------------

def _extraer_semana_titulo(texto: str) -> tuple[int | None, int | None, str | None]:
    """Semana de corte y anio impresos, leidos del titulo de la tabla, del
    pie de estratificacion o del titulo de seccion (en ese orden de
    confianza). Si el titulo declara un rango ("SE01-52 2021"), el corte del
    acumulador es el segundo numero. Devuelve tambien la fuente usada."""
    for regex, fuente in ((RE_TITULO_TABLA, "titulo_tabla"),
                          (RE_PIE_ESTRATIFICACION, "pie_estratificacion"),
                          (RE_TITULO_SECCION, "titulo_seccion")):
        m = regex.search(texto)
        if m:
            semana = int(m.group(2)) if m.group(2) else int(m.group(1))
            return semana, int(m.group(3)), fuente
    return None, None, None


def _recortar_bloque(texto: str) -> str:
    """El bloque de tabla empieza en el titulo de la tabla o, si la pagina no
    lo trae (SE39/2018; pagina propia de 2023 temprana), en el encabezado de
    columnas. Nunca antes: la narrativa previa contiene numeros pegados a
    nombres de departamento ("...Chalatenango 1,377, San Salvador 1,005...")
    que contaminarian la captura."""
    m = RE_TITULO_TABLA.search(texto)
    if m:
        inicio = m.end()
    else:
        m2 = RE_ENCABEZADO_COLUMNAS.search(texto)
        inicio = m2.start() if m2 else 0
    fin = len(texto)
    for marcador in MARCADORES_FIN_BLOQUE:
        idx = texto.find(marcador, inicio)
        if idx != -1:
            fin = min(fin, idx)
    return texto[inicio:fin]


def _extraer_filas(bloque: str) -> tuple[list[FilaIRA], list[float]]:
    """Filas departamentales dentro del bloque. En el layout lado-a-lado el
    texto intercala filas de la tabla de grupos de edad ("<1 año 4,905 4,407
    San Salvador 17,958 1,005") -- anclar en el nombre del departamento y
    capturar los numeros que lo SIGUEN en la misma linea es inmune a eso.
    Se capturan a lo sumo 2 numeros (Total, Tasa): un tercer numero contiguo
    seria ruido de la tabla vecina, nunca una columna real de esta tabla."""
    _esp = r"[^\S\n]+"
    filas = []
    for nombre, patron in _PATRON_NOMBRE.items():
        regex = re.compile(rf"{patron}{_esp}({_NUM})(?:{_esp}({_NUM}))?")
        m = regex.search(bloque)
        if m:
            total = parsear_numero(m.group(1))
            tasa = parsear_numero(m.group(2)) if m.group(2) else None
            filas.append(FilaIRA(nombre, total, tasa))
    regex_otros = re.compile(rf"{_PATRON_OTROS}(?:{_esp}({_NUM}))?(?:{_esp}({_NUM}))?")
    m_otros = regex_otros.search(bloque)
    otros = [parsear_numero(g) for g in (m_otros.groups() if m_otros else []) if g]
    return filas, otros


def _extraer_totales(bloque: str) -> list[tuple[float, float | None]]:
    """TODAS las lineas de total del bloque. En el layout lado-a-lado hay dos
    ("Total general" de la tabla de edad y de la departamental) y NO siempre
    coinciden: en SE49/2021 difieren en 10 y en SE10/2018 en 43,238 (tabla
    departamental reimpresa de la semana anterior). Validar contra "el
    primero" seria validar contra la tabla equivocada."""
    _esp = r"[^\S\n]+"
    totales = []
    for m in re.finditer(rf"Total(?:{_esp}general)?{_esp}({_NUM})(?:{_esp}({_NUM}))?", bloque):
        total = parsear_numero(m.group(1))
        tasa = parsear_numero(m.group(2)) if m.group(2) else None
        totales.append((total, tasa))
    return totales


def analizar_texto_pagina(texto_pagina: str, resultado: ResultadoIRA) -> ResultadoIRA:
    """Analisis de la pagina que contiene la tabla departamental de IRA.
    Opera sobre TEXTO ya extraido -- separado de procesar_boletin (que solo
    agrega la I/O de pdfplumber) para poder probarse contra extractos reales
    guardados como fixture, sin versionar PDFs (misma convencion que
    corrida_distribucion.analizar_texto_pagina)."""
    m_titulo = RE_TITULO_TABLA.search(texto_pagina)
    resultado.layout = (
        "pagina_propia" if (m_titulo and "grupo de edad" not in m_titulo.group(0).lower()) or not m_titulo
        else "lado_a_lado"
    )
    semana, anio_titulo, fuente_semana = _extraer_semana_titulo(texto_pagina)
    resultado.semana_corte = semana
    resultado.anio_titulo = anio_titulo
    resultado.fuente_semana = fuente_semana

    bloque = _recortar_bloque(texto_pagina)
    filas, otros = _extraer_filas(bloque)
    resultado.filas = filas
    resultado.otros_paises = otros

    if len(filas) < 14:
        if len(filas) == 0:
            resultado.estado = "sin_filas_sospecha_imagen"
            resultado.nota = ("pagina IRA localizada (titulo presente) pero 0 filas departamentales "
                              "en el texto extraible -- sospecha de tabla renderizada como imagen")
        else:
            resultado.estado = "error_extraccion"
            resultado.nota = f"solo {len(filas)}/14 departamentos encontrados en el bloque"
        return resultado

    totales = _extraer_totales(bloque)
    resultado.totales_bloque = [t for t, _ in totales]
    suma14 = sum(f.total_acum for f in filas)
    resultado.suma14 = suma14

    # Validacion contra CUALQUIER total del bloque (la tabla de edad y la
    # departamental imprimen cada una el suyo y no siempre coinciden), con
    # ambas convenciones de "Otros paises" (incluido/excluido), como en
    # dengue -- en lo observado la fila viene siempre vacia y solo aplica la
    # primera. diff_total registra la distancia al total mas cercano.
    if totales:
        candidatos = [suma14] + ([suma14 + otros[0]] if otros else [])
        diffs = [(abs(c - t), c - t, t) for t, _ in totales for c in candidatos]
        diffs.sort()
        resultado.diff_total = diffs[0][1]
        resultado.total_impreso = diffs[0][2]
        resultado.validacion_cuadra = diffs[0][0] < 0.5

    if resultado.validacion_cuadra is False and abs(resultado.diff_total) <= 3:
        # Discrepancia minima del propio boletin: el total impreso difiere en
        # 1-3 de la suma real de sus 14 celdas (verificado a mano en
        # SE52/2023: las celdas impresas suman 1,574,871 y el total impreso
        # dice 1,574,872; el signo varia entre boletines). Frecuente en 2023
        # (25/49 boletines). Se conservan las celdas departamentales -- el
        # total es solo un checksum de MINSAL -- pero queda registrado.
        resultado.estado = "ok_discrepancia_minima"
        resultado.nota = (f"total impreso difiere de la suma de celdas en {resultado.diff_total:+.0f} "
                          "(inconsistencia interna del boletin, celdas conservadas)")
    elif resultado.validacion_cuadra is False:
        resultado.estado = "revision_manual"
        resultado.nota = (f"suma14={suma14:.0f} otros={otros} totales_bloque={resultado.totales_bloque} "
                          "-- no cuadra con ningun total impreso (ni sumando otros paises)")
        return resultado
    elif semana is None:
        resultado.estado = "revision_manual"
        resultado.nota = "tabla extraida pero no se pudo leer la semana de corte del titulo/pie/seccion"
        return resultado
    else:
        resultado.estado = "ok"

    # Contraste semana-titulo vs nombre de archivo (solo semanas simples):
    # el titulo de seccion en 2018 a veces repite la semana anterior, y una
    # tabla reimpresa puede declarar una semana que no corresponde.
    if (semana is not None and resultado.semana_archivo is not None
            and "-" not in str(resultado.semana_archivo)
            and semana != int(resultado.semana_archivo)):
        resultado.estado = "revision_manual"
        resultado.nota = (f"semana del {fuente_semana} (SE{semana}) difiere de la del nombre de "
                          f"archivo (SE{resultado.semana_archivo})" +
                          (f"; {resultado.nota}" if resultado.nota else ""))
    return resultado


def procesar_boletin(path: Path) -> ResultadoIRA:
    import pdfplumber  # import local: los tests corren sobre fixtures sin pdfplumber

    anio, semana_archivo, version = parsear_nombre(path)
    resultado = ResultadoIRA(
        archivo=path.name, anio=anio, semana_archivo=semana_archivo,
        version=version, estado="pendiente",
    )
    try:
        with pdfplumber.open(path) as pdf:
            paginas = [(i, p.extract_text() or "") for i, p in enumerate(pdf.pages)]
    except Exception as exc:  # noqa: BLE001 -- diagnostico exploratorio, no ingesta
        resultado.estado = "error_extraccion"
        resultado.nota = f"excepcion abriendo/leyendo PDF: {exc}"
        return resultado

    candidata = _localizar_pagina_ira(paginas)
    if candidata is None:
        texto_p0 = paginas[0][1] if paginas else ""
        if RE_MARCADORES_VACACION.search(texto_p0):
            resultado.estado = "ausencia_esperada_vacacion"
            resultado.nota = "sin pagina con tabla departamental de IRA; portada marca vacaciones/vigilancia intensificada"
        elif not any(RE_MARCA_IRA.search(t) for _, t in paginas):
            resultado.estado = "sin_texto_extraible"
            resultado.nota = "0 menciones de IRA en todo el documento -- sospecha de boletin escaneado/imagen"
        else:
            resultado.estado = "sin_tabla_ira"
            resultado.nota = "el documento menciona IRA pero ninguna pagina contiene la tabla departamental"
        return resultado

    i, texto = candidata
    resultado.pagina = i + 1
    return analizar_texto_pagina(texto, resultado)


def _localizar_pagina_ira(paginas: list[tuple[int, str]]) -> tuple[int, str] | None:
    """Pagina de la tabla departamental de IRA: debe tener marcador IRA y
    filas de departamento con numeros, y NO ser la tabla de otra enfermedad
    (dengue/zika/neumonias/EDAS tambien traen 14 departamentos). La pagina
    con titulo IRA pero 0 filas (tabla como imagen) tambien se devuelve, para
    clasificarla como sospecha de imagen en el analisis."""
    _esp = r"[^\S\n]+"
    mejor = None
    for i, texto in paginas:
        if not RE_MARCA_IRA.search(texto):
            continue
        con_titulo = bool(RE_TITULO_TABLA.search(texto) or RE_PIE_ESTRATIFICACION.search(texto))
        n_filas = sum(
            1 for patron in _PATRON_NOMBRE.values()
            if re.search(rf"{patron}{_esp}(?:{_NUM})", texto)
        )
        if n_filas >= 10 and RE_OTRA_ENFERMEDAD.search(texto) and not con_titulo:
            continue  # tabla departamental de otra enfermedad
        if n_filas >= 10 and (con_titulo or not RE_OTRA_ENFERMEDAD.search(texto)):
            # Sin titulo tambien vale si la pagina es inequivocamente de IRA
            # (SE39/2018 pasa de la narrativa directo al encabezado de
            # columnas, sin linea de titulo de tabla).
            return i, texto
        if con_titulo and mejor is None:
            mejor = (i, texto)  # titulo IRA sin filas: candidata a tabla-imagen
    return mejor


ESTADOS_USABLES = {"ok", "ok_discrepancia_minima"}


def detectar_reimpresiones(resultados: list[ResultadoIRA]) -> int:
    """Trampa confirmada en SE10/2018: la tabla departamental es una
    reimpresion EXACTA de la de SE09/2018 (los 14 valores identicos, San
    Salvador 119,670 en ambas) mientras la tabla de edad del mismo boletin ya
    trae datos de SE10. Ingerirla en su semana declarada fabricaria una
    semana de 0 casos seguida de una doble. Deteccion: 14 valores acumulados
    identicos al corte anterior del mismo anio es imposible como dato real
    (seria una semana nacional con 0 casos de IRA); se reclasifica el corte
    posterior a revision_manual. Devuelve cuantos reclasifico."""
    por_anio: dict[int, list[ResultadoIRA]] = defaultdict(list)
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
                actual.nota = (f"los 14 valores departamentales son identicos a los del corte "
                               f"SE{previo.semana_corte} ({previo.archivo}) -- tabla reimpresa/rezagada, "
                               "semana declarada no confiable")
                n += 1
    return n


# ---------------------------------------------------------------------------
# Paso 2 -- desacumular (mismas reglas que dengue, trampa 8)
# ---------------------------------------------------------------------------

@dataclass
class PuntoSemanal:
    anio: int
    departamento: str
    semana: int
    valor: float | None  # None = hueco o correccion negativa (no se fabrica)
    nota: str = ""


def desacumular(resultados: list[ResultadoIRA]) -> tuple[list[PuntoSemanal], list[dict]]:
    """Diferencia entre cortes consecutivos por (anio, departamento).
    Huecos entre cortes disponibles quedan como sin-dato (nunca se
    interpola); diffs negativos son correcciones retroactivas de MINSAL y se
    excluyen de la serie (nunca se clampean a cero). El primer corte de cada
    anio es acumulado desde SE1: si no es SE1, el punto abarca varias semanas
    y se marca en nota (no se divide -- dividir fabricaria datos)."""
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
                nota = "" if semana == 1 else f"primer corte del anio en SE{semana}: acumulado SE1-SE{semana}, no incidencia de una semana"
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
# Volcado a CSV (data/interim/, gitignoreado)
# ---------------------------------------------------------------------------

def volcar_bitacora(resultados: list[ResultadoIRA], descartados: list[tuple[Path, str]]) -> None:
    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
    path = INTERIM_ROOT / "bitacora_ira.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archivo", "anio", "semana_archivo", "version", "estado", "layout",
                    "pagina", "semana_corte", "fuente_semana", "anio_titulo", "suma14",
                    "otros_paises", "total_impreso", "diff_total", "validacion_cuadra", "nota"])
        for r in resultados:
            w.writerow([r.archivo, r.anio, r.semana_archivo, r.version, r.estado, r.layout,
                        r.pagina, r.semana_corte, r.fuente_semana, r.anio_titulo,
                        f"{r.suma14:.0f}" if r.suma14 is not None else "",
                        r.otros_paises,
                        f"{r.total_impreso:.0f}" if r.total_impreso is not None else "",
                        f"{r.diff_total:+.0f}" if r.diff_total is not None else "",
                        r.validacion_cuadra, r.nota])
        for p, motivo in descartados:
            w.writerow([p.name, "", "", "", "descartado_version", "", "", "", "", "", "", "", "", "", motivo])
    print(f"  -> {path}")
    resumen = Counter(r.estado for r in resultados)
    print("  Resumen de estados:")
    for estado, n in resumen.most_common():
        print(f"    {estado}: {n}")


def volcar_crudo(resultados: list[ResultadoIRA]) -> None:
    path = INTERIM_ROOT / "crudo_ira_departamental.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["archivo", "anio", "estado", "semana_corte", "departamento", "total_acum", "tasa"])
        for r in resultados:
            if r.estado not in ESTADOS_USABLES:
                continue
            for fila in r.filas:
                w.writerow([r.archivo, r.anio, r.estado, r.semana_corte, fila.departamento,
                            f"{fila.total_acum:.0f}", fila.tasa])
    print(f"  -> {path}")


def volcar_desacumulado(puntos: list[PuntoSemanal], negativas: list[dict]) -> None:
    path = INTERIM_ROOT / "desacumulado_ira_semanal.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "departamento", "semana", "valor", "nota"])
        for p in sorted(puntos, key=lambda x: (x.anio, x.departamento, x.semana)):
            w.writerow([p.anio, p.departamento, p.semana,
                        f"{p.valor:.0f}" if p.valor is not None else "", p.nota])
    print(f"  -> {path}")
    path2 = INTERIM_ROOT / "correcciones_negativas_ira.csv"
    with open(path2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "departamento", "semana", "diferencia", "acumulado_anterior", "acumulado_actual"])
        for c in negativas:
            w.writerow([c["anio"], c["departamento"], c["semana"], f"{c['diferencia']:.0f}",
                        f"{c['acumulado_anterior']:.0f}", f"{c['acumulado_actual']:.0f}"])
    print(f"  -> {path2}  ({len(negativas)} correcciones retroactivas detectadas)")


# ---------------------------------------------------------------------------
# Verificacion de acumulacion + casos conocidos
# ---------------------------------------------------------------------------

def verificar_monotonia(resultados: list[ResultadoIRA]) -> None:
    """Confirmacion empirica (no supuesta) de que la serie es acumulada desde
    SE1 en TODO el corpus disponible: por (anio, departamento), los cortes
    consecutivos deben ser no-decrecientes salvo correcciones retroactivas
    puntuales. Se reporta el conteo de pares crecientes/iguales/decrecientes."""
    series: dict[tuple[int, str], dict[int, float]] = defaultdict(dict)
    for r in resultados:
        if r.estado in ESTADOS_USABLES and r.semana_corte is not None:
            for fila in r.filas:
                series[(r.anio, fila.departamento)][r.semana_corte] = fila.total_acum
    crece = igual = decrece = 0
    for por_semana in series.values():
        valores = [v for _, v in sorted(por_semana.items())]
        for a, b in zip(valores, valores[1:]):
            if b > a:
                crece += 1
            elif b == a:
                igual += 1
            else:
                decrece += 1
    total = crece + igual + decrece
    print(f"Monotonia (evidencia de acumulacion): {total} pares consecutivos -- "
          f"{crece} crecientes, {igual} iguales, {decrece} decrecientes "
          f"({decrece / total:.2%} de correcciones retroactivas)" if total else "sin pares")


# Cifras leidas a mano de los PDF (evidencia directa, ver informe) -- ninguna inventada.
CASOS_CONOCIDOS = [
    {"archivo_contiene": "SE012023", "san_salvador": 11295, "total": 33360, "semana": 1,
     "fuente": "brief del coordinador + inspeccion pdfplumber pagina 14"},
    {"archivo_contiene": "SE522023", "san_salvador": 615619, "total": 1574872, "semana": 52,
     "fuente": "brief del coordinador + inspeccion pdfplumber pagina 13 (separador punto)"},
    {"archivo_contiene": "SE522019_v2", "san_salvador": 700913, "total": 1951867, "semana": 52,
     "fuente": "inspeccion pdfplumber pagina 11"},
    {"archivo_contiene": "SE01-02-2018", "chalatenango": 2823, "total": 54543, "semana": 2,
     "fuente": "inspeccion pdfplumber pagina 15 -- la narrativa previa trae 'Chalatenango 1,377' (tasa) que NO debe capturarse"},
    {"archivo_contiene": "SE032018", "total": 88099, "semana": 3,
     "fuente": "inspeccion pdfplumber pagina 21 -- narrativa repite 'SE 2-2018', el titulo de la tabla dice SE-03"},
]


def verificar_casos(resultados: list[ResultadoIRA]) -> None:
    por_archivo = {r.archivo: r for r in resultados}
    print("Verificacion contra casos conocidos:")
    for caso in CASOS_CONOCIDOS:
        r = next((v for k, v in por_archivo.items() if caso["archivo_contiene"] in k), None)
        if r is None:
            print(f"  [NO ENCONTRADO] {caso['archivo_contiene']}")
            continue
        checks = []
        if r.estado in ESTADOS_USABLES:
            if "san_salvador" in caso:
                fila = next(f for f in r.filas if f.departamento == "San Salvador")
                checks.append(("San Salvador", fila.total_acum == caso["san_salvador"]))
            if "chalatenango" in caso:
                fila = next(f for f in r.filas if f.departamento == "Chalatenango")
                checks.append(("Chalatenango", fila.total_acum == caso["chalatenango"]))
            checks.append(("total", r.total_impreso == caso["total"]))
            checks.append(("semana", r.semana_corte == caso["semana"]))
        ok = r.estado in ESTADOS_USABLES and all(c[1] for c in checks)
        detalle = " ".join(f"{n}={'OK' if v else 'X'}" for n, v in checks)
        print(f"  [{'OK' if ok else 'FALLA'}] {caso['archivo_contiene']}: estado={r.estado} {detalle}")


# ---------------------------------------------------------------------------
# Orquestacion
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limite", type=int, default=None)
    ap.add_argument("--solo-paso1", action="store_true")
    args = ap.parse_args()

    archivos = descubrir_archivos(args.limite)
    vigentes, descartados = resolver_versiones(archivos)
    print(f"Paso 1: {len(archivos)} PDF encontrados, {len(vigentes)} vigentes "
          f"({len(descartados)} descartados por version superada).")

    resultados = []
    for i, path in enumerate(vigentes, 1):
        resultados.append(procesar_boletin(path))
        if i % 40 == 0:
            print(f"  ... {i}/{len(vigentes)}")

    # Reclasificar reimpresiones ANTES de volcar, para que la bitacora y el
    # crudo reflejen el estado final (SE10/2018 y SE34/2019 en este corpus).
    n_reimpresas = detectar_reimpresiones(resultados)
    if n_reimpresas:
        print(f"Reimpresiones detectadas y reclasificadas a revision_manual: {n_reimpresas}")
    volcar_bitacora(resultados, descartados)
    volcar_crudo(resultados)
    if args.solo_paso1:
        return

    verificar_monotonia(resultados)
    puntos, negativas = desacumular(resultados)
    volcar_desacumulado(puntos, negativas)
    verificar_casos(resultados)


if __name__ == "__main__":
    main()
