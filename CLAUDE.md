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

- `regiones` — hierarchical regions (país → departamento; municipio reserved). `codigo` (ISO 3166-2:SV) does **not** match any identifier property in the geoBoundaries GeoJSON — `shapeISO` comes back empty for this boundary (confirmed 2026-08-05). The map join is resolved by name instead, once, at build time — see `docs/adr/0002-join-mapa-geojson-por-nombre.md` and `backend/ingestion/build_geo_departamentos.py`. Don't re-derive this from scratch; the frontend consumes the already-enriched `web/public/geo/slv-adm1.geojson`, which has `codigo` baked into each feature.
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

For scripts under `backend/ingestion/` that aren't part of the runtime API (geo/coordinate build steps, tests), install dev dependencies too — these are deliberately kept out of `requirements.txt` so the production image doesn't carry test/geometry tooling it never needs:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest backend/ingestion/tests/
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

There is no linter or CI configuration in this repo yet. A narrow pytest suite exists at `backend/ingestion/tests/` (currently: the departamentos catalog vs. migration consistency check) — not the full ingestion pipeline, which still has no coverage.

## Working conventions

- Domain/schema content (table names, columns, comments) is in Spanish, matching the project's source data (MINSAL bulletins, OpenDengue). Keep new schema/domain code consistent with this unless told otherwise.
- Keep the schema's disease/region-agnostic design intact — prefer extending the `tipos_evento`/`regiones`/`fuentes_datos` catalogs over adding disease- or country-specific columns/tables.
- When adding ingestion logic, respect the reconciliation check pattern established by `boletines_procesados`: validate against a published total before treating a bulk load as clean, and mark discrepancies for manual review rather than silently ingesting them.
- **Raw downloaded data is not versioned — `backend/ingestion/data/raw/` is gitignored, on purpose (MINSAL PDFs, OpenDengue CSV).** `backend/ingestion/geo/slv-adm1-source.geojson` and its derived `web/public/geo/slv-adm1.geojson` are a deliberate, narrow exception to that rule, not an oversight — do not gitignore or delete them. Reason: they're small (~100–120 KB total), static (a country's departmental boundaries don't change on any timescale relevant to this project), and without the raw one committed, `backend/ingestion/build_geo_departamentos.py` — and therefore the map — cannot be rebuilt without network access, which breaks the project's zero-cost-reproducibility requirement (see locked decisions). This is the same class of exception as the 2020 training-data exclusion: the fact alone isn't enough context to keep future changes honest, the reasoning has to travel with it. Full detail and the boundary-version pin in `docs/adr/0002-join-mapa-geojson-por-nombre.md`.
