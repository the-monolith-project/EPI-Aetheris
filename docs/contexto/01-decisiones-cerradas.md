# EPI-Aetheris — Decisiones cerradas

> Todo lo marcado aquí está **cerrado / no negociable**. Respételo salvo instrucción explícita del usuario reabriéndolo. Para lo que sigue sin resolver, ver `02-decisiones-abiertas.md`. Para la evidencia empírica detrás de las decisiones de fuentes de datos, ver `03-fuentes-de-datos.md`.

## Alcance y encuadre

- **Alcance geográfico:** nacional (El Salvador) para el MVP; regional/multinacional queda como refuerzo del argumento de escalabilidad, no como entregable.
- **Granularidad regional — "Opción B ampliada", producto amendado por el pivote "Opción C" (2026-08-09):** se sigue construyendo el parser departamental completo de boletines MINSAL (2018–2023) — no se revierte, sigue siendo compromiso, no opción en evaluación —, pero su producto cambia de "variable objetivo de la primera entrega" a "capa descriptiva para el mapa + variable objetivo condicionada a un reconteo posterior". Ver "Pivote de fase 1 — Opción C" más abajo para el detalle y el motivo.
- **Regla de ejecución:** dengue funcionando primero. La escalabilidad se diseña y se argumenta, pero el entregable es dengue funcionando — no sobre-ingenierizar la capa agnóstica a costa del MVP.

## Esquema de ingesta

Variable objetivo: `(región, periodo, tipo_evento, clasificación, conteo)` — 5 columnas, no 4. La columna `clasificación` (`probable`/`confirmado`) se agregó porque MINSAL reporta ambas series para semanas distintas dentro de la misma fila; no había dónde ubicar esa distinción sin corromper `tipo_evento`. Predictores: `(región, periodo, variable, valor)` estilo EAV, tabla `variables_ambientales` (no `variables_climáticas`, para dejar espacio a predictores no climáticos futuros).

**Tercer valor de `clasificación`: `total` (cerrado 2026-08-09, ADR 0005, migración `db/migrations/0003_clasificacion_total_opendengue.sql`).** Al cargar la serie nacional de OpenDengue (tarjeta 11) se confirmó que su columna `case_definition_standardised` vale `'Total'` en el 100 % de las 574 filas semanales de Admin0 — OpenDengue no separa probable/confirmado para El Salvador a esta resolución. Insertar ese total bajo `'confirmado'` habría mezclado, bajo una misma etiqueta, una cifra agregada con la confirmación de laboratorio real de MINSAL (órdenes de magnitud menor). `clasificacion` admite ahora `'probable'`, `'confirmado'` o `'total'`; `'total'` se puebla solo para `fuente_id = opendengue_v1_3` a nivel nacional — nada en el esquema fuerza esa correspondencia, es disciplina del loader (`backend/ingestion/cargar_opendengue.py`). **Consecuencia para quien consuma la tabla:** sumar `conteo` agrupando solo por `(región, año, semana)` sin filtrar por `clasificación` mezcla tres definiciones de caso distintas — filtrar siempre por `clasificación` según la serie que se necesite.

**Carga de OpenDengue nacional — ejecutada (2026-08-09, tarjeta 11).** `backend/ingestion/cargar_opendengue.py` resuelve la semana epidemiológica de cada fila por coincidencia exacta de `calendar_start_date` contra `semanas_epidemiologicas.fecha_inicio` (nunca recalculada con `epiweeks` de forma independiente, para no arriesgar un desfase con la tabla ya sembrada) y no filtra por el campo `Year` del CSV al leer (ese año es de calendario, no epidemiológico — una fila con `calendar_start_date` a fines de diciembre puede resolver a la SE01 del año siguiente; el filtro de rango se aplica después, sobre el año epidemiológico ya resuelto). 365 filas cargadas para 2018–2024. Verificación contra cifras nacionales conocidas: cercana pero no idéntica año a año (ej. 2018: 8.448 cargado vs. 8.443 documentado desde boletín MINSAL SE52; 2022: 16.542 vs. 16.529) — diferencia esperada y documentada, no forzada a cuadrar, porque la definición de caso de OpenDengue no es necesariamente la misma que la que MINSAL publica como cifra nacional. **Hallazgo colateral:** la resolución semanal de Admin0 en el extracto real cubre desde 2013/2014, no "desde 2018" como decía la documentación anterior — el filtro a 2018–2024 es una decisión de alcance (ventana narrativa/de entrenamiento acordada), no un límite real de la fuente; si se necesita historia más larga, está disponible sin volver a descargar nada.

