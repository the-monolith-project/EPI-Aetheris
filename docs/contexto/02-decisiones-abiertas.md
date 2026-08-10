# EPI-Aetheris — Decisiones abiertas

> A diferencia de `01-decisiones-cerradas.md`, nada de esto está resuelto. No invente una respuesta para avanzar una tarea que dependa de un punto de aquí — pregunte al usuario. Cuando algo de esta lista se cierre, muévalo a `01-decisiones-cerradas.md` y bórrelo de aquí; no lo deje duplicado en ambos.

## A. Parámetros de la etiqueta de riesgo alto/medio/bajo

El método ya está cerrado (canal endémico por percentil — ver `01-decisiones-cerradas.md`). Pendientes de una corrida real de distribución de clases, no de más discusión de escritorio:

- Variable base: probables o confirmados.
- Cortes de percentil, ventana de semanas vecinas, esquema de años base (retrospectivo vs. ventana expansiva).
- Piso de suficiencia de la línea base y tratamiento de celdas degeneradas (`Q3 = 0`). **Corrección aritmética pendiente de incorporar, no aplicada todavía:** el piso cerrado (12 observaciones + 3 de 4 años base) asume implícitamente una ventana de semanas vecinas que nunca se fijó — con 4 años base y resolución de una sola semana el máximo posible es 4 observaciones por celda, así que el piso tal como está escrito es matemáticamente inalcanzable. Con ventana ±1 (3 semanas × 4 años = 12) se vuelve alcanzable exactamente en el borde. Reformular como "12 observaciones contando ventana de vecinas de ±1 mínimo" cuando se cierre este punto — no adoptar ±1 como definitivo todavía, solo como el mínimo aritméticamente viable. **Corrección 2026-08-10: la ventana ±1 NO estaba implementada en `corrida_distribucion.py`** (afirmación anterior de este documento, incorrecta) — esa corrida compara semana exacta entre años, sin vecinas (máximo 4 observaciones, nunca 12), que es justamente por lo que casi todas las celdas cayeron bajo el piso declarado. La ventana ±1 sí se implementó, esta vez de verdad, en `corrida_canal_endemico_nacional.py` (ver `03-fuentes-de-datos.md`, corrida nacional).
- Techo de columnas del conjunto de features.
- **Insumo ya disponible, ahora también a nivel nacional (2026-08-10):** corrida de distribución de clases sobre la serie departamental (`data/interim/corrida_distribucion/`, no versionada) — ver punto H para el veredicto y sus límites. La misma corrida sobre la serie **nacional** de OpenDengue (`backend/ingestion/corrida_canal_endemico_nacional.py`, resumen en `docs/corrida-canal-endemico-nacional.md`) ya corrió: 96,2 % de celdas cumplen el piso de suficiencia con ventana ±1 (muy por encima del 87,9–92,8 % departamental), y ambos esquemas candidatos (P75/P90, P50/P75) separan 2019/2022 del resto sin clases vacías — pero **no deciden el corte por sí solos**: P50/P75 marca "alto" hasta una semana de 2021 (año bajo), señal de sobre-etiquetado a vigilar. Sigue siendo decisión del coordinador.

## B. Atribución de fuente climática en el catálogo

`fuentes_datos` solo tiene `open_meteo_era5_land`. Con dos modelos en juego (`era5_land` para temp/humedad/rocío, `era5` para precipitación), las filas de precipitación quedarían atribuidas a un modelo que no las produjo — rompe la trazabilidad. Dos salidas: segunda entrada de catálogo por modelo, o registrar el modelo por fila en `variables_ambientales` (más flexible, más caro). Es cambio de esquema: exige ADR antes de la migración. **Confirmado que la migración `0002` (ADR 0003 + ADR 0004) no lo incluyó** — no asumir que quedó resuelto de rebote.

## C. Mecanismo de migraciones

`docker-entrypoint-initdb.d` corre todo `db/migrations/` una sola vez, sobre volumen vacío, en orden alfabético — no hay tracking de qué se aplicó ya sobre una base en ejecución. Numerar los archivos es una convención, no un sistema de migraciones. Dos salidas: documentar "volumen limpio + reingesta" como flujo de trabajo aceptado, o implementar un runner mínimo con tabla `schema_migrations`. Elegir antes de que existan datos costosos de reconstruir. ADR 0004 tocó el esquema y **no resolvió esto** — no asumir que un cambio de esquema arregla el mecanismo de migraciones de rebote.

## D. Estrategia de pruebas del pipeline de ingesta

No hay `pytest` para el pipeline de boletines (sí existe una prueba para el catálogo de departamentos vs. mapa). El informe compromete un "protocolo de pruebas" y el rol del coordinador dentro del trío de programación es revisión/QA. Insumo ya disponible: tres boletines inspeccionados manualmente con cifras conocidas (`SE232018`, `SE522019_v2`, `SE522023`), usables como casos de referencia sin subir los PDF.

## E. Ubicación de la exclusión de 2020

Definida como ventana de *entrenamiento* (capa de modelado). Si se implementa como filtro en la capa de *ingesta*, se estrecha el estatuto: ingesta debe ser fiel a la fuente y agnóstica al uso posterior. En la práctica solo afecta filas de borde (ej. un "confirmado" de SE52/2020 reportado en el boletín de SE01/2021). No filtrar 2020 durante trabajo de ingesta sin este criterio fijado explícitamente.

