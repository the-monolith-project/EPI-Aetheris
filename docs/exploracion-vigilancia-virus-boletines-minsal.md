# Exploración: vigilancia centinela de Influenza, VSR y SARS-CoV-2 (MINSAL)

**Fecha:** 2026-08-28 · **Estado:** exploración cerrada, nada ingerido a Postgres
**Herramienta:** `backend/ingestion/corrida_respiratorios.py`
**Tests:** `backend/ingestion/tests/test_corrida_respiratorios.py` contra
`*.pagina_vigilancia_virus.txt`
**Protocolo:** `docs/protocolo-exploracion-respiratorios.md`

Neumonías se documenta aparte (`docs/exploracion-neumonias-boletines-minsal.md`).
Esta nota cubre **solo** la vigilancia virológica.

## Unidad de observación

No son casos clínicos departamentales.

La tabla que MINSAL publica semana a semana se titula *Resumen de resultados
de Vigilancia Laboratorial para virus respiratorios* / *Vigilancia Laboratorial
para virus respiratorios*. Cada fila es una **métrica de laboratorio
centinela**, a nivel **nacional**:

| Métrica en la fuente | Qué es | Unidad |
|---|---|---|
| Total de muestras analizadas | denominador | conteo |
| Muestras positivas a virus respiratorios | numerador (cualquier virus) | conteo |
| Total de virus de influenza (A y B) | detecciones influenza | conteo |
| Influenza A (H1N1)pdm2009 / H3N2 / no sub-tipificado / B | subtipo | conteo |
| Total de otros virus respiratorios | parainfluenza + VSR + adenovirus (+ COVID si aparece) | conteo |
| Parainfluenza, VSR, Adenovirus | virus no influenza | conteo |
| COVID 19(SEn) | etiqueta de SARS-CoV-2, solo 2023 | conteo |
| Positividad acumulada para virus / Influenza / VSR | proporción | porcentaje |

No se convierte positividad en casos. No se infiere un patógeno a partir de
IRA o Neumonías. ETI aparece solo en la narrativa regional OPS, no como tabla
nacional. IRAG aparece como corredor endémico (gráfico SIMMOW de egresos),
otra unidad; no se extrae como serie de virus.

## Granularidad

- **Temporal:** semanal, **acumulada desde SE1** (las columnas “año actual” y
  “año previo” son acumulados al corte; cuando hay tercera columna es la
  semana puntual).
- **Geográfica:** nacional. Ninguna tabla laboratorial extraída desagrega por
  departamento, establecimiento ni sitio centinela. **No hay mapa.**
- **Estratificación:** por virus / métrica, no por edad en esta tabla.

Layouts de columnas:

- 3 columnas (199 boletines `ok`): año previo, año actual, semana.
- 2 columnas (38 boletines `ok`, sobre todo 2023 tardío): año previo, año actual.

El encabezado de años a veces está atrasado (SE01/2023 imprime “2021 2022”
en un boletín de 2023). El año vigente sale del nombre/carpeta del archivo,
igual que en dengue.

## Resultado global (264 boletines)

| Estado | n |
|---|---|
| `ok` | 237 |
| `ausencia_esperada_vacacion` | 18 |
| `sin_texto_extraible` | 5 (2019 escaneados: SE23, SE28_v2, SE29_v2, SE32, SE35_v2) |
| `sin_filas_sospecha_imagen` | 3 (SE47–SE49/2021: sección presente, tabla de muestras no extraíble) |
| `revision_manual` | 1 (SE47/2018: número con asterisco `2428*` de “dato corregido”; el parser ya acepta el `*` en tests — la corrida original lo dejó fuera) |

Cortes `ok` por año: 2018: 48 · 2019: 44 · 2021: 47 · 2022: 49 · 2023: 49.

Métricas presentes en los 237 `ok` (n de boletines que las traen): muestras
analizadas 237; influenza A/B y subtipos 237; VSR/parainfluenza/adenovirus
236; positividad influenza 235 / VSR 234 / virus 229; muestras positivas 197
(el rótulo a veces parte de línea); **COVID-19 41, todos en 2023** (39 con
valor, 2 con etiqueta vacía — no se fabrica).

## Virus encontrados

Investigados y vistos en la fuente:

- Influenza A (H1N1)pdm2009 (a veces `H1N1*` “estacional”)
- Influenza A H3N2
- Influenza A no sub-tipificado
- Influenza B
- Virus Sincitial Respiratorio (VSR)
- Parainfluenza
- Adenovirus
- COVID-19 (rótulo `COVID 19(SEn)`, no “SARS-CoV-2”)

No se descartó ninguno del parser por no estar en el objetivo inicial.

## Decisión sobre 2020 (explícita)

La etiqueta COVID-19 **no aparece** en las tablas laboratoriales de 2018,
2019, 2021 ni 2022 del corpus. Empieza en 2023 (41 boletines).

Por tanto, **esta rama no descarga 2020**. No es una copia de la exclusión
de dengue/IRA: es que la fuente histórica disponible ya muestra el contrato
de SARS-CoV-2 (una fila nacional de detecciones, a veces incompleta) sin
necesidad de 2020 para saber qué es el dato. Si más adelante se quiere la
serie 2020 como contexto de pandemia, es una extensión aparte, con su
propio `descargar_2020.py`, sin meter esos PDF en dengue ni IRA.

2024+ sigue fuera de alcance.

## Persistencia (no implementada aquí)

`casos_epidemiologicos` no sirve: mezclaría muestras y porcentajes con
conteos clínicos, y no hay `region_id` departamental. Hace falta una tabla
de vigilancia virológica (métrica × virus × semana, `region_id` nulo) — ADR
en el commit documental siguiente.
