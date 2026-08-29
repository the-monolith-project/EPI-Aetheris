# Corrida reproducible — Vía 0

**Fecha:** 2026-08-18

**Estado técnico:** completada

**Veredicto predeclarado:** cerrar la vía multipaís por falta de transferencia

**Recomendación:** no adoptar el clasificador regional para El Salvador ni continuar ajustando esta
vía sin una hipótesis distinta

**Interpretación permitida:** diagnóstico exploratorio de transferencia espacial con validación
temporal forward-chaining

**Interpretación no permitida:** desempeño final independiente o modelo regional desplegable

## Resultado

Ninguno de los 16 países cumple la condición predeclarada de transferencia sostenida. De 52 folds
evaluables para recall de `alto`, solo uno consigue éxito estable en las 10 semillas: Bolivia 2024.
Costa Rica 2023 lo consigue en 5 de 10 semillas y Jamaica 2023 en 1 de 10. Los otros 49 folds
evaluables obtienen 0 de 10.

En total, el criterio se cumple en 16 de 520 combinaciones fold–semilla evaluables. Ese resultado no
se distribuye entre países: 10 de los 16 éxitos pertenecen al único fold estable. Por tanto, el éxito
retrospectivo de la corrida regional anterior no se transfiere a países no vistos de forma estable.

La regla congelada antes de entrenar clasificaba la vía así:

- 0–8 países con transferencia sostenida: cerrar la vía multipaís;
- 9–11: resultado inconcluso;
- 12–16: transferencia mayoritaria confirmada.

El resultado observado es **0 de 16**, sin proximidad al intervalo inconcluso.

## Diseño ejecutado

Cada fold mantiene simultáneamente dos separaciones:

1. el país externo queda completamente fuera del entrenamiento;
2. para un año externo `t`, el entrenamiento contiene únicamente años objetivo anteriores a `t` de
   los demás países.

Las etiquetas se construyen por separado dentro de cada país mediante la historia expansiva `H(y)`.
2020 no participa como objetivo ni en ningún pool histórico. El año externo, los años futuros y el
país externo no entran en entrenamiento, selección o transformaciones. No hubo selección de
hiperparámetros ni barrido de umbral: Random Forest de 300 árboles, `class_weight="balanced"` y
argmax quedaron fijos antes de correr.

Un fold es éxito estable solo si las 10 semillas 0–9 superan a la referencia climatológica en F1
macro y recall de `alto` sin que la constante mayoritaria o la constante siempre `alto` active el
veto por F1 macro. Un país requiere por lo menos dos folds evaluables y éxito estable en todos. La
semilla 42 se conserva únicamente como referencia histórica y no decide el veredicto.

## Fuentes y preparación congeladas

- OpenDengue: `Temporal_extract_PAHO_V1_3.csv`, Admin0, semanal, definición `Total`.
- SHA-256 del CSV: `f8eaa7134dd7e4a718df16ec5e2bfdd60bf446732281a1bbf3a1463084af230f`.
- Clima: Open-Meteo Archive, `era5_land` para cinco variables de superficie y `era5` para dos de
  precipitación.
- SHA-256 del JSON climático: `bd97df3c2c21964fafbfc291d7ea76f10a08180731facfb6cc378b221d4e0a6a`.
- Manifiesto: `backend/ingestion/via_cero_manifesto_congelado.json`.
- Firma previa de los folds: `7373de45c428f341b39c57d0b90a787870081a9a2b2d9d83bdb06b601f74dd89`.
- Entorno: Python 3.11.15, NumPy 2.4.6 y scikit-learn 1.5.1 dentro de la imagen del backend.

El extracto contiene 10.332 filas para 18 países, exactamente 574 por país entre 2014 y 2024 según
el calendario CDC/MMWR. La semana se resolvió desde `calendar_start_date`, no desde la columna
`Year`: 90 filas declaran un año calendario distinto del año epidemiológico. Bermuda y Virgin
Islands (US) quedaron fuera porque las cinco variables de `era5_land` están ausentes en sus 574
semanas; no se imputaron valores ni se transformó ausencia en cero.

El dataset final contiene:

