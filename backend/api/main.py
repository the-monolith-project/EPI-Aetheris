import csv
import json
import os
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import psycopg2

from .analisis import (
    ANIOS_ANALISIS_DENGUE,
    cargar_procedencia_observacion,
    construir_dataset_dengue,
)
from .idoneidad import (
    ANIOS_CLIMA,
    calcular_baseline_semana,
    calcular_serie_iv,
    calcular_sigma,
    cargar_clima_departamento,
    cargar_clima_departamentos,
    percentil,
)
from .presion import (
    ANIOS_BASE as ANIOS_BASE_PRESION,
    SERIES as SERIES_PRESION,
    calcular_presion,
    cargar_casos_departamentales,
    cargar_casos_departamento,
)
from .ira import (
    AVISO_HONESTIDAD_IRA,
    cargar_ira_departamental,
    cargar_ira_departamento_temporal,
)

# Artefactos de la tarjeta 23/24 -- generados por
# backend/ingestion/construir_dataset_modelado.py y entrenar_clasificador.py,
# leidos aqui via el mismo bind mount de ./backend (docker-compose.yml). No
# hay tabla de predicciones en el esquema (punto G de las decisiones
# abiertas, sin resolver) -- esta es la opcion "on-demand": recalcula desde
# el dataset ya generado en vez de persistir nada nuevo en Postgres.
INGESTION_DIR = Path(__file__).parent.parent / "ingestion"
DATASET_RIESGO_PATH = INGESTION_DIR / "data" / "interim" / "dataset_modelado" / "dataset_modelado.csv"
MODELO_PATH = INGESTION_DIR / "data" / "interim" / "modelo" / "clasificador_riesgo_nacional_v1.joblib"
METRICAS_MODELO_PATH = INGESTION_DIR / "data" / "interim" / "modelo" / "metricas_modelo.json"

AVISO_HONESTIDAD_RIESGO_NACIONAL = (
    "Esta clasificación es a nivel NACIONAL, entrenada sobre la serie agregada de "
    "El Salvador (pivote 'Opción C'). No representa riesgo por departamento -- el mapa "
    "no debe interpretarse como si cada departamento tuviera este nivel de riesgo "
    "individualmente. La coropleta departamental del mapa es una capa DESCRIPTIVA "
    "aparte (volumen de casos MINSAL, no riesgo) -- estos datos todavía no alimentan "
    "ningún clasificador."
)

app = FastAPI(
    title="EPI-Aetheris API",
    description="API para ingesta, predicción y consulta de datos epidemiológicos",
    version="0.1.0"
)

# El frontend Astro corre en un origen distinto (puerto 4321) al de esta API
# (puerto 8000) tanto en desarrollo local como dentro de docker-compose.
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:4321").split(",")
    if origin.strip()
]

