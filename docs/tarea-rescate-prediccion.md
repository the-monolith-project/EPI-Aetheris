# Tarea: rescatar la capa de predicción de EPI-Aetheris

**Asignada a:** Isaac
**Coordinación y revisión:** Eduardo (0V3R)
**Ventana:** hasta el cierre del proyecto. Hay una fecha de corte obligatoria en la sección 8 — léela antes de empezar, no después.

---

## 1. Qué se te está pidiendo exactamente

El clasificador de riesgo no funciona. Tu tarea es intentar que funcione, o determinar con evidencia que no se puede y dejar documentado por qué.

Las dos salidas son aceptables. **La única salida inaceptable es un modelo que parezca funcionar sin funcionar.** Eso incluye cualquier cosa que se vea bien en una tabla porque se eligió la configuración después de ver el resultado. Si en algún momento te encuentras pensando "con este año de prueba sale mejor", detente: acabas de cruzar la línea.

Eduardo te va a revisar contra este documento. No hay puntos por optimismo.

---

## 2. Qué está pasando, en términos concretos

El modelo predice riesgo semanal en tres clases (alto / medio / bajo) a partir de variables climáticas rezagadas. Entrena con 250 filas: la serie semanal nacional de casos de dengue de El Salvador para 2018, 2019, 2021, 2022 y 2023 (2020 está excluido a propósito porque la vigilancia se cayó en pandemia y los datos reflejan capacidad de reporte, no transmisión).

La etiqueta se construye por canal endémico: cada semana se compara contra un pool formado por esa
semana epidemiológica y sus semanas vecinas **±1** en los otros años base. Con cuatro años de
referencia, el pool nominal contiene 12 observaciones. Si el valor supera el percentil 90 del pool se
marca "alto"; si supera P75 pero no P90 se marca "medio"; en otro caso se marca "bajo". El año que se
etiqueta nunca entra en su propia línea base.

Resultado actual, en los dos años de prueba que tienen semanas "alto" reales:

| Año de prueba | F1 macro modelo | F1 macro línea base | Recall "alto" modelo | Recall "alto" base |
|---|---|---|---|---|
| 2019 | 0,102 | 0,102 | **0,000** | 0,000 |
| 2022 | 0,169 | 0,184 | **0,000** | 0,000 |

Cero. El modelo no identifica ni una sola semana de riesgo alto.

**La causa sustantiva ya tiene evidencia fuerte; no repitas los mismos experimentos sin una hipótesis
distinta.** La etiqueta correlaciona **0,955** con el total anual de casos. Es decir: en esta ventana
está dominada por "qué tan grande fue este año", más que por "qué está pasando esta semana". Eso no
elimina la obligación de auditar primero la validez del protocolo de evaluación: la Vía −1 de la
sección 6 es un prerrequisito, no una reapertura del diagnóstico sustantivo. Mira la distribución:

| Año | Casos anuales | Semanas "alto" |
|---|---|---|
| 2018 | 8.448 | 0 |
| 2019 | 27.470 | 28 |
| 2021 | 5.752 | 0 |
| 2022 | 16.542 | 22 |
| 2023 | 5.788 | 0 |

Solo 2 de 5 años contienen alguna semana "alto". Para la señal que domina la etiqueta, el tamaño de muestra efectivo no son 250 filas: son **5 años, con 2 ejemplos positivos**. Eso no permite estimar generalización de forma confiable aunque un método consiga ajustar las semanas observadas.

Y hay una razón de fondo, no solo estadística: el canal endémico condiciona por semana epidemiológica
(con ventana ±1), lo que elimina buena parte de la estacionalidad media y da mucho peso a la amplitud
interanual. El clima puede explicar estacionalidad y algunas anomalías interanuales, pero la amplitud
del brote también depende de serotipo, inmunidad acumulada, introducción del virus, movilidad y
control de vectores. Esas variables no están actualmente en el dataset del proyecto.

---

