"""
Exporta la salida de la corrida exploratoria de IRA (corrida_ira.py) a un JSON
estatico para la seccion web de exploracion (web/public/datos-exploracion/).

NO toca PostgreSQL y NO fabrica datos: solo re-formatea lo que la corrida ya
extrajo de los boletines reales a data/interim/corrida_ira/. El JSON generado
es dato intermedio y queda gitignoreado igual que data/interim/ -- si no
existe, la pagina /ira muestra un estado vacio explicando como generarlo,
nunca un dato inventado.

Uso:
    python3 corrida_ira.py            # primero: genera data/interim/corrida_ira/
    python3 exportar_ira_web.py       # despues: vuelca el JSON para la web
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).parent
INTERIM = RAIZ / "data" / "interim" / "corrida_ira"
SALIDA = RAIZ.parent.parent / "web" / "public" / "datos-exploracion" / "ira.json"


def main() -> None:
    desacumulado = INTERIM / "desacumulado_ira_semanal.csv"
    bitacora = INTERIM / "bitacora_ira.csv"
    if not desacumulado.exists() or not bitacora.exists():
        raise SystemExit(
            "Falta la salida de corrida_ira.py en data/interim/corrida_ira/ -- "
            "correr primero: python3 corrida_ira.py"
        )

    # Series desacumuladas: departamento -> anio -> [[semana, valor|null, nota?]]
    series: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    with open(desacumulado, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            valor = int(float(fila["valor"])) if fila["valor"] != "" else None
            punto = [int(fila["semana"]), valor]
            if fila["nota"]:
                punto.append(fila["nota"])
            series[fila["departamento"]][fila["anio"]].append(punto)
    for anios in series.values():
        for puntos in anios.values():
            puntos.sort(key=lambda p: p[0])

    # Resumen de estados de extraccion por anio (auditoria del dato).
    estados_por_anio: dict[str, Counter] = defaultdict(Counter)
    with open(bitacora, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila["anio"]:
                estados_por_anio[fila["anio"]][fila["estado"]] += 1

    salida = {
        "generado": date.today().isoformat(),
        "fuente": (
            "Boletines epidemiologicos MINSAL (tabla departamental de IRA), "
            "extraccion exploratoria corrida_ira.py -- serie acumulada desde SE1 "
            "desacumulada por diferencia entre cortes consecutivos"
        ),
        "advertencia": (
            "Dato exploratorio, NO ingerido al sistema (clasificacion pendiente de "
            "ADR 0011). Conteo clinico unico: la fuente no publica split "
            "probable/confirmado departamental para IRA."
        ),
        "estados_extraccion": {a: dict(c) for a, c in sorted(estados_por_anio.items())},
        "series": {d: dict(a) for d, a in sorted(series.items())},
    }

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, separators=(",", ":"))
    n_puntos = sum(len(p) for a in series.values() for p in a.values())
    print(f"-> {SALIDA}  ({len(series)} departamentos, {n_puntos} puntos)")


if __name__ == "__main__":
    main()
