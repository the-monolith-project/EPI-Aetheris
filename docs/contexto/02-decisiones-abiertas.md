# EPI-Aetheris — Decisiones abiertas

> A diferencia de `01-decisiones-cerradas.md`, nada de esto está resuelto. No invente una respuesta para avanzar una tarea que dependa de un punto de aquí — pregunte al usuario. Cuando algo de esta lista se cierre, muévalo a `01-decisiones-cerradas.md` y bórrelo de aquí; no lo deje duplicado en ambos.

## A. Parámetros de la etiqueta de riesgo alto/medio/bajo

El método ya está cerrado (canal endémico por percentil — ver `01-decisiones-cerradas.md`). Pendientes de una corrida real de distribución de clases, no de más discusión de escritorio:

- Variable base: probables o confirmados.
- Cortes de percentil, ventana de semanas vecinas, esquema de años base (retrospectivo vs. ventana expansiva).
- Piso de suficiencia de la línea base y tratamiento de celdas degeneradas (`Q3 = 0`).
- Techo de columnas del conjunto de features.

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

## Pendientes operativos conocidos (no son decisiones, pero sin avance registrado)

- Parser de boletines MINSAL: no existe todavía, solo el código de descarga (`backend/ingestion/minsal/common.py` + scripts por año).
- CI y *pre-commit*: mapeados, no implementados.
- `web/src/styles/tokens.css` y su configuración de Tailwind: convención acordada, no versionada.
- Para el estado real de qué archivos existen en el repo en un momento dado, verificar directamente (`git ls-files`, explorar `backend/`, `docs/adr/`, `db/migrations/`) en vez de confiar en una lista aquí — ese inventario se desactualiza de inmediato (ver el historial en `CHANGELOG.md`: la migración `0002` estuvo documentada como "no existe todavía" en el mismo commit que la creó).