if "*" in cors_origins:
    raise ValueError("CORS_ALLOWED_ORIGINS must not contain '*' for security reasons.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _conectar():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "db"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Allow inline styles/scripts and jsdelivr to ensure FastAPI Swagger UI works.
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com"
        return response

app.add_middleware(SecurityHeadersMiddleware)

@app.get("/health")
def health_check():
    """Endpoint de comprobación de salud que valida la conexión directa a PostgreSQL."""
    try:
        conn = _conectar()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
        conn.close()
        return {
            "status": "ok",
            "service": "backend",
            "database": "connected"
        }
    except Exception:
        # Security: Do not log or leak the original connection error string to clients.
        # Original error can contain credentials if improperly handled by the driver.
        raise HTTPException(
            status_code=500,
            detail="Error de conexión a la base de datos"
        )


@app.get("/api/casos-nacional")
def casos_nacional():
    """Serie semanal nacional de OpenDengue ya cargada (clasificacion='total',
    fuente opendengue_v1_3). Es la única variable objetivo cargada hasta ahora
    -- ver docs/contexto/01-decisiones-cerradas.md, pivote "Opción C". No es
    clasificación de riesgo -- para eso ver /api/riesgo-nacional."""
    try:
        conn = _conectar()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.fecha_inicio, c.anio, c.semana_epi, c.conteo
                FROM casos_epidemiologicos c
                JOIN regiones r ON r.id = c.region_id
                JOIN fuentes_datos f ON f.id = c.fuente_id
                JOIN semanas_epidemiologicas s
                    ON s.anio = c.anio AND s.semana_epi = c.semana_epi
                WHERE r.codigo = 'SV'
                  AND c.clasificacion = 'total'
                  AND f.codigo = 'opendengue_v1_3'
                ORDER BY c.anio, c.semana_epi
                """
            )
            filas = cursor.fetchall()
        conn.close()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error de conexión a la base de datos"
        )

    return [
        {
            "semana_inicio": fecha_inicio.isoformat(),
            "anio": anio,
            "semana_epi": semana_epi,
            "conteo": conteo,
        }
        for fecha_inicio, anio, semana_epi, conteo in filas
    ]


_modelo_cache = None


def _cargar_modelo():
    global _modelo_cache
    if _modelo_cache is None:
        if not MODELO_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail="Modelo no disponible -- correr entrenar_clasificador.py (tarjeta 24) primero.",
            )
        _modelo_cache = joblib.load(MODELO_PATH)
    return _modelo_cache


@app.get("/api/riesgo-nacional")
def riesgo_nacional(anio: int | None = None, semana: int | None = None):
    """Clasificación de riesgo NACIONAL para una semana epidemiológica dada
    (tarjetas 23/24/25, primera versión: semana fija, colores planos --
    selector de semanas viene después). Recalcula on-demand desde el dataset
    ya generado, no persiste nada nuevo en Postgres (ver comentario junto a
    DATASET_RIESGO_PATH).

    Sin parámetros, devuelve la última semana disponible del dataset (fin
    de 2023, año de prueba de la tarjeta 24) -- el sistema no tiene forma
    de verificar en vivo lo que predice, no hay fuente departamental
    automatizable después de 2023 (ver docs/contexto, punto F).
    """
    if not DATASET_RIESGO_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Dataset de modelado no disponible -- correr construir_dataset_modelado.py (tarjeta 23) primero.",
        )

    with open(DATASET_RIESGO_PATH, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    if anio is None or semana is None:
        fila = max(filas, key=lambda r: (int(r["anio"]), int(r["semana_epi"])))
    else:
        coincidencias = [r for r in filas if int(r["anio"]) == anio and int(r["semana_epi"]) == semana]
        if not coincidencias:
            raise HTTPException(
                status_code=404,
                detail=f"No hay datos de modelado para año={anio}, semana={semana}.",
            )
        fila = coincidencias[0]

    modelo_paquete = _cargar_modelo()
    modelo = modelo_paquete["modelo"]
    columnas_feature = modelo_paquete["columnas_feature"]
    clases = modelo_paquete["clases"]

    X = [[float(fila[c]) for c in columnas_feature]]
    etiqueta_predicha = modelo.predict(X)[0]
    probabilidades = dict(zip(modelo.classes_, modelo.predict_proba(X)[0].tolist()))

    metricas_modelo = None
    if METRICAS_MODELO_PATH.exists():
        metricas_modelo = json.loads(METRICAS_MODELO_PATH.read_text(encoding="utf-8"))

    return {
        "anio": int(fila["anio"]),
        "semana_epi": int(fila["semana_epi"]),
        "etiqueta_predicha": etiqueta_predicha,
        "etiqueta_real": fila["etiqueta_riesgo"],
        "probabilidades": {clase: round(probabilidades.get(clase, 0.0), 4) for clase in clases},
        "casos_observados": float(fila["casos"]),
        "metricas_modelo": metricas_modelo,
        "aviso": AVISO_HONESTIDAD_RIESGO_NACIONAL,
    }


AVISO_HONESTIDAD_CASOS_DEPARTAMENTALES = (
    "Capa DESCRIPTIVA -- casos probables/confirmados desacumulados de boletines MINSAL "
    "(2018-2023, con huecos reales entre boletines). No es una clasificación de riesgo: "
    "el color representa volumen de casos acumulado en la ventana cargada, no un nivel de "
    "riesgo por departamento. El clasificador de esta primera entrega es nacional (ver "
    "/api/riesgo-nacional) -- estos datos NO alimentan ningún modelo todavía."
)


@app.get("/api/casos-departamentales")
def casos_departamentales():
    """Capa descriptiva del mapa (tarjeta 25) -- casos MINSAL desacumulados
    (tarjeta 22) sumados por departamento en toda la ventana cargada
    (2018-2023, sin 2020 ni 2024+ porque no hay boletín automatizable desde
    entonces). Se agrega el acumulado completo, no una sola semana: con
    87-93% de celdas departamento-semana en cero (ver
    docs/contexto/03-fuentes-de-datos.md), una sola semana suele salir casi
    vacía y no representa bien la distribución real -- esto es una elección
    de presentación, no una decisión de equipo cerrada."""
    try:
        conn = _conectar()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    r.nombre,
                    r.codigo,
                    sum(c.conteo) FILTER (WHERE c.clasificacion = 'probable') AS probable_total,
                    sum(c.conteo) FILTER (WHERE c.clasificacion = 'confirmado') AS confirmado_total,
                    count(DISTINCT c.anio || '-' || c.semana_epi) FILTER (WHERE c.clasificacion = 'probable') AS semanas_con_dato_probable,
                    min(c.anio) AS primer_anio,
                    max(c.anio) AS ultimo_anio
                FROM regiones r
                LEFT JOIN casos_epidemiologicos c
                    ON c.region_id = r.id
                    AND c.fuente_id = (SELECT id FROM fuentes_datos WHERE codigo = 'minsal_pdf')
                WHERE r.nivel_admin = 1
                GROUP BY r.nombre, r.codigo
                ORDER BY r.nombre
                """
            )
            filas = cursor.fetchall()
        conn.close()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Error de conexión a la base de datos"
        )

    return {
        "departamentos": [
            {
                "nombre": nombre,
                "codigo": codigo,
                "probable_total": int(probable_total) if probable_total is not None else 0,
                "confirmado_total": int(confirmado_total) if confirmado_total is not None else 0,
                "semanas_con_dato_probable": int(semanas_con_dato) if semanas_con_dato is not None else 0,
                "primer_anio": primer_anio,
                "ultimo_anio": ultimo_anio,
            }
            for nombre, codigo, probable_total, confirmado_total, semanas_con_dato, primer_anio, ultimo_anio in filas
        ],
        "aviso": AVISO_HONESTIDAD_CASOS_DEPARTAMENTALES,
    }


