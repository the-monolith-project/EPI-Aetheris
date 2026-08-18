# Protocolo de evaluación — Vía −1 del rescate de predicción

**Estado:** Propuesto, no aprobado

**Versión:** 2, definición completa

**Fecha de revisión:** 2026-08-18

**Bloquea:** Vías 0–3 de `tarea-rescate-prediccion.md`

**Aprobación requerida:** Eduardo (0V3R)

Este documento define de forma completa la **Vía −1: congelar y verificar una validación limpia**.
No cambia producción, no busca mejorar métricas y no autoriza por sí mismo ningún experimento. Su
producto es un procedimiento reproducible que permite distinguir evidencia prospectiva de una
comparación retrospectiva.

La respuesta de Eduardo en `respuesta-protocolo-evaluacion.md` resolvió D1–D4 en principio, pero sigue
pendiente de firma y fue redactada sin disponer de esta definición completa. La sección 15 identifica
qué partes son compatibles y cuál debe corregirse antes de aprobar el protocolo.

## 1. Qué es y qué no es la Vía −1

### Objetivo

La Vía −1 determina si las métricas de las Vías 0–3 pueden interpretarse como evidencia fuera de
muestra. Para ello congela:

- qué datos puede ver cada fold;
- cómo se construye cada etiqueta;
- cómo se construyen los predictores;
- qué años sirven para desarrollo y evaluación externa;
- dónde puede ocurrir selección de configuración;
- qué métricas y referencias se reportan;
- qué pruebas deben demostrar la ausencia de fuga.

### No es un experimento de rescate

La Vía −1:

- no selecciona el año que produzca mejores resultados;
- no cambia P75/P90, la ventana ±1 ni el piso de suficiencia;
- no agrega casos previos, países, ONI ni features nuevas;
- no barre umbrales;
- no modifica los scripts ni artefactos de producción;
- no escribe en PostgreSQL;
- no puede convertir una corrida histórica contaminada en prospectiva.

Si al aplicar este protocolo un fold queda sin clases suficientes o sin filas, se reporta como
`no entrenable` o `no evaluable`, según corresponda. No se cambia el protocolo para rescatarlo.

## 2. Problema que corrige

El pipeline histórico construye las etiquetas sobre una lista fija de años y después separa el año de
prueba. El año etiquetado no entra en su propia línea base, pero todavía ocurren dos contaminaciones:

1. el año externo puede participar en los percentiles usados para etiquetar filas de entrenamiento;
2. una evaluación de un año antiguo puede entrenar con años posteriores.

Por ello, esas corridas son retrospectivas *leave-one-year-out*. Sirven para reproducir el diagnóstico,
pero no para estimar anticipación prospectiva.

El script `backend/ingestion/diagnostico_senal_etiqueta_auditable.py` conserva deliberadamente ese
protocolo legado. La Vía −1 se implementará en un script experimental separado.

## 3. Alcance exacto de esta definición

La primera implementación de la Vía −1 se limita a:

- El Salvador, nivel nacional;
- dengue;
- casos semanales de OpenDengue Admin0, `clasificacion='total'`;
- predictor únicamente climático;
- etiqueta de canal endémico P75/P90;
- Random Forest como modelo de referencia;
- años epidemiológicos completos como unidad de separación.

No convierte una clasificación nacional en riesgo departamental. Una aplicación multipaís,
departamental o con otra etiqueta deberá declarar sus propias unidades de agrupación y demostrar la
misma independencia temporal; no queda aprobada automáticamente por este documento.

## 4. Fuentes y foto reproducible de datos

La fuente canónica de la corrida es `db/seed/seed_datos_reales.sql`, con su SHA-256 registrado antes de
ejecutar. La base local puede utilizarse solamente si las tablas y filas consumidas corresponden a esa
foto; cualquier diferencia debe registrarse y la corrida deja de ser comparable hasta explicarla.

### Variable objetivo

- Tabla lógica: `casos_epidemiologicos`.
- Región: código `SV`, nivel nacional.
- Fuente: `opendengue_v1_3`.
- Clasificación: `total`.
- Resolución: semana epidemiológica OPS/CDC.
- Cobertura de casos disponible para construir historia: completa desde 2014 y disponible hasta 2024
  en la foto actual.

Los casos solo construyen la etiqueta. No entran como predictor en esta vía.

### Predictores

Las siete variables climáticas vigentes son:

- `temp_max`;
- `temp_min`;
- `temp_media`;
- `humedad_relativa_media`;
- `punto_rocio`;
- `precipitation_sum`;
- `precipitation_hours`.

