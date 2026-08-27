## 2024-08-27 - FastAPI Payload Compression
**Learning:** FastAPI doesn't enable compression out-of-the-box. For EPI-Aetheris's specific architecture where historical epidemiological datasets (several years of week-by-week data across all regions) are sent as unpaginated JSON objects for client-side processing, missing compression acts as a silent but significant network bottleneck.
**Action:** Always enable `GZipMiddleware` in FastAPI apps returning structured historical data, and monitor payload sizes of large JSON endpoints.
