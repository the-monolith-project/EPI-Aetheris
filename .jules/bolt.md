## 2026-08-27 - FastAPI payload compression
**Learning:** FastAPI does not compress responses out of the box. EPI-Aetheris serves full historical series (several years of week-by-week data per region) as unpaginated JSON for client-side processing; without compression that is a silent network bottleneck.
**Action:** Enable `GZipMiddleware` (`minimum_size=1000`) in `backend/api/main.py` and keep an eye on the payload size of the large JSON endpoints.
