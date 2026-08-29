# Corrida reproducible — Vía 3

**Fecha:** 2026-08-18

**Estado técnico:** completada

**Veredicto:** no adoptar

**Interpretación permitida:** validación forward-chaining exploratoria de predictores climáticos
con mecanismo biológico

**Interpretación no permitida:** desempeño final independiente, modelo mecanístico completo o
clasificador desplegable

## Resultado

Reemplazar los 21 rezagos climáticos crudos por siete transformaciones con fundamento biológico no
mejora el resultado decisivo. El único fold con semanas `alto` externas es 2022: el modelo obtiene
F1 macro 0,273, recall de `alto` 0,000 y **0 de 5 aciertos en las 10 semillas**. Es exactamente el
resultado de la climatológica y de la constante mayoritaria.

El resultado era estructuralmente difícil de rescatar: el entrenamiento disponible para 2022 tiene
150 semanas `bajo`, 2 `medio` y ninguna `alto`. `RandomForestClassifier` no puede emitir una clase
que nunca observó. Los folds 2023 y 2024 ya incluyen cinco ejemplos `alto` en entrenamiento, pero
sus externos contienen cero; allí el recall es `N/A` y solo pueden evaluarse F1 y falsos positivos.

La Vía 3 obtiene **0 de 10 semillas exitosas** en el único fold evaluable. No supera el criterio
aprobado y no toca el problema dominante de la etiqueta: las cinco semanas `alto` del corpus limpio
se concentran en 2022.

## Qué cambió

La fuente, la etiqueta, los años, los folds, las cuatro referencias, el modelo y el criterio son los
mismos de la Vía −1. El único cambio experimental es este reemplazo:

- configuración anterior: 7 variables × lag 1, lag 2 y media móvil de 4 semanas = 21 columnas;
- Vía 3: siete transformaciones fijas construidas solo con las 4 u 8 semanas anteriores.

No hubo selección de features, hiperparámetros o umbrales. Random Forest quedó fijado en 300
árboles, `class_weight="balanced"`, argmax, semillas 0–9 para estabilidad y 42 solo como referencia
histórica.

| Feature | Fórmula resumida | Observación previa al modelo |
|---|---|---|
| Racha térmica | Semanas consecutivas hasta lag 1, máximo 8, entre 17,8 y 34,6 °C | 8 en las 308 filas; no discrimina en El Salvador |
| Grados-día | Suma de 4 semanas de `7 × max(min(T, 35) − 16, 0)` | 211,16–345,77; 308 valores |
| Semanas temperatura–humedad óptimas | Conteo de 4 semanas con 27–29,5 °C y humedad >75 % | 0–2; solo 8 ocurrencias acumuladas |
| Interacción termohigrométrica | Exceso térmico dentro de 17,8–34,6 °C ponderado por humedad, media de 4 semanas | 3,39–7,14; 308 valores |
| Amplitud térmica | Media de 4 semanas de temperatura máxima menos mínima | 5,06–12,70 °C; 308 valores |
| Duración de lluvia | Suma de horas de precipitación de 4 semanas | 0,71–487,29 horas |
| Pulso seco→húmedo | Exceso positivo de lluvia en lag 1 contra la media de lags 2–4 | 0–245,60 mm |

La racha constante se conserva y se reporta porque fue parte del diseño predeclarado; no se
sustituyó después de observar su distribución. Su falta de variación es un hallazgo: el rango térmico
general de transmisión es demasiado amplio para separar semanas dentro del clima nacional.

No se construyó “número de días con lluvia sobre un mínimo”. El seed canónico conserva suma y
horas semanales, no observaciones diarias; inferir un conteo de días habría fabricado información.

