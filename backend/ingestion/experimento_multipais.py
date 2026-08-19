"""
Experimento: ¿entrenar con varios países de las Américas rescata el
clasificador nacional de riesgo de dengue? Ver la tarea completa y su
evidencia previa en el documento que acompañó este script (verificación de
cobertura ya hecha sin red: 18 países, 10.278 filas país-semana, 1.390
semanas "alto", 97 de 198 años-país con al menos una semana "alto"; El
Salvador correlaciona +0.280 con la señal regional -- último de los 18).

ADVERTENCIA DE ALCANCE: esto toca el estatuto cerrado de alcance geográfico
(nacional El Salvador para el MVP; lo multinacional era argumento de
escalabilidad, no entregable -- ver CLAUDE.md). Este script es un
experimento, no cambia producción: no escribe a Postgres, no toca
dataset_modelado.csv / clasificador_riesgo_nacional_v1.joblib /
metricas_modelo.json, no modifica construir_dataset_modelado.py,
entrenar_clasificador.py ni corrida_canal_endemico_nacional.py. Adoptar
esta vía en producción es decisión del coordinador.

Reutiliza sin reescribir la lógica de etiqueta ya validada de
corrida_canal_endemico_nacional.py (percentil, construir_pool, piso de
suficiencia) y la de evaluación ya validada de entrenar_clasificador.py
(metricas, baseline_climatologica) -- lo genuinamente nuevo aquí es el eje
país: aplicar esa misma lógica por país en vez de una sola vez para El
Salvador, y agregar el eje país al split de entrenamiento/prueba.

Parámetros de etiqueta y features idénticos a producción -- P75/P90,
ventana ±1, piso 12 obs / 3 años, LAGS=(1,2), media móvil de 4 semanas, 7
variables climáticas (+ oni_anom opcional). Si esto diverge de producción,
el experimento deja de hablar del modelo que se entrega.

Datos de entrada:
  Temporal_extract_PAHO_V1_3.csv, del repositorio oficial de OpenDengue
  (https://github.com/OpenDengue/master-repo -> assets/Temporal_extract_
  PAHO_V1_3.zip). NO se versiona (regla de datos crudos, CLAUDE.md) --
  descomprimir a backend/ingestion/data/raw/opendengue/, ya gitignoreado.

Tres corridas, tres preguntas distintas -- no se mezclan en la conclusión:
  --modo el-salvador                entrena con los otros 17 países, prueba
                                     en El Salvador año por año (la pregunta
                                     que importa para el entregable actual)
  --modo regional                   leave-one-year-out sobre los 18 países
                                     juntos (entregable distinto: clasificador
                                     regional, no de El Salvador)
  --modo regional --incluir-oni     igual que regional, + oni_anom (NOAA,
                                     ADR 0008) como predictor adicional

Uso:
    python3 experimento_multipais.py --csv RUTA/Temporal_extract_PAHO_V1_3.csv \
        --modo el-salvador [--incluir-oni] [--semillas 42] [--saltar-descarga]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import requests
from sklearn.ensemble import RandomForestClassifier

import corrida_canal_endemico_nacional as canal_endemico
from corrida_canal_endemico_nacional import construir_pool, percentil
from entrenar_clasificador import CLASES, baseline_climatologica, metricas

RAIZ = Path(__file__).parent
INTERIM_ROOT = RAIZ / "data" / "interim" / "experimento_multipais"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

# Mismo rango que la evidencia de cobertura ya verificada (11 años, 2014-2024).
ANIOS = list(range(2014, 2025))

# Idénticos a producción (construir_dataset_modelado.py) -- no divergir.
LAGS = (1, 2)
VENTANAS_MEDIA_MOVIL = (4,)
VARIABLES_ERA5_LAND = [
    "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
    "relative_humidity_2m_mean", "dew_point_2m_mean",
]
VARIABLES_ERA5 = ["precipitation_sum", "precipitation_hours"]
VARIABLES_CLIMA = VARIABLES_ERA5_LAND + VARIABLES_ERA5

# Un país cuenta como "serie completa" si cada uno de los 11 años tiene al
# menos 45 semanas presentes -- mismo umbral con el que se generó la
# evidencia de cobertura ya verificada (18 países, ver docstring del módulo).
UMBRAL_SEMANAS_MINIMAS = 45

# SEAS (temporada de 3 letras) -> mes central. Igual que cargar_oni.py.
MES_CENTRAL = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}

# Un punto representativo por país. Deliberadamente NO es el centroide
# geométrico de cada país -- para países grandes (Brasil, México, EEUU) un
# solo punto es una simplificación fuerte, declarada explícitamente en el
# informe, no escondida. Para Estados Unidos se usa un punto en Florida (no
# el centroide del país): es donde ocurre la transmisión real de dengue.
CENTROIDES = {
    "EL SALVADOR": (13.79, -88.90), "GUATEMALA": (15.70, -90.36),
    "HONDURAS": (14.75, -86.24), "NICARAGUA": (12.87, -85.21),
    "COSTA RICA": (9.75, -83.75), "PANAMA": (8.54, -80.78),
    "MEXICO": (23.63, -102.55), "COLOMBIA": (4.57, -74.30),
    "ECUADOR": (-1.83, -78.18), "BOLIVIA": (-16.29, -63.59),
    "BRAZIL": (-14.24, -51.93), "DOMINICAN REPUBLIC": (18.74, -70.16),
    "JAMAICA": (18.11, -77.30), "PUERTO RICO": (18.22, -66.59),
    "BARBADOS": (13.19, -59.54), "BERMUDA": (32.32, -64.76),
    "UNITED STATES OF AMERICA": (27.99, -81.76),  # Florida: donde hay dengue
    "VIRGIN ISLANDS (US)": (18.34, -64.90),
}


# ---------------------------------------------------------------- casos ---
def leer_casos(ruta_csv: Path):
    """Lee Temporal_extract_PAHO_V1_3.csv filtrando S_res=Admin0, T_res=Week,
    años en ANIOS. La columna Year es año calendario, no epidemiológico, y no
    hay número de semana explícito -- se numeran 1..N por orden cronológico
    de calendar_start_date dentro de cada país-año (misma regla que ya rige
    el loader de OpenDengue: no se recalcula con `epiweeks` por separado).

    Devuelve (serie, n_semanas, fechas_semana, completos):
      serie[pais][anio][semana] = dengue_total
      n_semanas[pais][anio] = cantidad real de semanas presentes ese año
      fechas_semana[(pais, anio, semana)] = calendar_start_date (str)
      completos = países con las 11 años >= UMBRAL_SEMANAS_MINIMAS semanas
    """
    bruto: dict[str, dict[int, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    with open(ruta_csv, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if row["S_res"] != "Admin0" or row["T_res"] != "Week":
                continue
            try:
                anio = int(row["Year"])
                valor = float(row["dengue_total"])
            except (ValueError, TypeError):
                continue
            if anio in ANIOS:
                bruto[row["adm_0_name"]][anio][row["calendar_start_date"]] = valor

    serie: dict[str, dict[int, dict[int, float]]] = {}
    fechas_semana: dict[tuple[str, int, int], str] = {}
    n_semanas: dict[str, dict[int, int]] = defaultdict(dict)
    for pais, anios_dict in bruto.items():
        serie[pais] = {}
        for anio, fechas_valores in anios_dict.items():
            ordenado = sorted(fechas_valores.items())  # por calendar_start_date
            serie[pais][anio] = {i + 1: v for i, (_f, v) in enumerate(ordenado)}
            n_semanas[pais][anio] = len(ordenado)
            for i, (fecha, _v) in enumerate(ordenado):
                fechas_semana[(pais, anio, i + 1)] = fecha

    completos = sorted(
        p for p in serie
        if sum(1 for a in ANIOS if len(serie[p].get(a, {})) >= UMBRAL_SEMANAS_MINIMAS) == len(ANIOS)
    )
    return serie, n_semanas, fechas_semana, completos


# ---------------------------------------------------------------- clima ---
def _solicitar_con_reintento(params: dict, sesion=requests) -> dict:
    """GET a Open-Meteo con reintento por backoff. Open-Meteo salta 429 (límite
    POR MINUTO) con pocas llamadas seguidas aunque la cuota diaria esté lejos
    -- trampa confirmada en vivo con cargar_clima.py. `sesion` se puede
    inyectar con un doble en tests para no depender de la red."""
    for intento in range(1, 6):
        r = sesion.get(ARCHIVE_URL, params=params, timeout=180)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            espera = 15 * intento
            print(f"  429 Too Many Requests -- esperando {espera}s (intento {intento}/5)")
            time.sleep(espera)
            continue
        r.raise_for_status()
    raise SystemExit("Open-Meteo no respondió tras 5 intentos")


def descargar_clima(paises: list[str], destino: Path) -> dict:
    """Una petición multi-ubicación por modelo (dos llamadas HTTP en total),
    igual que cargar_clima.py. era5_land para las 5 variables de superficie,
    era5 para las 2 de precipitación -- era5_land no sirve precipitación,
    nunca best_match/era5_seamless."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    lats = ",".join(f"{CENTROIDES[p][0]:.6f}" for p in paises)
    lons = ",".join(f"{CENTROIDES[p][1]:.6f}" for p in paises)
    salida: dict[str, list[dict]] = {}
    for modelo, variables in (("era5_land", VARIABLES_ERA5_LAND), ("era5", VARIABLES_ERA5)):
        params = {
            "latitude": lats, "longitude": lons,
            "start_date": f"{ANIOS[0] - 1}-01-01", "end_date": f"{ANIOS[-1]}-12-31",
            "daily": ",".join(variables), "models": modelo,
            "timezone": "America/El_Salvador",
        }
        print(f"  Llamando Open-Meteo ({modelo}, {len(variables)} variables, {len(paises)} países)...")
        datos = _solicitar_con_reintento(params)
        respuestas = datos if isinstance(datos, list) else [datos]
        salida[modelo] = respuestas
        print(f"  {modelo}: {len(respuestas)} ubicaciones")
    destino.write_text(json.dumps(salida), encoding="utf-8")
    return salida


