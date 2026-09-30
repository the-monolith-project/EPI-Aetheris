# Rama 5 · Módulos descriptivos y alertas

Vocabulario de las funciones que el producto ofrece hoy: los cuatro módulos descriptivos (M1 a M4), el observatorio respiratorio, el dataset analítico y las alertas de campo. Explica qué mide cada módulo, con qué fórmula, y qué **no** hace.

**Para quién es.** Para quien lee un panel de `/analisis`, la respuesta de un endpoint `/api/v1/...` o una alerta de `/alertas` y necesita saber qué significan `Iv`, `anomaly_sigma`, «percentil de presión», «antigüedad» o «alerta activa».

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris, con las fórmulas y constantes exactas), **Dónde** (archivo, ADR o endpoint) y **Ojo** (errores frecuentes). Las expansiones de siglas que el repositorio no da se marcan como «de uso general».

**Ramas vecinas.** La estadística que hay detrás (percentiles, leave-one-out, z-score) está en [`04-estadistica-y-modelado.md`](04-estadistica-y-modelado.md); las variables climáticas de M1 y M2, en [`03-clima-y-ambiente.md`](03-clima-y-ambiente.md); la API y sus contratos, en [`06-backend-y-api.md`](06-backend-y-api.md); las pantallas, en [`09-frontend-web.md`](09-frontend-web.md).

<!-- INDICE:INICIO -->

## Índice alfabético (44 entradas)

