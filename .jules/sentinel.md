## 2025-02-12 - Path Traversal via URL-encoded characters in `_nombre_desde_url_directa`
**Vulnerability:** A path traversal vulnerability existed in `backend/ingestion/minsal/common.py` when extracting filenames from direct PDF URLs. An attacker could craft a URL containing URL-encoded path separators (e.g. `%2f` for `/` and `%2e%2e` for `..`). `Path().name` did not recognize these as directory segments, so it included the traversal payload in the filename. The subsequent URL-decoding step would then produce a string containing directory traversal characters (e.g., `../../etc/passwd`), leading to file writes outside the intended directory.
**Learning:** Extracting filenames from URLs must correctly handle URL encoding. Decoding should happen *before* the path components are parsed, not after. Failing to do so allows attackers to bypass path validation logic.
**Prevention:** Always URL-decode strings representing paths *before* using tools like `Path().name` or `os.path.basename` to extract path components.

## 2025-02-26 - Insecure CORS Configuration via Environment Variables
**Vulnerability:** Dynamically loading CORS origins from an environment variable and splitting by a delimiter without validating the contents allowed a wildcard `*` to be unintentionally permitted. This could expose internal APIs to Cross-Origin Resource Sharing attacks from malicious external domains, defeating the purpose of CORS.
**Learning:** Input validation must occur on environment configuration inputs just as with user input, especially when it concerns security boundaries like CORS origins. Trusting that environment configurations are always secure and specific is a pitfall.
**Prevention:** Validate explicit CORS origins at application startup. Explicitly check for and reject dangerous wildcard characters like `*` before passing dynamically constructed lists to the application's CORS middleware.

## 2026-08-27 - XSS via `innerHTML` with unescaped API data
**Vulnerability:** `web/src/components/MetricasModelo.astro` built HTML with `innerHTML` from API fields (`aviso`, `nota`, `corte_percentil`, `probabilidades` keys) without escaping them. A manipulated API response could inject `<script>` (stored/reflected XSS).
**Learning:** Assigning strings that contain external data to `innerHTML` is unsafe by default even if the API is trusted today.
**Prevention:** Escape `<`, `>`, `&`, `"`, `'` with the shared `escapeHtml` util (`web/src/utils/security`) on every dynamic interpolation inside `innerHTML`, or use `document.createElement()` + `textContent`. Reuse the existing util -- do not redefine it per component.
