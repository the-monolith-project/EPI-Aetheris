# EPI Aethery

Sistema de predicción epidemiológica para El Salvador. Piloto inicial con
dengue; arquitectura agnóstica al tipo de evento y región.

## Stack

- **Backend:** FastAPI + psycopg2 (PostgreSQL raw SQL)
- **Frontend:** Astro 4 + TypeScript + Leaflet
- **Base de datos:** PostgreSQL 15
- **Infra:** Docker Compose (3 servicios)

## Requisitos

- Docker + Docker Compose
- Git

## Clonar

```bash
git clone git@github.com:genmath26-bit/PropuestaEstructuraMonolithProject.git
cd EPI_Aethery
```

## Inicio rápido

```bash
cp .env.example .env
docker compose up -d
```

- API: http://localhost:8000
- Web: http://localhost:4321
- DB: localhost:5432

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `POSTGRES_USER` | Usuario de BD | `aethery_user` |
| `POSTGRES_PASSWORD` | Contraseña de BD | `aethery_secure_password` |
| `POSTGRES_DB` | Nombre de la BD | `epi_aethery` |
| `POSTGRES_HOST` | Host de la BD | `db` |
| `POSTGRES_PORT` | Puerto de la BD | `5432` |

## Estructura

```
backend/api/       → FastAPI app (punto de entrada: api/main.py:app)
backend/ingestion/ → pipeline de ingesta (no implementado)
backend/model/     → modelos de predicción (no implementado)
web/               → frontend Astro
db/migrations/     → schema SQL (cargado automáticamente al iniciar db)
docs/adr/          → Architecture Decision Records (pendiente)
```