**Regla de ADR previo (no negociable):** toda modificación de esquema (columnas, restricciones, valores de `CHECK`, tablas nuevas) exige un ADR aceptado en `docs/adr/` *antes* de escribir la migración — plantilla en `docs/adr/0001-plantilla-base.md`.

**Estado real del esquema (verificar siempre contra `db/migrations/` y `docs/adr/`, no contra este documento):**
- `db/migrations/0001_init_schema.sql` — DDL base: `casos_epidemiologicos`, `variables_ambientales`, catálogos `regiones`/`tipos_evento`/`fuentes_datos`, `semanas_epidemiologicas`, `boletines_procesados`.
- `db/migrations/0002_bitacora_boletines_y_coordenadas_regiones.sql` — respalda ADR 0003 y ADR 0004 juntas (empaquetadas para no pagar dos ciclos de `docker compose down -v` con la base todavía vacía):
  - **ADR 0004:** `boletines_procesados.nombre_archivo TEXT UNIQUE` como llave natural real (no `url_origen`, que es una cadena reconstruida, no un dato observado) — el parser hace `INSERT ... ON CONFLICT (nombre_archivo) DO UPDATE`, idempotente por diseño. Columna `version SMALLINT` parseada del sufijo del archivo (`_v2`→2, etc.) para precedencia explícita entre republicaciones. Quinto valor de `estado`: `ausencia_esperada` (boletín abierto sin error pero sin tabla departamental por diseño — vacaciones o semanas combinadas — no cuenta como fallo de ingesta, distinto de `error` y `revision_manual`). `semana_archivo` deja de ser `NOT NULL`. `casos_epidemiologicos.boletin_id` (nullable, solo para filas `minsal_pdf`) traza cada fila al boletín exacto que la produjo.
  - **ADR 0003:** `regiones.centroide_lat`, `centroide_lon`, `elevacion_m` — punto representativo del polígono de mayor área por departamento (`backend/ingestion/compute_centroides.py`), deliberadamente distinto del centro de celda que devuelve cualquier proveedor climático.
- **No incluido en esa migración:** la atribución de fuente climática en `fuentes_datos` (dos modelos en juego, sin ADR propio todavía) — ver `02-decisiones-abiertas.md`.

## Stack tecnológico (cerrado 2026-07-15)

Python + FastAPI + scikit-learn (Random Forest / Gradient Boosting) para backend/ML, acceso a Postgres con `psycopg2` sin ORM. `pdfplumber` para extracción de PDF (MarkItDown evaluado y descartado: baja fidelidad en tablas, dependencia de API de pago, objetivo de diseño equivocado). PostgreSQL 15. Astro + TypeScript + Leaflet (`pnpm`) para frontend/mapa. Docker Compose para orquestación.

**Por qué:** el ecosistema de ML clásico favorece fuertemente a Python frente a JS/TS, con más documentación en español — relevante para el plazo y el nivel de bachillerato del equipo. Astro/TS/Leaflet se asigna porque ahí el equipo (0V3R) ya tiene fortaleza real (Node.js, Astro, TypeScript, Tailwind, Supabase), reduciendo curva de aprendizaje en la capa que el jurado evalúa primero. Todo-Python (Streamlit/Dash) y todo-TypeScript (ML en JS) fueron evaluados y descartados por menor pulido de UI y ecosistema inmaduro de árboles/boosting en JS, respectivamente.

### Herramientas complementarias del frontend (cerrado 2026-08-13; adopción diferida)

