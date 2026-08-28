# Fixtures MINSAL — extractos de texto reales, nunca PDFs

Cada `.txt` es el **texto extraído tal cual** (pdfplumber `extract_text()`)
de la página que contiene la tabla departamental de dengue del boletín
MINSAL correspondiente (o la portada / texto completo, en el caso del
boletín de vacaciones). Regla del proyecto
(`docs/contexto/03-fuentes-de-datos.md`, sección pytest): *"Guardar solo el
texto extraído como fixture, nunca los PDF"* — los PDFs viven en
`backend/ingestion/data/raw/minsal/` (gitignoreado) y se descargan con
`backend/ingestion/minsal/descargar_{año}.py` desde salud.gob.sv.

Ningún valor fue editado a mano: son datos públicos reales de la fuente,
extraídos el 2026-08-21 y verificados contra la bitácora de la corrida
exploratoria validada (`corrida_distribucion.py`, verificación 4/4, ver
`docs/contexto/03-fuentes-de-datos.md`).

| Fixture | Boletín | Por qué está aquí |
|---|---|---|
| `SE232018.pagina_tabla.txt` | `Boletin_epidemiologico_SE232018.pdf` | Caso de referencia verificado a mano (suma14 = 47 probables / 21 confirmados); Familia A; ruido narrativo pegado a la fila de Chalatenango ("… 3.4 21 casos.") |
| `SE242018.pagina_tabla.txt` | `Boletin_epidemiologico_SE242018.pdf` | Corte consecutivo al anterior (SE21→SE22) para el diff normal de desacumulación |
| `SE062018.pagina_tabla.txt` | `Boletin_epidemiologico_SE062018.pdf` | Celda en blanco = cero ("La Libertad 0 0.0", columna probable en blanco); el total impreso (12) solo cuadra leyendo el blanco como 0 |
| `SE352018.pagina_tabla.txt` | `Boletin_epidemiologico_SE352018.pdf` | Convención "Otros países INCLUIDO en el total publicado" (confirmados: 143+1=144); además, corte SE33 del par con diff negativo |
| `SE362018.pagina_tabla.txt` | `Boletin_epidemiologico_SE362018.pdf` | Corrección retroactiva real de MINSAL: Chalatenango probable acumulado 62→61 entre cortes SE33→SE34 (registrada en `correcciones_negativas.csv` de la corrida validada) |
| `SE382019.pagina_tabla.txt` | `Boletin_epidemiologico_SE382019.pdf` | Corte SE36 del par con hueco real de 14 semanas hasta SE50 (boletines intermedios de 2019 sin tabla departamental) |
| `SE522019_v2.pagina_tabla.txt` | `Boletin_epidemiologico_SE522019_v2.pdf` | Caso de referencia verificado a mano (437+2 / 174+2); convención "Otros países EXCLUIDO del total publicado" (footnote explícito en el boletín) |
| `SE012023.pagina_tabla.txt` | `Boletin_epidemiologico_SE012023.pdf` | Trampa del año: el título de la tabla dice "El Salvador 2022" dentro de un boletín de 2023 — el año se deriva del nombre/carpeta del archivo, nunca del texto |
| `SE522023.pagina_tabla.txt` | `Boletin_epidemiologico_SE522023.pdf` | Caso de referencia verificado a mano (17 / 54); Familia B (sin columna "Tasa x") |
| `SE01-02-2018.pagina_tabla.txt` | `Boletin_epidemiologico_SE01-02-2018.pdf` | Boletín de dos semanas combinadas (SE1+SE2 en un solo archivo) — ausencia esperada, ni se ingiere como semanal ni se divide |
| `SE142023-Semana-Santa.portada.txt` / `.texto_completo.txt` | `Boletin_epidemiologico_SE142023-Semana-Santa.pdf` | Boletín de vacaciones: se detecta por CONTENIDO (sin tabla departamental + portada de vacación), nunca por nombre de archivo (el nombre contiene un patrón `SE14` válido) |

Las páginas del texto completo van separadas por `\f` (form feed).

## Fixtures de IRA (`*.pagina_tabla_ira.txt`)

Extractos de la página que contiene la **tabla departamental de Infección
Respiratoria Aguda (IRA)** de cada boletín (misma regla: texto extraído tal
cual con pdfplumber, nunca PDFs), extraídos el 2026-08-21 para la corrida
exploratoria `corrida_ira.py` (ver `docs/exploracion-ira-boletines-minsal.md`).
Los usa `tests/test_corrida_ira.py`.

