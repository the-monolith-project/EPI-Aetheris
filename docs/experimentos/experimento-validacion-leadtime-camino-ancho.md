# Experimento: validación empírica del lead time del "Camino Ancho" (2026-08-18)

> Registro del experimento y su resultado, para no reintentarlo sin una hipótesis distinta. Es un
> diagnóstico exploratorio -- no cambia producción. No escribe a Postgres, no toca FastAPI ni el
> frontend, no modifica el esquema. Scripts: `backend/ingestion/validar_leadtime_camino_ancho.py`,
> `backend/ingestion/inicio_temporada_departamental.py` (auxiliar, calcula el inicio de temporada real
> a nivel departamental, que no existía en el repositorio antes de este experimento).

## Motivación

La propuesta "Camino Ancho" (`EPI-Aetheris_Camino_Ancho_v2_ajustada.md`, sección 1) reemplaza el
clasificador interanual descartado por un índice de idoneidad biofísica (Iv) más un detector de
anomalías estacionales, con una tesis de valor explícitamente marcada como **hipótesis no medida**:
que ese índice anticiparía el ascenso real de casos con semanas de margen frente al MINSAL. El propio
documento (sección 1, Módulo 2 [AJUSTE]) exige correr esta validación retrospectiva antes de
comunicar cualquier cifra de lead time. Este experimento la ejecuta.

## Qué NO se hizo (alcance explícito)

- No se construyó ningún endpoint de FastAPI ni se tocó el frontend.
- No se modificó el esquema de Postgres.
- Los parámetros biofísicos se usaron exactamente como "calibración inicial a verificar" (palabras
  del documento), nunca como si estuvieran validados.
- No se descartó ni "arregló" ningún departamento-año sin señal -- se reportan igual que los que sí
  muestran anticipación.

## Metodología

### 1. Datos usados

Clima ERA5-Land departamental 2014-2024 (14 departamentos × 7 variables ya cargadas, cobertura
completa verificada: 14 × 7 × semanas-del-año, sin huecos). Casos MINSAL departamentales 2018-2023
(`probable` + `confirmado` sumados; 2020 no existe en la tabla departamental -- nunca se descargó, no
es una exclusión de este experimento). Años evaluados: **2018, 2019, 2021, 2022, 2023** -- los mismos
que ya usa `corrida_canal_endemico_nacional.py` y la única ventana con datos MINSAL departamentales.

### 2. Índice de idoneidad (Iv)

Fórmulas tomadas literalmente del documento, sección 4, Módulo 1:

- `f_T(T) = max(0, c · T · (T−Tmin) · √(Tmax−T))`, Tmin=16°C, Tmax=38°C. `c` no es un número del
  documento -- se resolvió numéricamente (grid fino) para que `max(f_T)` en `[Tmin,Tmax]` = 1:
  **c = 0.000795**.
- `f_R(R) = 1 / (1 + e^(−k·(R−R0)))`, R0=30 mm/semana, k=0.1, sobre precipitación acumulada a 2
  semanas (semana actual + anterior; sin envolver entre años, semana 1 usa solo su propio valor).
- `Iv = f_T(T) × (0.3 + 0.7·f_R(R)) × f_H(HR)`.
- **`f_H(HR)` -- estimación propia del equipo, NO citada, marcada así explícitamente**: el documento
  solo especifica "penaliza humedad relativa bajo 50%", sin fórmula, y autoriza expresamente marcar
  como estimación propia lo que no esté trazado a Mordecai et al. Se usó una rampa lineal simple:
  `f_H(HR) = min(1, max(0, HR/50))`. Es la forma funcional más simple que cumple el requisito
  cualitativo del documento; no se inventó una logística o gaussiana que el documento no pedía.

**Chequeo de cordura (obligatorio antes de seguir, sección 4 paso 2):** sobre 8.036 observaciones
reales (departamento-semana, 2014-2024), Iv tiene media 0,450, mediana 0,387, desviación 0,224, rango
[0,027, 0,923]. Distribución con masa en casi todos los deciles (histograma completo en el script), no
degenerada. **El script aborta con `SystemExit` si la distribución sale constante o saturada en 0/1
-- no ocurrió.** Se continuó.

### 3. Baseline y detector de anomalías

