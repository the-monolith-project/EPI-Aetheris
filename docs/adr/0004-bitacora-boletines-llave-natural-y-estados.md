# 0004 - Bitácora de boletines: nombre de archivo como llave natural, estado de ausencia esperada y trazabilidad hacia casos

**Estado:** Aceptado

## Contexto

`boletines_procesados` (`db/migrations/0001_init_schema.sql`) se diseñó antes de que existiera el parser. Con el parser en construcción aparecen cuatro carencias que el DDL cerrado no cubre:

**1. No hay restricción `UNIQUE`.** Nada impide que reejecutar el parser sobre el mismo boletín inserte una fila de bitácora nueva en vez de actualizar la existente. La candidata obvia como llave, `url_origen`, es una cadena **reconstruida a partir del nombre de archivo** en el momento de la descarga (ver `backend/ingestion/minsal/common.py` y la ruta directa documentada en `docs/contexto/03-fuentes-de-datos.md`) — no es un dato observado del boletín en sí. Usarla como llave natural haría depender la idempotencia de la bitácora de que esa reconstrucción siga siendo correcta, lo que mezcla dos responsabilidades distintas: identificar qué se procesó, y recordar de dónde se descargó.

El nombre de archivo, en cambio, es la identidad real de lo procesado: es el dato que el parser efectivamente abre, verificable en disco sin acceso a red. Con la salvedad ya documentada en el maestro (Sección 5.1): las republicaciones corregidas (`_v2`, `_v3`, hasta `_v4` en el mismo año) tienen nombre de archivo distinto entre sí, así que cada una genera su propia fila de bitácora — la llave natural por nombre de archivo no colapsa versiones entre sí, y el orden de precedencia entre ellas (qué versión es la vigente para alimentar `casos_epidemiologicos`) tiene que quedar explícito en una columna consultable, no depender de en qué orden el sistema de archivos entregue los nombres al recorrer el directorio.

**2. El `CHECK` de `estado` no contempla un boletín que existe pero no trae tabla departamental.** Los valores permitidos hoy son `pendiente`, `ok`, `revision_manual` y `error`. Un boletín de vacaciones (~3 por año: Semana Santa, Fiestas Agostinas, Fin de Año) o uno que cubre dos semanas combinadas en un solo archivo (confirmado en SE01+SE02 de 2018) no es ninguno de los cuatro: el parser lo abre correctamente, no falla, y no hay nada que reconciliar contra un total nacional porque no hay tabla departamental que sumar. No es un error del parser ni un caso que requiera que alguien revise el boletín a mano — es una ausencia esperada y ya documentada empíricamente (maestro, Sección 5.1). Registrarlo como `error` infla artificialmente la tasa de fallos de la ingesta, que el informe cita como métrica de calidad; registrarlo como `revision_manual` sugiere que alguien tiene que intervenir, cuando no hay nada que revisar.

**3. `semana_archivo` es `NOT NULL`.** Un boletín que cubre dos semanas no tiene una sola semana que registrar en esa columna — forzar un valor ahí sería fabricar un dato para satisfacer una restricción, exactamente lo que el maestro prohíbe como principio (Sección 4). Además, el maestro deja constancia de que no todos los boletines de vacaciones tienen "nombres libres" con un patrón `SE\d+` reconocible (Sección 5.1) — la columna necesita poder quedar vacía también en ese caso, sin que eso bloquee insertar la fila de bitácora.

**4. No hay trazabilidad de boletín a fila de casos.** `casos_epidemiologicos.fuente_id` identifica la fuente (`minsal_pdf`), no el archivo concreto. Si un boletín resulta mal parseado después de haberse marcado `ok`, hoy no hay forma de averiguar qué filas de `casos_epidemiologicos` produjo, para poder revisarlas o revertirlas.