def extraer_diario(paises: list[str], bruto: dict) -> dict[tuple[str, str], dict[str, float]]:
    """(país, fecha) -> {variable: valor}. Aplica la guarda de precipitación
    confirmada en vivo: precipitation_hours puede venir 0.0 (no null) cuando
    el modelo no tiene el dato para ese día -- se rechaza precipitation_hours
    de cualquier día donde precipitation_sum venga null en la misma
    respuesta, nunca se confía en precipitation_hours por sí solo."""
    diario: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for modelo, respuestas in bruto.items():
        for pais, resp in zip(paises, respuestas):
            d = resp["daily"]
            fechas = d["time"]
            sum_nula = None
            if "precipitation_sum" in d:
                sum_nula = [v is None for v in d["precipitation_sum"]]
            for var in d:
                if var == "time":
                    continue
                valores = d[var]
                for i, fecha in enumerate(fechas):
                    val = valores[i]
                    if val is None:
                        continue
                    if var == "precipitation_hours" and sum_nula is not None and sum_nula[i]:
                        continue
                    diario[(pais, fecha)][var] = float(val)
    return diario


def descargar_oni() -> dict[tuple[int, int], float]:
    """Devuelve {(año_calendario, mes_calendario): anom}. Descarga directa de
    NOAA, misma lógica que cargar_oni.py -- se re-implementa aquí en vez de
    importar ese script porque cargar_oni.py escribe a Postgres en su flujo
    normal y este experimento no debe tocar la base de datos ni depender de
    que esté levantada."""
    resp = requests.get(ONI_URL, timeout=30)
    resp.raise_for_status()
    anom_por_mes: dict[tuple[int, int], float] = {}
    for linea in resp.text.splitlines()[1:]:
        partes = linea.split()
        if len(partes) != 4:
            continue
        seas, yr, _total, anom = partes
        mes = MES_CENTRAL.get(seas)
        if mes is None:
            continue
        anom_por_mes[(int(yr), mes)] = float(anom)
    return anom_por_mes


