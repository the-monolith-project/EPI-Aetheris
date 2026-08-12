"""
Corrida del canal endemico nacional fiel a las 4 zonas OPS/PAHO
(exito/seguridad/alarma/epidemia), previa a decidir el colapso a 3 clases
(punto A, docs/contexto/02-decisiones-abiertas.md -- sigue abierto, esta
corrida no lo cierra).

Reutiliza sin modificar la linea base ya validada en
corrida_canal_endemico_nacional.py: mismos anios base (2018, 2019, 2021,
2022, 2023; 2020 excluido), misma regla de fuga, misma ventana de semanas
vecinas +-1, mismo piso de suficiencia (12 observaciones, >=3 de 4 anios
base). Ninguno de esos parametros se reabre aqui.

El calculo se separa en dos pasos independientes:
  1. Zonas de 4 (exito/seguridad/alarma/epidemia) sobre P25/P50/P75 de la
     linea base de cada celda. No decide nada sobre 3 clases.
  2. Colapso a 3 clases, parametrizable por un mapeo explicito (no
     hardcodeado dentro del paso 1) -- permite comparar mapeos distintos
     sin recalcular percentiles.

Convencion de corte: limite inferior estricto (>), igual que clasificar()
en el modulo base -- no la definicion de libro [P50,P75) para alarma. Se
elige asi para que el colapso "exito+seguridad -> bajo, alarma -> medio,
epidemia -> alto" sea matematicamente identico, celda por celda, al esquema
P50/P75 ya calculado en corrida_canal_endemico_nacional.py. La verificacion
cruzada mas abajo lo confirma contra la implementacion original, no solo
lo afirma.

No escribe a Postgres, no entrena nada, no decide el colapso final -- eso
sigue siendo del coordinador. Salida completa (no versionada) en
data/interim/canal_endemico_nacional_4zonas/ (gitignoreada).

Uso:
    python3 corrida_canal_endemico_4zonas.py
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
    clasificar,
    construir_pool,
    leer_serie_nacional,
    percentil,
)

RAIZ = Path(__file__).parent
INTERIM_ROOT = RAIZ / "data" / "interim" / "canal_endemico_nacional_4zonas"

ZONAS = ("exito", "seguridad", "alarma", "epidemia")

# Paso 2: colapso explicito de 4 zonas a 3 clases. Este mapeo en particular
# es el que debe reproducir exactamente el esquema P50/P75 ya calculado --
# es el insumo de la verificacion cruzada, no una recomendacion de cual
# colapso usar en producción.
MAPEO_EQUIVALENTE_P50_P75 = {
    "exito": "bajo",
    "seguridad": "bajo",
    "alarma": "medio",
    "epidemia": "alto",
}


def zona(valor: float, p25: float, p50: float, p75: float) -> str:
    """Paso 1: cuatro zonas OPS. Limite inferior estricto (>) -- ver
    docstring del modulo para por que esta convencion, y no [P50,P75)."""
    if valor > p75:
        return "epidemia"
    if valor > p50:
        return "alarma"
    if valor > p25:
        return "seguridad"
    return "exito"


def colapsar(zona_valor: str, mapeo: dict[str, str]) -> str:
    """Paso 2: reduce una zona de 4 a una clase de 3 segun un mapeo
    explicito. No decide el mapeo -- eso es responsabilidad de quien
    llama, para poder comparar mapeos sin tocar el paso 1."""
    return mapeo[zona_valor]


@dataclass
class Celda:
    anio: int
    semana: int
    valor: float
    n_obs: int
    anios_presentes: int
    suficiente: bool
    p25: float | None
    p50: float | None
    p75: float | None
    zona: str | None
    clase_colapsada: str | None
    clase_p50_p75_original: str | None  # via clasificar() del modulo base


def correr() -> list[Celda]:
    serie = leer_serie_nacional()
    celdas = []
    for anio_objetivo in ANIOS_BASE:
        for semana, valor in sorted(serie.get(anio_objetivo, {}).items()):
            pool, anios_presentes = construir_pool(serie, anio_objetivo, semana)
            n_obs = len(pool)
            suficiente = n_obs >= PISO_OBSERVACIONES and anios_presentes >= PISO_ANIOS_MIN
            if pool:
                p25 = percentil(pool, 0.25)
                p50 = percentil(pool, 0.50)
                p75 = percentil(pool, 0.75)
                p90 = percentil(pool, 0.90)
                zona_valor = zona(valor, p25, p50, p75)
                clase_colapsada = colapsar(zona_valor, MAPEO_EQUIVALENTE_P50_P75)
                _, clase_original = clasificar(valor, p50, p75, p90)
            else:
                p25 = p50 = p75 = None
                zona_valor = clase_colapsada = clase_original = None
            celdas.append(
                Celda(anio_objetivo, semana, valor, n_obs, anios_presentes, suficiente,
                      p25, p50, p75, zona_valor, clase_colapsada, clase_original)
            )
    return celdas


def verificar_cruce(celdas: list[Celda]) -> list[Celda]:
    """El colapso exito+seguridad->bajo, alarma->medio, epidemia->alto debe
    reproducir, celda por celda, el esquema P50/P75 de clasificar() en el
    modulo base. Si no coincide, el paso 1 o la reutilizacion de la linea
    base tienen un error -- no seguir adelante con la salida."""
    discrepancias = [
        c for c in celdas
        if c.suficiente and c.clase_colapsada != c.clase_p50_p75_original
    ]
    if discrepancias:
        detalle = "\n".join(
            f"  anio={c.anio} semana={c.semana} valor={c.valor} "
            f"zona={c.zona} colapsada={c.clase_colapsada} "
            f"original_p50_p75={c.clase_p50_p75_original}"
            for c in discrepancias[:10]
        )
        raise SystemExit(
            f"Verificacion cruzada FALLIDA: {len(discrepancias)} celda(s) no "
            f"coinciden entre el colapso de 4 zonas y el esquema P50/P75 "
            f"original. No se escribe salida.\n{detalle}"
        )
    return discrepancias


def volcar_detalle(celdas: list[Celda]) -> Path:
    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
    path = INTERIM_ROOT / "canal_endemico_nacional_4zonas.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "anio", "semana", "valor", "n_obs_base", "anios_presentes_base",
            "cumple_piso_suficiencia", "p25", "p50", "p75", "zona",
            "clase_colapsada", "clase_p50_p75_original", "coincide",
        ])
        for c in celdas:
            coincide = (
                "" if c.zona is None
                else str(c.clase_colapsada == c.clase_p50_p75_original)
            )
            w.writerow([
                c.anio, c.semana, c.valor, c.n_obs, c.anios_presentes, c.suficiente,
                c.p25, c.p50, c.p75, c.zona, c.clase_colapsada,
                c.clase_p50_p75_original, coincide,
            ])
    return path


def volcar_distribucion(celdas: list[Celda]) -> Path:
    path = INTERIM_ROOT / "distribucion_zonas.csv"
    conteo: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in celdas:
        if not c.suficiente:
            continue
        conteo[c.anio][c.zona] += 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "exito", "seguridad", "alarma", "epidemia", "total_clasificado"])
        for anio in ANIOS_BASE:
            c = conteo[anio]
            total = sum(c[z] for z in ZONAS)
            w.writerow([anio, c["exito"], c["seguridad"], c["alarma"], c["epidemia"], total])
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

    verificar_cruce(celdas)
    print(f"Verificación cruzada OK: el colapso de 4 zonas reproduce exactamente "
          f"el esquema P50/P75 original en las {suficientes} celdas con suficiencia.")

    detalle_path = volcar_detalle(celdas)
    print(f"Detalle -> {detalle_path}")
    dist_path = volcar_distribucion(celdas)
    print(f"Distribución de zonas -> {dist_path}")

    print("\nDistribución de zonas por año (solo celdas con suficiencia):")
    with open(dist_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(
                f"  {row['anio']}: exito={row['exito']} seguridad={row['seguridad']} "
                f"alarma={row['alarma']} epidemia={row['epidemia']} "
                f"(total={row['total_clasificado']})"
            )


if __name__ == "__main__":
    main()