Mediana y desviación de Iv por (departamento, semana-del-año), *leave-one-out*: pool = los 10 años
restantes del corpus 2014-2024 (excluye el año evaluado de su propio baseline, mismo principio que
`corrida_canal_endemico_nacional.py` aplica a casos), misma semana exacta -- **sin ventana de semanas
vecinas** (el documento no la pide para Iv, a diferencia del canal endémico de casos). Z-score de cada
semana real contra ese baseline. Alerta = Z ≥ 1,5 durante dos semanas consecutivas (criterio literal
del documento). Semana de detección = primera alerta cronológica del año.

### 4. Inicio de temporada real

**Nacional:** se reutiliza sin recalcular el corte P75 ya cerrado de `corrida_canal_endemico_nacional.py`
(esquema P50/P75, ventana ±1, años base 2018/2019/2021/2022/2023, piso 12 obs/≥3 de 4 años). Inicio =
primera semana con suficiencia y valor > P75 propio.

**Departamental:** no existe un corte cerrado a nivel departamental (confirmado por inspección directa
del código antes de empezar: `corrida_canal_endemico_nacional.py` filtra `r.codigo = 'SV'`
explícitamente; `corrida_canal_endemico_4zonas.py` reutiliza esa misma serie nacional sin tocarla).
Extensión acordada con el coordinador, no inventada aquí: de los 14 departamentos, se calificó cada
uno por volumen de casos y suficiencia relajada (≥3 de 5 años base con ≥8 semanas de actividad
no-cero). **Solo San Salvador (SV-SS) califica.** Los otros 13 quedan fuera de la validación
departamental -- no se les asignó ningún inicio de temporada. Detalle completo en
`inicio_temporada_departamental.py` y su CSV de calificación.

Para SV-SS, 2018 y 2019 dan inicio en semana 1 -- señal de pool disperso/degenerado (muy pocas
observaciones base), no una lectura confiable. Se reportan en la tabla completa pero **se excluyen
del cálculo de mediana/RIC departamental**, marcados aparte, no ocultos.

### 5. Agregado nacional de Iv

Para comparar contra el inicio de temporada nacional, se usó el **promedio simple no ponderado** de
Iv sobre los 14 departamentos por semana. No hay una decisión de ponderación poblacional cerrada en
el proyecto -- esto es un supuesto explícito de este experimento, no una convención ya establecida.

## Resultado: tabla completa (todos los años, incluidos los sin señal)

| Nivel | Código | Año | Semana alerta | Semana inicio real | Lead time (sem.) | Nota |
|---|---|---|---|---|---|---|
| Nacional | SV | 2018 | 15 | 44 | **+29** | |
| Nacional | SV | 2019 | — | 2 | — | sin alerta ese año |
| Nacional | SV | 2021 | — | 51 | — | sin alerta ese año |
| Nacional | SV | 2022 | — | 2 | — | sin alerta ese año |
| Nacional | SV | 2023 | 11 | — | — | nunca cruza P75 con suficiencia ese año |
| Departamental | SV-SS | 2018 | 15 | 1 | −14 | inicio en semana 1, ver nota metodológica arriba |
| Departamental | SV-SS | 2019 | — | 1 | — | inicio en semana 1, sin alerta |
| Departamental | SV-SS | 2021 | — | 19 | — | sin alerta ese año |
| Departamental | SV-SS | 2022 | — | 16 | — | sin alerta ese año |
| Departamental | SV-SS | 2023 | 36 | 6 | **−30** | |

CSV completo: `backend/ingestion/data/interim/leadtime_camino_ancho/leadtime_resultados.csv`.

## Cifras de control

**Máximo Z alcanzado por año** (para entender si "sin alerta" significa que el detector no vio nada,
o que vio algo pero no dos semanas seguidas):

| Nivel | Año | Máx. Z (umbral=1,5) |
|---|---|---|
| Nacional | 2018 | 3,63 |
| Nacional | 2019 | 1,38 |
| Nacional | 2021 | 3,52 |
| Nacional | 2022 | 1,73 |
| Nacional | 2023 | 4,42 |
| Departamental | 2018 | 3,24 |
| Departamental | 2019 | 4,95 |
| Departamental | 2021 | 2,15 |
| Departamental | 2022 | 3,41 |
| Departamental | 2023 | 3,84 |

