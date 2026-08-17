# Experimento: la vía multipaís como rescate del clasificador nacional (2026-08-16)

> Registro del experimento y su resultado, para no reintentarlo sin una hipótesis distinta. Es un
> experimento -- no cambia producción. No se escribió nada a Postgres, no se tocaron
> `dataset_modelado.csv`, `clasificador_riesgo_nacional_v1.joblib` ni `metricas_modelo.json`, y no
> se modificó `construir_dataset_modelado.py`, `entrenar_clasificador.py` ni
> `corrida_canal_endemico_nacional.py`. Script: `backend/ingestion/experimento_multipais.py`.

## Motivación

El clasificador nacional de producción (250 filas: serie semanal de El Salvador 2018/2019/2021-2023,
21 predictores climáticos rezagados, etiqueta de canal endémico P75/P90) no supera su criterio de
éxito en ningún año de prueba evaluable -- recall de la clase "alto" en **0.000** tanto en 2019 como
en 2022, los dos únicos años de la ventana con semanas "alto" reales. Ya se descartaron
empíricamente: ajuste de umbral de decisión, cambio de algoritmo (RandomForest, GradientBoosting,
ExtraTrees, regresión logística), ventana climática ampliada (`experimento-ventana-climatica-
ampliada.md`) y ONI como predictor nacional (`experimento-oni-predictor.md`).

El diagnóstico ya establecido: la etiqueta correlaciona 0.955 con el total anual de casos -- mide
"qué tan grande fue el año", no "qué pasa esta semana". El tamaño muestral efectivo para la señal
dominante no son 250 filas, son 5 años, de los cuales solo 2 contienen algún "alto". Hipótesis a
verificar aquí: entrenar con varios países de las Américas eleva el número de ejemplos de
año-con-brote de 2 a ~97, lo que podría hacer aprendible la relación clima → brote.

**Esto toca el estatuto cerrado de alcance geográfico** (nacional El Salvador para el MVP; lo
multinacional era argumento de escalabilidad, explícitamente no un entregable -- ver `CLAUDE.md`).
Este documento cierra en números; adoptar cualquier vía multipaís en producción es decisión del
coordinador.

## Verificación de cobertura

La propia réplica reproduce exactamente las cifras que motivaron el experimento (fuente:
`Temporal_extract_PAHO_V1_3.csv`, filtro `S_res=Admin0`/`T_res=Week`, años 2014-2024, misma etiqueta
de canal endémico de producción P75/P90, ventana ±1, piso 12 obs/3 años):

| Cifra | Evidencia previa | Réplica de este script | Coincide |
|---|---|---|---|
| Países con serie semanal completa (11 años, ≥45 sem/año) | 18 | 18 | Sí |
| Filas país-semana etiquetadas (sin exigir clima) | 10.278 | 10.278 | Sí |
| Semanas "alto" | 1.390 (13,5 %) | 1.390 (13,5 %) | Sí |
| Años-país con ≥1 semana "alto" | 97 de 198 | 97 de 198 | Sí |
| Correlación media entre países (anomalía anual) | 0,453 | 0,453 | Sí |
| Primer componente común (varianza interanual) | 51,8 % | 51,8 % | Sí |
| Correlación señal regional ↔ ONI anual | 0,527 | 0,517 | Cercano (ver nota) |
| Correlación El Salvador ↔ señal regional | +0,280 (último de 18) | +0,280 (último de 18) | Sí |

Nota sobre ONI: la diferencia de tercer decimal (0,517 frente a 0,527) es una variación de método de
promediado del índice mensual a escala anual, no una discrepancia de datos -- ambas cifras dicen lo
mismo (correlación moderada-alta, ~0,52) y no cambian ninguna conclusión.

**Con clima ya no son 18 países, son 16.** Al pedir clima a Open-Meteo para el centroide de cada
país, **Bermuda y Virgin Islands (US) devuelven `null` en las 5 variables de `era5_land` para el
100 % de los días solicitados** (`precipitation_sum`/`precipitation_hours` de `era5` sí cargan
normalmente para ambos) -- consistente con un hueco de la máscara tierra/mar del reanálisis en islas
muy pequeñas, no con un error del script (la guarda de precipitación y el resto de países cargan sin
problema). El script imprime un aviso explícito (`AVISO: ... con 0% de cobertura climática...`)
cuando esto ocurre, en vez de dejarlo silencioso. Efecto: los dos países quedan fuera del dataset de
modelado por completo. Esto explica exactamente la caída de "97 años-país con alto" a **87** en el
dataset final (Bermuda aportaba 5/11 y Virgin Islands (US) 5/11 en la tabla de cobertura original;
97 − 5 − 5 = 87).

