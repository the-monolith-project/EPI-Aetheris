# 0012 - Persistencia de la vigilancia laboratorial de virus respiratorios

**Estado:** Aceptado (2026-08-28)

> Única verdad documental: **Aceptado**. No queda pendiente de confirmación.
> Aceptado sobre evidencia de `docs/exploracion-vigilancia-virus-boletines-minsal.md`
> (corrida `backend/ingestion/corrida_respiratorios.py`, 264 PDF). Migración:
> `db/migrations/0008_vigilancia_virus_y_catalogo_neumonia.sql`.
> Neumonías **no** usa esta tabla: reutiliza `casos_epidemiologicos` con
> `clasificacion='notificado'` (ADR 0011) y `tipos_evento='neumonia'`.

## Contexto

Los mismos boletines MINSAL de dengue/IRA/neumonías publican una tabla
nacional de **vigilancia centinela / laboratorial** de virus respiratorios.
La unidad observada no es un caso clínico departamental:

- muestras analizadas y muestras positivas (denominador / numerador);
- detecciones por virus (Influenza A/B y subtipos, VSR, parainfluenza,
  adenovirus, y en 2023 una fila `COVID 19`);
- positividad acumulada (porcentaje), publicada por la fuente.

No hay desagregación departamental. No hay probable/confirmado. Convertir
positividad o detecciones en filas de `casos_epidemiologicos.conteo`
falsearía la semántica de esa tabla (conteo de casos por región-semana) y
mezclaría porcentajes con enteros.

## Decisión

Crear la tabla `vigilancia_virus_respiratorios` (EAV por virus × métrica):

```text
anio, semana_epi, virus, metrica, valor, unidad,
region_id (nacional SV), fuente_id, boletin_id nullable
```

- `virus` es texto controlado por el loader, **sin CHECK de nombres**, para
  admitir un virus nuevo sin migración. Valores iniciales: `todos`,
  `influenza`, `influenza_a_h1n1`, `influenza_a_h3n2`,
  `influenza_a_no_subtipificado`, `influenza_b`, `vsr`, `parainfluenza`,
  `adenovirus`, `covid_19`.
- `metrica` CHECK: `muestras_analizadas`, `muestras_positivas`,
  `detecciones`, `positividad`.
- `unidad` CHECK: `conteo` | `porcentaje`. Un porcentaje nunca se guarda
  como `conteo`.
- `region_id` apunta a `regiones.codigo='SV'` (nivel_admin=0), igual que
  ONI (ADR 0008). No es nullable: así la UNIQUE no tropieza con NULL.
- Semanas ausentes no se insertan (hueco, no cero).
- La positividad se guarda **tal como la publica la fuente**, sin
  recalcularla en silencio. Los conteos se guardan como incidencia semanal:
  tercera columna de la tabla cuando existe; si no, diferencia de
  acumulados del año actual, con las mismas reglas de honestidad que IRA
  (hueco, corrección negativa excluida, primer corte marcado y no dividido).
- 2020 no se ingiere: la etiqueta COVID-19 no aparece en 2018–2022 del
  corpus y el contrato de 2023 ya es visible sin ese año.
- `fuente_id = minsal_pdf`. `boletin_id` queda NULL en la primera carga
  (igual que IRA): la bitácora exploratoria vive en interim.

Neumonías: INSERT de catálogo `tipos_evento ('neumonia', …)` en la misma
migración (dato, no esquema; ADR 0011 ya autoriza `'notificado'`).

### Alternativas descartadas

* Reutilizar `casos_epidemiologicos` con `tipo_evento` por virus — descartado:
  las cifras no son casos, la geografía no es departamental, y la positividad
  no cabe en `conteo INTEGER`.
* Columnas fijas `muestras_procesadas`, `positivos_influenza`, … — descartado:
  cada virus nuevo exigiría migración; duplica denominadores.
* No persistir vigilancia y dejar solo Neumonías — descartado: el objetivo
  de la rama es exponer Influenza/VSR/SARS-CoV-2 con su semántica real.

## Consecuencias

* Positivo: se conservan numerador, denominador y porcentaje por separado;
  virus nuevos no rompen el esquema; el mapa departamental no puede
  pintarse “por error” porque no hay `region_id` de departamento.
* Negativo: una tabla más, queries distintas a las de IRA/neumonías.
* Neutral: Neumonías sigue el camino de IRA (`casos_epidemiologicos`);
  dengue no cambia.