## 3. Lo que ya se probó y falló — no lo repitas

Seis intentos reportados. La ventana ampliada, ONI y multipaís ya tenían scripts o informes
versionados; umbral/AUC, comparación de algoritmos, pool no pareado y Vía 2 fueron recibidos y
reproducidos el 2026-08-17. Si tu propuesta se parece a alguno de estos, revisa primero su evidencia
antes de repetirlo:

1. **Ajustar el umbral de decisión** (predecir "alto" con probabilidad más baja). Se reportó un AUC de
   la probabilidad de "alto" contra el "alto" real de **0,23**. El artefacto recibido reprodujo AUC
   0,234 en 2019 y 0,231 en 2022. Bajar el umbral sí produce recall no nulo, pero no supera
   simultáneamente F1 macro y recall; ver la auditoría indicada abajo.
2. **Cambiar de algoritmo.** Se reportó recall 0,000 con RandomForest, GradientBoosting, ExtraTrees y
   regresión logística. La comparación fue recibida y reproducida con scikit-learn 1.5.1.
3. **Ampliar la ventana climática** (medias móviles de 8 y 12 semanas además de 4). Sin mejora, F1 peor.
4. **Agregar el índice ONI** (El Niño/La Niña) como predictor de la serie nacional. Sin mejora.
5. **Cambiar cómo se arma el pool de percentiles** (no parear por semana calendario). Ningún año supera.
6. **Entrenar con 15 países de las Américas y probar en El Salvador.** Falla en las 5 corridas evaluables y en las 11 semillas de cada una — 0 de 55, sin una excepción. El Salvador correlaciona apenas **+0,280** con la señal interanual compartida de la región: es el más desacoplado de 18 países (Colombia +0,952, Guatemala +0,908, Honduras +0,868). Un modelo regional perfecto explicaría alrededor del 8 % de su variación interanual.

También se probó ampliar la ventana de entrenamiento a 2014–2023. No se adoptó, y por un motivo que necesitas entender antes de proponer cualquier cambio de ventana: **al ampliar la línea base, el percentil relativo redefine "alto" para todo el histórico.** 2019 pasó de 28 semanas "alto" a 1 al agregar 2014 y 2015 al pool, porque esos años fueron aún más severos. Cualquier corrida anterior deja de ser comparable. Si tocas la ventana, todas tus tablas dejan de poder compararse con las de este documento — dilo explícitamente cuando lo hagas.

### Artefactos recibidos y auditados

Los cuatro análisis llegaron en un solo script bajo `docs/tobeer/`, con procedencia, JSON,
probabilidades por fila y log. Se verificó lo siguiente:

1. **Umbral/AUC:** recibido; AUC 0,234 en 2019 y 0,231 en 2022.
2. **Script de comparación de algoritmos**, con RandomForest, GradientBoosting, ExtraTrees y
   regresión logística: recibido; recall alto 0 en 2019 y 2022 para los cuatro.
3. **Pool no pareado:** recibido; no supera el criterio histórico en ningún año evaluable.
4. **Preliminar intraanual:** recibido; reproduce 6/10 en 2019, 10/10 en 2022 y 7/10 en 2023, además
   de 0/10 en 2018 y 2021.
5. **Salidas compactas:** recibidas y comparadas contra una reejecución con Python 3.11,
   scikit-learn 1.5.1 y el seed versionado. El JSON sustantivo coincidió y el CSV de probabilidades
   fue idéntico byte por byte.

La copia auditada que debe incluirse en el próximo commit está en
`backend/ingestion/diagnostico_senal_etiqueta_auditable.py`, con pruebas en
`backend/ingestion/tests/test_diagnostico_senal_etiqueta.py`. Procedencia, hashes, diferencias y
límites están en `docs/diagnostico-senal-etiqueta-auditoria.md`. Los archivos de `docs/tobeer/` son el
paquete de entrada y no sustituyen esas rutas permanentes.

---