Cada variable se agrega a nivel nacional mediante el promedio simple de los 14 departamentos, según
la decisión cerrada vigente. La cobertura climática de la foto actual es 2018–2024; no se asumirá que
existe clima anterior porque sí existan casos anteriores.

### Calendario y faltantes

El orden temporal se toma de `semanas_epidemiologicas.fecha_inicio`, no de ISO 8601 ni de ordenar
ingenuamente `(año, semana)`. Se respetan años de 51, 52 o 53 semanas.

No se fabrican, interpolan ni convierten a cero observaciones ausentes. Una fila sin la historia
necesaria para su etiqueta o sus predictores se excluye con un motivo contabilizado. No se elimina el
año completo ni se sustituye la observación.

## 5. Definiciones formales

Sea `t` el año externo de un fold, `y` un año objetivo de entrenamiento y `w` una semana
epidemiológica.

### Historia permitida

La historia de casos permitida para etiquetar un año `y` es:

```text
H(y) = todos los años observados r tales que r < y y r no esté excluido formalmente
```

La ventana es **expansiva**, no una ventana móvil de cuatro años. Por ejemplo, si 2020 queda excluido:

```text
H(2018) = {2014, 2015, 2016, 2017}
H(2019) = {2014, 2015, 2016, 2017, 2018}
H(2021) = {2014, 2015, 2016, 2017, 2018, 2019}
```

La historia de `y` no depende del fold externo que posteriormente use esa fila. La etiqueta de 2018,
por ejemplo, debe ser idéntica en los folds externos 2019, 2021, 2022, 2023 y 2024.

### Pool de la etiqueta

Para la celda `(y, w)`, el pool contiene, por cada `r` en `H(y)`, las observaciones realmente presentes
en las semanas `w-1`, `w` y `w+1` de `r`.

- La ventana ±1 **no envuelve entre años**: la semana 1 no toma la última semana del año anterior y la
  última semana no toma la semana 1 del siguiente.
- El año `y` nunca participa en su propio pool.
- Un año posterior a `y` nunca participa en el pool.
- Se cuentan observaciones presentes, no observaciones esperadas.
- La celda requiere al menos 12 observaciones y presencia de al menos 3 años históricos.
- Si no alcanza ambos pisos, la celda queda sin etiqueta y se registra como
  `sin_suficiencia_etiqueta`.

El piso de 12 hace que normalmente se necesiten por lo menos cuatro años históricos en semanas
interiores. En los bordes del año pueden necesitarse más, porque la ventana no cruza años.

### Percentiles y clase

Los percentiles usan interpolación lineal inclusiva. Para el pool ordenado `x` de tamaño `n` y un
percentil `p`:

```text
posición = p × (n − 1)
Q(p) = interpolación lineal entre x[floor(posición)] y x[ceil(posición)]
```

La etiqueta se asigna con comparaciones estrictas:

```text
alto  si casos(y, w) > P90
medio si casos(y, w) > P75 y casos(y, w) <= P90
bajo  si casos(y, w) <= P75
```

La igualdad con un corte queda en la clase inferior. P75/P90, ventana ±1 y los dos pisos permanecen
congelados durante toda la Vía −1.

## 6. Construcción de predictores sin información futura

Para cada semana objetivo se calculan 21 predictores: por cada una de las siete variables climáticas,
rezago 1, rezago 2 y media de las cuatro semanas anteriores.

- Ningún predictor incluye la semana objetivo.
- Los rezagos sí cruzan el límite de año siguiendo `fecha_inicio`; esta continuidad climática es
  distinta de la ventana de la etiqueta, que no cruza años.
- La media móvil usa exactamente las cuatro semanas anteriores y no una cantidad menor.
- Si falta cualquiera de los 21 valores, la fila se excluye como `sin_historia_climatica`.
- No se usa el número de casos, el total anual ni una etiqueta previa como predictor.

Si una vía posterior agrega o transforma features, debe congelar esa definición antes de ejecutarse.
Cualquier escalado, imputación o selección aprendida debe ajustarse solo con el entrenamiento del fold
correspondiente. La configuración de referencia de la Vía −1 no agrega esas transformaciones.

## 7. Folds externos prospectivos

Para un fold externo `t`:

1. se construyen las etiquetas de cada año objetivo `y < t` únicamente con `H(y)`;
2. se conservan como entrenamiento solo las filas completas de esos años objetivo;
3. la etiqueta externa de `t` se construye únicamente con `H(t)`;
4. ninguna fila de `t` entra en entrenamiento, transformaciones o selección;
5. ningún año posterior a `t` puede aparecer en ningún rol;
6. el modelo se ajusta con la configuración ya congelada;
7. `t` se evalúa una sola vez para esa configuración.