Dataset final de modelado (16 países, clima completo, LAGS=(1,2), media móvil de 4 semanas, 7
variables climáticas): **9.072 filas, 1.330 "alto" (14,7 %), 87 años-país con ≥1 semana "alto"**.
1.206 semanas candidatas se descartaron por falta de historia climática completa (mayormente las de
Bermuda/Virgin Islands, más un margen esperado de las primeras semanas de 2014 por no tener año
anterior con datos).

## Simplificación declarada: un centroide por país

Cada país usa **un único punto representativo**, no un promedio de varios puntos (a diferencia de
los 14 departamentos de El Salvador en producción). Para Brasil, México y Estados Unidos esto es una
simplificación fuerte -- un solo punto no representa el clima de un territorio de ese tamaño. Para
Estados Unidos se usó un punto en Florida (27.99, -81.76), no el centroide geométrico del país,
porque es donde ocurre la transmisión real de dengue; para el resto de países, el centroide es una
aproximación razonable dado su tamaño. Esta simplificación es aceptable para un experimento de
verificación, pero **no debe leerse como validada para producción** -- si alguna vía multipaís se
adoptara, sustituir por varios puntos por país (mismo criterio que ya se usa por departamento) sería
un prerequisito, no un detalle.

## Corrida A -- `--modo el-salvador` (la pregunta que importa para el entregable actual)

Entrena con los otros 15 países con clima disponible, prueba en El Salvador año por año. El Salvador
correlaciona apenas **+0,280 (R² ≈ 0,08)** con la señal regional compartida -- un modelo regional
perfecto explicaría alrededor del 8 % de su variación interanual. Se esperaba que esta corrida
fallara.

| Año | Soporte "alto" real | F1 modelo | Recall alto modelo | F1 base clim. | Recall alto base | Veredicto (11 semillas) |
|---|---|---|---|---|---|---|
| 2014 | 38 | 0,027 | 0,000 | 0,027 | 0,000 | no supera (0/11) |
| 2015 | 29 | 0,108 | 0,000 | 0,108 | 0,000 | no supera (0/11) |
| 2016 | 5  | 0,294 | 0,000 | 0,294 | 0,000 | no supera (0/11) |
| 2019 | 1  | 0,222 | 0,000 | 0,222 | 0,000 | no supera (0/11) |
| 2022 | 11 | 0,268 | 0,000 | 0,268 | 0,000 | no supera (0/11) |

**Falla en las 5 corridas, en las 11 semillas cada una (55/55) -- sin una sola excepción.** El
detalle más informativo no es solo el 0.000 de recall: el modelo entrenado con los otros 15 países
predice **exactamente la misma distribución que la línea base climatológica en los 5 años** (F1
idéntico a 3 decimales, matriz de confusión idéntica) -- ambos colapsan a predecir siempre "bajo".
El Random Forest, con `class_weight="balanced"`, no encuentra en el clima de los otros países ninguna
frontera de decisión transferible a El Salvador; ante eso, se comporta como el propio dato de
entrenamiento visto desde fuera (mayoría "bajo"), igual que la base climatológica. Esto **no es un
experimento perdido**: es la explicación, con número y nombre, de por qué el modelo local nunca
funcionó -- El Salvador está estadísticamente desacoplado de la dinámica que comparten sus vecinos.

## Corrida B -- `--modo regional`

Leave-one-year-out sobre los 16 países con clima completo, sin distinguir cuál país se prueba.

| Año | Soporte "alto" real | F1 modelo | Recall alto modelo | F1 base clim. | Recall alto base | Veredicto (11 semillas) |
|---|---|---|---|---|---|---|
| 2014 | 121 | 0,280 | 0,000 | 0,280 | 0,000 | no supera (0/11) |
| 2015 | 104 | 0,278 | 0,000 | 0,276 | 0,000 | no supera (0/11) |
| 2016 | 109 | 0,279 | 0,009 | 0,273 | 0,000 | **SUPERA (11/11)** |
| 2017 | 4   | 0,399 | 0,250 | 0,326 | 0,000 | **SUPERA (11/11)** † |
| 2018 | 2   | 0,327 | 0,000 | 0,328 | 0,000 | no supera (0/11) † |
| 2019 | 140 | 0,251 | 0,007 | 0,246 | 0,000 | **SUPERA (9/11)** |
| 2020 | 52  | 0,296 | 0,000 | 0,297 | 0,000 | no supera (0/11) |
| 2021 | 2   | 0,324 | 0,000 | 0,325 | 0,000 | no supera (0/11) † |
| 2022 | 28  | 0,331 | 0,071 | 0,302 | 0,000 | **SUPERA (11/11)** |
| 2023 | 240 | 0,267 | 0,054 | 0,226 | 0,000 | **SUPERA (11/11)** |
| 2024 | 528 | 0,139 | 0,017 | 0,133 | 0,000 | **SUPERA (11/11)** |

