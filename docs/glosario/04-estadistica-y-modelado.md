# Rama 4 · Estadística y modelado

Vocabulario estadístico y de aprendizaje automático que aparece en los ADR, los experimentos y los scripts de `backend/ingestion/`: cómo se mide una predicción, qué protocolo evita la fuga de información, qué modelos se probaron y por qué el clasificador de riesgo se retiró mientras la predicción de casos a corto plazo se mantuvo.

**Para quién es.** Para quien lee un experimento firmado, un informe de cierre o el bloque `desempeno` de la API y necesita saber qué es un WIS, un fold, una semilla o un «control de mutación» antes de interpretar un número.

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris, con las cifras documentadas), **Dónde** (archivo, ADR o experimento) y **Ojo** (errores frecuentes). Las siglas que el repositorio no expande se marcan como «de uso general».

**Ramas vecinas.** Los datos de entrada están en [`02-fuentes-de-datos-e-ingesta.md`](02-fuentes-de-datos-e-ingesta.md) y [`03-clima-y-ambiente.md`](03-clima-y-ambiente.md); los módulos descriptivos que usan percentiles y z-scores (M1 a M4), en [`05-modulos-descriptivos-y-alertas.md`](05-modulos-descriptivos-y-alertas.md); las reglas de firma y de gobernanza de los experimentos, en [`10-proceso-gobernanza-y-documentacion.md`](10-proceso-gobernanza-y-documentacion.md).

<!-- INDICE:INICIO -->

## Índice alfabético (98 entradas)

