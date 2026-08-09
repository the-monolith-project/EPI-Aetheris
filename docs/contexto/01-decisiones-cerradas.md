# EPI-Aetheris — Decisiones cerradas

> Todo lo marcado aquí está **cerrado / no negociable**. Respételo salvo instrucción explícita del usuario reabriéndolo. Para lo que sigue sin resolver, ver `02-decisiones-abiertas.md`. Para la evidencia empírica detrás de las decisiones de fuentes de datos, ver `03-fuentes-de-datos.md`.

## Alcance y encuadre

- **Alcance geográfico:** nacional (El Salvador) para el MVP; regional/multinacional queda como refuerzo del argumento de escalabilidad, no como entregable.
- **Granularidad regional — "Opción B ampliada":** se construye el parser departamental completo de boletines MINSAL (2018–2023), no solo la vía nacional vía OpenDengue. Compromiso, no opción en evaluación.
- **Regla de ejecución:** dengue funcionando primero. La escalabilidad se diseña y se argumenta, pero el entregable es dengue funcionando — no sobre-ingenierizar la capa agnóstica a costa del MVP.

## Esquema de ingesta

Variable objetivo: `(región, periodo, tipo_evento, clasificación, conteo)` — 5 columnas, no 4. La columna `clasificación` (`probable`/`confirmado`) se agregó porque MINSAL reporta ambas series para semanas distintas dentro de la misma fila; no había dónde ubicar esa distinción sin corromper `tipo_evento`. Predictores: `(región, periodo, variable, valor)` estilo EAV, tabla `variables_ambientales` (no `variables_climáticas`, para dejar espacio a predictores no climáticos futuros).

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

## Alcance del MVP (bloqueado, 2 meses, 3 personas)

1. Ingesta: OpenDengue nacional (narrativo, 2018–2024) + MINSAL departamental (entrenamiento: 2018, 2019, 2021, 2022, 2023) + Open-Meteo (modelo por variable, ver arriba).
2. Pipeline de limpieza + features temporales (rezagos climáticos, medias móviles) a escala **semanal**: humedad relativa media, punto de rocío, precipitación acumulada, horas de lluvia. ET₀ fuera de alcance.
3. Modelo de clasificación alto/medio/bajo por región-semana (etiqueta = función determinista del conteo de casos de la propia semana; el modelo predice esa banda desde el clima — declarar así, no como otra cosa).
4. Dashboard: mapa de riesgo + series temporales + métricas del modelo siempre visibles (incluido margen de error) + indicador explícito de qué años tienen dato departamental real (2018, 2019, 2021–2023) frente a los que no (2020, 2024+).
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
