## 2026-08-27 - FastAPI payload compression
**Learning:** FastAPI does not compress responses out of the box. EPI-Aetheris serves full historical series (several years of week-by-week data per region) as unpaginated JSON for client-side processing; without compression that is a silent network bottleneck.
**Action:** Enable `GZipMiddleware` (`minimum_size=1000`) in `backend/api/main.py` and keep an eye on the payload size of the large JSON endpoints.

## 2026-08-28 - FastAPI file IO overhead in route handlers
**Learning:** FastAPI route handlers run synchronously by default unless declared with `async def`. Performing synchronous disk I/O (like reading a CSV file via `csv.DictReader` inside the `/api/riesgo-nacional` endpoint) on every request without caching blocks the thread and significantly increases the endpoint latency when dealing with static artifact files.
**Action:** Implemented an in-memory global cache (`_dataset_riesgo_cache`) to parse the CSV file only once upon the first request, avoiding unnecessary disk access and reducing overhead for subsequent requests.

## 2026-08-30 - Missing Cache-Control headers on analytical endpoints
**Learning:** Certain static/historical analytical endpoints (like `/api/neumonias/*` and `/api/respiratorios/*`) were missing the `_cache_control` utility call, causing clients to re-fetch identical data repeatedly without client-side caching.
**Action:** Added `response: Response` and `_cache_control(response, CACHE_TTL_HISTORICO)` to these endpoints to enable standard HTTP caching and reduce unnecessary server load.
