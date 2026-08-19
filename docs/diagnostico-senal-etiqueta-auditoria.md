# Auditoría del diagnóstico de señal y etiqueta

**Fecha:** 2026-08-17  
**Alcance:** incorporación de los artefactos recibidos en `docs/tobeer/`  
**Resultado:** reproducido con las dependencias del proyecto

## Procedencia recibida

El paquete declara que un único script contiene cuatro análisis:

1. barrido de umbral y AUC;
2. comparación de Random Forest, Gradient Boosting, Extra Trees y regresión logística;
3. pool de percentiles no pareado por semana;
4. preliminar de etiqueta intraanual.

Archivos recibidos:

| Archivo | SHA-256 |
|---|---|
| `LEEME-procedencia.md` | `989a52e62bd89f61550dc342b8292eda2122e1edda407a86326463940476084e` |
| `diagnostico_senal_etiqueta_auditable.py` original | `c1f0b821132787576f00fd567639a79714156d83accd78506d69f21243b1f53d` |
| `corrida_completa.log` | `ee6055f5ab76586df31321b9f689ee9306f6d73b5c9306b5c4f499dfe4d626f8` |
| `probabilidades_por_fila.csv` | `c688466b4b8651da03ee2bd33f2d366fc6d50fd305d42115c1badb45bf4da267` |
| `resultados_diagnostico.json` | `63db479ddaac57abf0e7c6a9f43a646a862ce98cc8735515881458f617e41447` |

El log original registra Python 3.12.3, NumPy 2.4.4 y scikit-learn 1.8.0. El proyecto fija
scikit-learn 1.5.1, por lo que esas salidas no se aceptaron sin una nueva corrida.

## Reproducción independiente

Se reconstruyó la imagen `backend` desde `backend/requirements.txt` y se ejecutó el script contra:

- `db/seed/seed_datos_reales.sql`;
- tamaño: 4.435.319 bytes;
- SHA-256: `25feff52b0347244814545522925dd924c3fb1a5f9c678aeffd2764515921bed`.

Entorno resuelto:

- Python 3.11.15;
- scikit-learn 1.5.1;
- NumPy 2.4.6.

Comando de reproducción del original:

```bash
docker compose run --rm --no-deps -T \
  -v /home/isaac/Documentos/EPI-Aetheris:/repo \
  -w /repo backend \
  python docs/tobeer/diagnostico_senal_etiqueta_auditable.py \
  --seed-sql db/seed/seed_datos_reales.sql \
  --salida backend/ingestion/data/interim/diagnostico_reproduccion
```

El JSON, excluyendo fecha y metadatos de entorno, fue idéntico al recibido. El CSV de probabilidades
fue idéntico byte por byte y conservó el mismo SHA-256.

## Resultados reproducidos

### Dataset y etiqueta

- 250 filas;
- 21 predictores;
- correlación entre total anual y semanas `alto`: 0,955;
- dos de cinco años con alguna semana `alto`.

### Modelo de referencia

| Año | F1 macro actual | Recall alto | Aciertos |
|---|---:|---:|---:|
| 2019 | 0,102 | 0,000 | 0 de 28 |
| 2022 | 0,240 | 0,000 | 0 de 22 |

El F1 0,240 de 2022 corresponde al seed actual de 250 filas. El informe histórico que reporta 0,169
fue generado cuando el dataset tenía 247 filas. El recall alto 0 de 22 no cambia.

### AUC y umbral

| Año | AUC P(alto) | Umbral 0,05: recall | Umbral 0,05: precisión | Umbral 0,05: F1 macro |
|---|---:|---:|---:|---:|
| 2019 | 0,234 | 0,179 (5 de 28) | 0,238 | 0,086 |
| 2022 | 0,231 | 0,500 (11 de 22) | 0,324 | 0,169 |

La afirmación correcta no es que ningún umbral produzca recall. Un umbral bajo sí produce aciertos,
pero no supera simultáneamente F1 macro y recall frente a la climatológica. Además, el barrido se hizo
sobre los años externos y es descriptivo; no constituye selección válida de un umbral desplegable.

### Algoritmos

Los cuatro algoritmos obtuvieron recall alto 0 en 2019 y 2022. Cambiaron F1 y falsos positivos, pero
ninguno identificó una semana alta real mediante `argmax`.

### Pool no pareado

Ninguna combinación reportada de P75/P90 o P50/P75 superó simultáneamente el criterio histórico por
año. Este experimento cambia la semántica del canal y permanece descartado.

### Preliminar intraanual

| Año | Semillas que superan el criterio histórico |
|---|---:|
| 2018 | 0/10 |
| 2019 | 6/10 |
| 2021 | 0/10 |
| 2022 | 10/10 |
| 2023 | 7/10 |

La etiqueta fuerza 13 semanas `alto` en cada año, incluidos años de transmisión baja. Este resultado
es reproducible, pero cambia la pregunta del producto, utiliza el año completo para definir la verdad
y no constituye evidencia suficiente para adopción.

## Copia auditada incorporada

El código incorporado vive en:

`backend/ingestion/diagnostico_senal_etiqueta_auditable.py`

Respecto del original:

- declara explícitamente que reproduce la validación retrospectiva legada;
- no se presenta como implementación de la Vía −1;
- registra SHA-256 del seed;
- fija las tres clases al calcular F1 macro;
- conserva métricas de años sin `alto` y muestra recall `N/A`;
- corrige el texto del barrido de umbral;
- mantiene resultados de 2019, 2022, AUC y Vía 2.

Se agregaron cuatro pruebas unitarias en
`backend/ingestion/tests/test_diagnostico_senal_etiqueta.py`; pasan bajo la imagen backend.

## Límites pendientes

1. NumPy es una dependencia transitiva no fijada en `backend/requirements.txt`; la reconstrucción
   resolvió 2.4.6. La réplica coincidió, pero el entorno no está congelado completamente.
2. El diagnóstico conserva deliberadamente el split retrospectivo contaminado para reproducir los
   informes. No debe usarse para afirmar desempeño prospectivo.
3. La selección interna de umbral mencionada en la procedencia no fue entregada y debe reimplementarse
   únicamente después de aprobar el protocolo de la Vía −1.
4. Los resultados generados permanecen en `data/interim/` y no se versionan; el código y este informe
   son los artefactos permanentes.

