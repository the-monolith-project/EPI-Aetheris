import pytest
import sys
from pathlib import Path

# Fix Python path for importing from parent directory
sys.path.append(str(Path(__file__).resolve().parent.parent))

from entrenar_clasificador import formatear_recall_alto

def test_formatear_recall_alto():
    # Note: The issue states the signature is `def formatear_recall_alto(r: float | None) -> str:`
    # but the actual code has `def formatear_recall_alto(valor: float | None, n_alto_real: int) -> str:`
    # The actual implementation:
    # def formatear_recall_alto(valor: float | None, n_alto_real: int) -> str:
    #     if valor is None:
    #         return f"N/A -- 0 casos reales de 'alto' en el conjunto evaluado ({n_alto_real} soporte)"
    #     return f"{valor:.3f}"

    # Test None
    assert formatear_recall_alto(None, 42) == "N/A -- 0 casos reales de 'alto' en el conjunto evaluado (42 soporte)"

    # Test 0.0
    assert formatear_recall_alto(0.0, 10) == "0.000"

    # Test 1.0
    assert formatear_recall_alto(1.0, 10) == "1.000"

    # Test typical decimal values
    assert formatear_recall_alto(0.5234, 10) == "0.523"
    assert formatear_recall_alto(0.9999, 10) == "1.000"
    assert formatear_recall_alto(0.5235, 10) == "0.523"  # In python f-string, round to half even applies