## 4. Un problema del criterio que tienes que conocer

El criterio formal vigente dice: superar a la línea base climatológica en F1 macro **y** en recall de
la clase alta, en cada año de prueba evaluable para recall. Cualquier sustitución de ese criterio debe
aprobarse y registrarse antes de ejecutar nuevos experimentos; ver el cierre de esta sección.

La línea base climatológica predice la clase modal de cada semana calendario según los años de entrenamiento. En la práctica eso siempre resulta "bajo", así que **su recall de "alto" es 0,000 por construcción, siempre.** Consecuencia: un solo acierto aislado ya "supera" esa mitad del criterio.

Esto ya generó una lectura engañosa. En la corrida regional multipaís, tres de los seis años marcados como "SUPERA" corresponden a **un único acierto** (1 de 109, 1 de 140, 1 de 4). Y en 2024, donde el 65 % de las filas son "alto", el modelo obtuvo F1 macro 0,139 — mientras que un predictor trivial que dijera "alto" siempre habría obtenido 0,262 y recall 1,000. El modelo "superó" el criterio en el año donde fue peor que la respuesta más tonta posible.

**Regla de reporte que aplica a todo tu trabajo:** cada vez que reportes un recall, reporta al lado los
aciertos absolutos (`X de Y`). Reporta siempre estas referencias, pero no les apliques mecánicamente
el mismo criterio porque miden extremos distintos:

- la climatológica actual (clase modal por semana calendario);
- una constante de clase mayoritaria;
- una constante que predice siempre "alto", como control de cordura;
- persistencia autorregresiva (la clase de la semana anterior), como referencia retrospectiva no
  desplegable con las fuentes actuales.

La constante "siempre alto" tiene recall de alto = 1,000 por construcción; exigir superarla en recall
sería matemáticamente imposible. El criterio propuesto para aprobación antes de correr es:

- contra la climatológica: superar **F1 macro y recall de alto**;
- contra la constante mayoritaria: superar **F1 macro**; reportar recall de alto como contexto;
- contra "siempre alto": superar **F1 macro y precisión de alto**; su recall solo se reporta como el
  extremo trivial 1,000;
- contra persistencia: reportar la comparación completa, pero declarar que resuelve una tarea
  retrospectiva distinta y usa información que el modelo solo-clima no tiene disponible.

Un año con cero semanas `alto` no es completamente "no evaluable": su recall de alto es `N/A`, pero
sí se evalúan F1 macro, precisión, falsos positivos y las líneas base.

**Puerta de gobernanza:** este criterio ampliado todavía no sustituye por sí solo la decisión cerrada
en `docs/contexto/01-decisiones-cerradas.md`. Antes de la primera corrida, Eduardo debe aprobarlo y
el cambio debe quedar registrado formalmente en `01-decisiones-cerradas.md` y en
`docs/contexto/CHANGELOG.md`; si quedan alternativas sin resolver, se registran primero en
`02-decisiones-abiertas.md`. Sin ese registro, sigue aplicando el criterio formal vigente.

---

## 5. Reglas que no puedes romper

Son estatutos del proyecto. No están a discusión y romperlos invalida el trabajo completo, no solo la parte afectada.

- **Nunca fabriques, simules ni sintetices datos.** Ni para probar, ni para completar un hueco, ni para una demo. Si falta dato, el resultado es "falta dato".
- **Nada de APIs pagadas ni servicios con cuota de pago.** El costo de replicación para un tercero tiende a cero.
- **Nunca elijas nada mirando el año de prueba.** Umbrales, hiperparámetros, features, corte de percentil: todo se elige con validación *dentro* de los años de entrenamiento. Si eliges viendo el resultado del año de prueba, ese resultado ya no vale y no hay forma de arreglarlo después.
- **Nunca reportes un resultado de una sola semilla.** Mínimo 10 semillas, y reporta en cuántas se sostiene. Un resultado que aparece con una semilla y desaparece con otra no es un resultado. Y ten claro que 10 semillas miden la variabilidad del algoritmo, no la de haber observado estos 5 años y no otros — no las presentes como si fueran 10 muestras independientes.
- **Nunca descartes un año porque salió mal.** Si tiene cero semanas "alto" reales, el recall de alto
  se declara `N/A`; el año permanece en la tabla con el resto de métricas y sus falsos positivos.