Con la cobertura y exclusión de 2020 propuestas, la matriz de folds es:

| Año externo `t` | Años objetivo que pueden entrenar | Uso permitido |
|---|---|---|
| 2019 | 2018 | Desarrollo retrospectivamente observado |
| 2021 | 2018, 2019 | Desarrollo retrospectivamente observado |
| 2022 | 2018, 2019, 2021 | Desarrollo; resultados ya observados |
| 2023 | 2018, 2019, 2021, 2022 | Desarrollo; resultado de producción ya observado |
| 2024 | 2018, 2019, 2021, 2022, 2023 | Externo reservado, con soporte de clases ya inspeccionado |

Los folds 2019–2023 permiten evaluar el mecanismo forward-chaining, pero no son tests finales
intactos: sus resultados ya influyeron directa o indirectamente en el diagnóstico del proyecto.
También se conoce anticipadamente que 2024 no tendría semanas `alto` bajo el cálculo preliminar de
Eduardo; esa tabla todavía debe reproducirse con la fuente canónica y con esta construcción
prospectiva.

2018 es el primer año que puede etiquetarse con el piso vigente, pero no puede ser año externo de un
modelo prospectivo porque no existe un año objetivo anterior y etiquetable con el cual entrenar. No
hay folds externos válidos anteriores a 2019 bajo esta definición.

### Estados de un fold

- `entrenable`: contiene filas de entrenamiento y por lo menos dos clases reales.
- `entrenable_con_clase_ausente`: contiene por lo menos dos clases, pero falta una de las tres; se
  ejecuta como diagnóstico y la ausencia se declara, sin atribuir capacidad para aprender esa clase.
- `no_entrenable`: no contiene filas o todas pertenecen a una sola clase.
- `recall_alto_no_evaluable`: el externo contiene cero filas reales `alto`; las demás métricas se
  conservan.

Estos estados se determinan antes de ajustar el modelo y nunca justifican cambiar o descartar el fold.

### Por qué 2016 no es un fold de la Vía −1

2016 no puede utilizarse como segundo año externo prospectivo con los datos y pisos actuales:

- `H(2016)` solo contiene 2014 y 2015, insuficientes para alcanzar 12 observaciones en una ventana ±1;
- la foto actual no contiene predictores climáticos para 2016.

Las seis semanas `alto` informadas por Eduardo se obtuvieron etiquetando 2016 contra el pool fijo de
producción, que contiene años futuros respecto de 2016. Esa cifra puede conservarse como análisis
retrospectivo, pero no como resultado de la Vía −1. Incorporar 2016 exigiría otra fuente real de clima,
más historia real de casos y una nueva aprobación; no se bajará el piso para habilitarlo.

## 8. Folds internos y selección

La Vía −1 de referencia **no ajusta hiperparámetros, features ni umbral**. Ejecuta la configuración
congelada de la sección 9 para auditar el protocolo.

Cuando una Vía 0–3 necesite selección, deberá adjuntar antes de correr:

- lista cerrada de configuraciones candidatas;
- métrica de selección y desempate;
- folds internos disponibles;
- regla aplicable si un fold no es entrenable;
- condición de aceptación ya aprobada.

Los folds internos también son forward-chaining por años completos. Para validar internamente en un
año `v`, solamente pueden entrenar años objetivo anteriores a `v`, cuyas etiquetas se construyeron
con sus respectivas historias `H(y)`. Nunca se dividen aleatoriamente semanas del mismo año.

Si hay menos de dos años de validación interna utilizables, no se selecciona nada: se conserva la
configuración predefinida. Los resultados internos se agregan mediante la regla escrita antes de
correr; no se elige el fold más favorable.

El año externo no puede modificar la lista de candidatos, la métrica, el desempate ni la configuración
elegida. Alterar únicamente sus casos o clima debe dejar intacta toda selección interna.

## 9. Configuración de referencia congelada

La corrida de validación de la Vía −1 utiliza:

- Random Forest;
- 300 árboles;
- `class_weight="balanced"`;
- predicción por `.predict()`, equivalente al argmax de clases en esta configuración;
- siete variables climáticas;
- rezagos 1 y 2;
- media móvil de 4 semanas;
- P75/P90;
- ventana de etiqueta ±1;
- piso de 12 observaciones y 3 años históricos;
- semillas 0–9 para estabilidad;
- semilla 42 solamente como referencia comparable con el diagnóstico histórico.

