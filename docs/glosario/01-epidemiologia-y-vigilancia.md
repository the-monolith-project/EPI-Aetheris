# Rama 1 · Epidemiología y vigilancia

Vocabulario de salud pública que aparece en EPI-Aetheris: qué es un caso, cómo se cuenta el tiempo (semanas epidemiológicas), qué instituciones publican los datos, cómo se llaman las enfermedades vigiladas y cómo nombra el proyecto cada tipo de conteo.

**Para quién es.** Para quien lee los boletines de MINSAL, las alertas de campo, los paneles del sitio o las tablas de la base y necesita saber qué significa cada palabra antes de interpretar una cifra.

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris, con los valores exactos), **Dónde** (archivo, ADR o endpoint) y **Ojo** (errores frecuentes). Las definiciones generales de salud pública son de uso corriente; cuando el repositorio no expande una sigla, la entrada lo dice.

**Ramas vecinas.** Las fuentes y sus trampas están en [`02-fuentes-de-datos-e-ingesta.md`](02-fuentes-de-datos-e-ingesta.md); las fórmulas y métricas, en [`04-estadistica-y-modelado.md`](04-estadistica-y-modelado.md); los módulos del producto, en [`05-modulos-descriptivos-y-alertas.md`](05-modulos-descriptivos-y-alertas.md).

<!-- INDICE:INICIO -->

## Índice alfabético (96 entradas)