- **Nunca cambies el criterio después de ver el resultado.** Si crees que el criterio está mal planteado (y la sección 4 te da razones), lo argumentas *antes* de correr, con Eduardo, y queda registrado. No después.
- **No escribas nada a la base de datos.** Cualquier cambio de esquema requiere un documento de decisión aprobado antes de la migración. Tus experimentos escriben a la carpeta de datos intermedios, que no se versiona.
- **No toques los archivos del modelo de producción** ni los scripts de producción del pipeline. Trabaja en scripts nuevos de experimento.
- **No modifiques los archivos de contexto del proyecto.** Registran decisiones del coordinador; se actualizan por decisión suya, no por resultado de un experimento.
- **No presentes un modelo que usa casos previos como si anticipara.** Si tu modelo necesita saber los casos de la semana pasada, es un modelo de estimación del presente, no de anticipación. Se puede entregar, pero se llama por su nombre.

---

## 6. Las vías que quedan, en orden de lo que honestamente esperaría de cada una

Cada vía es un experimento independiente con su propio informe. **Ninguna se adopta en producción por tu cuenta** — tú produces números y una recomendación; adoptar es decisión de Eduardo. Las que están marcadas *requiere aprobación previa* modifican una decisión ya cerrada del proyecto: puedes correr el experimento, pero necesitas el visto bueno de Eduardo antes de correrlo, porque el resultado puede empujar a cambiar el estatuto.

### Vía −1 — Congelar y verificar una validación limpia (empieza antes de cualquier corrida)

**No busca mejorar una métrica. Determina si las métricas que se van a producir pueden interpretarse
como evidencia fuera de muestra.** El pipeline actual construye primero las etiquetas sobre todos los
años y después separa `train`/`test`. Aunque el año objetivo nunca entra en su propia línea base, el
año de prueba puede participar en los percentiles usados para etiquetar filas de entrenamiento.
Además, algunas corridas llamadas temporales entrenan con años posteriores al evaluado.

Antes de las vías 0–3:

1. Define y documenta los folds externos por año, sin barajar filas semanales.
2. Construye las etiquetas dentro de cada fold, sin permitir que casos del año externo de prueba
   participen en etiquetas, umbrales, selección de features o hiperparámetros del entrenamiento.
3. Si el objetivo es anticipación prospectiva, usa solamente información cronológicamente anterior a
   cada predicción. Si se conserva una línea base con años futuros, llama al resultado retrospectivo,
   no prospectivo.
4. Realiza cualquier selección en folds internos agrupados por año. Nunca dividas semanas contiguas
   aleatoriamente entre entrenamiento y validación.
5. Declara que 2019 y 2022 ya fueron observados durante seis experimentos: sirven para desarrollo y
   comparación histórica, pero no son una prueba final intacta de las nuevas vías.
6. Identifica antes de correr si existe un año final no usado y con soporte de `alto`. Si no existe,
   toda conclusión se presenta como exploratoria y esa limitación forma parte del veredicto.
7. Agrega pruebas automáticas que demuestren la independencia del fold y fallen si una etiqueta de
   entrenamiento depende del año externo de prueba.

**Salida obligatoria:** `docs/protocolo-evaluacion-rescate-prediccion.md`, aprobado por Eduardo antes
de correr las demás vías. Si el protocolo cambia el esquema de años base o el criterio formal, debe
registrarse siguiendo la puerta de gobernanza de la sección 4.

### Vía 0 — Diagnóstico: dejar un país fuera, uno por uno (primera corrida tras la Vía −1)

