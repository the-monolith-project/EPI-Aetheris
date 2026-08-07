# Hallazgos — llamada de prueba a Open-Meteo (tarjeta 20)

**La decisión de qué modelo sirve `precipitation_sum` se investigó a
fondo y se documentó en `hallazgos_precipitacion_modelo.md`** — este
archivo se deja tal cual quedó (histórico de cómo se descubrió el
problema), no se reescribe.

Evidencia cruda en este mismo directorio. Coordenadas pedidas desde
`backend/ingestion/geo/centroides_departamentos.csv` (punto representativo
por departamento, no centroide aritmético — ver `compute_centroides.py`).

## 1. Cuáles de las 8 variables existen de verdad como agregado diario bajo `era5_land`

| Variable | `era5_land`, diario | `era5_land`, horario | `best_match`, diario |
|---|---|---|---|
| `temperature_2m_max` | Sí | Sí | Sí |
| `temperature_2m_min` | Sí | Sí | Sí |
| `temperature_2m_mean` | Sí | Sí | Sí |
| `precipitation_sum` | **`null` en las 7 filas** | **`null` en las 24 h probadas** | Sí (valores reales) |
| `precipitation_hours` | "Sí" pero engañoso — ver abajo | — | Sí (valores reales) |
| `relative_humidity_2m_mean` | Sí | — | Sí |
| `dew_point_2m_mean` | Sí | — | Sí |
| `et0_fao_evapotranspiration` | **`null` en las 7 filas** | **`null` en las 24 h probadas** | Sí (valores reales) |

**Hallazgo, no anticipado en la tarjeta:** `precipitation_sum` y
`et0_fao_evapotranspiration` no vienen `null` por faltar el agregado diario
(que se resolvería promediando horas, como preveía la tarjeta) — vienen
`null` porque **ERA5-Land no modela precipitación en absoluto**, ni a
escala horaria ni diaria. Confirmado dos veces: empíricamente (`null` en
todas las fechas/ubicaciones probadas, incluyendo `evidencia_openmeteo_era5_land_hourly_precipitacion_null.json`)
y contra la documentación oficial de Open-Meteo: *"ERA5-Land focuses on
surface conditions like temperature, humidity, soil temperature, and soil
moisture"* — no incluye precipitación, lluvia, nieve ni radiación solar.
`et0_fao_evapotranspiration` está listado solo para `ERA5` (25 km), no
para `ERA5-Land`. No hay hora que promediar: el dato no existe en este
modelo, en ningún grano temporal.

**Trampa adicional, no anticipada:** `precipitation_hours` bajo `era5_land`
no viene `null` — viene `0.0` en los 7 días, para las dos ubicaciones
probadas. Parece un dato real ("cero horas de lluvia"), pero comparado
contra `best_match` en el mismo rango (`evidencia_openmeteo_best_match.json`,
que sí devuelve `precipitation_hours` con valores 2–15 h y `precipitation_sum`
correlacionado) queda claro que el `0.0` de `era5_land` es un valor por
defecto cuando la variable base no existe en el modelo, no una observación.
Si el pipeline llegara a usar `precipitation_hours` de `era5_land` sin
cruzarlo contra `precipitation_sum`, registraría "cero lluvia" todos los
días de forma silenciosa e incorrecta.

**Para obtener `precipitation_sum` y `et0_fao_evapotranspiration` con datos
reales hay que usar `models=best_match`** (o no fijar `models`, que
por defecto ya es `best_match`) — nunca `era5_land` explícito.

## 2. Grilla fina vs. gruesa

Confirmado con las 14 ubicaciones (`evidencia_openmeteo_14departamentos_era5_land.json`,
tabla completa en `tabla_14_departamentos_openmeteo.csv`): con
`models=era5_land`, las 14 coordenadas devueltas caen exactamente en
múltiplos de 0,1° (ej. `13.9, -89.9`; `13.5, -88.7`) — grilla fina de
ERA5-Land, tal como fija la decisión cerrada de julio. **No salieron
múltiplos de 0,25.**

