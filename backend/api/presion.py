"""
Motor de presion epidemiologica relativa -- Modulo 3 de "El Camino Ancho".

Responde: "¿que tan alta es la presion de casos observados en este
departamento-semana comparado con su propia historia?" -- 100% descriptivo.
NO es un clasificador, NO predice nada, NO usa clima como insumo. Es un
percentil calculado directamente sobre conteos de casos historicos del
mismo departamento. No comparte codigo ni logica con el clasificador
retirado (entrenar_clasificador.py).

Formula cerrada por el coordinador (documento de decision: INSTRUCCIONES de
la tarea M3, 2026-08-21; ver tambien docs/modulo-3-presion-epidemiologica.md):

  - Variable base: casos_epidemiologicos.conteo, clasificacion IN
    ('probable', 'confirmado') como DOS SERIES SEPARADAS, nunca fusionadas,
    regiones de nivel_admin=1 (departamento). Nunca se mezcla
    clasificacion='total' (serie OpenDengue nacional, concepto distinto --
    ADR 0005).
  - Metodo: percentil historico leave-one-out, mismo patron que
    backend/ingestion/corrida_canal_endemico_nacional.py. Las funciones de
    ventana/pool estan duplicadas deliberadamente desde ese script (no
    existe paquete compartido entre backend/api y backend/ingestion --
    misma convencion que las formulas de idoneidad.py); `percentil()` SI se
    reutiliza importada de idoneidad.py, que ya es el duplicado documentado
    del de ingestion.
  - Anios base: 2018, 2019, 2021, 2022, 2023. 2020 excluido del baseline
    (colapso real de vigilancia durante covid, no baja transmision -- ver
    CLAUDE.md "Why 2020 is excluded"; exclusion de ventana de comparacion,
    NO de ingesta).
  - Anti-fuga: leave-one-out estricto -- el anio descrito nunca aparece en
    su propio baseline.
  - Ventana de semanas vecinas: +-1 (actual, anterior y siguiente), sin
    envolver entre anios -- la semana 1 no toma semanas del anio anterior
    ni la ultima del anio toma la semana 1 del siguiente.
  - Piso de suficiencia: al menos 3 de los 4 anios leave-one-out aportan
    alguna observacion dentro de la ventana +-1 (cuentan anios distintos,
    no el numero de semanas). Si no se cumple, la celda es INSUFICIENTE y
    el resultado es None + nota -- nunca se inventa ni interpola un valor.
  - Cortes: P50 y P75 sobre el pool del baseline (decision explicita del
    coordinador: mas sensible que el P75/P90 de la corrida nacional; se
    acepta que pueda sobre-etiquetar semanas de anios de baja transmision,
    trade-off consciente, no un error a corregir).
  - Lectura cualitativa (texto libre, no bandera booleana de alerta --
    Camino Ancho no hace alertas binarias): valor <= P50 -> "baja";
    P50 < valor <= P75 -> "media"; valor > P75 -> "alta". La convencion en
    los bordes (igualdad cae hacia abajo) es la misma que
    corrida_canal_endemico_nacional.clasificar.
  - Ademas de la categoria se expone el percentil relativo crudo del valor
    observado dentro del pool (donde cae exactamente, 0-100), igual que
    M1/M2 exponen `iv` y `anomaly_sigma` continuos junto a cualquier
    lectura cualitativa.

Nada se persiste: todo se calcula on-request desde casos_epidemiologicos,
mismo patron que M1/M2 (idoneidad.py). Sin cambios de esquema.
"""

from __future__ import annotations

from collections import defaultdict

from .idoneidad import percentil

# Mismos anios base que la ventana departamental cerrada del proyecto
# (2020 excluido -- ver docstring del modulo).
ANIOS_BASE = [2018, 2019, 2021, 2022, 2023]
VENTANA = 1  # +-1 semana vecina, sin wrap entre anios
PISO_ANIOS_MIN = 3  # al menos 3 de los 4 anios leave-one-out con observacion

SERIES = ("probable", "confirmado")

NOTA_INSUFICIENTE = (
    "sin datos suficientes para baseline "
    "(menos de 3 años base con observaciones en la ventana ±1)"
)
NOTA_SIN_OBSERVACION = (
    "sin observación registrada para esta semana/año en esta serie "
    "(hueco real de la fuente MINSAL, no un cero)"
)