**Esto no rescata nada. Aclara qué significa el resultado que ya tienes, y es un día de trabajo.**

En la corrida regional multipaís, el modelo entrena y prueba con los mismos 16 países, dejando fuera un año. El problema es que el clima es casi una huella dactilar del país — latitud, altitud, régimen de lluvia — así que el modelo puede estar aprendiendo "este perfil climático es Colombia, y Colombia suele verse así" sin aprender ninguna relación clima→brote transferible.

La prueba real de generalización es dejar fuera un **país**, no un año. Eso es exactamente lo que se hizo con El Salvador (y falló). Repítelo para los 16 países.

- Si falla en la mayoría → el "éxito" regional era memorización de identidad de país. La vía multipaís se cierra completa.
- Si funciona en 12 o 14 de 16 y El Salvador es de los pocos que falla → el hallazgo "El Salvador está desacoplado" queda confirmado con fuerza, y se vuelve el eje del capítulo de resultados.

Los dos desenlaces sirven. Ninguno hace perder tiempo.

### Vía 1 — Usar casos previos como predictor *(requiere aprobación previa)*

**Es la vía con más probabilidad real de dar un modelo que funcione.**

Hoy el predictor es solo-clima por decisión cerrada. Pero la línea base de persistencia —predecir la
clase de la semana anterior— obtiene en 2019 **F1 macro 0,814 y recall de "alto" 0,929 (26 de 28)**.
El valor 0,945 corresponde al F1 de la clase alta, no a su recall. La persistencia muestra que hay una
señal autorregresiva fuerte en la serie de casos, aunque no sea desplegable con las fuentes actuales.

Un modelo que combine clima rezagado con casos de las semanas previas casi con seguridad supera el criterio. Y no es una trampa: **prácticamente todos los sistemas operacionales de alerta temprana de dengue en la literatura hacen exactamente eso** — los de Brasil y Vietnam, por ejemplo, usan casos rezagados junto con clima. El solo-clima es la excepción, no la norma.

Los costos, que hay que declarar sin adornos:
- Deja de ser anticipación a semanas de distancia y pasa a ser estimación del presente o de una a dos semanas.
- Exige una fuente de casos actualizada para operar en vivo. Para el nivel nacional existe (la serie nacional histórica llega a 2024); no se actualiza semana a semana, así que el sistema queda como herramienta retrospectiva y de validación, no como alerta en tiempo real. Eso hay que decirlo en pantalla, no en una nota al pie.

Si Eduardo aprueba, corre dos variantes: solo casos rezagados, y casos + clima. La segunda solo se justifica si supera claramente a la primera; si el clima no aporta nada por encima de los casos, ese también es un resultado que hay que reportar.

### Vía 2 — Cambiar qué pregunta responde la etiqueta *(requiere aprobación previa)*

Definir "alto" **dentro de cada año** — la semana está en el 25 % superior de su propio año — en vez de contra el histórico. Eso cambia la pregunta de "¿qué tan grande es este año?" a "¿en qué punto de la temporada estamos?", que es lo que el clima sí puede explicar.

El preliminar recibido y auditado con 10 semillas supera la línea base histórica en 2022 (10 de 10),
2023 (7 de 10) y 2019 (6 de 10), y falla en 2018 y 2021. La reproducción técnica de esas cifras no
autoriza la vía ni resuelve su inestabilidad. En años de baja transmisión, forzar un 25 % de semanas
a "alto" crea una temporada relativa que no equivale a un brote histórico.

Los costos:
- Es **inestable**. 7 de 10 no es un resultado que se sostenga solo; hay que reportarlo como lo que es.
- Crea un problema de comunicación grave: una semana "alto" de 2023 tiene menos casos que una semana "bajo" de 2019. Si esto se adopta, el tablero tiene que decirlo de forma visible o el sistema miente.
- La etiqueta de referencia ya no se puede calcular a mitad de año, porque necesita la distribución del año completo. El modelo sí sigue prediciendo solo desde clima; lo que se vuelve retrospectivo es la validación.

