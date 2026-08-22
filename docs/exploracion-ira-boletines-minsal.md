# Exploración: Infección Respiratoria Aguda (IRA) en los boletines MINSAL

**Fecha:** 2026-08-21 · **Estado:** exploración cerrada, nada ingerido a Postgres
**Herramienta:** `backend/ingestion/corrida_ira.py` (parser exploratorio, patrón de
`corrida_distribucion.py`; salida en `data/interim/corrida_ira/`, gitignoreada)
**Tests:** `backend/ingestion/tests/test_corrida_ira.py` (19 tests, todos sobre
extractos de texto reales en `tests/fixtures/minsal/*.pagina_tabla_ira.txt`)
**Decisión pendiente del coordinador:** ADR 0011 (propuesto) —
`docs/adr/0011-clasificacion-ira-departamental.md`

## Alcance del corpus

El brief asumía 15 PDFs disponibles en este worktree; el filesystem contiene en
realidad el **corpus completo de 264 boletines** (2018, 2019, 2021, 2022, 2023 —
2020 ausente por decisión vigente del proyecto). Toda cifra de este informe sale
de esos 264 PDFs reales; nada se descargó ni se fabricó. Donde un hallazgo se
verificó a mano sobre el PDF se indica el boletín y página exactos.

## Resultado global de la corrida (264 boletines)

| Estado | n | Qué significa |
|---|---|---|
| `ok` | 189 | Tabla extraída, suma de 14 departamentos cuadra con un total impreso del bloque |
| `ok_discrepancia_minima` | 25 | Cuadre con diferencia ±1–3 propia del boletín (ver hallazgo 6) — celdas conservadas |
| `sin_filas_sospecha_imagen` | 25 | Título de tabla presente, 0 filas extraíbles — tabla renderizada como imagen |
| `ausencia_esperada_vacacion` | 18 | Boletín de vacaciones sin tabla IRA (9 son los diarios de Semana Santa 2018) |
| `sin_texto_extraible` | 5 | 2019: SE23, SE28_v2, SE29_v2, SE32, SE35_v2 — sin ninguna mención de IRA extraíble (boletines escaneados, mismos sospechosos que en dengue) |
| `revision_manual` (reimpresión) | 2 | SE10/2018 y SE34/2019: tabla idéntica al corte anterior (hallazgo 5) |

Cortes usables por año (`ok` + `ok_discrepancia_minima`, tras excluir
reimpresiones): 2018: 45 · 2019: 22 · 2021: 50 · 2022: 49 · 2023: 48.
**2019 es el año dañado:** todos los boletines SE01–SE22 tienen la tabla IRA como
imagen; la serie extraíble de 2019 empieza en SE24.

Verificación contra casos conocidos (5/5): SE01/2023 (San Salvador 11,295, total
33,360), SE52/2023 (615.619 / 1.574.872, separador punto), SE52/2019_v2 (700,913 /
1,951,867), SE01-02/2018 (Chalatenango 2,823, total 54,543, corte SE2), SE03/2018
(total 88,099, corte SE3 pese a narrativa rezagada).

## Hallazgos

### 1. Un solo conteo por departamento — no existe split probable/confirmado

