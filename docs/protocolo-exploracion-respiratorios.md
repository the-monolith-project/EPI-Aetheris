# Protocolo de exploración respiratoria (MINSAL)

Corrida exploratoria: `backend/ingestion/corrida_respiratorios.py`.
Salida (gitignoreada): `backend/ingestion/data/interim/corrida_respiratorios/`.
Tests: `backend/ingestion/tests/test_corrida_respiratorios.py` contra extractos reales
en `backend/ingestion/tests/fixtures/minsal/` (`*.pagina_tabla_neumonias.txt`,
`*.pagina_vigilancia_virus.txt`). Nada de este protocolo escribe a Postgres.

## Qué se busca, por separado

Neumonías e Influenza/VSR/SARS-CoV-2 **no se tratan como un mismo contrato**.
La hipótesis de trabajo (no decisión) es: Neumonías ≈ evento notificable
departamental (candidato a parecerse a IRA); Influenza/VSR/SARS-CoV-2 ≈
vigilancia centinela/laboratorial nacional (muestras, positivos, positividad).

### Neumonías

Por cada PDF: presencia de sección, título exacto, página, semana declarada
(leída del título de la tabla, nunca de la narrativa), tipo de tabla, filas
departamentales, total nacional, tasa, grupo etario si aparece, acumulado vs
semanal, cuadre de suma, ausencia, tabla-imagen, reimpresión, corrección
retroactiva, cambio de layout.

### Vigilancia de virus

Por cada PDF, registrar lo que exista: Influenza (A/B y subtipos), VSR,
SARS-CoV-2/COVID-19, otros virus (parainfluenza, adenovirus, …), ETI, IRAG,
centinela, muestras procesadas, positivas, negativos, positividad, semana,
hospital/laboratorio/unidad centinela, departamento (si existe), total nacional,
rango etario.

La unidad de observación y la granularidad se anotan; no se convierten
porcentajes en conteos ni se infiere un patógeno a partir de IRA.

## Corpus

Reutilizar `backend/ingestion/data/raw/minsal/{año}/` (datos, no código).
Años históricos conocidos: 2018, 2019, 2021, 2022, 2023. **2020 no se excluye
por copiar la regla de dengue/IRA**: si la carpeta existe, se recorre; si no,
se documenta. 2024+ queda fuera de esta rama.

## Estados de auditoría

Reutilizar semántica ya existente, no inventar una docena de estados:

| Estado | Cuándo |
|---|---|
| `ok` | Tabla extraída y usable |
| `ok_discrepancia_minima` | Cuadre con diferencia ±1–3 del propio boletín; celdas conservadas |
| `ausencia_esperada_vacacion` | Vacaciones / vigilancia intensificada, sin tabla de la sección |
| `sin_texto_extraible` | El documento no menciona la sección en texto extraíble |
| `sin_filas_sospecha_imagen` | Título presente, 0 filas extraíbles |
| `revision_manual` | Reimpresión, semana ilegible, o no cuadra |
| `error_extraccion` | Fallo al abrir el PDF o extracción incompleta |

## Desacumulación (solo si la fuente es acumulada)

```
valor_semana_t = acumulado_t - acumulado_t-1
```

Hueco entre cortes → sin dato. Primer corte tardío → acumulado parcial, no
dividir. Diff negativo → corrección retroactiva, excluir (nunca clampear a 0).
Reimpresión idéntica → `revision_manual`. Salto de varias semanas → no repartir.

## Qué no hace esta corrida

No persiste, no migra esquema, no instala OCR, no fabrica celdas, no mezcla
Neumonías con IRA, no trata positividad como casos, no descarga 2024+.

## Cómo ejecutar

```text
cd backend
.venv/bin/python ingestion/corrida_respiratorios.py
.venv/bin/python ingestion/corrida_respiratorios.py --solo-neumonias
.venv/bin/python ingestion/corrida_respiratorios.py --solo-virus
.venv/bin/python ingestion/corrida_respiratorios.py --limite 10
.venv/bin/python -m pytest ingestion/tests/test_corrida_respiratorios.py
```
