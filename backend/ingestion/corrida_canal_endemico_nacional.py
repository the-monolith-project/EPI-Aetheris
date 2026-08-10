"""
Corrida del canal endemico sobre la serie nacional de OpenDengue (TAREA-02,
ver docs/contexto/01-decisiones-cerradas.md, pivote "Opcion C"). Alimenta la
eleccion de cortes de percentil que bloquea la tarjeta 23 -- no entrena
nada, es exploratorio.

Lee casos_epidemiologicos ya cargado (clasificacion='total', fuente
opendengue_v1_3, region SV) -- no vuelve a tocar el CSV de OpenDengue.
Implementa la ventana de semanas vecinas +-1 (ver
docs/contexto/02-decisiones-abiertas.md, punto A): la corrida exploratoria
de MINSAL (corrida_distribucion.py) NO la implementaba pese a una
afirmacion previa incorrecta en el contexto (ya corregida) -- esta es la
primera vez que se aplica de verdad. La ventana no envuelve entre anios: la
semana 1 pierde su vecina "semana 0" y la ultima semana del anio pierde su
vecina siguiente, en vez de tomar una semana del anio de al lado.

Mismos anios base que la ventana de entrenamiento departamental ya
cerrada: 2018, 2019, 2021, 2022, 2023 (2020 excluido). No escribe a
Postgres, no entrena nada -- toda salida va a
data/interim/canal_endemico_nacional/ (gitignoreada).

Uso:
    python3 corrida_canal_endemico_nacional.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from db import get_connection

RAIZ = Path(__file__).parent
INTERIM_ROOT = RAIZ / "data" / "interim" / "canal_endemico_nacional"
ANIOS_BASE = [2018, 2019, 2021, 2022, 2023]
VENTANA = 1  # +-1 semana vecina, minimo aritmeticamente viable (ver punto A)
PISO_OBSERVACIONES = 12
PISO_ANIOS_MIN = 3


def leer_serie_nacional() -> dict[int, dict[int, float]]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.anio, c.semana_epi, c.conteo
                FROM casos_epidemiologicos c
                JOIN regiones r ON r.id = c.region_id
                JOIN fuentes_datos f ON f.id = c.fuente_id
                WHERE r.codigo = 'SV' AND c.clasificacion = 'total'
                  AND f.codigo = 'opendengue_v1_3' AND c.anio = ANY(%s)
                ORDER BY c.anio, c.semana_epi
                """,
                (ANIOS_BASE,),
            )
            filas = cur.fetchall()
    finally:
        conn.close()

    serie: dict[int, dict[int, float]] = defaultdict(dict)
    for anio, semana, conteo in filas:
        serie[anio][semana] = float(conteo)
    return serie


def percentil(valores: list[float], p: float) -> float:
    """Interpolacion lineal, metodo 'inclusive' (igual que
    statistics.quantiles) generalizado a un percentil p arbitrario -- evita
    agregar numpy como dependencia nueva solo para esto."""
    ordenados = sorted(valores)
    n = len(ordenados)
    if n == 1:
        return ordenados[0]
    rango = p * (n - 1)
    lo = int(rango)
    hi = min(lo + 1, n - 1)
    frac = rango - lo
    return ordenados[lo] + frac * (ordenados[hi] - ordenados[lo])


def clasificar(valor: float, p50: float, p75: float, p90: float) -> tuple[str, str]:
    """Dos esquemas de corte candidatos, ninguno cerrado todavia (punto A)."""
    esquema_p75_p90 = "alto" if valor > p90 else ("medio" if valor > p75 else "bajo")
    esquema_p50_p75 = "alto" if valor > p75 else ("medio" if valor > p50 else "bajo")
    return esquema_p75_p90, esquema_p50_p75


@dataclass
class Celda:
    anio: int
    semana: int
    valor: float
    n_obs: int
    anios_presentes: int
    suficiente: bool
    p50: float | None
    p75: float | None
    p90: float | None
    clase_p75_p90: str | None
    clase_p50_p75: str | None


