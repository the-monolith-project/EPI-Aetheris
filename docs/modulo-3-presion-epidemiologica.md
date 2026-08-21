# Módulo 3 — Presión epidemiológica relativa (fórmula cerrada e implementación)

- **Fecha:** 2026-08-21
- **Estado:** fórmula cerrada por el coordinador del proyecto; implementada en `backend/api/presion.py`, servida por `GET /api/v1/presion/current?week=&year=` y `GET /api/v1/presion/temporal/{departamento_codigo}?anio=`.
- **Contexto previo:** la decisión estuvo abierta desde el pivote "Camino Ancho" (`docs/informe-cierre-rescate-prediccion.md`, punto en `docs/contexto/02-decisiones-abiertas.md`) precisamente para que nadie inventara cortes, ventana ni piso de suficiencia de forma unilateral. Este documento registra la decisión que la cierra.

## Qué es M3 y qué NO es

M3 responde: **"¿qué tan alta es la presión de casos observados en este departamento-semana comparado con su propia historia?"** — 100% descriptivo.

- **NO es un clasificador**, no predice nada, no usa clima como insumo.
- **NO es una resurrección del clasificador retirado** (`entrenar_clasificador.py`): no comparte código ni lógica con él. Lo que hereda es la metodología de canal endémico percentilar (`backend/ingestion/corrida_canal_endemico_nacional.py`), que el informe de cierre mantiene explícitamente como comparación histórica descriptiva válida.
- **NO produce alertas binarias.** La lectura cualitativa (baja/media/alta) es texto libre descriptivo, acompañada siempre del percentil relativo crudo — nunca un campo booleano de alerta.

## Fórmula (decisión cerrada — no ajustar sin nueva decisión del coordinador)

| Elemento | Decisión |
|---|---|
| Variable base | `casos_epidemiologicos.conteo`, `clasificacion IN ('probable','confirmado')` como **dos series separadas** (nunca fusionadas, nunca `total` — ADR 0005), regiones `nivel_admin = 1` |
| Método | Percentil histórico leave-one-out, mismo patrón que `corrida_canal_endemico_nacional.py` |
| Años base | 2018, 2019, 2021, 2022, 2023 (2020 excluido del baseline: colapso real de vigilancia, no baja transmisión — exclusión de ventana de comparación, no de ingesta) |
| Anti-fuga | Leave-one-out estricto: el año descrito nunca aparece en su propio baseline |
| Ventana | ±1 semana (actual, anterior, siguiente), **sin envolver entre años** |
| Piso de suficiencia | Al menos **3 de los 4 años** leave-one-out aportan alguna observación en la ventana ±1 (cuentan años distintos, no semanas) |
| Cortes | **P50 y P75** sobre el pool del baseline |
| Insuficiencia | `percentil = null` + nota explícita — nunca se inventa ni interpola un valor |

**Sobre los cortes P50/P75:** la corrida nacional validada (`docs/corrida-canal-endemico-nacional.md`) mostró que P75/P90 fue el esquema que mejor separó los años pico. El coordinador eligió **deliberadamente** P50/P75 para M3: es más sensible y se acepta que pueda sobre-etiquetar semanas de años de baja transmisión. Es un trade-off consciente, no un error a corregir.

**Lectura cualitativa:** valor ≤ P50 → `baja`; P50 < valor ≤ P75 → `media`; valor > P75 → `alta`. La igualdad exacta con el corte cae hacia abajo (misma convención que `corrida_canal_endemico_nacional.clasificar`). Además de la categoría se expone el **percentil relativo crudo** (0–100) del valor observado dentro del pool — la inversa de la interpolación lineal de `percentil()`, con empates resueltos al punto medio — igual que M1/M2 exponen `iv` y `anomaly_sigma` continuos.

## Dónde vive el output

Igual que M1/M2: **calculado on-request, nada persistido, sin cambios de esquema.** La pregunta abierta "¿dónde vive el output de M3/M4?" queda resuelta para M3 (mismo patrón on-request); sigue abierta para M4.

## Ejemplo de output real (docker-compose + `db/seed/seed_datos_reales.sql`, 2026-08-21)

`GET /api/v1/presion/current?week=24&year=2019` — 2019 es el año del pico histórico nacional. Extracto (serie `probable`):

| Departamento | Casos obs. | Percentil | Categoría | P50/P75 baseline | n pool / años |
|---|---|---|---|---|---|
| SV-SO (Sonsonate) | 39 | 100.0 | alta | 0.0 / 0.0 | 12 / 4 |
| SV-SS (San Salvador) | 21 | 100.0 | alta | 0.0 / 0.0 | 12 / 4 |
| SV-LI (La Libertad) | 11 | 100.0 | alta | 0.0 / 0.5 | 11 / 4 |
| SV-SA (Santa Ana) | 5 | 100.0 | alta | 0.0 / 0.8 | 12 / 4 |

8 de 14 departamentos salen en `alta` esa semana — consistente con el pico real de 2019 y con un baseline dominado por ceros (87–93% de las celdas departamento-semana de la fuente MINSAL desacumulada son cero, ver `docs/contexto/03-fuentes-de-datos.md`).

Celda insuficiente real: `GET /api/v1/presion/current?week=52&year=2021`, SV-SS serie `probable` — 0 de los 4 años leave-one-out tienen observaciones en la ventana ±1 (los boletines de fin de año son semanas festivas sin tabla departamental):

```json
{
  "casos_observados": null,
  "percentil": null,
  "categoria": null,
  "p50_baseline": null,
  "p75_baseline": null,
  "n_obs_baseline": 0,
  "anios_baseline": 0,
  "nota": "sin datos suficientes para baseline (menos de 3 años base con observaciones en la ventana ±1)"
}
```

## Limitaciones honestas

- La serie MINSAL desacumulada es **estructuralmente escasa** (huecos por semanas festivas, tablas en imagen sin OCR, correcciones retroactivas excluidas): los pools de baseline están dominados por ceros, así que una sola observación positiva puede caer en percentil 100. El percentil describe la historia *observada*, no la transmisión real subyacente.
- `probable` y `confirmado` **no son comparables entre sí** — definiciones distintas, magnitudes distintas. Por eso son dos series separadas de punta a punta (backend y UI).
- Las semanas 51–52 son insuficientes en casi todos los años (boletines festivos de fin de año): eso es la fuente, no un bug.
- Nada aquí pronostica: un percentil alto dice que lo ya observado es inusual contra la propia historia del departamento, no que vaya a pasar algo.

## Pruebas

- `backend/api/tests/test_presion.py` — lógica pura: anti-fuga, ventana ±1 sin wrap, piso de suficiencia (años distintos, no semanas), bordes de categoría, inversa del percentil, empates.
- `backend/api/tests/test_endpoints_presion.py` — endpoints contra la base real sembrada (se omiten sin Postgres): semana pico 2019 con `alta` real, celda insuficiente con nota, 422/404, ausencia de campos de alerta/predicción retirados.
