# Limitaciones de la ingesta respiratoria (rama `feature/ingesta-respiratoria`)

Validado 2026-08-28 sobre 264 PDF MINSAL (2018, 2019, 2021, 2022, 2023).

## Qué se puede afirmar

- Neumonías: conteo clínico departamental notificado, acumulado desde SE1 y
  desacumulado a semana. 2,749 filas cargadas. Huecos reales (2019 temprana
  como imagen, vacaciones, 23 correcciones negativas).
- Influenza/VSR/otros/COVID-19: vigilancia **laboratorial nacional**
  (muestras, detecciones, positividad). 3,028 filas. No hay mapa
  departamental porque la fuente no lo publica.
- COVID-19 como fila de la tabla solo en 2023 (rótulo `COVID 19`, no
  SARS-CoV-2). 2020 no se descargó.

## Qué no se puede afirmar

- Predicción, riesgo, causalidad virus → IRA/Neumonías.
- Que un hueco es cero.
- Que la positividad es un conteo de casos.
- Cobertura 2024–2026 (fuera de alcance).
- Tablas-imagen (25 neumonías, 3 virus 2021): sin OCR.

## Cómo reproducir la carga

```text
# corpus (omite PDF ya presentes)
backend/.venv/bin/python backend/ingestion/minsal/descargar_2018.py
# ... 2019, 2021, 2022, 2023

backend/.venv/bin/python backend/ingestion/corrida_respiratorios.py
# aplica 0008 si la base ya existía:
#   docker exec -i aetheris_db psql ... < db/migrations/0008_....sql
# si el volumen no tenía 0007, aplicarla antes (CHECK notificado).

docker exec -w /app aetheris_backend python ingestion/cargar_neumonias.py
docker exec -w /app aetheris_backend python ingestion/cargar_vigilancia_respiratoria.py
```

El seed versionado (ADR 0010) **sí** incluye esta foto (regenerado 2026-09-01):
Neumonías 2.749 filas y vigilancia viral 3.028, más IRA 2.742. Un `git clone`
+ `docker compose up` sobre volumen nuevo aplica `0007`/`0008` y carga esas
filas sin repetir los loaders. Si la base de desarrollo ya existía, el seed
no se reejecuta: hace falta `docker compose down -v` o correr los loaders.