# Tipo de la serie por departamento: anio -> semana -> conteo
SerieAnual = dict[int, dict[int, float]]


# --- Logica de calculo (funciones puras, sin acceso a datos) --------------


def _semanas_en_ventana(semanas_anio: dict[int, float], semana: int) -> list[float]:
    """Valores del anio dentro de la ventana +-VENTANA alrededor de
    `semana`, sin envolver entre anios: solo semanas >= 1 y presentes en el
    propio anio -- duplicado deliberado de
    corrida_canal_endemico_nacional._semanas_en_ventana (sin paquete
    compartido entre api e ingestion, misma convencion que idoneidad.py)."""
    if not semanas_anio:
        return []
    max_semana = max(semanas_anio)
    valores = []
    for w in range(semana - VENTANA, semana + VENTANA + 1):
        if 1 <= w <= max_semana and w in semanas_anio:
            valores.append(semanas_anio[w])
    return valores


def construir_pool(serie: SerieAnual, anio_objetivo: int, semana: int) -> tuple[list[float], int]:
    """Pool leave-one-out del baseline: observaciones de ANIOS_BASE menos el
    anio descrito, en la ventana +-1 de `semana`. Devuelve (pool, numero de
    anios distintos que aportaron alguna observacion)."""
    pool: list[float] = []
    anios_presentes = 0
    for anio in ANIOS_BASE:
        if anio == anio_objetivo:
            continue
        valores = _semanas_en_ventana(serie.get(anio, {}), semana)
        if valores:
            anios_presentes += 1
            pool.extend(valores)
    return pool, anios_presentes


def rango_percentil(pool: list[float], valor: float) -> float:
    """Percentil relativo (0-100) de `valor` dentro de `pool`: la inversa de
    la interpolacion lineal de `percentil()` (metodo 'inclusive'), para que
    rango_percentil(pool, percentil(pool, p)) ~= 100*p. Empates en el pool
    se resuelven con el punto medio del tramo empatado. Valores fuera del
    rango del pool saturan en 0 o 100 -- el percentil relativo describe
    donde cae el valor DENTRO de la historia observada, no extrapola."""
    ordenados = sorted(pool)
    n = len(ordenados)
    if n == 1:
        return 50.0 if valor == ordenados[0] else (0.0 if valor < ordenados[0] else 100.0)
    if valor <= ordenados[0]:
        return 0.0 if valor < ordenados[0] else _rango_empate(ordenados, valor)
    if valor >= ordenados[-1]:
        return 100.0 if valor > ordenados[-1] else _rango_empate(ordenados, valor)
    if valor in ordenados:
        return _rango_empate(ordenados, valor)
    # Interpolacion entre los dos vecinos que encierran a `valor`.
    for i in range(n - 1):
        lo, hi = ordenados[i], ordenados[i + 1]
        if lo < valor < hi:
            frac = (valor - lo) / (hi - lo)
            return 100.0 * (i + frac) / (n - 1)
    # Inalcanzable con pool ordenado; defensivo.
    return 100.0 * ordenados.index(valor) / (n - 1)


def _rango_empate(ordenados: list[float], valor: float) -> float:
    """Punto medio (en indices) del tramo de valores del pool iguales a
    `valor` -- convencion de empates de rango_percentil."""
    n = len(ordenados)
    primero = ordenados.index(valor)
    ultimo = primero
    while ultimo + 1 < n and ordenados[ultimo + 1] == valor:
        ultimo += 1
    return 100.0 * ((primero + ultimo) / 2.0) / (n - 1)


def categorizar(valor: float, p50: float, p75: float) -> str:
    """Lectura cualitativa (texto libre, no bandera de alerta): misma
    convencion de bordes que corrida_canal_endemico_nacional.clasificar
    (esquema p50_p75) -- la igualdad exacta con el corte cae hacia abajo."""
    if valor > p75:
        return "alta"
    if valor > p50:
        return "media"
    return "baja"