# ---------------------------------------------------------------------------
# "Camino Ancho" -- Módulo 1 (idoneidad biofísica Iv) y Módulo 2 (anomalía
# climática continua). Ver backend/api/idoneidad.py para las fórmulas y su
# procedencia (duplicadas literalmente desde
# backend/ingestion/validar_leadtime_camino_ancho.py, experimento ya
# validado en docs/experimento-validacion-leadtime-camino-ancho.md).
#
# La validación empírica descartó la tesis de "ventana de anticipación"
# (lead time) -- por eso estos endpoints NO exponen alerta binaria, NO
# exponen ningún campo de lead time, y NO usan lenguaje de anticipación en
# ningún lado. Solo Iv y un Z-score continuo (sigma), descriptivos.
# ---------------------------------------------------------------------------

AVISO_HONESTIDAD_IDONEIDAD = (
    "Índice de idoneidad biofísica (Iv) para el vector Aedes aegypti, calculado a partir de "
    "clima ERA5-Land/ERA5 (temperatura, precipitación acumulada a 2 semanas, humedad relativa). "
    "NO es una predicción de casos ni una alerta -- una validación empírica retrospectiva "
    "(docs/experimento-validacion-leadtime-camino-ancho.md) encontró que este índice NO anticipa "
    "de forma medible y consistente el ascenso real de casos, así que esa tesis fue retirada. "
    "El componente de humedad relativa (f_H) es una estimación propia del equipo, sin cita "
    "bibliográfica. El 'anomaly_sigma' es un Z-score continuo contra el histórico del propio "
    "departamento/semana -- no implica alerta ni umbral alguno; un valor alto no es, por sí "
    "mismo, evidencia de brote."
)


