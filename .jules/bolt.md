## 2026-08-27 - Compresión Gzip de payloads de la API
**Learning:** FastAPI no comprime respuestas por defecto. EPI-Aetheris sirve series históricas completas (varios años de datos semana a semana por región) como JSON sin paginar para procesamiento en el cliente; sin compresión eso es un cuello de botella de red silencioso.
**Action:** Habilitar `GZipMiddleware` (`minimum_size=1000`) en `backend/api/main.py` y vigilar el tamaño de los endpoints JSON grandes.
