# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**EPI-Aetheris** is an epidemiological surveillance system, piloted on **dengue in El Salvador**. It ingests historical case counts and environmental (climate) predictors, aligns them by epidemiological week, and classifies **outbreak risk (alto / medio / bajo) per department per week**, exposed through a FastAPI backend and a Leaflet map frontend.

The contribution of this project is **software engineering, not epidemiological novelty**. ML-based dengue prediction is a mature academic field; what does not exist is a free, containerized, reproducible system. Never describe this project as a novel model or as a medical oracle.

The domain model is deliberately **agnostic to disease type and region**: event types (`tipos_evento`) and regions (`regiones`) are catalogs rather than hardcoded columns, so the schema can extend beyond dengue/El Salvador without migration changes.

## Non-negotiable constraints

These are project statutes. Do not work around them, and do not relitigate them without explicit instruction from the coordinator.

- **Only real, public, aggregated data.** Never fabricate, simulate, or synthesize a dataset, not even for testing or demos. If data is missing, say so.
- **No paid APIs, no freemium tiers, no mandatory subscriptions** in the core system. Replication cost for a third party must tend to zero.
- **Docker is mandatory.** The system must come up reproducibly.
- **Model metrics and error margins are always visible** in the dashboard. Never hide the error rate.
- **Never present output as diagnosis or certainty.** This is a prioritization aid.
- **No personal data.** Only aggregated public figures, and it must stay that way.
- **ADR before schema change.** Any modification to the database schema requires an accepted ADR in `docs/adr/` *before* the migration is written — including added columns, constraints, `CHECK` values, or new tables. Template: `docs/adr/0001-plantilla-base.md`.

## Architecture

Three Docker services orchestrated by `docker-compose.yml`, networked on `aetheris_network`:

- **`db`** — PostgreSQL 15. Schema loads automatically on first container start via `db/migrations/*.sql` mounted into `/docker-entrypoint-initdb.d`. **Those files run only once, on an empty data volume, in alphabetical order.** Adding a new migration does not apply it to an already-initialized database — that currently requires `docker compose down -v` and a full re-ingest. There is no migration runner; this limitation is a known open decision.
- **`backend`** (`./backend`) — Python FastAPI. Talks to Postgres directly via `psycopg2`, no ORM. Entry point `backend/api/main.py`. Source is bind-mounted for hot reload.
- **`web`** (`./web`) — Astro + TypeScript + Leaflet. Source is bind-mounted; `node_modules` is a separate anonymous volume.

### Database schema (`db/migrations/0001_init_schema.sql`)

Star-schema-like design around epidemiological weeks:

- `regiones` — hierarchical regions (país → departamento; municipio reserved). `codigo` uses ISO 3166-2:SV. **This has not been verified against the geoBoundaries GeoJSON used by Leaflet** — confirm before relying on it as a map join key. Note also that this table has **no latitude/longitude columns**, which currently blocks the Open-Meteo ingestion (see open decisions below).
- `tipos_evento` — catalog of disease/event types (currently `dengue`).
- `fuentes_datos` — provenance catalog (`opendengue_v1_3`, `minsal_pdf`, `open_meteo_era5_land`).
- `semanas_epidemiologicas` — shared epi-week calendar. **PAHO/CDC (MMWR) epi weeks, not ISO 8601.** Use the `epiweeks` library rather than recomputing boundaries by hand. Populated by an ingestion script, not by the DDL. Both fact tables FK into it, so it must be populated first.
- `casos_epidemiologicos` — target variable: counts by region/event/epi-week/classification (`probable` vs `confirmado`). A single MINSAL table row reports probable and confirmado for **different weeks** — insert them as separate rows with their own resolved week.
- `variables_ambientales` — predictors by region/epi-week, EAV-style (`variable`/`valor`). Named "ambientales" rather than "climáticas" to leave room for non-climate predictors. `variable` is free text with **no catalog table and no constraint**, so a typo silently creates a second, separate series that the model will treat as a distinct predictor. Use exactly these strings and no variants:

  `temp_max`, `temp_min`, `temp_media`, `precipitation_sum`, `precipitation_hours`, `humedad_relativa_media`, `punto_rocio`, `et0_fao`

  Adding a new predictor means adding a new string to this list here, in the same session, not inventing one at the call site.