† Soporte "alto" real muy pequeño (2-4 casos) -- lectura frágil, un acierto o error de más cambia el
recall en 25-50 puntos porcentuales de golpe. Los años con soporte sustancial (2016, 2019, 2022,
2023, 2024) son la evidencia sólida.

**Supera el criterio en 6 de 11 años, de forma robusta entre semillas (11/11 o 9/11 de 11).** A
diferencia de la corrida A, el modelo no colapsa a la base climatológica -- mejora el recall de
"alto" de forma consistente en los años con soporte real, aunque el efecto sigue siendo modesto
(recall entre 0,009 y 0,25, nunca alto en términos absolutos). Esto es exactamente el resultado que
la correlación media entre países (0,453) y el primer componente común (51,8 % de la varianza)
predecían: existe una señal regional real y parcialmente aprendible, distinta del ruido de un solo
país. **El entregable que saldría de esto es un clasificador regional de las Américas, no de El
Salvador** -- cambio de alcance mayor, decisión del coordinador.

## Corrida C -- `--modo regional --incluir-oni`

Igual que la corrida B, con `oni_anom` (NOAA ONI) agregado como predictor adicional (mismos rezagos y
media móvil que las 7 variables climáticas). El ONI ya se descartó como predictor **nacional** contra
El Salvador solo (`experimento-oni-predictor.md`, resultado negativo); aquí se prueba contra la señal
regional compartida, con la que correlaciona +0,52 -- justo el componente que le faltaba a la corrida
B.

| Año | Soporte "alto" real | F1 modelo | Recall alto modelo | F1 base clim. | Recall alto base | Veredicto (11 semillas) |
|---|---|---|---|---|---|---|
| 2014 | 121 | 0,278 | 0,000 | 0,280 | 0,000 | no supera (0/11) |
| 2015 | 104 | 0,299 | 0,192 | 0,276 | 0,000 | **SUPERA (11/11)** |
| 2016 | 109 | 0,313 | 0,110 | 0,273 | 0,000 | **SUPERA (11/11)** |
| 2017 | 4   | 0,353 | 0,250 | 0,326 | 0,000 | **SUPERA (11/11)** † |
| 2018 | 2   | 0,372 | 1,000 | 0,328 | 0,000 | **SUPERA (11/11)** † |
| 2019 | 140 | 0,259 | 0,014 | 0,246 | 0,000 | **SUPERA (11/11)** |
| 2020 | 52  | 0,348 | 0,038 | 0,297 | 0,000 | **SUPERA (11/11)** |
| 2021 | 2   | 0,324 | 0,000 | 0,325 | 0,000 | no supera (0/11) † |
| 2022 | 28  | 0,302 | 0,000 | 0,302 | 0,000 | no supera (0/11) |
| 2023 | 240 | 0,312 | 0,183 | 0,226 | 0,000 | **SUPERA (11/11)** |
| 2024 | 528 | 0,192 | 0,085 | 0,133 | 0,000 | **SUPERA (11/11)** |

† Mismo aviso de soporte pequeño que en la corrida B -- el recall=1,000 de 2018 es 2/2 aciertos, no
una señal fuerte por sí sola, aunque se sostuvo en las 11 semillas.

**Supera en 8 de 11 años, con robustez perfecta entre semillas en los 8 (11/11 cada uno).** Mejora
sobre la corrida B tanto en cobertura (8 vs 6 años) como en magnitud de recall en los años con
soporte real (ej. 2015: 0,000→0,192; 2023: 0,054→0,183). **El contraste con `experimento-oni-
predictor.md` es la pieza más interesante de este resultado**: el mismo predictor (ONI) que no
aportó nada contra una sola serie de 5 años de El Salvador sí aporta contra 16 países, porque el
mecanismo que el ONI captura (El Niño/La Niña como forzante climático de escala continental) solo se
vuelve visible cuando el ruido de un solo país deja de dominar la varianza. No contradice el
experimento anterior -- lo explica.

## Interpretación de conjunto

El patrón de las tres corridas es internamente consistente, no contradictorio:

