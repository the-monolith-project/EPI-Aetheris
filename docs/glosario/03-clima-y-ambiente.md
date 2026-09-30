# Rama 3 · Clima y ambiente

Vocabulario de las variables climáticas y oceánicas que el proyecto usa como contexto y como insumo de los módulos M1 y M2 y del nowcast: de dónde salen, con qué modelo y resolución, cómo se agregan a semana epidemiológica y qué trampas se documentaron.

**Para quién es.** Para quien lee `cargar_clima.py`, una fila de `variables_ambientales`, el panel de idoneidad o el ADR de Open-Meteo y necesita saber qué significan `era5_land`, «punto de rocío», «cero falso» u «ONI».

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris), **Dónde** (archivo, ADR o endpoint) y **Ojo** (errores frecuentes). Las expansiones de siglas que el repositorio no da se marcan como «de uso general».

**Ramas vecinas.** Las fuentes de casos y la ingesta general están en [`02-fuentes-de-datos-e-ingesta.md`](02-fuentes-de-datos-e-ingesta.md); las fórmulas de idoneidad (`Iv`) y anomalía, en [`05-modulos-descriptivos-y-alertas.md`](05-modulos-descriptivos-y-alertas.md); el uso del clima en los modelos, en [`04-estadistica-y-modelado.md`](04-estadistica-y-modelado.md).

<!-- INDICE:INICIO -->

## Índice alfabético (44 entradas)

