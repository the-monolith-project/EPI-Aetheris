#!/usr/bin/env bash
# Regenera db/seed/seed_datos_reales.sql (ADR 0010). Accion manual: no hay
# hook que lo mantenga sincronizado con la base de desarrollo.
#
# pg_dump --disable-triggers emite ALTER TABLE ... DISABLE/ENABLE TRIGGER ALL.
# Esas lineas exigen superuser; aetheris_user en el Postgres gestionado de
# Render no lo es, y con ON_ERROR_STOP la carga hace rollback completo
# (issue #82). El post-proceso las quita. El orden de tablas por dependencia
# ya garantiza las FK sin desactivar triggers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESTINO="$ROOT/db/seed/seed_datos_reales.sql"

PGHOST="${POSTGRES_HOST:-localhost}"
if [ "$PGHOST" = "db" ]; then
  # Nombre de servicio de docker-compose: solo resuelve dentro de
  # aetheris_network. Este script corre desde el host.
  PGHOST="localhost"
fi
export PGHOST
export PGPORT="${POSTGRES_PORT:-5432}"
export PGUSER="${POSTGRES_USER:?Definir POSTGRES_USER}"
export PGDATABASE="${POSTGRES_DB:?Definir POSTGRES_DB}"
# PGPASSWORD se toma del entorno si esta definida.

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

pg_dump --data-only --disable-triggers \
  --exclude-table=regiones \
  --exclude-table=tipos_evento \
  --exclude-table=fuentes_datos \
  --exclude-table=schema_migrations \
  | grep -vE 'DISABLE TRIGGER ALL;|ENABLE TRIGGER ALL;' > "$tmp"

if grep -E 'DISABLE TRIGGER ALL;|ENABLE TRIGGER ALL;' "$tmp" >/dev/null; then
  echo "El post-proceso no elimino todos los toggles de trigger" >&2
  exit 1
fi

mv "$tmp" "$DESTINO"
trap - EXIT
echo "Escrito $DESTINO"
sha256sum "$DESTINO"
