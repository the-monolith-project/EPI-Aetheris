"""
Tarjeta 23 -- construye el conjunto de datos de modelado: una fila por
semana nacional con predictores climaticos rezagados y etiqueta de riesgo
aplicada. Ver docs/contexto/01-decisiones-cerradas.md (cierre 2026-08-15)
para las dos decisiones que desbloquearon esta tarjeta.

Reutiliza sin reescribir la logica ya validada del canal endemico nacional
(corrida_canal_endemico_nacional.py): misma serie de casos, misma regla de
fuga de informacion (el anio objetivo nunca esta en su propia linea base),
misma ventana de semanas vecinas +-1, mismo piso de suficiencia. Lo nuevo
aqui es (a) agregar el clima de 14 departamentos a 1 serie nacional por
promedio simple, (b) construir rezagos/medias moviles climaticas, (c) fijar
el corte de percentil en P75/P90 (cerrado 2026-08-15 -- deliberadamente NO
el que reproduce el canal endemico OPS/PAHO de 4 zonas, que da P50/P75).

El predictor del modelo es UNICAMENTE clima rezagado (decision cerrada
2026-08-09) -- no se incluye clima de la semana actual como feature, solo
rezagos y medias moviles de semanas anteriores. Los rezagos climaticos SI
cruzan el limite de anio (el clima es un proceso fisico continuo, a
diferencia de la linea base de percentiles de la etiqueta, que nunca debe
ver el anio que esta etiquetando).

No escribe a Postgres: no existe tabla para un dataset de modelado en el
esquema (agregarla exigiria un ADR previo, ver CLAUDE.md). Salida a
data/interim/dataset_modelado/ (gitignoreada), igual que las corridas
exploratorias previas.

Uso:
    python3 construir_dataset_modelado.py
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass, fields
from pathlib import Path

import corrida_canal_endemico_nacional as canal_endemico
from corrida_canal_endemico_nacional import (
    ANIOS_BASE as ANIOS_BASE_PRODUCCION,
    PISO_ANIOS_MIN,
    PISO_OBSERVACIONES,
    VENTANA,
    construir_pool,
    leer_serie_nacional,
    percentil,
)
from db import get_connection

RAIZ = Path(__file__).parent
INTERIM_ROOT = RAIZ / "data" / "interim" / "dataset_modelado"

VARIABLES_CLIMA = [
    "temp_max", "temp_min", "temp_media",
    "humedad_relativa_media", "punto_rocio",
    "precipitation_sum", "precipitation_hours",
]
LAGS = (1, 2)
# Media movil a 4 semanas. Se probo ampliar a (4, 8, 12) el 2026-08-16 para
# ver si una ventana mas larga (el ciclo mosquito-transmision acumula
# condiciones favorables durante 2-3 meses, no 1) le daba al modelo la senal
# que le faltaba para detectar "alto" -- resultado NEGATIVO: recall de
# "alto" siguio en 0.000 en los dos anios de prueba con casos reales (2019,
# 2022), igual que con la ventana corta, y de paso empeoro el F1 macro del
# modelo de produccion (2023). Revertido. Detalle completo del experimento
# descartado en docs/experimento-ventana-climatica-ampliada.md -- no
# reabrir esto sin una senal distinta de que el problema es de ventana.
VENTANAS_MEDIA_MOVIL = (4,)  # semanas anteriores, sin incluir la semana actual
ANIO_2020_EXCLUIDO = 2020  # recorte de entrenamiento, no de ingesta -- ver punto E

# Cortes de percentil candidatos. p75_p90 es el de produccion (cerrado
# 2026-08-15). p50_p75 es el que SI reproduce el canal endemico OPS/PAHO de
# 4 zonas ya verificado -- exploratorio, para probar si "alto" siendo el
# 25% superior (en vez del 10%) le da al modelo mas ejemplos positivos de
# los que aprender. Ver docs/contexto/01-decisiones-cerradas.md para el
# motivo por el que se eligio p75_p90 en produccion pese a esto.
CORTES = {"p75_p90": (0.75, 0.90), "p50_p75": (0.50, 0.75)}
CORTE_PRODUCCION = "p75_p90"


def leer_clima_departamental_por_semana() -> tuple[dict[tuple[int, int], dict[str, float]], dict[tuple[int, int, str], int]]:
    """Agrega variables_ambientales de 14 departamentos a 1 serie nacional
    por promedio simple (cerrado 2026-08-15), igual para las 7 variables.

    Devuelve (clima_nacional, cobertura) donde cobertura cuenta cuantos
    departamentos aportaron cada (anio, semana, variable) -- para detectar
    huecos silenciosos en vez de asumir que siempre son 14/14.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT v.anio, v.semana_epi, v.variable, AVG(v.valor), COUNT(*)
                FROM variables_ambientales v
                JOIN regiones r ON r.id = v.region_id
                WHERE r.nivel_admin = 1
                GROUP BY v.anio, v.semana_epi, v.variable
                """
            )
            filas = cur.fetchall()
    finally:
        conn.close()

    clima: dict[tuple[int, int], dict[str, float]] = defaultdict(dict)
    cobertura: dict[tuple[int, int, str], int] = {}
    for anio, semana, variable, promedio, n_deptos in filas:
        clima[(anio, semana)][variable] = float(promedio)
        cobertura[(anio, semana, variable)] = n_deptos
    return clima, cobertura


def leer_secuencia_semanas() -> list[tuple[int, int]]:
    """Orden cronologico real (por fecha_inicio), no un simple sort de
    (anio, semana) -- necesario para que los rezagos crucen el limite de
    anio en el orden correcto, incluidos anios de 53 semanas."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT anio, semana_epi FROM semanas_epidemiologicas ORDER BY fecha_inicio"
            )
            return [(row[0], row[1]) for row in cur.fetchall()]
    finally:
        conn.close()