| Fixture | Boletín | Por qué está aquí |
|---|---|---|
| `SE01-02-2018.pagina_tabla_ira.txt` | `Boletin_epidemiologico_SE01-02-2018.pdf` | Layout lado-a-lado 2018 (sin tildes); la narrativa previa trae "…Chalatenango 1,377, San Salvador 1,005…" (tasas) que NO deben capturarse como filas; corte SE2 (boletín combinado SE1+SE2) |
| `SE032018.pagina_tabla_ira.txt` | `Boletin_epidemiologico_SE032018.pdf` | La narrativa repite la semana ANTERIOR ("SE 2-2018"); el título de la tabla dice "SE-03 de 2018" y es la única fuente válida de la semana de corte |
| `SE092018.pagina_tabla_ira.txt` / `SE102018.pagina_tabla_ira.txt` | `…SE092018.pdf` / `…SE102018.pdf` | Par de re-impresión: la tabla departamental de SE10 es idéntica a la de SE09 (San Salvador 119,670 en ambas) mientras la tabla de edad de SE10 ya trae datos nuevos — `detectar_reimpresiones` debe reclasificar SE10 |
| `SE382018.pagina_tabla_ira.txt` | `Boletin_epidemiologico_SE382018.pdf` | Total impreso malformado "1363,652" (primera coma de millares perdida) — debe leerse 1,363,652 y cuadrar con la suma de celdas |
| `SE012019.pagina_tabla_ira.txt` | `Boletin_epidemiologico_SE012019.pdf` | Título de tabla presente pero 0 filas extraíbles — tabla renderizada como imagen (sospecha explícita, nunca se rellena) |
| `SE432019_v3.pagina_tabla_ira.txt` | `Boletin_epidemiologico_SE432019_v3.pdf` | Variante de título "Casos y tasas **de IRA** por grupo de edad y departamento" (otro orden de palabras) |
| `SE522019_v2.pagina_tabla_ira.txt` | `Boletin_epidemiologico_SE522019_v2.pdf` | Layout lado-a-lado con tildes; acumulado final 2019 (San Salvador 700,913; total 1,951,867) |
| `SE522021.pagina_tabla_ira.txt` | `Boletin_epidemiologico_SE522021.pdf` | Título con rango "SE01-52 2021" (el corte es el segundo número); fila "Otros países" presente pero vacía; tasa sin separador ("19460") |
| `SE012023.pagina_tabla_ira.txt` | `Boletin_epidemiologico_SE012023.pdf` | Layout 2023 temprano: tabla departamental en página propia SIN título y con encabezado de columna erróneo ("Grupo de edad") — la semana sale del pie de estratificación |
| `SE522023.pagina_tabla_ira.txt` | `Boletin_epidemiologico_SE522023.pdf` | Separador de miles punto ("615.619"); discrepancia mínima real: las celdas suman 1,574,871 y el total impreso dice 1,574,872 |

## Fixtures de Neumonías (`*.pagina_tabla_neumonias.txt`)

Extractos de la página con la **tabla departamental de Neumonías** (pdfplumber
`extract_text()`, nunca PDFs). Los usa `tests/test_corrida_respiratorios.py`
y `backend/ingestion/corrida_respiratorios.py`. Extraídos 2026-08-28.

| Fixture | Boletín | Por qué está aquí |
|---|---|---|
| `SE01-02-2018.pagina_tabla_neumonias.txt` | `…SE01-02-2018.pdf` | Layout lado-a-lado 2018 (sin tildes); corte SE2 de un boletín combinado; San Salvador 172, total 701 |
| `SE032018.pagina_tabla_neumonias.txt` | `…SE032018.pdf` | Narrativa rezagada ("SE 2-2018"); el título de la tabla dice SE-03; San Salvador 259, total 1,142 |
| `SE092018.pagina_tabla_neumonias.txt` / `SE102018.pagina_tabla_neumonias.txt` | `…SE092018.pdf` / `…SE102018.pdf` | Cortes consecutivos distintos (no reimpresión: SS 1,001 → 1,130) para desacumulación y huecos |
| `SE012019.pagina_tabla_neumonias.txt` | `…SE012019.pdf` | Título de tabla presente, 0 filas extraíbles — tabla-imagen |
| `SE012023.pagina_tabla_neumonias.txt` | `…SE012023.pdf` | Layout 2023 página propia sin título de tabla; semana en el pie de estratificación (SE 1); SS 101, total 488 |
| `SE252023.pagina_tabla_neumonias.txt` | `…SE252023.pdf` | Tabla departamental 2023 con título propio; SS 2,733, total 10,618 |
| `SE522023.pagina_tabla_neumonias.txt` | `…SE522023.pdf` | Separador de miles punto ("5.667", "22.337"); las celdas suman 22,336 y el total impreso dice 22,337 |

## Fixtures de vigilancia de virus (`*.pagina_vigilancia_virus.txt`)

Extractos de la página con la **tabla laboratorial / vigilancia centinela**
de influenza y otros virus respiratorios. Unidad observada: muestras, no
casos clínicos. Granularidad: nacional.

| Fixture | Boletín | Por qué está aquí |
|---|---|---|
| `SE01-02-2018.pagina_vigilancia_virus.txt` | `…SE01-02-2018.pdf` | Tabla de 3 columnas (año previo / año actual / semana); VSR e influenza B; **sin** SARS-CoV-2 |
| `SE032018.pagina_vigilancia_virus.txt` | `…SE032018.pdf` | Mismo layout 2018, corte SE03 |
| `SE012023.pagina_vigilancia_virus.txt` | `…SE012023.pdf` | Layout 2023 temprano; encabezado de años de plantilla dudoso (imprime 2021/2022 en un boletín 2023) |
| `SE252023.pagina_vigilancia_virus.txt` | `…SE252023.pdf` | Dos columnas (2022/2023 acumulado); aparece `COVID 19(SE25)` con un valor |
| `SE522023.pagina_vigilancia_virus.txt` | `…SE522023.pdf` | Etiqueta `COVID 19(SE23)` **sin** valores extraíbles — no se fabrica; VSR 206; Adenovirus partido en dos líneas |
