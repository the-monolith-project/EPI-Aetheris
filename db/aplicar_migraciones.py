"""
Runner minimo de migraciones para una base ya inicializada.

`docker-entrypoint-initdb.d` corre db/migrations/*.sql una sola vez, sobre
volumen vacio, al crear el contenedor de Postgres -- una migracion agregada
despues nunca se aplica sola sobre una base que ya existe. Este script cubre
ese caso, via una tabla `schema_migrations` que registra que archivos ya
corrieron. Ver docs/adr/0009-runner-minimo-de-migraciones.md para el porque.

Uso (desde el host, con el stack levantado -- el puerto 5432 esta publicado
por docker-compose.yml):

    python db/aplicar_migraciones.py --bootstrap   # una sola vez, ver ADR 0009 punto C
    python db/aplicar_migraciones.py               # aplica lo nuevo

Requiere psycopg2 y python-dotenv (ya en backend/requirements.txt; usar
backend/.venv o instalar ambos en el entorno desde el que se corra).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).parent.parent
_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _conectar() -> psycopg2.extensions.connection:
    load_dotenv(_REPO_ROOT / ".env")
    return psycopg2.connect(
        host=os.getenv("MIGRACIONES_POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT", "5432"),
    )


def _tabla_existe(cur, nombre: str) -> bool:
    cur.execute("SELECT to_regclass(%s) IS NOT NULL", (nombre,))
    return cur.fetchone()[0]


def _archivos_migracion() -> list[Path]:
    return sorted(_MIGRATIONS_DIR.glob("*.sql"))


def _checksum(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def bootstrap(conn) -> None:
    with conn.cursor() as cur:
        if _tabla_existe(cur, "schema_migrations"):
            print("schema_migrations ya existe -- no se vuelve a sembrar. Usa la corrida normal.")
            return

        cur.execute(
            """
            CREATE TABLE schema_migrations (
                filename    text PRIMARY KEY,
                checksum    text NOT NULL,
                applied_at  timestamptz NOT NULL DEFAULT now()
            )
            """
        )

        archivos = _archivos_migracion()
        for ruta in archivos:
            cur.execute(
                "INSERT INTO schema_migrations (filename, checksum) VALUES (%s, %s)",
                (ruta.name, _checksum(ruta)),
            )
        conn.commit()
        print(f"schema_migrations creada. Sembrados como ya aplicados ({len(archivos)}):")
        for ruta in archivos:
            print(f"  - {ruta.name}")


def aplicar_pendientes(conn) -> None:
    with conn.cursor() as cur:
        if not _tabla_existe(cur, "schema_migrations"):
            sys.exit(
                "schema_migrations no existe todavia. Corre primero:\n"
                "  python db/aplicar_migraciones.py --bootstrap"
            )

        cur.execute("SELECT filename, checksum FROM schema_migrations")
        aplicadas = dict(cur.fetchall())

    pendientes = [r for r in _archivos_migracion() if r.name not in aplicadas]

    for ruta in _archivos_migracion():
        if ruta.name in aplicadas and _checksum(ruta) != aplicadas[ruta.name]:
            print(
                f"AVISO: {ruta.name} ya estaba aplicado pero su contenido cambio "
                "desde entonces (checksum no coincide). No se reaplica solo -- "
                "revisar manualmente."
            )

    if not pendientes:
        print("Nada pendiente. La base ya tiene todas las migraciones de db/migrations/.")
        return

    for ruta in pendientes:
        sql = ruta.read_text()
        with conn.cursor() as cur:
            try:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (filename, checksum) VALUES (%s, %s)",
                    (ruta.name, _checksum(ruta)),
                )
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()
        print(f"aplicada: {ruta.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Crea schema_migrations y siembra los archivos actuales como ya aplicados (una sola vez).",
    )
    args = parser.parse_args()

    conn = _conectar()
    try:
        if args.bootstrap:
            bootstrap(conn)
        else:
            aplicar_pendientes(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
