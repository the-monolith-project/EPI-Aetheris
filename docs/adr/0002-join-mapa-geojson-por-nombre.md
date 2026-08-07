# 0002 - Unión entre `regiones` y el GeoJSON de límites departamentales por nombre normalizado, no por `shapeISO`

**Estado:** Aceptado

## Contexto

El frontend (Astro + Leaflet) necesita pintar los 14 departamentos de El Salvador coloreados según el riesgo calculado por región, lo que exige una llave de unión entre `regiones.codigo` (ej. `SV-AH`) y las features del GeoJSON de límites administrativos.

La premisa inicial era que el GeoJSON de ADM1 (geoBoundaries, fuente OSM vía osm-boundaries.com, `boundaryID` `SLV-ADM1-98794003`) traería un código ISO 3166-2 (`shapeISO`, ej. `SV-AH`) directamente comparable con `regiones.codigo`, evitando así normalización de texto.

Se descargó el GeoJSON (`gjDownloadURL` / `simplifiedGeometryGeoJSON` desde `https://www.geoboundaries.org/api/current/gbOpen/SLV/ADM1/`) y se inspeccionaron sus propiedades:

- `shapeISO` viene vacío (`""`) en las 14 features. La fuente subyacente (osm-boundaries.com) no trae ese dato relleno para este boundary.
- `shapeName` sí identifica cada departamento, pero de forma inconsistente: la mayoría lleva el prefijo `"Departamento de "` (ej. `"Departamento de Ahuachapán"`), mientras que dos no lo llevan (`"La Libertad"`, `"San Vicente"`).

Por lo tanto la premisa **no se sostiene**: no hay código ISO utilizable, y la unión debe hacerse por nombre.

## Decisión

La unión por nombre normalizado se hace **una sola vez, en tiempo de construcción, en Python** — no en el frontend. `backend/ingestion/build_geo_departamentos.py` lee el GeoJSON fuente desde `backend/ingestion/geo/slv-adm1-source.geojson` — **commiteado tal cual se descargó, sin tocar** — normaliza cada `shapeName` (quitar prefijo `"Departamento de "` case-insensitive, `unicodedata.normalize('NFD', s)` sin marcas diacríticas, minúsculas, espacios colapsados) y lo une contra el catálogo de 14 pares nombre→`codigo` (espejo de `db/migrations/0001_init_schema.sql`, sección 5). El script escribe `codigo` (ej. `SV-AH`) como propiedad nueva en cada feature y sobreescribe `web/public/geo/slv-adm1.geojson` con el resultado — solo si la unión da exactamente 14 a 14; si no, el script termina con código de salida distinto de cero y no toca el archivo de salida.

El script **no descarga nada de la red**: el archivo fuente pineado a `9469f09` (mismo commit fijado en este ADR) ya está en el repositorio, así que el build no depende de que geoboundaries.org esté en línea, y una actualización futura del boundary requiere reemplazar `slv-adm1-source.geojson` a mano y de forma explícita (comando documentado en la cabecera del script) — nunca ocurre implícitamente en un `git pull` o en CI.

El frontend (Leaflet) por lo tanto **no contiene ninguna lógica de normalización de texto**: une contra el GeoJSON ya enriquecido por igualdad estricta sobre `properties.codigo`. Esto evita reimplementar la misma normalización en dos lenguajes (Python en el parser MINSAL, TypeScript en el frontend) y que diverjan en un caso borde sin que nadie lo note — la unión ambigua se resuelve una única vez, no en cada render.

El catálogo de 14 pares hardcodeado en el script tiene su propia guarda contra desactualizarse respecto a la migración: `backend/ingestion/tests/test_build_geo_departamentos.py` parsea los `INSERT INTO regiones` de `0001_init_schema.sql` y compara el resultado contra `DEPARTAMENTOS` — no lee de Postgres (el build no depende de tener la base levantada), lee el mismo archivo `.sql` que ya es la fuente de verdad. Falla si diverge un nombre, un código, o el conteo de 14.

Verificado 14 a 14, sin sobrantes de ningún lado, el `2026-08-05`.

## Consecuencias

* Positivo: no se requiere ningún cambio de esquema ni tocar `regiones.codigo`; la normalización de texto vive en un único lugar (el script de construcción), no duplicada entre el parser MINSAL y el frontend.
* Positivo: la verificación 14-a-14 es parte del propio build — si `slv-adm1-source.geojson` se reemplaza por una versión con nombres distintos, el script falla de forma ruidosa (`sys.exit(1)`) en vez de dejar un departamento sin pintar en el mapa en silencio. Probado deliberadamente (quitando un departamento del catálogo) para confirmar que la guarda realmente dispara.
* Positivo: el build no tiene dependencia de red ni de Postgres — un tercero puede clonar el repo y regenerar `web/public/geo/slv-adm1.geojson` sin nada más levantado.
* Negativo: la unión por nombre sigue siendo más frágil que un código real; el catálogo de 14 pares está hardcodeado en el script como espejo de la migración — mitigado por el test de arriba, pero sigue siendo edición manual, no lectura automática de una única fuente.
* Negativo: `codigo` queda embebido en un artefacto derivado (`web/public/geo/slv-adm1.geojson`) que no es el dato crudo descargado; regenerar el mapa requiere volver a correr el script, no editar el GeoJSON a mano.
* Negativo: actualizar el boundary a una versión más nueva de geoBoundaries es un paso manual (reemplazar `slv-adm1-source.geojson`, repetir la verificación 14-a-14, actualizar este ADR) — si alguien reemplaza el archivo sin seguir ese proceso, nada fuerza la actualización del ADR ni del commit pineado en el comentario del script.
* Neutral: se usó la versión `simplifiedGeometryGeoJSON` (~117 KB sin `codigo`, ~101 KB tras compactar el JSON) en vez de la versión completa `gjDownloadURL` (~1.2 MB) — la simplificada es suficiente para Leaflet a la escala de departamento y carga más rápido en el navegador.
* **Atribución pendiente, y más abierta de lo que parece a primera vista:** este archivo redistribuye datos derivados de geoBoundaries gbOpen (CC-BY 4.0, exige atribución). El campo `boundaryLicense` de la API para este boundary específico además reporta "Creative Commons Attribution-ShareAlike 2.0" (fuente subyacente: osm-boundaries.com) — distinto del CC-BY 4.0 genérico del proyecto geoBoundaries. Pendiente sin resolver: los datos de OpenStreetMap se distribuyen bajo ODbL (licencia de base de datos con cláusula compartir-igual sobre la base de datos, no sobre el contenido como tal), no bajo una licencia de contenido tipo CC; `slv-adm1.geojson` con `codigo` horneado es una base de datos derivada, lo que puede exigir algo más que una línea de atribución simple. Confirmar la licencia declarada por osm-boundaries.com específicamente (no asumir que replica la de OSM) antes de redactar el texto de atribución del dashboard (tarjeta de atribuciones, tablero "Tablero general" > "Generales"). El proyecto en sí es GPL-3.0, lo que no exime de esta obligación — son capas de licencia distintas (código del proyecto vs. datos redistribuidos).