def construir_clima_semanal(
    diario: dict[tuple[str, str], dict[str, float]],
    fechas_semana: dict[tuple[str, int, int], str],
    oni_por_mes: dict[tuple[int, int], float] | None,
) -> dict[tuple[str, int, int], dict[str, float]]:
    """Diario -> semanal: media para variables de estado, suma para las
    acumulativas (mismo criterio que cargar_clima.py). La semana se alinea
    contra calendar_start_date de OpenDengue -- no se recalcula por separado.
    Exige las 7 variables climáticas completas (>=5/7 días cada una) para
    aceptar la celda; oni_anom (si se pide) se añade aparte, por mes
    calendario, sin exigir cobertura diaria porque no es un dato diario."""
    import datetime as dt

    ACUMULATIVAS = {"precipitation_sum", "precipitation_hours"}
    semanal: dict[tuple[str, int, int], dict[str, float]] = {}
    for (pais, anio, semana), inicio in fechas_semana.items():
        d0 = dt.date.fromisoformat(inicio)
        dias = [(pais, (d0 + dt.timedelta(days=k)).isoformat()) for k in range(7)]
        acc: dict[str, list[float]] = defaultdict(list)
        for clave in dias:
            for var, val in diario.get(clave, {}).items():
                acc[var].append(val)

        fila: dict[str, float] = {}
        for var in VARIABLES_CLIMA:
            vals = acc.get(var, [])
            if len(vals) < 5:
                continue
            fila[var] = sum(vals) if var in ACUMULATIVAS else sum(vals) / len(vals)
        if len(fila) != len(VARIABLES_CLIMA):
            continue

        if oni_por_mes is not None:
            clave_mes = (d0.year, d0.month)
            anom = oni_por_mes.get(clave_mes)
            if anom is None:
                continue
            fila["oni_anom"] = anom

        semanal[(pais, anio, semana)] = fila
    return semanal