Cada semilla usa exactamente los mismos folds, etiquetas y filas. Las semillas miden aleatoriedad del
algoritmo, no incertidumbre entre años, y no se presentan como muestras epidemiológicas independientes.

No se barren umbrales sobre la etiqueta actual. Una vía que cambie el objetivo solo podrá solicitar
esa reapertura bajo las condiciones de D4 y antes de mirar su año externo.

## 10. Referencias y criterio de interpretación

Cada fold reporta cuatro referencias, calculadas sin información posterior al año externo:

1. **Climatológica:** clase modal por semana epidemiológica entre las filas de entrenamiento; si una
   semana no existe allí, moda global del entrenamiento.
2. **Constante mayoritaria:** clase más frecuente en el entrenamiento completo.
3. **Siempre `alto`:** predice `alto` en todas las filas, como control de cordura.
4. **Persistencia:** etiqueta real de la semana inmediatamente anterior del año externo; referencia
   retrospectiva no desplegable. Una fila sin semana anterior contigua se excluye solo de esta
   referencia y se contabiliza.

Los empates de la climatológica se resuelven primero por la clase más frecuente en todo el
entrenamiento y, si persisten, por el orden fijo `bajo`, `medio`, `alto`. La constante mayoritaria usa
ese mismo orden fijo si hay empate global. Esta regla se guarda en el manifiesto y se prueba
automáticamente.

El criterio formal actualmente registrado sigue siendo superar a la climatológica en F1 macro y
recall de `alto`, por año evaluable para recall. Si Eduardo firma y registra D3, se aplicará además el
veto siguiente: un resultado no puede contarse como éxito si cualquiera de los dos predictores
constantes supera al modelo en F1 macro. Persistencia y las constantes se reportan, pero no se
convierten en umbrales adicionales.

Un año con cero semanas `alto` no puede confirmar ni refutar la parte del criterio basada en recall.
Permanece en la tabla para F1 macro, precisión, clases `bajo`/`medio` y falsos positivos de `alto`.

Las métricas de varios años no se promedian para sustituir el criterio por año. La Vía −1 queda
validada cuando demuestra reproducibilidad e independencia temporal, aunque el modelo falle. El éxito
predictivo del modelo es una conclusión distinta y, mientras no exista un test intacto y evaluable,
solo puede reportarse como exploratoria.

## 11. Métricas obligatorias

Las clases se fijan en el orden `bajo`, `medio`, `alto`, aunque alguna tenga soporte cero. Por año
externo y por semilla se guardan:

- F1 macro sobre las tres clases, con `zero_division=0`;
- precisión, recall, F1 y soporte por clase;
- recall de `alto` como proporción y como `X aciertos de Y`, o `N/A` si `Y = 0`;
- matriz de confusión completa 3×3;
- falsos positivos de `alto`, especialmente cuando su soporte real sea cero;
- distribución real y predicha;
- AUC ROC y curva precisión-recall para `alto` frente al resto solo si hay positivos y negativos;
- métricas equivalentes de las cuatro referencias;
- resultados individuales de las semillas y resumen de estabilidad, sin ocultar semillas adversas.

También se registra el número de celdas descartadas por falta de etiqueta, clima, clase o continuidad.
No se promedian silenciosamente años ni se sustituye `N/A` por cero.

## 12. Artefactos y trazabilidad

La implementación deberá vivir, como mínimo, en rutas separadas de producción:

- `backend/ingestion/validar_via_menos_uno.py` — implementación experimental;
- `backend/ingestion/tests/test_validar_via_menos_uno.py` — independencia y reglas temporales;
- `docs/corrida-via-menos-uno.md` — informe reproducible cuando se autorice la corrida.

Cada ejecución escribe únicamente bajo `backend/ingestion/data/interim/via_menos_uno/`, carpeta no
versionada, y produce:

- manifiesto JSON con parámetros congelados;
- SHA-256 del seed y del script;
- versiones de Python, NumPy y scikit-learn;
- años y número de filas en cada rol;
- distribución de etiquetas por año;
- etiquetas y cortes por fila;
- predicciones y probabilidades por fila y semilla;
- métricas JSON;
- log de ejecución.

Se versionan el código, las pruebas y el informe resumido. No se versionan modelos, datasets
intermedios ni salidas voluminosas salvo decisión explícita posterior.

## 13. Pruebas obligatorias contra fuga

Antes de cualquier corrida de las Vías 0–3 deben existir pruebas automáticas que demuestren:

