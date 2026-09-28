# 0020 - Predicción de casos de dengue a corto plazo (nowcast)

**Estado:** Aceptado (2026-09-09; expuesto en la UI 2026-09-10; enmendado 2026-09-27)

## Contexto

El pivote a herramienta descriptiva (2026-08-18) retiró el clasificador de
riesgo de brote alto/medio/bajo y, con él, quedó un veto de facto a la
palabra "predicción" en todo el producto. Ese veto se apoyaba en una creencia, no en una medición: que con esta serie ni un
proto-predictor era viable. Nadie lo había probado con protocolo.

El experimento se firmó antes de correrlo (firmado 2026-09-08, ejecutado
2026-09-09): objetivo, horizonte decisivo, baselines, métrica y
criterio de éxito predeclarados, con la configuración del modelo escrita en
el documento antes de ver un resultado. Salió **positivo y acotado**: en la
ventana 2014+ el modelo supera al baseline más fuerte en los cuatro
horizontes probados y gana en 5/5 años de prueba (h=4: WIS 74,6 → 53,1;
skill medio por año +0,33; cobertura 0,42/0,94 contra el nominal 0,50/0,95).
Al recortar la historia a 2016+ el resultado se vuelve parcial y en 2019
el skill cae a −0,32: el modelo de árboles satura ante un brote sin
precedente comparable en entrenamiento.

Antes de exponer nada se cumplieron las tres condiciones que la firma
exigía: verificación de 2014–2015 contra MINSAL/OPS (transmisión real, no
reetiquetado ni contaminación por chikungunya), **segunda confirmación
independiente** con el WIS, el forward-chaining y los baselines
reimplementados desde cero (`backend/ingestion/nowcast_segunda_confirmacion.py`,
paridad a la décima en las 8 filas) y calibración de intervalos (CQR-r).

Eduardo autorizó la exposición el 2026-09-09 y **levantó el veto a la
palabra "predicción"**. Esta ADR registra la decisión, que hasta ahora solo
vivía como un párrafo en `02-decisiones-abiertas.md`.

El número es 0020: 0019 (integridad de la vigilancia) es la última en `dev`.
No lleva migración — no toca el esquema — pero se escribe igual porque es
una decisión de producto y de método, no de esquema.

## Decisión

**A. Qué se predice, y qué no.** El objeto es el **conteo semanal de la
serie nacional agregada de dengue** (OpenDengue V1.3, `clasificacion='total'`,
región `SV`) en `t+h`, `h = 1..8` semanas, como distribución predictiva
completa de 23 cuantiles (el conjunto estándar de los hubs de CDC/OPS, para
que el WIS sea comparable con esa literatura). **No** reabre el clasificador
retirado: no hay etiqueta alto/medio/bajo, no hay juicio de "¿habrá brote?",
no hay salida departamental y no se usa M3 ni sus cortes como objetivo o
como feature.

**B. Método fijo, no barrido.** `HistGradientBoostingRegressor(loss="quantile")`
de scikit-learn (misma familia que LightGBM, sin dependencia nueva), config
declarada antes de correr: `max_iter=150`, `max_leaf_nodes=7`,
`min_samples_leaf=20`, `l2_regularization=1.0`, `learning_rate=0.05`,
`random_state=0`. Objetivo en `log1p`. Features: 8 rezagos de `log1p` de la
serie, medias de 4 y 8 semanas, momento a 4 semanas, tres armónicos anuales
del día del año **de la semana objetivo** (determinista, conocido en `t`),
media de 4 semanas de cada variable climática agregada a nacional, ONI
(ADR 0008) y el año objetivo — **todos disponibles en el origen `t`**,
ninguna variable contemporánea a `t+h`. Validación: forward-chaining de ventana expansiva, reajuste cada 2
semanas, 2020 excluido como origen y objetivo de prueba. Métrica primaria
WIS; comparador el baseline más fuerte (persistencia RW en h≤4, persistencia
estacional en h=8). Intervalos calibrados con **CQR-r**.

**C. Artefacto precomputado y versionado, no cómputo por request.**
`backend/ingestion/nowcast_estimacion_dengue.py` reutiliza la maquinaria ya
validada del experimento y escribe `backend/api/datos/nowcast_dengue.json`
(versionado en el repo): ancla, estimación de 23 cuantiles calibrados por
horizonte, ~120 semanas observadas de contexto, backtest a h=4 en los años
de prueba y el bloque `desempeno` (WIS modelo vs. baseline, skill por año,
años ganados, cobertura empírica). `GET /api/nowcast-dengue` lo sirve tal
cual, con `RATE_LIMIT_HEAVY`; si el archivo falta en un despliegue responde
**200 con `disponible: false` y motivo**, el mismo patrón de
`/api/riesgo-nacional` y `/api/ira/*`. Nada se persiste en Postgres, no hay
cambio de esquema y el entrenamiento no ocurre en producción.

