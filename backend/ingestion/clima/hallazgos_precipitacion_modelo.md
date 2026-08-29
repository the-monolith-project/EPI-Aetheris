# Hallazgos — de qué modelo sale la precipitación (escalado desde tarjeta 20)

Continúa `hallazgos_openmeteo.md`, que dejó abierto de qué modelo tomar
`precipitation_sum` porque `era5_land` no la sirve. ET₀ queda fuera de
alcance por decisión ya tomada — no se prueba ni se reporta aquí.
Evidencia cruda: `prueba1_ecmwf_ifs/`, `prueba2_14deptos_*.json`,
`prueba3_*.json`, `prueba4_era5_land_5variables.json`.

## Decisión del coordinador (2026-08-07)

**IFS queda descartado para el MVP.** El hallazgo no anticipado (más abajo)
es el que decide, no las pruebas 1–4 por sí solas: la heterogeneidad
temporal entre versiones del modelo es un error peor que el colapso
espacial de `era5`, porque contamina la comparación *entre años*, que es
justo el eje sobre el que el modelo se entrena y se evalúa. Un efecto de
año que no es meteorológico (sino un cambio de versión operativa de IFS)
haría que la validación retrospectiva por año retenido terminara midiendo
un artefacto del dataset, no capacidad predictiva real. Detenerse a
reportar esto en vez de concluir "IFS resuelve todo" fue la actuación
correcta.

**Configuración cerrada, modelos siempre explícitos — nunca `best_match`
ni `era5_seamless`** (ambos entregan lo mismo que las llamadas de abajo,
pero sin poder nombrar qué grilla produjo cada variable, y el informe
necesita poder decirlo):

- `era5_land` → `temperature_2m_max`, `temperature_2m_min`,
  `temperature_2m_mean`, `relative_humidity_2m_mean`, `dew_point_2m_mean`.
  Resolución 0,1°.
- `era5` → `precipitation_sum`, `precipitation_hours`. Resolución 0,25°.
- ET₀ fuera de alcance — ya confirmado, no se reabre.

**Se acepta el colapso de celda entre La Libertad y San Salvador** (Prueba
2): ambos departamentos siguen siendo distinguibles por las otras cinco
variables (0,1°, 14 celdas distintas) y por la elevación. Lo que se pierde
es distinguirlos por lluvia, no distinguirlos en general.

**La regla de guarda de la Prueba 3 se mantiene**, aunque con esta
configuración `precipitation_sum` ya se le pide siempre al modelo que sí
la sirve (`era5`), no a `era5_land`. Protege contra un cambio futuro de
configuración — es exactamente el momento en que ese cero falso
reaparecería sin que nadie lo esté buscando.

**Pendiente, fuera de este documento:** con dos modelos en juego, el
catálogo `fuentes_datos` va a terminar atribuyendo filas de precipitación
a un modelo que no las produjo (ahora mismo solo contempla
`open_meteo_era5_land`). Es cambio de esquema y necesita su propio ADR
antes de cualquier migración — no se escribe aquí ni ahora.

---

## Prueba 1 — ¿IFS cubre toda la ventana 2018–2023?

Una coordenada (La Libertad, 13.744564/-89.361267), 6 fechas de temporada
lluviosa repartidas por la ventana de entrenamiento (2020 excluido, como
ya está cerrado):

| Fecha | precipitation_sum (mm) | precipitation_hours (h) |
|---|---|---|
| 2018-06-05 | 3.1 | 5.0 |
| 2019-07-15 | 4.6 | 5.0 |
| 2021-07-15 | 0.1 | 1.0 |
| 2022-07-15 | 0.3 | 3.0 |
| 2023-07-15 | 2.4 | 9.0 |
| 2023-09-25 | 7.8 | 5.0 |

Las 6 fechas devolvieron valores reales, no nulos. `2021-07-15` es bajo
(0,1 mm) pero no cero ni nulo — un valor bajo es plausible en un solo día
de temporada lluviosa, no indica cobertura parcial. **IFS cubre las 6
fechas de prueba en toda la ventana.**

Dato adicional, no pedido por la prueba: las 6 llamadas devolvieron el
mismo centro de celda (`13.813708, -89.33826`) — idéntico al que había
devuelto `best_match` para el mismo punto en la ronda anterior. Confirma
que `best_match` está tomando IFS como fuente de precipitación aquí, sin
que hiciera falta volver a llamar `best_match` (no se usó en ninguna
prueba de este documento, como se pidió).

## Prueba 2 — Resolución efectiva por modelo (14 departamentos, 2023-07-15)

| Modelo | Celdas distintas | Departamentos que comparten celda | Distancia pedido→celda (min–max) |
|---|---|---|---|
| `era5_land` | 14 de 14 | ninguno | 1,83–6,48 km |
| `era5` | **13 de 14** | **SV-LI (La Libertad) y SV-SS (San Salvador) comparten la celda (13.75, -89.25)** — mismo valor de precipitación para ambos (3,3 mm) | 3,45–14,89 km |
| `ecmwf_ifs` | 14 de 14 | ninguno | 1,65–8,08 km |

Con `era5` (0,25°), La Libertad y San Salvador —dos departamentos
distintos, con dinámica de dengue propia— reciben exactamente el mismo
dato de lluvia. Es justo el problema que la decisión de julio quiso evitar
al descartar el ERA5 plano para departamentos pequeños; queda confirmado
con datos, no solo con el argumento de área que se usó entonces.

