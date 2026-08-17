# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**EPI-Aetheris** is an epidemiological surveillance system, piloted on **dengue in El Salvador**. It ingests historical case counts and environmental (climate) predictors, aligns them by epidemiological week, and classifies **outbreak risk (alto / medio / bajo) by epidemiological week**, exposed through a FastAPI backend and a Leaflet map frontend.

**Phased scope (pivot decision "Opción C", 2026-08-09 — see `docs/contexto/01-decisiones-cerradas.md`):** the first classifier operates at **national level**, trained on the OpenDengue weekly series, not per department. A second, departmental classifier is planned as a later phase, conditioned on the MINSAL departmental signal surviving a pending recount (see `docs/contexto/02-decisiones-abiertas.md`, point H). The map still renders departmental MINSAL data from the first milestone, but as a **descriptive layer**, not as classifier output — the UI must say so explicitly, never imply department-level risk from a national label.

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

- **`db`** — PostgreSQL 15. Schema loads automatically on first container start via `db/migrations/*.sql` mounted into `/docker-entrypoint-initdb.d`. **Those files run only once, on an empty data volume, in alphabetical order.** Adding a new migration does not apply it to an already-initialized database on its own. **ADR 0009 (2026-08-16) closed this**: `db/aplicar_migraciones.py` applies migrations not yet recorded in a `schema_migrations` table (created by the script itself, not by a numbered migration file) against a database that already has data — `docker compose down -v` + full re-ingest is no longer required for routine schema changes. Run `python db/aplicar_migraciones.py --bootstrap` once per existing database (seeds already-applied files without re-running them), then `python db/aplicar_migraciones.py` after adding any new migration file. Runs from the host against the published `localhost:5432`, not inside the `backend` container. No rollback (`down`) — a bad migration is corrected with a new migration, not automatic reversion.
- **`backend`** (`./backend`) — Python FastAPI. Talks to Postgres directly via `psycopg2`, no ORM. Entry point `backend/api/main.py`. Source is bind-mounted for hot reload.
- **`web`** (`./web`) — Astro + TypeScript + Leaflet. Source is bind-mounted; `node_modules` is a separate anonymous volume.

### Database schema (`db/migrations/0001_init_schema.sql`)

Star-schema-like design around epidemiological weeks:

- `regiones` — hierarchical regions (país → departamento; municipio reserved). `codigo` uses ISO 3166-2:SV. **This has not been verified against the geoBoundaries GeoJSON used by Leaflet** — confirm before relying on it as a map join key. Note also that this table has **no latitude/longitude columns**, which currently blocks the Open-Meteo ingestion (see open decisions below).
- `tipos_evento` — catalog of disease/event types (currently `dengue`).
- `fuentes_datos` — provenance catalog (`opendengue_v1_3`, `minsal_pdf`, `open_meteo_era5_land`, `open_meteo_era5`, `noaa_oni`).
- `semanas_epidemiologicas` — shared epi-week calendar. **PAHO/CDC (MMWR) epi weeks, not ISO 8601.** Use the `epiweeks` library rather than recomputing boundaries by hand. Populated by an ingestion script, not by the DDL. Both fact tables FK into it, so it must be populated first.
- `casos_epidemiologicos` — target variable: counts by region/event/epi-week/classification (`probable` vs `confirmado`). A single MINSAL table row reports probable and confirmado for **different weeks** — insert them as separate rows with their own resolved week.
- `variables_ambientales` — predictors by region/epi-week, EAV-style (`variable`/`valor`). Named "ambientales" rather than "climáticas" to leave room for non-climate predictors. `variable` is free text with **no catalog table and no constraint**, so a typo silently creates a second, separate series that the model will treat as a distinct predictor. Use exactly these strings and no variants:

  `temp_max`, `temp_min`, `temp_media`, `precipitation_sum`, `precipitation_hours`, `humedad_relativa_media`, `punto_rocio`, `oni_anom`

  `et0_fao` is deprecated — never loaded, out of scope (ET₀ removed 2026-08-07). `oni_anom` (ADR 0008, migration `0006`) is NOAA's Oceanic Niño Index anomaly, stored under region `SV` (national, `nivel_admin=0`) — not departmental. Same monthly value applies to every epi-week within that calendar month (a state variable, not an accumulable count — see ADR 0008 point C for why that isn't the same kind of fabrication the OpenDengue Admin1 monthly-to-weekly split would have been). Experimental predictor, not confirmed in production yet.

  Adding a new predictor means adding a new string to this list here, in the same session, not inventing one at the call site.
