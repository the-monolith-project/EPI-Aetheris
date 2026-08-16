# 0008 - Nueva fuente de datos: NOAA ONI (Oceanic Niño Index) como predictor experimental

**Estado:** Aceptado

## Contexto

Las corridas de evaluación con años de prueba reales (2019, 2022 — ver `docs/contexto/CHANGELOG.md`, entrada 2026-08-16) mostraron que el clasificador de riesgo nacional obtiene **recall de "alto" = 0,000** en ambos, empatado con la línea base climatológica. El experimento de ampliar la ventana de rezago climático (4→4/8/12 semanas) no movió esa métrica (`docs/experimento-ventana-climatica-ampliada.md`). El clima local rezagado (Open-Meteo, por departamento) no está capturando la señal de brote severo.

La literatura epidemiológica documenta El Niño/La Niña (medido por el índice ONI de NOAA) como factor asociado a brotes de dengue en Centroamérica — condiciones más cálidas y secas durante El Niño favorecen la cría de *Aedes aegypti* en agua almacenada. Es una oscilación climática de escala oceánica/continental, distinta en naturaleza del clima superficial local que ya se usa (temperatura, humedad, precipitación por departamento) — no reemplaza esas variables, las complementa con una señal que Open-Meteo no puede dar por diseño (es un dato puntual por coordenada, no un índice de teleconexión).

**Verificado en vivo antes de decidir** (no asumido de memoria): `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` — texto plano público, HTTP 200 sin autenticación, serie mensual (rolling de 3 meses) desde 1950 hasta el mes más reciente disponible.

**Tensión con la decisión cerrada del predictor (2026-08-09):** "el predictor es únicamente clima rezagado... los casos MINSAL tienen un solo rol, construir la etiqueta." ONI no es un dato de casos (no reabre esa parte de la decisión, que existe para no depender de una fuente departamental de casos inexistente en vivo tras 2023) — es una serie climática/oceánica, publicada con meses de antelación suficiente para seguir siendo utilizable en producción. Se interpreta como una extensión de "clima rezagado", no una excepción a la regla — el coordinador confirmó explorar esta vía.

## Decisión

**A. Nueva fila de catálogo:** `fuentes_datos.codigo = 'noaa_oni'`, sin cambio de estructura — mismo principio de extensión que `tipos_evento`/`open_meteo_era5` (ADR 0006).

**B. Nueva variable:** `oni_anom` en `variables_ambientales.variable` (catálogo de texto libre, sin `CHECK` — ver `CLAUDE.md`, actualizado en la misma sesión que este ADR). Valor = anomalía de temperatura superficial del mar (ANOM), no el valor absoluto (TOTAL) — es la anomalía la que se usa operacionalmente para clasificar fase El Niño/Neutral/La Niña.

**C. Resolución temporal — mapeo, no fabricación.** ONI es un índice de **estado** (nivel oceánico), no un conteo acumulable como los casos de MINSAL Admin1 (que si se fraccionaran entre semanas sí fabricarían dato, por eso esa fuente se descartó). Asignar el mismo valor mensual a cada semana epidemiológica dentro de ese mes es una operación de resolución honesta (el dato real no tiene granularidad semanal, se declara tal cual), no una interpolación ni un reparto de una cantidad que sí la tiene. Mes de referencia de cada semana epidemiológica: mes calendario de `semanas_epidemiologicas.fecha_inicio`. Convención de temporada NOAA verificada en vivo: cada código de 3 letras (DJF, JFM, ..., NDJ) representa el mes central de una ventana móvil de 3 meses, y el año publicado (`YR`) corresponde al año calendario de ese mes central (confirmado: `DJF 1950` es dic-1949/ene-1950/feb-1950, año publicado 1950 = año de enero).

**D. Región:** se almacena bajo `regiones.codigo = 'SV'` (nacional, `nivel_admin = 0`) — el esquema ya permite esto sin cambio (`variables_ambientales.region_id` no restringe por `nivel_admin`). No se departamentaliza: ONI no tiene resolución subnacional, atribuirlo a los 14 departamentos por igual sería una fila repetida 14 veces sin información nueva.

**E. Estado experimental, no de producción todavía.** Se carga y se prueba como predictor adicional (junto a `construir_dataset_modelado.py`, análogo a los experimentos de corte/ventana/años ya documentados) antes de decidir si entra al conjunto de features de producción — no se asume que ayuda solo porque la fuente es real y verificada.

## Consecuencias

* Positivo: primera fuente climática de escala oceánica/continental del proyecto — complementa, no compite con, el clima superficial local ya cargado.
* Positivo: gratuita, sin límite de tasa documentado, formato estable (texto plano, sin versión de API que romper).
* Negativo: introduce una segunda escala temporal (mensual) dentro de una tabla pensada originalmente para datos ya-semanales — el mapeo mes→semana (punto C) es una elección de diseño nueva que hay que mantener consistente si se agregan más fuentes de resolución distinta a la semanal en el futuro.
* Negativo: NOAA publica el ONI con un retraso de aproximadamente un mes respecto al mes en curso — relevante si alguna vez se usa para inferencia "en vivo" (ver punto F de `docs/contexto/02-decisiones-abiertas.md`, el sistema ya no verifica en vivo lo que predice, así que esto no agrega una limitación nueva).
* Neutral: no reabre la decisión cerrada de predictor climático — se interpreta como una extensión de "clima", no como autocorrelación de casos.

## Migración

`db/migrations/0006_fuente_noaa_oni.sql` — una única fila de catálogo, sin cambio de estructura, igual patrón que la migración `0004`.
