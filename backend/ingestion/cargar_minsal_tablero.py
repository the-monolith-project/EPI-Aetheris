"""
Carga a casos_epidemiologicos las series nacionales semanales del tablero de
vigilancia de MINSAL (boletin.salud.gob.sv), leidas de capturas HAR.

Las capturas las guarda una persona desde las herramientas de desarrollo del
navegador al abrir el tablero; este script solo lee esos archivos y nunca
hace peticiones al sitio (ADR 0021, backend/ingestion/minsal/common.py).
Cada respuesta de Superset trae la consulta SQL con el anio escrito
(`da.anio=2025`) y una fila por semana (`semana_mes` = "NN-Mes").

Se cargan cuatro series, con fuente minsal_tablero y region SV:
dengue sospechoso, dengue confirmado, IRA y neumonias. Si varias capturas
traen la misma semana, gana la mas reciente y se informan las diferencias
(MINSAL puede revisar semanas ya publicadas). No se rellenan huecos: la
semana 53 de 2025 no aparece en el tablero y queda sin dato.

Uso:
    python3 cargar_minsal_tablero.py [--dry-run] [captura.har ...]
    (sin rutas lee data/raw/minsal_tablero/*.har)
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).parent
DIR_CAPTURAS = RAIZ / "data" / "raw" / "minsal_tablero"

# diagnostico del tablero -> (tipos_evento.codigo, clasificacion)
SERIES = {
    "Casos Sospechosos de Dengue": ("dengue", "sospechoso"),
    "Casos confirmados de Dengue": ("dengue", "confirmado"),
    "Infección Respiratoria Aguda": ("ira", "notificado"),
    "Neumonías": ("neumonia", "notificado"),
}

_RE_ANIO = re.compile(r"\banio\s*=\s*(\d{4})\b")
_RE_SEMANA = re.compile(r"^(\d{1,2})-\w+$")
_RE_TABLERO = re.compile(r"/dashboard/(\d+)/")


@dataclass(frozen=True)
class Punto:
    evento: str
    clasificacion: str
    anio: int
    semana: int
    conteo: int
    capturado: str  # startedDateTime de la peticion (ISO 8601, UTC)
    archivo: str


def _normalizar(texto: str) -> str:
    # el tablero trae dobles espacios y espacios duros en algunos nombres
    return " ".join(texto.split())


def _diagnostico(form_data: dict) -> str | None:
    filtros = form_data.get("adhoc_filters") or []
    diagnosticos = [f for f in filtros if f.get("subject") == "diagnostico"]
    if len(diagnosticos) != 1:
        return None
    valor = diagnosticos[0].get("comparator")
    if isinstance(valor, list):
        if len(valor) != 1:
            return None
        valor = valor[0]
    return _normalizar(valor) if isinstance(valor, str) else None


def leer_captura(ruta: Path) -> list[Punto]:
    """Extrae de un HAR los puntos de las series de SERIES.

    Falla con ValueError si una serie reconocida viene con un formato que no
    se sabe leer (anio ambiguo, semana repetida, valor no entero): mejor no
    cargar que cargar mal.
    """
    har = json.loads(ruta.read_text(encoding="utf-8"))
    puntos: list[Punto] = []
    for entrada in har["log"]["entries"]:
        peticion = entrada["request"]
        if peticion["method"] != "POST" or "/api/v1/chart/data" not in peticion["url"]:
            continue
        if entrada["response"]["status"] != 200:
            continue
        cuerpo = json.loads((peticion.get("postData") or {}).get("text") or "{}")
        form_data = cuerpo.get("form_data") or {}
        if form_data.get("viz_type") != "echarts_timeseries_line":
            continue
        diagnostico = _diagnostico(form_data)
        if diagnostico not in SERIES:
            continue
        evento, clasificacion = SERIES[diagnostico]

        texto = entrada["response"]["content"].get("text") or "{}"
        resultado = json.loads(texto)["result"][0]
        anios = set(_RE_ANIO.findall(resultado.get("query") or ""))
        if len(anios) != 1:
            raise ValueError(f"{ruta.name}: {diagnostico} sin un anio unico en la consulta ({sorted(anios)})")
        anio = int(anios.pop())

        columnas = [c for c in resultado["colnames"] if c != "semana_mes"]
        if len(columnas) != 1:
            raise ValueError(f"{ruta.name}: {diagnostico} trae columnas inesperadas {resultado['colnames']}")
        columna = columnas[0]

        vistas: set[int] = set()
        for fila in resultado["data"]:
            m = _RE_SEMANA.match(fila["semana_mes"])
            if m is None:
                raise ValueError(f"{ruta.name}: semana ilegible {fila['semana_mes']!r}")
            semana = int(m.group(1))
            if not 1 <= semana <= 53 or semana in vistas:
                raise ValueError(f"{ruta.name}: {diagnostico} {anio} semana {semana} fuera de rango o repetida")
            vistas.add(semana)
            valor = fila[columna]
            if valor is None:
                continue
            if valor < 0 or valor != int(valor):
                raise ValueError(f"{ruta.name}: {diagnostico} {anio}-S{semana} valor no entero {valor!r}")
            puntos.append(
                Punto(evento, clasificacion, anio, semana, int(valor), entrada["startedDateTime"], ruta.name)
            )
    return puntos


def combinar(puntos: list[Punto]) -> tuple[dict[tuple[str, str, int, int], Punto], list[str]]:
    """Una cifra por (evento, clasificacion, anio, semana): la de la captura mas reciente."""
    elegidos: dict[tuple[str, str, int, int], Punto] = {}
    diferencias: list[str] = []
    for p in sorted(puntos, key=lambda p: p.capturado):
        clave = (p.evento, p.clasificacion, p.anio, p.semana)
        previo = elegidos.get(clave)
        if previo is not None and previo.conteo != p.conteo:
            diferencias.append(
                f"{p.evento}/{p.clasificacion} {p.anio}-S{p.semana}: "
                f"{previo.conteo} ({previo.archivo}) -> {p.conteo} ({p.archivo})"
            )
        elegidos[clave] = p
    return elegidos, diferencias


def huecos(elegidos: dict[tuple[str, str, int, int], Punto]) -> list[str]:
    """Semanas que faltan entre la 1 y la ultima publicada de cada serie y anio."""
    por_serie: dict[tuple[str, str, int], set[int]] = {}
    for evento, clasificacion, anio, semana in elegidos:
        por_serie.setdefault((evento, clasificacion, anio), set()).add(semana)
    faltan = []
    for (evento, clasificacion, anio), semanas in sorted(por_serie.items()):
        ausentes = sorted(set(range(1, max(semanas) + 1)) - semanas)
        if ausentes:
            faltan.append(f"{evento}/{clasificacion} {anio}: faltan {ausentes}")
    return faltan


def cargar(rutas: list[Path], dry_run: bool = False) -> int:
    puntos = [p for ruta in rutas for p in leer_captura(ruta)]
    elegidos, diferencias = combinar(puntos)
    for ruta in rutas:
        har = json.loads(ruta.read_text(encoding="utf-8"))
        paginas = [_RE_TABLERO.search(p.get("title") or "") for p in har["log"].get("pages", [])]
        tableros = sorted({m.group(1) for m in paginas if m})
        print(f"{ruta.name}: tablero {', '.join(tableros) or '?'}")
    for linea in diferencias:
        print(f"REVISADO POR MINSAL: {linea}")
    for linea in huecos(elegidos):
        print(f"AVISO: {linea}")

    resumen: dict[tuple[str, str, int], list[int]] = {}
    for (evento, clasificacion, anio, semana), p in elegidos.items():
        resumen.setdefault((evento, clasificacion, anio), []).append(semana)
    for (evento, clasificacion, anio), semanas in sorted(resumen.items()):
        total = sum(elegidos[(evento, clasificacion, anio, s)].conteo for s in semanas)
        print(f"  {evento}/{clasificacion} {anio}: semanas {min(semanas)}-{max(semanas)}, {total} casos")

    if dry_run:
        print(f"[dry-run] {len(elegidos)} filas listas, nada escrito.")
        return 0

    from psycopg2.extras import execute_values

    from db import get_connection

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM regiones WHERE codigo = 'SV'")
            region_id = cur.fetchone()[0]
            cur.execute("SELECT id FROM fuentes_datos WHERE codigo = 'minsal_tablero'")
            fila = cur.fetchone()
            if fila is None:
                raise RuntimeError("fuentes_datos no tiene 'minsal_tablero' -- correr la migracion 0012.")
            fuente_id = fila[0]
            cur.execute("SELECT codigo, id FROM tipos_evento")
            evento_id = dict(cur.fetchall())
            cur.execute("SELECT anio, semana_epi FROM semanas_epidemiologicas")
            calendario = set(cur.fetchall())

            sin_semana = sorted({(a, s) for (_, _, a, s) in elegidos if (a, s) not in calendario})
            if sin_semana:
                raise RuntimeError(
                    f"semanas sin calendario {sin_semana[:5]} -- correr poblar_semanas_epidemiologicas.py."
                )

            valores = [
                (region_id, evento_id[evento], anio, semana, clasificacion, p.conteo, fuente_id)
                for (evento, clasificacion, anio, semana), p in sorted(elegidos.items())
            ]
            execute_values(
                cur,
                """
                INSERT INTO casos_epidemiologicos
                    (region_id, tipo_evento_id, anio, semana_epi, clasificacion, conteo, fuente_id)
                VALUES %s
                ON CONFLICT (region_id, tipo_evento_id, anio, semana_epi, clasificacion, fuente_id)
                DO UPDATE SET conteo = EXCLUDED.conteo, fecha_ingesta = now()
                """,
                valores,
                page_size=len(valores),
            )
        conn.commit()
    finally:
        conn.close()
    return len(valores)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capturas", nargs="*", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    rutas = args.capturas or sorted(DIR_CAPTURAS.glob("*.har"))
    if not rutas:
        raise SystemExit(f"No hay capturas en {DIR_CAPTURAS}.")
    n = cargar(rutas, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"OK: {n} filas insertadas/actualizadas (fuente=minsal_tablero, nivel nacional).")


if __name__ == "__main__":
    main()