@app.get("/api/v1/spatial/current")
def idoneidad_espacial_actual(week: int, year: int):
    """Índice de idoneidad biofísica (Iv) y anomalía climática continua
    (anomaly_sigma), por departamento, para la semana epidemiológica y año
    pedidos. Capa DESCRIPTIVA -- no hay campo de lead time ni de alerta
    binaria (ver AVISO_HONESTIDAD_IDONEIDAD y docstring del módulo
    idoneidad.py: esa tesis fue retirada tras validación empírica).

    El baseline de anomaly_sigma es leave-one-out sobre el corpus climático
    completo 2014-2024 (excluye el propio año pedido de su baseline), misma
    semana exacta, sin ventana de semanas vecinas -- igual método que
    validar_leadtime_camino_ancho.py. Departamentos con menos de 3 años de
    baseline disponible devuelven anomaly_sigma=null, no un valor inventado.
    """
    if not (1 <= week <= 53):
        raise HTTPException(status_code=422, detail="El parámetro 'week' debe estar entre 1 y 53.")

    semanas_necesarias = [week] if week == 1 else [week - 1, week]

    try:
        conn = _conectar()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT codigo, nombre FROM regiones WHERE nivel_admin = 1 ORDER BY nombre")
                departamentos = cursor.fetchall()
            clima = cargar_clima_departamentos(conn, anios=ANIOS_CLIMA, semanas=semanas_necesarias)
        finally:
            conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    serie_iv = calcular_serie_iv(clima)

    resultado = []
    for codigo, nombre in departamentos:
        serie_codigo = serie_iv.get(codigo, {})
        valor = serie_codigo.get(year, {}).get(week)
        if valor is None:
            resultado.append({
                "codigo": codigo,
                "nombre": nombre,
                "iv": None,
                "anomaly_sigma": None,
                "nota": "sin datos climáticos completos para esta semana/año en este departamento",
            })
            continue

        _, mediana, desv = calcular_baseline_semana(serie_codigo, anio_excluir=year, semana=week)
        sigma = calcular_sigma(valor, mediana, desv)
        resultado.append({
            "codigo": codigo,
            "nombre": nombre,
            "iv": round(valor, 4),
            "anomaly_sigma": round(sigma, 4) if sigma is not None else None,
        })

    return {
        "semana_epi": week,
        "anio": year,
        "departamentos": resultado,
        "aviso": AVISO_HONESTIDAD_IDONEIDAD,
    }


# ---------------------------------------------------------------------------
# "Camino Ancho" -- Módulo 3 (presión epidemiológica relativa). Ver
# backend/api/presion.py para la fórmula (cerrada por el coordinador,
# docs/modulo-3-presion-epidemiologica.md) y su procedencia (mismo patrón de
# percentil leave-one-out que corrida_canal_endemico_nacional.py). Igual que
# M1/M2: calculado on-request, nada persistido, sin cambios de esquema.
# ---------------------------------------------------------------------------

AVISO_HONESTIDAD_PRESION = (
    "Presión epidemiológica relativa: percentil del conteo de casos observado "
    "(MINSAL, desacumulado) dentro de la historia del propio departamento "
    "(años base 2018, 2019, 2021, 2022, 2023 -- 2020 excluido por colapso real de "
    "vigilancia durante covid, no por baja transmisión; ventana ±1 semana, "
    "leave-one-out). Es 100% DESCRIPTIVO: dice qué tan inusual es lo ya observado "
    "contra su propia historia, NO predice nada, NO es una alerta ni un nivel de "
    "riesgo. Los cortes P50/P75 son deliberadamente sensibles (decisión del equipo): "
    "'alta' puede aparecer en semanas de años de baja transmisión. 'probable' y "
    "'confirmado' son series separadas y no comparables entre sí. Los huecos "
    "(null + nota) reflejan límites reales de la fuente MINSAL, no errores."
)


@app.get("/api/v1/analisis/dengue")
def dataset_analitico_dengue(year: int):
    """Dataset anual compartido para exploracion descriptiva de dengue.

    Agrega casos MINSAL, M1, M2 y M3 por departamento/semana reutilizando
    sus motores actuales. No persiste resultados ni modifica metodologia.
    """
    if year not in ANIOS_ANALISIS_DENGUE:
        disponibles = ", ".join(str(anio) for anio in ANIOS_ANALISIS_DENGUE)
        raise HTTPException(
            status_code=422,
            detail=f"El parametro 'year' debe ser uno de: {disponibles}.",
        )

    try:
        conn = _conectar()
        try:
            respuesta = construir_dataset_dengue(conn, anio=year)
        finally:
            conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    respuesta["avisos"] = {
        "idoneidad": AVISO_HONESTIDAD_IDONEIDAD,
        "presion": AVISO_HONESTIDAD_PRESION,
    }
    return respuesta


@app.get("/api/v1/analisis/dengue/procedencia")
def procedencia_analitica_dengue(year: int, week: int, dept: str, serie: str):
    """Trazabilidad almacenada de una observacion departamental de dengue."""
    if year not in ANIOS_ANALISIS_DENGUE:
        disponibles = ", ".join(str(anio) for anio in ANIOS_ANALISIS_DENGUE)
        raise HTTPException(
            status_code=422,
            detail=f"El parametro 'year' debe ser uno de: {disponibles}.",
        )
    if not (1 <= week <= 53):
        raise HTTPException(
            status_code=422,
            detail="El parámetro 'week' debe estar entre 1 y 53.",
        )
    if serie not in SERIES_PRESION:
        raise HTTPException(
            status_code=422,
            detail="El parámetro 'serie' debe ser 'probable' o 'confirmado'.",
        )

    try:
        conn = _conectar()
        try:
            respuesta = cargar_procedencia_observacion(
                conn,
                anio=year,
                semana=week,
                departamento_codigo=dept,
                serie=serie,
            )
        finally:
            conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    if respuesta is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe un departamento con código '{dept}'.",
        )
    return respuesta