Una variante que vale la pena y que resuelve parte del problema de comunicación: **entregar dos indicadores separados en vez de uno.** El clasificador responde "en qué punto de la temporada estamos" (predicción del modelo), y el canal endémico —que ya está calculado y no necesita modelo— responde "cómo se compara este año con el histórico" como capa descriptiva. Son dos preguntas distintas que hoy están mezcladas en una sola etiqueta, y separarlas es más honesto que cualquiera de las dos sola.

### Vía 3 — Features con mecanismo biológico, no rezagos crudos

**No requiere aprobación: no cambia ninguna decisión cerrada.** Sigue siendo solo-clima y la misma etiqueta. Es la única vía libre que queda sin probar.

Hoy los predictores son las variables climáticas crudas rezagadas 1 y 2 semanas más una media móvil de 4. Eso ignora cómo funciona el mosquito. Alternativas con base biológica:

- Semanas consecutivas por encima de un umbral de temperatura (el desarrollo larvario tiene umbrales, no es lineal).
- Grados-día acumulados sobre el umbral de desarrollo.
- Días con lluvia por encima de un mínimo, en vez de milímetros totales.
- Transiciones seco→húmedo (el llenado de recipientes tras una sequía es un mecanismo documentado de brote).
- Interacciones temperatura × humedad, en vez de las dos por separado.

Honestamente: **espero poco de esto**, porque no toca el problema del efecto año. Pero es gratis, no necesita permiso, y es el tipo de trabajo que un revisor va a preguntar si se intentó. Cuida el número de columnas — con ~2.700 filas de entrenamiento en el pipeline departamental y 250 en el nacional, agregar 30 features nuevas es sobreajuste garantizado. Reemplaza, no acumules.

### Vía 4 — Clasificador departamental

14 departamentos multiplicarían las filas. **Está bloqueada por una razón concreta:** con el piso de suficiencia acordado (mínimo 12 observaciones y al menos 3 de 4 años base por celda departamento-semana), el 100 % de las celdas queda por debajo del piso. No hay etiqueta departamental calculable. Bajar el piso es reabrir una decisión cerrada y además debilita la etiqueta justo donde ya es frágil.

**No la tomes salvo que las vías 0 a 3 se agoten y Eduardo lo pida.** La menciono para que no la descubras como idea nueva en la semana tres.

---

## 7. Cifras de control

Antes de reportar cualquier resultado, verifica que tu réplica reproduce esto. Si no coincide, el error está en tu código y hay que resolverlo antes de seguir:

- Dataset nacional de producción: **250 filas, 21 predictores**.
- Distribución por año: 2018 → 46 bajo / 4 medio / 0 alto. 2019 → 9 / 13 / 28. 2021 → 49 / 1 / 0. 2022 → 19 / 9 / 22. 2023 → 50 / 0 / 0.
- Correlación total anual con número de semanas "alto": **0,955**.
- AUC reproducido de la probabilidad de "alto": **0,234 en 2019 y 0,231 en 2022**.
- Multipaís: **18 países** con serie semanal completa 2014–2024, **10.278 filas**, **1.390 semanas "alto"**, **97 de 198 años-país** con al menos un "alto". Con clima disponible bajan a 16 países (Bermuda y Virgin Islands no tienen cobertura del reanálisis terrestre por ser islas muy pequeñas) y 87 años-país.

El diagnóstico recibido fue auditado y copiado a
`backend/ingestion/diagnostico_senal_etiqueta_auditable.py`. Esa copia reproduce el protocolo
retrospectivo legado y no implementa la Vía −1; su función es cerrar la procedencia de las cifras
anteriores. La validación limpia debe vivir en un script experimental separado.

**Trampas de datos ya confirmadas en vivo, para que no las pierdas medio día descubriendo:**

