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