La tabla departamental de IRA es `Departamento | Total | Tasa x 100 mil` en todo
el corpus. El encabezado "Probable / Confirmado" que aparece en la tabla
**nacional por grupo de edad** de 2023 es un **error de plantilla de MINSAL, no
un dato**: en SE01/2023 (página 13), `pdfplumber.extract_table()` confirma que la
grilla dice `['Grupo de edad', 'Probable SE1', 'Confirmado SE1']`, pero la
columna "Confirmado" trae 2,112 / 1,364 / 823 / … con "Total" **485** — que es la
tasa nacional x100mil publicada en la narrativa del mismo boletín ("485 casos
x100mil/hab."), imposible como suma de casos (ningún sumando es menor que 485).
La columna "Probable" sí suma exacto: 33,360 = total nacional del resumen de
notificación (página 3 del mismo boletín). Conclusión: **la segunda columna es la
tasa; solo existe un total clínico**. No hay forma real de desagregar
probable/confirmado a nivel departamental (ni nacional) para IRA en ningún
boletín revisado.

Esto responde la duda del brief: el "Confirmado" nacional NO es confirmado — es
la tasa con el rótulo equivocado, y el orden de columnas de `extract_text()` no
era el problema (la grilla real lo dice).

### 2. Acumulado desde SE1 — confirmado empíricamente en todo el corpus

Misma trampa 8 que dengue. Evidencia de corrida completa, no solo el par
SE01/SE52: sobre 2,926 pares de cortes consecutivos por (año, departamento),
**2,923 son crecientes y 3 decrecientes** (0.10%). Los 3 decrecientes son las
correcciones retroactivas reales (Cuscatlán 2022 SE47: 48,199→47,434, diff −765;
Cuscatlán 2023 SE50: 40,474→40,425, diff −49) más un caso absorbido por la
reimpresión de SE34/2019. La de-acumulación (diferencia entre cortes
consecutivos) replica las reglas validadas de dengue: huecos = sin dato (nunca
interpolar), diffs negativos = corrección retroactiva excluida (nunca clampear a
cero). El primer corte de cada año es acumulado desde SE1 y queda marcado si no
es SE1 (no se divide).

### 3. Separador de miles inconsistente — y a veces malformado

- Coma en 2018–2022 y 2023 temprano ("33,360"); **punto** en SE52/2023
  ("1.574.872", "615.619"); tasas a veces **sin separador** ("19460" en
  SE52/2021, "24574" en SE44/2022). Manejado por heurística de grupos de 3
  dígitos (`parsear_numero`), documentada en el código.
- **Malformado real:** SE38/2018, SE43/2018, SE49/2018 y SE44/2022 imprimen el
  total con la primera coma de millares perdida ("Total general **1363,652**" =
  1,363,652 — verificado porque la suma de las 14 celdas del mismo boletín da
  exactamente ese valor). El parser lo acepta como millares.

### 4. Dos layouts, y la semana de corte solo es confiable en el título de la tabla

- **2018–2022 ("lado a lado"):** la tabla departamental comparte página con la de
  grupos de edad y `extract_text()` intercala filas de ambas. Anclar en el nombre
  del departamento y capturar máximo 2 números en la misma línea es inmune a eso.
  2018 imprime departamentos sin tilde ("Usulutan", "Morazan").
- **2023 ("página propia"):** tabla departamental separada. En 2023 temprano
  (SE01–…) esa página **no tiene título** y su encabezado de columna dice
  **"Grupo de edad"** siendo las filas departamentos (otro error de plantilla);
  la semana se lee del pie de estratificación de la misma página.
- **La narrativa sobre la tabla está rezagada una semana en 2018:** SE03/2018
  dice "Infección Respiratoria Aguda… SE 2-2018" en la sección y "SE-03 de 2018"
  en el título de la tabla; además la narrativa trae números pegados a nombres de
  departamento ("…Chalatenango 1,377, San Salvador 1,005…" — tasas) que
  contaminarían la captura. Regla implementada: la semana sale del **título de la
  tabla** (212/216 casos), después del pie de estratificación (3), después del
  título de sección (1, SE39/2018, contrastado contra el nombre de archivo); el
  bloque de filas empieza en el título o en el encabezado de columnas, nunca
  antes. En los 216 boletines parseados la semana del título coincide con la del
  nombre de archivo (a diferencia de dengue, donde el corte del encabezado puede
  diferir).
- Variante de título en 2019: "Casos y tasas **de IRA** por grupo de edad y
  departamento" (SE43/2019) además del orden usual "…por grupo de edad y
  departamento de IRAS".

### 5. Tablas reimpresas/rezagadas — trampa nueva, no documentada en dengue

**SE10/2018** publica como tabla departamental una **reimpresión exacta de la de
SE09/2018** (los 14 valores idénticos; San Salvador 119,670 en ambas) mientras la
tabla de edad del mismo boletín ya trae los datos nuevos de SE10 (total 369,467
vs 326,229 de la departamental — así se detectó). Ídem **SE34/2019** respecto de
SE33/2019. Ingerirla en su semana declarada fabricaría una semana de 0 casos
seguida de una doble. Detección implementada: 14 valores acumulados idénticos al
corte anterior del mismo año (imposible como dato real — sería una semana
nacional con 0 casos de IRA) → `revision_manual`.

Corolario: en el layout lado-a-lado hay **dos** líneas "Total general" (edad y
departamental) que **no siempre coinciden** (SE49/2021 difieren en 10). La
reconciliación valida contra cualquiera de los totales del bloque, no "el
primero".

### 6. El total impreso difiere en ±1–3 de la suma de sus propias celdas (2023)

En **25 de los 48** boletines parseables de 2023 (y solo en 2023), la suma de las
14 celdas impresas difiere del total impreso en 1–3 casos, **con signo variable**.
Verificado a mano en SE52/2023: las celdas impresas suman 1,574,871 y el total
dice 1,574,872. No es error de extracción — es inconsistencia interna del boletín
(≈2×10⁻⁶ relativo). Tratamiento: estado `ok_discrepancia_minima` (|diff| ≤ 3),
celdas conservadas tal cual (el total es solo un checksum de MINSAL), diferencia
registrada en bitácora. Nunca se ajusta ninguna celda para forzar el cuadre.

### 7. "Otros países" existe como fila pero nunca trae valores

La fila aparece en 2021–2023 y está **vacía en el 100% de los boletines
parseados** (en 2018–2019 ni aparece). Distinto de dengue, donde sí trae conteos
y su inclusión en el total varía. La reconciliación implementa de todos modos
ambas convenciones por si el corpus futuro la trajera con valores.

### 8. Ausencias y años dañados

- Los 9 boletines diarios de Semana Santa 2018 y los de vacaciones
  (agostinas/fin de año) no traen tabla IRA — detectados por contenido de
  portada, como en dengue.
- **2019 SE01–SE22: tabla IRA como imagen** (21 boletines) + SE23/28/29/32/35 sin
  texto extraíble → la serie 2019 extraíble empieza en SE24. Rescatarlos
  requeriría OCR, que está fuera de alcance y **requiere confirmación del
  coordinador antes de instalar dependencias** (regla del stack cerrado).
- 2018: SE48/SE50/SE52 también como imagen; 2023: solo SE05.
- El boletín combinado SE01-02/2018 **sí es usable para IRA** (a diferencia de la
  ingesta semanal de dengue): al ser la serie un acumulador, su corte SE2 es un
  punto válido del acumulador; el primer diff queda marcado como "acumulado
  SE1-SE2", nunca dividido.

## Qué queda listo para decidir (no decidido aquí)

1. **ADR 0011 (propuesto):** nuevo valor `'reportado'` en el CHECK de
   `casos_epidemiologicos.clasificacion` — ni `probable`, ni `confirmado`, ni el
   `total` reservado de OpenDengue describen un conteo clínico sin split. Sin
   migración escrita; decisión del coordinador.
2. INSERT de catálogo `tipos_evento ('ira', …)` — no requiere ADR, queda sugerido
   en el ADR 0011; no ejecutado.
3. Si se aprueba la ingesta: el pipeline es exactamente el prototipado aquí
   (extraer → validar cuadre → desacumular con reglas de dengue), con los estados
   de bitácora existentes de `boletines_procesados` mapeables 1:1
   (`ausencia_esperada`, `sin_texto_extraible`, `revision_manual`).

## Hipótesis que el corpus disponible no permite cerrar

- Si los boletines de 2024+ (no descargados) mantienen el layout 2023 y su
  discrepancia ±1–3.
- La causa de las tablas-imagen (2019 primera mitad, fin de 2018): el patrón
  sugiere un cambio de herramienta de maquetación de MINSAL, pero es conjetura.
- Si la tasa departamental impresa es siempre acumulada (parece serlo: crece
  junto al conteo), porque no se usó para nada en esta corrida.
