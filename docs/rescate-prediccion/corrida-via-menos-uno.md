# Corrida reproducible — Vía −1

**Fecha:** 2026-08-18

**Estado:** mecanismo técnico validado

**Interpretación permitida:** validación forward-chaining exploratoria

**Interpretación no permitida:** desempeño final independiente

## Resultado

La Vía −1 reproduce exactamente la estructura declarada antes de ejecutar y demuestra que el
pipeline puede separar años sin fuga temporal. También confirma la limitación estructural prevista:
no existe ningún fold que contenga semanas `alto` tanto en el entrenamiento como en el externo.

El único externo con semanas `alto` es 2022, con 5. Su entrenamiento contiene 150 semanas `bajo`, 2
`medio` y cero `alto`. El Random Forest predice `bajo` en las 52 semanas en las 10 semillas de
estabilidad: F1 macro 0,273 y recall de `alto` 0,000, es decir, **0 aciertos de 5**. Iguala a las
referencias climatológica y constante mayoritaria; no las supera.

Esto valida el mecanismo de evaluación, no el desempeño predictivo. No existe un test que sea a la
vez intacto y evaluable para recall de `alto`.

## Fuente y configuración congeladas

- Seed: `db/seed/seed_datos_reales.sql`.
- SHA-256 del seed: `25feff52b0347244814545522925dd924c3fb1a5f9c678aeffd2764515921bed`.
- Manifiesto: `backend/ingestion/via_menos_uno_manifesto_congelado.json`.
- SHA-256 del manifiesto: `92694553865f8d156759072d04c6d46c01a2c0a7b67ba2e4f0789e7d6897309d`.
- Script: `backend/ingestion/validar_via_menos_uno.py`.
- SHA-256 del script ejecutado: `b8c2cb70ca90d81dadab90a5dd92f4d14dd7e8fdbbed17cd1cc3c03d6a6a07f0`.
- Entorno: Python 3.11.15, NumPy 2.4.6 y scikit-learn 1.5.1 dentro de la imagen del backend.
- Dataset prospectivo: 308 filas y 21 predictores.
- Modelo: Random Forest, 300 árboles, `class_weight="balanced"`, argmax.
- Semillas de estabilidad: 0–9. Semilla 42 separada como referencia histórica.

El script verifica el hash antes de leer el seed y aborta si no coincide. No se conecta a PostgreSQL,
no guarda modelos y no toca artefactos de producción.

## Reproducción de etiquetas

| Año | Historia permitida | Sin etiqueta | Bajo | Medio | Alto |
|---|---|---:|---:|---:|---:|
| 2016 | 2014–2015 | 52 | 0 | 0 | 0 |
| 2017 | 2014–2016 | 52 | 0 | 0 | 0 |
| 2018 | 2014–2017 | 2 | 50 | 0 | 0 |
| 2019 | 2014–2018 | 2 | 48 | 2 | 0 |
| 2021 | 2014–2019, sin 2020 | 0 | 52 | 0 | 0 |
| 2022 | 2014–2021, sin 2020 | 0 | 36 | 11 | 5 |
| 2023 | 2014–2022, sin 2020 | 0 | 52 | 0 | 0 |
| 2024 | 2014–2023, sin 2020 | 0 | 52 | 0 | 0 |

Las cuatro celdas descartadas del corpus objetivo son las semanas de borde de 2018 y 2019. No hubo
descarte por clima ni imputación.

## Folds observados

| Externo | Entrenamiento | Distribución de entrenamiento | Distribución externa | Estado |
|---|---|---|---|---|
| 2019 | 2018 | 50 bajo | 48 bajo, 2 medio | `no_entrenable` |
| 2021 | 2018, 2019 | 98 bajo, 2 medio | 52 bajo | `entrenable_con_clase_ausente` + recall `N/A` |
| 2022 | 2018, 2019, 2021 | 150 bajo, 2 medio | 36 bajo, 11 medio, 5 alto | `entrenable_con_clase_ausente` |
| 2023 | 2018, 2019, 2021, 2022 | 186 bajo, 13 medio, 5 alto | 52 bajo | `entrenable` + recall `N/A` |
| 2024 | 2018, 2019, 2021, 2022, 2023 | 238 bajo, 13 medio, 5 alto | 52 bajo | `entrenable` + recall `N/A` |

La firma coincide con la declaración previa sin una sola diferencia.

## Métricas

Los valores del modelo son el rango mínimo–máximo de las semillas 0–9. Todos los rangos colapsan a
un único valor; la semilla 42 produce el mismo resultado.

| Externo | F1 macro modelo | Recall `alto` modelo | F1 climatológica | Recall `alto` climatológica | F1 mayoritaria | F1 siempre `alto` | F1 persistencia |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | N/A | N/A | 0,327 | N/A | 0,327 | 0,000 | 0,319 |
| 2021 | 0,333–0,333 | N/A | 0,333 | N/A | 0,333 | 0,000 | 0,333 |
| 2022 | 0,273–0,273 | 0,000 — 0 de 5 | 0,273 | 0,000 — 0 de 5 | 0,273 | 0,058 | 0,766 |
| 2023 | 0,333–0,333 | N/A | 0,333 | N/A | 0,333 | 0,000 | 0,333 |
| 2024 | 0,333–0,333 | N/A | 0,333 | N/A | 0,333 | 0,000 | 0,333 |

