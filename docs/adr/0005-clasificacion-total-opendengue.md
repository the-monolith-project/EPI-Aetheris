# 0005 - Tercer valor de `clasificacion`: `total`, para la serie nacional de OpenDengue

**Estado:** Aceptado

## Contexto

`casos_epidemiologicos.clasificacion` (`db/migrations/0001_init_schema.sql`) tiene `CHECK (clasificacion IN ('probable', 'confirmado'))`, diseñado alrededor de la tabla departamental de MINSAL, donde cada fila del boletín efectivamente reporta esas dos series por separado.

Al preparar la carga de la serie nacional de OpenDengue (tarjeta 11 del tablero; ver `docs/contexto/01-decisiones-cerradas.md`, pivote "Opción C" — esta serie es ahora la variable objetivo del primer clasificador, no solo material narrativo) se confirmó, filtrando el CSV real (`backend/ingestion/data/raw/opendengue/opendengue_el_salvador_v1_3.csv`) a resolución nacional/semanal (`S_res = 'Admin0'`, `T_res = 'Week'`, 574 filas), que **la columna `case_definition_standardised` vale `'Total'` en el 100 % de esas filas**. OpenDengue no publica un desglose probable/confirmado para El Salvador a esta resolución — entrega un conteo agregado bajo una definición de caso propia, distinta de las dos series de laboratorio que MINSAL sí separa.

Insertar ese total bajo `clasificacion = 'confirmado'` o `'probable'` etiquetaría el dato con una definición que no es la real: `'confirmado'` en el resto del esquema significa específicamente confirmación de laboratorio (vía MINSAL), una cifra órdenes de magnitud menor que el total agregado de OpenDengue. Eso viola el principio de no fabricar/tergiversar datos (no negociable del proyecto) y corrompería silenciosamente cualquier consulta futura que agregue `clasificacion = 'confirmado'` esperando solo casos de laboratorio.

## Decisión

Se elimina la restricción `casos_epidemiologicos_clasificacion_check` (nombre confirmado en vivo sobre Postgres 15 desechable, cargando `0001` + `0002` sin modificar, siguiendo el mismo criterio de verificación que el ADR 0004) y se recrea con un tercer valor:

```sql
CHECK (clasificacion IN ('probable', 'confirmado', 'total'))
```

El nombre `'total'` se toma verbatim del propio valor que trae el campo `case_definition_standardised` del CSV de OpenDengue, en vez de inventar un término nuevo — mismo criterio que el ADR 0004 usó para `ausencia_esperada`.

`'total'` se puebla únicamente para filas con `fuente_id` correspondiente a `opendengue_v1_3` y nivel nacional (`region_id` de `regiones.codigo = 'SV'`). Nada en el esquema fuerza esa correspondencia — es disciplina del loader (`backend/ingestion/cargar_opendengue.py`), no una garantía de la base de datos, igual que ya ocurre con `version` en `boletines_procesados` (ADR 0004).

Se aprovecha la misma migración para corregir el texto de `fuentes_datos.notas` de la fila `opendengue_v1_3`, que todavía decía "uso narrativo/exploratorio" — desactualizado desde el pivote "Opción C". Es una corrección de dato (`UPDATE`), no un cambio de estructura, así que no exige su propio ADR, pero se deja registrada aquí para que quede trazable por qué cambió en esta migración.

## Consecuencias

* Positivo: la serie nacional de OpenDengue se puede cargar sin fingir que es una de las dos series de laboratorio de MINSAL — preserva la definición real de la fuente.
* Positivo: desbloquea la tarjeta 11 (carga de OpenDengue) sin comprometer la fidelidad de la variable objetivo del primer clasificador.
* Positivo: `UNIQUE (region_id, tipo_evento_id, anio, semana_epi, clasificacion, fuente_id)` sigue funcionando sin cambios — `'total'` es solo un valor más de esa columna, no rompe la llave.
* Negativo: cualquier consulta o capa de modelado que sume `casos_epidemiologicos.conteo` agrupando solo por `(region, anio, semana_epi)` sin filtrar por `clasificacion` mezclaría ahora tres definiciones de caso distintas (probable, confirmado, total) bajo una sola suma — quien consuma la tabla debe filtrar explícitamente por `clasificacion` según qué serie necesita, no asumir que sumar todo es seguro.
* Negativo: si la base de datos ya tiene datos cargados al momento de aplicar esta migración, hace falta `docker compose down -v` y reingesta completa — el proyecto sigue sin un runner de migraciones (punto C de `docs/contexto/02-decisiones-abiertas.md`, no resuelto por este ADR).
* Neutral: no resuelve el mecanismo de migraciones en sí, ni la atribución de fuente climática (`fuentes_datos`, punto B de la misma lista) — ambos siguen abiertos, tal como estaban.

## Migración

`db/migrations/0003_clasificacion_total_opendengue.sql` — aplica el cambio del `CHECK` descrito arriba y la corrección de `fuentes_datos.notas` para `opendengue_v1_3`. Verificada en secuencia (`0001` → `0002` → `0003`) sobre Postgres 15 desechable antes de aceptarse.