def construir_rezagos(
    clima: dict[tuple[int, int], dict[str, float]],
    secuencia: list[tuple[int, int]],
) -> dict[tuple[int, int], dict[str, float | None]]:
    """Para cada semana de la secuencia, calcula rezago-1, rezago-2 y medias
    moviles de VENTANAS_MEDIA_MOVIL semanas anteriores (excluyendo la semana
    actual), por variable. None si falta cualquier semana requerida -- no se
    interpola ni se rellena con la propia semana."""
    features: dict[tuple[int, int], dict[str, float | None]] = {}
    for i, semana_actual in enumerate(secuencia):
        fila: dict[str, float | None] = {}
        for variable in VARIABLES_CLIMA:
            for lag in LAGS:
                j = i - lag
                clave = f"{variable}_lag{lag}"
                if j < 0:
                    fila[clave] = None
                    continue
                valores_prev = clima.get(secuencia[j], {})
                fila[clave] = valores_prev.get(variable)

            for ventana in VENTANAS_MEDIA_MOVIL:
                clave_ventana = f"{variable}_media_movil{ventana}"
                j0 = i - ventana
                if j0 < 0:
                    fila[clave_ventana] = None
                    continue
                ventana_valores = []
                for j in range(j0, i):
                    v = clima.get(secuencia[j], {}).get(variable)
                    if v is None:
                        ventana_valores = None
                        break
                    ventana_valores.append(v)
                if ventana_valores is None or len(ventana_valores) < ventana:
                    fila[clave_ventana] = None
                else:
                    fila[clave_ventana] = sum(ventana_valores) / len(ventana_valores)
        features[semana_actual] = fila
    return features


def clasificar(valor: float, corte_inferior: float, corte_superior: float) -> str:
    return "alto" if valor > corte_superior else ("medio" if valor > corte_inferior else "bajo")


@dataclass
class FilaDataset:
    anio: int
    semana_epi: int
    casos: float
    n_obs_base: int
    anios_presentes_base: int
    cumple_piso_suficiencia: bool
    corte_inferior_base: float | None
    corte_superior_base: float | None
    etiqueta_riesgo: str | None
    features: dict[str, float | None]