# ------------------------------------------------------------ rezagos -----
def retroceder_semana(
    pais: str, anio: int, semana: int, pasos: int,
    n_semanas: dict[str, dict[int, int]],
) -> tuple[int, int] | None:
    """Retrocede `pasos` semanas desde (anio, semana), cruzando el límite de
    año con el número REAL de semanas del año anterior para ESE país (que
    varía: 51, 52 o 53). None si el año anterior no tiene datos.

    Corrige el bug del script de referencia que acompañó esta tarea: ahí el
    retroceso usaba `len([... for c in clima if ...]) or 52` -- contaba
    cuántas celdas de *clima ya filtrado* existían para ese país-año, que no
    es lo mismo que el número real de semanas del calendario (cambia con la
    cobertura climática, no con el calendario), y además caía a un `52` fijo
    cuando esa cuenta daba cero. Aquí se usa el conteo real derivado de la
    propia serie de casos (n_semanas), no de la disponibilidad de clima."""
    a, s = anio, semana
    for _ in range(pasos):
        s -= 1
        if s < 1:
            a -= 1
            total = n_semanas.get(pais, {}).get(a)
            if total is None:
                return None
            s = total
    return (a, s)


def construir_features_semana(
    pais: str, anio: int, semana: int,
    clima_semanal: dict[tuple[str, int, int], dict[str, float]],
    n_semanas: dict[str, dict[int, int]],
    variables: list[str],
) -> dict[str, float] | None:
    """Rezagos LAGS y media móvil VENTANAS_MEDIA_MOVIL, idénticos a
    producción. Los rezagos climáticos SÍ cruzan el límite de año (el clima
    es un proceso físico continuo) -- distinto de la línea base de
    percentiles de la etiqueta, que nunca ve el año que está etiquetando
    (esa regla se aplica en construir_dataset, vía construir_pool). None si
    falta cualquier semana requerida -- no se interpola ni se rellena."""
    max_pasos = max(max(LAGS), max(VENTANAS_MEDIA_MOVIL))
    celdas: dict[int, dict[str, float] | None] = {}
    for pasos in range(1, max_pasos + 1):
        objetivo = retroceder_semana(pais, anio, semana, pasos, n_semanas)
        celdas[pasos] = clima_semanal.get((pais, *objetivo)) if objetivo is not None else None

    feat: dict[str, float] = {}
    for variable in variables:
        for lag in LAGS:
            c = celdas[lag]
            if c is None or variable not in c:
                return None
            feat[f"{variable}_lag{lag}"] = c[variable]
        for ventana in VENTANAS_MEDIA_MOVIL:
            vals = []
            for pasos in range(1, ventana + 1):
                c = celdas[pasos]
                if c is None or variable not in c:
                    return None
                vals.append(c[variable])
            feat[f"{variable}_media_movil{ventana}"] = sum(vals) / len(vals)
    return feat