- **A** — [Agregación diaria a semana epidemiológica](#agregación-diaria-a-semana-epidemiológica) · [Anomalía ONI (oni_anom)](#anomalía-oni-oni_anom) · [Asignación mensual a semanal (no interpolación)](#asignación-mensual-a-semanal-no-interpolación)
- **B** — [best_match y era5_seamless (prohibidos)](#best_match-y-era5_seamless-prohibidos)
- **C** — [Caja geográfica (validación de coordenadas)](#caja-geográfica-validación-de-coordenadas) · [Capa climática hasta el presente](#capa-climática-hasta-el-presente) · [Celda de grilla y resolución espacial](#celda-de-grilla-y-resolución-espacial) · [Centroide (centroide_lat, centroide_lon)](#centroide-centroide_lat-centroide_lon) · [Cero falso de la precipitación](#cero-falso-de-la-precipitación) · [Clima congelado (2024 y anteriores)](#clima-congelado-2024-y-anteriores) · [Clima rezagado](#clima-rezagado) · [Colapso de celda](#colapso-de-celda) · [Condición biofísica frente a incidencia](#condición-biofísica-frente-a-incidencia) · [Cuota y límites de uso gratuito](#cuota-y-límites-de-uso-gratuito)
- **E** — [ECMWF IFS](#ecmwf-ifs) · [El Niño y La Niña](#el-niño-y-la-niña) · [Elevación (elevacion_m)](#elevación-elevacion_m) · [ERA5](#era5) · [ERA5-Land](#era5-land) · [Estado del ONI como predictor](#estado-del-oni-como-predictor) · [Evapotranspiración de referencia (ET₀)](#evapotranspiración-de-referencia-et₀)
- **G** — [Guarda de precipitación](#guarda-de-precipitación)
- **H** — [Heterogeneidad temporal entre versiones de un modelo](#heterogeneidad-temporal-entre-versiones-de-un-modelo) · [Horas de precipitación (precipitation_hours)](#horas-de-precipitación-precipitation_hours) · [Humedad relativa media (humedad_relativa_media)](#humedad-relativa-media-humedad_relativa_media)
- **L** — [Límite de tasa (429) y reintento](#límite-de-tasa-429-y-reintento)
- **M** — [Modelo explícito por variable](#modelo-explícito-por-variable)
- **O** — [ONI (Oceanic Niño Index)](#oni-oceanic-niño-index) · [Open-Meteo](#open-meteo)
- **P** — [Petición multiubicación](#petición-multiubicación) · [Precipitación acumulada (precipitation_sum)](#precipitación-acumulada-precipitation_sum) · [Punto de rocío (punto_rocio)](#punto-de-rocío-punto_rocio) · [Punto representativo (frente a centroide)](#punto-representativo-frente-a-centroide)
- **R** — [Reanálisis](#reanálisis) · [Región nacional del ONI](#región-nacional-del-oni) · [Rezago de ERA5 (~5 días)](#rezago-de-era5-5-días) · [Rezago de publicación del ONI](#rezago-de-publicación-del-oni)
- **S** — [Semana incompleta (DIAS_MINIMOS_SEMANA)](#semana-incompleta-dias_minimos_semana)
- **T** — [Teleconexión](#teleconexión) · [Temperatura del aire a 2 m (temp_max, temp_min, temp_media)](#temperatura-del-aire-a-2-m-temp_max-temp_min-temp_media) · [Temporada móvil de tres meses (SEAS)](#temporada-móvil-de-tres-meses-seas)
- **V** — [Variable ambiental](#variable-ambiental) · [Volcado climático versionado](#volcado-climático-versionado)
- **Z** — [Zona horaria (America/El_Salvador)](#zona-horaria-americael_salvador)

<!-- INDICE:FIN -->

## 1. Fuentes y modelos climáticos

### Variable ambiental

**Qué es.** Magnitud del entorno medida o modelada por semana y lugar (temperatura, humedad, lluvia, índice oceánico).

**En el proyecto.** Se guardan en `variables_ambientales` con una fila por `(región, año, semana_epi, variable, fuente)`. La columna `variable` es **texto libre sin `CHECK`**: un error de escritura crea una segunda serie en silencio, así que se usan exactamente ocho cadenas: `temp_max`, `temp_min`, `temp_media`, `humedad_relativa_media`, `punto_rocio`, `precipitation_sum`, `precipitation_hours` y `oni_anom`. Ver [`variables_ambientales`](07-base-de-datos-y-migraciones.md#variables_ambientales).

### Open-Meteo

**Qué es.** API meteorológica gratuita y alojada que sirve datos de varios modelos (`open-meteo.com`).

**En el proyecto.** Fuente de las siete variables climáticas por departamento, mediante el archivo histórico `archive-api.open-meteo.com/v1/archive`. El self-hosting se evaluó y se descartó: recortar la grilla global no está documentado de forma usable y el volumen excede el hardware del proyecto. Sus datos tienen licencia **CC BY 4.0** y, según los términos de uso del sitio, obligan a citar la fuente y a indicar que el dato se modificó (aquí se agrupa por departamento y semana epidemiológica).

**Dónde.** `backend/ingestion/cargar_clima.py`, [ADR 0006](../adr/0006-atribucion-fuente-climatica-era5.md), [ADR 0018](../adr/0018-extension-capa-climatica-presente.md).

**Ojo.** El uso es **no comercial**: los términos listan investigación pública en instituciones públicas y contenido educativo, y el perfil del proyecto (institución educativa pública, feria técnica, sin publicidad ni suscripciones) entra en ese uso.

### Reanálisis

**Qué es.** Reconstrucción histórica del estado de la atmósfera que combina un modelo con observaciones y se recalcula con una versión fija del modelo, de modo que la serie es homogénea en el tiempo.

**En el proyecto.** ERA5 y ERA5-Land son reanálisis; por eso sirven para comparar años entre sí. En cambio, ECMWF IFS es un archivo de corridas operativas de pronóstico y cambia con cada versión del modelo.

### ERA5

**Qué es.** Reanálisis global del ECMWF (Centro Europeo de Predicción Meteorológica a Plazo Medio; expansión de uso general). Resolución de 0,25° (unos 25 km), desde 1940.

**En el proyecto.** Es el modelo de las dos variables de **precipitación** (`precipitation_sum` y `precipitation_hours`), con la fuente `open_meteo_era5`. Al ser tan grueso, los departamentos La Libertad y San Salvador **comparten celda** (13,75; −89,25) y reciben el mismo dato de lluvia. Se aceptó deliberadamente porque siguen distinguiéndose por las otras cinco variables y por la elevación.

### ERA5-Land

**Qué es.** Reanálisis derivado de ERA5 a resolución de 0,1° (unos 11 km), desde 1950, centrado en condiciones de superficie: temperatura, humedad, suelo.

**En el proyecto.** Modelo de **temperatura máxima, mínima y media, humedad relativa media y punto de rocío** (fuente `open_meteo_era5_land`). Sus 14 puntos caen en 14 celdas distintas y, con `models=era5_land`, las coordenadas devueltas son múltiplos de 0,1°.

**Ojo.** **No modela precipitación** en absoluto, ni horaria ni diaria: la devuelve `null`. Tampoco sirve evapotranspiración (ET₀), que queda fuera de alcance.

### `best_match` y `era5_seamless` (prohibidos)

**Qué es.** Modos de Open-Meteo que combinan modelos según la variable.

**En el proyecto.** Están **prohibidos**: entregan datos, pero sin poder nombrar qué grilla produjo cada variable, y el informe necesita poder decirlo. Los modelos se piden siempre de forma explícita (`models=era5_land` o `models=era5`). Con `best_match` la coordenada devuelta no es el centro de una grilla cruda (para La Libertad salió 13,813708; −89,33826), porque interpola entre modelos.

### ECMWF IFS

**Qué es.** Sistema integrado de pronóstico del ECMWF; en la API histórica de Open-Meteo, un archivo de sus corridas operativas (9 km, desde 2017).

**En el proyecto.** Se evaluó para precipitación y se **descartó** el 2026-08-07: sirve datos reales en toda la ventana, pero es un producto que se actualiza con cada versión operativa del modelo. Como la ventana atraviesa varias actualizaciones, la lluvia de 2018 y la de 2023 pueden no ser homogéneas entre sí, y esa heterogeneidad contaminaría la comparación entre años, que es el eje sobre el que el modelo se entrena y se evalúa.

### Heterogeneidad temporal entre versiones de un modelo

**Qué es.** Cambio de comportamiento de una serie por una actualización del modelo que la produce, no por el clima real.

**En el proyecto.** Es el argumento que decidió a favor de ERA5 (grueso pero fijo) y en contra de IFS (fino pero cambiante) para la precipitación. La documentación de Open-Meteo recomienda usar solo ERA5 o ERA5-Land para estudios de décadas. Un predictor heterogéneo puede introducir una tendencia espuria: más o menos «lluvia» solo porque cambió el modelo.

### Modelo explícito por variable

**Qué es.** Regla de fijar, para cada variable, un único modelo nombrado.

**En el proyecto.**

| Variables | Modelo | Resolución | Fuente en el catálogo |
|---|---|---|---|
| Temperatura máx, mín y media; humedad relativa media; punto de rocío | `era5_land` | 0,1° | `open_meteo_era5_land` |
| Precipitación acumulada y horas de precipitación | `era5` | 0,25° | `open_meteo_era5` |

Cada variable tiene un modelo fijo y único (nunca los dos para la misma variable); por eso bastó una segunda fila de catálogo y no una columna `modelo` en la tabla de hechos ([ADR 0006](../adr/0006-atribucion-fuente-climatica-era5.md)).

### Celda de grilla y resolución espacial

**Qué es.** Un modelo devuelve el valor de una celda de una malla; la resolución es el tamaño de esa celda.

**En el proyecto.** La API responde con el **centro de la celda** que usó, no con la coordenada pedida. Ese centro depende del modelo y de la resolución, y **no se persiste** ([ADR 0003](../adr/0003-coordenadas-regiones-columnas.md)): se usa en el momento para comprobar la distancia contra el punto solicitado. En `era5_land` esa distancia va de 1,8 a 6,5 km (mínimo Chalatenango, máximo La Libertad), coherente con una celda de 9 a 11 km.

### Colapso de celda

**Qué es.** Que dos lugares distintos reciban el mismo dato porque caen en la misma celda.

**En el proyecto.** Ocurre con `era5` entre `SV-LI` (La Libertad) y `SV-SS` (San Salvador), que reciben la misma precipitación (3,3 mm el 2023-07-15). Se acepta y se declara: lo que se pierde es distinguirlos por lluvia, no distinguirlos en general.

### Petición multiubicación

**Qué es.** Una sola llamada a la API con varias coordenadas.

**En el proyecto.** Cada modelo se llama **una vez para los 14 departamentos** (latitudes y longitudes separadas por coma, en el orden de `centroides_departamentos.csv`). La respuesta es una lista con un objeto por ubicación, en el mismo orden, cada uno con su propio `latitude`, `longitude`, `elevation`, `utc_offset_seconds` y `daily`. No hay envoltorio común.

### Cuota y límites de uso gratuito

**Qué es.** Límites de la capa gratuita de Open-Meteo.

**En el proyecto.** 600 llamadas por minuto, 5.000 por hora, 10.000 por día y 300.000 por mes. El peor caso estimado de la descarga histórica completa (unas 2.200 llamadas ponderadas) deja mucho margen frente al techo diario de 10.000. Lo que sí se dispara es el límite por minuto.

### Límite de tasa (429) y reintento

**Qué es.** Respuesta `429 Too Many Requests` cuando se superan las peticiones permitidas por minuto.

**En el proyecto.** `cargar_clima.py` reintenta hasta 5 veces con espera creciente (15 s, 30 s, 45 s…) antes de fallar.

### Zona horaria (`America/El_Salvador`)

**Qué es.** Parámetro `timezone` de la API que fija la hora local de los agregados diarios.

**En el proyecto.** Se fija `timezone=America/El_Salvador`. `utc_offset_seconds` vale `-21600` (GMT−6) en todas las ubicaciones, lo que confirma que los agregados diarios caen en hora local y no en UTC. Es necesario para que los rezagos semanales no queden corridos un día.

## 2. Variables

### Temperatura del aire a 2 m (`temp_max`, `temp_min`, `temp_media`)

**Qué es.** Temperatura del aire a 2 metros sobre el suelo, la altura estándar de las estaciones. Máxima, mínima y media diarias.

**En el proyecto.** Vienen de `temperature_2m_max`, `temperature_2m_min` y `temperature_2m_mean` de `era5_land`, en °C. La media semanal de `temp_media` alimenta el `Iv` (M1), donde la temperatura entra por la función de Brière ([`f_T`](05-modulos-descriptivos-y-alertas.md#f_t-brière-temperatura)).

### Humedad relativa media (`humedad_relativa_media`)

**Qué es.** Porcentaje de vapor de agua en el aire respecto al máximo que cabría a esa temperatura.

**En el proyecto.** Viene de `relative_humidity_2m_mean` de `era5_land`. Entra al `Iv` con la rampa lineal [`f_H`](05-modulos-descriptivos-y-alertas.md#f_h-rampa-humedad), estimación propia del equipo que penaliza la humedad por debajo del 50 %.

### Punto de rocío (`punto_rocio`)

**Qué es.** Temperatura a la que el aire se satura de vapor y el agua empieza a condensarse; mide cuánto vapor hay, sin depender de la temperatura del momento.

**En el proyecto.** Viene de `dew_point_2m_mean` de `era5_land`. Se carga y se conserva como variable, pero el `Iv` no lo usa: sus tres insumos son `temp_media`, `precipitation_sum` y `humedad_relativa_media`.

### Precipitación acumulada (`precipitation_sum`)

**Qué es.** Lluvia total del período, en milímetros.

**En el proyecto.** Viene de `era5` y se **suma** por semana. Entra al `Iv` como precipitación acumulada a dos semanas (la semana y la anterior, sin envolver entre años) mediante la logística [`f_R`](05-modulos-descriptivos-y-alertas.md#f_r-logística-precipitación).

### Horas de precipitación (`precipitation_hours`)

**Qué es.** Número de horas con lluvia en el día.

**En el proyecto.** Viene de `era5` y se suma por semana. Es la variable afectada por la trampa del [cero falso](#cero-falso-de-la-precipitación). No entra al `Iv`.

### Evapotranspiración de referencia (ET₀)

**Qué es.** Agua que evaporaría una superficie de referencia; se nombra `et0_fao_evapotranspiration` en la API.

**En el proyecto.** Fuera de alcance por decisión ya tomada: no se prueba ni se reporta. Solo se menciona porque `era5_land` la devuelve `null` y porque está listada únicamente para ERA5.

### Anomalía ONI (`oni_anom`)

**Qué es.** Variable que guarda la anomalía mensual del índice oceánico ONI.

**En el proyecto.** Se almacena bajo la región nacional `SV`, no por departamento. Ver [ONI](#oni-oceanic-niño-index).

## 3. Agregación, rezago y calidad

### Agregación diaria a semana epidemiológica

**Qué es.** Convertir los valores diarios en un valor por semana epidemiológica.

**En el proyecto.** La API no tiene agregación semanal nativa, así que el pipeline construye la semana con el calendario MMWR de `semanas_epidemiologicas`: **media** para las variables de estado (`temp_max`, `temp_min`, `temp_media`, `humedad_relativa_media`, `punto_rocio`) y **suma** para las acumulativas (`precipitation_sum`, `precipitation_hours`). Es una elección de implementación, no una regla cerrada más allá de «sumar o promediar diarios»; la variante «máximo semanal del máximo diario» quedó anotada como alternativa por si hiciera falta.

**Dónde.** `AGREGACION` y `agregar_a_semana` en `backend/ingestion/cargar_clima.py`.

### Semana incompleta (`DIAS_MINIMOS_SEMANA`)

**Qué es.** Umbral de días observados por debajo del cual una semana no se agrega.

**En el proyecto.** `DIAS_MINIMOS_SEMANA = 5`: una semana con menos de 5 días se **descarta** en vez de agregarse. Motivo: en una variable de suma como la precipitación, una semana parcial es indistinguible aguas abajo de una semana genuinamente seca, y alimentaría el `Iv`, la anomalía y la línea base leave-one-out. Por eso la cola del año en curso no entra hasta completarse.

### Rezago de ERA5 (~5 días)

**Qué es.** El reanálisis ERA5 no cubre los últimos días: llega con un atraso de unos cinco.

**En el proyecto.** El archivo no acepta fechas futuras y `fecha_fin` se recorta a hoy. Esos días salen nulos y **no se imputan** ni se cierran con el modelo de pronóstico (cerrar ese tramo sería nowcasting, otra tarea; [ADR 0018](../adr/0018-extension-capa-climatica-presente.md), punto C).

**Ojo.** No confundir con el [rezago de publicación del ONI](#rezago-de-publicación-del-oni) ni con el [rezago epidemiológico](01-epidemiologia-y-vigilancia.md#rezago-epidemiológico-lag).

### Cero falso de la precipitación

**Qué es.** Un `0,0` que parece una observación real pero es un valor por defecto de un modelo que no tiene el dato.

**En el proyecto.** Bajo `era5_land`, un día de lluvia real (2023-06-05, 12,5 mm según IFS) devuelve `precipitation_sum = null` (correcto) pero `precipitation_hours = 0.0` (cero fabricado). Un pipeline que usara ese campo registraría «cero lluvia» todos los días, de forma silenciosa e incorrecta. `precipitation_sum` dice la verdad; `precipitation_hours` no.

### Guarda de precipitación

**Qué es.** Regla del pipeline contra el cero falso.

**En el proyecto.** Antes de aceptar cualquier valor de precipitación de una respuesta se comprueba que `precipitation_sum` del mismo día no sea `null`; si lo es, se descarta también `precipitation_hours` de ese día, sin importar su valor. Nunca se infiere «sin lluvia» de un `precipitation_hours` en cero sin haber confirmado `precipitation_sum`. Vale para cualquier modelo. Se mantiene aunque hoy la precipitación se pida siempre a `era5`, porque protege contra un cambio futuro de configuración, que es justo cuando el cero falso reaparecería sin que nadie lo busque.

**Dónde.** `extraer_puntos_diarios` en `backend/ingestion/cargar_clima.py`, `backend/ingestion/clima/hallazgos_precipitacion_modelo.md`.

### Capa climática hasta el presente

**Qué es.** La ampliación de M1 y M2 más allá de 2023 ([ADR 0018](../adr/0018-extension-capa-climatica-presente.md), 2026-09-08).

**En el proyecto.** `ANIOS_CLIMA` crece hasta el año calendario en curso (`list(range(2014, date.today().year + 1))`), duplicada a mano en `backend/api/idoneidad.py` y `backend/ingestion/validar_leadtime_idoneidad.py`; un test de fórmulas duplicadas falla si se desincronizan. El clima **va por delante de los casos**: llega al año en curso mientras la serie nacional de dengue termina en 2024 y la departamental en 2023. No es un desajuste a corregir: M1 y M2 describen condición biofísica y pueden ser actuales, y todo lo que depende de casos queda anclado a la última semana con casos observados.

**Ojo.** Al entrar años nuevos al pool leave-one-out, la mediana y la σ de las semanas 2018–2023 ya publicadas **se recalculan y se mueven**; queda escrito en el ADR y no es un efecto colateral silencioso. Quien compare capturas anteriores con las actuales verá diferencias numéricas.

### Clima congelado (2024 y anteriores)

**Qué es.** Decisión de no volver a escribir el clima ya cargado hasta 2024.

**En el proyecto.** Una recarga local movió 70 filas de 2024 SE01 (cambios menores de 0,1 °C o unos 2 puntos de humedad, probable conteo de días en la semana de borde) y se restauraron a los valores anteriores, porque movían la `firma_previa_sha256` de la Vía 3, que es un artefacto congelado ([Manifiesto congelado](04-estadistica-y-modelado.md#manifiesto-congelado-y-firma-previa)). El clima ≤ 2024 quedó congelado byte a byte.

### Volcado climático versionado

**Qué es.** Qué parte del clima trae un clon limpio.

**En el proyecto.** El volcado versionado incluye 2025 completo y 2026 hasta la SE 35 (issue #124, 2026-09-10). Antes, un `git clone` fresco o Render no veían clima posterior a 2024 ([ADR 0018](../adr/0018-extension-capa-climatica-presente.md) dejó ese gap escrito). Ver [Volcado versionado](07-base-de-datos-y-migraciones.md#volcado-versionado-seed).

**Ojo.** La Biblioteca 04 cita «35.868 filas, 2018–2024» (7 variables × 14 departamentos), una cifra de una etapa anterior: la primera versión del volcado traía 56.924 filas de `variables_ambientales` (clima 2014–2024 más el ONI).

### Condición biofísica frente a incidencia

**Qué es.** Distinción de honestidad entre lo que describe el clima y lo que describen los casos.

**En el proyecto.** `AVISO_HONESTIDAD_IDONEIDAD` y el panel de auditoría separan **condición biofísica** (clima, hasta el presente) de **incidencia** y de **presión epidemiológica** (M3, casos MINSAL). Un valor de M1 o M2 describe el clima ya observado; no anticipa un ascenso de casos ([Coexistencia temporal](01-epidemiologia-y-vigilancia.md#coexistencia-temporal-no-es-causalidad)).

### Clima rezagado

**Qué es.** Usar como predictor el clima de semanas anteriores al momento que se quiere explicar.

**En el proyecto.** La decisión cerrada del 2026-08-09 fijó que **el predictor del clasificador era únicamente clima rezagado** y que los casos solo servían para construir la etiqueta. Se probaron ventanas de rezago de 4, 8 y 12 semanas sin mover el recall de la clase «alto». En el nowcast, en cambio, entra la media de 4 semanas de cada variable climática agregada a nivel nacional ([ADR 0020](../adr/0020-nowcast-corto-plazo.md)).

## 4. Geografía para el clima

### Punto representativo (frente a centroide)

**Qué es.** Un punto que garantiza estar dentro del polígono, a diferencia del centroide aritmético, que en una forma cóncava puede caer fuera.

**En el proyecto.** Cada departamento se consulta en Open-Meteo con su **punto representativo**, calculado con `shapely.representative_point()` sobre el polígono de mayor área (si la geometría es `MultiPolygon`). La Unión y Usulután tienen islas en el golfo de Fonseca y la bahía de Jiquilisco, donde un centroide aritmético se correría hacia el mar. La tabla de 14 filas está en `backend/ingestion/geo/centroides_departamentos.csv`.

**Dónde.** `backend/ingestion/compute_centroides.py`; `shapely` es dependencia de desarrollo, no entra a la imagen de producción.

### Centroide (`centroide_lat`, `centroide_lon`)

**Qué es.** Nombre de las columnas de `regiones` donde se guarda el punto representativo.

**En el proyecto.** Aunque se llamen «centroide», guardan el punto representativo, no el centroide aritmético. Son propiedad geométrica del departamento y sobreviven a un cambio de proveedor climático ([ADR 0003](../adr/0003-coordenadas-regiones-columnas.md)). Las columnas existían desde 2026-08-07 pero ninguna carga las poblaba: recibieron datos reales el 2026-08-10, como efecto colateral de `cargar_clima.py`, que ya necesita latitud y longitud para llamar a la API. Ver [`regiones`](07-base-de-datos-y-migraciones.md#regiones).

**Ojo.** Lo que **no** se guarda es el centro de celda que devuelve la API: es detalle de fuente y modelo, no identidad de la región.

### Caja geográfica (validación de coordenadas)

**Qué es.** Rango de latitud y longitud dentro del cual debe caer cualquier punto de El Salvador.

**En el proyecto.** `compute_centroides.py` acepta solo latitudes entre 13,1 y 14,5 y longitudes entre −90,2 y −87,6. Existe porque GeoJSON guarda `[longitud, latitud]` y Open-Meteo espera latitud y longitud por separado: invertir el orden no produce error, produce clima válido de otro punto del planeta.

### Elevación (`elevacion_m`)

**Qué es.** Altura del punto representativo según el modelo digital de elevación (DEM) interno de Open-Meteo.

**En el proyecto.** No depende del modelo climático pedido (`era5_land` y `best_match` devolvieron los mismos 530 m para el mismo punto), así que una sola llamada la puebla junto con cualquier variable. `regiones.elevacion_m` lleva un `COMMENT ON COLUMN` con la salvedad.

**Ojo.** **No es una medición topográfica del departamento**: es la altura que el DEM le asigna a ese punto. Un departamento con relieve variado no tiene una sola altura real; cambiar de proveedor podría cambiar el valor sin que cambie nada del departamento.

## 5. El Niño, La Niña y el índice ONI

### El Niño y La Niña

**Qué es.** Fases opuestas de una oscilación climática de escala oceánica y continental en el Pacífico ecuatorial: El Niño (calentamiento anómalo del mar) y La Niña (enfriamiento). El conjunto se conoce como ENSO (El Niño–Oscilación del Sur; sigla de uso general, el repositorio no la usa).

**En el proyecto.** La literatura epidemiológica los asocia con brotes de dengue en Centroamérica: condiciones más cálidas y secas durante El Niño favorecen la cría de *Aedes aegypti* en agua almacenada ([ADR 0008](../adr/0008-fuente-noaa-oni.md)). Es una señal de otra naturaleza que el clima superficial local, y por diseño Open-Meteo no puede darla.

### ONI (Oceanic Niño Index)

**Qué es.** Índice del Climate Prediction Center (CPC) de NOAA: anomalía de la temperatura superficial del mar en la región Niño 3.4 (la nota de la migración `0006` la nombra así), promediada en ventanas móviles de tres meses. El umbral de ±0,5 °C que separa las fases El Niño y La Niña es de uso general; el repositorio no lo fija.

**En el proyecto.** Archivo de texto plano público, sin credenciales ni límite de tasa documentado y con formato estable: `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`, con columnas `SEAS`, `YR`, `TOTAL` y `ANOM`. Se guarda `ANOM` (la anomalía, que es la que se usa para clasificar la fase) y no `TOTAL`, bajo la variable `oni_anom` y la fuente `noaa_oni`.

**Dónde.** [ADR 0008](../adr/0008-fuente-noaa-oni.md), migración `0006`, `backend/ingestion/cargar_oni.py`.

### Temporada móvil de tres meses (`SEAS`)

**Qué es.** Código de tres letras (DJF, JFM, FMA, MAM, AMJ, MJJ, JJA, JAS, ASO, SON, OND, NDJ) con las iniciales de los tres meses de la ventana.

**En el proyecto.** Cada código representa el **mes central** de la ventana, y `YR` es el año calendario de ese mes central: `DJF 1950` es diciembre de 1949, enero y febrero de 1950, y su `YR` es 1950. El loader lo traduce con el diccionario `MES_CENTRAL` (DJF → 1, JFM → 2, …, NDJ → 12).

### Asignación mensual a semanal (no interpolación)

**Qué es.** El ONI es mensual y la tabla de hechos es semanal.

**En el proyecto.** El mismo valor mensual se aplica a **cada semana epidemiológica cuyo `fecha_inicio` cae en ese mes calendario**. Es una asignación de resolución declarada como tal: el ONI es un índice de **estado** (nivel oceánico), no un conteo acumulable, y por eso no es una interpolación ni un reparto. El contraste es el caso de OpenDengue Admin1, donde fraccionar un acumulado sí fabricaría dato ([ADR 0008](../adr/0008-fuente-noaa-oni.md), punto C).

### Rezago de publicación del ONI

**Qué es.** NOAA publica el ONI con aproximadamente un mes de retraso respecto al mes en curso.

**En el proyecto.** Es relevante solo si alguna vez se usa para inferencia «en vivo». En el nowcast entra con el valor del origen `t`.

### Región nacional del ONI

**Qué es.** El ONI no tiene resolución subnacional.

**En el proyecto.** Se almacena una sola vez bajo `regiones.codigo = 'SV'` (`nivel_admin = 0`); repetirlo 14 veces no aportaría información. Cobertura cargada: 574 filas semanales, alineadas con la serie nacional de dengue (2014–2024).

### Estado del ONI como predictor

**Qué es.** Qué papel juega el ONI en los modelos.

**En el proyecto.** El [ADR 0008](../adr/0008-fuente-noaa-oni.md) lo aceptó como predictor *experimental*. En el clasificador retirado no ayudó (no mejoró 2019 ni 2022); hoy es una de las features del nowcast de dengue, con el valor del origen `t` ([ADR 0020](../adr/0020-nowcast-corto-plazo.md)). La Biblioteca lo describe como contexto descriptivo: tener la serie en la base no autoriza a leerla como palanca de brote.

### Teleconexión

**Qué es.** Relación entre fenómenos climáticos separados por grandes distancias (aquí, el Pacífico ecuatorial y el clima de El Salvador).

**En el proyecto.** La Biblioteca describe el ONI como «índice público de teleconexión». Complementa, no reemplaza, el clima superficial local.