- `boletines_procesados` — audit log of bulletin ingestion, tracking whether departmental sums reconcile against the published national total (`validacion_cuadra`). A mismatch is flagged `revision_manual` and **never ingested silently**. Allowed `estado` values today: `pendiente`, `ok`, `revision_manual`, `error`. Note that none of them fits "bulletin with no departmental table" (holiday and multi-week bulletins); recording those as `error` pollutes the ingestion quality metric that the report will cite. Adding the missing value is part of the pending `0002` migration and requires an ADR first.

**Controlled values elsewhere in the schema** — reuse verbatim, never invent: `casos_epidemiologicos.clasificacion` is `probable` or `confirmado`; `boletines_procesados.familia_esquema` is `A` or `B`; `fuentes_datos.codigo` is `opendengue_v1_3`, `minsal_pdf` or `open_meteo_era5_land`; `regiones.codigo` follows ISO 3166-2:SV.

## Data sources and their traps

### MINSAL PDF bulletins (departmental cases, 2018–2023)

The full corpus is downloaded to `backend/ingestion/data/raw/minsal/{año}/`. These traps were confirmed empirically by manual inspection and are the expensive part to rediscover:

- **The year printed inside the PDF is not reliable.** Confirmed: `SE012023.pdf` says "El Salvador 2022" in its table title. Always derive the year from the filename, never from the document text.
- **Two table formats exist, and the split is NOT clean by year.** Detect the format **per document**, by checking whether a "Tasa x 100.000" column is present. Never infer it from a year range. (An earlier version of this file stated the split as 2018–2020 vs 2021–2023 — that is descriptive only and must not be used as a detection rule.)
- **Blank cells mean zero**, not missing. Ingest as `0`, never `NULL`, never a skipped row.
- **"Otros países" is a real table row that maps to no department.** The published national total excludes it. Separate it out before summing; the 14 departments must equal the total exactly.
- **Republications with a version suffix (`_v2` … `_v4`) are corrections of the same bulletin**, not distinct ones. Reprocessing must overwrite, and the precedence between versions must be explicit (highest version wins) rather than depending on directory traversal order.
- **Holiday bulletins carry no departmental table** (Semana Santa, Fiestas Agostinas, Fin de Año — roughly 3 weeks/year). **Filename detection does not work**: `SE142023-Semana-Santa.pdf` contains a valid `SE\d+` pattern. Detect by content — absence of the departmental table anchor — and record the result as an expected absence, distinct from an extraction failure.
- The column headers state which epidemiological week each column belongs to. Read that from each table's own header; never assume a fixed offset from the filename week.
- **In Familia A, the rate column does not correspond to the "probable" column.** The table title declares probable cases for one week and incidence rates for *confirmed* cases of another. Deriving population by dividing probables by the rate yields a large, plausible, meaningless integer — an error that does not fail, it just corrupts. Correct form: `population = confirmed(SE_Y) / rate(SE_Y) x 100000`, where `SE_Y` is the week the header declares for the confirmed series. Not yet verified: whether the rate is weekly or cumulative to date. Check the header and footnote before writing that line.
- **Some bulletins cover more than one week.** Confirmed for 2018, where SE01 and SE02 come combined in a single file. Do **not** ingest as a weekly row and do **not** split the count between the two weeks — splitting fabricates data, and ingesting as weekly injects an observation of roughly double magnitude that contaminates any baseline built over it. Detect by header: if it declares a two-week range, record it with the same expected-absence state as a holiday bulletin.
- Real departmental coverage is therefore about **49 of 52 weeks per year**, not 52.
- Holiday weeks are not fixed: Semana Santa moves (SE13, SE16, SE13, SE15, SE14 across 2018–2023). Also, the published gaps appear shifted one week earlier than the calculated holiday week, likely because the bulletin for week N is published during week N+1. **Do not precompute a table of expected gaps by week** — count what is actually present.

### Why 2020 is excluded — do not "fix" this

Only 2018, 2019, 2021, 2022 and 2023 were downloaded. **2020 is deliberately absent and must not be added back.** Two independent reasons, either of which would be sufficient:

1. **Real under-reporting, not low transmission.** Epidemiological surveillance was disrupted during the covid-19 pandemic — consultations were suspended and reporting of notifiable diseases dropped. National figures: 2019 recorded 26,434 cases (the historical peak and the only severe-outbreak year in the window), while 2020 recorded 5,224. Training on 2020 would teach the classifier a "low risk" signal that reflects the reporting system's capacity that year rather than actual transmission.
2. **Extraction risk.** The 2020 sample showed empty cells under plain-text extraction, with a higher misalignment risk than 2018–2019.