**Contexto de oportunidad.** Mientras `db` no tenga datos reales cargados, el mecanismo de migraciones actual (`docker-entrypoint-initdb.d`, que corre los archivos de `db/migrations/` una sola vez, en orden alfabético, sobre volumen vacío — ver maestro Sección 7.3) hace que cualquier cambio de esquema cueste lo mismo: `docker compose down -v` y reingesta desde cero, hoy vacía de costo real porque no hay nada que reingerir todavía. En cuanto el parser cargue los 264 boletines, ese mismo cambio pasa a costar una reingesta completa. El ADR 0003 (coordenadas de `regiones`) ya está aceptado pero su migración no se ha escrito; conviene resolverlo en la misma ventana que este cambio, mientras siga siendo gratis. La atribución de fuente climática (maestro, Sección 10.1 punto J) está en la misma cola pero **no tiene ADR propio todavía** — por la regla de la Sección 7.4 (ADR antes que migración, sin excepción), no puede empaquetarse en la misma migración hasta que exista y sea aceptado. Este ADR no lo resuelve.

**Nota de exactitud sobre el mecanismo de `CHECK`:** en PostgreSQL un `CHECK` no se modifica in place, se elimina y se vuelve a crear. El nombre de la restricción es autogenerado por el motor, no una convención fijada por este proyecto. Se verificó en vivo (Postgres 15 desechable, cargando `0001_init_schema.sql` sin modificar) en vez de asumirlo: la restricción sobre `estado` se llama `boletines_procesados_estado_check`.

**Nota de exactitud sobre "migraciones":** numerar los archivos de `db/migrations/` no constituye un sistema de migraciones. Como todos los archivos de esa carpeta corren juntos, una sola vez, sobre volumen limpio, lo que existe hoy es un esquema repartido en varios archivos con una convención de orden, no un mecanismo que sepa qué se aplicó ya sobre una base en ejecución. Ese problema queda abierto en el maestro (Sección 10.1, punto E) y este ADR no lo resuelve — solo agrega un archivo más dentro de la misma convención.

## Decisión

**A. Llave natural: `nombre_archivo`, no `url_origen`.**

Se agrega la columna `nombre_archivo TEXT NOT NULL UNIQUE`. El parser hace `INSERT ... ON CONFLICT (nombre_archivo) DO UPDATE` — reprocesar el mismo archivo actualiza su fila de bitácora en vez de duplicarla. `url_origen` se conserva como metadato descriptivo (sigue siendo útil para auditar de dónde se intentó descargar), pero deja de ser candidata a llave: no se le agrega restricción de unicidad.

Para hacer explícito el orden de precedencia entre republicaciones, se agrega `version SMALLINT NOT NULL DEFAULT 1`, poblada por el parser al leer el sufijo del nombre de archivo (`_v2` → `2`, `_v3` → `3`, sin sufijo → `1`) — nunca inferida de la fecha de modificación del archivo ni del orden de recorrido del directorio. Regla de precedencia declarada aquí explícitamente: dentro del mismo `(anio, semana_archivo)`, la fila con `version` más alta es la vigente para alimentar `casos_epidemiologicos`; las versiones anteriores permanecen en la bitácora (nunca se borran, son parte de la auditoría) pero no se usan como fuente para la tabla de hechos una vez que existe una versión superior procesada.

**B. Nuevo valor de `estado`: `ausencia_esperada`.**

Se elimina la restricción `boletines_procesados_estado_check` (nombre confirmado en vivo, no asumido) y se recrea incluyendo el quinto valor:

```sql
CHECK (estado IN ('pendiente', 'ok', 'revision_manual', 'error', 'ausencia_esperada'))
```

El nombre se toma directamente del vocabulario que el propio documento maestro ya usa para describir este caso (Sección 5.1: "se registra con el mismo estado de ausencia esperada que un boletín de vacaciones"), en vez de inventar un término nuevo. Significa: el boletín se descargó y se abrió sin error, pero por diseño de MINSAL no trae tabla departamental (boletín de vacaciones) o cubre más de una semana en un solo archivo (no hay una semana única que ingerir como fila semanal). Distinto de `error` (el parser falló de forma inesperada sobre un boletín que debería traer tabla) y de `revision_manual` (la tabla existe pero la suma departamental no cuadra contra el total nacional publicado). Al reportar la calidad de la ingesta, las filas en `ausencia_esperada` no cuentan como fallo.

**C. `semana_archivo` deja de ser `NOT NULL`.**