1. cambiar casos del año externo no modifica etiquetas ni matrices de entrenamiento;
2. cambiar clima del año externo no modifica features, transformaciones ni matrices de entrenamiento;
3. cambiar datos posteriores al año externo no modifica ninguna parte del fold;
4. ningún año igual o posterior al objetivo aparece en `H(y)`;
5. la etiqueta de un año no usa ese mismo año;
6. la etiqueta de un año es idéntica en todos los folds externos que la reutilizan;
7. la ventana ±1 de la etiqueta no cruza el año y respeta observaciones ausentes;
8. los rezagos climáticos sí cruzan años de 51, 52 o 53 semanas usando el calendario real;
9. un faltante no se convierte en cero ni se imputa silenciosamente;
10. un año sin `alto` conserva F1 macro y falsos positivos, con recall `N/A`;
11. la configuración elegida internamente no cambia al alterar solo el externo;
12. 2016 es rechazado como fold prospectivo con la cobertura actual.

Además de pasar con la implementación correcta, las pruebas de independencia deben **verse fallar**
contra una mutación deliberadamente contaminada que introduzca el año externo en una etiqueta de
entrenamiento. El procedimiento, la prueba que falló y su salida se registran en el informe; después se
revierte la mutación y se conserva únicamente la implementación limpia.

## 14. Condiciones que invalidan una corrida

Una corrida no puede presentarse como evidencia prospectiva si ocurre cualquiera de estas condiciones:

- el año externo o un año posterior participa en etiquetas de entrenamiento;
- se entrena con un año posterior al evaluado;
- se mezclan semanas de un mismo año mediante split aleatorio;
- se elige año, feature, hiperparámetro, umbral o semilla mirando el externo;
- se cambia el criterio después de observar resultados;
- se descarta un año o semilla porque empeora la tabla;
- se modifica P75/P90, la ventana o los pisos sin aprobación previa;
- se llama prospectivo al resultado de 2016 calculado contra años futuros;
- se fabrican o imputan datos no observados;
- no se puede identificar el seed, código o configuración ejecutados;
- se sobrescribe un artefacto de producción o se escribe en la base.

La corrida puede conservarse como diagnóstico retrospectivo si se etiqueta claramente y se explica
la causa de invalidez. No se mezcla en la tabla prospectiva.

## 15. Compatibilidad con la respuesta de Eduardo

| Decisión | Compatibilidad con esta definición | Acción antes de aprobar |
|---|---|---|
| D1 — excluir 2020 de objetivo y pool | Compatible para la Vía −1 nacional | Firmar y registrar el cambio de alcance donde corresponda |
| D2 — 2024 externo | Compatible, pero su soporte debe recalcularse con `H(2024)` y la fuente canónica | Reproducir la tabla y declarar que no existe test intacto y evaluable a la vez |
| D2 — 2016 segundo externo | **Incompatible** con la Vía −1 | Retirarlo del protocolo prospectivo o reclasificarlo explícitamente como retrospectivo |
| D3 — cuatro referencias y veto de constantes | Compatible | Firmar y registrar el veto antes de aplicarlo |
| D4 — argmax fijo | Compatible | Firmar; cualquier reapertura futura requiere un anexo por vía |

La tabla preliminar de D2 se construyó contra el pool fijo de producción. Esta Vía −1 utiliza una
historia distinta para cada año, por lo que esa tabla no valida la distribución prospectiva salvo para
los casos en que ambos pools coincidan. No se copiarán sus cifras al informe sin reproducción.

## 16. Puerta para comenzar las Vías 0–3

No comienza ningún experimento hasta que:

- Eduardo confirme por escrito que recibió esta definición completa;
- D1–D4 estén firmadas y D2 corregida respecto de 2016;
- la tabla D2 se reproduzca con el seed y `H(t)`;
- D1 y D3 estén registrados formalmente si modifican decisiones cerradas;
- los años externos queden congelados por escrito;
- exista la implementación separada de producción;
- todas las pruebas de independencia pasen;
- al menos una prueba se haya visto fallar ante la fuga deliberada documentada;
- el manifiesto de configuración esté congelado antes de ejecutar.

## 17. Registro de aprobación

- **Definición completa de la Vía −1 recibida por Eduardo:** pendiente
- **D1 — 2020:** respuesta emitida, pendiente de firma y registro
- **D2 — años externos:** requiere corrección sobre 2016 y reproducción de cifras
- **D3 — referencias y veto:** respuesta emitida, pendiente de firma y registro
- **D4 — argmax:** respuesta emitida, pendiente de firma
- **Años externos congelados:** pendiente
- **Aprobado por:** pendiente
- **Fecha de aprobación:** pendiente
