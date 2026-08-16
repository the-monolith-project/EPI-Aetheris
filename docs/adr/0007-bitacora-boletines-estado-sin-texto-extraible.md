# 0007 - Bitácora de boletines: nuevo estado `sin_texto_extraible`

**Estado:** Aceptado

## Contexto

La corrida exploratoria del parser (`backend/ingestion/corrida_distribucion.py`, 264 PDF, resumen en `docs/contexto/03-fuentes-de-datos.md` trampa 8/11) encontró un caso que el `CHECK` actual de `boletines_procesados.estado` (`pendiente`, `ok`, `revision_manual`, `error`, `ausencia_esperada` — ADR 0004) no cubre: 3 boletines de 2019 (`SE232019`, `SE322019`, `SE352019_v2`) tienen la tabla departamental de dengue pegada como imagen/raster en vez de texto extraíble — cero menciones de la palabra "dengue" en todo el documento, y el boletín **no** es de vacaciones (no aplica `ausencia_esperada`).

Ninguno de los cinco valores existentes describe esto con precisión:

- `error`: implica que el parser falló de forma inesperada sobre un boletín que debería procesarse — pero aquí el PDF se abre sin excepción, el problema es que el contenido relevante no existe como texto en absoluto, algo estructuralmente distinto de un fallo de parsing.
- `revision_manual`: implica que la tabla existe y se extrajo, pero la suma departamental no cuadra contra el total nacional — aquí no hay tabla que sumar, no se llegó a extraer nada.
- `ausencia_esperada`: implica que MINSAL, por diseño, no publicó tabla departamental esa semana (vacaciones, semanas combinadas) — aquí sí la publicó, solo que como imagen en vez de texto.

Meter este caso en cualquiera de los tres contamina esa métrica: `error` infla la tasa de fallos genuinos del parser (que el informe cita como calidad de la ingesta) con algo que no es un fallo del parser sino una limitación conocida y localizada de la fuente; `ausencia_esperada` afirmaría que MINSAL no publicó el dato, cuando sí lo hizo, solo que en un formato que esta ingesta no lee.

**Alcance de este ADR:** registrar el estado, no resolver el rescate. El rescate en sí (rasterizar la página y aplicar OCR con `pytesseract`) es la tarjeta 26, bloqueada aparte porque agregar una dependencia de OCR toca el stack ya cerrado (`docs/contexto/01-decisiones-cerradas.md`) y requiere confirmación explícita del coordinador antes de instalarse — no se resuelve aquí ni se adelanta.

## Decisión

Se elimina la restricción `boletines_procesados_estado_check` y se recrea con un sexto valor:

```sql
CHECK (estado IN ('pendiente', 'ok', 'revision_manual', 'error', 'ausencia_esperada', 'sin_texto_extraible'))
```

`sin_texto_extraible`: el boletín se descargó y se abrió sin error, pero no se encontró ninguna mención de "dengue" en el texto extraíble de ninguna página — indicio de que la tabla departamental (o el documento completo) está renderizada como imagen, no como texto de fuente. Distinto de `error` (el parser encontró contenido de texto pero no pudo interpretarlo) y de `ausencia_esperada` (MINSAL no publicó tabla departamental esa semana por diseño). Al reportar la calidad de la ingesta, las filas en `sin_texto_extraible` se cuentan aparte, no como fallo del parser ni como ausencia real de dato — son un hueco de cobertura conocido, pendiente de rescate vía OCR (tarjeta 26).

**Estados exploratorios que NO requieren un nuevo valor, mapeados a uno existente por el parser de producción:**

- `ausencia_esperada_vacacion` y `ausencia_esperada_multisemana` (distinguidos en la corrida exploratoria para diagnóstico) colapsan ambos a `ausencia_esperada` en producción — la distinción entre "vacaciones" y "semanas combinadas" queda en la columna `notas` de texto libre, no amerita una rama nueva del `CHECK`.
- `sin_tabla_no_vacacional` (trampa 9, `SE182023`: no es vacación, sí menciona "dengue" en el documento, pero no se localiza la tabla departamental) mapea a `revision_manual` — es una anomalía real que alguien debe mirar a mano, la misma semántica que ya cubre ese valor.

## Consecuencias

* Positivo: la métrica de calidad de la ingesta que cita el informe distingue ahora tres cosas antes mezcladas: fallo genuino del parser (`error`), ausencia real de dato (`ausencia_esperada`), y hueco de cobertura conocido por limitación de formato (`sin_texto_extraible`).
* Positivo: dejar constancia explícita de estos 3 boletines en la bitácora es lo que permite, más adelante, contar exactamente cuántas semanas de 2019 dependen del rescate OCR (tarjeta 26) sin tener que releer la corrida exploratoria cada vez.
* Negativo: mismo costo ya aceptado en el ADR 0004 — con el volumen de Postgres ya poblado (clima 2014-2024, casos OpenDengue 2014-2023), aplicar este cambio de esquema exige, en ausencia de un runner de migraciones (punto C de `docs/contexto/02-decisiones-abiertas.md`, sigue abierto), aplicar la sentencia DDL directamente sobre el volumen en ejecución además de dejar la migración versionada para instalaciones limpias — no un `docker compose down -v` completo esta vez, por el costo de reingesta ya explicado en ese punto.
* Neutral: no adelanta ni bloquea la decisión de si la vía departamental se activa como segundo clasificador (punto H de `02-decisiones-abiertas.md`) — solo mejora la calidad del registro de auditoría del parser de producción.

## Migración

`db/migrations/0005_bitacora_sin_texto_extraible.sql` — un único cambio de `CHECK`, sin empaquetar con ningún otro ADR pendiente.
