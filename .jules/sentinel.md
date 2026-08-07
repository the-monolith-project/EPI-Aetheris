## 2026-08-05 - Hardcoded Secret & Information Disclosure in Healthcheck
**Vulnerability:** Found a hardcoded fallback database password (`aetheris_secure_password`) and an exposed raw exception message (`str(e)`) in the HTTP response during database connection failures in `backend/api/main.py`.
**Learning:** Hardcoded credentials should never be used, even as fallbacks in `.getenv`. Unhandled/raw exception messages can leak sensitive infrastructure details like Data Source Names, usernames, paths, and potentially passwords.
**Prevention:** Never use hardcoded secrets for fallback configuration values. Always sanitize error messages in API responses to avoid leaking application internals or stack traces.
