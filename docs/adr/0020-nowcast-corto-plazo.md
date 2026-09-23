# 0020 - Predicción de casos de dengue a corto plazo (nowcast)

**Estado:** Aceptado (2026-09-09; expuesto en la UI 2026-09-10)

## Contexto

El pivote "Camino Ancho" (2026-08-18, `docs/contexto/01-decisiones-cerradas.md`)
retiró el clasificador de riesgo de brote alto/medio/bajo y, con él, quedó
un veto de facto a la palabra "predicción" en todo el producto. Ese veto se
apoyaba en una creencia, no en una medición: que con esta serie ni un
proto-predictor era viable. Nadie lo había probado con protocolo.

El experimento se firmó antes de correrlo
(`docs/experimentos/experimento-nowcast-corto-plazo.md`, firmado 2026-09-08,
ejecutado 2026-09-09): objetivo, horizonte decisivo, baselines, métrica y
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