- `boletines_procesados` — audit log of bulletin ingestion, tracking whether departmental sums reconcile against the published national total (`validacion_cuadra`). A mismatch is flagged `revision_manual` and **never ingested silently**. Allowed `estado` values: `pendiente`, `ok`, `revision_manual`, `error`, `ausencia_esperada` (ADR 0004), `sin_texto_extraible` (ADR 0007 — bulletin opened fine but no "dengue" text found anywhere, likely a scanned/image table).

**Controlled values elsewhere in the schema** — reuse verbatim, never invent: `casos_epidemiologicos.clasificacion` is `probable`, `confirmado`, or `total` (ADR 0005 — `total` is OpenDengue's aggregate case count, populated only for `fuente_id = opendengue_v1_3` at national level; it is NOT equivalent to `confirmado`, which means lab-confirmed MINSAL cases specifically — never sum `conteo` across `clasificacion` values without filtering first); `boletines_procesados.familia_esquema` is `A` or `B`; `fuentes_datos.codigo` is `opendengue_v1_3`, `minsal_pdf`, `open_meteo_era5_land`, or `open_meteo_era5` (ADR 0006 — `open_meteo_era5` is exclusively for `precipitation_sum`/`precipitation_hours`, since `era5_land` cannot serve precipitation at all; never attribute precipitation rows to `open_meteo_era5_land`); `regiones.codigo` follows ISO 3166-2:SV.

## Data sources and their traps

### MINSAL PDF bulletins (departmental cases, 2018–2023)

The full corpus is downloaded to `backend/ingestion/data/raw/minsal/{año}/`. These traps were confirmed empirically by manual inspection and are the expensive part to rediscover:

- **The year printed inside the PDF is not reliable.** Confirmed: `SE012023.pdf` says "El Salvador 2022" in its table title. Always derive the year from the filename, never from the document text.
- **Two table formats exist, and the split is NOT clean by year.** Detect the format **per document**, by checking whether a "Tasa x 100.000" column is present. Never infer it from a year range. (An earlier version of this file stated the split as 2018–2020 vs 2021–2023 — that is descriptive only and must not be used as a detection rule.)
- **Blank cells mean zero**, not missing. Ingest as `0`, never `NULL`, never a skipped row.
- **"Otros países" is a real table row that maps to no department.** Whether the published national total includes it is **not consistent across the corpus** — confirmed excluded in SE52/2019 (footnote explicit), confirmed included in SE35–52/2018. Test both conventions per bulletin when reconciling against the published total; do not hardcode one.
- **Probable/Confirmado in the departmental table are cumulative from SE1, not weekly incidence — in both table families.** Confirmed by monotonic non-decreasing national totals across 47 tables in 2023, and independently by exact arithmetic cross-checks (SE23/2019: 276+3=279 matches the "Casos probables (SE 1-21)" figure in the same bulletin's cumulative-situation table; SE52/2019 similarly). Each column's header declares the **cumulative cutoff week**, not a single week's count — the "read the week from the header" rule still applies, but its meaning is "cutoff of the accumulator," not "the week being counted." **Inserting these values as-is into `casos_epidemiologicos.conteo` corrupts the target variable** (the endemic channel would train on a monotonically increasing series). De-accumulate by differencing consecutive bulletins per (department, series): gaps between available cutoffs must be recorded as a no-data interval, never split or interpolated; negative diffs are MINSAL retroactive corrections and must be excluded from the series, not clamped to zero. A validated exploratory implementation of this exists at `backend/ingestion/corrida_distribucion.py` (not the production parser, does not write to Postgres) — see `docs/contexto/03-fuentes-de-datos.md`, trap 8, before reimplementing this from scratch.
- **A small number of 2019 bulletins have the departmental table rendered as an image, not text** (`SE232019`, `SE322019`, `SE352019_v2` — zero occurrences of "dengue" anywhere in extractable text). "No OCR needed" is not a universal property of this source. Rescue is file-specific (rasterize just the table page, OCR it), not a general parsing strategy — and adding an OCR dependency (`pytesseract`) requires coordinator confirmation before installing, since it touches the closed stack.
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

National (Admin0) weekly series, real coverage 2013/2014–2024 in the downloaded extract (loaded window: 2018–2024), in `backend/ingestion/data/raw/opendengue/`. **As of the "Opción C" pivot (2026-08-09), this is the target variable for the first (national) classifier** — not narrative-only anymore, loaded via `backend/ingestion/cargar_opendengue.py`. It remains narrative/exploratory for years outside the departmental training window (2020, 2024+). Its departmental (Admin1) extract exists only for 2000–2009 and is **monthly**, which does not align with a weekly classifier — still not usable for departmental work.

**Loading trap confirmed 2026-08-09:** the CSV's `case_definition_standardised` is `'Total'` for 100% of the national weekly rows — OpenDengue does not split probable/confirmado for El Salvador at this resolution. Stored as `casos_epidemiologicos.clasificacion = 'total'` (ADR 0005), not `'confirmado'` — forcing it into an existing value would misrepresent it as lab-confirmed MINSAL data, which is a much smaller, differently-defined count. There is no explicit week-number column; resolve the epi week by exact match of `calendar_start_date` against `semanas_epidemiologicas.fecha_inicio`, never by recomputing with `epiweeks` independently on the CSV. Also: `psycopg2.extras.execute_values` only reports `cur.rowcount` for its last internal page when the row count exceeds `page_size` (default 100) — pass `page_size=len(rows)` (or count rows yourself) rather than trusting `cur.rowcount` for the total, confirmed by a live off-by-page-size bug while writing the loader.

### Open-Meteo (climate)

Two models, not one — `era5_land` for `temperature_2m_max/min/mean`, `relative_humidity_2m_mean`, `dew_point_2m_mean`; `era5` for `precipitation_sum`/`precipitation_hours` (`era5_land` cannot serve precipitation at all). Never `best_match` or `era5_seamless` — both hide which grid produced which value. Free hosted API; self-hosting was evaluated and rejected. No weekly aggregation exists in the API — build epi-week aggregates in the pipeline from daily values (`backend/ingestion/cargar_clima.py`: mean for state variables — temp/humidity/dew point — sum for cumulative ones — precipitation; an implementation choice, not a locked team decision). "Precipitation probability" does not exist in historical reanalysis; use `precipitation_sum` and `precipitation_hours`. The API returns the **center of the grid cell actually used**, not the requested coordinate, and that relationship must be persisted rather than assumed.

**Loaded 2026-08-10 (card 12):** `backend/ingestion/cargar_clima.py` — 35,868 rows, 7 variables × 14 departments × 2018–2024 (2020 included; the 2020 exclusion is training-only, never filter it at ingestion). Only 2 real HTTP calls total (multi-location: all 14 departments in one request per model) — the ~2,200-weighted-call estimate from earlier research didn't materialize. **Trap confirmed live:** Open-Meteo's per-minute rate limit triggers (`429`) with just a few calls in quick succession even though the daily/monthly quota is nowhere close — the loader retries with backoff. As a side effect, this script is what actually populates `regiones.centroide_lat/lon/elevacion_m` (columns existed since ADR 0003 but nothing wrote to them before this) — `elevacion_m` comes from Open-Meteo's own response (its internal DEM), not a separate topographic measurement.

## Repository conventions

- Domain content (table names, columns, comments, docstrings) is in **Spanish**, matching the source data. Keep new schema and domain code consistent with this.
- Keep the disease/region-agnostic design intact — extend the `tipos_evento` / `regiones` / `fuentes_datos` catalogs rather than adding disease- or country-specific columns.
- Respect the reconciliation pattern of `boletines_procesados`: validate against a published total before treating a load as clean, and flag discrepancies for manual review instead of ingesting them.
- **Raw and intermediate data are not versioned.** `backend/ingestion/data/raw/` is gitignored, and `backend/ingestion/data/interim/` must be too — that is where the parser dumps each bulletin's raw extracted table (including the Familia A rate column, which is always kept) before normalisation. Reading the 264 PDFs happens once; everything downstream consumes the intermediate layer. Code and documentation inside `backend/ingestion/data/` are tracked. Never commit downloaded PDFs or extracts. **Deliberate exception (ADR 0010, 2026-08-17):** `db/seed/seed_datos_reales.sql` — a `pg_dump --data-only` snapshot (4.4 MB) of the fact tables (`semanas_epidemiologicas`, `boletines_procesados`, `casos_epidemiologicos`, `variables_ambientales`, not the catalog tables already seeded by the migrations themselves) — IS tracked, mounted as an individual file into `/docker-entrypoint-initdb.d/` alongside `db/migrations/*.sql` so `git clone` + `docker compose up` yields a working system with real data, no PDFs or API calls required. It's a point-in-time snapshot, not kept in sync automatically — regenerate manually per the ADR when it's worth a fresher one.
- Validate downloaded PDFs by byte signature (`%PDF`), not by HTTP `Content-Type` — the server returns `application/octet-stream`.

## Open decisions — do not resolve these unilaterally

These are unresolved at the project level. If a task depends on one, stop and ask rather than inventing an answer.

- **The risk label method is decided; its parameters are not.** The label is built as an **endemic channel** (historical percentile within each department), never as a population-incidence threshold — the population denominator for the training window was invalidated by the 2024 census and an error there would land in the target variable. Still undecided, pending an actual class-distribution run: base variable (probable vs confirmed), percentile cuts, neighbouring-week window, base-year scheme, sufficiency floor, and the feature-column ceiling. Do not invent any of these. Two method rules are fixed: the year being labelled must **never** appear in its own percentile baseline, and baseline sufficiency is judged by counting observations actually present per (department, target year, week), never from a precomputed per-cell table.
- **Whether the classifier uses lagged case counts as predictors, or climate only**, is undecided. This determines whether the system can operate on current weeks at all, since no automated departmental case source exists after 2023.
- **The 2020 exclusion** is defined as a *training-window* decision. Whether it is also enforced at the ingestion layer is not settled — do not silently filter 2020 out during ingestion.
- **Where model output lives** (computed on request vs. persisted in a table) is undecided, and the schema has no table for predictions.
- **Departmental coordinates for Open-Meteo** — assignment method and storage location are undecided.
- **Whether the departmental classifier ever activates** depends on a pending recount of the MINSAL rejection criteria after rescuing the 2019 image-table bulletins (see the accumulation trap above). Do not treat the departmental parser as blocked on the MVP anymore — the national classifier is the unblocked path — but do not assume the departmental one will ship either.

This list is a working summary; `docs/contexto/02-decisiones-abiertas.md` is the fuller, more current source when the two disagree — check there before assuming this file is exhaustive.

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

### Multi-agent / multi-worktree note (Orca ADE)

`docker-compose.yml` uses fixed `container_name` values and fixed host ports (5432/8000/4321), shared at the Docker daemon level — not per git worktree. If you're running multiple agents in parallel worktrees (e.g. via Orca), **only one worktree should run `docker-compose up` at a time.** Agents in other worktrees should work on code without starting the stack, or coordinate with whoever has it up. Do not "fix" this by editing `docker-compose.yml` to namespace ports/names per worktree without asking first — it's a deliberate simplicity trade-off for a single shared dev stack, not an oversight.

There is currently **no test suite, linter, or CI configuration** in this repository. Adding pytest coverage for the ingestion pipeline is a known pending task, with three manually verified bulletins available as reference cases.
