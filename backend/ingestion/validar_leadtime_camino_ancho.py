"""
Validacion empirica previa del "Camino Ancho" (docs/experimento-validacion-
leadtime-camino-ancho.md). Responde una sola pregunta: si el indice de
idoneidad biofisica (Iv) + detector de anomalias estacionales habrian
anticipado el ascenso real de casos observado en los boletines MINSAL,
y por cuantas semanas -- reportando el resultado real, incluyendo los
casos sin anticipacion o con senal tardia. No entrena nada, no escribe a
Postgres, no toca FastAPI ni el frontend.

Formulas de Iv tomadas literalmente de "EPI-Aetheris_Camino_Ancho_v2_
ajustada.md" (seccion 4, Modulo 1):

  f_T(T) = max(0, c . T . (T-Tmin) . sqrt(Tmax-T))   Tmin=16, Tmax=38
  f_R(R) = 1 / (1 + e^(-k.(R-R0)))                    R0=30mm/sem, k=0.1
  Iv = f_T(T) . (0.3 + 0.7.f_R(R)) . f_H(HR)

f_H(HR) NO tiene formula explicita en el documento ("penaliza humedad
relativa bajo 50%") -- ni Mordecai et al. ni la tesis UES estan citadas
para esa funcion especificamente, a diferencia de f_T/f_R. Por indicacion
expresa del documento ("marcarse explicitamente como estimacion propia
del equipo, con esa etiqueta visible"), se usa una rampa lineal simple,
NO citada, marcada como tal en el informe:

  f_H(HR) = min(1, max(0, HR/50))   -- 0 en HR=0%, 1 desde HR=50% en
  adelante. Monotona, capa el requisito cualitativo del documento sin
  inventar una forma funcional mas compleja (logistica, gaussiana) que
  el documento no pide.

c (constante de normalizacion de f_T) se resuelve numericamente para que
max(f_T) en T e [Tmin,Tmax] = 1, via grid search fino -- no esta en el
documento como numero, es una normalizacion mecanica del propio Tmin/Tmax.

Metodologia de comparacion contra datos reales, acordada con el
coordinador (no inventada aqui):

  - Nacional: agregado simple (promedio no ponderado, sin pesos
    poblacionales -- no hay una decision de ponderacion cerrada en el
    proyecto) de Iv sobre los 14 departamentos, comparado contra el
    inicio de temporada YA CERRADO de corrida_canal_endemico_nacional.py
    (esquema P50/P75, sin recalcular).
  - Departamental: SOLO San Salvador (SV-SS), el unico de los 14 que
    califica bajo el filtro de suficiencia relajado ya corrido en
    inicio_temporada_departamental.py. Los otros 13 quedan fuera --
    no se les inventa un inicio de temporada.
  - Los anios 2018 y 2019 de SV-SS llevan una advertencia: el inicio de
    temporada calculado cae en semana 1 en ambos, seniai de pool
    disperso/degenerado en vez de una lectura real (ver
    inicio_temporada_departamental.py). Se reportan, no se ocultan, pero
    se excluyen del calculo de mediana/RIC departamental por ese motivo,
    marcados aparte.
  - Anios evaluados: 2018, 2019, 2021, 2022, 2023 (mismos que el canal
    endemico nacional y la unica ventana con datos MINSAL departamentales
    cargados). 2020 no esta en la tabla de casos departamentales en
    absoluto (nunca se descargo, ver AGENTS.md) -- no aplica exclusion
    especial aqui, simplemente no hay datos que comparar ese anio.
  - Baseline de Iv (mediana/desviacion por semana-del-anio): leave-one-
    out sobre el corpus climatico completo 2014-2024 (excluyendo el anio
    evaluado de su propio baseline, mismo principio que canal_endemico_
    nacional.py aplica a casos) -- SIN ventana de semanas vecinas (el
    documento no la pide para Iv, a diferencia del canal endemico de
    casos que si la usa).
  - Alerta: Z >= 1.5 dos semanas consecutivas (criterio literal del
    documento, seccion 4 Modulo 2). Primera alerta cronologica del anio
    = semana de deteccion. Sin alerta => "sin alerta", no se fuerza nada.

Uso:
    python3 validar_leadtime_camino_ancho.py
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from corrida_canal_endemico_nacional import (
    ANIOS_BASE,
    construir_pool as construir_pool_casos,
    percentil,
)
from db import get_connection
from inicio_temporada_departamental import (
    califica,
    correr_departamento,
    inicio_temporada_por_anio,
    leer_serie_departamental,
)

RAIZ = Path(__file__).parent
INTERIM_ROOT = RAIZ / "data" / "interim" / "leadtime_camino_ancho"
DOC_ROOT = RAIZ.parent.parent / "docs"

ANIOS_CLIMA = list(range(2014, 2025))  # 2014-2024, corpus completo para el baseline
ANIOS_EVALUADOS = ANIOS_BASE  # [2018, 2019, 2021, 2022, 2023] -- unicos con casos MINSAL depto cargados

TMIN, TMAX = 16.0, 38.0
R0, K = 30.0, 0.1
UMBRAL_Z = 1.5

SV_SS_ANIOS_DEGENERADOS = {2018, 2019}  # inicio calculado en semana 1, ver docstring


def _resolver_c_normalizacion() -> float:
    """max(f_T crudo) en T e [Tmin,Tmax], via grid fino -- c = 1/ese maximo."""
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
    if temp_media <= TMIN or temp_media >= TMAX:
        return 0.0
    crudo = temp_media * (temp_media - TMIN) * math.sqrt(TMAX - temp_media)
    return max(0.0, min(1.0, C_NORM * crudo))


def f_R(precip_acum_2sem: float) -> float:
    return 1.0 / (1.0 + math.exp(-K * (precip_acum_2sem - R0)))


def f_H(humedad_relativa: float) -> float:
    return min(1.0, max(0.0, humedad_relativa / 50.0))


def calcular_Iv(temp_media: float, precip_acum_2sem: float, humedad_relativa: float) -> float:
    return f_T(temp_media) * (0.3 + 0.7 * f_R(precip_acum_2sem)) * f_H(humedad_relativa)


def cargar_clima_departamental() -> dict[str, dict[int, dict[int, dict[str, float]]]]:
    """codigo -> anio -> semana -> {variable: valor}"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.codigo, va.anio, va.semana_epi, va.variable, va.valor
                FROM variables_ambientales va
                JOIN regiones r ON r.id = va.region_id
                WHERE r.nivel_admin = 1
                  AND va.anio = ANY(%s)
                  AND va.variable IN ('temp_media', 'precipitation_sum', 'humedad_relativa_media')
                """,
                (ANIOS_CLIMA,),
            )
            filas = cur.fetchall()
    finally:
        conn.close()

    out: dict[str, dict[int, dict[int, dict[str, float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(dict))
    )
    for codigo, anio, semana, variable, valor in filas:
        out[codigo][anio][semana][variable] = float(valor)
    return out


def calcular_serie_Iv(
    clima: dict[str, dict[int, dict[int, dict[str, float]]]]
) -> dict[str, dict[int, dict[int, float]]]:
    """codigo -> anio -> semana -> Iv. Precipitacion acumulada a 2 semanas
    sin envolver entre anios (misma convencion que canal_endemico_nacional):
    si la semana anterior no existe (semana 1), se usa solo la semana
    actual."""
    resultado: dict[str, dict[int, dict[int, float]]] = defaultdict(lambda: defaultdict(dict))
    requeridas = ("temp_media", "precipitation_sum", "humedad_relativa_media")
    for codigo, por_anio in clima.items():
        for anio, semanas in por_anio.items():
            for semana, valores in semanas.items():
                if any(valores.get(v) is None for v in requeridas):
                    continue
                precip_prev = semanas.get(semana - 1, {}).get("precipitation_sum", 0.0) if semana > 1 else 0.0
                r_acum = valores["precipitation_sum"] + precip_prev
                iv = calcular_Iv(valores["temp_media"], r_acum, valores["humedad_relativa_media"])
                resultado[codigo][anio][semana] = iv
    return resultado


def chequeo_de_cordura(serie_iv: dict[str, dict[int, dict[int, float]]]) -> list[float]:
    todos = [v for por_anio in serie_iv.values() for semanas in por_anio.values() for v in semanas.values()]
    n = len(todos)
    media = statistics.mean(todos)
    mediana = statistics.median(todos)
    desv = statistics.stdev(todos)
    minimo, maximo = min(todos), max(todos)
    frac_cero = sum(1 for v in todos if v < 0.01) / n
    frac_uno = sum(1 for v in todos if v > 0.99) / n

    print(f"Chequeo de cordura Iv (n={n}):")
    print(f"  media={media:.4f} mediana={mediana:.4f} desv={desv:.4f} min={minimo:.4f} max={maximo:.4f}")
    print(f"  fraccion < 0.01: {frac_cero:.1%}   fraccion > 0.99: {frac_uno:.1%}")

    bins = [0] * 10
    for v in todos:
        idx = min(9, int(v * 10))
        bins[idx] += 1
    print("  histograma (deciles 0.0-1.0):")
    for i, c in enumerate(bins):
        print(f"    [{i/10:.1f},{(i+1)/10:.1f}): {'#' * int(60 * c / n)} ({c/n:.1%})")

    if desv < 1e-6:
        raise SystemExit(
            "ABORTA: Iv es constante en todo el corpus real de El Salvador "
            "(desviacion ~0). La formula no produce variacion real -- reportar "
            "esto tal cual, no seguir adelante."
        )
    if frac_cero > 0.95 or frac_uno > 0.95:
        raise SystemExit(
            f"ABORTA: Iv es degenerado -- {frac_cero:.1%} de las observaciones < 0.01 "
            f"o {frac_uno:.1%} > 0.99 en el corpus real. No seguir adelante con esta formula."
        )
    print("  Distribucion no degenerada -- se continua.\n")
    return todos


def calcular_alertas_por_anio(
    serie_codigo: dict[int, dict[int, float]], anios_evaluar: list[int]
) -> dict[int, dict]:
    """Para un codigo (departamento o 'NACIONAL'), calcula Z-score semana a
    semana contra baseline leave-one-out (pool = ANIOS_CLIMA menos el anio
    evaluado, misma semana exacta) y la primera semana con alerta (Z>=1.5
    dos semanas consecutivas)."""
    resultado = {}
    for anio_obj in anios_evaluar:
        semanas_anio = sorted(serie_codigo.get(anio_obj, {}))
        detalle = []
        for semana in semanas_anio:
            pool = [
                serie_codigo[a][semana]
                for a in ANIOS_CLIMA
                if a != anio_obj and semana in serie_codigo.get(a, {})
            ]
            if len(pool) < 3:
                detalle.append((semana, serie_codigo[anio_obj][semana], None, None, None))
                continue
            mediana = statistics.median(pool)
            desv = statistics.stdev(pool)
            valor = serie_codigo[anio_obj][semana]
            z = None if desv < 1e-9 else (valor - mediana) / desv
            detalle.append((semana, valor, mediana, desv, z))

        primera_alerta = None
        for i in range(len(detalle) - 1):
            z1, z2 = detalle[i][4], detalle[i + 1][4]
            if z1 is not None and z2 is not None and z1 >= UMBRAL_Z and z2 >= UMBRAL_Z:
                primera_alerta = detalle[i][0]
                break

        resultado[anio_obj] = {"detalle": detalle, "primera_alerta": primera_alerta}
    return resultado


def inicio_temporada_nacional() -> dict[int, int | None]:
    """Reutiliza sin recalcular el esquema P50/P75 ya cerrado de
    corrida_canal_endemico_nacional.py. Primera semana con suficiencia y
    valor > p75 propio, por anio."""
    from corrida_canal_endemico_nacional import leer_serie_nacional

    serie = leer_serie_nacional()
    resultado: dict[int, int | None] = {}
    for anio_obj in ANIOS_BASE:
        celdas = []
        for semana, valor in sorted(serie.get(anio_obj, {}).items()):
            pool, anios_presentes = construir_pool_casos(serie, anio_obj, semana)
            n_obs = len(pool)
            suficiente = n_obs >= 12 and anios_presentes >= 3
            if pool and suficiente:
                p75 = percentil(pool, 0.75)
                celdas.append((semana, valor, p75))
        primera = next((s for s, v, p in celdas if v > p), None)
        resultado[anio_obj] = primera
    return resultado


@dataclass
class ResultadoLeadTime:
    nivel: str  # "nacional" | "departamental"
    codigo: str
    anio: int
    semana_alerta: int | None
    semana_inicio_real: int | None
    lead_time: int | None  # positivo = anticipo, negativo = tarde
    nota: str = ""


def main() -> None:
    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)

    print(f"c de normalizacion de f_T resuelto numericamente: {C_NORM:.6f}\n")

    print("Cargando clima departamental 2014-2024...")
    clima = cargar_clima_departamental()
    serie_iv = calcular_serie_Iv(clima)

    print("\nEjecutando chequeo de cordura sobre Iv (obligatorio antes de seguir)...")
    todos_iv = chequeo_de_cordura(serie_iv)

    # Volcar distribucion completa para inspeccion
    with open(INTERIM_ROOT / "distribucion_iv.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["iv"])
        for v in todos_iv:
            w.writerow([v])

    # --- Nacional: agregado simple (promedio no ponderado) de los 14 deptos ---
    print("Calculando agregado nacional de Iv (promedio simple, sin ponderar por poblacion)...")
    serie_iv_nacional: dict[int, dict[int, float]] = defaultdict(dict)
    for anio in ANIOS_CLIMA:
        semanas_comunes = set.intersection(
            *[set(serie_iv[cod].get(anio, {})) for cod in serie_iv]
        ) if serie_iv else set()
        for semana in semanas_comunes:
            valores = [serie_iv[cod][anio][semana] for cod in serie_iv]
            serie_iv_nacional[anio][semana] = statistics.mean(valores)

    alertas_nacional = calcular_alertas_por_anio(serie_iv_nacional, ANIOS_EVALUADOS)
    inicio_nacional = inicio_temporada_nacional()

    resultados: list[ResultadoLeadTime] = []
    for anio in ANIOS_EVALUADOS:
        alerta = alertas_nacional[anio]["primera_alerta"]
        inicio = inicio_nacional.get(anio)
        lead = None
        if alerta is not None and inicio is not None:
            lead = inicio - alerta
        nota = ""
        if inicio is None:
            nota = "sin inicio de temporada real detectado ese anio (nunca cruza P75 con suficiencia)"
        elif alerta is None:
            nota = "el detector no genero alerta ese anio"
        resultados.append(ResultadoLeadTime("nacional", "SV", anio, alerta, inicio, lead, nota))

    # --- Departamental: solo SV-SS ---
    print("Calculando inicio de temporada departamental real (SV-SS, unico que califica)...")
    serie_casos_depto = leer_serie_departamental()
    pasa, _ = califica(serie_casos_depto["SV-SS"])
    assert pasa, "SV-SS deberia calificar segun la corrida previa -- revisar si los datos cambiaron"
    celdas_ss = correr_departamento("SV-SS", serie_casos_depto["SV-SS"])
    inicio_ss = inicio_temporada_por_anio(celdas_ss)

    alertas_ss = calcular_alertas_por_anio(serie_iv["SV-SS"], ANIOS_EVALUADOS)
    for anio in ANIOS_EVALUADOS:
        alerta = alertas_ss[anio]["primera_alerta"]
        inicio = inicio_ss.get(anio)
        lead = None
        if alerta is not None and inicio is not None:
            lead = inicio - alerta
        nota = ""
        if anio in SV_SS_ANIOS_DEGENERADOS:
            nota = "inicio real cae en semana 1 -- probable artefacto de pool disperso, no lectura confiable (ver inicio_temporada_departamental.py)"
        elif inicio is None:
            nota = "sin inicio de temporada real detectado ese anio"
        elif alerta is None:
            nota = "el detector no genero alerta ese anio"
        resultados.append(ResultadoLeadTime("departamental", "SV-SS", anio, alerta, inicio, lead, nota))

    # Volcar detalle semana-a-semana de Z-scores (para explicar por que no
    # hubo alerta en los anios donde no la hubo, no solo reportar "no hubo")
    zdetalle_path = INTERIM_ROOT / "zscores_detalle.csv"
    with open(zdetalle_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nivel", "codigo", "anio", "semana", "valor_iv", "mediana_baseline", "desv_baseline", "z"])
        for anio, info in alertas_nacional.items():
            for semana, valor, mediana, desv, z in info["detalle"]:
                w.writerow(["nacional", "SV", anio, semana, valor, mediana, desv, z])
        for anio, info in alertas_ss.items():
            for semana, valor, mediana, desv, z in info["detalle"]:
                w.writerow(["departamental", "SV-SS", anio, semana, valor, mediana, desv, z])
    print(f"Detalle Z-score semana a semana -> {zdetalle_path}")

    print("\nMaximo Z alcanzado por anio (para entender que tan cerca estuvo de disparar la alerta):")
    for nivel, alertas in (("nacional", alertas_nacional), ("departamental", alertas_ss)):
        for anio, info in alertas.items():
            zs = [z for _, _, _, _, z in info["detalle"] if z is not None]
            if zs:
                print(f"  {nivel:13s} {anio}: max Z = {max(zs):.2f}  (umbral={UMBRAL_Z})")
            else:
                print(f"  {nivel:13s} {anio}: sin Z calculable (baseline insuficiente)")

    # Volcar tabla completa
    detalle_path = INTERIM_ROOT / "leadtime_resultados.csv"
    with open(detalle_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nivel", "codigo", "anio", "semana_alerta", "semana_inicio_real", "lead_time_semanas", "nota"])
        for r in resultados:
            w.writerow([r.nivel, r.codigo, r.anio, r.semana_alerta, r.semana_inicio_real, r.lead_time, r.nota])

    print(f"\nResultados -> {detalle_path}\n")
    print(f"{'nivel':13s} {'codigo':6s} {'anio':5s} {'alerta':7s} {'inicio':7s} {'lead':6s} nota")
    for r in resultados:
        print(f"{r.nivel:13s} {r.codigo:6s} {r.anio:<5d} "
              f"{str(r.semana_alerta):7s} {str(r.semana_inicio_real):7s} {str(r.lead_time):6s} {r.nota}")

    # Cifras de control: mediana/RIC de lead time, nacional vs departamental,
    # excluyendo explicitamente los anios degenerados de SV-SS y los "sin
    # dato" (None) del calculo estadistico -- se listan aparte, no se
    # imputan.
    def resumen(nivel: str, excluir_anios: set[int] = frozenset()) -> None:
        validos = [
            r.lead_time for r in resultados
            if r.nivel == nivel and r.lead_time is not None and r.anio not in excluir_anios
        ]
        total_nivel = [r for r in resultados if r.nivel == nivel and r.anio not in excluir_anios]
        n_total = len(total_nivel)
        n_validos = len(validos)
        print(f"\n=== Resumen nivel={nivel} (excluidos por decision metodologica: {sorted(excluir_anios) or 'ninguno'}) ===")
        print(f"  {n_validos}/{n_total} anio-casos con lead time medible (con alerta Y con inicio real).")
        if validos:
            mediana = statistics.median(validos)
            q1 = percentil(validos, 0.25)
            q3 = percentil(validos, 0.75)
            positivos = sum(1 for v in validos if v > 0)
            print(f"  mediana lead time = {mediana:.1f} semanas, RIC=[{q1:.1f}, {q3:.1f}]")
            print(f"  {positivos}/{n_validos} ({positivos/n_validos:.0%}) con lead time positivo (anticipo real)")
        else:
            print("  Sin ningun caso con lead time medible -- no hay base para calcular mediana/RIC.")

    resumen("nacional")
    resumen("departamental", excluir_anios=SV_SS_ANIOS_DEGENERADOS)

    print(f"\nCSV completo con todas las filas (incluidos anios degenerados y sin dato) -> {detalle_path}")


if __name__ == "__main__":
    main()