- **El clima predice el riesgo de dengue a escala regional** (corridas B y C, robustas entre
  semillas) -- la hipótesis de origen (18→97 años-con-brote hace la relación aprendible) es correcta
  a esa escala.
- **El Salvador está desacoplado de esa dinámica regional** (r=+0,280, el más bajo de 18 países) --
  por eso la corrida A, que es la que importa para el entregable actual, falla limpio y sin
  excepción en 55/55 corridas semilla×año.
- Esto **explica el fracaso del modelo nacional actual con un mecanismo concreto**, no solo con "no
  hay suficientes datos": no es (únicamente) un problema de tamaño de muestra -- es que, incluso con
  la muestra ampliada, El Salvador no comparte la señal que sí comparten sus vecinos con transmisión
  más intensa (Colombia r=+0,952, Guatemala +0,908, Honduras +0,868).
- Sumado a los cinco experimentos ya descartados contra la serie nacional sola (umbral de decisión,
  cambio de algoritmo, ventana ampliada, ONI nacional, pool no pareado), este es un sexto intento que
  tampoco rescata el clasificador **de El Salvador**. La vía multipaís sí produce un hallazgo
  positivo, pero a una escala distinta de la que pidió el MVP.

## Qué NO se prueba con esto

- No se prueba que un clasificador regional de las Américas sea desplegable como está: recall de
  "alto" en el rango 0,009-0,25 en los años con soporte real es una mejora sobre 0,000, no un
  clasificador operacional. Falta, como mínimo, calibración y una discusión de qué umbral de
  decisión sería útil en la práctica.
- No se prueba que agregar más países (fuera de los 18 de la extracción PAHO) mejoraría más --
  no se exploró esa dimensión.
- No se prueba una vía de transferencia parcial (ej. entrenar regional y ajustar/recalibrar solo con
  El Salvador) -- fuera de alcance de esta tarea.
- No se resuelve el centroide-por-país como método de producción -- ver la sección de simplificación
  declarada arriba.

## Veredictos explícitos

| Corrida | Resultado | Veredicto |
|---|---|---|
| A -- el-salvador | Falla limpio, 0/55 (semilla×año) | **No adoptar.** Cierra esta vía específica para El Salvador; se suma a los cinco experimentos ya descartados. |
| B -- regional | Supera en 6/11 años, robusto entre semillas | **`[decisión previa requerida]`** -- hallazgo real, pero cambia el alcance del entregable (regional, no El Salvador). No se adopta sin decisión explícita del coordinador. |
| C -- regional + ONI | Supera en 8/11 años, robusto entre semillas, mejor que B | **`[decisión previa requerida]`** -- mismo veredicto que B, con evidencia más fuerte. Reabre la pregunta de ONI, pero solo a escala regional -- el resultado negativo de `experimento-oni-predictor.md` a escala nacional sigue vigente y no se revierte por esto. |

En los tres casos: informe cerrado con números, sin tocar `docs/contexto/`, sin adoptar nada en
producción. La decisión de si el entregable del proyecto cambia de escala geográfica -- lo que
tocaría el estatuto cerrado de alcance -- es del coordinador, no de este experimento.

## Reproducibilidad

```bash
# Datos (no versionados, descomprimir a backend/ingestion/data/raw/opendengue/):
# https://github.com/OpenDengue/master-repo -> assets/Temporal_extract_PAHO_V1_3.zip

cd backend/ingestion
python3 experimento_multipais.py --csv data/raw/opendengue/Temporal_extract_PAHO_V1_3.csv \
    --modo el-salvador --semillas 0,1,2,3,4,5,6,7,8,9,42        # corrida A
python3 experimento_multipais.py --csv data/raw/opendengue/Temporal_extract_PAHO_V1_3.csv \
    --modo regional --saltar-descarga --semillas 0,1,2,3,4,5,6,7,8,9,42            # corrida B
python3 experimento_multipais.py --csv data/raw/opendengue/Temporal_extract_PAHO_V1_3.csv \
    --modo regional --incluir-oni --saltar-descarga --semillas 0,1,2,3,4,5,6,7,8,9,42  # corrida C

# Pruebas unitarias (guarda de precipitación, reintento 429, retroceso de semanas):
python3 -m pytest backend/ingestion/tests/test_experimento_multipais.py -v
```

La primera corrida descarga clima de Open-Meteo (2 peticiones multi-ubicación) y lo cachea en
`data/interim/experimento_multipais/clima_multipais.json`; las siguientes pueden usar
`--saltar-descarga` para reutilizarlo sin volver a golpear la API. Resultados por corrida en
`data/interim/experimento_multipais/resultados_<modo>.json` (gitignoreado).
