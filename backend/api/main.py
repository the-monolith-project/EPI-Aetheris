import csv
import json
import os
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import psycopg2

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
    "individualmente. La capa departamental descriptiva aún no está disponible "
    "(el parser de producción de boletines MINSAL, tarjeta 22, sigue sin construirse)."
)

app = FastAPI(
    title="EPI-Aetheris API",
    description="API para ingesta, predicción y consulta de datos epidemiológicos",
    version="0.1.0"
)

# El frontend Astro corre en un origen distinto (puerto 4321) al de esta API
# (puerto 8000) tanto en desarrollo local como dentro de docker-compose.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:4321").split(","),
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
                SELECT s.fecha_inicio, c.anio, c.conteo
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
        {"semana_inicio": fecha_inicio.isoformat(), "anio": anio, "conteo": conteo}
        for fecha_inicio, anio, conteo in filas
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