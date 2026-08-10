# 0006 - Segunda fila de catálogo `open_meteo_era5` para atribuir precipitación a su modelo real

**Estado:** Aceptado

## Contexto

`fuentes_datos` (`db/migrations/0001_init_schema.sql`) solo tiene una fila para Open-Meteo: `open_meteo_era5_land`. El modelo climático dejó de ser único el 2026-08-07 (`docs/contexto/01-decisiones-cerradas.md`): `era5_land` sirve `temperature_2m_max/min/mean`, `relative_humidity_2m_mean` y `dew_point_2m_mean`, pero **no sirve precipitación** (limitación confirmada de la implementación, no del dataset — ver `backend/ingestion/clima/hallazgos_precipitacion_modelo.md`). `precipitation_sum` y `precipitation_hours` salen de `era5`, un modelo distinto, con resolución distinta (0,25° vs. 0,1°) y con su propia trampa de cero falso ya documentada.

Este hueco quedó registrado como punto abierto (`02-decisiones-abiertas.md`, punto B) desde el cierre del modelo por variable, con la nota explícita de no escribir el ADR sin que se pidiera. Al construir el loader de clima (tarjeta 12) se volvió bloqueante real: insertar filas de `precipitation_sum`/`precipitation_hours` con `fuente_id = open_meteo_era5_land` atribuiría esos datos a un modelo que no los produjo — mismo tipo de mala etiqueta que motivó el ADR 0005 para OpenDengue, esta vez sobre la procedencia del predictor climático en vez del conteo de casos.

**Dos salidas evaluadas** (ya enumeradas en el punto B): (1) una segunda fila de catálogo por modelo, o (2) una columna `modelo` en `variables_ambientales` para registrar la procedencia fila por fila. La segunda es más flexible (permite mezclar modelos dentro de la misma fuente lógica) pero más cara: toca la tabla de hechos completa, no solo el catálogo, y ninguna variable actual del proyecto lo necesita — cada variable tiene un modelo fijo y único (`era5_land` o `era5`, nunca ambos para la misma variable). `fuentes_datos` ya está diseñada como catálogo abierto a nuevas filas sin migración de estructura (mismo principio que `tipos_evento`), así que una fila nueva no exige tocar columnas, restricciones ni valores de `CHECK` — pero se sigue el mismo proceso de ADR previo que el resto del proyecto, porque el propio punto B ya lo exigía explícitamente y la decisión de forma (fila nueva vs. columna nueva) sí es una decisión de diseño que vale la pena dejar registrada.

## Decisión

Se agrega una segunda fila a `fuentes_datos`:

```sql
INSERT INTO fuentes_datos (codigo, nombre, url_referencia, notas) VALUES
    ('open_meteo_era5', 'Open-Meteo - ERA5', 'https://open-meteo.com',
     'Unico modelo usado para precipitation_sum/precipitation_hours (era5_land no sirve precipitacion). Resolucion 0,25 grados -- La Libertad y San Salvador comparten celda, aceptado deliberadamente (ver docs/contexto/01-decisiones-cerradas.md).');
```

`open_meteo_era5_land` conserva las cinco variables de superficie (temperatura ×3, humedad, punto de rocío). `open_meteo_era5` es exclusivamente para las dos variables de precipitación. El loader (`backend/ingestion/cargar_clima.py`) resuelve el `fuente_id` correcto por variable antes de insertar — nada en el esquema fuerza esa correspondencia (mismo patrón de disciplina de loader que `clasificacion = 'total'` en el ADR 0005), así que cualquier código nuevo que escriba en `variables_ambientales` debe hacer el mismo mapeo variable → fuente, no asumir una sola fuente para toda la tabla.

## Consecuencias

* Positivo: `variables_ambientales.fuente_id` queda trazable a un modelo real y consultable por separado — se puede auditar o recalibrar precipitación sin tocar las otras cinco variables.
* Positivo: no exige tocar ninguna columna, restricción ni `CHECK` existente — es una fila de catálogo, coherente con el diseño ya cerrado de `fuentes_datos` como tabla abierta a extensión.
* Negativo: nada en el esquema impide que un loader futuro use el `fuente_id` equivocado para una variable — sigue siendo disciplina de código, no una garantía de la base de datos (igual que la correspondencia `clasificacion`↔`fuente_id` del ADR 0005).
* Negativo: si se necesitara mezclar dos modelos dentro de la misma variable en el futuro (no es el caso hoy), esta forma no alcanzaría y habría que revisar la opción de columna `modelo` descartada aquí.
* Neutral: no resuelve el punto B en el sentido de que sigue sin haber una restricción de base de datos que ligue variable↔fuente automáticamente — solo resuelve la atribución correcta de los datos ya cargados.

## Migración

`db/migrations/0004_fuente_climatica_era5.sql` — un solo `INSERT`, sin cambios de estructura. Verificada en secuencia (`0001`→`0002`→`0003`→`0004`) sobre Postgres 15 desechable antes de aceptarse, mismo criterio que los ADR anteriores.
