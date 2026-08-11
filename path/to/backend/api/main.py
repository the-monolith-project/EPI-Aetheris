from fastapi import FastAPI, Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import psycopg2

app = FastAPI(
    title="EPI-Aetheris API",
    description="API para ingesta, predicción y consulta de datos epidemiológicos",
    version="0.1.0"
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
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
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "db"),
            database=os.getenv("POSTGRES_DB"),
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
    except Exception as e:
        # Security: Do not log or leak the original connection error string to clients.
        # Original error can contain credentials if improperly handled by the driver.
        raise HTTPException(
            status_code=500, 
            detail="Error de conexión a la base de datos"
        )
