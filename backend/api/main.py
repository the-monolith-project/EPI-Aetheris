import os
from fastapi import FastAPI, HTTPException
import psycopg2

app = FastAPI(
    title="EPI-Aetheris API",
    description="API para ingesta, predicción y consulta de datos epidemiológicos",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    """Endpoint de comprobación de salud que valida la conexión directa a PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "db"),
            database=os.getenv("POSTGRES_DB", "epi_aetheris"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
        conn.close()
        return {
            "status": "ok",
            "service": "backend",
            "database": "connected"
        }
    except Exception:
        raise HTTPException(
            status_code=500, 
            detail="Error de conexión a la base de datos."
        )