def calcular_presion(serie: SerieAnual, anio: int, semana: int) -> dict:
    """Presion epidemiologica relativa de una celda (departamento implicito
    en `serie`, una sola serie probable O confirmado -- nunca fusionadas).

    Devuelve un dict con:
      - casos_observados: conteo real de la celda, o None si no hay
        observacion (hueco de la fuente).
      - percentil / categoria / p50_baseline / p75_baseline: None cuando la
        celda no tiene observacion o el baseline es insuficiente.
      - n_obs_baseline / anios_baseline: tamano del pool y anios distintos
        que aportaron (siempre presentes, describen el baseline).
      - nota: presente solo cuando percentil es None, explica por que.
    """
    observado = serie.get(anio, {}).get(semana)
    pool, anios_presentes = construir_pool(serie, anio, semana)
    suficiente = anios_presentes >= PISO_ANIOS_MIN

    base = {
        "casos_observados": observado,
        "percentil": None,
        "categoria": None,
        "p50_baseline": None,
        "p75_baseline": None,
        "n_obs_baseline": len(pool),
        "anios_baseline": anios_presentes,
    }

    if not suficiente:
        base["nota"] = NOTA_INSUFICIENTE
        return base
    if observado is None:
        base["nota"] = NOTA_SIN_OBSERVACION
        return base

    p50 = percentil(pool, 0.50)
    p75 = percentil(pool, 0.75)
    base.update(
        percentil=round(rango_percentil(pool, observado), 1),
        categoria=categorizar(observado, p50, p75),
        p50_baseline=round(p50, 1),
        p75_baseline=round(p75, 1),
    )
    return base


# --- Acceso a datos (casos_epidemiologicos) -------------------------------


def cargar_casos_departamentales(
    conn, anios: list[int], semanas: list[int] | None = None
) -> dict[str, dict[str, SerieAnual]]:
    """codigo -> clasificacion ('probable'|'confirmado') -> anio -> semana
    -> conteo, para todos los departamentos (nivel_admin=1). `semanas`
    restringe la carga (el endpoint espacial solo necesita la ventana +-1
    de la semana pedida, no el corpus completo).

    Nunca incluye clasificacion='total' (OpenDengue nacional, ADR 0005).
    Hoy la unica fuente departamental es minsal_pdf; el SUM/GROUP BY es
    defensivo ante duplicados, no una fusion de fuentes deliberada."""
    sql = """
        SELECT r.codigo, c.clasificacion, c.anio, c.semana_epi, SUM(c.conteo)
        FROM casos_epidemiologicos c
        JOIN regiones r ON r.id = c.region_id
        WHERE r.nivel_admin = 1
          AND c.clasificacion IN ('probable', 'confirmado')
          AND c.anio = ANY(%s)
    """
    params: list = [anios]
    if semanas is not None:
        sql += " AND c.semana_epi = ANY(%s)"
        params.append(semanas)
    sql += " GROUP BY r.codigo, c.clasificacion, c.anio, c.semana_epi"

    with conn.cursor() as cur:
        cur.execute(sql, params)
        filas = cur.fetchall()

    out: dict[str, dict[str, SerieAnual]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict))
    )
    for codigo, clasificacion, anio, semana, conteo in filas:
        out[codigo][clasificacion][anio][semana] = float(conteo)
    return out


def cargar_casos_departamento(conn, codigo: str, anios: list[int]) -> dict[str, SerieAnual]:
    """clasificacion -> anio -> semana -> conteo, para un solo departamento
    (codigo ISO 3166-2:SV, ej. 'SV-SS')."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.clasificacion, c.anio, c.semana_epi, SUM(c.conteo)
            FROM casos_epidemiologicos c
            JOIN regiones r ON r.id = c.region_id
            WHERE r.nivel_admin = 1
              AND r.codigo = %s
              AND c.clasificacion IN ('probable', 'confirmado')
              AND c.anio = ANY(%s)
            GROUP BY c.clasificacion, c.anio, c.semana_epi
            """,
            (codigo, anios),
        )
        filas = cur.fetchall()

    out: dict[str, SerieAnual] = defaultdict(lambda: defaultdict(dict))
    for clasificacion, anio, semana, conteo in filas:
        out[clasificacion][anio][semana] = float(conteo)
    return out