`ecmwf_ifs` no cae en múltiplos de 0,1° ni 0,25° — su espaciado entre
celdas vecinas midió 8,93 km en el par más cercano de los 14 puntos, lo
que es consistente con la resolución de 9 km que la propia documentación
de Open-Meteo declara para IFS (ver Prueba 2b más abajo), pero no es una
grilla lat/lon uniforme como las otras dos — no se puede describir con un
único número de grados.

## Prueba 3 — El cero falso, confirmado con precisión de campo

Mismo punto y mismo día (La Libertad, 2023-06-05, día de lluvia real —
12,5 mm bajo IFS):

| Modelo | `precipitation_sum` | `precipitation_hours` |
|---|---|---|
| `era5_land` | `null` (campo presente, valor nulo) | `0.0` (no nulo — **cero falso**) |
| `ecmwf_ifs` | `12.50` | `11.0` |

`precipitation_sum` dice la verdad bajo `era5_land`: viene `null`, nunca
un cero engañoso. `precipitation_hours` no — devuelve `0.0` como si fuera
una observación real de "cero horas de lluvia" cuando en realidad el
modelo no tiene el dato en absoluto.

**Regla de guarda para el pipeline:** antes de aceptar cualquier valor de
precipitación de una llamada, verificar que `precipitation_sum` de esa
misma respuesta no sea `null`. Si lo es, rechazar también
`precipitation_hours` de esa respuesta, sin importar qué valor traiga —
no es información, es un valor por defecto del modelo. Nunca inferir
"sin lluvia" de un `precipitation_hours` en cero sin haber confirmado
`precipitation_sum` primero. Esto es válido para cualquier modelo, no solo
`era5_land` — es la forma correcta de no confiar en que un campo no
soportado llegue como `null` de forma consistente.

## Prueba 4 — Las cinco variables restantes bajo `era5_land`

Confirmado con valores reales, sin nulos, en 7 días de prueba
(2023-06-01 a 2023-06-07): `temperature_2m_max`, `temperature_2m_min`,
`temperature_2m_mean`, `relative_humidity_2m_mean`, `dew_point_2m_mean`.
Ninguna faltó. `era5_land` sigue siendo la fuente correcta para estas 5.

## Hallazgo no anticipado por ninguna de las 4 pruebas — me detengo aquí, no lo resuelvo

Ninguna de las 4 pruebas pedía verificar **qué es** `ecmwf_ifs` dentro de
la API histórica. Lo revisé porque la Prueba 1 mostró que sirve
precipitación real en toda la ventana, y antes de que eso se leyera como
"entonces úsese IFS para precipitación" quise confirmar qué tipo de
producto es. Según la documentación de Open-Meteo:

> *"ECMWF IFS ... simulation runs daily at 0z, 6z, 12z and 18z, employing
> the most up-to-date version of IFS."*

Es decir: **`ecmwf_ifs` no es un reanálisis estático como ERA5/ERA5-Land —
es un archivo de corridas operativas de pronóstico, que se actualiza con
cada versión operativa del modelo IFS.** Y la propia documentación trae
una advertencia directamente aplicable a este proyecto:

> *"when studying climate change over decades, it is advisable to
> exclusively utilise ERA5 or ERA5-Land. This choice ensures data
> consistency and prevents unintentional alterations that could arise
> from the adoption of different weather model upgrades."*

La ventana de entrenamiento (2018, 2019, 2021, 2022, 2023) atraviesa
varias actualizaciones operativas de IFS. Eso significa que la
precipitación de `ecmwf_ifs` en 2018 y en 2023 puede no ser homogénea
entre sí — no por error de la prueba, sino porque son literalmente
versiones distintas del modelo respondiendo — mientras que la temperatura,
humedad y punto de rocío de `era5_land` sí vienen de un producto de
reanálisis fijo y consistente en toda la ventana. Un predictor
heterogéneo en el tiempo puede introducir una tendencia espuria (más o
menos "lluvia" simplemente porque cambió el modelo, no el clima) en un
clasificador que compara años entre sí.

No decido si esto descarta `ecmwf_ifs`, si se acepta el riesgo, o si hay
una alternativa que no se probó aquí (`era5` tiene el mismo problema de
colapso de celdas que ya se documentó, y ambos modelos "puros" — `era5` y
`ecmwf_ifs` — son opciones con una desventaja distinta cada uno). Es la
misma clase de decisión que la tarjeta pidió no resolver por mi cuenta,
solo que apareció un nivel más abajo de lo previsto.

## Entregable — resumen

- Evidencia cruda: guardada en este directorio (`prueba1_ecmwf_ifs/`,
  `prueba2_14deptos_*.json`, `prueba3_*.json`, `prueba4_era5_land_5variables.json`).
- Tabla comparativa de resolución por modelo: Prueba 2, arriba.
- Regla de guarda: escrita arriba, en Prueba 3.
- Recomendación de qué modelo sirve qué variable, a qué resolución —
  **cerrada por el coordinador, ver "Decisión del coordinador" arriba:**
  - `temperature_2m_max/min/mean`, `relative_humidity_2m_mean`,
    `dew_point_2m_mean` → `era5_land`, 0,1° (~9–11 km).
  - `precipitation_sum`/`precipitation_hours` → `era5`, 0,25°. `ecmwf_ifs`
    quedó descartado por heterogeneidad temporal entre versiones del
    modelo, un riesgo más grave que el colapso de celda de `era5` porque
    contamina la comparación entre años.
  - ET₀ fuera de alcance, no vuelve a evaluarse.
  - Nunca `best_match` ni `era5_seamless` — el informe necesita poder
    nombrar qué grilla produjo cada variable.
