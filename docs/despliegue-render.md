# Despliegue en Render

Decisión tomada 2026-08-22, para tener una URL pública antes del video demo
(2026-09-05) y la Expo Técnica (2026-09-29). Investigación de costo-beneficio
comparó Render, Railway, Fly.io y Vercel; Render ganó por encajar directo con
el `docker-compose.yml` existente (Blueprint declara los 3 servicios como
IaC), tener el mejor historial de uptime reciente de las opciones evaluadas,
y no requerir administración manual de Postgres (a diferencia de Fly.io). El
plan de pago (~$14/mes, Starter + Basic-256mb) se eligió desde el día 1 en
vez del tier gratuito: el free tier de Render duerme el backend a los 15 min
de inactividad (cold start ~1 min, malo para una demo en vivo) y su Postgres
gratis expira a los 30 días -- la ventana de trabajo hasta la Expo supera eso.

Railway quedó descartado por su historial de incidentes (5 publicados desde
noviembre 2025, incluyendo un corte de ~8h en mayo 2026) frente a una fecha
fija no negociable. Fly.io quedó descartado por exigir Postgres
self-managed sin backups automáticos en su tier barato -- carga operativa
que no conviene meter en las semanas de video/expo. Vercel + Render
(separando frontend de backend/DB) es una alternativa igual de válida al
mismo costo total (~$14/mes, Vercel Hobby es gratis para este tráfico) --
se descartó solo por preferencia de una sola cuenta/dashboard, no por un
problema técnico.

Esto es un despliegue para demo, no para producción con usuarios reales
-- no cambia el statuto del proyecto sobre APIs de datos de pago (ver
CLAUDE.md), que sigue aplicando a las fuentes (MINSAL/OpenDengue/Open-Meteo),
no a la infraestructura de hosting.

## Qué declara `render.yaml`

Blueprint con tres servicios, todos en la región `oregon` (misma región =
red privada entre backend y base):

- `epi-aetheris-db` -- Postgres 15 gestionado, plan `basic-256mb`.
- `epi-aetheris-backend` -- FastAPI vía Docker (`backend/Dockerfile`), CMD
  sobreescrito para quitar `--reload` (ese flag es para el hot-reload de
  docker-compose en desarrollo, no debe correr en el proceso de producción).
- `epi-aetheris-web` -- sitio estático Astro (`pnpm build`, publica `dist/`).

Las variables de Postgres (`POSTGRES_HOST/PORT/DB/USER/PASSWORD`) se
inyectan automáticamente al backend vía `fromDatabase`. `CORS_ALLOWED_ORIGINS`
y `PUBLIC_API_URL` están hardcodeadas al patrón predecible
`https://<nombre-del-servicio>.onrender.com` -- Render usa ese subdominio
exacto salvo colisión de nombre (namespace global), así que **hay que
verificar las URLs reales en el dashboard tras el primer deploy y corregir
`render.yaml` si no coinciden**, luego redeployar.

## Primer despliegue (pasos manuales, una sola vez)

Render, a diferencia de la imagen oficial de Postgres en docker-compose, no
tiene un hook `docker-entrypoint-initdb.d` que auto-aplique
`db/migrations/*.sql` sobre una base gestionada recién creada. Hay que
aplicarlas a mano:

1. En el dashboard de Render, conectar el Blueprint a este repo (rama
   `main`) -- esto crea los 3 servicios pero el backend fallará su
   healthcheck hasta el paso 3, porque la base está vacía.
2. Copiar la **External Connection String** de `epi-aetheris-db` (dashboard
   → esa base → "Connect" → External).
3. Desde el host (no dentro de ningún contenedor), aplicar migraciones y
   seed contra esa base remota:

   ```bash
   cd db
   export MIGRACIONES_POSTGRES_HOST=<host externo de Render>
   export POSTGRES_PORT=<puerto externo>
   export POSTGRES_USER=aetheris_user
   export POSTGRES_DB=epi_aetheris
   export POSTGRES_PASSWORD=<password del dashboard>
   python aplicar_migraciones.py --bootstrap
   psql "<external connection string>" -f seed/seed_datos_reales.sql
   ```

   `--bootstrap` crea la tabla `schema_migrations` y siembra qué migraciones
   ya se consideran aplicadas (ver ADR 0009) -- correrlo antes de cargar el
   seed evita que el runner normal intente reaplicar el DDL después.
4. Verificar en el dashboard las URLs reales asignadas a
   `epi-aetheris-backend` y `epi-aetheris-web`. Si Render agregó un sufijo
   por colisión de nombre, actualizar `CORS_ALLOWED_ORIGINS` (env var del
   backend) y `PUBLIC_API_URL` (env var del frontend) en el dashboard --o
   en `render.yaml` y volver a sincronizar el Blueprint-- y forzar un
   redeploy del frontend (`PUBLIC_API_URL` se embebe en build-time, un
   cambio de env var sin rebuild no tiene efecto).
5. Confirmar `GET /health` del backend y que `/panel` cargue el mapa con
   datos reales -- si el mapa muestra "sin dato" en todo, lo más probable
   es el paso 4 (frontend compilado apuntando al `PUBLIC_API_URL` viejo).

## Cambios de esquema después del primer despliegue

Igual que en local (ver CLAUDE.md, sección de comandos): agregar un archivo
nuevo en `db/migrations/`, luego correr `python aplicar_migraciones.py`
(sin `--bootstrap`) contra la base de Render usando las mismas variables de
entorno del paso 3. Sigue aplicando la regla del proyecto: ADR aceptado en
`docs/adr/` antes de escribir la migración.