- **A** — [Alcance territorial (departamentos)](#alcance-territorial-departamentos) · [Alerta de campo](#alerta-de-campo) · [anomaly_sigma](#anomaly_sigma) · [Antigüedad (M4)](#antigüedad-m4) · [Archivo de alertas](#archivo-de-alertas) · [Aviso de honestidad (AVISO_HONESTIDAD_)](#aviso-de-honestidad-aviso_honestidad_) · [Aviso de virus](#aviso-de-virus)
- **C** — [Cálculo on-request (nada persistido)](#cálculo-on-request-nada-persistido) · [Campos clínicos de una alerta](#campos-clínicos-de-una-alerta) · [Campos prohibidos (CAMPOS_PROHIBIDOS)](#campos-prohibidos-campos_prohibidos) · [Canal endémico (panel)](#canal-endémico-panel) · [Capa «Integridad de la vigilancia» (confianza)](#capa-integridad-de-la-vigilancia-confianza) · [Completitud](#completitud) · [Constantes del corpus respiratorio](#constantes-del-corpus-respiratorio) · [Contrato de respuesta de alertas](#contrato-de-respuesta-de-alertas) · [Cuadre](#cuadre)
- **D** — [Dataset analítico anual de dengue](#dataset-analítico-anual-de-dengue) · [Dos series, nunca fusionadas](#dos-series-nunca-fusionadas) · [Duplicado deliberado (sin paquete compartido)](#duplicado-deliberado-sin-paquete-compartido)
- **E** — [Enfoque dual (consulta y análisis)](#enfoque-dual-consulta-y-análisis) · [Equipo de vigilancia](#equipo-de-vigilancia) · [Escritura autenticada de alertas](#escritura-autenticada-de-alertas) · [Estimación propia del equipo](#estimación-propia-del-equipo) · [Etiqueta de alerta (test, simulacro, historica)](#etiqueta-de-alerta-test-simulacro-historica)
- **F** — [f_H (rampa, humedad)](#f_h-rampa-humedad) · [f_R (logística, precipitación)](#f_r-logística-precipitación) · [f_T (Brière, temperatura)](#f_t-brière-temperatura) · [Feed Atom de alertas](#feed-atom-de-alertas)
- **I** — [Insuficiente y sin observación](#insuficiente-y-sin-observación)
- **M** — [M1: idoneidad biofísica (Iv)](#m1-idoneidad-biofísica-iv) · [M2: anomalía climática continua](#m2-anomalía-climática-continua) · [M3: presión epidemiológica relativa](#m3-presión-epidemiológica-relativa) · [M4: integridad de la vigilancia](#m4-integridad-de-la-vigilancia) · [Módulos descriptivos (M1 a M4)](#módulos-descriptivos-m1-a-m4) · [Mordecai et al. (2017)](#mordecai-et-al-2017)
- **N** — [Nivel de alerta](#nivel-de-alerta)
- **O** — [Observatorio respiratorio](#observatorio-respiratorio)
- **P** — [Panel de auditoría de datos (AuditoriaDatos)](#panel-de-auditoría-de-datos-auditoriadatos) · [Panel de cobertura respiratoria](#panel-de-cobertura-respiratoria) · [Percentil de presión](#percentil-de-presión) · [Procedencia de una observación](#procedencia-de-una-observación)
- **T** — [Tipo de alerta](#tipo-de-alerta) · [Transcripción citada](#transcripción-citada)
- **V** — [Vigencia y activa](#vigencia-y-activa)

<!-- INDICE:FIN -->

## 1. Los módulos descriptivos en general

### Módulos descriptivos (M1 a M4)

**Qué es.** Las cuatro funciones de la herramienta «Camino Ancho»: cada una compara una serie con su propia historia o describe la calidad del dato. **Ninguna emite alerta automática, clasifica riesgo de brote ni predice.**

**En el proyecto.**

| Módulo | Responde | Insumo | Endpoint |
|---|---|---|---|
| M1 `Iv` | ¿Qué tan favorable es el clima de un departamento-semana para *Aedes aegypti*? | Clima (Open-Meteo) | `GET /api/v1/spatial/current`, `GET /api/v1/temporal/{codigo}` |
| M2 `anomaly_sigma` | ¿Qué tan inusual es ese `Iv` frente a su propia historia? | `Iv` | los mismos |
| M3 percentil | ¿Qué tan alta es la presión de casos **ya observados** frente a la historia del departamento? | Casos MINSAL | `GET /api/v1/presion/current`, `GET /api/v1/presion/temporal/{codigo}` |
| M4 integridad | ¿Qué tan completo, cuadrado y reciente es el dato? | Bitácora y tablas | `GET /api/v1/vigilancia/integridad` |

M1, M2 y M3 se calculan **al consultar la API**, sin tabla propia y sin cambio de esquema; M4 también.

**Dónde.** `backend/api/idoneidad.py` (M1, M2), `backend/api/presion.py` (M3), `backend/api/vigilancia.py` (M4), [`docs/biblioteca/03-funciones.md`](../biblioteca/03-funciones.md).

### Cálculo on-request (nada persistido)

**Qué es.** Calcular el resultado en cada petición a partir de las tablas existentes, en lugar de guardarlo.

**En el proyecto.** Es el patrón de M1 a M4: sin tabla nueva y sin migración. Contrasta con las alertas (texto humano persistido) y con el nowcast (artefacto precomputado y versionado).

### Aviso de honestidad (`AVISO_HONESTIDAD_*`)

**Qué es.** Constante de texto que cada módulo o endpoint devuelve para declarar qué mide y qué niega.

**En el proyecto.** Existen `AVISO_HONESTIDAD_IDONEIDAD`, `AVISO_HONESTIDAD_VIGILANCIA`, `AVISO_HONESTIDAD_VIRUS`, `AVISO_COBERTURA` y `AVISO_HONESTIDAD_ALERTAS`. Por ejemplo, el de M4 dice que describe qué tan completo y reciente es el dato disponible, no la transmisión ni el riesgo, y que **un departamento sin fila esa semana es un hueco real, no un cero ni un departamento seguro**. La declaración canónica de los límites está en la [Biblioteca 05](../biblioteca/05-sensibilidad-y-honestidad.md).

### Campos prohibidos (`CAMPOS_PROHIBIDOS`)

**Qué es.** Lista de nombres que la respuesta de M4 nunca debe traer.

**En el proyecto.** `indice`, `indice_compuesto`, `score`, `confianza`, `riesgo`, `alerta`, `alert`, `lead_time` y `lead_time_weeks`. Es la forma de hacer cumplir por código el contrato «sin índice compuesto y sin lenguaje de alerta».

### Duplicado deliberado (sin paquete compartido)

**Qué es.** Copiar a mano una función porque `backend/api` y `backend/ingestion` no comparten paquete.

**En el proyecto.** Se duplican las fórmulas de `Iv`, el método de Z-score, `percentil()`, `ANIOS_CLIMA` y las funciones de ventana y pool. La copia es literal (mismas constantes), no una reimplementación independiente. Un test de fórmulas duplicadas falla si se desincronizan; si las fórmulas cambian en un lado, deben cambiar en el otro a mano.

## 2. M1: idoneidad biofísica (`Iv`)

### M1: idoneidad biofísica (`Iv`)

**Qué es.** Índice continuo de 0 a 1 que resume qué tan favorables son la temperatura, la lluvia y la humedad de una semana para el vector del dengue (*Aedes aegypti*). Describe **el clima, no casos**.

**En el proyecto.** `Iv = f_T(T) × (0,3 + 0,7 · f_R(R)) × f_H(HR)`, con `T` la temperatura media semanal, `R` la precipitación acumulada a dos semanas y `HR` la humedad relativa media. Los insumos son `temp_media` y `humedad_relativa_media` de ERA5-Land y `precipitation_sum` de ERA5; una semana a la que le falte alguna de las tres variables se **omite** (no se imputa). El chequeo de cordura sobre 8.036 observaciones dio media 0,450, mediana 0,387, desviación 0,224 y rango 0,027 a 0,923.

**Dónde.** `backend/api/idoneidad.py`, `backend/ingestion/validar_leadtime_idoneidad.py`.

**Ojo.** No clasifica riesgo de brote ni adelanta una temporada. Que `Iv` y el percentil de casos coincidan una semana es [coexistencia, no causalidad](01-epidemiologia-y-vigilancia.md#coexistencia-temporal-no-es-causalidad).

### `f_T` (Brière, temperatura)

**Qué es.** Idoneidad térmica con la forma de **Brière**, una curva asimétrica de desarrollo que crece hasta un óptimo y cae bruscamente cerca del límite superior.

**En el proyecto.** `f_T(T) = c · T · (T − Tmin) · √(Tmax − T)` para `Tmin < T < Tmax` con **Tmin = 16 °C y Tmax = 38 °C**, y **0** fuera de ese intervalo. La constante de normalización `c` **no viene publicada**: se resuelve numéricamente con una búsqueda en malla fina (paso de 0,001 °C) para que el máximo de `f_T` en el intervalo sea 1; da `c ≈ 0,000795`. El módulo la recalcula en lugar de copiar el número, para no arriesgar un desfase silencioso.

### `f_R` (logística, precipitación)

**Qué es.** Idoneidad hídrica: una función logística (curva en S) sobre la lluvia acumulada.

**En el proyecto.** `f_R(R) = 1 / (1 + e^(−k·(R − R0)))` con **R0 = 30 mm** y **k = 0,1**, sobre la precipitación **acumulada a dos semanas** (la semana actual más la anterior, sin envolver entre años: si la semana anterior no existe, como en la semana 1, se usa solo la actual).

### `f_H` (rampa, humedad)

**Qué es.** Idoneidad por humedad relativa.

**En el proyecto.** `f_H(HR) = min(1, max(0, HR / 50))`: una **rampa lineal** que vale 0 con HR = 0 % y 1 desde HR = 50 %. Es una **estimación propia del equipo, no citada**: el documento de diseño solo pedía «penaliza humedad relativa bajo 50 %», sin fórmula, y ni Mordecai et al. ni la tesis de la UES la especifican. Se eligió la forma más simple que cumple ese requisito cualitativo, y la interfaz la marca como tal.

**Ojo.** Si se reemplazara por otra forma (logística, curva de la literatura), los números cambian y habría que rehacer las corridas, no ajustar el resultado a mano.

### Mordecai et al. (2017)

**Qué es.** Referencia bibliográfica del modelo térmico de transmisión en el que se apoyan el rango de temperatura y el carácter no lineal de `f_T` (DOI `10.1371/journal.pntd.0005568`).

**En el proyecto.** Respalda el rango térmico y el carácter no lineal de `f_T` y las constantes `Tmin` y `Tmax` como «calibración inicial a verificar», no como parámetros validados en El Salvador.

### Estimación propia del equipo

**Qué es.** Etiqueta que el proyecto pone a cualquier fórmula o valor que no está trazado a una fuente citada.

**En el proyecto.** Es el caso de `f_H`. La regla es marcarla con esa etiqueta visible en el código y en el informe, en lugar de presentarla como validada.

## 3. M2: anomalía climática continua

### M2: anomalía climática continua

**Qué es.** Cuántas desviaciones estándar se aparta el `Iv` de una semana de lo habitual para ese departamento y esa semana del año.

**En el proyecto.** Z-score leave-one-out de `Iv` por (departamento, semana del año): `anomaly_sigma = (Iv − mediana) / desviación`. La línea base es el corpus de clima **desde 2014 hasta el año en curso** ([ADR 0018](../adr/0018-extension-capa-climatica-presente.md)), excluyendo el año descrito (anti-fuga), en la **misma semana exacta, sin ventana de semanas vecinas**. La mediana y la desviación (muestral, con `n − 1`) solo se calculan con **al menos 3 observaciones**; con una desviación casi nula (< 10⁻⁹) el resultado es `None`. Se expone como **serie continua** (`anomaly_sigma`).

**Ojo.** No emite alerta binaria, no habla de «temporada adelantada» y no expone `lead_time_weeks`. El umbral Z ≥ 1,5 durante dos semanas se retiró por cruzarse en el 100 % de los años ([Umbral Z](04-estadistica-y-modelado.md#umbral-z--15-durante-dos-semanas)). Al entrar años nuevos al pool, los σ ya mostrados para 2018–2023 se mueven.

### `anomaly_sigma`

**Qué es.** Campo de la respuesta de M2 con la anomalía en unidades de desviación estándar (σ).

**En el proyecto.** Aparece en `/api/v1/spatial/current` y `/api/v1/temporal/{codigo}` junto a `iv`. Es continuo: sin umbral, sin bandera.

## 4. M3: presión epidemiológica relativa

### M3: presión epidemiológica relativa

**Qué es.** Qué tan alto es el conteo de casos **ya observados** de un departamento-semana comparado con la historia de ese mismo departamento.

**En el proyecto.** Fórmula cerrada por la coordinación el **2026-08-21**:

| Elemento | Valor |
|---|---|
| Variable | `casos_epidemiologicos.conteo`, series `probable` y `confirmado` **por separado** (nunca fusionadas ni con `total`) |
| Método | Percentil histórico leave-one-out |
| Años base | 2018, 2019, 2021, 2022, 2023 (2020 fuera del baseline) |
| Ventana | ±1 semana, sin envolver entre años |
| Piso | Al menos 3 de los 4 años leave-one-out con alguna observación en la ventana |
| Cortes | P50 y P75 |
| Lectura | ≤ P50 `baja`; P50 < x ≤ P75 `media`; > P75 `alta`; más el percentil crudo 0–100 |
| Insuficiencia | `percentil = null` y una nota; no se interpola |

**Dónde.** `backend/api/presion.py`; el documento de decisión histórico está en el repositorio STC (`EPI-Aetheris/historico/modulos-descriptivos/modulo-3-presion-epidemiologica.md`).

**Ojo.** Un percentil alto describe lo ya ocurrido frente a la historia observada del departamento: no predice, no usa clima y no produce alerta binaria. **No compara departamentos entre sí.** El corte P50/P75 es más sensible que el P75/P90 del clasificador retirado y puede sobre-etiquetar semanas de años de baja transmisión: es un trade-off consciente, no un error.

### Percentil de presión

**Qué es.** Posición (0–100) de los casos de una semana entre los de otros años del mismo departamento.

**En el proyecto.** Campo `percentil` de M3, redondeado a un decimal. Va acompañado de `categoria` (`baja`, `media`, `alta`), `p50_baseline`, `p75_baseline`, `n_obs_baseline` y `anios_baseline`. Ver [Percentil relativo](04-estadistica-y-modelado.md#percentil-relativo-rango_percentil).

### Insuficiente y sin observación

**Qué es.** Los dos motivos por los que M3 no devuelve percentil.

**En el proyecto.** **Insuficiente:** menos de 3 años base aportan observaciones en la ventana ±1 (`NOTA_INSUFICIENTE`). **Sin observación:** no hay fila para esa semana y serie, es «hueco real de la fuente MINSAL, no un cero» (`NOTA_SIN_OBSERVACION`). En ambos casos `percentil`, `categoria` y los dos cortes van `null` y se añade `nota`.

### Dos series, nunca fusionadas

**Qué es.** M3 trata `probable` y `confirmado` como dos series independientes.

**En el proyecto.** No se suman ni se combinan y nunca se mezcla la clasificación `total` (la serie nacional de OpenDengue, otro concepto). La constante es `SERIES = ("probable", "confirmado")`.

### Canal endémico (panel)

**Qué es.** Panel de `/analisis` que dibuja los cortes de M3 como tres bandas con los casos observados encima. La definición epidemiológica está en [Canal endémico](01-epidemiologia-y-vigilancia.md#canal-endémico).

**En el proyecto.** Usa la línea base de M3, que deja fuera el año descrito, así que **la banda cambia de un año a otro**. Las semanas sin línea base suficiente quedan en blanco.

## 5. M4: integridad de la vigilancia

### M4: integridad de la vigilancia

**Qué es.** Tres hechos verificables sobre la calidad del dato, **sin combinarlos en un índice**: completitud, cuadre y antigüedad.

**En el proyecto.** Fórmula cerrada el 2026-09-08 ([ADR 0019](../adr/0019-integridad-vigilancia.md)). Responde «qué tan completo, cuadrado y reciente es el dato que mostramos», no «qué tan alta es la transmisión». Con `week` y `year` juntos devuelve la vista semanal del mapa; sin parámetros, el resumen anual y la antigüedad. Usa `RATE_LIMIT_HEAVY` y `Cache-Control` de 900 s.

**Ojo.** Un departamento sin color no es un departamento seguro: es un departamento sin fila esa semana.

### Completitud

**Qué es.** Cuántos de los 14 departamentos tienen fila en `casos_epidemiologicos` para `(año, semana_epi, clasificación)`.

**En el proyecto.** Se mide `n / 14` por semana, para dengue de MINSAL con `probable` y `confirmado` por separado. El agregado anual cuenta semanas con 14/14 frente a **52 nominales** (el mismo denominador que la cobertura respiratoria; no se inventa una semana 53 vacía). Las semanas ausentes son huecos y **no se convierten en `n = 0`**.

### Cuadre

**Qué es.** Si la suma departamental coincide con el total nacional impreso en el mismo boletín.

**En el proyecto.** M4 **expone** `validacion_cuadra` y la magnitud `suma_departamental − total_nacional_publicado` ya guardadas en `boletines_procesados`; no recalcula la suma de 14. Si falta uno de los dos lados, la discrepancia es `None` (no se fabrica un 0), y si no hay fila de bitácora el cuadre queda en `null`, no en `false`. Ver [Cuadre](02-fuentes-de-datos-e-ingesta.md#cuadre-validacion_cuadra).

### Antigüedad (M4)

**Qué es.** Semanas epidemiológicas entre hoy y la última semana con dato de cada serie.

**En el proyecto.** Se calcula con el calendario PAHO/CDC (librería `epiweeks`) para nueve series: `dengue_minsal_departamental`, `dengue_opendengue_nacional`, `dengue_tablero_nacional`, `clima`, `ira`, `neumonias`, `ira_tablero_nacional`, `neumonias_tablero_nacional` y `virus_respiratorios`. Convierte el corte de 2023 en una **cifra** y no en un silencio.

**Ojo.** **No es latencia de reporte** (retraso entre el caso y la publicación del boletín): esa fecha no está en la base, porque `boletines_procesados.fecha_procesado` es el timestamp de *nuestra* corrida del parser. Además depende de `date.today()`, así que con el cache de 15 minutos puede mostrar un valor desfasado en el borde de una semana; cambia como máximo una vez por semana.

### Capa «Integridad de la vigilancia» (`confianza`)

**Qué es.** Capa del mapa que codifica **únicamente** «hay dato / falta dato / el boletín no cuadra».

**En el proyecto.** El id de capa sigue siendo `'confianza'` para no romper el selector, pero la etiqueta visible es «Integridad de la vigilancia». No es un semáforo de riesgo.

### Panel de auditoría de datos (`AuditoriaDatos`)

**Qué es.** Componente que muestra la calidad y procedencia del dato.

**En el proyecto.** Es computado para la completitud anual y la antigüedad, y conserva **estáticos** los hechos que no son métrica (la ventana y la exclusión de 2020).

## 6. Dataset analítico y procedencia

### Dataset analítico anual de dengue

**Qué es.** Una sola lectura con las 53 semanas de cada departamento que reúne M1, M2 y M3.

**En el proyecto.** `GET /api/v1/analisis/dengue`. No define metodología nueva: reutiliza los motores de `idoneidad.py` y `presion.py` para los años base (`ANIOS_ANALISIS_DENGUE = ANIOS_BASE`). Los huecos permanecen como `None` y las series probable y confirmado nunca se fusionan.

### Procedencia de una observación

**Qué es.** La trazabilidad almacenada de una celda epidemiológica: de qué boletín salió.

**En el proyecto.** `GET /api/v1/analisis/dengue/procedencia?year=&week=&dept=&serie=`. Un código de departamento inexistente devuelve `None`; una región válida sin filas devuelve `disponible: false` y `registros: []`, sin fabricar una fuente para un dato ausente.

## 7. Observatorio respiratorio

### Observatorio respiratorio

**Qué es.** La sección `/respiratorio` que agrupa IRA, neumonías y la vigilancia laboratorial de virus. Misma familia de boletines MINSAL, **otras tablas y otra semántica**. No hay ruta `/ira` propia: IRA y neumonías son secciones de esa página.

**En el proyecto.**

- **Serie nacional de IRA y de neumonías:** casos notificados por semana según el tablero de MINSAL desde 2025, con una línea por año, la última semana comparada con la misma de un año antes, las semanas sin publicar y una tabla con los valores.
- **Neumonías:** conteo clínico departamental único, acumulado desde SE1, `clasificacion = 'notificado'`, `tipo_evento = 'neumonia'`.
- **IRA:** el mismo contrato de conteo notificado ([ADR 0011](../adr/0011-clasificacion-ira-departamental.md)), serie acumulada y desacumulada.
- **Vigilancia laboratorial nacional** ([ADR 0012](../adr/0012-persistencia-vigilancia-virus-respiratorios.md)): influenza, VSR y SARS-CoV-2 (muestras, detecciones, positividad). No hay mapa departamental de virus.
- **Panel de cobertura:** qué semanas y qué tablas están presentes.

**Ojo.** **No computa idoneidad, anomalía ni presión**: esas fórmulas están cerradas solo para dengue, y neumonías no hereda M1–M4.

### Panel de cobertura respiratoria

**Qué es.** Recuento de semanas con fila en la base frente a 52 nominales, más las notas ya documentadas por la exploración de los 264 PDF.

**En el proyecto.** `GET /api/respiratorios/cobertura`. No es M4. Las semanas sin fila son huecos, nunca ceros. Las notas son constantes del corpus congelado 2018–2019 y 2021–2023, que **hay que regenerar** si se incorpora 2020 o 2024+.

### Constantes del corpus respiratorio

**Qué es.** Hechos de la exploración de los 264 PDF que el panel de cobertura muestra.

**En el proyecto.** Neumonías: 25 tablas-imagen, 18 ausencias por vacaciones, 4 boletines sin texto extraíble, una reimpresión (`SE34/2019_v2 = SE33/2019`, 14 valores idénticos), 23 correcciones negativas excluidas y cortes usables por año (2018: 46, 2019: 22, 2021: 50, 2022: 48, 2023: 49). Virus: 3 tablas-imagen, 5 boletines sin texto extraíble, COVID-19 como fila solo en 2023, 2020 no descargado y granularidad nacional.

### Aviso de virus

**Qué es.** `AVISO_HONESTIDAD_VIRUS`.

**En el proyecto.** Declara que es vigilancia centinela y laboratorial de MINSAL a nivel nacional: muestras analizadas, detecciones por virus y positividad publicada por la fuente; **no son casos clínicos ni se desagregan por departamento**; «huecos = semanas sin fila». La API no convierte porcentajes en casos ni afirma causalidad.

## 8. Alertas de campo

### Alerta de campo

**Qué es.** Decisión **humana** y fechada que el equipo de vigilancia emite para quien atiende en una unidad de salud: qué muestran los datos y qué hacer.

**En el proyecto.** Se guarda en la tabla `alertas` ([ADR 0013](../adr/0013-alertas-de-campo-humanas.md), migración `0009`). El tipo y el nivel los asigna quien emite y **no se recalculan**: nada se rellena desde idoneidad, anomalía, presión, canal endémico ni el clasificador retirado, porque convertir un `Iv`, un Z-score o un percentil en alerta reabriría el lenguaje de aviso automático que el pivote retiró. Una alerta es un texto operativo firmado, no un conteo ni un atributo geográfico.

**Dónde.** `backend/api/alertas.py`, `GET /api/alertas`, `/alertas`, `/alertas/archivo`, `/alertas/nueva`.

**Ojo.** Las alertas de demostración y de prueba se separan con [etiquetas](#etiqueta-de-alerta-test-simulacro-historica); una alerta emitida nunca se borra.

### Tipo de alerta

**Qué es.** Campo `tipo`.

**En el proyecto.** Dos valores controlados: `dengue` y `respiratorio` (constante `TIPOS_ALERTA`). Un valor distinto en el filtro responde 422.

### Nivel de alerta

**Qué es.** Campo `nivel`.

**En el proyecto.** Tres valores: `informativo`, `atencion` e `intensificacion` (`NIVELES_ALERTA`). Lo elige quien emite; no es un semáforo de riesgo calculado. La interfaz acompaña cada nivel con su significado operativo (`SIGNIFICADO_NIVEL` en `vista-alertas.ts`):

| Nivel | Significado que muestra la tarjeta |
|---|---|
| Informativo | Sin señal relevante en los datos; recordatorio de vigilancia rutinaria |
| Atención | Los datos históricos recientes están por encima de lo esperado para la época; reforzar la notificación y la búsqueda de casos |
| Intensificación | Señal sostenida varias semanas o concentración territorial; activar medidas locales y coordinar con el SIBASI |

### Vigencia y `activa`

**Qué es.** El periodo en que una alerta aplica, más un interruptor.

**En el proyecto.** `vigente_desde` (obligatoria) y `vigente_hasta` (opcional; nula significa «sin fecha de cierre declarada», no vigencia infinita automática). **`activa` es el filtro principal** y no se infiere de `vigente_hasta`: una fila vencida que siga `activa` permanece visible hasta que el equipo la apague. Apagar una alerta es `PATCH` con `activa = false`.

### Etiqueta de alerta (`test`, `simulacro`, `historica`)

**Qué es.** Columna `etiqueta`, nula en el caso normal de producción.

**En el proyecto.** Tres valores permitidos: `test`, `simulacro` e `historica`. **Cualquier valor no nulo queda fuera del GET por defecto.** Si una fila etiquetada se renderiza, lleva el rótulo `ALERTA DE PRUEBA — NO ACTUAR SOBRE ESTA INFORMACIÓN` dentro de la tarjeta, como texto y no como un chip de color. Una fila inactiva y etiquetada necesita `incluir_inactivas` **e** `incluir_etiquetadas` para aparecer.

### Campos clínicos de una alerta

**Qué es.** Cinco columnas de texto opcionales: `definicion_caso`, `signos_alarma`, `criterios_referencia`, `que_notificar` y `contacto_vigilancia`.

**En el proyecto.** Son **contenedores**: se entregó el contenedor vacío y no el contenido inventado ([ADR 0014](../adr/0014-enfoque-dual-panorama-analisis.md)). La API los expone siempre (clave presente, valor posiblemente `null`) y la vista muestra cada bloque solo si tiene contenido. Se llenan por transcripción citada ([ADR 0015](../adr/0015-alertas-operables.md)): dengue desde VIGEPES y los algoritmos de la OPS; respiratorio solo `definicion_caso` y `que_notificar`, y **`signos_alarma` y `criterios_referencia` quedan `null`** porque VIGEPES define qué se notifica y no cuándo referir. El contacto describe la ruta SIBASI / VIGEPES-01 / UVET **sin teléfono ni correo**, porque el número del SIBASI del piloto no está en una fuente pública citada.

**Ojo.** Inventar un teléfono o un criterio de referencia para que la tarjeta «se vea completa» sería la peor versión de esta función. Alguien del equipo debe cotejar los bloques contra los PDF citados antes de tratarlos como texto de producción cerrado. Ver [vocabulario clínico](01-epidemiologia-y-vigilancia.md#8-vocabulario-clínico-de-las-alertas).

### Transcripción citada

**Qué es.** Copiar de una fuente oficial, con página y organismo, en lugar de redactar.

**En el proyecto.** Regla para los campos clínicos y para el material de prevención. **Sí está permitido** mostrar recomendaciones ya publicadas por OPS/OMS o MINSAL, citando la fuente (por ejemplo «elimine criaderos, revise depósitos de agua»); **no** que el sistema redacte indicaciones clínicas propias ni las derive del nivel de M1–M3, de M4 o del clasificador retirado.

### Alcance territorial (`departamentos`)

**Qué es.** Columna `alertas.departamentos TEXT[]` ([ADR 0022](../adr/0022-alertas-con-alcance-territorial.md)).

**En el proyecto.** **`NULL` significa alcance nacional**; una lista no vacía limita la alerta a esos departamentos (una lista vacía no se guarda: la API la convierte en `NULL`). Los elementos son códigos ISO 3166-2 y un `CHECK` rechaza cualquiera fuera de los 14. `GET /api/alertas?departamento=SV-SS` devuelve las nacionales y las que incluyen ese departamento; un código desconocido responde 422. Las alertas existentes quedaron nacionales.

**Ojo.** Una alerta regional no dice nada sobre los demás departamentos: **su ausencia no es una señal**.

### Escritura autenticada de alertas

**Qué es.** La creación y edición por la API, protegidas con un secreto compartido.

**En el proyecto.** `POST /api/alertas` y `PATCH /api/alertas/{id}` exigen `Authorization: Bearer <ALERTAS_TOKEN>`, comparado con `secrets.compare_digest`. Falta de cabecera y token incorrecto responden **401** sin distinguirse; si `ALERTAS_TOKEN` no está definido responde **503**; un cuerpo mal formado, **422**. **No hay `DELETE`**: una alerta emitida es un hecho registrado y se desactiva. No hay tabla de usuarios: un token compartido no es autorización por persona y no deja auditoría de quién lo usó. Ver [Bearer](06-backend-y-api.md#bearer-y-alertas_token).

### Archivo de alertas

**Qué es.** La vista compartible `/alertas/archivo` de lo emitido.

**En el proyecto.** Filtros por rango de fechas y tipo (en la URL, así que sobreviven a un refresh), más reciente primero. Una fila no vigente muestra un texto del tipo `NO VIGENTE — venció el DD/MM/AAAA`, no solo un color.

### Feed Atom de alertas

**Qué es.** `GET /api/alertas/feed.xml`, con las alertas activas y sin etiqueta en formato Atom.

**En el proyecto.** Mismo criterio que el GET público. La URL del sitio sale de la variable de entorno `SITIO_PUBLICO`.

### Contrato de respuesta de alertas

**Qué es.** Forma del cuerpo de `GET /api/alertas`.

**En el proyecto.** `{aviso, ultima_revision, alertas}`. A diferencia de los endpoints respiratorios, **no** se degrada a `disponible: false`: solo distingue fallo de conexión (503) del resto (500).

### Enfoque dual (consulta y análisis)

**Qué es.** Decisión del [ADR 0014](../adr/0014-enfoque-dual-panorama-analisis.md): el sitio atiende dos usos distintos con una sola arquitectura de información y **sin un interruptor de modo**.

**En el proyecto.** Cara de **consulta** (personal de salud en una unidad rural: poco tiempo, mala conexión, cero tolerancia a jerga estadística) y cara de **análisis** (equipo de vigilancia e investigadores). La navegación es `Inicio · Alertas · Análisis · Biblioteca · Sugerencias`, con `/dengue` y `/respiratorio` bajo el índice `/analisis`. La portada tiene dos «puertas» explícitas: «Personal de salud» hacia `/alertas` e «Investigación y datos» hacia `/analisis`. Se descartó el botón de modo porque no se descubre, la persona olvida en cuál está y los enlaces compartidos abrirían distinto según quién los reciba.

### Equipo de vigilancia

**Qué es.** Quien redacta las alertas.

**En el proyecto.** `AVISO_HONESTIDAD_ALERTAS` las atribuye al equipo de vigilancia del proyecto (INSAMT, Equipo 4) a partir de datos públicos históricos (MINSAL, OpenDengue, Open-Meteo) y aclara que **no reemplazan los lineamientos del MINSAL ni el criterio clínico**. El campo `autor` guarda un rol o iniciales, nunca datos personales. Ver [INSAMT y Equipo 4](10-proceso-gobernanza-y-documentacion.md#insamt-y-equipo-4).
