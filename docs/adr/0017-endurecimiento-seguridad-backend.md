# 0017 - Endurecimiento incremental del backend y umbral de escritura

**Estado:** Aceptado (2026-09-08)

> No elige slowapi: esa dependencia ya está en `dev` desde los PRs #66 y
> #78 (capa 7 del issue #61). Este ADR registra el umbral de escritura
> que faltaba y los diferimientos deliberados de la pasada de
> endurecimiento. El número es 0017, no 0016: la PR #110 (biblioteca)
> ya reserva `docs/adr/0016-*.md`. El coordinador puede degradar este
> ADR a una entrada de CHANGELOG si le parece demasiado peso.

## Contexto

El issue #61 (rate limiting / DoS) tiene la capa de aplicación cubierta
en `dev`: `slowapi` con contador en memoria, límite global
`120/minute`, umbral `RATE_LIMIT_HEAVY` en los endpoints de cálculo
on-demand, `/health` exento, `key_func` que toma el último hop de
`X-Forwarded-For` (issue #67), 429 con cabeceras CORS, pool de
conexiones (issue #68) y `SecurityHeadersMiddleware` (nosniff, DENY,
HSTS, CSP para `/docs`). Render corre un solo proceso Uvicorn sin
`--workers`, así que el contador en memoria es el global.

Quedaban tres huecos acotados:

1. `POST /api/alertas` y `PATCH /api/alertas/{id}` (ADR 0015) heredaban
   solo el límite global de 120/min. Crear o editar alertas es una
   operación humana de baja frecuencia; 120 intentos por minuto por IP
   es holgado para un bucle de abuso sobre la superficie de escritura.
2. Faltaban `Referrer-Policy` y `Permissions-Policy`.
3. CORS `allow_headers=["*"]` no documentaba qué cabeceras reales
   acepta el preflight del formulario `/alertas/nueva`.

Fuera de este ADR, a propósito:

- **Cloudflare / WAF perimetral:** única parte que el propio issue #61
  deja pendiente. Requiere cuenta Cloudflare y decisión de
  infraestructura. No se cierra #61 aquí.
- **Issue #72** (`GET /api/riesgo-nacional` 503 si faltan artefactos):
  necesita decisión de equipo sobre versionar derivados o degradar el
  endpoint. No se resuelve aquí.
- **Swap de `psycopg2.pool` a `psycopg_pool`:** el pool actual funciona
  (issue #68 cerrado). Cambiarlo sería churn de dependencia contra
  `AGENTS.md` §5 sin beneficio medible.
- **Apretar la CSP** (quitar `'unsafe-inline'` / `cdn.jsdelivr.net`):
  esos valores mantienen viva la Swagger UI de `/docs`. La API sirve
  JSON, no HTML de usuario; apretar la CSP rompe `/docs` sin ganancia
  de cara al usuario.

## Decisión

### Umbral de escritura

- Constante de módulo `RATE_LIMIT_WRITE`, default `"10/minute"`, leída
  de `os.getenv` en import (mismo idiom que `RATE_LIMIT_DEFAULT` y
  `RATE_LIMIT_HEAVY`, para que los tests bajen el valor con
  `monkeypatch` + `importlib.reload`).
- `@limiter.limit(RATE_LIMIT_WRITE)` en `POST /api/alertas` y
  `PATCH /api/alertas/{id}`. Usa la misma `key_func` `_client_ip` del
  `Limiter` (último hop de `X-Forwarded-For`).
- `GET /api/alertas` se queda con el límite global: es lectura pública
  cacheada (`CACHE_TTL_ALERTAS`).
- Justificación del 10/min: deja margen para corregir varias alertas
  seguidas en una sesión de equipo y corta un bucle de abuso. Se
  ajusta por env sin redeploy de código. No se declara en `render.yaml`
  porque el default del código ya sirve en producción.

### Cabeceras

En `SecurityHeadersMiddleware`, además de las ya existentes:

- `Referrer-Policy: strict-origin-when-cross-origin` (default moderno
  de los navegadores; explicitarlo cubre clientes viejos).
- `Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=()`.
  La API no usa esas features; negarlas es barato y correcto.

No se tocan HSTS, `X-Content-Type-Options`, `X-Frame-Options`,
`X-XSS-Protection` ni la CSP. No se reordena ningún `add_middleware`:
`SlowAPIMiddleware` sigue antes de CORS (429 con cabeceras CORS);
`SecurityHeadersMiddleware` sigue último (envuelve todo).

### CORS `allow_headers`

Lista explícita `["Authorization", "Content-Type"]`. Son las dos
cabeceras que manda `web/src/pages/alertas/nueva.astro`. El resto de
`fetch` del frontend no envía cabeceras personalizadas hacia la API.

### Dependencias

Ninguna nueva. `slowapi==0.1.10` y `limits==5.8.0` ya estaban.

## Consecuencias

* Positivo: la superficie de escritura autenticada deja de compartir
  el techo holgado de 120/min; el preflight de `/alertas/nueva` queda
  cubierto por test; las dos cabeceras que faltaban quedan fijas.
* Negativo: un operador que cree más de 10 alertas en un minuto desde
  la misma IP recibirá 429 y deberá esperar. Improbable en uso real;
  se sube `RATE_LIMIT_WRITE` por env si hace falta.
* Neutral: el issue #61 sigue abierto hasta que exista decisión de
  infra sobre Cloudflare/WAF. El coordinador decide si abre un issue
  de infra aparte o re-scopea #61. Este ADR no usa `Closes #61`.