Con `models=best_match`, la coordenada devuelta para el mismo punto
(La Libertad) fue `13.813708, -89.33826` — ni múltiplo de 0,1 ni de 0,25.
`best_match` no devuelve el centro de una grilla cruda: interpola/combina
entre modelos según la variable, así que el discriminador de "múltiplos de
0,25" no aplica directamente a `best_match` — el punto de comparación real
es que, para precipitación y et0, el modelo que efectivamente responde
bajo `best_match` no es `era5_land` (que no los soporta), es otra cosa
(probablemente ERA5 de 25 km o IFS, sin confirmar cuál exactamente).

## 3. Forma de la respuesta con varias ubicaciones

Arreglo de objetos, un objeto por ubicación, en el mismo orden que se
pidieron `latitude`/`longitude` (confirmado con 2 y con 14 ubicaciones).
Cada objeto trae sus propios `latitude`, `longitude`, `elevation`,
`utc_offset_seconds`, `daily_units`, `daily` — no hay un envoltorio común.

## 4. Distancia entre lo pedido y lo devuelto (`era5_land`)

Calculada con Haversine para las 14 departamentos, en
`tabla_14_departamentos_openmeteo.csv`: mínimo 1,825 km (Chalatenango),
máximo 6,485 km (La Libertad). Todas dentro de lo esperable para una
celda de ~9–11 km (la diagonal media de una celda de ese tamaño ronda los
6–8 km) — nada fuera de rango.

## 5. `elevation` y `utc_offset_seconds`

Capturados para los 14 departamentos en `tabla_14_departamentos_openmeteo.csv`.
`utc_offset_seconds` es `-21600` (GMT-6, hora de El Salvador) en todas las
ubicaciones probadas — confirma que la agregación diaria está en hora
local cuando se fija `timezone=America/El_Salvador`, no en UTC. La
elevación no depende del modelo pedido: la misma llamada con `era5_land` y
con `best_match` devolvió la misma elevación (530 m) para el mismo punto,
así que una sola llamada basta para poblarla junto con cualquier variable.

## Cuota (paso 4)

Cerrado por aritmética, sin necesidad de medir: en el peor caso (que el
costo se multiplique por ubicación en vez de compartirse), la descarga
histórica completa para los 14 departamentos ronda las ~2.200 llamadas
ponderadas contra el límite diario de 10.000 de la capa gratuita de
Open-Meteo. Sobra margen de sobra; no es un riesgo operativo para este
proyecto. Deja cerrada la decisión abierta sobre viabilidad de cuota.

## Lo que falta decidir (no lo decido yo, toca un estatuto)

La decisión cerrada de julio dice *"Model is fixed to `era5_land` /
`best_match`"*, tratándolos como una sola cosa. Este hallazgo muestra que
no lo son: `era5_land` no puede servir precipitación ni et0 bajo ninguna
circunstancia, así que para esas dos variables el pipeline
necesariamente va a usar `best_match` (o algún modelo explícito
distinto de `era5_land`) — y `best_match` no ofrece la garantía de
resolución de 9–11 km que fue la razón original para descartar el ERA5
plano de 25 km. El chequeo de "múltiplos de 0,25" que se pidió como gatillo
de alarma no se disparó (la grilla de `era5_land` sí es fina), pero el
problema de fondo que ese chequeo buscaba detectar — que la decisión de
modelo no se esté cumpliendo en la práctica para todas las variables — sí
apareció, por una vía distinta a la prevista.

No elegí una salida (llamada separada con `best_match` solo para
precipitación/et0, aceptar el modelo que `best_match` use para esas dos
variables sin confirmar su resolución, u otra) porque es exactamente el
tipo de decisión que la tarjeta pide escalar, no inventar.