# ------------------------------------------------------------- dataset ----
def construir_dataset(
    paises: list[str],
    serie: dict[str, dict[int, dict[int, float]]],
    n_semanas: dict[str, dict[int, int]],
    clima_semanal: dict[tuple[str, int, int], dict[str, float]],
    incluir_oni: bool,
) -> tuple[list[dict], dict[str, int]]:
    variables = VARIABLES_CLIMA + (["oni_anom"] if incluir_oni else [])
    canal_endemico.ANIOS_BASE = ANIOS  # ver construir_dataset_modelado.py: mismo patrón de reuso

    contadores = {
        "total_candidatas": 0,
        "descartadas_sin_suficiencia_etiqueta": 0,
        "descartadas_sin_historia_climatica": 0,
        "filas_finales": 0,
    }
    filas: list[dict] = []
    for pais in paises:
        for anio in ANIOS:
            if anio not in serie[pais]:
                continue
            for semana, valor in sorted(serie[pais][anio].items()):
                contadores["total_candidatas"] += 1

                pool, anios_presentes = construir_pool(serie[pais], anio, semana)
                suficiente = (
                    len(pool) >= canal_endemico.PISO_OBSERVACIONES
                    and anios_presentes >= canal_endemico.PISO_ANIOS_MIN
                )
                if not suficiente:
                    contadores["descartadas_sin_suficiencia_etiqueta"] += 1
                    continue

                c1 = percentil(pool, 0.75)
                c2 = percentil(pool, 0.90)
                etiqueta = "alto" if valor > c2 else ("medio" if valor > c1 else "bajo")

                feats = construir_features_semana(pais, anio, semana, clima_semanal, n_semanas, variables)
                if feats is None:
                    contadores["descartadas_sin_historia_climatica"] += 1
                    continue

                filas.append({
                    "pais": pais, "anio": anio, "semana_epi": semana,
                    "etiqueta_riesgo": etiqueta, **feats,
                })
                contadores["filas_finales"] += 1
    return filas, contadores


# ------------------------------------------------------------ evaluación --
def columnas_feature(fila: dict) -> list[str]:
    return sorted(k for k in fila if k not in ("pais", "anio", "semana_epi", "etiqueta_riesgo"))


def preparar_matrices(filas: list[dict], cols: list[str]) -> tuple[np.ndarray, list[str]]:
    X = np.array([[fila[c] for c in cols] for fila in filas])
    y = [fila["etiqueta_riesgo"] for fila in filas]
    return X, y


def evaluar(train: list[dict], test: list[dict], cols: list[str], semilla: int) -> dict | None:
    """Un modelo (RandomForest, hiperparámetros idénticos a producción salvo
    la semilla) contra la línea base climatológica (reutilizada de
    entrenar_clasificador.py, sin reescribirla). None si el conjunto de
    prueba no tiene ninguna semana 'alto' real -- no evaluable, igual que en
    producción."""
    if not any(f["etiqueta_riesgo"] == "alto" for f in test):
        return None

    X_train, y_train = preparar_matrices(train, cols)
    X_test, y_test = preparar_matrices(test, cols)

    modelo = RandomForestClassifier(n_estimators=300, random_state=semilla, class_weight="balanced")
    modelo.fit(X_train, y_train)
    y_pred_modelo = modelo.predict(X_test).tolist()
    met_modelo = metricas(y_test, y_pred_modelo)

    y_pred_clima = baseline_climatologica(train, test)
    met_clima = metricas(y_test, y_pred_clima)

    supera = (
        met_modelo["f1_macro"] > met_clima["f1_macro"]
        and met_modelo["recall_alto"] is not None
        and met_clima["recall_alto"] is not None
        and met_modelo["recall_alto"] > met_clima["recall_alto"]
    )
    return {"modelo": met_modelo, "climatologica": met_clima, "supera": supera}