- **A** — [Aedes aegypti](#aedes-aegypti) · [AINE](#aine) · [Algoritmos OPS de manejo clínico de dengue](#algoritmos-ops-de-manejo-clínico-de-dengue) · [Año epidemiológico y año calendario](#año-epidemiológico-y-año-calendario) · [Año pico y años de referencia](#año-pico-y-años-de-referencia) · [Arbovirosis](#arbovirosis) · [Ascertainment (intensidad de vigilancia)](#ascertainment-intensidad-de-vigilancia)
- **B** — [Boletín epidemiológico semanal](#boletín-epidemiológico-semanal)
- **C** — [Canal endémico](#canal-endémico) · [Caso](#caso) · [Caso confirmado](#caso-confirmado) · [Caso probable](#caso-probable) · [Caso sospechoso](#caso-sospechoso) · [Casos observados](#casos-observados) · [CDC y MMWR](#cdc-y-mmwr) · [Celda vacía = 0](#celda-vacía--0) · [Chikungunya y zika](#chikungunya-y-zika) · [Clasificación (clasificacion)](#clasificación-clasificacion) · [Cobertura 14 de 14](#cobertura-14-de-14) · [Código ISO 3166-2:SV](#código-iso-3166-2sv) · [Coexistencia temporal (no es causalidad)](#coexistencia-temporal-no-es-causalidad) · [confirmado](#confirmado) · [Conteo (conteo)](#conteo-conteo) · [Conteo notificado](#conteo-notificado) · [Criterios de referencia](#criterios-de-referencia)
- **D** — [Definición de caso](#definición-de-caso) · [Dengue](#dengue) · [Dengue con y sin signos de alarma, y dengue grave](#dengue-con-y-sin-signos-de-alarma-y-dengue-grave) · [Denominador poblacional y Censo 2024](#denominador-poblacional-y-censo-2024) · [Departamento](#departamento) · [Detección](#detección)
- **E** — [Endemia](#endemia) · [Epidemia y brote](#epidemia-y-brote) · [Estertores crepitantes, matidez e infiltrado](#estertores-crepitantes-matidez-e-infiltrado) · [ETI (enfermedad tipo influenza)](#eti-enfermedad-tipo-influenza) · [Evento de salud (tipo de evento)](#evento-de-salud-tipo-de-evento) · [Exantema, mialgia, artralgia y cefalea](#exantema-mialgia-artralgia-y-cefalea)
- **F** — [Factores no climáticos de un brote](#factores-no-climáticos-de-un-brote) · [Fila «Otros países»](#fila-otros-países)
- **H** — [Hemograma, hematocrito y plaquetopenia](#hemograma-hematocrito-y-plaquetopenia) · [Hepatomegalia](#hepatomegalia) · [Hisopado nasofaríngeo](#hisopado-nasofaríngeo) · [Hueco (sin dato) frente a cero](#hueco-sin-dato-frente-a-cero)
- **I** — [Incidencia](#incidencia) · [Influenza y subtipos](#influenza-y-subtipos) · [IRA (infección respiratoria aguda)](#ira-infección-respiratoria-aguda) · [IRAG e IRAGI](#irag-e-iragi) · [IRAS (infecciones respiratorias agudas de vías superiores)](#iras-infecciones-respiratorias-agudas-de-vías-superiores) · [ISO 8601 (semanas)](#iso-8601-semanas)
- **L** — [Letalidad](#letalidad) · [Librería epiweeks](#librería-epiweeks) · [Lineamientos técnicos VIGEPES](#lineamientos-técnicos-vigepes)
- **M** — [MINSAL](#minsal) · [Muestras analizadas y muestras positivas](#muestras-analizadas-y-muestras-positivas)
- **N** — [Neumonías](#neumonías) · [Niveles administrativos (Admin0, Admin1, Admin2)](#niveles-administrativos-admin0-admin1-admin2) · [Notación de semana](#notación-de-semana) · [Notificación](#notificación) · [notificado](#notificado)
- **O** — [Observatorio respiratorio](#observatorio-respiratorio) · [OPS y OMS](#ops-y-oms) · [Oximetría de pulso y SatO2](#oximetría-de-pulso-y-sato2)
- **P** — [PAHO PLISA](#paho-plisa) · [Positividad](#positividad) · [probable](#probable) · [Procedimiento de arbovirosis (M02-VS-DISAM-PRO-42)](#procedimiento-de-arbovirosis-m02-vs-disam-pro-42)
- **R** — [Rezago epidemiológico (lag)](#rezago-epidemiológico-lag)
- **S** — [SARS-CoV-2 y COVID-19](#sars-cov-2-y-covid-19) · [Semana 53](#semana-53) · [Semana de archivo, semana de corte y semana real](#semana-de-archivo-semana-de-corte-y-semana-real) · [Semana epidemiológica (SE)](#semana-epidemiológica-se) · [Semana MMWR (calendario CDC/PAHO)](#semana-mmwr-calendario-cdcpaho) · [Semanas de vacaciones](#semanas-de-vacaciones) · [Semanas nominales](#semanas-nominales) · [Serie nacional y serie departamental](#serie-nacional-y-serie-departamental) · [SIBASI](#sibasi) · [Signos de alarma](#signos-de-alarma) · [SIMMOW](#simmow) · [sospechoso](#sospechoso) · [Subregistro y subnotificación](#subregistro-y-subnotificación)
- **T** — [Taquipnea](#taquipnea) · [Tasa por 100.000 habitantes](#tasa-por-100000-habitantes) · [Temporada e inicio de temporada](#temporada-e-inicio-de-temporada) · [Tiraje](#tiraje) · [total](#total)
- **U** — [UVET y UVETV](#uvet-y-uvetv)
- **V** — [VIGEPES](#vigepes) · [VIGEPES-01 (formulario de notificación)](#vigepes-01-formulario-de-notificación) · [Vigilancia centinela y laboratorial](#vigilancia-centinela-y-laboratorial) · [Vigilancia epidemiológica](#vigilancia-epidemiológica) · [Vigilancia epidemiológica descriptiva](#vigilancia-epidemiológica-descriptiva) · [Vigilancia laboratorial de virus respiratorios](#vigilancia-laboratorial-de-virus-respiratorios) · [Vigilancia pasiva](#vigilancia-pasiva) · [Volumen de casos (capa del mapa)](#volumen-de-casos-capa-del-mapa) · [VSR, parainfluenza y adenovirus](#vsr-parainfluenza-y-adenovirus)
- **Z** — [Zonas del canal endémico OPS](#zonas-del-canal-endémico-ops)

<!-- INDICE:FIN -->

## 1. Ideas generales de vigilancia y epidemiología

### Vigilancia epidemiológica

**Qué es.** Recolección, análisis e interpretación sistemática y continua de datos de salud para orientar decisiones de prevención y control.

**En el proyecto.** EPI-Aetheris es un sistema de vigilancia **descriptiva**: ingiere series públicas, las alinea por semana epidemiológica y responde "qué está pasando y qué tan inusual es contra su propia historia". No diagnostica ni clasifica riesgo de brote (`AGENTS.md` §5 y §17; [ADR 0020](../adr/0020-nowcast-corto-plazo.md) para la única excepción predictiva).

### Vigilancia epidemiológica descriptiva

**Qué es.** Vigilancia que se limita a describir lo observado (cuánto, dónde, cuándo) sin atribuir causas ni emitir pronósticos de riesgo.

**En el proyecto.** Es el marco de los módulos M1 a M4: cada uno compara una serie con su propia historia o describe la calidad del dato, y ninguno emite alerta automática. Ver [Módulos descriptivos](05-modulos-descriptivos-y-alertas.md#módulos-descriptivos-m1-a-m4).

### Vigilancia pasiva

**Qué es.** Vigilancia basada en la notificación rutinaria que hacen las unidades de salud, sin búsqueda activa de casos.

**En el proyecto.** Los boletines semanales de MINSAL y el tablero de vigilancia son productos de vigilancia pasiva consolidada. Por eso el conteo depende de cuánto se notifica, no solo de cuánta gente enferma (texto del glosario de la interfaz: "Conteo notificado").

### Vigilancia centinela y laboratorial

**Qué es.** Vigilancia que recoge datos de una red seleccionada de sitios o laboratorios (centinela) y mide muestras analizadas y detecciones de un agente, no casos clínicos.

**En el proyecto.** Es la fuente de la tabla nacional de virus respiratorios (influenza, VSR, SARS-CoV-2): muestras analizadas, muestras positivas, detecciones y positividad. No tiene desglose departamental, por eso no hay mapa de virus ([ADR 0012](../adr/0012-persistencia-vigilancia-virus-respiratorios.md)).

### Evento de salud (tipo de evento)

**Qué es.** Enfermedad o condición que se vigila.

**En el proyecto.** Se modela como catálogo, no como columnas fijas: la tabla `tipos_evento` tiene `dengue`, `ira` y `neumonia`. Así el esquema es agnóstico a la enfermedad. Ver [`tipos_evento`](07-base-de-datos-y-migraciones.md#tipos_evento).

### Caso

**Qué es.** Persona que cumple la definición de caso vigente para un evento.

**En el proyecto.** El sistema nunca maneja personas: solo **conteos agregados** por región y semana. No hay datos personales ([Solo datos agregados](10-proceso-gobernanza-y-documentacion.md#solo-datos-agregados-y-sin-datos-personales)).

### Definición de caso

**Qué es.** Criterios oficiales para decidir si un paciente es sospechoso, probable o confirmado.

**En el proyecto.** Cada fuente usa la suya y **no son intercambiables**: por eso la base guarda la definición en la columna `clasificacion` y nunca suma series de definiciones distintas. Las definiciones de dengue y neumonías que muestran las alertas son transcripción citada de VIGEPES (migración `0011`).

### Caso sospechoso

**Qué es.** Caso que cumple los criterios clínicos iniciales, todavía sin clasificar como probable o confirmado.

**En el proyecto.** Es el nombre que usa el tablero de MINSAL ("Casos Sospechosos de Dengue") y por eso se guarda con `clasificacion = 'sospechoso'` ([ADR 0021](../adr/0021-fuente-tablero-minsal.md)). Tiene la misma definición y la misma escala que el `total` de OpenDengue.

**Según VIGEPES (dengue sin signos de alarma).** Persona con fiebre de 2 a 7 días de evolución y 2 o más de estos 5 criterios: cefalea y dolor retro ocular, exantema, mialgias y artralgias, sangrado de mucosas, conteo de glóbulos blancos menor de 5.000 por mm³ (migración `0011`).

### Caso probable

**Qué es.** Caso clasificado como probable por criterios clínicos y epidemiológicos, sin confirmación de laboratorio.

**En el proyecto.** Es una de las dos series de la tabla departamental de dengue de los boletines de MINSAL (junto a `confirmado`). Se muestra siempre **por separado** del confirmado. Ver [`probable`](#probable).

### Caso confirmado

**Qué es.** Caso con confirmación de laboratorio.

**En el proyecto.** Segunda serie de la tabla departamental de dengue; también se usa para los confirmados nacionales del tablero. No equivale al `total` de OpenDengue, que es una cifra órdenes de magnitud mayor ([ADR 0005](../adr/0005-clasificacion-total-opendengue.md)). Ver [`confirmado`](#confirmado).

### Notificación

**Qué es.** Comunicación de un caso o evento al sistema de vigilancia.

**En el proyecto.** VIGEPES distingue notificación **individual e inmediata** (p. ej. dengue en sus tres formas, neumonías) y notificación **agrupada y semanal** (p. ej. infecciones respiratorias agudas de vías superiores). La tabla de la migración `0011` lo transcribe como "qué notificar".

### Conteo notificado

**Qué es.** Casos que las unidades de salud reportaron a MINSAL.

**En el proyecto.** Es lo que registra `clasificacion = 'notificado'` (IRA, neumonías). Depende de cuánto se notifica y no solo de cuánto se enferma. Ver [`notificado`](#notificado).

### Subregistro y subnotificación

**Qué es.** Casos que ocurren pero no llegan a los registros, por falta de acceso, de diagnóstico o de reporte.

**En el proyecto.** Es una de las razones por las que 2020 queda fuera de la ventana departamental: la vigilancia cayó durante la pandemia de covid-19 y los datos reflejan capacidad de reporte, no transmisión. También explica por qué M3 compara solo con años base comparables. Ver [2020 excluido](02-fuentes-de-datos-e-ingesta.md#2020-excluido).

### Ascertainment (intensidad de vigilancia)

**Qué es.** Sesgo de detección: cuántos casos se encuentran depende de cuánto se busca.

**En el proyecto.** Es el caveat asociado a 2014–2015 en el nowcast: hubo alerta nacional de arbovirosis (llegada del chikungunya) y tamizaje masivo de síndrome febril, que pudieron inflar los casos notificados. Como ese pico es determinante para el modelo, el caveat se reporta junto al resultado ([ADR 0020](../adr/0020-nowcast-corto-plazo.md), punto E).

### Endemia

**Qué es.** Presencia habitual de una enfermedad en una zona.

**En el proyecto.** "El dengue es endémico en El Salvador" es el punto de partida de la Biblioteca. La idea de "lo habitual" se operativiza con el canal endémico.

### Epidemia y brote

**Qué es.** Aumento de casos por encima de lo esperado en un lugar y momento (brote: episodio localizado; epidemia: más extenso).

**En el proyecto.** "Riesgo de brote" es una expresión **prohibida** en el producto desde el retiro del clasificador (2026-08-18). Los módulos hablan de "presión" relativa a la propia historia y no de brote. Ver [Clasificador retirado](04-estadistica-y-modelado.md#clasificador-de-riesgo-retirado).

### Temporada e inicio de temporada

**Qué es.** Período del año en que la enfermedad se intensifica; el inicio de temporada es la primera semana en que se sale de lo habitual.

**En el proyecto.** En el experimento de lead time se definió "inicio de temporada real" como la primera semana con suficiencia cuyo valor supera el P75 de su propio pool. Ese experimento se cerró sin sostener una ventana de anticipación (+29 y −30 semanas, sin acuerdo de signo). Ver [Lead time](04-estadistica-y-modelado.md#lead-time-tiempo-de-anticipación).

### Año pico y años de referencia

**Qué es.** Años cuya magnitud domina la lectura de una serie.

**En el proyecto.** En la serie nacional de OpenDengue (`total`) los años pico son 2014–2015 (con el caveat de ascertainment), 2019 (27.470 casos, máximo de la ventana 2018–2023) y 2022 (16.542). Años bajos: 2018 (8.448), 2021 (5.752), 2023 (5.788). 2020 es un caso especial por la pandemia. La etiqueta del clasificador retirado correlacionaba 0,955 con el total anual, es decir, medía "qué tan grande fue el año".

### Canal endémico

**Qué es.** Herramienta de vigilancia que compara los casos observados de cada semana contra los percentiles de esa misma semana en años anteriores, dibujados como bandas.

**En el proyecto.** Se implementa como **percentil histórico leave-one-out** por departamento y semana: el año descrito nunca entra en su propia línea base, la ventana es de ±1 semana y se exige al menos 3 de los 4 años de referencia. Los cortes de M3 son P50 y P75: hasta P50 es `baja`, entre P50 y P75 `media`, por encima de P75 `alta`. El panel «Canal endémico» de `/analisis` dibuja esas tres bandas con los casos observados encima. Es comparación histórica descriptiva, no alerta ([`docs/biblioteca/03-funciones.md`](../biblioteca/03-funciones.md)).

**Dónde.** `backend/api/presion.py`, `web/src/components/analisis/CanalEndemico.astro`, `backend/ingestion/corrida_canal_endemico_nacional.py`.

**Ojo.** El corte P75/P90 que usó el clasificador retirado **no** es el canal endémico clásico de la OPS; el que sí lo reproduce es P50/P75 ([Cortes de percentil](04-estadistica-y-modelado.md#cortes-de-percentil-p50p75-y-p75p90)).

### Zonas del canal endémico OPS

**Qué es.** Las cuatro zonas clásicas del canal endémico de la OPS/PAHO.

**En el proyecto.** Calculadas sobre P25, P50 y P75 (`corrida_canal_endemico_4zonas.py`): **éxito** (valor ≤ P25), **seguridad** (P25 < valor ≤ P50), **alarma** (P50 < valor ≤ P75) y **epidemia** (valor > P75). Colapsadas a 3 clases con éxito+seguridad = bajo, alarma = medio, epidemia = alto, son idénticas celda por celda al esquema P50/P75 (0 discrepancias en 250 celdas). Los límites inferiores son estrictos (`>`), no la definición de libro `[P50, P75)`.

### Incidencia

**Qué es.** Casos nuevos en una población y período dados; suele expresarse como tasa.

**En el proyecto.** No se usa como etiqueta ni como variable central: el denominador poblacional de la ventana quedó invalidado por el Censo 2024 (~5 % de sobrestimación nacional, error departamental no cuantificable). Se conserva solo como contexto. Ver [Denominador poblacional](#denominador-poblacional-y-censo-2024).

### Tasa por 100.000 habitantes

**Qué es.** Casos divididos entre la población y multiplicados por 100.000. En los boletines aparece como «Tasa x 100 mil» o «Tasa por 100.000».

**En el proyecto.** Familia A de la tabla de dengue y las tablas de IRA y neumonías la traen; el pipeline la extrae y la conserva en `data/interim/` pero **no** la guarda en la tabla de hechos. En Familia A la columna de tasa corresponde a los **confirmados** de una semana distinta, no a los probables (trampa 6): despejar población dividiendo probables entre tasa da un número plausible y sin sentido. La fórmula correcta es `población = confirmados(SE_Y) / tasa(SE_Y) × 100.000`.

### Denominador poblacional y Censo 2024

**Qué es.** Población que sirve de base para calcular tasas.

**En el proyecto.** El Censo 2024 desmintió el denominador disponible para la ventana de entrenamiento (~5 % de sobrestimación nacional, error departamental no cuantificable). Un error así caería en la variable objetivo y volvería ininterpretables las métricas, por eso la etiqueta se construyó por canal endémico y no por incidencia poblacional.

### Letalidad

**Qué es.** Proporción de fallecidos entre los casos.

**En el proyecto.** Los boletines traen una tabla de egresos, fallecidos y letalidad hospitalaria (SIMMOW). **No se extrae**: es otra unidad de observación distinta de la serie de casos notificados.

### Coexistencia temporal (no es causalidad)

**Qué es.** Dos series pueden ser altas la misma semana sin que una cause la otra.

**En el proyecto.** M1 (`Iv`) y M3 (percentil de casos) pueden coincidir; eso no prueba que el clima de esas semanas causara los casos ni que el índice anticipe el conteo. El sitio lo declara una sola vez, en el aviso de sensibilidad de la Biblioteca. Se conoce internamente como «coexistencia ≠ causalidad» ([`docs/biblioteca/05-sensibilidad-y-honestidad.md`](../biblioteca/05-sensibilidad-y-honestidad.md)).

### Rezago epidemiológico (lag)

**Qué es.** Retraso entre una causa candidata y su efecto observable; en dengue se estudia el rezago de semanas entre clima y casos.

**En el proyecto.** La literatura relaciona la incidencia con temperatura, lluvia y humedad de **semanas anteriores**; por eso el clasificador retirado usaba rezagos climáticos y el nowcast usa medias de 4 semanas. No confundir con el rezago de publicación de una fuente ([Antigüedad](05-modulos-descriptivos-y-alertas.md#antigüedad-m4)).

## 2. Calendario epidemiológico

### Semana epidemiológica (SE)

**Qué es.** Semana de domingo a sábado numerada dentro del año para comparar la vigilancia entre años; algunos años tienen 53.

**En el proyecto.** Es la unidad temporal común de casos y clima (`semana_epi`, con `anio`). El calendario es el de **OPS/CDC (MMWR)**, no ISO 8601, y se genera con la librería `epiweeks`. La tabla `semanas_epidemiologicas` guarda `fecha_inicio` y `fecha_fin` de cada una y es la llave foránea compartida por `casos_epidemiologicos`, `variables_ambientales` y `vigilancia_virus_respiratorios`.

**Dónde.** `db/migrations/0001_init_schema.sql`, `backend/ingestion/poblar_semanas_epidemiologicas.py`.

**Ojo.** Se abrevia `SE`, `SE01`, `S38` (en «2026-S38») o «semana 38»; en la interfaz se rotula `SE` con dos dígitos.

### Semana MMWR (calendario CDC/PAHO)

**Qué es.** Convención de los CDC de EE. UU. adoptada por la OPS: las semanas empiezan en domingo y la semana 1 es la primera del año con al menos cuatro días dentro del año calendario. Un año tiene 52 o 53 semanas.

**En el proyecto.** Es la única definición de semana que se acepta. `AGENTS.md` §17: «PAHO/CDC (MMWR), no ISO 8601 — usa la librería `epiweeks`, no recalcules límites a mano».

### ISO 8601 (semanas)

**Qué es.** Norma internacional de fechas cuyas semanas empiezan en lunes y cuya semana 1 contiene el primer jueves del año.

**En el proyecto.** **No se usa** para semanas epidemiológicas. La documentación lo recuerda porque una semana ISO no siempre coincide con la semana epidemiológica.

### Año epidemiológico y año calendario

**Qué es.** El año epidemiológico agrupa las semanas MMWR; una semana que empieza a fines de diciembre puede pertenecer a la SE01 del año siguiente.

**En el proyecto.** `cargar_opendengue.py` **no** filtra por la columna `Year` del CSV (que es de calendario): resuelve la semana por coincidencia exacta de `calendar_start_date` contra `semanas_epidemiologicas.fecha_inicio` y aplica el filtro de rango después, sobre el año epidemiológico. En el extracto multipaís, 90 filas declaran un año calendario distinto del epidemiológico.

### Semana 53

**Qué es.** La semana extra de los años MMWR largos.

**En el proyecto.** Genera casos especiales: la semana 53 de 2025 (28 de diciembre al 3 de enero) **no** aparece publicada en el tablero de MINSAL y queda sin fila («nunca un cero»); la 53 de 2020 es una de las nueve semanas con 0 casos de OpenDengue. El calendario nominal de completitud usa 52 semanas y no inventa una 53 vacía.

### Notación de semana

**Qué es.** Cómo se escribe una semana en los documentos.

**En el proyecto.** `SE23/2019` o `SE232019` (archivo de boletín), `2026-S38` (año y semana), «SE de corte» y «semana de archivo». Los nombres de archivo de boletines siguen el patrón `Boletin_epidemiologico_SE{semana}{año}.pdf`, con sufijos `_v2` a `_v4` para republicaciones.

### Semana de archivo, semana de corte y semana real

**Qué es.** Tres semanas distintas que pueden aparecer en un mismo boletín.

**En el proyecto.** La **semana de archivo** (`boletines_procesados.semana_archivo`) sale del nombre del archivo; la **semana de corte** es la que declara el encabezado de la tabla (el acumulado llega hasta ahí); la **semana real** (`casos_epidemiologicos.semana_epi`) es la del dato. En un mismo renglón, probable y confirmado pueden tener semanas de corte distintas (Familia B: probable semana actual, confirmado semana − 1). La semana se lee del encabezado, nunca se asume igual a la del nombre.

### Semanas de vacaciones

**Qué es.** Períodos en que MINSAL publica un boletín reducido.

**En el proyecto.** Son tres por año: Semana Santa (móvil: SE13 en 2018, SE16 en 2019, SE13 en 2021, SE15 en 2022, SE14 en 2023), Fiestas Agostinas y Fin de Año. Ninguno trae tabla departamental. Se detectan por el **contenido de la portada**, no por el nombre del archivo (`SE142023-Semana-Santa.pdf` contiene un `SE14` válido). En el nowcast, la marca de vacaciones de la semana objetivo usa: Semana Santa (domingo de Ramos a domingo de Pascua), fiestas agostinas (1–6 de agosto) y fin de año (20 de diciembre a 2 de enero).

### Librería epiweeks

**Qué es.** Paquete de Python que implementa el calendario epidemiológico CDC/MMWR.

**En el proyecto.** Fijada en `backend/requirements.txt` (`epiweeks==2.4.0`). Se usa para poblar `semanas_epidemiologicas` (`Year(anio, system="cdc").iterweeks()`) y para calcular la antigüedad de M4 (`Week.fromdate`). Regla: no recalcular límites de semana a mano.

### Semanas nominales

**Qué es.** Denominador teórico de semanas por año.

**En el proyecto.** M4 usa 52 como semanas nominales para la completitud anual; la cobertura efectiva de las tablas departamentales de dengue ronda ~49/52 por año (48/52 en 2023). Ver [Cobertura de publicación](02-fuentes-de-datos-e-ingesta.md#cobertura-real-de-publicación).

## 3. Instituciones, sistemas y documentos

### MINSAL

Ministerio de Salud de El Salvador. Publica los boletines epidemiológicos semanales en PDF (`salud.gob.sv`, hasta 2023) y el tablero de vigilancia (`boletin.salud.gob.sv`, desde 2024). Es la fuente de las series departamentales de dengue, IRA y neumonías y de la vigilancia laboratorial de virus respiratorios. Ver [Fuentes](02-fuentes-de-datos-e-ingesta.md#boletines-epidemiológicos-de-minsal-pdf).

### VIGEPES

Sistema de vigilancia epidemiológica de MINSAL: los boletines lo citan como «FUENTE: VIGEPES» y la documentación del proyecto transcribe sus «Lineamientos técnicos VIGEPES (Acuerdo Ejecutivo 1300, 03-12-2024)». El repositorio **no expande la sigla**.

### VIGEPES-01 (formulario de notificación)

Formulario de notificación individual de enfermedades objetivo de vigilancia sanitaria. Aparece en el campo `contacto_vigilancia` de las alertas junto con la ruta SIBASI.

### Lineamientos técnicos VIGEPES

Documento de MINSAL (Acuerdo Ejecutivo 1300, 3 de diciembre de 2024) del que se transcriben las definiciones de caso y la tabla de notificación (Tabla 1, p. 18; secciones 32 a 35). Es un documento de **vigilancia**, no una guía de manejo clínico: define qué se notifica, no cuándo referir. Por eso los campos `signos_alarma` y `criterios_referencia` de las alertas respiratorias quedan en `NULL` ([ADR 0015](../adr/0015-alertas-operables.md)).

### SIBASI

Unidad territorial de la red de salud a la que se notifica y con la que se coordina la respuesta local. El repositorio no expande la sigla; en el uso general corresponde a los Sistemas Básicos de Salud Integral. Las alertas dan la ruta «SIBASI / VIGEPES-01» y **nunca un teléfono ni un correo**: el número del SIBASI del piloto no está en una fuente pública citada y no se inventa.

### UVET y UVETV

Unidad que consolida semanalmente lo notificado y «revisa y aprueba el boletín epidemiológico semanal», según el procedimiento de arbovirosis citado en la migración `0011`. El repositorio no expande la sigla.

### Boletín epidemiológico semanal

**Qué es.** PDF semanal de MINSAL con resúmenes nacionales y tablas por departamento (dengue, IRA, neumonías, otras enfermedades, vigilancia laboratorial).

**En el proyecto.** Es la fuente de 264 archivos (2018–2023, sin 2020) cargados por el parser. Sus cifras son **acumuladas desde la SE1** y hay que desacumularlas. Ver [Acumulado y desacumulación](02-fuentes-de-datos-e-ingesta.md#desacumulación).

### OPS y OMS

Organización Panamericana de la Salud y Organización Mundial de la Salud (PAHO/WHO en inglés). Fuentes de las guías de prevención y manejo que las alertas transcriben con cita (p. ej. «Algoritmos para el Manejo Clínico de los Casos de Dengue», junio 2020). El proyecto también adopta su calendario epidemiológico y su método de canal endémico.

### Algoritmos OPS de manejo clínico de dengue

Documento «Algoritmos para el Manejo Clínico de los Casos de Dengue» (OPS, junio de 2020). El proyecto transcribe de su p. 10 los criterios de referencia para hospitalización (`criterios_referencia` de las alertas de dengue). En los documentos internos se cita como `[OPS-ALG]`; no hay un equivalente salvadoreño localizado para IRA y neumonías.

### Procedimiento de arbovirosis (M02-VS-DISAM-PRO-42)

Procedimiento de MINSAL para vigilancia y control de arbovirosis (Acuerdo Ejecutivo 2771, 28-10-2025). Su Anexo 5 y la sección de responsabilidades respaldan la ruta de notificación del campo `contacto_vigilancia`. Se cita como `[ARBO]`.

### CDC y MMWR

Centers for Disease Control and Prevention de EE. UU. y su publicación *Morbidity and Mortality Weekly Report*, origen del calendario epidemiológico MMWR. Ver [Semana MMWR](#semana-mmwr-calendario-cdcpaho).

### PAHO PLISA

Plataforma regional de la OPS de la que provienen los datos nacionales semanales de OpenDengue (Admin0). En el uso general corresponde a la Plataforma de Información en Salud para las Américas; el repositorio la cita solo como «PAHO/PLISA».

### SIMMOW

Sistema de MINSAL del que provienen tablas y gráficos de egresos hospitalarios, fallecidos y letalidad (y el corredor endémico de IRAG). El repositorio no lo extrae ni expande la sigla: son otra unidad de observación.

## 4. Geografía administrativa

### Niveles administrativos (Admin0, Admin1, Admin2)

**Qué es.** Jerarquía político-administrativa que usan las fuentes y la base.

**En el proyecto.** `regiones.nivel_admin`: **0** = nacional (`SV`), **1** = departamento (14), **2** = municipio, **reservado y sin filas**. Las notas de fuentes mencionan además 48 municipios y 266 distritos (Admin3). Las series de OpenDengue Admin0 son nacionales y semanales; las Admin1 (departamentales) solo cubren 2000–2009 y son mensuales, por lo que no se usan.

**Ojo.** Que `nivel_admin = 2` esté reservado es la razón por la que ninguna vista se titula «hoy» ni «mi municipio»: no hay dato que la sostenga ([ADR 0014](../adr/0014-enfoque-dual-panorama-analisis.md)).

### Departamento

Primer nivel subnacional de El Salvador. Son 14 y la base los identifica con códigos ISO 3166-2:SV.

| Código | Departamento | Código | Departamento |
|---|---|---|---|
| `SV-AH` | Ahuachapán | `SV-SA` | Santa Ana |
| `SV-CA` | Cabañas | `SV-SM` | San Miguel |
| `SV-CH` | Chalatenango | `SV-SO` | Sonsonate |
| `SV-CU` | Cuscatlán | `SV-SS` | San Salvador |
| `SV-LI` | La Libertad | `SV-SV` | San Vicente |
| `SV-MO` | Morazán | `SV-UN` | La Unión |
| `SV-PA` | La Paz | `SV-US` | Usulután |

### Código ISO 3166-2:SV

Norma que da a cada departamento un código de la forma `SV-XX`. Es el identificador estable de `regiones.codigo`, de las URL de la API (`/api/v1/temporal/SV-SS`) y del alcance territorial de las alertas. El país entero es `SV`. Aunque el GeoJSON de límites traía `shapeISO` vacío, el código se inyecta al construirlo ([ADR 0002](../adr/0002-join-mapa-geojson-por-nombre.md)).

### Cobertura 14 de 14

M4 mide la completitud geográfica como `n/14` departamentos con fila en una semana. Un departamento **sin fila** esa semana es un hueco real, no un cero ni un departamento seguro.

### Fila «Otros países»

Fila de la tabla departamental de dengue que no corresponde a ningún departamento (casos de personas de otros países). A veces se incluye en el total impreso y a veces no; el validador prueba ambas convenciones por boletín. Ver [Trampa 3](02-fuentes-de-datos-e-ingesta.md#trampas-de-las-fuentes-catálogo).

## 5. Dengue

### Dengue

Enfermedad viral transmitida por mosquitos *Aedes*. Es endémica en El Salvador y el caso piloto del sistema; aparece con cuatro series: `probable`, `confirmado`, `total` (OpenDengue) y `sospechoso` (tablero).

### Aedes aegypti

Mosquito vector del dengue. El módulo M1 (`Iv`) mide qué tan favorable es el clima de una semana para su desarrollo; el proyecto usa la curva térmica de Mordecai et al. (2017). Se cría en recipientes con agua acumulada, razón de las recomendaciones oficiales de «eliminar criaderos y revisar depósitos de agua» que el sitio puede reproducir con cita.

### Arbovirosis

Enfermedades causadas por arbovirus (virus transmitidos por artrópodos), como dengue, chikungunya y zika. Aparece en la «alerta nacional de arbovirosis» de 2014–2015 y en el procedimiento de MINSAL `M02-VS-DISAM-PRO-42`.

### Chikungunya y zika

Otras arbovirosis. En 2014 MINSAL contó aparte 167.957 casos de chikungunya, dato usado para descartar que el pico de dengue de 2014 fuera contaminación por reetiquetado. Los boletines traen tablas departamentales de zika y chikungunya que el proyecto **no** ingiere.

### Dengue con y sin signos de alarma, y dengue grave

**Qué es.** Clasificación clínica que usa VIGEPES: dengue sin signos de alarma, dengue con signos de alarma (caso sospechoso que presenta uno o más signos de la lista) y dengue grave.

**En el proyecto.** Las alertas de dengue transcriben las definiciones y indican notificación individual e inmediata en los tres casos, con confirmación de laboratorio. El sistema no clasifica pacientes.

### Signos de alarma

Hallazgos que, según VIGEPES (sección 34), distinguen el dengue con signos de alarma: dolor abdominal intenso y sostenido o a la palpación, vómitos persistentes, acumulación de líquidos, sangrado espontáneo, letargo o inquietud, hepatomegalia mayor a dos centímetros bajo el reborde costal e incremento del hematocrito con plaquetopenia (ambos a la vez). Campo opcional `alertas.signos_alarma`; **queda en `NULL` en las alertas respiratorias**.

### Criterios de referencia

Criterios para sugerir hospitalización, transcritos de los Algoritmos OPS: dengue con signos de alarma, dengue grave, intolerancia a la vía oral, dificultad respiratoria, acortamiento de la presión de pulso, prolongación del llenado capilar (mayor de 2 segundos), hipotensión arterial, insuficiencia renal aguda, embarazo, coagulopatía; la decisión debe individualizarse y considerar comorbilidades, extremos de la vida y factores sociales. Campo `alertas.criterios_referencia`.

### Factores no climáticos de un brote

**Qué es.** Causas de la amplitud interanual que el clima no explica: serotipo circulante, inmunidad acumulada de la población, introducción del virus, movilidad y control de vectores.

**En el proyecto.** Es la explicación estructural de por qué el clasificador climático retirado no acertó: esas variables no están en el conjunto de datos y la etiqueta medía sobre todo «qué tan grande fue el año».

## 6. Enfermedades respiratorias

### IRA (infección respiratoria aguda)

Evento respiratorio con tabla departamental en los boletines (`Departamento | Total | Tasa x 100 mil`). Es un **conteo clínico único**, sin división probable/confirmado, acumulado desde la SE1. Se guarda con `tipos_evento.codigo = 'ira'` y `clasificacion = 'notificado'` ([ADR 0011](../adr/0011-clasificacion-ira-departamental.md)), con 2.742 filas departamentales (2018–2023 sin 2020). El encabezado «Probable/Confirmado» de la tabla nacional por grupo de edad de 2023 es un **error de plantilla** de MINSAL: su segunda columna es la tasa.

### IRAS (infecciones respiratorias agudas de vías superiores)

Categoría de VIGEPES de notificación **agrupada y semanal**, con confirmación clínica.

### IRAG e IRAGI

IRAG: infección respiratoria aguda grave; aparece en los boletines como corredor endémico de egresos (SIMMOW), otra unidad que no se extrae. IRAGI: infección respiratoria aguda **inusitada**, caso sospechoso de notificación individual e inmediata con confirmación de laboratorio (transcripción VIGEPES).

### Neumonías

Conteo clínico departamental notificado (incluye bronconeumonía), acumulado desde SE1, mismo formato que IRA. Se guarda con `tipos_evento.codigo = 'neumonia'` y `clasificacion = 'notificado'`; no se mezcla con IRA. Definición VIGEPES: confirmada por clínica (enfermedad respiratoria aguda febril con tos productiva, dificultad respiratoria, taquipnea y dos o más de limitación de la entrada de aire, matidez y estertores crepitantes, o infiltrado lobar o segmentario y/o derrame pleural) o con aislamiento etiológico. Hay 2.749 filas departamentales.

**Ojo.** La suma departamental de neumonías de los boletines promedia entre 500 y 780 casos por semana según el año, frente a 130–430 del tablero en 2025–2026; **no se ha comprobado si es la misma definición**, por eso no se empalman.

### ETI (enfermedad tipo influenza)

Aparece solo en la narrativa regional de la OPS, no como tabla nacional; no se extrae.

### Influenza y subtipos

Virus respiratorio con tipos A y B. En la fuente aparecen influenza A (H1N1)pdm2009 (a veces `H1N1*` «estacional»), A H3N2, A no sub-tipificado e influenza B. En la base, `virus` toma valores `influenza`, `influenza_a_h1n1`, `influenza_a_h3n2`, `influenza_a_no_subtipificado` e `influenza_b`.

### VSR, parainfluenza y adenovirus

VSR: virus sincitial respiratorio. Junto con la parainfluenza y el adenovirus forma el grupo «otros virus respiratorios» de la tabla de laboratorio. En la base: `vsr`, `parainfluenza`, `adenovirus`.

### SARS-CoV-2 y COVID-19

En los boletines aparece como fila `COVID 19(SEn)` (no «SARS-CoV-2») **solo desde 2023** (41 boletines, 39 con valor). Se guarda como `covid_19`. Una etiqueta vacía no se rellena. Por eso 2020 no se descarga para esta rama.

### Vigilancia laboratorial de virus respiratorios

Tabla nacional semanal de MINSAL: total de muestras analizadas, muestras positivas, detecciones por virus y positividad acumulada. Es **nacional y no departamental**, acumulada desde SE1 (columnas «año previo», «año actual» y a veces «semana»). Se guarda en `vigilancia_virus_respiratorios` como pares virus × métrica con unidad `conteo` o `porcentaje`. 3.028 filas.

### Muestras analizadas y muestras positivas

Denominador y numerador de la vigilancia laboratorial. Métricas `muestras_analizadas` y `muestras_positivas` (`unidad = 'conteo'`).

### Detección

Hallazgo positivo de un virus en una muestra. Métrica `detecciones` (conteo por virus). No es un caso clínico ni se convierte en uno.

### Positividad

Proporción de muestras con detección de un virus en una semana. La fuente la publica acumulada; el sistema la guarda **tal como la publica** (`metrica = 'positividad'`, `unidad = 'porcentaje'`) y nunca la recalcula ni la trata como conteo.

### Hisopado nasofaríngeo

Toma de muestra de las vías respiratorias superiores para detectar virus. Aparece en la definición de neumonía con aislamiento etiológico.

### Observatorio respiratorio

Sección `/respiratorio` del sitio: IRA, neumonías y vigilancia de laboratorio. No calcula M1 a M4 (esas fórmulas están cerradas solo para dengue). Ver [Observatorio respiratorio](05-modulos-descriptivos-y-alertas.md#observatorio-respiratorio).

## 7. Cómo nombra y cuenta los casos el proyecto

### Clasificación (`clasificacion`)

Columna de `casos_epidemiologicos` que registra **la definición del conteo**. Valores permitidos por `CHECK`: `probable`, `confirmado`, `total`, `notificado`, `sospechoso` (agregados por las migraciones `0003`, `0007` y `0012`). Regla: **nunca sumar `conteo` entre valores de `clasificacion` sin filtrar primero**. Ver [`clasificacion`](07-base-de-datos-y-migraciones.md#clasificacion).

### `probable`

Casos probables de la tabla departamental de dengue de los boletines de MINSAL. Se muestra por separado del confirmado y nunca se suma con él. Serie con más cobertura; alimenta el mapa de volumen y M3.

### `confirmado`

Casos con confirmación de laboratorio según MINSAL: series departamentales de los boletines y confirmados nacionales del tablero (203 en 2025 y 48 en 2026 hasta la SE37). Serie distinta de `probable`.

### `total`

Conteo agregado de OpenDengue (`case_definition_standardised = 'Total'` en el 100 % de las 574 filas semanales nacionales). **Exclusivo** de `fuente_id = opendengue_v1_3` a nivel nacional. No equivale a `confirmado` ni a `probable` ([ADR 0005](../adr/0005-clasificacion-total-opendengue.md)).

### `sospechoso`

Casos notificados del tablero de MINSAL desde 2025, con el nombre que usa la fuente. Misma definición y escala que `total`, pero la serie llega **suavizada** por la fuente (parece un promedio de las 6 o 7 semanas anteriores). Ver [Serie suavizada del tablero](02-fuentes-de-datos-e-ingesta.md#serie-suavizada-del-tablero).

### `notificado`

Conteo sin desagregación probable/confirmado ni confirmación de laboratorio declarada: IRA, neumonías y las series nacionales respiratorias del tablero. Nombre elegido porque la propia fuente titula la tabla «Resumen acumulado de eventos de notificación» ([ADR 0011](../adr/0011-clasificacion-ira-departamental.md)); se descartaron `reportado`, `total_clinico` y `clinico`.

### Conteo (`conteo`)

Entero no negativo de casos de una región, semana, evento, clasificación y fuente. La restricción `UNIQUE (region_id, tipo_evento_id, anio, semana_epi, clasificacion, fuente_id)` impide duplicados.

### Serie nacional y serie departamental

Nacional: región `SV`, semanal (OpenDengue 2014–2024, tablero desde 2025). Departamental: 14 regiones `nivel_admin = 1` (boletines 2018–2023 sin 2020). **No son comparables** entre sí: por eso `GET /api/casos-nacional` empalma OpenDengue y tablero con un campo `fuente` por fila para que la curva marque el tramo.

### Hueco (sin dato) frente a cero

Principio no negociable: **ausencia de dato ≠ cero**. Una semana sin fila (boletín ausente, tabla no publicada, semana 53 de 2025) queda sin dato; solo una celda vacía de la tabla departamental de dengue se ingiere como 0 porque MINSAL lo establece así. Las funciones devuelven `None`/`null` con una nota y nunca interpolan.

### Celda vacía = 0

Regla de la tabla departamental de dengue de MINSAL: una celda en blanco significa cero, no dato ausente (SE062018: «La Libertad 0 0.0», con la columna probable en blanco). Se ingiere como `0`, nunca como `NULL` ni como fila omitida.

### Casos observados

Conteo real de una celda (departamento, año, semana, serie); `null` cuando no hay observación. Es el valor que M3 compara contra el pool de su baseline.

### Volumen de casos (capa del mapa)

Capa inicial del mapa: casos semanales de MINSAL, probables o confirmados, coloreados por cuantiles de los datos. Muchas celdas departamento-semana son cero (87–93 %), por lo que el mapa historicamente agregaba el acumulado de la ventana cargada.

## 8. Vocabulario clínico de las alertas

Definiciones generales para leer las alertas; **no son guía clínica**. El contenido clínico de una alerta se transcribe de la fuente citada.

### Taquipnea

Respiración rápida, con frecuencia respiratoria por encima de lo esperado para la edad. Aparece en las definiciones de neumonía.

### Tiraje

Hundimiento de la piel entre las costillas o bajo ellas al respirar; signo de dificultad respiratoria. Se menciona en las alertas respiratorias de demostración (menores de 5 años).

### Oximetría de pulso y SatO2

Medición no invasiva de la saturación de oxígeno de la sangre (SatO2) con un pulsioxímetro. Las alertas de demostración piden documentarla en todo paciente con dificultad respiratoria.

### Estertores crepitantes, matidez e infiltrado

Signos de examen físico y radiológico de neumonía: ruidos finos al final de la inspiración, sonido apagado a la percusión del tórax y sombra pulmonar (lobar o segmentaria), a veces con derrame pleural.

### Hemograma, hematocrito y plaquetopenia

Hemograma: análisis de sangre que cuenta sus células. Hematocrito: proporción de glóbulos rojos. Plaquetopenia: cifra baja de plaquetas. Su combinación (incremento del hematocrito con plaquetopenia) es un signo de alarma del dengue.

### Hepatomegalia

Aumento del tamaño del hígado; en la lista de signos de alarma, más de dos centímetros bajo el reborde costal.

### Exantema, mialgia, artralgia y cefalea

Erupción cutánea, dolor muscular, dolor articular y dolor de cabeza: parte de los cinco criterios de la definición de caso sospechoso de dengue, junto con dolor retro ocular, sangrado de mucosas y leucopenia.

### AINE

Antiinflamatorios no esteroideos. Se mencionan en la alerta de dengue de demostración (migración `0009`), que es contenido de ensayo redactado por el equipo, no una recomendación del sistema.