def construir_dataset(corte: str, anios_base: list[int]) -> tuple[list[FilaDataset], dict[str, int]]:
    p_inferior, p_superior = CORTES[corte]
    # leer_serie_nacional() y construir_pool() (importadas de
    # corrida_canal_endemico_nacional) leen su propio ANIOS_BASE del
    # namespace del modulo en tiempo de llamada -- sobreescribirlo aqui es
    # la forma de extender la ventana de anios base sin reimplementar esa
    # logica ya validada (ver docstring del modulo).
    canal_endemico.ANIOS_BASE = anios_base
    serie_casos = leer_serie_nacional()
    clima_nacional, cobertura = leer_clima_departamental_por_semana()
    secuencia = leer_secuencia_semanas()
    rezagos = construir_rezagos(clima_nacional, secuencia)

    huecos_cobertura = {k: v for k, v in cobertura.items() if v != 14}
    if huecos_cobertura:
        print(
            f"AVISO: {len(huecos_cobertura)} combinaciones (año, semana, variable) climáticas "
            f"no tienen los 14 departamentos esperados. Ejemplos: "
            f"{list(huecos_cobertura.items())[:5]}"
        )

    contadores = {
        "total_candidatas": 0,
        "descartadas_sin_historia_climatica": 0,
        "descartadas_sin_suficiencia_etiqueta": 0,
        "descartadas_anio_2020": 0,
        "filas_finales": 0,
    }

    filas: list[FilaDataset] = []
    for anio_objetivo in anios_base:
        for semana, valor_casos in sorted(serie_casos.get(anio_objetivo, {}).items()):
            contadores["total_candidatas"] += 1

            if anio_objetivo == ANIO_2020_EXCLUIDO:
                # No debería ocurrir -- ANIOS_BASE ya excluye 2020 -- pero
                # se deja el chequeo explícito porque el recorte de 2020 es
                # una regla de esta capa, no de la ingesta (punto E).
                contadores["descartadas_anio_2020"] += 1
                continue

            pool, anios_presentes = construir_pool(serie_casos, anio_objetivo, semana)
            n_obs = len(pool)
            suficiente = n_obs >= PISO_OBSERVACIONES and anios_presentes >= PISO_ANIOS_MIN
            if not suficiente:
                contadores["descartadas_sin_suficiencia_etiqueta"] += 1
                continue

            corte_inf = percentil(pool, p_inferior)
            corte_sup = percentil(pool, p_superior)
            etiqueta = clasificar(valor_casos, corte_inf, corte_sup)

            feats = rezagos.get((anio_objetivo, semana), {})
            if any(v is None for v in feats.values()) or not feats:
                contadores["descartadas_sin_historia_climatica"] += 1
                continue

            filas.append(
                FilaDataset(
                    anio=anio_objetivo,
                    semana_epi=semana,
                    casos=valor_casos,
                    n_obs_base=n_obs,
                    anios_presentes_base=anios_presentes,
                    cumple_piso_suficiencia=suficiente,
                    corte_inferior_base=corte_inf,
                    corte_superior_base=corte_sup,
                    etiqueta_riesgo=etiqueta,
                    features=feats,
                )
            )
            contadores["filas_finales"] += 1

    return filas, contadores


def volcar_dataset(filas: list[FilaDataset], sufijo: str) -> Path:
    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
    path = INTERIM_ROOT / f"dataset_modelado{sufijo}.csv"

    columnas_feature = []
    for variable in VARIABLES_CLIMA:
        for lag in LAGS:
            columnas_feature.append(f"{variable}_lag{lag}")
        for ventana in VENTANAS_MEDIA_MOVIL:
            columnas_feature.append(f"{variable}_media_movil{ventana}")

    columnas_base = [f.name for f in fields(FilaDataset) if f.name != "features"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columnas_base + columnas_feature)
        for fila in filas:
            base = [getattr(fila, c) for c in columnas_base]
            feats = [fila.features.get(c) for c in columnas_feature]
            w.writerow(base + feats)
    return path