**Todos los años, sin excepción, alcanzan Z ≥ 1,5 en algún momento** -- el umbral de anomalía no es
raro, es rutinario. Lo que decide si hay "alerta" o no es casi siempre el requisito de **dos semanas
consecutivas**, no la ausencia de anomalías. Esto es un hallazgo relevante por sí solo: el detector
tal como está especificado es ruidoso -- ve señales frecuentes que no se sostienen dos semanas
seguidas, más que un precursor limpio y raro del ascenso de casos.

Mediana y RIC del lead time, sobre los casos con alerta Y con inicio real (los únicos comparables):

- **Nacional:** 1 de 5 años tiene ambos valores. Mediana = 29,0 semanas, RIC = [29,0, 29,0].
- **Departamental (SV-SS, excluidos 2018/2019 por el motivo ya explicado):** 1 de 3 años tiene ambos
  valores. Mediana = −30,0 semanas, RIC = [−30,0, −30,0].

## Conclusión honesta

**No se sostiene la tesis de una ventana de anticipación medible y consistente.** No es un resultado
ambiguo por falta de casos favorables aislados -- es la ausencia casi total de casos comparables, y
los dos que sí existen apuntan en direcciones opuestas:

- A nivel nacional, el único año con alerta y con inicio de temporada real (2018) da un "lead time" de
  +29 semanas -- más de la mitad del año. Un solo dato no permite afirmar que el detector se adelanta
  consistentemente; ese número tan grande sugiere coincidencia (el detector disparó temprano en el
  año por razones climáticas propias, no porque anticipara ese ascenso específico) más que señal real.
- A nivel departamental, el único año comparable (SV-SS 2023) da **−30 semanas**: el detector llegó
  muy tarde, no temprano.
- En 3 de 5 años nacionales y en 3 de 5 años departamentales, **el detector simplemente no disparó
  ninguna alerta**, pese a que el Z-score sí cruzó 1,5 en algún momento en absolutamente todos los
  años -- el criterio de "dos semanas consecutivas" filtra casi toda la señal detectada.
- En 1 año nacional (2023) el propio inicio de temporada real es indefinido (el año nunca cruza su
  propio P75 con suficiencia), lo cual también limita cuántos años son evaluables en absoluto.
- La extensión departamental deja **13 de 14 departamentos completamente fuera** de esta validación
  por falta de suficiencia en los datos MINSAL -- el resultado departamental descansa en un único
  departamento, con solo un año utilizable después de excluir los dos años degenerados.

Con esta base (2 pares de alerta+inicio real comparables en total, uno de cada nivel, sin acuerdo de
signo entre ellos), **no hay evidencia suficiente para afirmar ni refutar con confianza una ventana de
anticipación real** -- lo único defendible es que **no hay evidencia que la sostenga**, que es
justamente lo que había que saber antes de construir tres semanas de infraestructura sobre esa
premisa.

## Decisión que esto desbloquea

Según el propio documento (sección 1 y "Qué decisión desbloquea esto" de la tarea): la tesis de
"ventana de anticipación" **se retira del pitch y del informe**. El resto del Camino Ancho --
idoneidad biofísica, detector de anomalías como herramienta descriptiva, indicador de presión relativa
e índice de confianza de vigilancia -- sigue siendo válido por sí solo, tal como el documento ya lo
contemplaba como plan B (sección 1, Módulo 3: "Mientras el lead time no esté validado... se presenta
como información descriptiva, no como instrucción de despacho"). Este resultado no invalida esos
módulos; invalida específicamente el número de semanas de anticipación como cifra comunicable.

## Limitaciones de este experimento (para no repetirlas sin avisar)

- El agregado nacional de Iv es un promedio simple sin ponderación poblacional -- una decisión no
  cerrada en el proyecto, hecha aquí solo para tener un valor comparable contra el canal endémico
  nacional.
- `f_H(HR)` es una estimación propia no citada (ver metodología) -- si se reemplaza por una forma
  distinta (logística, curva citada de literatura), estos números cambian y habría que rehacer esta
  corrida, no ajustar el resultado a mano.
- El baseline de Iv no usa ventana de semanas vecinas (el documento no la pidió); el canal endémico de
  casos sí la usa. Son dos convenciones distintas coexistiendo en este experimento, no un error --
  pero si se homogeniza en el futuro, este resultado también debería rehacerse.
- La muestra utilizable es extremadamente pequeña (5 años nacionales, 1 departamento). Cualquier
  cifra puntual de este experimento (incluida la mediana reportada) descansa en n=1 por nivel y no
  debe presentarse como una estadística robusta.