def correr_modo_el_salvador(filas: list[dict], cols: list[str], semillas: list[int]) -> dict:
    resultados: dict[int, list[dict]] = {}
    for anio in ANIOS:
        test = [f for f in filas if f["pais"] == "EL SALVADOR" and f["anio"] == anio]
        if not test:
            continue
        train = [f for f in filas if f["pais"] != "EL SALVADOR"]
        corridas = []
        for semilla in semillas:
            r = evaluar(train, test, cols, semilla)
            if r is not None:
                corridas.append({"semilla": semilla, **r})
        if corridas:
            resultados[anio] = corridas
    return resultados


def correr_modo_regional(filas: list[dict], cols: list[str], semillas: list[int]) -> dict:
    resultados: dict[int, list[dict]] = {}
    for anio in ANIOS:
        test = [f for f in filas if f["anio"] == anio]
        if not test:
            continue
        train = [f for f in filas if f["anio"] != anio]
        corridas = []
        for semilla in semillas:
            r = evaluar(train, test, cols, semilla)
            if r is not None:
                corridas.append({"semilla": semilla, **r})
        if corridas:
            resultados[anio] = corridas
    return resultados


def imprimir_resultados(resultados: dict, nombre_modo: str) -> None:
    print(f"\n=== {nombre_modo} ===")
    for anio, corridas in resultados.items():
        n_semillas = len(corridas)
        n_supera = sum(1 for c in corridas if c["supera"])
        primero = corridas[0]
        f1m, rm = primero["modelo"]["f1_macro"], primero["modelo"]["recall_alto"]
        f1b, rb = primero["climatologica"]["f1_macro"], primero["climatologica"]["recall_alto"]
        etiqueta_supera = (
            f"SUPERA en {n_supera}/{n_semillas} semillas" if n_semillas > 1
            else ("SUPERA" if primero["supera"] else "no supera")
        )
        print(
            f"  {anio}  modelo F1={f1m:.3f} rec_alto={rm:.3f}  |  "
            f"base F1={f1b:.3f} rec_alto={rb:.3f}  {etiqueta_supera}"
        )


def volcar_resultados(resultados: dict, sufijo: str) -> Path:
    INTERIM_ROOT.mkdir(parents=True, exist_ok=True)
    path = INTERIM_ROOT / f"resultados{sufijo}.json"
    serializable = {
        str(anio): [
            {"semilla": c["semilla"], "supera": c["supera"], "modelo": c["modelo"], "climatologica": c["climatologica"]}
            for c in corridas
        ]
        for anio, corridas in resultados.items()
    }
    path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    return path


