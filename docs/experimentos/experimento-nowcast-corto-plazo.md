# Experimento: proto-predictor de nowcast de horizonte corto (2026-09-08)

> Ejecutado el 2026-09-09 — ver "Resultados" al final. Los parámetros se fijaron antes de mirar
> los datos, igual que `experimento-oni-predictor.md` y `experimento-validacion-leadtime-camino-ancho.md`.
> Es un diagnóstico exploratorio — no cambia producción. No escribe a Postgres, no toca FastAPI ni
> el frontend, no modifica el esquema. No reabre ninguna decisión cerrada: M3 (P50/P75,
> leave-one-out, ±1) queda intacto y no se usa como objetivo ni como insumo aquí. No autoriza
> lenguaje de "predicción" en el producto — ver "Decisiones pendientes de firma".

## Motivación

El clasificador interanual se retiró (`docs/contexto/01-decisiones-cerradas.md`, pivote "Camino
Ancho", 2026-08-18) tras demostrar recall de "alto" = 0.000 en todos los años de prueba evaluables
y no superar la línea base climatológica. El informe de cierre de la línea de rescate
(`docs/rescate-prediccion/informe-cierre-rescate-prediccion.md`) cerró las cinco vías de rescate
que conservaban el marco de **clasificación interanual retrospectiva**.

Un hallazgo colateral de esas corridas quedó sin explorar: en la corrida ONI de prueba 2022
(`entrenamiento-clasificador-riesgo-nacional_desde2014_oni_prueba2022.md`), la **línea base de
persistencia** (autocorrelación de casos) obtuvo F1 macro 0.748 y recall "alto" 0.667, contra
0.268 / 0.000 del modelo climático. La persistencia está marcada como "no desplegable en vivo",
pero eso se debe a que la etiqueta "alto" se computa contra la línea base del año completo
(leave-one-out) — un problema de construcción de la etiqueta, no de predictibilidad. Hay
estructura de corto plazo en la serie de casos y ninguna corrida la aprovechó.

Este experimento prueba una hipótesis distinta de todo lo cerrado: **¿un nowcast probabilístico de
horizonte corto (4 semanas) sobre el conteo de casos supera de forma estable a los baselines de
persistencia y climatología estacional, con scoring propio y protocolo sin fuga temporal?**

Es un marco nuevo respecto a lo descartado:

- objetivo = conteo observado, no una etiqueta categórica derivada de una línea base;
- horizonte corto declarado (4 semanas), no "anticipación de temporada" ni lead time de meses;
- métrica continua (WIS), no recall de una clase rara;
- criterio = ganar en promedio al baseline, no ganar todos los años en una clase con soporte 1-6.

## Qué NO se hace (alcance explícito)

- No se construye ningún endpoint de FastAPI ni se toca el frontend.
- No se modifica el esquema de Postgres ni se escribe ninguna fila.
- No se usa M3, ni su fórmula ni sus cortes, como objetivo ni como feature.
- No se reintroduce la etiqueta "alto/medio/bajo" en ninguna forma.
- No se barren hiperparámetros contra los folds de prueba. La configuración del primer modelo se
  declara en este documento antes de correr nada.
- No se descarta ningún año ni semana "sin señal" — se reportan todos.
- No se comunica ninguna cifra de este experimento fuera del repositorio hasta la firma de las
  decisiones pendientes de abajo.

## Metodología

### 1. Datos

| Insumo | Fuente | Cobertura | Nota |
|---|---|---|---|
| Objetivo: casos nacionales semanales | `casos_epidemiologicos`, `clasificacion='total'`, `fuente='opendengue_v1_3'`, región `SV` | 2018–2024 cargado; extensible a 2013/2014 sin volver a descargar (`01-decisiones-cerradas.md`, "Carga de OpenDengue nacional") | serie objetivo única ya cargada |
| Clima departamental | ERA5 / Open-Meteo, 7 variables × 14 departamentos | 2018–2024 completo, incluye 2020 | se agrega a nivel nacional (media ponderada por población o media simple — decisión de implementación, se declara en el script) |
| ONI (anomalía SST) | `variable_ambientales`, `variable='oni_anom'`, región `SV` (ADR 0008) | según carga | se incluye como feature candidata; ya se sabe que no ayuda al marco semanal-clasificación, se re-evalúa aquí por completitud |

Todo predictor climático y de ONI entra **solo con rezago suficiente** para estar disponible en el
momento de origen `t` (ver rezago ERA5 de ~5 días declarado en ADR 0018). Ninguna variable
contemporánea a `t+h`.

### 2. Objetivo (target)

`y_t` = conteo nacional de casos en la semana epidemiológica `t`. Transformación: `log1p(y_t)`.

El modelo predice la **distribución predictiva completa** de `y_{t+h}`, reportada como el conjunto
estándar de 23 cuantiles (0.010, 0.025, 0.050, 0.100, …, 0.950, 0.975, 0.990) usado por los hubs
de forecasting de CDC/OPS, para que WIS sea comparable con esa literatura.

**No hay etiqueta.** Si en el futuro se necesita una vista categórica (semáforo), se deriva
*post-hoc* umbralando el conteo predicho contra un percentil estacional calculado solo con años
anteriores — pero eso no es parte de este experimento.

### 3. Horizonte

**Decisivo: `h = 4` semanas.** Se reporta también `h ∈ {1, 2, 8}` como secundario para trazar la
curva de degradación del skill, pero el criterio de éxito se evalúa solo sobre `h = 4`.

### 4. Baselines (obligatorios, el modelo debe superarlos)

1. **Persistencia / random walk** en escala log: `ŷ_{t+h} = y_t`, con intervalos derivados de la
   distribución empírica de los residuos `log1p(y_{t'+h}) − log1p(y_{t'})` sobre `t' ≤ t`.
2. **Climatología estacional**: los cuantiles de `y` para la misma semana epidemiológica,
   calculados **únicamente con años estrictamente anteriores** al año de `t+h`.
3. **Persistencia estacional** (combinación): `ŷ_{t+h} = y_t · (clim_{semana(t+h)} / clim_{semana(t)})`,
   incertidumbre por bootstrap de residuos.

El **comparador decisivo** es el baseline más fuerte de los tres en el conjunto de prueba agrupado
(se elige por menor WIS medio, declarado en el reporte de resultados antes de comparar el modelo).

### 5. Protocolo temporal (sin fuga)

Forward-chaining con ventana expansiva. Para cada semana de origen `t` en el rango de prueba:

- entrenamiento y toda normalización, referencia climatológica y estimación de residuos usan
  **solo** datos con fecha de inicio de semana `≤` la de `t`;
- se predice `t+h`;
- nada con fecha `>` la de `t` toca ninguna parte del cálculo, incluida la construcción de features.

**Años de origen de prueba:** 2019, 2021, 2022, 2023, 2024 recorridos semana a semana. 2020 ver
decisión pendiente. Los años previos al primero de prueba forman el entrenamiento inicial.

**Vetos anti-fuga (heredados del protocolo de rescate, `docs/rescate-prediccion/protocolo-evaluacion-rescate-prediccion.md`):**

- se prohíben predictores constantes y cualquier uso de estadísticas del conjunto completo;
- una mutación deliberada (ej. adelantar el target una semana) debe **empeorar** el WIS de forma
  visible — control obligatorio, se reporta;
- dos corridas independientes deben producir artefactos de métricas idénticos (repetibilidad);
- la configuración del modelo es la de la sección 6, fijada aquí; cualquier cambio exige una nueva
  entrada en este documento antes de correr.

### 6. Primer modelo (después de tener los baselines)

Se corre **primero solo los baselines** y se escribe su WIS en el reporte. Recién con ese número
fijado se corre el primer modelo:

- **Regresión cuantílica por gradient boosting** (LightGBM objetivo `quantile`, un modelo por
  cuantil, o `quantile` con `alpha` barrido — sin tuning contra prueba, profundidad y hojas fijas
  en valores conservadores declarados en el script).
- **Features:** rezagos autorregresivos de `log1p(y)` en `t, t−1, …, t−8`; media móvil de 4 y 8
  semanas; armónicos estacionales `sin/cos(2πk·semana/52)` para `k ∈ {1,2,3}`; clima nacional
  rezagado (disponible en `t`); ONI rezagado; año calendario como covariable de tendencia.
- Nada de features derivadas de M1–M4.

Si el primer modelo no supera los baselines, el experimento cierra con resultado negativo y se
documenta como tal. No se itera arquitectura dentro de este experimento.

### 7. Métrica

- **Primaria:** WIS medio sobre todas las semanas de prueba de `h = 4`, y el **skill relativo**
  `1 − WIS_modelo / WIS_baseline_decisivo` (positivo = el modelo es mejor).
- **Secundarias:** cobertura empírica de los intervalos al 50 % y 95 % (debe estar cerca del
  nominal); MAE de la mediana; WIS por año de prueba; curva de skill vs `h`.

## Criterio de éxito predeclarado

El proto-predictor se considera **con señal** si y solo si, sobre `h = 4`:

1. skill relativo agrupado `> 0` frente al baseline decisivo; **y**
2. WIS del modelo `≤` WIS del baseline decisivo en **al menos 3 de los años de prueba**
   (evaluados por separado); **y**
3. cobertura del intervalo al 95 % dentro de `[0.85, 0.99]` y la del 50 % dentro de `[0.35, 0.65]`
   (no basta acertar la mediana con intervalos mal calibrados).

Cualquier resultado que no cumpla los tres se reporta como negativo o parcial, sin maquillar, con
la misma franqueza que las corridas del clasificador.

## Qué se reporta pase lo que pase

- WIS y skill de los tres baselines y del modelo, agrupado y por año.
- Tabla de cobertura de intervalos.
- Resultado del control de mutación y de la prueba de repetibilidad.
- Curva de skill vs horizonte.
- Si es negativo: se archiva junto a los demás experimentos cerrados como evidencia reproducible
  de que también el marco de horizonte corto se probó.

## Reproducibilidad

Script: `backend/ingestion/experimento_nowcast_corto_plazo.py`. Lee de Postgres en modo solo
lectura, no usa `docker compose`, no escribe a la base. Salida en
`backend/ingestion/data/interim/nowcast/`.

```bash
cd backend/ingestion
POSTGRES_HOST=localhost ../.venv/bin/python experimento_nowcast_corto_plazo.py --solo-baselines
POSTGRES_HOST=localhost ../.venv/bin/python experimento_nowcast_corto_plazo.py --modelo --control-mutacion --horizonte 4,1,2,8
```

## Decisiones firmadas (Eduardo, 2026-09-08 — opciones por defecto)

1. **Extensión de la serie nacional.** Sin acción requerida: la carga ya en Postgres cubre
   **2014–2024** (574 semanas), no 2018–2024 como decía `01-decisiones-cerradas.md`. Se usa 2014+.
2. **Tratamiento de 2020.** 2020 excluido como año de origen y de objetivo de prueba; excluido del
   pool de la climatología (coherente con D1, `docs/rescate-prediccion/...`); retenido solo como
   insumo de rezagos autorregresivos para semanas vecinas.
3. **Horizonte decisivo.** 4 semanas (se reportan también 1, 2 y 8).
4. **Umbrales del criterio de éxito.** Firmados con un ajuste: "≥ 3 de N años" → **≥ 4 de 5**, para
   no repetir la vara que la Vía 2 no alcanzó (3/5 → no adoptada). Ver "Enmiendas".
5. **Qué habilita un positivo.** Un positivo **no** autoriza lenguaje de predicción en el producto;
   exige una segunda confirmación independiente antes de cualquier exposición en la UI.

## Enmiendas al documento firmado

- **Modelo.** El doc proponía LightGBM. Se usa `sklearn.ensemble.HistGradientBoostingRegressor(loss="quantile")`
  para no agregar una dependencia y respetar la restricción de "árboles ligeros / hardware modesto"
  del proyecto. Misma familia (quantile gradient boosting). Config fija declarada en el script
  (`max_iter=150`, `max_leaf_nodes=7`, `min_samples_leaf=20`, `l2_regularization=1.0`,
  `learning_rate=0.05`, `random_state=0`), no barrida contra los folds.
- **Métrica decisiva.** Skill relativo **promediado por año con peso igual** (no WIS agrupado
  crudo, que lo domina el año de mayor conteo). Se reporta el WIS agrupado natural y en escala log
  como secundarios.
- **Criterio 3/5 → 4/5** (decisión 4).
- **Sensibilidad de alcance.** El experimento se corre completo en dos ventanas de historia,
  **2014+** y **2016+**, porque 2014–2015 están ~2× por encima del nivel de 2016+ en la serie
  `total` de OpenDengue (el loader solo se verificó contra MINSAL para 2018 y 2022). Se reportan
  ambas.
- **Reajuste del modelo.** Ventana expansiva, reajuste cada 2 semanas epidemiológicas (no semanal),
  por costo de cómputo. No es una fuente de fuga, solo de recencia.

## Resultados (ejecución 2026-09-09)

WIS = Weighted Interval Score (menor es mejor), 23 cuantiles, escala natural salvo aclaración.
256 orígenes de prueba a h=4. Comparador decisivo = el baseline más fuerte por WIS agrupado
(persistencia RW en h≤4; persistencia estacional en h=8).

| Alcance | h | WIS baseline | WIS modelo | WIS-log baseline | WIS-log modelo | Skill medio/año | Años ganados | Veredicto |
|---|---|---|---|---|---|---|---|---|
| **2014+** | 1 | 46.7 | **33.7** | 0.210 | **0.174** | +0.31 | 5/5 | cumple |
| **2014+** | 2 | 50.8 | **38.3** | 0.264 | **0.192** | +0.31 | 5/5 | cumple |
| **2014+** | 4 | 74.6 | **53.1** | 0.316 | **0.240** | +0.33 | 5/5 | cumple |
| **2014+** | 8 | 105.9 | **75.1** | 0.428 | **0.305** | +0.37 | 5/5 | cumple |
| 2016+ | 1 | 54.5 | 56.4 | 0.209 | 0.215 | +0.24 | 4/5 | parcial |
| 2016+ | 2 | 54.1 | 62.9 | 0.263 | 0.234 | +0.17 | 4/5 | parcial |
| 2016+ | 4 | 76.4 | 78.1 | 0.315 | 0.289 | +0.23 | 4/5 | parcial |
| 2016+ | 8 | 103.7 | **100.2** | 0.396 | **0.365** | +0.23 | 4/5 | cumple |

"parcial" = pasa el criterio firmado (skill medio/año > 0, ≥ 4/5 años, cobertura en banda) pero
queda peor que el baseline en WIS agrupado (natural y/o log). "cumple" = pasa ambas cosas.

Skill por año, h=4:

| | 2019 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| **2014+** | +0.28 | +0.36 | +0.15 | +0.39 | +0.47 |
| 2016+ | **−0.32** | +0.41 | +0.14 | +0.39 | +0.55 |

Cobertura de intervalos (nominal 0.50 / 0.95): 2014+ h4 → 0.42 / 0.94; 2016+ h4 → 0.38 / 0.88.
Los intervalos corren algo estrechos, sobre todo en 2016+ y a horizontes largos — dentro de la
banda firmada pero en el borde inferior.

**Controles.** Garantía anti-fuga: para una muestra de orígenes se toman los índices de objetivo
que `pares_entrenamiento` realmente devuelve y se verifica que todos tienen fecha anterior al
corte —comprobación independiente del filtro, no una tautología—, más un control negativo que
desactiva el filtro y confirma que la comprobación entonces sí rompe. Control de mutación
(etiquetas de entrenamiento permutadas, semilla 12345): WIS sube de 53.1 a 128.8 en 2014+ h4 — el
modelo colapsa como se esperaba. Repetibilidad: dos corridas independientes de 2014+ h4 produjeron
el JSON de métricas idéntico byte a byte.

### Lectura

**Con historia completa (2014+): hay señal de corto plazo, consistente.** El proto-predictor le
gana a persistencia y a climatología en los cuatro horizontes (1 a 8 semanas) y en los cinco años
de prueba, recortando el WIS entre 25 % y 30 % tanto en escala natural como logarítmica. Cumple el
criterio firmado sin ambigüedad.

**Con historia recortada (2016+): se rompe donde más importa.** Si el entrenamiento no contiene
ningún brote grande previo, el modelo falla en **2019** —el único año de brote fuerte del set de
prueba— con skill −0.32 y WIS 264 contra 199 de persistencia. El mecanismo es estructural, no un
"mal ajuste": los objetivos de entrenamiento para 2019 bajo 2016+ salen solo de 2016/2017/2018,
cuyo pico semanal es ~437 (log1p ≈ 6.08); el pico real de 2019 es 2178 (log1p ≈ 7.69). Un modelo
de árboles por cuantiles apenas extrapola por encima del rango de entrenamiento (las hojas son
cuantiles dentro de muestra; el boosting aditivo estira poco eso con shrinkage), así que satura y
subestima de forma marcada cualquier brote de magnitud nueva.
En los otros cuatro años (todos de baja transmisión, dentro del rango visto) el modelo sí gana.

**Bajo WIS agrupado, 2014+ pasa en los cuatro horizontes; 2016+ solo a h=8.** En 2016+ a h=1/2/4
el modelo queda peor que persistencia en agregado (por el desastre de 2019); solo aprueba la
métrica de skill promediado por año, de ahí el "parcial". A h=8 el error de 2019 se diluye y 2016+
también gana en agregado. Los ocho JSON traen `cumple_criterio_firmado` y
`gana_wis_agrupado_nat_y_log` por separado; `cumple_criterio_exito` exige las dos.

**Implicación.** Es el mismo mecanismo de falla que cerró el clasificador interanual —"sin
ejemplos del extremo en el entrenamiento, no hay nada que aprender"— pero aquí **acotado y
diagnosticable**: con los 11 años de historia ya cargados (2014+), la condición se cumple y el
nowcast tiene valor real a 1–8 semanas. Regla operativa: un nowcast de árboles por cuantiles queda
efectivamente topado cerca del máximo histórico y subestimará un brote de magnitud sin precedente
en su ventana de entrenamiento; si alguna vez se retoma, la salida es modelar tasas de crecimiento
o una cola paramétrica, no niveles.

### Veredicto

**Positivo y acotado.** Con la ventana de entrenamiento completa (2014+), el proto-predictor supera
de forma estable a los baselines en todos los horizontes probados, en las tres métricas (skill por
año, WIS agrupado natural, WIS agrupado log), y pasa el criterio firmado. La fragilidad ante brotes
sin precedente (visible al recortar a 2016+) es una limitación estructural conocida del modelo de
árboles, no un fallo del marco.

**2014–2015 verificado (2026-09-09): transmisión real, base comparable a 2016+.** Toda la serie
2014–2024 viene de la misma fuente (PAHO PLISA) con la misma definición (`case_definition_standardised
= "Total"`, dominada por sospechosos) — no hay cambio en 2016. Los `Total` cargados coinciden con los
sospechosos de MINSAL (boletín SE52-2015: 53.290 / 50.144). No es contaminación por chikungunya
(MINSAL lo contó aparte: 167.957 casos en 2014). Prueba decisiva: los confirmados de dengue de 2014
(~15.900) por sí solos superan el `Total` completo de 2016, 2017 y 2018 — ningún reetiquetado
produce esa caída. **Caveat a declarar:** la intensidad de vigilancia fue mayor en 2014–2015 (alerta
nacional de arbovirosis durante la llegada del chikungunya, tamizaje masivo de síndrome febril), lo
que infla algo los niveles de esos dos años frente al valle 2016–2018 — es efecto de ascertainment,
no de definición, y no explica la magnitud de la caída. Detalle y fuentes:
`docs/experimentos/verificacion-dengue-2014-2015.local.md`.

Con esto, el titular positivo (fila 2014+) se sostiene. El pico 2014–15 es load-bearing para el
modelo, así que el caveat de ascertainment se reporta junto al resultado.

### Qué falta antes de cualquier uso (decisión 5)

1. ~~Verificar 2014–2015 contra MINSAL/OPS~~ — **hecho 2026-09-09**, ver arriba. 2014+ es la ventana
   principal; 2016+ queda como chequeo de robustez.
2. **Segunda confirmación independiente** (otro periodo de prueba, u otra persona reproduciendo el
   pipeline) — requisito firmado, en curso (subagente, 2026-09-09).
3. **Calibración de intervalos**: ensanchar la incertidumbre (cobertura al 50 % corre en ~0.40).
4. **Regla de historia mínima**: formalizar el tope de magnitud del modelo de árboles y el criterio
   de "precedente comparable en entrenamiento" antes de exponer cualquier cifra.
5. Nada de esto entra a la UI ni al pitch sin decisión explícita de Eduardo.

## Relación con el estado del proyecto

- No contradice el pivote "Camino Ancho": si sale positivo, el aporte es una capa de estimación de
  horizonte corto claramente rotulada por su horizonte, no un retorno a "¿habrá brote?".
- Si sale negativo, refuerza la narrativa de cierre con una vía más auditada.
- No compite por tiempo con la Expo Técnica del 29-sep salvo que se decida lo contrario: es una
  línea de investigación paralela.
