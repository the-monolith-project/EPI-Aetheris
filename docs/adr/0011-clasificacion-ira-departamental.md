# 0011 - Clasificación para el conteo departamental de IRA (nuevo valor de `clasificacion`)

**Estado:** Propuesto

> **Borrador para decisión del coordinador — NO aplicado.** Ninguna migración
> acompaña este ADR y nada de IRA se ha insertado en `casos_epidemiologicos`.
> La evidencia empírica que lo sustenta está en
> `docs/exploracion-ira-boletines-minsal.md` (corrida exploratoria
> `backend/ingestion/corrida_ira.py`, 2026-08-21).

## Contexto

Los mismos boletines PDF de MINSAL ya usados para dengue publican, boletín a
boletín, una tabla departamental de **Infección Respiratoria Aguda (IRA)**:
dato real, público, ya descargado. El esquema es deliberadamente agnóstico a
enfermedad (`tipos_evento` es catálogo), así que ingerir IRA no requiere
columnas nuevas — pero sí choca con un CHECK constraint existente:

- `casos_epidemiologicos.clasificacion` solo admite `'probable'`,
  `'confirmado'` y `'total'`.
- La tabla departamental de IRA trae **un solo conteo clínico por
  departamento** (`Departamento | Total | Tasa x 100 mil`), sin split
  probable/confirmado. Verificado empíricamente en todo el corpus disponible
  (2018–2023 sin 2020): no existe desagregación probable/confirmado
  departamental de IRA en ningún boletín revisado. El encabezado
  "Probable/Confirmado" que aparece en la tabla **nacional por grupo de edad**
  de 2023 es un error de plantilla de MINSAL, no un dato: su segunda columna
  es la tasa x100mil (en SE01/2023 el "Total" de esa columna es 485 = la tasa
  nacional publicada en la narrativa del mismo boletín, imposible como suma
  de casos), confirmado con `pdfplumber.extract_table()` sobre la grilla real.

Ninguno de los tres valores existentes describe bien este conteo:

- `'probable'` / `'confirmado'` afirmarían un estado de laboratorio/definición
  de caso que la fuente no reporta.
- `'total'` ya tiene significado reservado (ADR 0005): agregado OpenDengue
  **nacional**, exclusivo de `fuente_id = opendengue_v1_3`. Reutilizarlo aquí
  rompería esa exclusividad y mezclaría dos conceptos de procedencia distinta
  en la misma etiqueta.

La regla del proyecto es "ADR antes de cambio de esquema", y ampliar un CHECK
constraint es cambio de esquema.

## Decisión (propuesta)

Agregar el valor **`'reportado'`** al CHECK de
`casos_epidemiologicos.clasificacion`, con semántica: *conteo clínico
notificado por la fuente sin desagregación probable/confirmado ni
confirmación de laboratorio declarada*.

Alternativa considerada: `'total_clinico'`. Se prefiere `'reportado'` por ser
más corto, no colisionar léxicamente con el `'total'` de OpenDengue (evita
confusión al leer queries) y describir el hecho epidemiológico real (casos
reportados al sistema de vigilancia, definición clínica).

La fila de catálogo para el evento **no** requiere ADR (es dato, no esquema);
queda lista para cuando el coordinador decida:

```sql
INSERT INTO tipos_evento (codigo, nombre, descripcion)
VALUES ('ira', 'Infección Respiratoria Aguda',
        'Conteo clínico semanal de IRA por departamento, boletines MINSAL; serie acumulada desde SE1 desacumulada por diferencia de cortes consecutivos');
```

## Consecuencias

* Positivo: IRA (y futuras tablas del mismo boletín: neumonías, EDAS,
  zika/chikungunya, que comparten el formato de conteo único) se ingiere sin
  falsear su definición de caso; `'confirmado'` conserva su significado MINSAL
  estricto y `'total'` su exclusividad OpenDengue (ADR 0005 intacto).
* Positivo: el diseño agnóstico a enfermedad se ejercita de verdad por primera
  vez (segundo evento en `tipos_evento` sin tocar columnas).
* Negativo: toda query que hoy hace `WHERE clasificacion IN (...)` debe
  revisarse — la regla vigente "nunca sumar `conteo` entre valores de
  `clasificacion` sin filtrar" pasa a tener un cuarto valor que excluir o
  incluir explícitamente.
* Negativo: requiere migración nueva (ampliar el CHECK) aplicada con
  `db/aplicar_migraciones.py` (ADR 0009); el seed versionado (ADR 0010) no la
  conoce hasta regenerarse.
* Neutral: la desacumulación previa a cualquier ingesta (la serie publicada es
  acumulada desde SE1, misma trampa 8 de dengue) es independiente de esta
  decisión y ya está prototipada en `backend/ingestion/corrida_ira.py`.