- 16 países;
- 4.928 filas;
- 21 predictores climáticos;
- 64 celdas descartadas por insuficiencia de la etiqueta;
- 80 folds, todos entrenables;
- 52 folds con por lo menos una semana externa `alto`;
- 28 folds con recall de `alto` en `N/A`, conservados para las demás métricas.

## Resultado por país

| País externo | Años evaluables para `alto` | Años con éxito estable | Veredicto |
|---|---|---|---|
| Barbados | 2021, 2023, 2024 | ninguno | transferencia no sostenida |
| Bolivia | 2019, 2022, 2023, 2024 | 2024 | transferencia no sostenida |
| Brazil | 2019, 2022, 2023, 2024 | ninguno | transferencia no sostenida |
| Colombia | 2019, 2021, 2023, 2024 | ninguno | transferencia no sostenida |
| Costa Rica | 2023, 2024 | ninguno | transferencia no sostenida |
| Dominican Republic | 2019, 2023, 2024 | ninguno | transferencia no sostenida |
| Ecuador | 2019, 2021, 2023, 2024 | ninguno | transferencia no sostenida |
| El Salvador | 2022 | ninguno | evidencia insuficiente por país; sin éxito |
| Guatemala | 2019, 2023, 2024 | ninguno | transferencia no sostenida |
| Honduras | 2019, 2023, 2024 | ninguno | transferencia no sostenida |
| Jamaica | 2019, 2023, 2024 | ninguno | transferencia no sostenida |
| Mexico | 2019, 2022, 2023, 2024 | ninguno | transferencia no sostenida |
| Nicaragua | 2019, 2023, 2024 | ninguno | transferencia no sostenida |
| Panama | 2019, 2022, 2023, 2024 | ninguno | transferencia no sostenida |
| Puerto Rico | 2022, 2023, 2024 | ninguno | transferencia no sostenida |
| United States of America | 2019, 2022, 2023, 2024 | ninguno | transferencia no sostenida |

El Salvador solo tiene un fold evaluable porque la etiqueta prospectiva produce semanas `alto`
únicamente en 2022. Esa limitación impide atribuirle un veredicto espacial aislado con el mínimo de
dos folds, pero no altera el resultado de conjunto: los otros 15 países tampoco sostienen
transferencia.

## Únicos folds con alguna semilla exitosa

| País y año | `alto` real | Semillas exitosas | F1 modelo | Recall modelo | F1 climatológica | F1 siempre `alto` | F1 persistencia |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bolivia 2024 | 14 | **10/10** | 0,210–0,232 | 0,286–0,357 — 4–5 de 14 | 0,069 | 0,141 | 0,544 |
| Costa Rica 2023 | 21 | 5/10 | 0,198–0,231 | 0,000–0,048 — 0–1 de 21 | 0,198 | 0,192 | 0,808 |
| Jamaica 2023 | 14 | 1/10 | 0,216–0,259 | 0,000–0,071 — 0–1 de 14 | 0,228 | 0,141 | 0,675 |

Bolivia 2024 no basta para sostener transferencia del país: sus otros tres años evaluables fallan en
0 de 10 semillas. Tampoco representa desempeño operacional; aun en ese fold, persistencia obtiene
recall 0,571 —8 de 14— y F1 macro 0,544, muy por encima del modelo solo-clima.

## El Salvador 2022

El único fold evaluable de El Salvador contiene 36 semanas `bajo`, 11 `medio` y 5 `alto`. El
entrenamiento, formado por los otros 15 países y solo por años anteriores, contiene 1.746 `bajo`,
169 `medio` y 365 `alto`.

| Referencia | F1 macro | Recall `alto` | Aciertos |
|---|---:|---:|---:|
| Modelo, semillas 0–9 | 0,268–0,323 | 0,000 | 0 de 5 |
| Climatológica | 0,273 | 0,000 | 0 de 5 |
| Constante mayoritaria | 0,273 | 0,000 | 0 de 5 |
| Siempre `alto` | 0,058 | 1,000 | 5 de 5; 47 falsos positivos |
| Persistencia | 0,766 | 0,600 | 3 de 5; 2 falsos positivos |

Agregar otros países sí aporta cientos de ejemplos `alto` al entrenamiento, pero no produce un
límite climático transferible que detecte los cinco positivos de El Salvador.

## Diferencia respecto de la corrida multipaís histórica