This exclusion applies to the **departmental training window**. It does not apply to narrative use: the national OpenDengue series is shown for 2018–2024 including 2020, with an explanatory note about why that year looks anomalous. The year is excluded from training, not hidden from the story.

If a task appears to require 2020 departmental data, stop and ask rather than downloading it.

### OpenDengue

National (Admin0) weekly series, 2018–2024, in `backend/ingestion/data/raw/opendengue/`. Narrative/exploratory use only — it does not feed the classifier. Its departmental (Admin1) extract exists only for 2000–2009 and is **monthly**, which does not align with a weekly classifier.

### Open-Meteo (climate)

Model fixed to `era5_land` / `best_match` (9–11 km). Free hosted API; self-hosting was evaluated and rejected. No weekly aggregation exists in the API — build epi-week aggregates in the pipeline from daily values. "Precipitation probability" does not exist in historical reanalysis; use `precipitation_sum` and `precipitation_hours`. The API returns the **center of the grid cell actually used**, not the requested coordinate, and that relationship must be persisted rather than assumed.

## Repository conventions

- Domain content (table names, columns, comments, docstrings) is in **Spanish**, matching the source data. Keep new schema and domain code consistent with this.
- Keep the disease/region-agnostic design intact — extend the `tipos_evento` / `regiones` / `fuentes_datos` catalogs rather than adding disease- or country-specific columns.
- Respect the reconciliation pattern of `boletines_procesados`: validate against a published total before treating a load as clean, and flag discrepancies for manual review instead of ingesting them.
- **Raw and intermediate data are not versioned.** `backend/ingestion/data/raw/` is gitignored, and `backend/ingestion/data/interim/` must be too — that is where the parser dumps each bulletin's raw extracted table (including the Familia A rate column, which is always kept) before normalisation. Reading the 264 PDFs happens once; everything downstream consumes the intermediate layer. Code and documentation inside `backend/ingestion/data/` are tracked. Never commit downloaded PDFs or extracts.
- Validate downloaded PDFs by byte signature (`%PDF`), not by HTTP `Content-Type` — the server returns `application/octet-stream`.

## Open decisions — do not resolve these unilaterally

These are unresolved at the project level. If a task depends on one, stop and ask rather than inventing an answer.

- **The risk label method is decided; its parameters are not.** The label is built as an **endemic channel** (historical percentile within each department), never as a population-incidence threshold — the population denominator for the training window was invalidated by the 2024 census and an error there would land in the target variable. Still undecided, pending an actual class-distribution run: base variable (probable vs confirmed), percentile cuts, neighbouring-week window, base-year scheme, sufficiency floor, and the feature-column ceiling. Do not invent any of these. Two method rules are fixed: the year being labelled must **never** appear in its own percentile baseline, and baseline sufficiency is judged by counting observations actually present per (department, target year, week), never from a precomputed per-cell table.
- **Whether the classifier uses lagged case counts as predictors, or climate only**, is undecided. This determines whether the system can operate on current weeks at all, since no automated departmental case source exists after 2023.
- **The 2020 exclusion** is defined as a *training-window* decision. Whether it is also enforced at the ingestion layer is not settled — do not silently filter 2020 out during ingestion.
- **Where model output lives** (computed on request vs. persisted in a table) is undecided, and the schema has no table for predictions.
- **Departmental coordinates for Open-Meteo** — assignment method and storage location are undecided.

## Commands

Run everything (Postgres + API + web, hot reload):

```bash
docker-compose up --build
```

- Backend API: http://localhost:8000 (health check at `/health`)
- Web frontend: http://localhost:4321
- Postgres: localhost:5432

Environment variables come from `.env` (copy from `.env.example`; never commit `.env`).

### Backend outside Docker

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Note: the development environment is Arch-based; prefer a virtualenv over a bare `pip install`.

### Web outside Docker

The Dockerfile uses `pnpm` via Corepack, pinned to v9. Use `pnpm`, not `npm`.

```bash
cd web
pnpm install
pnpm dev       # port 4321
pnpm build
pnpm preview
```

There is currently **no test suite, linter, or CI configuration** in this repository. Adding pytest coverage for the ingestion pipeline is a known pending task, with three manually verified bulletins available as reference cases.
