## 2026-08-27 - FastAPI payload compression
**Learning:** FastAPI does not compress responses out of the box. EPI-Aetheris serves full historical series (several years of week-by-week data per region) as unpaginated JSON for client-side processing; without compression that is a silent network bottleneck.
**Action:** Enable `GZipMiddleware` (`minimum_size=1000`) in `backend/api/main.py` and keep an eye on the payload size of the large JSON endpoints.

## 2026-08-28 - FastAPI file IO overhead in route handlers
**Learning:** FastAPI route handlers run synchronously by default unless declared with `async def`. Performing synchronous disk I/O (like reading a CSV file via `csv.DictReader` inside the `/api/riesgo-nacional` endpoint) on every request without caching blocks the thread and significantly increases the endpoint latency when dealing with static artifact files.
**Action:** Implemented an in-memory global cache (`_dataset_riesgo_cache`) to parse the CSV file only once upon the first request, avoiding unnecessary disk access and reducing overhead for subsequent requests.

## 2026-08-30 - Missing Cache-Control headers on analytical endpoints
**Learning:** Certain static/historical analytical endpoints (like `/api/neumonias/*` and `/api/respiratorios/*`) were missing the `_cache_control` utility call, causing clients to re-fetch identical data repeatedly without client-side caching.
**Action:** Added `response: Response` and `_cache_control(response, CACHE_TTL_HISTORICO)` to these endpoints to enable standard HTTP caching and reduce unnecessary server load.

## 2026-09-13 - Python standard library statistics overhead
**Learning:** Python's built-in `statistics` module (like `statistics.median` and `statistics.stdev`) adds massive execution overhead due to exact fraction representation and internal type checking (visible via cProfile). In tight loops processing many small arrays (like `calcular_baseline_semana`), this becomes a severe bottleneck.
**Action:** Replaced standard library functions with manual math operations (`math.sqrt` and manual median from sorted list) for tight loops, reducing calculation time by ~10x (~0.09s -> ~0.009s for 10k loops).

## 2024-05-18 - Replacing statistics module for performance in ingestion scripts
**Learning:** The Python standard library `statistics` module functions (`median`, `stdev`, `quantiles`) are significantly slower than inline math operations or custom linear interpolation functions for small arrays in tight loops, due to exact fraction representation and internal type checking. Similar to the issue found on 2026-09-13 in the API, this bottleneck also existed in `backend/ingestion/validar_leadtime_camino_ancho.py` and `backend/ingestion/corrida_distribucion.py`.
**Action:** Avoid using `statistics` module functions in performance-critical paths; use inline math for `stdev`/`mean`/`median` and custom `percentil` implementations instead.
