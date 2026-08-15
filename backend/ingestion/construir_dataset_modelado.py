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

import csv
from collections import defaultdict
from dataclasses import dataclass, fields
from pathlib import Path

from corrida_canal_endemico_nacional import (
    ANIOS_BASE,
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
VENTANA_MEDIA_MOVIL = 4  # semanas anteriores, sin incluir la semana actual
ANIO_2020_EXCLUIDO = 2020  # recorte de entrenamiento, no de ingesta -- ver punto E


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
    """Para cada semana de la secuencia, calcula rezago-1, rezago-2 y media
    movil de las VENTANA_MEDIA_MOVIL semanas anteriores (excluyendo la
    semana actual), por variable. None si falta cualquier semana requerida
    -- no se interpola ni se rellena con la propia semana."""
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

            j0 = i - VENTANA_MEDIA_MOVIL
            if j0 < 0:
                fila[f"{variable}_media_movil{VENTANA_MEDIA_MOVIL}"] = None
                continue
            ventana_valores = []
            for j in range(j0, i):
                v = clima.get(secuencia[j], {}).get(variable)
                if v is None:
                    ventana_valores = None
                    break
                ventana_valores.append(v)
            if ventana_valores is None or len(ventana_valores) < VENTANA_MEDIA_MOVIL:
                fila[f"{variable}_media_movil{VENTANA_MEDIA_MOVIL}"] = None
            else:
                fila[f"{variable}_media_movil{VENTANA_MEDIA_MOVIL}"] = sum(ventana_valores) / len(ventana_valores)
        features[semana_actual] = fila
    return features


def clasificar_p75_p90(valor: float, p75: float, p90: float) -> str:
    return "alto" if valor > p90 else ("medio" if valor > p75 else "bajo")


@dataclass
class FilaDataset:
    anio: int
    semana_epi: int
    casos: float
    n_obs_base: int
    anios_presentes_base: int
    cumple_piso_suficiencia: bool
    p75_base: float | None
    p90_base: float | None
    etiqueta_riesgo: str | None
    features: dict[str, float | None]


def construir_dataset() -> tuple[list[FilaDataset], dict[str, int]]:
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
    for anio_objetivo in ANIOS_BASE:
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

            p75 = percentil(pool, 0.75)
            p90 = percentil(pool, 0.90)
            etiqueta = clasificar_p75_p90(valor_casos, p75, p90)

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
                    p75_base=p75,
                    p90_base=p90,
                    etiqueta_riesgo=etiqueta,
                    features=feats,
                )
            )
            contadores["filas_finales"] += 1

    return filas, contadores


def volcar_dataset(filas: list[FilaDataset]) -> Path:
    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
    path = INTERIM_ROOT / "dataset_modelado.csv"

    columnas_feature = []
    for variable in VARIABLES_CLIMA:
        for lag in LAGS:
            columnas_feature.append(f"{variable}_lag{lag}")
        columnas_feature.append(f"{variable}_media_movil{VENTANA_MEDIA_MOVIL}")

    columnas_base = [f.name for f in fields(FilaDataset) if f.name != "features"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columnas_base + columnas_feature)
        for fila in filas:
            base = [getattr(fila, c) for c in columnas_base]
            feats = [fila.features.get(c) for c in columnas_feature]
            w.writerow(base + feats)
    return path


def volcar_distribucion(filas: list[FilaDataset]) -> Path:
    path = INTERIM_ROOT / "distribucion_clases.csv"
    conteo: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for fila in filas:
        conteo[fila.anio][fila.etiqueta_riesgo] += 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["anio", "bajo", "medio", "alto", "total"])
        for anio in ANIOS_BASE:
            c = conteo[anio]
            total = c["bajo"] + c["medio"] + c["alto"]
            w.writerow([anio, c["bajo"], c["medio"], c["alto"], total])
    return path


def main() -> None:
    filas, contadores = construir_dataset()

    print(f"Corte de percentil: P75/P90 (cerrado 2026-08-15, no es el fiel a OPS/PAHO -- ver docs/contexto).")
    print(f"Agregación climática nacional: promedio simple de 14 departamentos (cerrado 2026-08-15).")
    print(f"Años objetivo: {', '.join(str(a) for a in ANIOS_BASE)} (ventana ±{VENTANA}, "
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

    dataset_path = volcar_dataset(filas)
    print(f"\nDataset -> {dataset_path}")
    dist_path = volcar_distribucion(filas)
    print(f"Distribución de clases -> {dist_path}")

    print("\nDistribución por año (esquema P75/P90):")
    with open(dist_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(f"  {row['anio']}: bajo={row['bajo']} medio={row['medio']} alto={row['alto']} "
                  f"(total={row['total']})")


if __name__ == "__main__":
    main()
