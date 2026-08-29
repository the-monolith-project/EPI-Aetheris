# Corrida reproducible — Vía 2

**Fecha:** 2026-08-18

**Estado técnico:** completada

**Veredicto:** no adoptar

**Interpretación permitida:** clasificación retrospectiva de la posición relativa de una semana
dentro de su temporada completa

**Interpretación no permitida:** riesgo contra el histórico, brote absoluto, validación prospectiva o
modelo listo para producción

## Resultado

La etiqueta intraanual permite al modelo superar de forma estable el criterio en 2021, 2022 y 2023,
pero no en 2019 ni 2024. El resultado global es **3 de 5 folds con éxito estable**:

- 2019: 0 de 10 semillas; mejora recall, pero no supera el F1 de la climatológica;
- 2021, 2022 y 2023: 10 de 10 semillas;
- 2024: 8 de 10 semillas.

La condición congelada exige éxito en las 10 semillas de todos los folds externos. La vía no la
cumple. Además, persistencia sigue siendo claramente superior en 2019, 2022, 2023 y 2024.

El resultado es mejor que el de la etiqueta histórica, pero responde otra pregunta y no puede
interpretarse como rescate del clasificador de riesgo vigente.

## Qué cambió respecto de producción

La Vía 2 sustituye experimentalmente la etiqueta de canal endémico P75/P90 por una etiqueta relativa
al año completo:

```text
bajo  si casos <= P50 del mismo año
medio si casos > P50 y casos <= P75
alto  si casos > P75
```

Cada año completo produce 26 semanas `bajo`, 13 `medio` y 13 `alto`. Los predictores permanecen
idénticos a los de la Vía −1: 21 columnas climáticas construidas solo con las semanas anteriores. Los
folds son forward-chaining y no hubo selección de features, hiperparámetros o umbrales.

| Año etiquetado | P50 | P75 | Distribución bajo / medio / alto |
|---|---:|---:|---:|
| 2018 | 146,50 | 240,75 | 26 / 13 / 13 |
| 2019 | 272,50 | 929,25 | 26 / 13 / 13 |
| 2021 | 120,00 | 138,50 | 26 / 13 / 13 |
| 2022 | 303,00 | 498,25 | 26 / 13 / 13 |
| 2023 | 109,00 | 137,25 | 26 / 13 / 13 |
| 2024 | 149,00 | 208,50 | 26 / 13 / 13 |

La etiqueta usa semanas futuras del mismo año para conocer sus percentiles. Por ello, los casos del
año externo no entran en etiquetas de entrenamiento, pero sí en su propia etiqueta externa. Es una
validación reconstructiva y no prospectiva.

El experimento toca la decisión cerrada sobre la etiqueta P75/P90 contra historia y cambia la
pregunta del producto. La autorización de Eduardo habilitó la corrida, no una modificación de
producción. También permanece el costo comunicacional advertido antes de ejecutar: una semana
`alto` de una temporada de baja transmisión puede tener menos casos que una semana `bajo` de una
temporada severa.

## Resultados por año

El modelo se reporta como rango de las semillas 0–9. Cada recall incluye sus aciertos absolutos y
`FP` indica falsos positivos de `alto`. Persistencia evalúa 51 de las 52 filas porque excluye la
primera semana.

| Externo | Modelo Vía 2, 10 semillas | Climatológica | Mayoritaria | Siempre `alto` | Persistencia |
|---|---|---|---|---|---|
| 2019 | F1 0,774–0,805; recall 0,846 — 11 de 13; 5–6 FP; **éxito 0/10** | F1 0,808; recall 0,769 — 10 de 13; 3 FP | F1 0,222; recall 0,000 — 0 de 13; 0 FP | F1 0,133; recall 1,000 — 13 de 13; 39 FP | F1 0,819; recall 0,846 — 11 de 13; 2 FP |
| 2021 | F1 0,485–0,498; recall 0,308 — 4 de 13; 7–9 FP; **éxito 10/10** | F1 0,421; recall 0,231 — 3 de 13; 7 FP | F1 0,222; recall 0,000 — 0 de 13; 0 FP | F1 0,133; recall 1,000 — 13 de 13; 39 FP | F1 0,419; recall 0,308 — 4 de 13; 8 FP |
| 2022 | F1 0,394–0,416; recall 0,385–0,462 — 5–6 de 13; 10–13 FP; **éxito 10/10** | F1 0,290; recall 0,154 — 2 de 13; 10 FP | F1 0,222; recall 0,000 — 0 de 13; 0 FP | F1 0,133; recall 1,000 — 13 de 13; 39 FP | F1 0,858; recall 0,846 — 11 de 13; 2 FP |
| 2023 | F1 0,386–0,412; recall 0,231 — 3 de 13; 4–8 FP; **éxito 10/10** | F1 0,343; recall 0,077 — 1 de 13; 7 FP | F1 0,222; recall 0,000 — 0 de 13; 0 FP | F1 0,133; recall 1,000 — 13 de 13; 39 FP | F1 0,508; recall 0,615 — 8 de 13; 5 FP |
| 2024 | F1 0,666–0,751; recall 0,538–0,769 — 7–10 de 13; 2–4 FP; **éxito 8/10** | F1 0,595; recall 0,538 — 7 de 13; 3 FP | F1 0,222; recall 0,000 — 0 de 13; 0 FP | F1 0,133; recall 1,000 — 13 de 13; 39 FP | F1 0,910; recall 0,923 — 12 de 13; 1 FP |

