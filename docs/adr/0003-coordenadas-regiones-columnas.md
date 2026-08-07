# 0003 - Coordenadas de `regiones` como columnas nuevas, no una tabla aparte

**Estado:** Aceptado

## Contexto

`regiones` no tiene columnas de latitud/longitud (decisión abierta anotada en el proyecto). Sin coordenada por departamento no se puede consultar Open-Meteo, que recibe latitud/longitud por ubicación, no un identificador de región.

Se calculó un punto representativo por departamento (`backend/ingestion/compute_centroides.py`, sobre el GeoJSON ya horneado con `codigo` — no el GeoJSON fuente, porque `codigo` es la llave con la que se va a guardar cada coordenada) y se probó contra Open-Meteo (`archive-api.open-meteo.com/v1/archive`, modelo `era5_land`) para los 14 departamentos en una sola llamada. Evidencia en `backend/ingestion/clima/`. La API devuelve, para cada ubicación pedida, tres cosas conceptualmente distintas:

1. La coordenada del punto representativo que se pidió (calculada una vez, no cambia si cambia el proveedor de clima).
2. La elevación del punto (metadato geográfico general — Open-Meteo la deriva de un DEM, no es un output del modelo climático en sí).
3. El centro de la celda de grilla que el modelo usó para responder (depende del modelo y de la resolución; distinto para `era5_land` que para `best_match`, confirmado empíricamente — ver evidencia).

Dos formas de persistir esto:

| Opción | A favor | En contra |
|---|---|---|
| Columnas nuevas en `regiones` | Simple, una migración chica | Mezcla la identidad del departamento con un detalle de una fuente y un modelo concretos |
| Tabla aparte que relacione región, fuente y modelo con su punto | Sobrevive a cambiar de modelo o agregar otra fuente ambiental | Una tabla más y una unión más |

## Decisión

**Columnas nuevas en `regiones`: `centroide_lat`, `centroide_lon`, `elevacion_m`.** Pero acotado: estas tres columnas guardan únicamente los ítems 1 y 2 de arriba — el punto representativo (propiedad geométrica del departamento, calculada del GeoJSON, no de ningún proveedor climático) y su elevación (propiedad física del lugar, no del modelo). **El ítem 3 — el centro de celda que devuelve cada llamada — no se persiste en `regiones`, ni en ninguna tabla nueva por ahora.** Se usa en el momento de la llamada (para el chequeo de distancia contra el centroide, como el que ya se hizo aquí) y, si algún día hace falta auditar qué celda respondió qué dato, es un candidato natural para un campo en `variables_ambientales` o una nota en `fuentes_datos` — no antes de que haga falta.

Esto responde directamente la objeción de "mezclar identidad con detalle de fuente": lo que se guarda en `regiones` no es un detalle de Open-Meteo ni de `era5_land` — es una coordenada y una elevación que seguirían siendo válidas aunque el proyecto cambiara de proveedor climático mañana. Lo que sí es específico de fuente/modelo (el centro de celda) deliberadamente se deja fuera de `regiones`.

La tabla separada (opción B) sigue siendo la opción correcta el día que el proyecto tenga más de una fuente ambiental activa a la vez, o necesite guardar históricamente qué celda sirvió cada observación — ninguna de las dos cosas es cierta hoy (fuente climática única, cerrada; ver decisiones cerradas del proyecto). No se construye esa tabla por adelantado.

## Consecuencias

* Positivo: la migración es chica (3 columnas `NUMERIC` nullable en `regiones`) y no exige tocar el resto del esquema.
* Positivo: las columnas son legítimamente parte de la identidad del departamento (dónde está, qué tan alto), no un detalle de implementación de Open-Meteo — sobreviven un cambio de proveedor climático sin migración.
* Negativo: si el proyecto llegara a necesitar más de una fuente ambiental simultánea, o auditar la celda exacta por observación histórica, hay que añadir esa pieza aparte (tabla o columna en `variables_ambientales`) — no es gratis, pero tampoco exige deshacer nada de esto.
* Neutral: `elevacion_m` se puebla con el valor que devuelve Open-Meteo al consultar cualquier variable para ese punto (no depende de qué variable se pida ni de qué modelo — confirmado: la misma llamada con `era5_land` y con `best_match` devolvió la misma elevación, 530 m, para el mismo punto), así que no hace falta una llamada dedicada solo para elevación.
* **Pendiente, fuera del alcance de este ADR:** de qué modelo(s) exactamente se toma cada una de las 8 variables ambientales no está resuelto — ver hallazgo en `backend/ingestion/clima/`. Afecta el diseño del fetch de `variables_ambientales`, no la persistencia de coordenadas que resuelve este ADR.

## Migración

No incluida en este ADR — según el proceso del proyecto, el ADR se escribe y acepta antes de escribir la migración, no junto con ella.