- La API de clima devuelve `0.0` en vez de nulo para horas de precipitación cuando el mismo día
  `precipitation_sum` viene nulo. Es un cero fabricado: **descártalo junto con la suma nula; no lo
  guardes como una observación real**.
- Esa API tiene límite **por minuto**, no solo diario: salta error con pocas llamadas seguidas. Reintento con espera creciente.
- Dos modelos distintos de clima, no uno: el terrestre para temperatura, humedad y punto de rocío; el otro exclusivamente para precipitación. El terrestre no sirve precipitación en absoluto. Los modelos combinados están prohibidos porque esconden qué malla produjo cada valor.
- Los rezagos climáticos sí cruzan el límite de año (el clima es continuo), pero la línea base de percentiles **nunca** puede ver el año que está etiquetando. Son dos reglas distintas y las dos siguen aplicando.
- El calendario epidemiológico es el de OPS/CDC, no ISO 8601. Usa la librería del proyecto, no recalcules fronteras de semana a mano.
- Al retroceder semanas cruzando el fin de año, el año anterior puede tener 51, 52 o 53 semanas y varía por año. Hay una implementación floja de esto en un script de referencia — revísala, no la copies.

---

## 8. Fecha de corte y qué entregas

**Vía −1: antes de cualquier experimento.** El protocolo y cualquier cambio del criterio deben quedar
aprobados y registrados primero.

**Vía 0: el primer día después de aprobar la Vía −1.** Es diagnóstico y desbloquea la lectura de todo
lo demás.

**Vías 1 a 3: una semana desde que Eduardo apruebe las que lo requieren.** Si al cabo de esa semana
ninguna produce un modelo que cumpla de forma estable el criterio aprobado de la sección 4 frente a
las cuatro referencias reportadas, **se cierra la línea de trabajo y escribes el informe de cierre.**
No hay extensión. El proyecto tiene entregables de tablero, de reproducibilidad y de documento que
están sin hacer y que sí dependen del equipo; quemar tres semanas en el modelo con seis intentos
fallidos a la espalda es la peor decisión disponible, incluso si la séptima hubiera funcionado.

Escribir el informe de cierre no es rendirse. Es el entregable.

Por cada vía que corras, un informe con: qué se cambió respecto de producción, qué decisión cerrada
toca (si toca alguna), resultados por año con las cuatro referencias de la sección 4 y los aciertos
absolutos al lado de cada recall, cuántas semillas sostienen el resultado, y una recomendación
explícita de adoptar / no adoptar / decisión del coordinador.

Y al final, un informe corto de conjunto: qué se intentó, qué funcionó, qué no, y qué recomiendas entregar.

---

## 9. Una cosa más

Que el modelo no funcione no significa que el proyecto no funcione. El aporte declarado de EPI-Aetheris desde el inicio es de ingeniería de software, no de novedad epidemiológica — está escrito en la documentación del proyecto desde antes de que existiera un solo resultado, y fue una decisión correcta.

Sirve que sepas esto antes de empezar: Johansson et al. (2016), *Evaluating the performance of
infectious disease forecasts: A comparison of climate-driven and seasonal dengue forecasts for
Mexico* (`https://doi.org/10.1038/srep33707`), trabajó con 28 años de datos mensuales, una serie
nacional y 17 estatales de México, y encontró que las variables climáticas no mejoraban
significativamente a sus modelos estacionales autorregresivos. Es evidencia contextual, no una
reproducción directa de EPI-Aetheris: cambia el país, la resolución temporal, el objetivo y el uso de
casos autorregresivos. Su exigencia de validación completamente fuera de muestra sí refuerza la
necesidad de la Vía −1.

Intenta en serio las vías de la sección 6. Si alguna funciona, excelente. Si ninguna funciona, lo que entregas es un resultado negativo con mecanismo identificado, siete experimentos documentados y reproducibles, y convergencia con literatura revisada por pares. Eso se defiende de pie.

Lo que no se defiende es un número bonito que no aguante una pregunta.