@app.get("/api/v1/presion/current")
def presion_espacial_actual(week: int, year: int):
    """Presión epidemiológica relativa (Módulo 3) por departamento, para la
    semana epidemiológica y año pedidos, en dos series separadas
    ('probable' y 'confirmado', nunca fusionadas). Estructura espejo de
    /api/v1/spatial/current. Capa DESCRIPTIVA -- ver
    AVISO_HONESTIDAD_PRESION y el docstring de presion.py.

    Celdas sin baseline suficiente (menos de 3 de los 4 años leave-one-out
    con observaciones en la ventana ±1) devuelven percentil=null con nota
    explícita -- nunca un valor inventado ni interpolado.
    """
    if not (1 <= week <= 53):
        raise HTTPException(status_code=422, detail="El parámetro 'week' debe estar entre 1 y 53.")

    # Solo la ventana ±1 de la semana pedida; el baseline necesita los años
    # base completos más el año descrito (si no es uno de ellos).
    semanas_necesarias = [w for w in (week - 1, week, week + 1) if w >= 1]
    anios_necesarios = sorted(set(ANIOS_BASE_PRESION) | {year})

    try:
        conn = _conectar()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT codigo, nombre FROM regiones WHERE nivel_admin = 1 ORDER BY nombre")
                departamentos = cursor.fetchall()
            casos = cargar_casos_departamentales(conn, anios=anios_necesarios, semanas=semanas_necesarias)
        finally:
            conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    resultado = []
    for codigo, nombre in departamentos:
        fila = {"codigo": codigo, "nombre": nombre}
        for serie in SERIES_PRESION:
            fila[serie] = calcular_presion(casos.get(codigo, {}).get(serie, {}), anio=year, semana=week)
        resultado.append(fila)

    return {
        "semana_epi": week,
        "anio": year,
        "departamentos": resultado,
        "aviso": AVISO_HONESTIDAD_PRESION,
    }


@app.get("/api/v1/presion/temporal/{departamento_id}")
def presion_temporal_departamento(departamento_id: str, anio: int):
    """Serie temporal de presión epidemiológica relativa (Módulo 3) de un
    departamento para `anio`, en las dos series separadas. Espejo de
    /api/v1/temporal/{departamento_id}. `departamento_id` es el `codigo`
    de `regiones` (ISO 3166-2:SV, ej. 'SV-SS')."""
    anios_necesarios = sorted(set(ANIOS_BASE_PRESION) | {anio})

    try:
        conn = _conectar()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT codigo, nombre FROM regiones WHERE nivel_admin = 1 AND codigo = %s",
                    (departamento_id,),
                )
                fila_region = cursor.fetchone()
            if fila_region is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"No existe un departamento con código '{departamento_id}'.",
                )
            casos_depto = cargar_casos_departamento(conn, codigo=departamento_id, anios=anios_necesarios)
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    codigo, nombre = fila_region

    # Todas las semanas con alguna observación en cualquier año/serie -- las
    # semanas sin dato del propio `anio` salen con nota, no se omiten.
    todas_las_semanas = sorted({
        semana
        for series in casos_depto.values()
        for semanas in series.values()
        for semana in semanas
    })

    semanas_salida = []
    for semana in todas_las_semanas:
        fila = {"semana_epi": semana}
        for serie in SERIES_PRESION:
            fila[serie] = calcular_presion(casos_depto.get(serie, {}), anio=anio, semana=semana)
        semanas_salida.append(fila)

    return {
        "departamento_codigo": codigo,
        "departamento_nombre": nombre,
        "anio": anio,
        "semanas": semanas_salida,
        "aviso": AVISO_HONESTIDAD_PRESION,
    }


