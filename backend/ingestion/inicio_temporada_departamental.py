"""
Inicio de temporada por departamento-anio, para el diagnostico de lead time
del "Camino Ancho" (docs/experimento-validacion-leadtime-camino-ancho.md,
en construccion). No entrena nada, no escribe a Postgres.

Metodologia acordada explicitamente con el coordinador (no inventada aqui):

- Nivel nacional: reutiliza sin recalcular el corte P75 ya cerrado de
  corrida_canal_endemico_nacional.py (esquema p50_p75, ventana +-1,
  anios base 2018/2019/2021/2022/2023, piso 12 obs / >=3 de 4 anios).
  Inicio de temporada = primera semana del anio, entre las que cumplen el
  piso de suficiencia, con valor > p75 de su propio pool.

- Nivel departamental: NO existe corte cerrado (confirmado por inspeccion:
  corrida_canal_endemico_nacional.py filtra r.codigo = 'SV' explicitamente,
  corrida_canal_endemico_4zonas.py reutiliza esa misma serie nacional sin
  tocarla). Extension limitada, no forzada, definida por el coordinador:

    1. Volumen total de casos por departamento (probable + confirmado,
       2018-2023), los 14 ordenados de mayor a menor.
    2. Un departamento CALIFICA para percentil propio solo si al menos 3
       de los 5 anios base tienen >=8 semanas con actividad no-cero
       (suficiencia relajada -- el piso completo de 12 obs/3 anios ya se
       sabe que falla al 100% a nivel departamental, no se repite ese
       intento).
    3. Solo en los departamentos que califican: mismo metodo P50/P75,
       ventana +-1, sobre la serie propia del departamento (pool de los
       otros anios base). Inicio de temporada = primera semana con
       valor > p75 de su propio pool. Se reporta el n_obs/anios_presentes
       de cada celda igual que a nivel nacional, sin usarlo como filtro
       adicional -- la calificacion ya ocurrio en el paso 2.
    4. Los departamentos que no califican quedan FUERA de la validacion
       departamental -- no se les inventa un inicio de temporada. El
       diagnostico de lead time para esos se apoya solo en el resultado
       nacional.

Serie de casos usada para el ranking de volumen y para el canal propio:
probable + confirmado sumados por (region, anio, semana_epi) -- unica
fuente disponible a nivel departamental (minsal_pdf); no existe un
'total' departamental analogo al de OpenDengue. Esto es un supuesto
explicito de esta corrida, no una convencion ya cerrada en el proyecto.

Uso:
    python3 inicio_temporada_departamental.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from corrida_canal_endemico_nacional import (
    ANIOS_BASE,
    PISO_ANIOS_MIN,
    PISO_OBSERVACIONES,
    VENTANA,
    construir_pool,
    percentil,
)
from db import get_connection

RAIZ = Path(__file__).parent
INTERIM_ROOT = RAIZ / "data" / "interim" / "inicio_temporada_departamental"

PISO_SEMANAS_NO_CERO = 8
PISO_ANIOS_ACTIVIDAD = 3


def leer_serie_departamental() -> dict[str, dict[int, dict[int, float]]]:
    """codigo_depto -> anio -> semana -> conteo (probable + confirmado)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.codigo, c.anio, c.semana_epi, SUM(c.conteo)
                FROM casos_epidemiologicos c
                JOIN regiones r ON r.id = c.region_id
                JOIN fuentes_datos f ON f.id = c.fuente_id
                WHERE f.codigo = 'minsal_pdf' AND r.nivel_admin = 1
                  AND c.clasificacion IN ('probable', 'confirmado')
                  AND c.anio = ANY(%s)
                GROUP BY r.codigo, c.anio, c.semana_epi
                ORDER BY r.codigo, c.anio, c.semana_epi
                """,
                (ANIOS_BASE,),
            )
            filas = cur.fetchall()
    finally:
        conn.close()

    serie: dict[str, dict[int, dict[int, float]]] = defaultdict(lambda: defaultdict(dict))
    for codigo, anio, semana, conteo in filas:
        serie[codigo][anio][semana] = float(conteo)
    return serie


def volumen_total(serie_depto: dict[int, dict[int, float]]) -> float:
    return sum(v for anio_map in serie_depto.values() for v in anio_map.values())


def semanas_no_cero_por_anio(serie_depto: dict[int, dict[int, float]]) -> dict[int, int]:
    return {
        anio: sum(1 for v in semanas.values() if v > 0)
        for anio, semanas in serie_depto.items()
    }


def califica(serie_depto: dict[int, dict[int, float]]) -> tuple[bool, dict[int, int]]:
    no_cero = semanas_no_cero_por_anio(serie_depto)
    anios_con_actividad = sum(
        1 for anio in ANIOS_BASE if no_cero.get(anio, 0) >= PISO_SEMANAS_NO_CERO
    )
    return anios_con_actividad >= PISO_ANIOS_ACTIVIDAD, no_cero


@dataclass
class CeldaDepto:
    codigo: str
    anio: int
    semana: int
    valor: float
    n_obs: int
    anios_presentes: int
    suficiente: bool
    p50: float | None
    p75: float | None
    clase: str | None


def correr_departamento(codigo: str, serie_depto: dict[int, dict[int, float]]) -> list[CeldaDepto]:
    celdas = []
    for anio_objetivo in ANIOS_BASE:
        for semana, valor in sorted(serie_depto.get(anio_objetivo, {}).items()):
            pool, anios_presentes = construir_pool(serie_depto, anio_objetivo, semana)
            n_obs = len(pool)
            suficiente = n_obs >= PISO_OBSERVACIONES and anios_presentes >= PISO_ANIOS_MIN
            if pool:
                p50 = percentil(pool, 0.50)
                p75 = percentil(pool, 0.75)
                clase = "alto" if valor > p75 else ("medio" if valor > p50 else "bajo")
            else:
                p50 = p75 = None
                clase = None
            celdas.append(
                CeldaDepto(codigo, anio_objetivo, semana, valor, n_obs, anios_presentes,
                           suficiente, p50, p75, clase)
            )
    return celdas


def inicio_temporada_por_anio(celdas: list[CeldaDepto]) -> dict[int, int | None]:
    """Primera semana (cronologica) con valor > p75 propio, por anio. None si
    ninguna semana del anio cruza el umbral."""
    por_anio: dict[int, list[CeldaDepto]] = defaultdict(list)
    for c in celdas:
        if c.p75 is not None:
            por_anio[c.anio].append(c)
    resultado: dict[int, int | None] = {}
    for anio, lista in por_anio.items():
        lista.sort(key=lambda c: c.semana)
        primera = next((c.semana for c in lista if c.valor > c.p75), None)
        resultado[anio] = primera
    return resultado


def main() -> None:
    serie = leer_serie_departamental()
    volumenes = {cod: volumen_total(s) for cod, s in serie.items()}
    ranking = sorted(volumenes, key=lambda c: volumenes[c], reverse=True)

    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)

    print(f"14 departamentos, ranking por volumen total probable+confirmado "
          f"({ANIOS_BASE[0]}-{ANIOS_BASE[-1]}, {len(ANIOS_BASE)} años base):\n")

    calificados = []
    resumen_path = INTERIM_ROOT / "calificacion_departamentos.csv"
    with open(resumen_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "codigo", "volumen_total"] + [f"no_cero_{a}" for a in ANIOS_BASE]
                    + ["anios_con_actividad", "califica"])
        for i, cod in enumerate(ranking, start=1):
            pasa, no_cero = califica(serie[cod])
            anios_con_actividad = sum(1 for a in ANIOS_BASE if no_cero.get(a, 0) >= PISO_SEMANAS_NO_CERO)
            w.writerow([i, cod, volumenes[cod]] + [no_cero.get(a, 0) for a in ANIOS_BASE]
                        + [anios_con_actividad, pasa])
            marca = "CALIFICA" if pasa else "no califica"
            print(f"  {i:2d}. {cod}  vol={volumenes[cod]:.0f}  "
                  f"no_cero_por_anio={[no_cero.get(a, 0) for a in ANIOS_BASE]}  -> {marca}")
            if pasa:
                calificados.append(cod)

    print(f"\n{len(calificados)} de 14 departamentos califican para percentil propio "
          f"(>= {PISO_ANIOS_ACTIVIDAD} de {len(ANIOS_BASE)} años base con "
          f">= {PISO_SEMANAS_NO_CERO} semanas de actividad no-cero): {calificados}")
    print(f"Calificación completa -> {resumen_path}")

    detalle_path = INTERIM_ROOT / "inicio_temporada_departamental.csv"
    inicio_path = INTERIM_ROOT / "inicio_temporada_resumen.csv"
    with open(detalle_path, "w", newline="", encoding="utf-8") as fd, \
         open(inicio_path, "w", newline="", encoding="utf-8") as fi:
        wd = csv.writer(fd)
        wd.writerow(["codigo", "anio", "semana", "valor", "n_obs", "anios_presentes",
                     "suficiente", "p50", "p75", "clase"])
        wi = csv.writer(fi)
        wi.writerow(["codigo", "anio", "semana_inicio_temporada"])

        print("\nInicio de temporada por departamento calificado:")
        for cod in calificados:
            celdas = correr_departamento(cod, serie[cod])
            for c in celdas:
                wd.writerow([c.codigo, c.anio, c.semana, c.valor, c.n_obs, c.anios_presentes,
                             c.suficiente, c.p50, c.p75, c.clase])
            inicios = inicio_temporada_por_anio(celdas)
            for anio in ANIOS_BASE:
                semana = inicios.get(anio)
                wi.writerow([cod, anio, semana if semana is not None else ""])
            print(f"  {cod}: {inicios}")

    print(f"\nDetalle celda-a-celda -> {detalle_path}")
    print(f"Resumen inicio de temporada -> {inicio_path}")


if __name__ == "__main__":
    main()