Se aprueba técnicamente, dentro de Astro sin React/Vue, la adopción futura de: `astro-icon` + Iconify para SVG reutilizable; `@fontsource/inter` y `@fontsource/ibm-plex-mono` para auto-hospedar las tipografías actuales; Observable Plot para las visualizaciones de métricas; ColorBrewer como base de paleta y Chroma.js (`chroma-js`) para escalas de color; `@astrojs/check`, ESLint + `eslint-plugin-astro` y Prettier + `prettier-plugin-astro` como tooling de calidad; Playwright + `@axe-core/playwright` para E2E y accesibilidad; e i18n nativo de Astro para internacionalización futura.

`simple-statistics` queda **aprobada condicionalmente**. Las condiciones de su adopción, los pendientes de Playwright/axe y la activación de i18n se registran exclusivamente en el [punto I de `02-decisiones-abiertas.md`](02-decisiones-abiertas.md#i-estrategia-de-implementación-de-herramientas-aprobadas-del-frontend).

**La aprobación técnica no equivale a instalación.** Ningún paquete se agrega a `web/package.json` hasta que la funcionalidad asociada lo necesite, se evalúen versión, licencia, tamaño y configuración, y se implemente en su propio cambio. Se mantienen Astro, TypeScript, Tailwind CSS v4 y Leaflet como stack vigente; no se introduce React ni Vue. Detalle y orden de adopción: `docs/levantamiento-gaps-stack-web.md`.

## Invariantes de infraestructura (no negociables)

GNU/Linux, hardware modesto. Docker obligatorio, despliegue reproducible con un comando (`git clone` + `docker compose up`). Open-source y self-hosted: sin APIs de pago, sin límites freemium ocultos, sin suscripciones obligatorias en el core. Costo de replicación para un tercero → $0. Hardware mínimo estimado: 4 GB RAM, CPU doble núcleo x86-64, ~10 GB almacenamiento (series semanales, modelos de árboles ligeros).

## Fuente y modelo climático (cerrado 2026-07-14, modelo enmendado 2026-08-07)

**Open-Meteo**, API gratuita alojada — self-hosting evaluado y descartado (función de recorte geográfico "mayormente sin documentar" según los propios mantenedores; sin ella, sincronizar la grilla global cuesta decenas/cientos de GB, excede el presupuesto de hardware sin beneficio proporcional al volumen real necesario: 14 puntos, consultados una vez). Uso no comercial confirmado sin zona gris (términos oficiales listan explícitamente investigación pública e institución educativa).

**El modelo no es único, es uno por variable** (enmendado 2026-08-07 — la redacción original fijaba `era5_land`/`best_match` para todo, y esa premisa resultó falsa al probarla en vivo):

| Variables | Modelo | Resolución |
|---|---|---|
| `temperature_2m_max/min/mean`, `relative_humidity_2m_mean`, `dew_point_2m_mean` | `era5_land` | 0,1° (14/14 celdas distintas) |
| `precipitation_sum`, `precipitation_hours` | `era5` | 0,25° (13/14 celdas — La Libertad y San Salvador comparten celda, aceptado deliberadamente) |

`era5_land` no sirve precipitación en Open-Meteo (limitación de la implementación, no del dataset). **Prohibidos `best_match` y `era5_seamless`** — mezclan grilla sin exponer qué modelo produjo cada variable. `ecmwf_ifs` fue evaluado (14 celdas distintas, precipitación real) y descartado: es archivo de corridas operativas, no reanálisis estático, y cambia entre versiones del modelo — varias caen dentro de la ventana de entrenamiento, lo que contaminaría la comparación año a año sobre la que se entrena y valida el clasificador. ET₀ queda fuera de alcance. Evidencia completa: `backend/ingestion/clima/hallazgos_precipitacion_modelo.md`.

**Guarda de pipeline obligatoria:** `precipitation_hours` bajo `era5_land` devuelve `0.0` (no `null`) incluso sin datos de precipitación — cero fabricado. Rechazar `precipitation_hours` de cualquier respuesta donde `precipitation_sum` venga nulo. Se conserva aunque la config actual ya no pida precipitación a `era5_land`, para proteger contra una regresión de configuración futura.

**Atribución de fuente climática — cerrado 2026-08-10 (ADR 0006, migración `db/migrations/0004_fuente_climatica_era5.sql`).** `fuentes_datos` tiene ahora dos filas de Open-Meteo: `open_meteo_era5_land` (las cinco variables de superficie) y `open_meteo_era5` (`precipitation_sum`/`precipitation_hours`), en vez de atribuir toda la tabla al mismo modelo. Sin cambio de estructura — solo una fila de catálogo nueva, mismo principio de extensión que `tipos_evento`. `variables_ambientales.fuente_id` correcto por variable es responsabilidad del loader (`backend/ingestion/cargar_clima.py`), no una garantía del esquema.

**Carga real de clima — ejecutada (2026-08-10, tarjeta 12).** `backend/ingestion/cargar_clima.py` llama `archive-api.open-meteo.com` dos veces (una por modelo), cada una con los 14 departamentos en una sola petición multi-ubicación — no 14 llamadas, el estimado de ~2.200 llamadas ponderadas de julio no se materializó porque multi-ubicación cuenta como una sola petición HTTP. **Trampa nueva confirmada en vivo:** el límite por minuto se dispara con pocas llamadas seguidas (`429 Too Many Requests`) aunque el límite diario/mensual esté lejos de tocarse — el loader reintenta con backoff (15 s × intento, hasta 5 intentos). Cargadas 35.868 filas: 7 variables × 14 departamentos × 2018–2024 completo, **incluyendo 2020** (la exclusión de 2020 es de entrenamiento, no de ingesta — ver `02-decisiones-abiertas.md`, punto E). Valores verificados decimal a decimal contra una llamada cruda de control (semana 25/2023, San Salvador). **Agregación diaria → semanal, elección de implementación, no cierre de equipo:** media semanal para `temp_max`/`temp_min`/`temp_media`/`humedad_relativa_media`/`punto_rocio` (variables de estado), suma semanal para `precipitation_sum`/`precipitation_hours` (variables acumulativas) — revisar si se necesita otro criterio (ej. máximo semanal del máximo diario). **Coordenadas y elevación de `regiones` quedaron pobladas como efecto colateral** (ADR 0003 aceptado desde el 2026-08-07, pero ninguna carga anterior escribía esas columnas) — `elevacion_m` sale de la respuesta de Open-Meteo (DEM interno), no de una medición topográfica propia.

Dos endpoints en combinación: `archive-api` (histórico, entrenamiento) y `forecast?past_days=` (semanas recientes no disponibles aún en el reanálisis, 5–7 días de retraso). Sin agregación semanal nativa — el pipeline suma/promedia diarios en el pipeline, igual que MINSAL.

## Ventana de entrenamiento del modelo (cerrado)

El clasificador departamental entrena con MINSAL **2018, 2019, 2021, 2022, 2023 — 2020 excluido**. Motivo doble: riesgo de desalineación en extracción de texto (Familia A) y evidencia real de subregistro por disrupción de vigilancia epidemiológica durante la pandemia. 2019 (26.434 casos, pico histórico) es indispensable para que el modelo vea un brote severo real — una ventana 2021–2023 sola nunca se lo muestra. Esta exclusión es solo de *entrenamiento departamental*: la serie nacional narrativa/exploratoria (OpenDengue Admin0, 2018–2024) sí incluye 2020, con nota aclaratoria en vez de ocultarlo.

## Predictor del modelo (cerrado 2026-08-09)

El predictor es **únicamente clima rezagado**; los casos MINSAL tienen un solo rol, construir la etiqueta — no son predictor. Confirmado contra el informe de investigación (la variable independiente son las climáticas; los casos son referencia de validación) y contra la promesa de anticipación ya comprometida ante el docente: un predictor autorregresivo con casos recientes rompería esa promesa porque no hay fuente departamental automatizable desde 2024. Sub-decisión con inclinación pero no cerrada: departamento no entra como categórica, se usa elevación como proxy geográfico.

## Etiqueta de riesgo alto/medio/bajo — método (cerrado 2026-08-05, parámetros abiertos)

Se construye por **canal endémico** (percentil histórico dentro de cada departamento), nunca por umbral de incidencia poblacional. Motivo decisivo: el denominador poblacional de la ventana quedó invalidado por el Censo 2024 (~5% de sobrestimación nacional, error departamental no cuantificable) — un error ahí caería en la **variable objetivo**, no en un predictor, volviendo ininterpretables las métricas. La incidencia se conserva solo como métrica de contexto, nunca como etiqueta.

Dos criterios de método fijados (no debatibles): el año etiquetado nunca puede estar en su propia línea base de percentiles (fuga de información), y la suficiencia de la línea base se cuenta sobre observaciones realmente presentes por (departamento, año objetivo, semana), nunca contra una tabla precalculada. La columna "Tasa x 100.000" de Familia A se extrae y conserva siempre en `data/interim/` (no en la tabla de hechos), independientemente de esta decisión — es la única vía para recuperar el denominador que MINSAL usó. Parámetros (variable base, cortes de percentil, ventana de semanas, esquema de años base, piso de suficiencia, techo de columnas) siguen abiertos — ver `02-decisiones-abiertas.md`.

## Criterio de éxito, línea base y margen de error (cerrado 2026-08-09)

**Línea base doble:** climatológica (predice la banda típica histórica; ancla el contraste de hipótesis pese a colapsar casi siempre en la clase media por cómo se fijan los cortes de percentil) y de persistencia (semana = semana anterior; referencia dura pero **no desplegable en vivo**, porque depende de una etiqueta de la semana anterior que no existe para departamentos desde 2024 — se muestra igual si el modelo no la supera, con esa aclaración).

**Métrica decisiva — comparativa, no absoluta:** el modelo debe superar a la línea base climatológica en **F1 macro y recall de la clase alta, por año de prueba**. Recall de "alto" es criterio explícito, no nota al pie — buen F1 macro con mal recall en la clase alta sería la falsa promesa que prohíbe el Pilar 3. Sin umbral absoluto todavía (depende de la prevalencia real de "alto", pendiente de la corrida de distribución de clases).

**Margen de error, orden de construcción:** (1) matriz de confusión por año — mínimo obligatorio; (2) tabla precisión/recall/F1 por clase; (3) selector de año, no agregación. Probabilidades calibradas por celda quedan diferidas a post-MVP (exigen calibración sobre un modelo que aún no existe; mal calibradas serían peores que ausentes).

Esto resuelve como efecto colateral la validación retrospectiva con OpenDengue Admin1: ese extracto es mensual, incompatible con un clasificador semanal — se descarta a favor de validación temporal simple (entrenar en años viejos, probar contra el más reciente).

## Librería de calendario epidemiológico (cerrado 2026-08-05)

Se adopta `epiweeks` (PyPI, cálculo CDC/MMWR que PAHO adopta) en vez de recalcular límites de semana a mano. Fijada en `backend/requirements.txt` junto con `pdfplumber`, ambas con versión pinneada.

## Pivote de fase 1 — Opción C: clasificador nacional primero (cerrado 2026-08-09)

**Motivo:** el punto H de `02-decisiones-abiertas.md` (semántica acumulada de Probable/Confirmado MINSAL) bloqueaba por completo el parser departamental. Una corrida exploratoria (`backend/ingestion/corrida_distribucion.py`, 264 PDF, ver `03-fuentes-de-datos.md` trampa 8) validó la desacumulación pero mostró que la señal departamental es delgada — especialmente confirmado, que no sirve como única variable objetivo departamental (92,8 % de celdas en cero). Esperar a resolver eso por completo antes de tener cualquier clasificador funcionando ponía en riesgo el hito de rebanada vertical.

**Decisión:** la serie nacional semanal de OpenDengue (limpia, sin huecos, 2018–2023, con dinámica real de brote) pasa a ser la variable objetivo del **primer** clasificador entregado — misma lógica de canal endémico, misma regla de fuga de información, 1 región (país) en vez de 14 departamentos; la aritmética del piso de suficiencia funciona igual. La carga de OpenDengue nacional sube de prioridad media a inmediata. **El mapa del hito planeado pinta los datos departamentales descriptivos de MINSAL** (probables desacumulados, que sí existen y varían por departamento) **junto con el indicador de riesgo nacional como banda/semáforo separado** — la interfaz debe declarar explícitamente que la clasificación es a nivel nacional; no pintar los 14 departamentos del mismo color presentándolo como riesgo departamental (norma de honestidad del proyecto, no un detalle de UI).

**Lo que NO cambia:** el parser departamental de MINSAL se sigue construyendo (alimenta la capa descriptiva del mapa desde ya) y, si la señal de `probable` sobrevive a un reconteo posterior (tras rescatar los boletines de 2019 con tabla-imagen, ver `03-fuentes-de-datos.md` trampa 11, y aplicar la ventana de semanas vecinas ±1), se agrega como segundo clasificador sobre la misma infraestructura — cambiar el filtro de región, no reescribir código. Ver `02-decisiones-abiertas.md`, punto H, para lo que sigue condicionado.

## Alcance del MVP (bloqueado, 2 meses, 3 personas)

1. Ingesta: OpenDengue nacional (narrativo 2018–2024, y ahora también variable objetivo de la primera entrega — ver "Pivote de fase 1" arriba) + MINSAL departamental (capa descriptiva desde el primer hito; entrenamiento de un segundo clasificador condicionado: 2018, 2019, 2021, 2022, 2023) + Open-Meteo (modelo por variable, ver arriba).
2. Pipeline de limpieza + features temporales (rezagos climáticos, medias móviles) a escala **semanal**: humedad relativa media, punto de rocío, precipitación acumulada, horas de lluvia. ET₀ fuera de alcance.
3. Modelo de clasificación alto/medio/bajo por **región-semana, con región = país en la primera entrega** (ver "Pivote de fase 1" arriba); departamental queda como segundo clasificador condicionado al reconteo de la señal MINSAL, no parte garantizada del MVP. Etiqueta = función determinista del conteo de casos de la propia semana; el modelo predice esa banda desde el clima — declarar así, no como otra cosa.
4. Dashboard: mapa con coropleta departamental descriptiva (MINSAL, probables desacumulados) + banda/semáforo de riesgo nacional junto al mapa, con leyenda explícita de que la clasificación es a nivel nacional + series temporales + métricas del modelo siempre visibles (incluido margen de error) + indicador explícito de qué años tienen dato departamental real (2018, 2019, 2021–2023) frente a los que no (2020, 2024+).
5. Contacto de autoridades competentes ante un brote (lista estática).
6. Despliegue de un comando (contenedorizado).
7. Validación retrospectiva honesta (entrenar hasta año X, predecir X+1, mostrar aciertos y fallos) vía validación temporal simple (ver arriba).

**Diferido, NO parte del MVP (no prometer):** vista de detalle completo, regresión del número de casos, forecasting real a fechas futuras, filtro municipal (sin fuente automatizable), dashboard de autoridades con capacidad hospitalaria (sin fuente identificada), recomendaciones automáticas por nivel de riesgo, comparación multi-enfermedad, segunda enfermedad/región como demo de escalabilidad.

## Restricciones éticas y de honestidad (NO NEGOCIABLES)

- Herramienta de priorización complementaria, nunca oráculo médico ni diagnóstico — la interfaz nunca afirma certezas.
- Métricas y márgenes de error siempre visibles en el dashboard, nunca ocultos.
- Validación retrospectiva honesta, mostrando fallos además de aciertos.
- Solo datos agregados públicos (sin datos personales) — sin problema de privacidad, así debe permanecer.
- Nada de datos fabricados, nada de "nadie se dará cuenta", riesgos reales declarados desde el día uno.
- No fabricar datasets propios, en ningún caso: todo dato debe venir de fuentes públicas, reales, verificables y citables, para que cualquier evaluador reproduzca las métricas.

## Posicionamiento frente al estado del arte

Dengue + ML + clima es un campo académico maduro (Bangladesh, Vietnam, India, Brasil — LightGBM/XGBoost/LSTM/SHAP). **Nunca presentar el modelo como novedoso.** El diferenciador honesto: (1) esos trabajos son papers, ninguno entrega software open-source desplegable a costo cero — EPI-Aetheris sí; (2) la arquitectura agnóstica al evento no aparece en esa literatura (cada trabajo está hardcodeado a su enfermedad/región); (3) el foco El Salvador/Centroamérica es un nicho poco cubierto frente a la literatura asiática/brasileña.