def volcar_distribucion(filas: list[FilaDataset], sufijo: str, anios_base: list[int]) -> Path:
    path = INTERIM_ROOT / f"distribucion_clases{sufijo}.csv"
    conteo: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for fila in filas:
        conteo[fila.anio][fila.etiqueta_riesgo] += 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "bajo", "medio", "alto", "total"])
        for anio in anios_base:
            c = conteo[anio]
            total = c["bajo"] + c["medio"] + c["alto"]
            w.writerow([anio, c["bajo"], c["medio"], c["alto"], total])
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corte", choices=sorted(CORTES), default=CORTE_PRODUCCION,
        help=(
            f"Corte de percentil para la etiqueta (default: {CORTE_PRODUCCION}, producción -- "
            "sobrescribe dataset_modelado.csv, el que usa /api/riesgo-nacional a través de "
            "entrenar_clasificador.py). Con cualquier otro valor, corrida exploratoria: escribe "
            "a archivos con sufijo _<corte>, sin tocar los artefactos de producción."
        ),
    )
    parser.add_argument(
        "--anio-min", type=int, default=min(ANIOS_BASE_PRODUCCION),
        help=(
            f"Primer año base a incluir (default: {min(ANIOS_BASE_PRODUCCION)}, producción). "
            "Un valor menor amplía la ventana de entrenamiento hacia atrás (ej. 2014, con datos "
            "de OpenDengue/Open-Meteo ya cargados) -- 2020 siempre queda excluido. Cualquier valor "
            "distinto del de producción es corrida exploratoria: no toca los artefactos de "
            "producción."
        ),
    )
    args = parser.parse_args()
    anios_base = [a for a in range(args.anio_min, max(ANIOS_BASE_PRODUCCION) + 1) if a != ANIO_2020_EXCLUIDO]
    es_produccion = args.corte == CORTE_PRODUCCION and args.anio_min == min(ANIOS_BASE_PRODUCCION)
    partes_sufijo = []
    if args.corte != CORTE_PRODUCCION:
        partes_sufijo.append(args.corte)
    if args.anio_min != min(ANIOS_BASE_PRODUCCION):
        partes_sufijo.append(f"desde{args.anio_min}")
    sufijo = "" if not partes_sufijo else "_" + "_".join(partes_sufijo)

    filas, contadores = construir_dataset(args.corte, anios_base)

    p_inferior, p_superior = CORTES[args.corte]
    print(f"Corte de percentil: {args.corte} (P{int(p_inferior*100)}/P{int(p_superior*100)}).")
    print(f"Agregación climática nacional: promedio simple de 14 departamentos (cerrado 2026-08-15).")
    print(f"Años objetivo: {', '.join(str(a) for a in anios_base)} (ventana ±{VENTANA}, "
          f"piso {PISO_OBSERVACIONES} obs / {PISO_ANIOS_MIN} años).")
    print()
    print(f"Semanas candidatas evaluadas: {contadores['total_candidatas']}")
    print(f"  Descartadas por falta de historia climática (rezagos/media móvil incompletos): "
          f"{contadores['descartadas_sin_historia_climatica']}")
    print(f"  Descartadas por no cumplir piso de suficiencia de la línea base de etiqueta: "
          f"{contadores['descartadas_sin_suficiencia_etiqueta']}")
    print(f"  Filas finales en el dataset: {contadores['filas_finales']}")

    if not filas:
        print("\nNo se generó ninguna fila -- revisar que clima y casos estén cargados antes de reintentar.")
        return

    dataset_path = volcar_dataset(filas, sufijo)
    print(f"\nDataset -> {dataset_path}")
    dist_path = volcar_distribucion(filas, sufijo, anios_base)
    print(f"Distribución de clases -> {dist_path}")

    print(f"\nDistribución por año (esquema {args.corte}):")
    with open(dist_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(f"  {row['anio']}: bajo={row['bajo']} medio={row['medio']} alto={row['alto']} "
                  f"(total={row['total']})")


if __name__ == "__main__":
    main()
