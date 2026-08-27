"""
Motor de idoneidad biofisica (Iv) y anomalia climatica continua -- Modulos 1
y 2 de "El Camino Ancho" v3 (docs/experimento-validacion-leadtime-camino-
ancho.md).

Las formulas de Iv y el metodo de Z-score leave-one-out estan duplicados
LITERALMENTE (mismas constantes, mismo metodo de resolucion de `c`) desde
`backend/ingestion/validar_leadtime_camino_ancho.py`, que ya corrio la
validacion empirica sobre datos reales (chequeo de cordura incluido, ver el
doc arriba). No existe hoy un paquete compartido entre `backend/api` y
`backend/ingestion`, asi que esto es una copia deliberada de las funciones
puras -- no una reimplementacion independiente. Si las formulas cambian en
el script de referencia, deben cambiar aqui tambien a mano.

Deliberadamente NO se trae de ese script:

  - La alerta binaria (Z >= 1.5 durante dos semanas consecutivas).
  - Cualquier framing de "lead time" / "ventana de anticipacion" / "temporada
    adelantada".

La validacion empirica (ver el doc) concluyo que esa tesis de anticipacion
NO se sostiene -- quedo retirada del pitch. Lo que este modulo expone es
Iv y el Z-score como series CONTINUAS, descriptivas, sin umbral ni bandera.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict

# --- Modulo 1: idoneidad biofisica (Iv) --------------------------------

TMIN, TMAX = 16.0, 38.0
R0, K = 30.0, 0.1

# Corpus climatico completo usado como baseline leave-one-out del Modulo 2
# (mismo rango que validar_leadtime_camino_ancho.py: ANIOS_CLIMA).
ANIOS_CLIMA = list(range(2014, 2025))  # 2014-2024

VARIABLES_REQUERIDAS = ("temp_media", "precipitation_sum", "humedad_relativa_media")


def _resolver_c_normalizacion() -> float:
    """max(f_T crudo) en T e [Tmin,Tmax], via grid fino -- c = 1/ese maximo.
    Mismo metodo que validar_leadtime_camino_ancho.py (que resuelve
    c=0.000795 sobre este mismo rango); se recalcula aqui en vez de copiar
    el numero para no arriesgar un desfase silencioso si Tmin/Tmax cambian
    en un solo lugar y no en el otro."""
    mejor = 0.0
    t = TMIN
    paso = 0.001
    while t <= TMAX:
        crudo = t * (t - TMIN) * math.sqrt(max(0.0, TMAX - t))
        if crudo > mejor:
            mejor = crudo
        t += paso
    return 1.0 / mejor


C_NORM = _resolver_c_normalizacion()


def f_T(temp_media: float) -> float:
    """Idoneidad termica. 0 fuera de [Tmin, Tmax] por definicion."""
    if temp_media <= TMIN or temp_media >= TMAX:
        return 0.0
    crudo = temp_media * (temp_media - TMIN) * math.sqrt(TMAX - temp_media)
    return max(0.0, min(1.0, C_NORM * crudo))


def f_R(precip_acum_2sem: float) -> float:
    """Idoneidad hidrica, logistica sobre precipitacion acumulada a 2
    semanas (R0=30mm/semana, k=0.1)."""
    return 1.0 / (1.0 + math.exp(-K * (precip_acum_2sem - R0)))


def f_H(humedad_relativa: float) -> float:
    """Idoneidad por humedad relativa -- ESTIMACION PROPIA DEL EQUIPO, NO
    CITADA (ni Mordecai et al. ni la tesis UES especifican una formula para
    esto; el documento solo pide "penaliza humedad relativa bajo 50%").
    Rampa lineal simple, la forma funcional mas simple que cumple ese
    requisito cualitativo sin inventar una curva mas compleja que nadie
    pidio."""
    return min(1.0, max(0.0, humedad_relativa / 50.0))


def calcular_Iv(temp_media: float, precip_acum_2sem: float, humedad_relativa: float) -> float:
    """Indice de idoneidad biofisica vectorial (Aedes aegypti), Modulo 1."""
    return f_T(temp_media) * (0.3 + 0.7 * f_R(precip_acum_2sem)) * f_H(humedad_relativa)


def _acumular_precipitacion_2sem(semanas_valores: dict[int, dict[str, float]], semana: int) -> float:
    """Precipitacion acumulada a 2 semanas (actual + anterior), sin envolver
    entre anios: si la semana anterior no existe (p.ej. semana 1), se usa
    solo la semana actual -- misma convencion que
    validar_leadtime_camino_ancho.py y corrida_canal_endemico_nacional.py."""
    valor_actual = semanas_valores.get(semana, {}).get("precipitation_sum", 0.0)
    valor_prev = semanas_valores.get(semana - 1, {}).get("precipitation_sum", 0.0) if semana > 1 else 0.0
    return valor_actual + valor_prev


def calcular_serie_iv(
    clima: dict[str, dict[int, dict[int, dict[str, float]]]]
) -> dict[str, dict[int, dict[int, float]]]:
    """codigo -> anio -> semana -> Iv, a partir de codigo -> anio -> semana
    -> {variable: valor}. Semanas con alguna de las 3 variables faltante se
    omiten (no se imputa nada)."""
    resultado: dict[str, dict[int, dict[int, float]]] = defaultdict(lambda: defaultdict(dict))
    for codigo, por_anio in clima.items():
        for anio, semanas in por_anio.items():
            for semana, valores in semanas.items():
                if (
                    "temp_media" not in valores
                    or "precipitation_sum" not in valores
                    or "humedad_relativa_media" not in valores
                ):
                    continue

                valor_actual = valores["precipitation_sum"]
                if semana > 1:
                    prev_sem = semanas.get(semana - 1)
                    valor_prev = prev_sem.get("precipitation_sum", 0.0) if prev_sem else 0.0
                else:
                    valor_prev = 0.0
                r_acum = valor_actual + valor_prev

                iv = calcular_Iv(valores["temp_media"], r_acum, valores["humedad_relativa_media"])
                resultado[codigo][anio][semana] = iv
    return resultado


# --- Modulo 2: anomalia climatica continua (Z-score) --------------------


def calcular_baseline_semana(
    serie_codigo: dict[int, dict[int, float]],
    anio_excluir: int,
    semana: int,
    anios_corpus: list[int] = ANIOS_CLIMA,
) -> tuple[list[float], float | None, float | None]:
    """Pool leave-one-out (anios_corpus menos anio_excluir, misma semana
    exacta, sin ventana de semanas vecinas -- el documento no la pide para
    Iv). Devuelve (pool, mediana, desviacion); mediana/desviacion son None
    si el pool tiene menos de 3 observaciones (mismo piso que
    validar_leadtime_camino_ancho.py)."""
    pool = [
        serie_codigo[a][semana]
        for a in anios_corpus
        if a != anio_excluir and semana in serie_codigo.get(a, {})
    ]
    if len(pool) < 3:
        return pool, None, None
    return pool, statistics.median(pool), statistics.stdev(pool)


def calcular_sigma(valor: float, mediana: float | None, desv: float | None) -> float | None:
    """Z-score continuo de `valor` contra el baseline (mediana, desv). None
    si el baseline es insuficiente o degenerado (desv ~ 0). Deliberadamente
    NO hay umbral ni bandera aqui -- ver docstring del modulo."""
    if mediana is None or desv is None or desv < 1e-9:
        return None
    return (valor - mediana) / desv


def percentil(valores: list[float], p: float) -> float:
    """Interpolacion lineal, mismo metodo que
    corrida_canal_endemico_nacional.percentil -- duplicado aqui en vez de
    importado por la misma razon que las formulas de Iv (sin paquete
    compartido entre api e ingestion)."""
    ordenados = sorted(valores)
    n = len(ordenados)
    if n == 1:
        return ordenados[0]
    rango = p * (n - 1)
    lo = int(rango)
    hi = min(lo + 1, n - 1)
    frac = rango - lo
    return ordenados[lo] + frac * (ordenados[hi] - ordenados[lo])


# --- Acceso a datos (variables_ambientales) ------------------------------


def cargar_clima_departamentos(
    conn, anios: list[int], semanas: list[int] | None = None
) -> dict[str, dict[int, dict[int, dict[str, float]]]]:
    """codigo -> anio -> semana -> {variable: valor}, para todos los
    departamentos (nivel_admin=1), restringido a `anios` y opcionalmente a
    un subconjunto de `semanas` (para el endpoint /spatial/current, que
    solo necesita la semana pedida y la anterior, no el corpus completo)."""
    sql = """
        SELECT r.codigo, va.anio, va.semana_epi, va.variable, va.valor
        FROM variables_ambientales va
        JOIN regiones r ON r.id = va.region_id
        WHERE r.nivel_admin = 1
          AND va.anio = ANY(%s)
          AND va.variable IN ('temp_media', 'precipitation_sum', 'humedad_relativa_media')
    """
    params: list = [anios]
    if semanas is not None:
        sql += " AND va.semana_epi = ANY(%s)"
        params.append(semanas)

    with conn.cursor() as cur:
        cur.execute(sql, params)
        filas = cur.fetchall()

    out: dict[str, dict[int, dict[int, dict[str, float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict))
    )
    for codigo, anio, semana, variable, valor in filas:
        out[codigo][anio][semana][variable] = float(valor)
    return out


def cargar_clima_departamento(
    conn, codigo: str, anios: list[int] = ANIOS_CLIMA
) -> dict[int, dict[int, dict[str, float]]]:
    """anio -> semana -> {variable: valor}, para un solo departamento
    (codigo ISO 3166-2:SV, ej. 'SV-SS'), corpus completo de anios."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT va.anio, va.semana_epi, va.variable, va.valor
            FROM variables_ambientales va
            JOIN regiones r ON r.id = va.region_id
            WHERE r.nivel_admin = 1
              AND r.codigo = %s
              AND va.anio = ANY(%s)
              AND va.variable IN ('temp_media', 'precipitation_sum', 'humedad_relativa_media')
            """,
            (codigo, anios),
        )
        filas = cur.fetchall()

    out: dict[int, dict[int, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for anio, semana, variable, valor in filas:
        out[anio][semana][variable] = float(valor)
    return out