Estas variables son **proxies inspirados en mecanismos**, no un modelo entomológico. El rango de
transmisión y su carácter no lineal se basan en el modelo térmico de
[Mordecai et al. (2017)](https://doi.org/10.1371/journal.pntd.0005568); los umbrales y la relevancia
de la amplitud térmica, en los experimentos de
[Carrington et al. (2013)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3592833/); la interacción de
temperatura y humedad, en [Campbell et al. (2013)](https://doi.org/10.4269/ajtmh.13-0321); y el
mecanismo de llenado de recipientes y eclosión, en
[Jeffery et al. (2012)](https://doi.org/10.1371/journal.pone.0039067). Esas fuentes respaldan las
transformaciones, no garantizan capacidad predictiva sobre la etiqueta de EPI-Aetheris.

## Resultados por año

Cada recall se presenta con aciertos absolutos. `N/A — 0 de 0` significa que el externo no contiene
ninguna semana `alto`; el año permanece en la evaluación. En esos folds también se indican los
falsos positivos de `alto` (`FP`). La persistencia excluye la primera semana del año porque no usa la
etiqueta del año anterior.

| Externo | Modelo Vía 3, 10 semillas | Climatológica | Mayoritaria | Siempre `alto` | Persistencia |
|---|---|---|---|---|---|
| 2019 | no entrenable; una sola clase en train | F1 0,327; recall N/A — 0 de 0; 0 FP | F1 0,327; recall N/A — 0 de 0; 0 FP | F1 0,000; recall N/A — 0 de 0; 50 FP | F1 0,319; recall N/A — 0 de 0; 0 FP |
| 2021 | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,000; recall N/A — 0 de 0; 52 FP | F1 0,333; recall N/A — 0 de 0; 0 FP |
| **2022** | **F1 0,273; recall 0,000 — 0 de 5; 0 FP** | F1 0,273; recall 0,000 — 0 de 5; 0 FP | F1 0,273; recall 0,000 — 0 de 5; 0 FP | F1 0,058; recall 1,000 — 5 de 5; 47 FP | F1 0,766; recall 0,600 — 3 de 5; 2 FP |
| 2023 | F1 0,327–0,330; recall N/A — 0 de 0; 0–1 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,000; recall N/A — 0 de 0; 52 FP | F1 0,333; recall N/A — 0 de 0; 0 FP |
| 2024 | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,333; recall N/A — 0 de 0; 0 FP | F1 0,000; recall N/A — 0 de 0; 52 FP | F1 0,333; recall N/A — 0 de 0; 0 FP |

El F1 macro se calcula sobre las tres clases congeladas aun cuando una clase no aparezca en el
externo. Por eso una predicción perfecta de las 52 semanas `bajo`, sin soporte de `medio` o `alto`,
produce F1 macro 0,333 y no 1,000.

## Comparación con los rezagos crudos

La Vía −1 y la Vía 3 son directamente comparables porque comparten filas, etiquetas y folds.

| Externo | 21 predictores crudos | 7 predictores Vía 3 | Cambio |
|---|---:|---:|---|
| 2021 | F1 0,333; recall N/A | F1 0,333; recall N/A | ninguno |
| 2022 | F1 0,273; recall 0,000 — 0 de 5 | F1 0,273; recall 0,000 — 0 de 5 | ninguno |
| 2023 | F1 0,333; 0 FP de `alto` | F1 0,327–0,330; 0–1 FP de `alto` | leve deterioro |
| 2024 | F1 0,333; recall N/A | F1 0,333; recall N/A | ninguno |

Las transformaciones no aportan señal que sobreviva a la separación temporal. En 2023 incluso
introducen un falso positivo de `alto` con algunas semillas, sin posibilidad de compensarlo con un
acierto porque el externo no contiene esa clase.

## Controles contra fuga

Antes del primer ajuste se congeló:

- manifiesto: `backend/ingestion/via_tres_manifesto_congelado.json`;
- firma del dataset y folds: `d8c2b907833f799a233d99f18289416803f22370e916dbd212da3943620303ae`;
- 308 filas, siete columnas y los cinco estados de fold;
- lista única de features, modelo, semillas, referencias y criterio.

Se ejecutaron 16 pruebas sobre el seed real. Cubren hashes, fórmulas, orden temporal, exclusión de la
semana objetivo, dependencia efectiva del clima previo, independencia frente a casos del externo y
datos posteriores, faltantes sin imputación, firma de folds y configuración fija. Resultado limpio:
`Ran 16 tests ... OK`.

Con `VIA_TRES_MUTACION_FUGA=1`, la prueba de independencia falla al introducir deliberadamente la
semana objetivo en sus propios predictores. Sin esa variable, vuelve a `OK`.

## Reproducibilidad

Dos corridas completas hacia carpetas persistentes produjeron los cinco artefactos sustantivos
idénticos byte por byte:

| Artefacto | SHA-256 |
|---|---|
| `etiquetas.csv` | `0f2ff2f90afd09389f1e08a0cd96dce42288761232a7c116529a1b976dc17d36` |
| `dataset.csv` | `064f3d181b91b2e1d816f4b55f84670d7684e1604fb57c9a23758594eb3d7cda` |
| `predicciones.csv` | `e1ff5ec9bcc7b03a14d3e04b65f739d412a19d6e7262210090e7f5a3928d2d6a` |
| `metricas.json` | `8698e4ad0a4f9f163ff9fa52361835adea79ff5212f748f5287ab0020615e75f` |
| `firma_previa.json` | `5c26012e4ad3d0fa6b99816c12e30c68f0dc15f80e1f3de4bf1deaee7ff38472` |

`manifiesto_ejecucion.json` y `ejecucion.log` contienen hora y ruta de salida, por lo que esa metadata
no es byte-idéntica por diseño. El entorno fue Python 3.11.15, NumPy 2.4.6 y scikit-learn 1.5.1.

## Reproducción

```bash
docker compose run --no-deps --rm \
  -v ./db:/workspace/db:ro backend \
  python ingestion/validar_via_tres.py \
  --seed-sql /workspace/db/seed/seed_datos_reales.sql

docker compose run --no-deps --rm \
  -v ./db:/workspace/db:ro \
  -e VIA_TRES_SEED_SQL=/workspace/db/seed/seed_datos_reales.sql \
  backend python -m unittest ingestion.tests.test_validar_via_tres -v
```

Los artefactos quedan en `backend/ingestion/data/interim/via_tres/`, ruta gitignoreada. El runner
lee el volcado canónico, no se conecta a PostgreSQL, no escribe modelos y no toca producción.

## Cierre técnico

La Vía 3 debe cerrarse. Las features incorporan no linealidad, acumulación, duración y transiciones,
pero no cambian la distribución interanual de la variable objetivo ni crean ejemplos `alto` donde el
fold limpio carece de ellos. No hay evidencia para adoptar estas transformaciones en producción ni
para seguir ajustándolas sobre los mismos años.

La adopción oficial sigue siendo decisión del coordinador. Las Vías 1 y 2 permanecen pendientes de
su aprobación explícita porque cambian, respectivamente, el conjunto de predictores y la pregunta de
la etiqueta.
