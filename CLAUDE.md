# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**EPI-Aetheris** is an epidemiological surveillance/prediction system, currently piloted on **dengue in El Salvador**. It ingests case counts and environmental (climate) predictors, aligns them by epidemiological week, and will expose them via API and a Leaflet-based map frontend. The project is early-stage (skeleton scaffolding, single initial commit) — most application logic (ingestion pipeline, prediction, additional API endpoints, frontend views) does not exist yet.

The domain model is deliberately **agnostic to disease type and region**: event types (`tipos_evento`) and regions (`regiones`) are catalogs rather than hardcoded columns, so the schema can extend beyond dengue/El Salvador without migration changes.

## Architecture

Three Docker services orchestrated by `docker-compose.yml`, networked together on `aetheris_network`:

- **`db`** — PostgreSQL 15. Schema is loaded automatically on first container start via `db/migrations/*.sql` mounted into `/docker-entrypoint-initdb.d` (standard Postgres image behavior — SQL files there only run once, on an empty data volume).
- **`backend`** (`./backend`) — Python FastAPI service. Talks to Postgres directly via `psycopg2` (no ORM). Entry point: `backend/api/main.py`. Source is bind-mounted for hot reload (`uvicorn --reload`).
- **`web`** (`./web`) — Astro + Leaflet frontend (map-based UI, not yet built out). Source is bind-mounted; `node_modules` is a separate anonymous volume so container-installed deps don't get clobbered by the host mount.

### Database schema (`db/migrations/0001_init_schema.sql`)

Star-schema-like design around epidemiological weeks:

- `regiones` — hierarchical regions (país → departamento; municipio reserved). `codigo` must match the GeoJSON admin-boundary identifiers used by Leaflet on the frontend — check this before using it as a map join key.
- `tipos_evento` — catalog of disease/event types (currently just `dengue`).
- `fuentes_datos` — data source catalog for provenance (`opendengue_v1_3`, `minsal_pdf`, `open_meteo_era5_land`).
- `semanas_epidemiologicas` — shared epi-week calendar (PAHO/CDC epi week, **not** ISO 8601 week). Populated by a future ingestion-pipeline script, not by this DDL. Both fact tables FK into it.
- `casos_epidemiologicos` — target variable: case counts by region/event/epi-week/classification (`probable` vs `confirmado`). MINSAL bulletins often report probable/confirmado for a case belonging to *different* weeks — these must be inserted as separate rows.
- `variables_ambientales` — predictors (temp, precipitation, humidity, etc.) by region/epi-week, EAV-style (`variable`/`valor` columns rather than one column per variable). Named "ambientales" rather than "climáticas" to leave room for non-climate predictors (e.g. vector index) later.
- `boletines_procesados` — audit log of MINSAL PDF bulletin ingestion, tracking whether departmental sums reconcile against the nationally published total (`validacion_cuadra`). A mismatch should be flagged `revision_manual`, never ingested silently.

Data sources have specific validity windows to be aware of when building the ingestion pipeline: OpenDengue Admin0 covers 2018–2024 (Admin1 only 2000–2009, retrospective validation only); MINSAL PDF covers 2018–2023 excluding 2020, with two table-schema families (`A`: 2018–2020, `B`: 2021–2023).

## Commands

Run everything (Postgres + API + web, with hot reload):

```bash
docker-compose up --build
```

- Backend API: http://localhost:8000 (health check at `/health`)
- Web frontend: http://localhost:4321
- Postgres: localhost:5432 (exposed for direct inspection)

Environment variables come from `.env` (copy from `.env.example`; never commit `.env`).

### Backend (FastAPI) — outside Docker

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

### Web (Astro) — outside Docker

The Dockerfile uses `pnpm` (via Corepack, pinned to v9), so prefer `pnpm` over `npm` for consistency with the container even though no lockfile is committed yet.

```bash
cd web
pnpm install
pnpm dev       # astro dev --host 0.0.0.0, port 4321
pnpm build     # astro build
pnpm preview   # astro preview
```

There is currently no test suite, linter, or CI configuration in this repo.

## Working conventions

- Domain/schema content (table names, columns, comments) is in Spanish, matching the project's source data (MINSAL bulletins, OpenDengue). Keep new schema/domain code consistent with this unless told otherwise.
- Keep the schema's disease/region-agnostic design intact — prefer extending the `tipos_evento`/`regiones`/`fuentes_datos` catalogs over adding disease- or country-specific columns/tables.
- When adding ingestion logic, respect the reconciliation check pattern established by `boletines_procesados`: validate against a published total before treating a bulk load as clean, and mark discrepancies for manual review rather than silently ingesting them.
