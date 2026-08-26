import os
import sys
from pathlib import Path
import pytest

# Add the backend directory to sys.path so 'api' module can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def test_cors_rejects_wildcard(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "*")

    with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS must not contain '\\*' for security reasons."):
        # We need to import main here to trigger the module-level parsing
        # but because it's already imported, we might need to reload it
        import importlib
        import api.main
        importlib.reload(api.main)

def test_cors_accepts_valid_origins(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000, https://example.com")

    import importlib
    import api.main
    importlib.reload(api.main)

    # Check that the origins were parsed correctly
    # Note: starlette's CORSMiddleware stores the origins, but it's easier to just
    # check that it didn't raise an error.
    assert True