Esta Vía 0 no es una repetición numérica de `docs/experimento-multipais.md`. Corrige cuatro aspectos
que impiden interpretar aquella corrida como evidencia prospectiva de transferencia:

1. la corrida histórica etiqueta contra un pool fijo que incluye años futuros; esta usa `H(y)`;
2. la corrida histórica prueba años dejando el mismo país presente en entrenamiento; esta deja un
   país completo fuera;
3. la corrida histórica incluye 2020; esta aplica la exclusión firmada en todos los países;
4. la corrida histórica filtra por `Year` y renumera las fechas dentro de cada año; esta resuelve la
   semana epidemiológica desde la fecha real, evitando perder o desplazar semanas de frontera.

Por ello, los éxitos históricos regionales no sobreviven como evidencia fuera de país y de tiempo.
El resultado es compatible con aprendizaje de identidad o contexto del país en la corrida anterior,
no con una relación clima→brote transferible de forma general.

## Pruebas contra fuga

Se ejecutaron 17 pruebas con las dos fuentes reales. Cubren:

1. hashes y cobertura exacta de las fuentes;
2. resolución CDC/MMWR desde la fecha, incluida la SE01 que comienza en diciembre;
3. exclusión explícita de los dos países sin clima de superficie;
4. firma, dimensiones y 80 estados congelados antes de ajustar modelos;
5. exclusión de 2020, del año objetivo y de años futuros en las etiquetas;
6. ausencia completa del país externo en entrenamiento;
7. independencia del entrenamiento ante cambios en casos o clima del país externo;
8. independencia ante cambios en casos o clima del año externo;
9. exclusión de la semana objetivo de sus propios predictores;
10. uso efectivo de clima previo y descarte de faltantes sin imputación;
11. reporte de las cuatro referencias y conservación de métricas cuando recall es `N/A`;
12. configuración fija, diez semillas y argmax sin selección ni barrido.

Resultado limpio: `Ran 17 tests ... OK`.

Con `VIA_CERO_MUTACION_FUGA=1`, la prueba que cambia los casos del país externo falla al reintroducir
deliberadamente ese país en entrenamiento. Al retirar la variable, la misma prueba vuelve a `OK`.

## Reproducibilidad

Dos corridas completas hacia carpetas persistentes produjeron los cinco artefactos sustantivos
idénticos byte por byte:

| Artefacto | SHA-256 |
|---|---|
| `etiquetas.csv` | `37839441bc6a0afc1422c64b7ecc7ecc8680642e3409ff885e21c38c10a814f1` |
| `dataset.csv` | `559fdf0e7de20d8909ee6dad59d73ecf46faec3742cedf1cd630dc77aa20661c` |
| `predicciones.csv` | `950198aa1a1972b8d1d5e3de4f871b9bb0dd2847a6de90dc7a438bac2e2257a8` |
| `metricas.json` | `25a4dc0dd34626c6b7dbef23c7a24b4ac65e266ec595286966fbc9435017c8bc` |
| `firma_folds.json` | `666e383ff7148ccd4acba1209173e34730fb94cde1f45c8cb2a9ac3d2ee8eafd` |

`manifiesto_ejecucion.json` y `ejecucion.log` contienen hora y ruta de salida, por lo que esa metadata
no es byte-idéntica por diseño.

## Reproducción

Las fuentes crudas permanecen en la ruta gitignoreada
`backend/ingestion/data/raw/opendengue/`. El runner verifica sus hashes antes de leerlas.

```bash
docker compose run --no-deps --rm backend \
  python ingestion/validar_via_cero.py

docker compose run --no-deps --rm backend \
  python -m unittest ingestion.tests.test_validar_via_cero -v
```

Los artefactos quedan en `backend/ingestion/data/interim/via_cero/`, también gitignoreado. El script
no se conecta a PostgreSQL, no guarda modelos y no toca los artefactos de producción.

## Cierre técnico

La Vía 0 cumple su propósito diagnóstico y debe cerrarse. La evidencia no respalda que el éxito
regional histórico represente generalización a países no vistos. El único resultado estable es un
país–año aislado y no cambia el veredicto predeclarado.

Este cierre es una recomendación técnica. Su incorporación al registro oficial y cualquier decisión
de alcance del producto siguen a cargo del coordinador.