# ------------------------------------------------------------------ main --
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, required=True, help="Ruta a Temporal_extract_PAHO_V1_3.csv")
    ap.add_argument("--modo", choices=["el-salvador", "regional"], default="el-salvador")
    ap.add_argument("--incluir-oni", action="store_true")
    ap.add_argument("--semillas", type=str, default="42", help="Lista separada por comas, ej. '42' o '0,1,2,3,4,5,6,7,8,9'")
    ap.add_argument("--cache-clima", type=Path, default=INTERIM_ROOT / "clima_multipais.json")
    ap.add_argument("--saltar-descarga", action="store_true")
    args = ap.parse_args()

    semillas = [int(s) for s in args.semillas.split(",")]

    print("Leyendo casos...")
    serie, n_semanas, fechas_semana, completos = leer_casos(args.csv)
    paises = [p for p in completos if p in CENTROIDES]
    print(f"Países con serie completa {ANIOS[0]}-{ANIOS[-1]} y centroide definido: {len(paises)}")
    if len(paises) != 18:
        print(
            f"AVISO: se esperaban 18 países (evidencia previa) y se obtuvieron {len(paises)}. "
            "Revisar antes de seguir -- ver sección 2 de la tarea."
        )

    # Verificación de cobertura contra la evidencia previa (sección 2 de la tarea).
    total_filas_casos = sum(len(serie[p].get(a, {})) for p in paises for a in ANIOS)
    print(f"Verificación de cobertura de casos (sin clima todavía): {total_filas_casos} filas país-semana "
          f"crudas sobre {len(paises)} países.")

    if args.saltar_descarga and args.cache_clima.exists():
        print(f"Usando caché de clima: {args.cache_clima}")
        bruto = json.loads(args.cache_clima.read_text(encoding="utf-8"))
    else:
        print("Descargando clima de Open-Meteo (2 peticiones multi-ubicación)...")
        bruto = descargar_clima(paises, args.cache_clima)

    diario = extraer_diario(paises, bruto)
    oni_por_mes = descargar_oni() if args.incluir_oni else None
    if args.incluir_oni:
        print(f"ONI descargado: {len(oni_por_mes)} valores mensuales.")

    clima_semanal = construir_clima_semanal(diario, fechas_semana, oni_por_mes)
    print(f"Celdas país-semana con clima completo: {len(clima_semanal)}")

    faltantes_por_pais: dict[str, int] = defaultdict(int)
    totales_por_pais: dict[str, int] = defaultdict(int)
    for clave in fechas_semana:
        pais = clave[0]
        totales_por_pais[pais] += 1
        if clave not in clima_semanal:
            faltantes_por_pais[pais] += 1
    paises_sin_clima = [
        p for p in paises
        if totales_por_pais[p] and faltantes_por_pais[p] == totales_por_pais[p]
    ]
    if paises_sin_clima:
        print(
            f"AVISO: {len(paises_sin_clima)} país(es) con 0% de cobertura climática de superficie "
            f"(era5_land devuelve null en las 5 variables para el centroide elegido -- probable "
            f"hueco de máscara tierra/mar del reanálisis en islas pequeñas): {', '.join(paises_sin_clima)}. "
            "Quedan fuera del dataset de modelado por completo, no solo de algunas semanas."
        )

    filas, contadores = construir_dataset(paises, serie, n_semanas, clima_semanal, args.incluir_oni)
    print(f"\nSemanas candidatas evaluadas: {contadores['total_candidatas']}")
    print(f"  Descartadas por piso de suficiencia de la etiqueta: {contadores['descartadas_sin_suficiencia_etiqueta']}")
    print(f"  Descartadas por falta de historia climática: {contadores['descartadas_sin_historia_climatica']}")
    print(f"  Filas finales: {contadores['filas_finales']}")

    total_alto = sum(1 for f in filas if f["etiqueta_riesgo"] == "alto")
    anios_pais_con_alto = len({
        (f["pais"], f["anio"]) for f in filas if f["etiqueta_riesgo"] == "alto"
    })
    print(f"\nDataset final: {len(filas)} filas, {total_alto} 'alto' ({total_alto / len(filas):.1%}), "
          f"{anios_pais_con_alto} años-país con >=1 semana 'alto'.")

    if not filas:
        raise SystemExit("Dataset vacío -- revisar clima/casos antes de reintentar.")

    cols = columnas_feature(filas[0])
    print(f"Predictores: {len(cols)} ({', '.join(cols)})")

    if args.modo == "el-salvador":
        print("\nMODO EL SALVADOR -- entrena con los otros 17 países, prueba en SV año por año")
        print("(la pregunta que importa para el entregable actual)")
        resultados = correr_modo_el_salvador(filas, cols, semillas)
        imprimir_resultados(resultados, "el-salvador")
        sufijo = "_el-salvador" + ("_oni" if args.incluir_oni else "")
    else:
        print("\nMODO REGIONAL -- leave-one-year-out sobre los 18 países")
        print("(entregable distinto: clasificador regional, no de El Salvador)")
        resultados = correr_modo_regional(filas, cols, semillas)
        imprimir_resultados(resultados, "regional" + (" + ONI" if args.incluir_oni else ""))
        sufijo = "_regional" + ("_oni" if args.incluir_oni else "")

    path = volcar_resultados(resultados, sufijo)
    print(f"\nResultados -> {path}")


if __name__ == "__main__":
    sys.exit(main())