@app.get("/api/v1/temporal/{departamento_id}")
def idoneidad_temporal_departamento(departamento_id: str, anio: int):
    """Serie temporal de un departamento (Módulos 1 y 2): banda histórica
    (P25/mediana/P75 de Iv por semana-del-año, leave-one-out excluyendo
    `anio`) vs. la serie real de `anio`, con anomaly_sigma continuo por
    semana. `departamento_id` es el `codigo` de `regiones` (ISO 3166-2:SV,
    ej. 'SV-SS') -- es el identificador estable que ya usa el resto de la
    API (ver /api/casos-departamentales), no el id numérico interno.

    Capa DESCRIPTIVA -- no hay `estimated_transmission_window_start` ni
    `season_shift_alert` (retirados, ver AVISO_HONESTIDAD_IDONEIDAD)."""
    try:
        conn = _conectar()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT codigo, nombre FROM regiones WHERE nivel_admin = 1 AND codigo = %s",
                    (departamento_id,),
                )
                fila_region = cursor.fetchone()
            if fila_region is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"No existe un departamento con código '{departamento_id}'.",
                )
            clima_depto = cargar_clima_departamento(conn, codigo=departamento_id, anios=ANIOS_CLIMA)
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    codigo, nombre = fila_region

    serie_iv = calcular_serie_iv({codigo: clima_depto})
    serie_codigo = serie_iv.get(codigo, {})

    todas_las_semanas = sorted({
        semana
        for semanas in serie_codigo.values()
        for semana in semanas
    })

    semanas_salida = []
    for semana in todas_las_semanas:
        pool, mediana, desv = calcular_baseline_semana(serie_codigo, anio_excluir=anio, semana=semana)
        iv_real = serie_codigo.get(anio, {}).get(semana)
        sigma = calcular_sigma(iv_real, mediana, desv) if iv_real is not None else None
        semanas_salida.append({
            "semana_epi": semana,
            "iv_real": round(iv_real, 4) if iv_real is not None else None,
            "p25_baseline": round(percentil(pool, 0.25), 4) if pool else None,
            "mediana_baseline": round(mediana, 4) if mediana is not None else None,
            "p75_baseline": round(percentil(pool, 0.75), 4) if pool else None,
            "anomaly_sigma": round(sigma, 4) if sigma is not None else None,
        })

    return {
        "departamento_codigo": codigo,
        "departamento_nombre": nombre,
        "anio": anio,
        "semanas": semanas_salida,
        "aviso": AVISO_HONESTIDAD_IDONEIDAD,
    }


# ---------------------------------------------------------------------------
# Infección Respiratoria Aguda (IRA) -- ADR 0011 (aceptado 2026-08-22).
# Ver backend/api/ira.py: NO es un módulo de "El Camino Ancho" (M1-M4), es
# otro tipo_evento con su propia serie 'notificado', sin Iv/anomalía/presión
# calculados. Cargado por backend/ingestion/cargar_ira.py (2742 filas,
# 2018-2023 sin 2020, 14 departamentos).
# ---------------------------------------------------------------------------


@app.get("/api/ira/departamental")
def ira_departamental():
    """Resumen por departamento del conteo notificado de IRA (total
    acumulado en la ventana cargada, semanas con dato, rango de años) --
    espejo de /api/casos-departamentales. Capa DESCRIPTIVA, ver
    AVISO_HONESTIDAD_IRA."""
    try:
        conn = _conectar()
        try:
            departamentos = cargar_ira_departamental(conn)
        finally:
            conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    return {
        "departamentos": departamentos,
        "aviso": AVISO_HONESTIDAD_IRA,
    }


@app.get("/api/ira/temporal/{departamento_id}")
def ira_temporal_departamento(departamento_id: str):
    """Serie semanal de IRA notificada de un departamento, por año
    (2018-2023, sin 2020). `departamento_id` es el `codigo` de `regiones`
    (ISO 3166-2:SV, ej. 'SV-SS'). Las semanas sin fila son huecos reales de
    la fuente MINSAL (boletín de vacaciones, tabla como imagen, corrección
    retroactiva excluida) -- se devuelven como ausentes, nunca como cero ni
    valor interpolado."""
    try:
        conn = _conectar()
        try:
            serie = cargar_ira_departamento_temporal(conn, codigo=departamento_id)
            if serie is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"No existe un departamento con código '{departamento_id}'.",
                )
            cur = conn.cursor()
            cur.execute(
                "SELECT nombre FROM regiones WHERE nivel_admin = 1 AND codigo = %s",
                (departamento_id,),
            )
            (nombre,) = cur.fetchone()
            cur.close()
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    anios = sorted(serie.keys())
    return {
        "departamento_codigo": departamento_id,
        "departamento_nombre": nombre,
        "anios": anios,
        "series": {
            str(anio): [[semana, valor] for semana, valor in sorted(semanas.items())]
            for anio, semanas in serie.items()
        },
        "aviso": AVISO_HONESTIDAD_IRA,
    }
