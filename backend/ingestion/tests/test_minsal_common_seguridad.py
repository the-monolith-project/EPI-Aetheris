"""
Regresion del fix de path traversal en minsal.common._nombre_desde_url_directa
(vulnerabilidad reportada por Sentinel, ver .jules/sentinel.md). Un unico
unquote() dejaba una capa residual de encoding explotable: _clean_filename
volvia a hacer unquote() internamente sin re-extraer el basename, asi que
un payload con doble encoding (%252e%252e%252f) se decodificaba en dos
pasos hasta convertirse en "../" dentro del nombre de archivo final.

No toca Postgres ni PDFs.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from minsal.common import _nombre_desde_url_directa  # noqa: E402


def test_encoding_simple_no_produce_traversal():
    url = "https://salud.gob.sv/wp-content/uploads/%2e%2e%2fetc%2fpasswd.pdf"
    nombre = _nombre_desde_url_directa(url)
    assert "/" not in nombre
    assert ".." not in nombre


def test_encoding_doble_no_produce_traversal():
    # %252e%252e%252f -> (1er unquote) %2e%2e%2f -> (2do unquote) ../
    url = "https://salud.gob.sv/wp-content/uploads/%252e%252e%252fetc%252fpasswd.pdf"
    nombre = _nombre_desde_url_directa(url)
    assert "/" not in nombre
    assert ".." not in nombre


def test_encoding_triple_no_produce_traversal():
    url = "https://salud.gob.sv/wp-content/uploads/%25252e%25252e%25252fetc%25252fpasswd.pdf"
    nombre = _nombre_desde_url_directa(url)
    assert "/" not in nombre
    assert ".." not in nombre


def test_nombre_normal_no_se_altera():
    url = "https://salud.gob.sv/wp-content/uploads/2023/09/SE352023.pdf"
    assert _nombre_desde_url_directa(url) == "SE352023.pdf"
