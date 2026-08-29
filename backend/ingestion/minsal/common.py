"""
Utilidades compartidas para los scripts descargar_{anio}.py de este paquete.

Descarga boletines epidemiologicos del MINSAL (salud.gob.sv) en PDF.
Ver Instrucciones_Claude_Code_Descarga_MINSAL.md para el detalle del
mecanismo (ruta directa / ruta de respaldo, validacion %PDF, etc).

No tocar boletin.salud.gob.sv (dashboard 2024+) bajo ninguna circunstancia.
"""

from __future__ import annotations

import re
import time
import unicodedata
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}

INDEX_URL_TEMPLATE = "https://www.salud.gob.sv/boletines-epidemiologicos-{anio}/"

# Ruta directa: URLs de PDF embebidas crudas en el HTML del indice.
DIRECT_PDF_RE = re.compile(
    r"https://www\.salud\.gob\.sv/wp-content/uploads/download-manager-files/"
    r"[^\"'()\s]*\.pdf",
    re.IGNORECASE,
)

# Ruta de respaldo: enlaces data-downloadurl de <a class="wpdm-download-link">,
# que resuelven al PDF real via redirect al seguir la URL con wpdmdl=.
BACKUP_LINK_RE = re.compile(r'data-downloadurl="([^"]*wpdmdl=\d+[^"]*)"')

DATA_ROOT = Path(__file__).parent.parent / "data" / "raw" / "minsal"

REQUEST_PAUSE_SECONDS = 1.5
PDF_SIGNATURE = b"%PDF"


@dataclass
class DownloadResult:
    filename: str
    ok: bool
    reason: str = ""
    skipped_existing: bool = False


@dataclass
class YearSummary:
    anio: int
    ruta_usada: str
    total_indice: int
    resultados: list = field(default_factory=list)

    @property
    def total_exitoso(self) -> int:
        return sum(1 for r in self.resultados if r.ok)

    @property
    def total_fallido(self) -> int:
        return sum(1 for r in self.resultados if not r.ok)

    def imprimir(self) -> None:
        print(f"\n{'=' * 60}")
        print(f"RESUMEN {self.anio}")
        print(f"{'=' * 60}")
        print(f"Ruta usada:            {self.ruta_usada}")
        print(f"Total en el indice:    {self.total_indice}")
        print(f"Total descargado OK:   {self.total_exitoso}")
        print(f"Total fallido:         {self.total_fallido}")
        if self.total_fallido:
            print("Fallos:")
            for r in self.resultados:
                if not r.ok:
                    print(f"  - {r.filename}: {r.reason}")
        print(f"{'=' * 60}\n")


def _clean_filename(name: str) -> str:
    name = urllib.parse.unquote(name)
    name = unicodedata.normalize("NFC", name)
    return name.strip()


def extraer_urls_directas(html: str) -> list[str]:
    """Ruta directa: extrae URLs de PDF embebidas crudas en el HTML del indice."""
    urls = []
    vistos = set()
    for url in DIRECT_PDF_RE.findall(html):
        if url not in vistos:
            vistos.add(url)
            urls.append(url)
    return urls


def extraer_urls_respaldo(html: str) -> list[str]:
    """Ruta de respaldo: extrae los enlaces data-downloadurl (wpdmdl=ID)."""
    urls = []
    vistos = set()
    for url in BACKUP_LINK_RE.findall(html):
        url = url.replace("&amp;", "&")
        if url not in vistos:
            vistos.add(url)
            urls.append(url)
    return urls


def es_pdf_valido_en_disco(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with open(path, "rb") as f:
            return f.read(4) == PDF_SIGNATURE
    except OSError:
        return False


def _nombre_desde_url_directa(url: str) -> str:
    # Resolve URL path first, then fully decode URL entities (looping to unwind
    # multi-layer encoding like %252e%252e%252f), and FINALLY extract filename.
    # This prevents path traversal payloads from bypassing Path().name -- a
    # single unquote() pass left one residual encoding layer exploitable via
    # _clean_filename's own unquote() call, which had no basename re-extraction.
    path = urllib.parse.urlparse(url).path
    while True:
        unquoted = urllib.parse.unquote(path)
        if unquoted == path:
            break
        path = unquoted
    return Path(_clean_filename(Path(path).name)).name


def _descargar_bytes(session: requests.Session, url: str, timeout: int = 30) -> requests.Response:
    return session.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)


def descargar_pdf_ruta_directa(
    session: requests.Session, url: str, destino_dir: Path
) -> DownloadResult:
    filename = _nombre_desde_url_directa(url)
    destino = destino_dir / filename

    if es_pdf_valido_en_disco(destino):
        return DownloadResult(filename=filename, ok=True, skipped_existing=True)

    try:
        resp = _descargar_bytes(session, url)
    except requests.RequestException as exc:
        return DownloadResult(filename=filename, ok=False, reason=f"error de red: {exc}")

    if resp.status_code != 200:
        return DownloadResult(
            filename=filename, ok=False, reason=f"HTTP {resp.status_code}"
        )

    if not resp.content.startswith(PDF_SIGNATURE):
        return DownloadResult(
            filename=filename, ok=False, reason="firma %PDF invalida (no es un PDF real)"
        )

    destino_dir.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(resp.content)
    return DownloadResult(filename=filename, ok=True)


def descargar_pdf_ruta_respaldo(
    session: requests.Session, download_trigger_url: str, destino_dir: Path
) -> DownloadResult:
    """
    Sigue la URL data-downloadurl (?wpdmdl=ID) que redirige al PDF real,
    y usa el nombre de archivo resuelto tras el redirect como nombre final.
    """
    try:
        resp = _descargar_bytes(session, download_trigger_url)
    except requests.RequestException as exc:
        return DownloadResult(
            filename=download_trigger_url, ok=False, reason=f"error de red: {exc}"
        )

    filename = _nombre_desde_url_directa(resp.url) or f"wpdmdl_{int(time.time())}.pdf"
    destino = destino_dir / filename

    if es_pdf_valido_en_disco(destino):
        return DownloadResult(filename=filename, ok=True, skipped_existing=True)

    if resp.status_code != 200:
        return DownloadResult(
            filename=filename, ok=False, reason=f"HTTP {resp.status_code}"
        )

    if not resp.content.startswith(PDF_SIGNATURE):
        return DownloadResult(
            filename=filename, ok=False, reason="firma %PDF invalida (no es un PDF real)"
        )

    destino_dir.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(resp.content)
    return DownloadResult(filename=filename, ok=True)


def descargar_boletines_del_anio(anio: int) -> YearSummary:
    session = requests.Session()
    destino_dir = DATA_ROOT / str(anio)

    index_url = INDEX_URL_TEMPLATE.format(anio=anio)
    resp = session.get(index_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    urls_directas = extraer_urls_directas(html)

    if urls_directas:
        ruta_usada = "directa"
        resultados = []
        for url in urls_directas:
            resultados.append(descargar_pdf_ruta_directa(session, url, destino_dir))
            time.sleep(REQUEST_PAUSE_SECONDS)
        total_indice = len(urls_directas)
    else:
        ruta_usada = "respaldo"
        urls_respaldo = extraer_urls_respaldo(html)
        resultados = []
        for url in urls_respaldo:
            resultados.append(descargar_pdf_ruta_respaldo(session, url, destino_dir))
            time.sleep(REQUEST_PAUSE_SECONDS)
        total_indice = len(urls_respaldo)

    return YearSummary(
        anio=anio,
        ruta_usada=ruta_usada,
        total_indice=total_indice,
        resultados=resultados,
    )