**D. Encuadre obligatorio en la interfaz.** La predicción se extiende
**desde la última semana observada de la fuente, no desde hoy**; el panel
muestra la fecha de ancla explícita y el aviso de honestidad del endpoint lo
repite. Vive como la pestaña "Predicción a corto plazo" de `/dengue`
(`web/src/components/nowcast/PanelNowcastDengue.astro`) y, desde
2026-09-22, tiene además una ruta propia de presentación `/demos/nowcast`
(`noindex`, fuera del sitemap). El desempeño se muestra junto a la cifra,
no en una nota al pie.

**E. Alcance declarado junto al número.** El campo `nota_alcance` del
artefacto y `docs/biblioteca/05-sensibilidad-y-honestidad.md` declaran que
la estimación **asume un brote grande ya presente en el historial de
entrenamiento** (serie desde 2014) y que sin ese precedente el método pierde
ventaja frente a una extrapolación ingenua. El caveat de *ascertainment* de
2014–2015 (alerta nacional de arbovirosis, tamizaje masivo de síndrome
febril) se reporta con el resultado, porque ese pico es load-bearing para el
modelo.

### Alternativas descartadas

* **Recalcular por request desde Postgres**, como M1/M2/M3/M4 — descartado:
  el ajuste es caro y el resultado solo cambia cuando cambia la fuente, que
  va meses atrás. Un artefacto versionado además hace el número auditable y
  reproducible byte a byte.
* **Derivar un semáforo alto/medio/bajo** umbralando el conteo predicho —
  descartado: reintroduce por la puerta de atrás justo la salida que el
  pivote retiró. Si algún día se necesita, exige decisión y ADR propios.
* **2016+ como ventana principal** (la más conservadora) — descartada: es la
  ventana donde el modelo no tiene precedente de brote y falla; usarla como
  titular describiría un modelo peor sin ser más honesto. Se conserva como
  chequeo de robustez y su fragilidad se declara en la nota de alcance.
* **Calibración por inflado global** de los intervalos — descartada frente a
  CQR-r, que lleva la cobertura al 50 % de ~0,40 a ~0,55 sin degradar el
  veredicto en 2014+.
* **LightGBM** (lo que proponía el documento firmado) — descartado para no
  agregar una dependencia y respetar la restricción de hardware modesto.

## Consecuencias

* Positivo: el proyecto recupera una capacidad predictiva **medida**, con
  protocolo predeclarado, confirmación independiente y desempeño a la vista
  — lo contrario del clasificador retirado, que se cerró justamente por no
  sostener esa vara.
* Positivo: sin migración, sin esquema nuevo, sin entrenamiento en
  producción. Un despliegue sin el artefacto degrada a `disponible: false`
  en vez de romper la página.
* Negativo: el ancla es la última semana de OpenDengue V1.3 (2024-12-22), y
  la fuente va ~21 meses detrás del tiempo real. En reloj de pared la
  "predicción" cae en el pasado; el encuadre de la UI es lo único que evita
  leerla como pronóstico de la semana que viene. Cuando OpenDengue publique
  un extracto nuevo hay que recargar la serie y **regenerar el artefacto**;
  hoy eso es manual y no hay recordatorio automático.
* Negativo: el soporte empírico de la robustez ante brotes sin precedente es
  **n = 1** (un solo año, 2019, con un solo brote grande). Probar ese
  mecanismo en una segunda serie o ventana sigue pendiente
  (`02-decisiones-abiertas.md`).
* Negativo: el panel existe duplicado en los dos frontends (`web/` del
  monorepo y el repo vitrina `aetheris-nitor`), así que todo cambio se
  aplica dos veces hasta que se decida cuál copia es la fuente.
* Neutral: el veto de vocabulario queda levantado solo para esta capa y con
  su horizonte rotulado. "Riesgo de brote" sigue prohibido en el producto.

## Ampliación (2026-09-27): predicción desde cualquier semana

La interfaz permite mover el punto de partida de la predicción a cualquier
semana de la serie y contrastar el abanico de 1 a 8 semanas con lo observado
después. El método no cambia; cambia solo cuántos orígenes se precomputan.

* `backend/ingestion/nowcast_retrospectivo_dengue.py` escribe
  `backend/api/datos/nowcast_dengue_retrospectivo.json` y
  `GET /api/nowcast-dengue/retrospectivo` lo sirve con el mismo contrato de
  `disponible: false` que el artefacto principal. Va en un endpoint aparte
  porque pesa unas diez veces más y solo lo pide la vista completa del panel.
* Cada abanico usa solo datos anteriores a su semana de partida. Por
  horizonte corren dos cadenas forward-chaining: la de los orígenes de prueba
  del experimento (misma secuencia de reajustes que el backtest publicado) y
  la del resto de las semanas.
* El script aborta si, a h = 4 en los orígenes de prueba, no reproduce el
  desempeño publicado con su redondeo. No se exige igualdad punto a punto:
  el ajuste no es reproducible bit a bit entre corridas (tampoco
  `nowcast_estimacion_dengue.py`) y una diferencia en la última cifra puede
  mover un factor CQR-r, que se elige por cuantil.