Los éxitos parciales no se agregan para reemplazar la regla por año. En particular, 8 de 10 en 2024
es inestable según la definición previa y 2019 falla aunque el rango quede cerca de la
climatológica.

## Relación con el preliminar histórico

El preliminar recibido anteriormente no es directamente comparable porque usaba leave-one-year-out
e incluía años futuros en entrenamiento. Esta corrida separa años completos en orden temporal y
nunca deja que los casos del externo modifiquen etiquetas del train. Las diferencias con aquel
preliminar no autorizan escoger la versión que produzca mejores cifras.

## Controles contra fuga

Antes del primer ajuste se congelaron:

- manifiesto: `backend/ingestion/via_dos_manifesto_congelado.json`;
- firma de preparación: `658b193b94ad5038e9131b13a2cc4d3730e573cd503c1418fc83031c1da82614`;
- 312 filas, 21 predictores, seis distribuciones de etiqueta y cinco folds entrenables;
- modelo de 300 árboles, `class_weight="balanced"`, argmax y semillas 0–9; la semilla 42 solo se
  conserva como referencia histórica.

Se ejecutaron 11 pruebas sobre el seed real. Cubren autorización y hashes, firma congelada,
percentiles y distribuciones, uso explícito del año completo, forward-chaining, semana objetivo
fuera de features, independencia de las etiquetas de entrenamiento frente al externo, independencia
ante años posteriores y configuración fija.

Con `VIA_DOS_MUTACION_FUGA=1`, la prueba correspondiente falla al incorporar deliberadamente casos
del año externo en los percentiles de años de entrenamiento. Sin la mutación, vuelve a `OK`.

## Reproducibilidad

Dos corridas completas produjeron los cinco artefactos sustantivos idénticos byte por byte:

| Artefacto | SHA-256 |
|---|---|
| `etiquetas.csv` | `823411a3c5e5aed3fe5c98dd749102166a762b42ac76cd4399e8124899138e8c` |
| `dataset.csv` | `796e54a49316f7ba6584fb90c30bf62ea0944ce6f1ae38db2530cd09d91b05d8` |
| `predicciones.csv` | `048e8b2451bdd6f20150bb228b7dfd8f5e6e931f2627ba8495ada188c90e8c6c` |
| `metricas.json` | `70d4a3c9e6ac3917e80026aebed2960a024005dd593fe3346eff5d2bd323252b` |
| `firma_previa.json` | `379b0d7380fa2de76f34a6b46372fbe323dda292e4523645a8e9734b7912e56a` |

El entorno fue Python 3.11.15, NumPy 2.4.6 y scikit-learn 1.5.1 dentro de la imagen del backend.
`manifiesto_ejecucion.json` y `ejecucion.log` incluyen hora y ruta, por lo que esa metadata no es
byte-idéntica por diseño.

## Reproducción

```bash
docker compose run --no-deps --rm \
  -v ./db:/workspace/db:ro backend \
  python ingestion/validar_via_dos.py \
  --seed-sql /workspace/db/seed/seed_datos_reales.sql

docker compose run --no-deps --rm \
  -v ./db:/workspace/db:ro \
  -e VIA_DOS_SEED_SQL=/workspace/db/seed/seed_datos_reales.sql \
  backend python -m unittest ingestion.tests.test_validar_via_dos -v
```

Los artefactos quedan en `backend/ingestion/data/interim/via_dos/`, ruta ignorada por Git. El runner
no se conecta a PostgreSQL, no guarda modelos y no toca producción.

## Cierre técnico

La Vía 2 muestra señal climática para una pregunta relativa de temporada, pero no satisface el
criterio estable completo y su objetivo requiere conocer el año entero. No debe sustituir el
indicador de riesgo histórico ni presentarse como alerta prospectiva.

La recomendación técnica es no adoptarla. Si el equipo quisiera conservarla como indicador
retrospectivo separado, requeriría una nueva decisión explícita de producto y comunicación; las
métricas actuales no bastan para integrarla automáticamente.