En 2022, la referencia siempre `alto` obtiene recall 1,000 —5 de 5— a costa de 47 falsos positivos.
Persistencia obtiene recall 0,600 —3 de 5—, F1 macro 0,766 y 2 falsos positivos sobre 51 filas
evaluables. Se reporta como referencia retrospectiva no desplegable: utiliza la etiqueta real de la
semana anterior y resuelve una tarea distinta al modelo solo-clima.

El AUC de `alto` en 2022 es 0,500 porque el entrenamiento no contiene esa clase y la probabilidad
asignada a `alto` es cero en todas las filas. No representa capacidad de ordenamiento.

## Pruebas contra fuga

Se ejecutaron 17 pruebas sobre el seed real. Cubren:

1. independencia de etiquetas y matrices de entrenamiento ante cambios en casos del externo;
2. independencia de features de entrenamiento ante cambios en clima del externo;
3. independencia completa ante cambios en años posteriores;
4. exclusión de año objetivo, años futuros y 2020 de `H(y)`;
5. reutilización idéntica de una etiqueta entre folds;
6. ventana ±1 sin cruce de año y respeto de observaciones ausentes;
7. rezagos por `fecha_inicio`, incluidos cruces de años de 52 y 53 semanas;
8. exclusión de clima faltante sin cero ni imputación;
9. conservación de F1, matriz y falsos positivos cuando recall de `alto` es `N/A`;
10. configuración fija independiente del externo;
11. desempate climatológico por moda global y luego por orden fijo;
12. rechazo de 2016 por insuficiencia de historia;
13. aislamiento de la salida respecto de PostgreSQL y los artefactos del modelo.

Comando limpio:

```bash
docker compose run --no-deps --rm \
  -v "$PWD/db:/workspace/db:ro" \
  -e VIA_MENOS_UNO_SEED_SQL=/workspace/db/seed/seed_datos_reales.sql \
  backend python -m unittest ingestion.tests.test_validar_via_menos_uno -v
```

Resultado: `Ran 17 tests ... OK`.

### Mutación deliberada

La variable `VIA_MENOS_UNO_MUTACION_FUGA=1` hace que, solo dentro del archivo de pruebas, el año
externo 2022 entre deliberadamente en los pools que etiquetan entrenamiento. No modifica el script de
ejecución.

Prueba ejecutada:

```text
test_cambiar_casos_externo_no_modifica_entrenamiento ... FAIL
esperado limpio: 2018-SE02, P75=373,0, P90=389,0
con fuga y externo alterado: 2018-SE02, P75=535,5, P90=1.000.155,8
FAILED (failures=1)
```

Al retirar la variable de mutación, la misma prueba terminó `OK`. La implementación permanente quedó
limpia.

## Reproducibilidad

Dos ejecuciones consecutivas produjeron artefactos sustantivos idénticos byte por byte:

| Artefacto | SHA-256 |
|---|---|
| `etiquetas.csv` | `0f2ff2f90afd09389f1e08a0cd96dce42288761232a7c116529a1b976dc17d36` |
| `dataset.csv` | `5fad743e245f54d8e6640d7de63e33f7dec66789ddf9cc952a0285978f9c7ec7` |
| `predicciones.csv` | `4c62d92b41bd6179439385f100ee803e1c7df5a53271e2dce09d40ab70ec89ea` |
| `metricas.json` | `0cab1a5e8daacd28749f062d50457ef422a789c7c0e8e8baaab2e7f1e9c6d001` |

`manifiesto_ejecucion.json` y `ejecucion.log` incluyen la hora de ejecución, por lo que esa metadata
no es byte-idéntica por diseño.

## Artefactos locales

La corrida escribe únicamente en `backend/ingestion/data/interim/via_menos_uno/`, ruta ignorada por
Git:

- `manifiesto_ejecucion.json`;
- `etiquetas.csv`;
- `dataset.csv`;
- `predicciones.csv`;
- `metricas.json`;
- `ejecucion.log`.

Para repetir la corrida:

```bash
docker compose run --no-deps --rm \
  -v "$PWD/db:/workspace/db:ro" \
  backend python ingestion/validar_via_menos_uno.py \
  --seed-sql /workspace/db/seed/seed_datos_reales.sql
```

## Estado de la puerta

Quedan cumplidos el script separado, el manifiesto congelado, las pruebas de independencia y la
demostración negativa ante fuga. El registro formal de D1 y D3 sigue a cargo del coordinador. No se
inicia ninguna Vía 0–3 hasta que ese registro cierre el último elemento pendiente de la puerta.

### Corrección factual del calendario

Durante la validación se comprobó con `epiweeks` que el calendario CDC/MMWR tiene años de 52 o 53
semanas, no de 51. Para 1900–2100 la biblioteca devuelve 165 años de 52 semanas y 36 de 53. Se
corrigieron las dos menciones del protocolo. El algoritmo ya estaba basado en `fecha_inicio`, por lo
que la corrección no modifica código, filas ni resultados.