* Las primeras semanas no tienen predicción: el modelo necesita unos tres
  años de historia para entrenarse. El artefacto las marca con `motivo` en
  vez de rellenarlas con persistencia.
* 2020 se muestra con un aviso. Sigue excluido como objetivo de
  entrenamiento, así que mostrarlo no cambia ninguna predicción de los demás
  años, y su resumen no entra en ningún agregado.
* La última semana observada no se duplica: su abanico es `estimacion` del
  artefacto principal.
* La vista está en el frontend `aetheris-nitor`
  (`src/components/nowcast/ContrasteNowcastDengue.astro`); la copia del panel
  en `web/` de este repositorio no la tiene.

## Enmienda (2026-09-27): desde 2025, serie del tablero y mezcla con tendencia amortiguada

El tablero de MINSAL (ADR 0021) extiende la serie nacional a 2025 y 2026 con la misma definición
de caso que OpenDengue, pero con la forma de un promedio de unas seis o siete semanas. Con esa
serie el modelo de esta ADR (M0), entrenado con conteos sin promediar, pierde contra la
persistencia de 1 a 5 semanas en 2025 y 2026 (`docs/experimentos/experimento-nowcast-mejora.md`).

El experimento firmado `docs/experimentos/experimento-nowcast-tendencia.md`, con el script
congelado en el commit 40b6ebb, define el candidato C: la mezcla 50/50 en `log1p` de M0 y de una
tendencia amortiguada (φ = 0,8, pendiente de 3 semanas, residuos de la historia hasta 2023
promediada a 7 semanas). La prueba son las 20 semanas objetivo de 2026-S38 a 2027-S05, a h = 4 y
h = 8, contra la persistencia suavizada. Eduardo decidió publicar C antes del veredicto; la
enmienda del experimento fija qué cambia y qué no.

* Orígenes hasta 2024-S52: M0 sin cambios. Desde 2025-S1: C sobre la serie del tablero.
* `nowcast_estimacion_dengue.py` y `nowcast_retrospectivo_dengue.py` escriben ahora la base de M0
  en `backend/api/datos/nowcast_dengue_opendengue.json` y
  `backend/api/datos/nowcast_dengue_retrospectivo_opendengue.json`.
  `backend/ingestion/nowcast_tablero_dengue.py` lee esa base y el crudo que deja
  `nowcast_retrospectivo_dengue.py`, comprueba que la serie de la base coincide con la de Postgres
  hasta 2024-S52 y que el crudo es el de la base, calcula C con las cadenas del experimento y
  escribe `nowcast_dengue.json` y `nowcast_dengue_retrospectivo.json`, los que sirve la API. Los
  endpoints y su contrato no cambian.
* El artefacto principal parte de la última semana capturada del tablero. Su abanico es la
  predicción de C que se va a puntuar, con anchos monótonos en el horizonte como en la sección C.
  El backtest y el bloque `desempeno` cubren 2025 y 2026 a h = 4 contra la persistencia suavizada,
  con `dentro_de_muestra: true`, porque esos años sirvieron para elegir C. El bloque `prueba`
  describe la prueba prospectiva.
* El retrospectivo marca con `motivo: "hueco_en_serie"` los orígenes de 2025-S53 a 2026-S7, cuya
  ventana de ocho semanas incluye la semana 53 de 2025, que el tablero no publica. El bloque
  `tablero` indica desde dónde rige C.
* A h = 4, en 2025 y 2026: WIS 19,6 frente a 22,8 de la persistencia suavizada (skill +0,14; +0,11
  en 2025 y +0,16 en 2026), cobertura 0,39 al 50 % y 0,91 al 95 %. En 2026 la cobertura del 95 % es
  0,79 a h = 4 y a h = 8, por debajo del 0,85 que exige el criterio. Los fallos se concentran en
  2026-S1 a S3, con el salto del cambio de año, y en S19 a S22. La prueba incluye el cambio de año
  de 2027.

Consecuencias:

* El ancla va unas dos semanas detrás del tiempo real, en lugar de los ~21 meses de OpenDengue. El
  encuadre de la sección D sigue: la predicción parte de la última semana publicada, no de hoy.
* Actualizar exige capturar el tablero y cargarlo (ADR 0021), recargar el clima hasta la semana de
  anclaje (`cargar_clima.py`), tener en `semanas_epidemiologicas` las ocho semanas siguientes
  (`poblar_semanas_epidemiologicas.py` antes de 2027) y correr `nowcast_tablero_dengue.py`, con
  el crudo de `nowcast_retrospectivo_dengue.py` en la misma máquina. El volcado de `db/seed` no
  incluye el tablero, así que desde un clon limpio solo se puede regenerar la base de M0.
* Si C no se confirma al corte, rige «Qué habilita cada resultado» del experimento: el sitio vuelve
  a M0 y dice que, con la serie del tablero, no supera a la persistencia.
* Los dos frontends muestran los textos de desempeño según el periodo. La vista de contraste desde
  cualquier semana sigue solo en `aetheris-nitor`.