def _semanas_en_ventana(serie: dict[int, dict[int, float]], anio: int, semana: int) -> list[float]:
    semanas_anio = serie.get(anio, {})
    if not semanas_anio:
        return []
    max_semana = max(semanas_anio)
    valores = []
    for w in range(semana - VENTANA, semana + VENTANA + 1):
        if 1 <= w <= max_semana and w in semanas_anio:
            valores.append(semanas_anio[w])
    return valores


def construir_pool(serie: dict[int, dict[int, float]], anio_objetivo: int, semana: int) -> tuple[list[float], int]:
    pool = []
    anios_presentes = 0
    for anio in ANIOS_BASE:
        if anio == anio_objetivo:
            continue
        valores = _semanas_en_ventana(serie, anio, semana)
        if valores:
            anios_presentes += 1
            pool.extend(valores)
    return pool, anios_presentes


def correr() -> list[Celda]:
    serie = leer_serie_nacional()
    celdas = []
    for anio_objetivo in ANIOS_BASE:
        for semana, valor in sorted(serie.get(anio_objetivo, {}).items()):
            pool, anios_presentes = construir_pool(serie, anio_objetivo, semana)
            n_obs = len(pool)
            suficiente = n_obs >= PISO_OBSERVACIONES and anios_presentes >= PISO_ANIOS_MIN
            if pool:
                p50 = percentil(pool, 0.50)
                p75 = percentil(pool, 0.75)
                p90 = percentil(pool, 0.90)
                clase_a, clase_b = clasificar(valor, p50, p75, p90)
            else:
                p50 = p75 = p90 = None
                clase_a = clase_b = None
            celdas.append(
                Celda(anio_objetivo, semana, valor, n_obs, anios_presentes, suficiente,
                      p50, p75, p90, clase_a, clase_b)
            )
    return celdas


def volcar_detalle(celdas: list[Celda]) -> Path:
    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
    path = INTERIM_ROOT / "canal_endemico_nacional.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "anio", "semana", "valor", "n_obs_base", "anios_presentes_base",
            "cumple_piso_suficiencia", "p50", "p75", "p90",
            "clase_p75_p90", "clase_p50_p75",
        ])
        for c in celdas:
            w.writerow([
                c.anio, c.semana, c.valor, c.n_obs, c.anios_presentes, c.suficiente,
                c.p50, c.p75, c.p90, c.clase_p75_p90, c.clase_p50_p75,
            ])
    return path


def volcar_distribucion(celdas: list[Celda]) -> Path:
    path = INTERIM_ROOT / "distribucion_clases.csv"
    conteo: dict[tuple[int, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in celdas:
        if not c.suficiente:
            continue
        conteo[(c.anio, "p75_p90")][c.clase_p75_p90] += 1
        conteo[(c.anio, "p50_p75")][c.clase_p50_p75] += 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "esquema", "bajo", "medio", "alto", "total_clasificado"])
        for anio in ANIOS_BASE:
            for esquema in ("p75_p90", "p50_p75"):
                c = conteo[(anio, esquema)]
                total = c["bajo"] + c["medio"] + c["alto"]
                w.writerow([anio, esquema, c["bajo"], c["medio"], c["alto"], total])
    return path


def main() -> None:
    celdas = correr()
    total = len(celdas)
    suficientes = sum(1 for c in celdas if c.suficiente)
    anios_base_por_celda = len(ANIOS_BASE) - 1

    print(f"{total} celdas (año objetivo, semana) evaluadas sobre {len(ANIOS_BASE)} años base "
          f"({', '.join(str(a) for a in ANIOS_BASE)}).")
    print(f"{suficientes} ({suficientes / total:.1%}) cumplen el piso de suficiencia "
          f"({PISO_OBSERVACIONES} obs / {PISO_ANIOS_MIN} de {anios_base_por_celda} años, ventana ±{VENTANA}).")

    detalle_path = volcar_detalle(celdas)
    print(f"Detalle -> {detalle_path}")
    dist_path = volcar_distribucion(celdas)
    print(f"Distribución de clases -> {dist_path}")

    print("\nDistribución por año y esquema (solo celdas con suficiencia):")
    with open(dist_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(
                f"  {row['anio']} {row['esquema']}: bajo={row['bajo']} medio={row['medio']} "
                f"alto={row['alto']} (total={row['total_clasificado']})"
            )


if __name__ == "__main__":
    main()