- **A** — [Abanico](#abanico) · [Agregado nacional simple](#agregado-nacional-simple) · [Ancla (semana de anclaje)](#ancla-semana-de-anclaje) · [Años base](#años-base) · [Años ganados](#años-ganados) · [Armónicos estacionales](#armónicos-estacionales) · [Artefacto precomputado del nowcast](#artefacto-precomputado-del-nowcast) · [Aserción anti-fuga](#aserción-anti-fuga)
- **C** — [Calibración de intervalos](#calibración-de-intervalos) · [Camino Ancho](#camino-ancho) · [Chequeo de cordura](#chequeo-de-cordura) · [Clasificador de riesgo retirado](#clasificador-de-riesgo-retirado) · [Climatología estacional](#climatología-estacional) · [Cobertura empírica y nominal](#cobertura-empírica-y-nominal) · [Comparador decisivo](#comparador-decisivo) · [Control de mutación](#control-de-mutación) · [Cortes de percentil (P50/P75 y P75/P90)](#cortes-de-percentil-p50p75-y-p75p90) · [CQR-r](#cqr-r) · [Criterio de éxito predeclarado](#criterio-de-éxito-predeclarado) · [Cuantil y 23 cuantiles](#cuantil-y-23-cuantiles)
- **D** — [D1 a D4](#d1-a-d4) · [Dataset de modelado](#dataset-de-modelado) · [Dentro de muestra (dentro_de_muestra)](#dentro-de-muestra-dentro_de_muestra)
- **E** — [Efecto año](#efecto-año) · [Escala log1p y expm1](#escala-log1p-y-expm1) · [Estados de un fold](#estados-de-un-fold) · [Etiqueta de riesgo (P75/P90)](#etiqueta-de-riesgo-p75p90) · [Etiqueta legada y etiqueta prospectiva](#etiqueta-legada-y-etiqueta-prospectiva) · [Experimento ventana climática ampliada](#experimento-ventana-climática-ampliada) · [Extrapolación y saturación de los árboles](#extrapolación-y-saturación-de-los-árboles)
- **F** — [F1 macro](#f1-macro) · [Features del nowcast](#features-del-nowcast) · [Fold (externo e interno) y año externo](#fold-externo-e-interno-y-año-externo) · [Forward-chaining (ventana expansiva)](#forward-chaining-ventana-expansiva) · [Fuga de información (leakage)](#fuga-de-información-leakage)
- **H** — [Heterocedasticidad](#heterocedasticidad) · [Hiperparámetros y barrido (sweep)](#hiperparámetros-y-barrido-sweep) · [Historia 2014+ y 2016+](#historia-2014-y-2016) · [Historia permitida H(y)](#historia-permitida-hy) · [Historia promediada](#historia-promediada) · [Horizonte (h) y origen (t)](#horizonte-h-y-origen-t)
- **I** — [Inflado global](#inflado-global) · [Informe de cierre del rescate](#informe-de-cierre-del-rescate) · [Interpretación permitida y no permitida](#interpretación-permitida-y-no-permitida)
- **L** — [Lead time (tiempo de anticipación)](#lead-time-tiempo-de-anticipación) · [Leave-one-out (LOO)](#leave-one-out-loo) · [Leave-one-year-out y leave-one-country-out](#leave-one-year-out-y-leave-one-country-out) · [Línea base (baseline) y referencia](#línea-base-baseline-y-referencia)
- **M** — [M0, M1, M2, T y C (candidatos del nowcast)](#m0-m1-m2-t-y-c-candidatos-del-nowcast) · [Manifiesto congelado y firma previa](#manifiesto-congelado-y-firma-previa) · [Matriz de confusión, falsos positivos, AUC y soporte](#matriz-de-confusión-falsos-positivos-auc-y-soporte) · [Mezcla C](#mezcla-c) · [Momento (momentum)](#momento-momentum) · [Multipaís](#multipaís)
- **N** — [Nowcast de dengue](#nowcast-de-dengue) · [Nowcast retrospectivo](#nowcast-retrospectivo)
- **O** — [Opción C (pivote de fase 1)](#opción-c-pivote-de-fase-1)
- **P** — [Percentil (interpolación lineal inclusiva)](#percentil-interpolación-lineal-inclusiva) · [Percentil relativo (rango_percentil)](#percentil-relativo-rango_percentil) · [Persistencia (random walk)](#persistencia-random-walk) · [Persistencia estacional](#persistencia-estacional) · [Persistencia suavizada, limpia y publicada](#persistencia-suavizada-limpia-y-publicada) · [Piso de suficiencia](#piso-de-suficiencia) · [Pool (línea base)](#pool-línea-base) · [Precedente comparable y nota de alcance](#precedente-comparable-y-nota-de-alcance) · [Predeclarar y firmar](#predeclarar-y-firmar) · [Predicción probabilística](#predicción-probabilística) · [Predictores del clasificador (21)](#predictores-del-clasificador-21) · [Prueba prospectiva](#prueba-prospectiva) · [Pruebas de independencia](#pruebas-de-independencia) · [Puerta de gobernanza](#puerta-de-gobernanza)
- **R** — [Random Forest](#random-forest) · [Rango del 50 % y del 95 %](#rango-del-50--y-del-95-) · [Reajuste (cadencia)](#reajuste-cadencia) · [Recall de «alto» y aciertos absolutos](#recall-de-alto-y-aciertos-absolutos) · [Referencias del clasificador](#referencias-del-clasificador) · [Regresión cuantílica por gradient boosting](#regresión-cuantílica-por-gradient-boosting) · [Repetibilidad](#repetibilidad) · [Rezago autorregresivo y media móvil](#rezago-autorregresivo-y-media-móvil) · [RIC (rango intercuartílico)](#ric-rango-intercuartílico)
- **S** — [Segunda confirmación independiente](#segunda-confirmación-independiente) · [Semanas con cero notificado](#semanas-con-cero-notificado) · [Semilla (seed)](#semilla-seed) · [Serie mixta](#serie-mixta) · [Skill relativo](#skill-relativo)
- **T** — [Tendencia amortiguada (T)](#tendencia-amortiguada-t)
- **U** — [Umbral Z ≥ 1,5 durante dos semanas](#umbral-z--15-durante-dos-semanas)
- **V** — [Ventana ±1 (semanas vecinas)](#ventana-1-semanas-vecinas) · [Veto de constantes](#veto-de-constantes) · [Vía 0 (multipaís, leave-one-country-out)](#vía-0-multipaís-leave-one-country-out) · [Vía 1 (casos previos)](#vía-1-casos-previos) · [Vía 2 (etiqueta intraanual)](#vía-2-etiqueta-intraanual) · [Vía 3 (features con mecanismo biológico)](#vía-3-features-con-mecanismo-biológico) · [Vía −1 (protocolo de validación limpia)](#vía-1-protocolo-de-validación-limpia) · [Vías de rescate (−1 a 4)](#vías-de-rescate-1-a-4)
- **W** — [Winsorización](#winsorización) · [WIS (Weighted Interval Score)](#wis-weighted-interval-score)
- **Z** — [Z-score y anomaly_sigma](#z-score-y-anomaly_sigma)

<!-- INDICE:FIN -->

## 1. Qué se predice y cómo se mide

### Nowcast de dengue

**Qué es.** En sentido estricto, estimar el estado presente de una serie que se publica con retraso; el proyecto lo usa para la **predicción de casos a corto plazo** de la serie nacional de dengue.

**En el proyecto.** [ADR 0020](../adr/0020-nowcast-corto-plazo.md): predice el **conteo semanal** nacional en `t+h`, con `h` de 1 a 8 semanas, como una distribución completa de 23 cuantiles. Es la única capa predictiva del producto y **no reabre** el clasificador retirado: no hay etiqueta alto, medio o bajo, ni juicio de «¿habrá brote?», ni salida departamental, y no usa M3 ni sus cortes como objetivo ni como feature. Vive en la pestaña «Predicción a corto plazo» de `/dengue` y, desde 2026-09-22, en `/demos/nowcast`.

**Ojo.** «Riesgo de brote» sigue prohibido en el producto. El veto a la palabra «predicción» se levantó solo para esta capa y con su horizonte rotulado.

### Predicción probabilística

**Qué es.** Predicción que entrega una distribución de valores posibles en lugar de un solo número.

**En el proyecto.** El modelo entrega un abanico de cuantiles por horizonte; la incertidumbre es parte de la cifra, y el desempeño se muestra junto a ella y no en una nota al pie.

### Cuantil y 23 cuantiles

**Qué es.** El cuantil `q` de una variable es el valor por debajo del cual queda una proporción `q` de la distribución; la mediana es el cuantil 0,5.

**En el proyecto.** Se predicen 23 cuantiles: 0,010, 0,025, 0,050, 0,100 y así hasta 0,950, 0,975 y 0,990. Es el conjunto estándar de los hubs de pronóstico de CDC y OPS, elegido para que el WIS sea comparable con esa literatura.

### Rango del 50 % y del 95 %

**Qué es.** Intervalo central que, si el modelo estuviera calibrado, contendría esa proporción de lo observado.

**En el proyecto.** Se reportan el rango del 50 % y el del 95 % y se comparan con lo observado (ver [Cobertura empírica](#cobertura-empírica-y-nominal)).

### Horizonte (`h`) y origen (`t`)

**Qué es.** El origen `t` es la semana desde la que se predice; el horizonte `h` es cuántas semanas adelante.

**En el proyecto.** `h = 1..8`. Los horizontes decisivos de los criterios firmados son `h = 4` y `h = 8`. Toda variable del modelo debe estar disponible en `t`: ninguna es contemporánea a `t+h`.

### Ancla (semana de anclaje)

**Qué es.** Última semana observada de la fuente, desde la cual se extiende la predicción.

**En el proyecto.** Se predice **desde la última semana publicada, no desde hoy**, y el panel muestra la fecha de ancla. Con OpenDengue el ancla era 2024-12-22 (la fuente iba unos 21 meses detrás del tiempo real); con el tablero desde 2025 va unas dos semanas detrás. Actualizar exige recargar la serie y **regenerar el artefacto**.

### Abanico

**Qué es.** El conjunto de cuantiles de las predicciones a 1–8 semanas trazado desde una semana de partida.

**En el proyecto.** Es lo que dibuja el panel. La vista retrospectiva permite mover el punto de partida a cualquier semana y contrastarlo con lo observado después. Cada abanico usa solo datos anteriores a su semana de partida.

### Escala `log1p` y `expm1`

**Qué es.** `log1p(x) = ln(1 + x)` comprime una serie de conteos con picos y admite ceros; `expm1` es su inversa.

**En el proyecto.** El objetivo del nowcast se modela como `z = log1p(casos)` y se devuelve a escala natural con `expm1` y piso 0. Existe un **WIS en escala log** como métrica secundaria junto al WIS natural.

### Línea base (baseline) y referencia

**Qué es.** Método simple contra el que debe ganar un modelo para justificar su complejidad.

**En el proyecto.** El nowcast se compara con tres líneas base y se usa como comparador decisivo la más fuerte por WIS medio: **persistencia**, **climatología estacional** y **persistencia estacional**. En el clasificador las referencias son otras cuatro ([Referencias del clasificador](#referencias-del-clasificador)).

### Persistencia (random walk)

**Qué es.** Predecir que el futuro será igual al último valor observado.

**En el proyecto.** En el nowcast: `ŷ(t+h) = y(t)` en escala log, con intervalos tomados de la distribución empírica de los cambios pasados `log1p(y(t'+h)) − log1p(y(t'))`. Es el comparador decisivo a `h ≤ 4`; a `h = 8` lo es la persistencia estacional. En el clasificador, en cambio, la persistencia predice la **etiqueta real de la semana anterior**.

### Climatología estacional

**Qué es.** Usar la distribución histórica de la misma semana epidemiológica como predicción.

**En el proyecto.** Cuantiles de `y` para la misma semana calculados **solo con años estrictamente anteriores** al año de `t+h`.

**Ojo.** No es la «línea base climatológica» del clasificador, que predice la clase **modal** de cada semana calendario ([Referencias del clasificador](#referencias-del-clasificador)).

### Persistencia estacional

**Qué es.** Combinación de las dos anteriores.

**En el proyecto.** `ŷ(t+h) = y(t) · clim(semana de t+h) / clim(semana de t)`, con incertidumbre por bootstrap de residuos. Es la comparadora decisiva a `h = 8`.

### Persistencia suavizada, limpia y publicada

**Qué es.** Tres versiones de la referencia de persistencia, según de qué historia aprende su margen de error.

**En el proyecto.**

- **Publicada:** la del ADR 0020, que aprende de toda la historia.
- **Limpia:** aprende sin las 17 semanas afectadas (cada semana con cero y la siguiente), y es la referencia del criterio del experimento de mejora.
- **Suavizada:** mediana `z[o]` más los cuantiles empíricos de `z[t+h] − z[t]` en la [historia promediada](#historia-promediada); es la referencia del criterio del experimento de tendencia.

**Ojo.** El criterio usa la suavizada porque la limpia aprende su margen de datos crudos, más ruidosos que el tablero: evaluar contra la limpia inflaría la ventaja del candidato.

### Comparador decisivo

**Qué es.** La línea base contra la que se firma el criterio de éxito.

**En el proyecto.** La más fuerte de las tres por WIS medio en el conjunto de prueba, elegida y declarada **antes** de comparar el modelo.

### WIS (Weighted Interval Score)

**Qué es.** Puntuación de una predicción dada por cuantiles: combina el error absoluto de la mediana con la amplitud de los intervalos centrales y una penalización cuando lo observado cae fuera. **Menor es mejor.**

**En el proyecto.** Métrica primaria del nowcast, calculada sobre los 23 cuantiles, en escala natural y en escala log. En `h = 4`, el modelo del ADR 0020 pasó de un WIS de 74,6 (baseline) a 53,1 con historia 2014+.

**Dónde.** `backend/ingestion/experimento_nowcast_corto_plazo.py`; reimplementado desde cero en `nowcast_segunda_confirmacion.py`.

### Skill relativo

**Qué es.** Ganancia relativa frente a una referencia: `skill = 1 − WIS_modelo / WIS_referencia`. Positivo significa que el modelo es mejor.

**En el proyecto.** Se promedia por año con **peso igual** (no el WIS agrupado crudo, que domina el año de mayor conteo). En 2014+ y `h = 4` el skill medio por año fue +0,33 y ganó 5 de 5 años.

### Años ganados

**Qué es.** Cuántos años de prueba (de 5) el modelo supera a la referencia.

**En el proyecto.** Los criterios firmados exigen «≥ 4 de 5»: se subió desde «≥ 3 de N» para no repetir la vara que la Vía 2 no alcanzó.

### Cobertura empírica y nominal

**Qué es.** La cobertura empírica es la proporción de valores observados que caen dentro de un intervalo; la nominal es la que el intervalo promete.

**En el proyecto.** Nominal 0,50 y 0,95. Bandas de los criterios firmados: **0,35 a 0,65** para el 50 % y **0,85 a 0,99** para el 95 %. Con el ADR 0020 (2014+, `h = 4`) la cobertura fue 0,42 y 0,94. Un intervalo puede acertar la mediana y estar mal calibrado, por eso no basta con lo primero.

### Calibración de intervalos

**Qué es.** Ajustar los rangos para que su cobertura empírica se acerque a la nominal.

**En el proyecto.** El modelo sin calibrar ya cumplía las bandas; se calibró porque sus intervalos corrían estrechos (0,40 frente a 0,50 al 50 %). Se compararon tres variantes: sin calibrar, `cqr_r` e inflado global.

### CQR-r

**Qué es.** Regresión cuantílica conformalizada (CQR, de uso general) en la variante «r» de Romano et al. (2019): la corrección es **multiplicativa** sobre el semiancho del intervalo y estable ante heterocedasticidad.

**En el proyecto.** Se calibra con los **52 pares más recientes** reservados como conjunto de calibración; el score se winsoriza al percentil 90 y el factor se topa en 4,0, porque con `n = 52` una sola semana de brote lo domina (sin esos topes el WIS explota a ~10¹²). Lleva la cobertura del 50 % de ~0,40 a ~0,55 sin cambiar el veredicto en 2014+.

**Ojo.** Para los pares 90, 95 y 98 % la corrección colapsa al mismo factor: es un **heurístico**, no conformal estricto, en los intervalos externos. Se adoptó solo en el régimen 2014+; con historia 2016+ calibrar rompe todo.

### Inflado global

**Qué es.** Multiplicar todos los semianchos por un mismo escalar.

**En el proyecto.** Se descartó frente a CQR-r: cuesta de 2 a 3 veces más y es ciego al régimen (a `h = 4` el skill de 2021 cae de +0,36 a +0,01).

### Heterocedasticidad

**Qué es.** Que la variabilidad de los errores cambie con el nivel de la serie.

**En el proyecto.** Es la razón de que la calibración sea multiplicativa: un valle y un brote no tienen el mismo margen de error.

### Winsorización

**Qué es.** Recortar los valores extremos a un percentil en lugar de eliminarlos.

**En el proyecto.** Los scores de calibración se winsorizan al percentil 90.

### Extrapolación y saturación de los árboles

**Qué es.** Un modelo de árboles predice dentro del rango que vio en entrenamiento y apenas lo supera.

**En el proyecto.** Con historia 2016+ el modelo falla en 2019 (skill −0,32) porque los objetivos de entrenamiento tienen pico ~437 semanal frente al pico real de 2019, 2.178. Regla operativa: el nowcast queda topado cerca del máximo histórico y subestima un brote de magnitud sin precedente en su ventana; la salida, si se retoma, es modelar tasas de crecimiento o una cola paramétrica, no niveles.

### Precedente comparable y nota de alcance

**Qué es.** Condición para que el nowcast funcione: tener un brote grande en el historial de entrenamiento.

**En el proyecto.** La estimación **asume un brote grande ya presente** en la serie desde 2014; sin ese precedente pierde ventaja frente a una extrapolación ingenua. Se declara en el campo `nota_alcance` del artefacto y en la Biblioteca 05. El soporte empírico de la robustez ante brotes sin precedente es **n = 1** (2019, un solo brote grande).

### Historia 2014+ y 2016+

**Qué es.** Las dos ventanas de entrenamiento con que se corrió el experimento.

**En el proyecto.** **2014+** es la principal (`ALCANCE_HISTORIA`): el modelo gana en los cuatro horizontes y en los cinco años. **2016+** queda como chequeo de robustez y su fragilidad se declara: sin el pico de 2014–2015 en el entrenamiento, a `h` = 1, 2 y 4 el modelo queda peor que la persistencia en agregado por el fallo de 2019 (a `h` = 8 sí gana).

### Semanas con cero notificado

**Qué es.** Semanas en que la serie de OpenDengue registra 0 casos y la siguiente trae aproximadamente el doble.

**En el proyecto.** Hay nueve: 2016-S15, S30 y S51, 2018-S2, 2020-S53, 2022-S51 y 2023-S30, S51 y S52. La persistencia aprendía de ellas saltos de hasta ±4 en escala log y abría sus cuantiles extremos: la ventaja del modelo a 1–3 semanas dependía de esas semanas. Se conservan como las publica la fuente, y el criterio se evalúa contra la referencia [limpia](#persistencia-suavizada-limpia-y-publicada).

## 2. Validación temporal y protocolo anti-fuga

### Fuga de información (leakage)

**Qué es.** Que el modelo o su etiqueta «vean» información del periodo que después se evalúa, inflando el resultado.

**En el proyecto.** Es el riesgo central de todo el trabajo predictivo. Ejemplo concreto: el pipeline histórico construía las etiquetas sobre una lista fija de años y después separaba el año de prueba, de modo que el año externo podía participar en los percentiles que etiquetaban el entrenamiento, y algunas corridas «temporales» entrenaban con años posteriores al evaluado. Por eso esas corridas son *retrospectivas*.

### Forward-chaining (ventana expansiva)

**Qué es.** Validación temporal en la que cada predicción se entrena solo con datos anteriores al origen, y la ventana de entrenamiento crece con el tiempo.

**En el proyecto.** Cada predicción usa solo pares cuyo objetivo tiene fecha anterior al origen. El nowcast reajusta **cada 2 semanas epidemiológicas** (por costo de cómputo; no es fuente de fuga, solo de recencia) y 2020 queda excluido como origen y como objetivo. Nunca se hace un split aleatorio de semanas del mismo año.

### Reajuste (cadencia)

**Qué es.** Cada cuánto se vuelve a entrenar el modelo.

**En el proyecto.** Cada 2 semanas. La segunda confirmación mostró que cadencias de 1, 2 y 4 semanas mueven el WIS agrupado menos del 3 % sin cambiar el veredicto.

### Aserción anti-fuga

**Qué es.** Comprobación automática de que ningún par de entrenamiento tiene fecha posterior al corte.

**En el proyecto.** Se toman los índices de objetivo que `pares_entrenamiento` realmente devuelve y se verifica que todos son anteriores al corte; un **control negativo** desactiva el filtro y confirma que la comprobación entonces sí rompe, para que no sea una tautología.

### Leave-one-out (LOO)

**Qué es.** Excluir del cálculo el elemento que se describe.

**En el proyecto.** Es el patrón de M2 y M3 y del canal endémico: **el año descrito nunca entra en su propia línea base**. No convierte un percentil en una relación causal con la lluvia o con El Niño.

### Leave-one-year-out y leave-one-country-out

**Qué es.** Dejar fuera un año (o un país) entero como prueba.

**En el proyecto.** Los diagnósticos históricos del clasificador eran **leave-one-year-out retrospectivos**: sirven para reproducir el diagnóstico, no para estimar anticipación prospectiva. La Vía 0 usó **leave-one-country-out** (dejar un país fuera, uno por uno) para saber si el modelo regional transfería a países no vistos.

### Fold (externo e interno) y año externo

**Qué es.** Una partición de datos en entrenamiento y evaluación.

**En el proyecto.** Un **fold externo** es un año completo `t` que se evalúa una sola vez; un **fold interno** sirve para elegir configuraciones y también es forward-chaining por años completos. Si hay menos de dos años de validación interna utilizables, no se selecciona nada y se conserva la configuración predefinida.

### Historia permitida `H(y)`

**Qué es.** Los años que pueden usarse para etiquetar el año `y`.

**En el proyecto.** `H(y)` = todos los años observados `r` con `r < y` y no excluidos formalmente. Es **expansiva**, no una ventana móvil de cuatro años: `H(2018) = {2014, 2015, 2016, 2017}` y `H(2021) = {2014, …, 2019}` sin 2020. La etiqueta de un año debe ser idéntica en todos los folds externos que la reutilizan.

### Semilla (seed)

**Qué es.** Valor que fija la aleatoriedad de un algoritmo.

**En el proyecto.** Mínimo **10 semillas** (0–9) para cada resultado del clasificador. Miden la variabilidad del algoritmo, **no** la de haber observado estos 5 años y no otros: no son 10 muestras epidemiológicas independientes. La semilla **42** se conserva solo como referencia comparable con el diagnóstico histórico; **12345** se usa en el control de mutación; el nowcast usa `random_state=0`.

### Hiperparámetros y barrido (sweep)

**Qué es.** Los hiperparámetros son los ajustes del modelo que no se aprenden de los datos; un barrido los prueba en muchas combinaciones.

**En el proyecto.** «No se barren hiperparámetros contra los años de prueba» es regla en todos los experimentos. La configuración se declara antes de correr y no se cambia sin una nueva entrada fechada.

### Predeclarar y firmar

**Qué es.** Escribir el candidato, la referencia, el conjunto de prueba y el criterio **antes** de ver el resultado, y que la coordinación los firme.

**En el proyecto.** Los experimentos del nowcast se firmaron antes de correr; cualquier cambio posterior va en una sección de **enmiendas** con su fecha y no puede tocar candidato, referencia ni criterio. Ver [Decisiones cerradas y abiertas](10-proceso-gobernanza-y-documentacion.md).

### Control de mutación

**Qué es.** Introducir a propósito un error (una fuga o etiquetas permutadas) y comprobar que la métrica empeora o que una prueba falla.

**En el proyecto.** En el nowcast se permutan las etiquetas de entrenamiento (semilla 12345): el WIS sube de 53,1 a 128,8 en 2014+ `h = 4`. En la Vía −1 la variable `VIA_MENOS_UNO_MUTACION_FUGA=1` mete el año externo 2022 en los pools de etiquetado, y la prueba de independencia debe **verse fallar**, con su salida registrada. Después se revierte y solo se conserva la implementación limpia.

### Repetibilidad

**Qué es.** Dos ejecuciones independientes producen los mismos artefactos.

**En el proyecto.** Se exige que los JSON de métricas sean idénticos byte a byte (o que los cuantiles coincidan). La Vía −1 publicó los SHA-256 de `etiquetas.csv`, `dataset.csv`, `predicciones.csv` y `metricas.json`.

### Pruebas de independencia

**Qué es.** Pruebas automáticas que demuestran que el fold no depende del año externo.

**En el proyecto.** Son 12 exigencias (por ejemplo: cambiar casos o clima del año externo no modifica etiquetas ni matrices de entrenamiento; la ventana ±1 no cruza el año; los rezagos climáticos sí lo cruzan; un faltante no se convierte en cero). La Vía −1 corrió 17 pruebas sobre el volcado real.

### Manifiesto congelado y firma previa

**Qué es.** Archivo JSON con los parámetros congelados de una corrida y los hashes de su preparación.

**En el proyecto.** `via_*_manifesto_congelado.json` (Vías −1, 0, 1, 2 y 3) guarda el SHA-256 del volcado y del script y la **firma previa** (`firma_previa_sha256`): un hash de la preparación (filas, descartes y estados de fold) que la corrida verifica antes de entrenar. El script aborta si el volcado no coincide.

### Prueba prospectiva

**Qué es.** Evaluar sobre datos que todavía no existían cuando se fijó el candidato.

**En el proyecto.** Para la mezcla C (ADR 0020, enmienda) la prueba son las **20 semanas objetivo de 2026-S38 a 2027-S05**, que MINSAL aún no había publicado. Se corre `--evaluar` **una sola vez** y el script se niega a puntuar antes, si su archivo tiene cambios sin commit, o si la salida ya existe.

### Dentro de muestra (`dentro_de_muestra`)

**Qué es.** Marca de que los datos con que se mide un desempeño ya sirvieron para elegir el modelo.

**En el proyecto.** El bloque `desempeno` de 2025 y 2026 lleva `dentro_de_muestra: true` porque esos años sirvieron para elegir C; el bloque `prueba` describe la prueba prospectiva. 2024, 2025 y 2026 se usaron para diseñar el candidato y no sirven como prueba.

### Segunda confirmación independiente

**Qué es.** Reimplementar desde cero el método de evaluación y comprobar que da lo mismo.

**En el proyecto.** `nowcast_segunda_confirmacion.py` reescribió el WIS, el forward-chaining y los baselines, con **paridad a la décima** en las 8 filas de la tabla. Verificó además robustez a la cadencia de reajuste y a un held-out terminal (entrenando solo hasta 2022 sin reajuste, el WIS baja entre 40 y 55 % en 2023–2024).

### Criterio de éxito predeclarado

**Qué es.** Condiciones numéricas que el resultado debe cumplir para contar como positivo.

**En el proyecto.** Para el nowcast original: skill relativo agrupado mayor que 0, al menos 4 de 5 años ganados y cobertura dentro de las bandas. Para el clasificador: superar a la línea base climatológica en F1 macro y en recall de «alto», por año evaluable.

### Puerta de gobernanza

**Qué es.** Lista de requisitos que deben cumplirse antes de correr o adoptar algo.

**En el proyecto.** La Vía −1 tenía una «puerta» (sección 16) con 11 elementos; ningún experimento de las Vías 0–3 arrancó hasta cerrarla. La parte que sigue a cargo de la coordinación es el registro formal de D1 y D3.

### Interpretación permitida y no permitida

**Qué es.** Cada informe de corrida declara para qué puede usarse su resultado y para qué no.

**En el proyecto.** Por ejemplo, la Vía −1 permite «validación forward-chaining exploratoria» y **no** «desempeño final independiente»; la Vía 2 permite «clasificación retrospectiva de la posición relativa» y **no** «riesgo contra el histórico» ni «modelo listo para producción».

## 3. Modelos del nowcast

### Regresión cuantílica por gradient boosting

**Qué es.** Un modelo que ajusta un cuantil de la distribución con árboles potenciados (boosting).

**En el proyecto.** `HistGradientBoostingRegressor(loss="quantile")` de scikit-learn, un modelo por cuantil, sin dependencia nueva (el documento firmado proponía LightGBM y se descartó por eso). Configuración fija, declarada antes de correr: `max_iter=150`, `max_leaf_nodes=7`, `min_samples_leaf=20`, `l2_regularization=1.0`, `learning_rate=0.05`, `random_state=0`, sin early stopping.

### Features del nowcast

**Qué es.** Las variables de entrada del modelo.

**En el proyecto.** Todas disponibles en el origen `t`: 8 rezagos de `log1p` de la serie, medias de 4 y 8 semanas, momento a 4 semanas, tres armónicos anuales del día del año de la **semana objetivo**, la media de 4 semanas de cada variable climática agregada a nivel nacional (promedio simple de los 14 departamentos), el ONI y el año objetivo. Nada se deriva de M1–M4.

### Rezago autorregresivo y media móvil

**Qué es.** Valores pasados de la propia serie (`z[t], z[t−1], …, z[t−7]`) y su promedio en una ventana.

**En el proyecto.** Los rezagos de casos son los predictores del nowcast, mientras que en el clasificador retirado eran solo climáticos. Un modelo que usa casos previos es de **estimación del presente o de muy corto plazo**, no de anticipación: se llama por su nombre.

### Momento (`momentum`)

**Qué es.** Cambio reciente de la serie.

**En el proyecto.** `momentum = z[t] − z[t−4]`.

### Armónicos estacionales

**Qué es.** Pares seno–coseno que codifican la estacionalidad anual.

**En el proyecto.** `sin` y `cos` de `2πk·doy/365,25` para `k ∈ {1, 2, 3}`, con `doy` el **día del año** de la semana objetivo (no semana/52, para no romperse en años de 53 semanas). Es determinista y conocido en `t`.

### M0, M1, M2, T y C (candidatos del nowcast)

**Qué es.** Nombres de los modelos de los experimentos de mejora y de tendencia.

**En el proyecto.**

- **M0:** el modelo publicado del ADR 0020, entrenado con conteos crudos.
- **M1 (mejora):** predice el **cambio** `z[t+h] − z[t]` en lugar del nivel y añade una marca de Semana Santa, fiestas agostinas y fin de año. No pasó la validación.
- **M2 (mejora):** combina M0 con la persistencia con un peso `w ∈ {0; 0,25; 0,5; 0,75; 1}` elegido en cada reajuste. Pasó la validación pero no se confirmó en 2025–2026.
- **T:** [tendencia amortiguada](#tendencia-amortiguada-t).
- **C:** [mezcla](#mezcla-c) de M0 y T.

**Ojo.** **M1 y M2 de este experimento no son los módulos M1 y M2 del producto** (idoneidad y anomalía). Es homonimia; el contexto la resuelve.

### Tendencia amortiguada (T)

**Qué es.** Extrapolar la pendiente reciente con una amortiguación que la va apagando.

**En el proyecto.** En escala `log1p`, la mediana es `z[o] + b · (φ + φ² + … + φʰ)` con `b = (z[o] − z[o−3]) / 3` y `φ = 0,8`. Los 23 cuantiles suman a esa mediana los cuantiles empíricos de los errores de la misma regla en la historia promediada. **No se entrena nada**; se vuelve a escala natural con `expm1` y piso 0.

### Mezcla C

**Qué es.** Promedio por cuantil de M0 y T con peso fijo 0,5.

**En el proyecto.** `q = expm1(0,5 · log1p(q_M0) + 0,5 · log1p(q_T))`, ordenado y con piso 0. Es el **candidato único** que la enmienda del ADR 0020 publica desde 2025-S1 sobre la serie del tablero. A `h = 4`, en 2025–2026: WIS 19,6 frente a 22,8 de la persistencia suavizada (skill +0,14), con cobertura 0,39 al 50 % y 0,91 al 95 %; en 2026 la cobertura del 95 % es 0,79, por debajo del 0,85 que exige el criterio.

### Historia promediada

**Qué es.** La serie con cada semana hasta 2023 sustituida por el promedio de las 7 semanas que terminan en ella.

**En el proyecto.** Se calcula en memoria (no toca la base) y la usan T y la referencia suavizada; M0 no. Desde 2024 la serie ya viene promediada y no se toca. Los 0 de OpenDengue entran al promedio como dato.

### Serie mixta

**Qué es.** La serie que une OpenDengue y el tablero. Ver [Serie mixta (empalme)](02-fuentes-de-datos-e-ingesta.md#serie-mixta-empalme).

**En el proyecto.** Es la entrada de M0 y C desde 2025-S1. El empalme de 2024 a 2025 une dos clasificaciones distintas (`total` y `sospechoso`) y el experimento **no corrige el nivel**: si introduce un sesgo, debe verse en 2025–2026.

### Artefacto precomputado del nowcast

**Qué es.** Archivo JSON versionado con la predicción ya calculada, que la API sirve tal cual.

**En el proyecto.** `backend/api/datos/nowcast_dengue.json` (ancla, 23 cuantiles calibrados por horizonte, unas 120 semanas de contexto, backtest a `h = 4` y bloque `desempeno`), más la versión retrospectiva y las bases de M0 (`*_opendengue.json`). El entrenamiento **no ocurre en producción**. Si el archivo falta en un despliegue, la API responde 200 con `disponible: false` y motivo. Ver [Contrato `disponible: false`](06-backend-y-api.md#contrato-disponible-false).

### Nowcast retrospectivo

**Qué es.** Predicciones precomputadas desde cualquier semana de la serie.

**En el proyecto.** `nowcast_retrospectivo_dengue.py` produce `nowcast_dengue_retrospectivo.json`, que sirve `GET /api/nowcast-dengue/retrospectivo` (pesa unas diez veces más que el principal). Las primeras semanas no tienen predicción (el modelo necesita unos tres años de historia) y el artefacto las marca con `motivo`. Los orígenes de 2025-S53 a 2026-S7 llevan `motivo: "hueco_en_serie"`, porque su ventana de ocho semanas incluye la 53 de 2025, que el tablero no publica. La vista de contraste vive solo en `aetheris-nitor`.

## 4. El clasificador de riesgo retirado

### Clasificador de riesgo retirado

**Qué es.** El clasificador de riesgo de brote nacional (alto, medio o bajo por semana, a partir de clima rezagado) que se construyó, se evaluó y se cerró el **2026-08-18**.

**En el proyecto.** No se adopta como producto: el código (`entrenar_clasificador.py` y afines) **se conserva** como evidencia reproducible, no para extenderlo ni exponerlo en vivo. Las razones: recall de «alto» igual a 0,000 en 2019 y 2022, los únicos años de la ventana con semanas de esa clase; cinco vías de rescate que no sostuvieron el criterio; y un experimento de lead time con resultados de signo opuesto. El retiro es coherente con el Pilar 3 del marco (márgenes de error declarados, prohibidos los atajos). Ya no hay ninguna clasificación, nacional ni departamental, presentada como predicción en producción.

**Dónde sobrevive.** Como **referencia histórica**: un panel colapsable «Clasificador histórico» con la marca «Retirado» (`web/src/components/MetricasModelo.astro`), el endpoint `GET /api/riesgo-nacional` (que responde `disponible: false` si faltan los artefactos, issue #72) y los artefactos versionados a propósito (`dataset_modelado.csv`, `clasificador_riesgo_nacional_v1.joblib`, `metricas_modelo.json`; issue #72, 2026-09-13).

### Camino Ancho

**Qué es.** Nombre de narrativa de producto tras el retiro del clasificador (2026-08-18): una herramienta **descriptiva** de análisis espacio-temporal.

**En el proyecto.** La pregunta central pasó de «¿habrá un brote?» a «¿qué está ocurriendo epidemiológica y ambientalmente en cada departamento, qué tan inusual es respecto a su historia y qué tan confiable es la información?», organizada en los módulos M1 a M4. Se enmendó el 2026-09-09: ya no debe leerse como «el proyecto no predice nada», por el nowcast. Ver [Módulos descriptivos](05-modulos-descriptivos-y-alertas.md#módulos-descriptivos-m1-a-m4).

### Opción C (pivote de fase 1)

**Qué es.** El plan intermedio del 2026-08-09: un clasificador **nacional** primero, con la serie nacional de OpenDengue como variable objetivo.

**En el proyecto.** Superado el 2026-08-18 por el pivote «Camino Ancho». Queda como historia de cómo se llegó; ya no hay clasificador departamental que «activar».

### Dataset de modelado

**Qué es.** La tabla de entrenamiento del clasificador: una fila por semana nacional con predictores y etiqueta.

**En el proyecto.** 250 filas y 21 predictores en producción (2018, 2019, 2021–2023). `construir_dataset_modelado.py` agrega el clima de los 14 departamentos por **promedio simple** y no escribe en Postgres, porque no existe tabla para él (crearla exigiría ADR). Sus derivados versionados son evidencia del clasificador retirado.

### Etiqueta de riesgo (P75/P90)

**Qué es.** La clase alto, medio o bajo de cada semana.

**En el proyecto.** Se construye por canal endémico con comparaciones **estrictas**: `alto` si casos > P90, `medio` si casos > P75 y ≤ P90, `bajo` si casos ≤ P75. La igualdad con un corte queda en la clase inferior. El año etiquetado nunca entra en su propio pool.

### Cortes de percentil (P50/P75 y P75/P90)

**Qué es.** Los dos pares de percentiles con que se puede partir una línea base.

**En el proyecto.** **P75/P90** es el corte del clasificador (cerrado 2026-08-15) y **no** reproduce el canal endémico clásico de la OPS. **P50/P75** es el que sí lo reproduce (0 discrepancias en 250 celdas, ver [Zonas del canal endémico OPS](01-epidemiologia-y-vigilancia.md#zonas-del-canal-endémico-ops)) y el que usa M3. Se probó `p50_p75` en el clasificador para dar más ejemplos positivos (25 % superior en vez de 10 %), y se mantuvo P75/P90 por decisión cerrada. M3 acepta que P50/P75 pueda sobre-etiquetar semanas de años de baja transmisión: trade-off consciente.

### Etiqueta legada y etiqueta prospectiva

**Qué es.** Dos construcciones de la misma etiqueta con distinta historia.

**En el proyecto.** La **legada** usa un pool fijo de años base que puede incluir años posteriores al etiquetado; en ella 2019 tiene 28 semanas «alto» y 2022 tiene 22. La **prospectiva** usa la historia expansiva `H(y)`; con ella solo 2022 tiene «alto» (5 semanas) y 2019 tiene 0. Ampliar la línea base redefine «alto» para todo el histórico: al agregar 2014 y 2015 al pool, 2019 pasó de 28 semanas «alto» a 1.

### Efecto año

**Qué es.** Que una etiqueta relativa a la historia mida más el tamaño del año que lo que ocurre en una semana.

**En el proyecto.** La etiqueta del clasificador correlacionaba **0,955** con el total anual de casos. El tamaño muestral efectivo eran **5 años, con 2 ejemplos positivos**, no 250 filas. Además, el canal endémico condiciona por semana epidemiológica y elimina buena parte de la estacionalidad media, dando mucho peso a la amplitud interanual, que depende de serotipo, inmunidad acumulada, introducción del virus, movilidad y control de vectores: variables que no están en el dataset.

### Random Forest

**Qué es.** Conjunto de árboles de decisión entrenados con muestras aleatorias, cuyo voto decide la clase.

**En el proyecto.** `RandomForestClassifier` con 300 árboles y `class_weight="balanced"`; se predice con `.predict()` (argmax de clases). También se probaron GradientBoosting, ExtraTrees y regresión logística, con recall 0,000 en todos.

**Ojo.** Un Random Forest **no puede emitir una clase que nunca observó**: es la causa inmediata de los 0 de 5 aciertos de las Vías 1 y 3 en 2022, cuyo entrenamiento no tenía ningún «alto».

### Predictores del clasificador (21)

**Qué es.** Las columnas de entrada.

**En el proyecto.** Siete variables climáticas nacionales × tres transformaciones (rezago 1, rezago 2 y media de las cuatro semanas anteriores) = 21. Ninguna incluye la semana objetivo; los rezagos climáticos **sí cruzan el año** (el clima es continuo), pero la línea base de la etiqueta **nunca** puede ver el año que etiqueta. Son dos reglas distintas y siguen aplicando las dos. Ampliar la media a 8 y 12 semanas no mejoró nada y se revirtió.

### F1 macro

**Qué es.** Promedio simple del F1 (media armónica de precisión y recall) de las tres clases.

**En el proyecto.** Se calcula con las tres clases fijas (`bajo`, `medio`, `alto`) y `zero_division=0` aunque alguna no aparezca en el externo. Por eso una predicción perfecta de las 52 semanas `bajo` produce F1 macro **0,333**, no 1,000.

### Recall de «alto» y aciertos absolutos

**Qué es.** Proporción de semanas realmente «alto» que el modelo detecta.

**En el proyecto.** Regla de reporte: cada recall se acompaña de sus **aciertos absolutos** (`X de Y`) y un año sin semanas «alto» declara `N/A — 0 de 0`, nunca 0. Motivo: con un único acierto aislado la parte del criterio basada en recall ya «se superaba» (tres de los seis años marcados «SUPERA» en el multipaís eran 1 de 109, 1 de 140 y 1 de 4).

### Matriz de confusión, falsos positivos, AUC y soporte

**Qué es.** Herramientas estándar de evaluación de clasificadores.

**En el proyecto.** Se guardan la matriz 3×3, los **falsos positivos de «alto»** (importantes cuando el soporte real es cero), el **soporte** por clase, y AUC ROC y curva precisión–recall solo si hay positivos y negativos. El AUC de la probabilidad de «alto» fue 0,234 en 2019 y 0,231 en 2022, por debajo de 0,5: la probabilidad ordenaba peor que el azar. Si el entrenamiento no contiene la clase, el AUC sale 0,500 y no representa capacidad de ordenamiento.

### Referencias del clasificador

**Qué es.** Cuatro comparadores que se reportan siempre.

**En el proyecto.**

1. **Climatológica:** clase modal por semana epidemiológica entre las filas de entrenamiento (si la semana no existe, la moda global). Su recall de «alto» es 0,000 **por construcción**, porque casi siempre la moda es «bajo».
2. **Constante mayoritaria:** la clase más frecuente en el entrenamiento.
3. **Siempre «alto»:** control de cordura; su recall es 1,000 por construcción.
4. **Persistencia:** la etiqueta real de la semana anterior del año externo; **retrospectiva y no desplegable**.

Los empates se resuelven por la clase más frecuente del entrenamiento y luego por el orden fijo `bajo`, `medio`, `alto`.

### Veto de constantes

**Qué es.** Regla de la decisión D3: un resultado no cuenta como éxito si cualquiera de los dos predictores constantes supera al modelo en F1 macro.

**En el proyecto.** Existe por un caso de la corrida regional multipaís: en 2024, con el 65 % de las filas en «alto», el modelo obtuvo F1 macro 0,139 mientras «siempre alto» habría obtenido 0,262, es decir, el modelo «superó» el criterio en el año en que fue peor que la respuesta más tonta. Persistencia y constantes se reportan, pero no se convierten en umbrales adicionales.

### Vías de rescate (−1 a 4)

**Qué es.** Los experimentos independientes de la tarea de rescate de la predicción (asignada a Isaac, revisada por la coordinación), cada uno con su informe.

**En el proyecto.**

| Vía | Pregunta | Resultado | Cierre |
|---|---|---|---|
| −1 | ¿La evaluación puede ejecutarse sin fuga temporal? | Mecanismo validado; 17 pruebas, control mutante y repetibilidad | Usar el protocolo para interpretar, no como evidencia predictiva |
| 0 | ¿El modelo regional transfiere a países no vistos? | 0 de 16 países con transferencia sostenida | Cerrar multipaís |
| 1 | ¿Casos previos rescatan la etiqueta y el clima añade valor? | 0 de 10 semillas en el único fold evaluable; clima sin aporte | No adoptar |
| 2 | ¿El clima clasifica la posición relativa dentro de la temporada? | Éxito estable en 3 de 5 folds; 2019 falla 0/10 y 2024 queda en 8/10 | No adoptar |
| 3 | ¿Features con mecanismo biológico rescatan la etiqueta? | 0 de 10 semillas en el único fold evaluable | No adoptar |
| 4 | Clasificador departamental | Bloqueada: con el piso de suficiencia el 100 % de las celdas departamentales queda por debajo | No ejecutar salvo solicitud explícita |

**Ojo.** Ninguna corrida modifica PostgreSQL, el esquema, los pipelines ni los modelos de producción.

### Vía −1 (protocolo de validación limpia)

**Qué es.** Congelar y verificar una validación sin fuga **antes** de correr las demás vías; no busca mejorar una métrica.

**En el proyecto.** Aprobada el 2026-08-18. Define folds externos por año completo (2019, 2021, 2022, 2023 y 2024), etiquetas con `H(y)` y las cuatro referencias. Confirma que **no existe ningún fold** con «alto» tanto en el entrenamiento como en el externo: el único externo con «alto» es 2022 (5 semanas) y su entrenamiento tiene 150 `bajo`, 2 `medio` y 0 `alto`. El Random Forest predice `bajo` las 52 semanas en las 10 semillas (F1 macro 0,273, recall 0 de 5). Valida el mecanismo, no el desempeño. 2016 se rechazó como fold prospectivo porque `H(2016)` solo tiene 2014 y 2015.

### Vía 0 (multipaís, leave-one-country-out)

**Qué es.** Repetir el experimento multipaís dejando fuera un país entero cada vez.

**En el proyecto.** Datos: OpenDengue Admin0 semanal de 18 países (574 semanas por país, 2014–2024); con clima quedan 16, porque Bermuda y Virgin Islands (US) devuelven `null` en las cinco variables de `era5_land` (islas muy pequeñas). Resultado: 0 de 16 países con transferencia sostenida; de 52 folds evaluables solo Bolivia 2024 tiene éxito en las 10 semillas. La regla congelada era: 0–8 países = cerrar, 9–11 = inconcluso, 12–16 = transferencia mayoritaria.

### Multipaís

**Qué es.** Entrenar el clasificador con países de las Américas y probar en El Salvador.

**En el proyecto.** Falla en las 5 corridas evaluables y en las 11 semillas de cada una (0 de 55). El Salvador correlaciona apenas **+0,280** con la señal interanual compartida de la región (R² ≈ 0,08), el más desacoplado de 18 países (Colombia +0,952, Guatemala +0,908, Honduras +0,868). El clima es casi una «huella dactilar» del país: el modelo podía aprender «este perfil climático es Colombia» sin aprender relación clima–brote transferible. Simplificación declarada: un punto representativo por país.

### Vía 1 (casos previos)

**Qué es.** Usar como predictor los casos de las semanas anteriores.

**En el proyecto.** Dos firmas congeladas: `solo_casos` (rezago 1, rezago 2 y media de 4 semanas) y `casos_mas_clima` (esas más los 21 climáticos). Dan resultados idénticos: el clima no aporta. Toca dos decisiones cerradas (predictor solo climático y promesa de anticipación); la autorización habilitó la corrida, no adoptó el resultado. Aunque funcionara, sería estimación del presente.

### Vía 2 (etiqueta intraanual)

**Qué es.** Definir «alto» **dentro de cada año** en vez de contra el histórico.

**En el proyecto.** `bajo` si casos ≤ P50 del mismo año, `medio` si > P50 y ≤ P75, `alto` si > P75: cada año da 26 `bajo`, 13 `medio` y 13 `alto`. Cambia la pregunta de «¿qué tan grande es este año?» a «¿en qué punto de la temporada estamos?». Es **retrospectiva** (la etiqueta usa semanas futuras del mismo año) y crea un problema de comunicación: una semana «alto» de un año de baja transmisión puede tener menos casos que una «bajo» de un año severo.

### Vía 3 (features con mecanismo biológico)

**Qué es.** Reemplazar los 21 rezagos crudos por siete transformaciones inspiradas en la biología del mosquito.

**En el proyecto.** Racha térmica (semanas consecutivas entre 17,8 y 34,6 °C, máximo 8), grados-día (`7 × max(min(T, 35) − 16, 0)` en 4 semanas), semanas de temperatura y humedad óptimas, interacción termohigrométrica, amplitud térmica, duración de lluvia y pulso seco→húmedo. No se construyó «días con lluvia sobre un mínimo» porque el volcado no conserva observaciones diarias: inferirlo habría fabricado información. La racha térmica vale 8 en las 308 filas: el rango térmico general de transmisión es demasiado amplio para separar semanas dentro del clima nacional. Son **proxies inspirados en mecanismos**, no un modelo entomológico.

### Estados de un fold

**Qué es.** Clasificación previa a ajustar el modelo de si un fold es utilizable.

**En el proyecto.** `entrenable` (filas y al menos dos clases reales), `entrenable_con_clase_ausente` (falta una de las tres; se corre como diagnóstico y no se atribuye capacidad de aprender esa clase), `no_entrenable` (sin filas o de una sola clase) y `recall_alto_no_evaluable` (el externo tiene cero filas «alto»). Nunca justifican descartar el fold. Matriz congelada: 2019 `no_entrenable`; 2021 y 2022 `entrenable_con_clase_ausente`; 2023 y 2024 `entrenable`, con recall `N/A`.

### D1 a D4

**Qué es.** Cuatro decisiones firmadas por la coordinación el 2026-08-18 en la respuesta al protocolo.

**En el proyecto.** **D1:** excluir 2020 de objetivo y de pool, en todo país y toda vía. **D2:** retirar 2016 como segundo externo y reservar 2024 con recall de «alto» en `N/A`. **D3:** cuatro referencias, climatológica decisiva y veto de constantes. **D4:** argmax fijo (`.predict()`). El registro formal de D1 y D3 en las decisiones cerradas queda a cargo de la coordinación.

### Informe de cierre del rescate

**Qué es.** Documento del 2026-08-18 que cierra la línea de rescate.

**En el proyecto.** Recomienda **cerrar sin adoptar ningún modelo experimental** y entregar el resultado negativo como evidencia reproducible: el proyecto auditó fuga, transferencia, autorregresión, cambio de objetivo y features con mecanismo sin escoger configuraciones después de ver los externos. No integrar una clasificación experimental al tablero como si fuera una alerta.

### Experimento ventana climática ampliada

**Qué es.** Probar medias móviles de 4, 8 y 12 semanas en lugar de solo 4.

**En el proyecto.** Resultado negativo: el recall de «alto» siguió en 0,000 en 2019 y 2022 y empeoró el F1 macro del modelo de producción en 2023. Se revirtió. No se reabre sin una señal distinta de que el problema es de ventana.

## 5. Lead time, percentiles y comparación con la propia historia

### Lead time (tiempo de anticipación)

**Qué es.** Semanas entre la primera alerta del detector (semana de detección) y el inicio real de la temporada; positivo significa que el detector se adelantó.

**En el proyecto.** El experimento del 2026-08-18 lo midió para `Iv` más el detector de anomalías y **no sostuvo la tesis de una ventana de anticipación**: de los dos únicos casos comparables, el nacional (2018) dio **+29** semanas y el departamental (San Salvador, 2023) **−30**, sin acuerdo de signo. En 3 de 5 años nacionales y 3 de 5 departamentales el detector no disparó ninguna alerta, pese a que el Z-score cruzó 1,5 en todos los años. La tesis se retiró del pitch y del informe; `lead_time_weeks` no se expone.

**Ojo.** Cada cifra descansa en n = 1 por nivel y no debe presentarse como estadística robusta. Solo San Salvador califica de los 14 departamentos, con una suficiencia relajada (≥ 3 de 5 años base con ≥ 8 semanas de actividad no nula); sus años 2018 y 2019 dan inicio en la semana 1 (pool degenerado) y se excluyen de la mediana.

### RIC (rango intercuartílico)

**Qué es.** Distancia entre los percentiles 25 y 75 de un conjunto de valores.

**En el proyecto.** Se reportó junto a la mediana del lead time; con un solo caso, el RIC es un punto (por ejemplo [29,0; 29,0]).

### Umbral Z ≥ 1,5 durante dos semanas

**Qué es.** Regla literal del documento de diseño para disparar una alerta de anomalía.

**En el proyecto.** Se usó en el experimento de lead time y **se retiró**: el umbral se cruza en el 100 % de los años evaluados y no discrimina. M2 expone solo la serie continua.

### Percentil (interpolación lineal inclusiva)

**Qué es.** Valor por debajo del cual queda una proporción dada de un conjunto ordenado.

**En el proyecto.** Para el pool ordenado `x` de tamaño `n`: posición = `p × (n − 1)` y `Q(p)` es la interpolación lineal entre `x[⌊posición⌋]` y `x[⌈posición⌉]` (método «inclusive», igual que `statistics.quantiles`, sin agregar NumPy). Está duplicado a mano en `idoneidad.py` y en `corrida_canal_endemico_nacional.py`.

### Percentil relativo (`rango_percentil`)

**Qué es.** El lugar (0–100) que ocupa un valor observado dentro del pool.

**En el proyecto.** Es la inversa de la interpolación anterior. Los empates se resuelven con el punto medio del tramo empatado y los valores fuera del rango saturan en 0 o 100: describe dónde cae el valor **dentro de la historia observada**, no extrapola. M3 lo expone junto a la lectura `baja`, `media` o `alta`.

### Pool (línea base)

**Qué es.** Conjunto de observaciones históricas con que se compara una celda.

**En el proyecto.** Para la celda `(y, w)`: por cada año base distinto de `y`, las observaciones realmente presentes en las semanas `w−1`, `w` y `w+1`. Nunca incluye el año descrito ni años posteriores (en el protocolo prospectivo), y cuenta observaciones **presentes**, no esperadas.

### Ventana ±1 (semanas vecinas)

**Qué es.** Tomar la semana y sus dos vecinas para tener más observaciones.

**En el proyecto.** **No envuelve entre años**: la semana 1 pierde su vecina «semana 0» y la última semana del año pierde la siguiente. Es la ventana mínima aritméticamente viable. La corrida exploratoria de MINSAL (`corrida_distribucion.py`) no la implementaba pese a una afirmación previa incorrecta; la primera aplicación real fue el canal endémico nacional.

**Ojo.** M2 (`Iv`) **no** usa ventana de semanas vecinas: compara la misma semana exacta.

### Piso de suficiencia

**Qué es.** Mínimo de historia para que una celda tenga línea base.

**En el proyecto.** Hay dos pisos según el contexto. **Etiqueta del clasificador y canal endémico nacional:** al menos **12 observaciones y 3 años** (`PISO_OBSERVACIONES = 12`, `PISO_ANIOS_MIN = 3`); las celdas que no lo alcanzan quedan `sin_suficiencia_etiqueta`. **M3 departamental:** solo **al menos 3 de los 4 años leave-one-out** con alguna observación en la ventana (cuentan años distintos, no semanas). Si no se cumple, `percentil` es `null` con nota y nunca se interpola.

**Ojo.** Con el piso de 12 observaciones el 100 % de las celdas departamentales queda por debajo: es el motivo del bloqueo de la Vía 4.

### Años base

**Qué es.** Los años que forman la línea base.

**En el proyecto.** 2018, 2019, 2021, 2022 y 2023 (`ANIOS_BASE`), con 2020 excluido. Con cuatro años leave-one-out y ventana ±1, el pool nominal tiene 12 observaciones.

### Z-score y `anomaly_sigma`

**Qué es.** Distancia de un valor a la mediana o media de su línea base, en desviaciones estándar.

**En el proyecto.** M2 calcula el Z-score leave-one-out de `Iv` por (departamento, semana del año) y lo expone como serie continua `anomaly_sigma`. Ver [M2](05-modulos-descriptivos-y-alertas.md#m2-anomalía-climática-continua).

### Chequeo de cordura

**Qué es.** Verificar que una distribución no sea degenerada antes de seguir.

**En el proyecto.** El script de lead time sobre 8.036 observaciones de `Iv` (media 0,450, mediana 0,387, desviación 0,224, rango 0,027–0,923) **aborta con `SystemExit`** si la distribución sale constante o saturada en 0 o 1.

### Agregado nacional simple

**Qué es.** Promedio no ponderado de los 14 departamentos.

**En el proyecto.** Es lo que usan el dataset del clasificador y el nowcast para el clima nacional. No existe una decisión de ponderación poblacional cerrada; es un supuesto explícito de cada experimento y no una convención establecida.