## F. Uso de casos recientes como predictor / operación en semanas actuales

Ya cerrado que el predictor del modelo es climático únicamente (ver `01-decisiones-cerradas.md`) — pero de ahí se deriva que el sistema no tiene forma de verificar en vivo lo que predice, porque no hay fuente departamental automatizable después de 2023/2024. Cómo se comunica esa limitación (dashboard, informe) sigue sin definir.

## G. Dónde vive la salida del modelo

Computado on-demand vs. persistido en una tabla — el esquema hoy no tiene tabla de predicciones. No inventar una sin que se decida.

## H. Semántica acumulada de Probable/Confirmado MINSAL y suficiencia de la variable objetivo departamental

**Estado actualizado 2026-08-09 — ya no bloquea el MVP completo, sigue bloqueando la activación del clasificador departamental.** Verificado empíricamente (ver `03-fuentes-de-datos.md`, trampa 8): los valores de Probable/Confirmado en la tabla departamental de cada boletín son **acumulados desde SE1**, no incidencia de esa semana, en ambas familias. La corrida exploratoria (`backend/ingestion/corrida_distribucion.py`, 264 PDF, verificación 4/4 contra casos conocidos) validó una metodología de desacumulación por diferencias entre boletines consecutivos y produjo el primer veredicto real sobre la señal departamental — ver el detalle completo en `03-fuentes-de-datos.md`, trampa 8. Con esa evidencia como insumo, el coordinador tomó la **decisión de pivote "Opción C"** (ver `01-decisiones-cerradas.md`): la primera entrega usa la serie **nacional** de OpenDengue como variable objetivo del clasificador, no la departamental — esto es lo que desbloquea el MVP. El punto H sigue abierto para lo que la Opción C no resuelve:

- **Activación del clasificador departamental como segunda pasada.** Condicionada a un reconteo del criterio "pierde >20 % de filas" (hoy inflado por un artefacto de la corrida — ver trampa 8) después de rescatar los 6 boletines problemáticos de 2019 (3 tablas-imagen + 3 con mismatch numérico residual, ver `03-fuentes-de-datos.md` trampa 11). Ese rescate es la tarea pendiente, no la escritura del clasificador en sí — si `probable` sobrevive el reconteo, el clasificador departamental se agrega sobre la misma infraestructura del nacional (cambiar el filtro de región, no reescribir código).
- **Promover `corrida_distribucion.py` (exploratorio, no escribe a Postgres) al parser de producción** (`backend/ingestion/minsal/parser.py`, que sigue sin existir), incorporando la semántica acumulada explícita en la capa intermedia, el validador de doble convención de Otros países (trampa 3), y el estado nuevo de bitácora para `sin_texto_extraible` (distinto de `revision_manual` y de `ausencia_esperada`). Cambia qué representa una fila de `casos_epidemiologicos` — probablemente amerita su propio ADR.
- **Migración `0002`-siguiente de `boletines_procesados`** (ver punto B más abajo en pendientes): el estado `sin_texto_extraible` que la corrida ya evidenció como necesario no está en el `CHECK` actual (`pendiente`, `ok`, `revision_manual`, `error`, `ausencia_esperada`) — requiere ADR antes de escribirse.

**Fuera de este punto, ya no es una pregunta abierta:** la cifra departamental de dengue seguirá siendo delgada frente a la carga real (los sospechosos nunca se desagregan por departamento en estos boletines) — eso ya no bloquea nada porque la variable objetivo de la primera entrega no depende de ella.

## Pendientes operativos conocidos (no son decisiones, pero sin avance registrado)

- ~~Carga de la serie nacional de OpenDengue a Postgres~~ — **hecho (2026-08-09, tarjeta 11).** `backend/ingestion/cargar_opendengue.py`, 365 filas 2018–2024, `clasificacion='total'` (ADR 0005, migración `0003`). Ver `01-decisiones-cerradas.md` para el detalle y la verificación contra cifras conocidas.
- Parser de boletines MINSAL de producción (`backend/ingestion/minsal/parser.py`): **no existe todavía.** El código de descarga sí existe (`backend/ingestion/minsal/common.py` + scripts por año), y ahora también un script exploratorio validado que resuelve la desacumulación (`backend/ingestion/corrida_distribucion.py`, ver punto H) — falta promoverlo a parser real con pruebas `pytest`, lo cual ya no bloquea el MVP (Opción C lo saca de la ruta crítica) pero sigue siendo trabajo pendiente para la capa descriptiva del mapa y el eventual clasificador departamental.
- Rescate de los 6 boletines problemáticos de 2019 (3 tablas-imagen + 3 con mismatch numérico) — requiere decisión previa del coordinador antes de agregar `pytesseract` como dependencia (toca el stack cerrado). Ver `03-fuentes-de-datos.md`, trampa 11.
- CI y *pre-commit*: mapeados, no implementados.
- `web/src/styles/tokens.css` y su configuración de Tailwind: convención acordada, no versionada.
- Para el estado real de qué archivos existen en el repo en un momento dado, verificar directamente (`git ls-files`, explorar `backend/`, `docs/adr/`, `db/migrations/`) en vez de confiar en una lista aquí — ese inventario se desactualiza de inmediato (ver el historial en `CHANGELOG.md`: la migración `0002` estuvo documentada como "no existe todavía" en el mismo commit que la creó).
