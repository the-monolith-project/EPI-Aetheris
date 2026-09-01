"""Configuración compartida de la suite de tests de la API.

El rate limiting (issue #61) se desactiva por defecto durante los tests: las
suites existentes disparan muchas peticiones seguidas con el mismo TestClient
(misma IP) y de otro modo tropezarían con el límite. El test que sí verifica
el rate limiting (test_rate_limiting.py) lo reactiva explícitamente vía
monkeypatch + reload, siguiendo el mismo idiom que test_cors.py.
"""
import os

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