Se elimina la restricción de no nulidad. Queda nula únicamente cuando no hay una semana única que registrar: boletines que cubren dos semanas combinadas, o boletines de vacaciones con nombre de archivo sin patrón `SE\d+` reconocible. Para el caso mayoritario de boletines de vacaciones que sí tienen una semana derivable del nombre (ej. `SE142023-Semana-Santa.pdf` → SE14), la columna se sigue poblando con normalidad — la nulidad es la salida para la ausencia genuina de dato, no una omisión general.

**D. Trazabilidad: `boletin_id` en `casos_epidemiologicos`.**

Se agrega `boletin_id INTEGER REFERENCES boletines_procesados(id)`, nullable. Nullable porque no todas las filas de `casos_epidemiologicos` provienen de un boletín MINSAL — las de `fuente_id = opendengue_v1_3` no tienen boletín que referenciar. Se puebla únicamente para filas cuyo `fuente_id` sea `minsal_pdf`. Con esto, ante un boletín marcado `ok` que después resulta mal parseado, `SELECT * FROM casos_epidemiologicos WHERE boletin_id = ?` responde exactamente qué filas produjo, sin depender de reconstruir la relación por `(anio, semana_epi, fuente_id)`, que no es uno a uno con un archivo concreto cuando hay republicaciones.

**E. Empaquetado con el ADR 0003.**

La migración que respalda este ADR también aplica el cambio ya aceptado en el ADR 0003 (`centroide_lat`, `centroide_lon`, `elevacion_m` en `regiones`), para no pagar dos ciclos de `docker compose down -v` mientras la base sigue vacía. No incluye la atribución de fuente climática (maestro, punto J): esa todavía no tiene ADR, y la regla de la Sección 7.4 no admite excepción por conveniencia de empaquetado. Si ese ADR se escribe y se acepta antes de que esta migración se redacte, debería evaluarse sumarlo también a la misma ventana.

## Consecuencias

* Positivo: la ingesta del parser queda idempotente por diseño — reejecutar sobre el mismo archivo actualiza, nunca duplica.
* Positivo: la métrica de calidad de la ingesta que cita el informe deja de contaminarse con boletines que nunca debieron contar como fallo.
* Positivo: los boletines de semanas combinadas se pueden registrar en la bitácora sin fabricar una semana que no existe.
* Positivo: un boletín mal parseado ya no es una pérdida de trazabilidad — se puede aislar exactamente qué filas de `casos_epidemiologicos` produjo.
* Positivo: una sola ventana de reconstrucción de volumen cubre este cambio y el del ADR 0003, mientras sigue siendo gratis.
* Negativo: `nombre_archivo` pasa a ser la pieza de la que depende la idempotencia. Si un archivo ya procesado se renombra fuera del flujo normal del parser (no hay evidencia de que esto ocurra, pero tampoco hay nada que lo impida a nivel de sistema de archivos), la próxima corrida lo trataría como un boletín nuevo en vez de una actualización — riesgo aceptado, no mitigado por este ADR.
* Negativo: la columna `version` depende de que el parser interprete el sufijo del nombre de archivo de forma consistente; no hay ninguna restricción de base de datos que lo verifique — es disciplina de código, no una garantía del esquema.
* Negativo: `boletin_id` solo cierra la trazabilidad para el tramo MINSAL de la ingesta; las filas de OpenDengue quedan fuera por diseño, tal como están hoy.
* Neutral: `url_origen` deja de ser candidata a llave pero se conserva sin cambios, como metadato descriptivo no verificado.
* Neutral: este ADR no resuelve el punto E del maestro (mecanismo de migraciones) ni el punto J (atribución de fuente climática) — ambos siguen abiertos, tal como estaban.

## Migración

No incluida en este ADR — según el proceso del proyecto, el ADR se escribe y se acepta antes de escribir la migración, no junto con ella. Cuando se acepte, la migración que respalda (`db/migrations/0002_*.sql`, nombre exacto pendiente) debe aplicar los cinco puntos de la Decisión más el cambio ya aceptado del ADR 0003, y ningún otro cambio de esquema que no tenga su propio ADR aceptado.
