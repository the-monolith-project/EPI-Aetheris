import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import psycopg2

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
    clasificación de riesgo: eso sigue sin un corte de percentil decidido
    (docs/contexto/02-decisiones-abiertas.md, punto A)."""
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