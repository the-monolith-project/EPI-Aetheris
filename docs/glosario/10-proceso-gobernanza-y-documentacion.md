# Rama 10 · Proceso, gobernanza y documentación

Vocabulario de cómo se decide, se documenta y se trabaja en el proyecto: los ADR, la precedencia entre fuentes, las decisiones cerradas y abiertas, los principios no negociables, los roles, los hitos y las convenciones de escritura.

**Para quién es.** Para quien lee un ADR, un mensaje de commit que dice «tarjeta 26» o una instrucción de `AGENTS.md` y necesita saber quién decide qué, en qué orden manda cada documento y qué quiere decir «cerrado», «firmado» o «puerta».

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris), **Dónde** (archivo o documento) y **Ojo** (errores frecuentes). Las expansiones de siglas que el repositorio no da se marcan como «de uso general».

**Ramas vecinas.** El marco metodológico completo (pilares, CIMT, Expotécnica) y la cronología están en el glosario del repositorio STC (`STC/glosario/`); el repositorio y sus flujos, en [`08-infraestructura-despliegue-y-repositorio.md`](08-infraestructura-despliegue-y-repositorio.md).

<!-- INDICE:INICIO -->

## Índice alfabético (35 entradas)

- **A** — [ADR (Architecture Decision Record)](#adr-architecture-decision-record) · [ADR antes de migración](#adr-antes-de-migración) · [AGENTS.md](#agentsmd) · [Analizar, proponer, implementar, validar, revisar diff](#analizar-proponer-implementar-validar-revisar-diff) · [Aporte de ingeniería](#aporte-de-ingeniería) · [Archivo histórico](#archivo-histórico) · [Archivos de contexto locales](#archivos-de-contexto-locales) · [Aviso de honestidad (AVISO_HONESTIDAD_)](#aviso-de-honestidad-aviso_honestidad_)
- **B** — [Biblioteca](#biblioteca)
- **C** — [Contradicciones y «no asumir»](#contradicciones-y-no-asumir) · [Coordinación (coordinador, 0V3R)](#coordinación-coordinador-0v3r) · [Coordinación entre agentes](#coordinación-entre-agentes) · [Costo de replicación tendiendo a cero](#costo-de-replicación-tendiendo-a-cero)
- **D** — [Decisiones cerradas y decisiones abiertas](#decisiones-cerradas-y-decisiones-abiertas) · [Documento de diseño externo y referencias](#documento-de-diseño-externo-y-referencias)
- **E** — [Enmienda y «parcialmente superado»](#enmienda-y-parcialmente-superado) · [Estatuto y principios no negociables](#estatuto-y-principios-no-negociables) · [Expotécnica y Expo Técnica](#expotécnica-y-expo-técnica)
- **H** — [Hito](#hito) · [Hogar canónico de un deslinde](#hogar-canónico-de-un-deslinde)
- **I** — [Idioma y convenciones](#idioma-y-convenciones) · [Índice de los ADR](#índice-de-los-adr) · [Informe de investigación e hipótesis](#informe-de-investigación-e-hipótesis) · [INSAMT y Equipo 4](#insamt-y-equipo-4) · [Isaac y la tarea de rescate](#isaac-y-la-tarea-de-rescate)
- **N** — [Nada de datos fabricados](#nada-de-datos-fabricados) · [Nombre del proyecto](#nombre-del-proyecto)
- **O** — [Orientador y evaluador externo](#orientador-y-evaluador-externo)
- **P** — [Pivote](#pivote) · [Precedencia de fuentes](#precedencia-de-fuentes) · [Propuestas descartadas](#propuestas-descartadas)
- **S** — [Sensibilidad y honestidad (aviso de sensibilidad)](#sensibilidad-y-honestidad-aviso-de-sensibilidad) · [Solo datos agregados y sin datos personales](#solo-datos-agregados-y-sin-datos-personales)
- **T** — [Tarjeta](#tarjeta)
- **V** — [Voz afirmativa](#voz-afirmativa)

<!-- INDICE:FIN -->

## 1. Decisiones formales

### ADR (Architecture Decision Record)

**Qué es.** Registro de una decisión arquitectónica (Registro de Decisión de Arquitectura; expansión de uso general, el repositorio solo usa la sigla).

**En el proyecto.** Viven en `docs/adr/` con la plantilla `0001-plantilla-base.md` y tienen tres secciones fijas: **Contexto** (los hechos que obligan a decidir, sin opiniones), **Decisión** y **Consecuencias** (positivas, negativas y neutrales). Algunos añaden **Migración** (qué archivo de `db/migrations/` los respalda) y **Alternativas descartadas**. Los estados son **Propuesto**, **Aceptado**, **Rechazado** y **Obsoleto**; los ADR aceptados son decisiones vigentes. Ver el [índice de los ADR](#índice-de-los-adr).

**Ojo.** El número no siempre sigue el orden del calendario: el 0016 quedó reservado por la PR #110 de la Biblioteca mientras el 0017 (endurecimiento del backend) se escribía antes.

### Índice de los ADR

**Qué es.** Lista de las 22 decisiones registradas.

**En el proyecto.**

| ADR | Tema |
|---|---|
| 0001 | Plantilla base |
| 0002 | Unión entre `regiones` y el GeoJSON por nombre normalizado |
| 0003 | Coordenadas de `regiones` como columnas nuevas |
| 0004 | Bitácora de boletines: llave natural, estado `ausencia_esperada`, trazabilidad |
| 0005 | Valor `total` de `clasificacion` (OpenDengue) |
| 0006 | Segunda fuente `open_meteo_era5` (atribución de la precipitación) |
| 0007 | Estado `sin_texto_extraible` |
| 0008 | Fuente NOAA ONI |
| 0009 | Runner mínimo de migraciones (`schema_migrations`) |
| 0010 | Volcado versionado de datos reales |
| 0011 | Valor `notificado` de `clasificacion` (IRA) |
| 0012 | Vigilancia laboratorial de virus respiratorios |
| 0013 | Alertas de campo humanas |
| 0014 | Enfoque dual (consulta y análisis), campos clínicos, caché offline |
| 0015 | Alertas operables: archivo, escritura autenticada, etiquetas |
| 0016 | Documentos propios para la Biblioteca |
| 0017 | Endurecimiento del backend y umbral de escritura |
| 0018 | Extensión de la capa climática hasta el presente |
| 0019 | Integridad de la vigilancia (M4) |
| 0020 | Predicción de casos a corto plazo (nowcast) |
| 0021 | Tablero de MINSAL como fuente (capturas HAR) |
| 0022 | Alertas con alcance territorial |

### Enmienda y «parcialmente superado»

**Qué es.** Formas de cambiar un ADR sin reescribirlo.

**En el proyecto.** Una **enmienda** es una sección fechada al final (por ejemplo, ADR 0010 punto E, 2026-09-06; ADR 0020, 2026-09-27; ADR 0021, 2026-09-27). Una **nota de estado** avisa de que un ADR quedó parcialmente superado por otro: el ADR 0013 dice que el 0015 lo supera en autenticación y creación, «el cuerpo se conserva intacto».

### ADR antes de migración

**Qué es.** Regla de proceso: cualquier cambio de esquema (tablas, columnas, restricciones, `CHECK`, valores controlados) exige un ADR **aceptado antes** de escribir la migración; «no escribas primero la migración para documentarla después».

**En el proyecto.** La migración lleva el número del ADR que la respalda. Las filas de catálogo son dato y no lo exigen. Ver [ADR antes de migración](07-base-de-datos-y-migraciones.md#adr-antes-de-migración).

### Precedencia de fuentes

**Qué es.** El orden en que manda cada documento cuando parecen contradecirse (`AGENTS.md` §4).

**En el proyecto.** 1) el **ADR aceptado** aplicable, 2) la **sección 17** de `AGENTS.md`, 3) el **código y la configuración** presentes en `main`. Si el conflicto no se resuelve con eso, **se declara** en lugar de asumir. «No cambies documentación silenciosamente para hacerla coincidir con una implementación contradictoria.»

**Ojo.** Estos glosarios **describen**, no deciden: si algo aquí contradice un ADR, manda el ADR.

### Contradicciones y «no asumir»

**Qué es.** Dos reglas de `AGENTS.md` (§18 y §19).

**En el proyecto.** Ante una contradicción: identificarla, decidir qué fuente manda, comprobar el historial, informar y modificar solo con una conclusión respaldada. Ante información faltante: no inventar datos, requisitos ni decisiones del equipo, y distinguir **estado actual, evidencia, decisión aprobada, hipótesis, propuesta y pendiente**.

### Decisiones cerradas y decisiones abiertas

**Qué es.** Las cerradas están firmadas y **no se reabren** sin instrucción explícita; las abiertas siguen sin resolver y **no se resuelven por cuenta propia**: se pregunta.

**En el proyecto.** El archivo de decisiones abiertas usa letras (A, B, C…). Cuando una se cierra se mueve a las cerradas y se borra de las abiertas; **la numeración salta a propósito**, no se reordena. Estado histórico: A (fórmulas de M3 y M4), B (atribución de la fuente climática, ADR 0006), C (mecanismo de migraciones, ADR 0009) y G (dónde vive la salida de M3 y M4) están cerradas. Siguen abiertas: D (estrategia de pruebas del pipeline de ingesta), E (si la exclusión de 2020 gobierna la ingesta), I (detalles de las herramientas de frontend), J (cuál copia del frontend es la canónica) y K (alineación del informe con la nueva hipótesis). F y H quedaron **sin objeto** tras el pivote. Ver [`AGENTS.md`](../../AGENTS.md) §17 «Decisiones abiertas».

**Ojo.** `AGENTS.md` §17 cita el ADR 0018 para el cierre de M4, pero el ADR de M4 es el **0019**.

### Estatuto y principios no negociables

**Qué es.** Las reglas que no se discuten (`AGENTS.md` §5); romperlas «invalida el trabajo completo, no solo la parte afectada».

**En el proyecto.** **Datos:** solo reales, públicos y agregados; no fabricar, simular ni sintetizar; no rellenar ausencias con supuestos no aprobados; no convertir ausencia en cero salvo que la fuente lo establezca; conservar trazabilidad. **Interpretación:** no presentar la salida como diagnóstico, certeza clínica, predicción infalible, recomendación médica ni descubrimiento epidemiológico. **Costos:** dependencias solo si están justificadas; sin servicios de pago ni suscripciones necesarias para el funcionamiento central. **Privacidad:** sin datos personales. **Reproducibilidad:** Docker forma parte del funcionamiento esperado.

### Solo datos agregados y sin datos personales

**Qué es.** Principio de privacidad por diseño.

**En el proyecto.** El sistema trabaja con conteos por departamento y semana y con reanálisis climático: sin nombres, documentos, historias clínicas ni geolocalización de personas. Gobierna el diseño: no hay tabla de usuarios; la escritura de alertas usa un secreto de entorno; el feedback va a GitHub Issues; el municipio (`nivel_admin = 2`) está reservado sin filas. La propuesta descartada AULA-PULSE (deserción escolar) exigía datos de menores y no había dataset público. Ver [Sin datos personales en la API](06-backend-y-api.md#sin-datos-personales-en-la-api).

### Nada de datos fabricados

**Qué es.** El estatuto más citado del proyecto.

**En el proyecto.** Consecuencias concretas: no se simula una serie «para que la demo funcione», no se reparte un hueco de vacaciones entre boletines vecinos, no se «suavizan» las correcciones negativas, `OpenDengue` no se etiqueta `confirmado` y un cero falso de precipitación se rechaza. Ver [Sin relleno](02-fuentes-de-datos-e-ingesta.md#sin-relleno-nunca-fabricar).

### Costo de replicación tendiendo a cero

**Qué es.** Criterio del Pilar 2: cualquier tercero debe poder clonar, seguir la documentación y desplegar sin barreras económicas ni técnicas.

**En el proyecto.** Explica el rechazo de APIs de pago, el volcado versionado de datos reales y el uso de `HistGradientBoosting` de scikit-learn en lugar de una dependencia nueva (LightGBM). Antes de agregar una dependencia: ver si ya existe una equivalente, comprobar decisiones cerradas, justificarla, evaluar mantenimiento, licencia, tamaño y complejidad, y evitar servicios de pago.

### Aporte de ingeniería

**Qué es.** La declaración de qué aporta el proyecto.

**En el proyecto.** «El aporte es de **ingeniería de software** (sistema libre, contenedorizado, reproducible), no de novedad epidemiológica ni un oráculo médico.» Lo que se publica: un sistema clonable con datos reales, una arquitectura agnóstica a evento y región, trazabilidad de cada fila a su boletín, modelo climático y definición de caso, y un foco geográfico (El Salvador y Centroamérica) poco cubierto por la literatura asiática y brasileña.

## 2. Documentación

### `AGENTS.md`

**Qué es.** Instrucciones para agentes de programación dentro del repositorio ([`AGENTS.md`](../../AGENTS.md)).

**En el proyecto.** Su sección 1 obliga a leer la sección 17 y los ADR de la tarea antes de cambios relevantes; la 17 es el **contexto técnico vigente**. La sección 14 dice que las tareas de revisión o análisis **no modifican archivos** hasta entregar los hallazgos. La sección 16 limita `docs/` a lo esencial: `adr/`, `biblioteca/` y `despliegue-render.md`.

**Ojo.** Estos glosarios están en `docs/glosario/`, una carpeta nueva: **es una desviación deliberada de esa regla**, hecha porque la coordinación pidió expresamente los `.md` de tecnicismos. No se usó `docs/biblioteca/` para no entrar a la colección de Astro.

### Biblioteca

**Qué es.** La sección pública `/biblioteca` con documentos propios, escritos para un lector externo ([ADR 0016](../adr/0016-biblioteca-documentos-propios.md)).

**En el proyecto.** Son síntesis, no copia de la documentación interna: si un hecho cambia, se actualiza **primero** el ADR o el módulo y después la Biblioteca. Frontmatter con `titulo`, `descripcion`, `orden` y `categoria`. Los cinco documentos: «Qué es EPI-Aetheris», «Qué hace hoy», «De dónde salen los datos», «Sensibilidad y honestidad» (en el repositorio vitrina se titula «Aviso de sensibilidad») y «Arquitectura y reproducibilidad». Los archivos se numeran 01, 03, 04, 05 y 06: no existe un 02.

### Sensibilidad y honestidad (aviso de sensibilidad)

**Qué es.** El documento canónico de los límites del sistema (`docs/biblioteca/05-sensibilidad-y-honestidad.md`, ruta `/biblioteca/05-sensibilidad-y-honestidad`).

**En el proyecto.** Declara **una sola vez** lo que el sistema **no afirma** y por qué. Las pantallas enlazan a él en lugar de repetir el deslinde (`RUTA_SENSIBILIDAD` en `enlaces.ts`).

### Hogar canónico de un deslinde

**Qué es.** El lugar único donde se declara una salvedad.

**En el proyecto.** Cada salvedad («no es diagnóstico», «coexistencia ≠ causalidad», «la predicción parte de la última semana observada») se escribe **una sola vez**, en su hogar (pie, panel de alertas, Biblioteca), no en cada pantalla. «El rigor se muestra con métricas y fuentes visibles, no repitiendo disclaimers.»

### Voz afirmativa

**Qué es.** Regla de redacción del texto de cara al usuario.

**En el proyecto.** Primero qué es y qué aporta, después el límite. El copy no debe sonar a disculpa permanente. Se cerró el 2026-09-07.

### Idioma y convenciones

**Qué es.** Convenciones de escritura del repositorio.

**En el proyecto.** El contenido de dominio (tablas, columnas, comentarios, docstrings) va en **español**. Se extienden los catálogos (`tipos_evento`, `regiones`, `fuentes_datos`) en lugar de añadir columnas por enfermedad o país, y los valores controlados del esquema se reutilizan **verbatim**, nunca se inventan. Los mensajes de commit son el historial de cambios: no hay `CHANGELOG` en el repositorio de código.

### Documento de diseño externo y referencias

**Qué es.** Fuentes que respaldan las fórmulas y que no viven en el repositorio.

**En el proyecto.** Las fórmulas de `Iv` están «tomadas literalmente» de la propuesta de diseño «Camino Ancho v2 ajustada» (sección 4, Módulo 1), un documento **externo al repositorio**. Las referencias citadas son Mordecai et al. (2017) para el modelo térmico, la tesis UES (Universidad de El Salvador; expansión de uso general) y, para la validación, Johansson et al. (2016): con 28 años de datos mensuales de México encontró que las variables climáticas no mejoraban de forma significativa a los modelos estacionales autorregresivos, evidencia contextual que refuerza la necesidad de una validación fuera de muestra.

### Archivo histórico

**Qué es.** La documentación interna que guió el proyecto hasta septiembre de 2026 y salió del repositorio principal el **2026-09-25**.

**En el proyecto.** Se conserva en el repositorio STC (`STC/EPI-Aetheris/historico/`) «como registro, no como referencia vigente». El repositorio de código conserva solo lo esencial. **Muchos comentarios de código y ADR citan rutas como `docs/contexto/...` o `docs/rescate-prediccion/...`**, que corresponden a su ubicación original; en STC equivalen a la misma ruta sin el prefijo `docs/`. Si algo del archivo contradice un ADR, manda el ADR.

### Archivos de contexto locales

**Qué es.** Los `.md` de trabajo (`*.local.md`) que no se versionan.

**En el proyecto.** Ver [Archivos de tarea locales](08-infraestructura-despliegue-y-repositorio.md#archivos-de-tarea-locales-localmd).

## 3. Roles y organización

### Coordinación (coordinador, `0V3R`)

**Qué es.** El rol que cierra decisiones, firma experimentos y aprueba adopciones.

**En el proyecto.** Es Eduardo (usuario de GitHub `0V3R`, Eduardo Rivas), uno de los tres integrantes dedicados a programar, con rol específico de **revisor técnico y QA** dentro del trío. Aparece en los documentos como «el coordinador», «decisión del coordinador» o «Eduardo». Sus firmas fijan fórmulas (M3 el 2026-08-21, M4 el 2026-09-08), autorizan la predicción (2026-09-09) y ratifican cierres. Los experimentos **no** adoptan nada por su cuenta: «tú produces números y una recomendación; adoptar es decisión de Eduardo».

### INSAMT y Equipo 4

**Qué es.** La institución y el equipo que hacen el proyecto.

**En el proyecto.** **INSAMT** es el Instituto Nacional de San Miguel Tepezontes (El Salvador). El proyecto lo desarrollan estudiantes de tercer año de Bachillerato Técnico Vocacional en Desarrollo de Software, **Equipo 4**: cinco integrantes, tres dedicados a tiempo completo a programar. Se presenta en la **Expotécnica**. Las alertas de campo se firman como «Equipo de vigilancia EPI-Aetheris (INSAMT, Equipo 4)».

### Expotécnica y Expo Técnica

**Qué es.** El evento de presentación de proyectos de la asignatura Desarrollo de Software.

**En el proyecto.** Fecha límite práctica: **2026-09-29**. El plazo del MVP era de 2 meses desde la selección de la propuesta. El video demo tenía fecha 2026-09-05. Ver el formato en `STC/glosario/`.

### Orientador y evaluador externo

**Qué es.** Dos figuras del informe de investigación.

**En el proyecto.** El **orientador** sugirió cambiar la hipótesis del Capítulo III a algo medible de forma concreta (las variables anteriores eran «muy técnicas y complicadas de demostrar, porque hablan de clima»). El **evaluador externo** es una persona con formación en ciencias de la computación, ajena al desarrollo, que repite una submuestra de 5 consultas para controlar el sesgo.

### Isaac y la tarea de rescate

**Qué es.** La persona a quien se asignó la tarea de rescatar la capa de predicción.

**En el proyecto.** Con la coordinación de Eduardo. Ver [Vías de rescate](04-estadistica-y-modelado.md#vías-de-rescate-1-a-4).

### Tarjeta

**Qué es.** Unidad de trabajo del tablero de gestión del equipo (el CHANGELOG histórico dice que las decisiones se registran «primero en Trello y trasladadas aquí»).

**En el proyecto.** El código y los ADR citan «tarjeta 11» (carga de OpenDengue), «tarjeta 12» (loader de clima), «tarjeta 20» (llamada de prueba a Open-Meteo), «tarjeta 22» (parser de producción), «tarjeta 23» (dataset de modelado), «tarjeta 24» (entrenamiento del clasificador), «tarjeta 25» (mapa descriptivo) y «tarjeta 26» (rescate de los boletines problemáticos).

### Hito

**Qué es.** Punto de control con fecha en el plan del proyecto.

**En el proyecto.** El CHANGELOG histórico menciona el **Hito 1** (el 2026-08-09 se cerraron dos de sus tres decisiones bloqueantes) y el **Hito 2** (que vencía el 2026-08-16). No confundir con los **tags `hito/*`** de Git, que son una serie narrativa de nueve tags para recorrer la evolución del proyecto en la Expotécnica ([Releases y tags de hito](08-infraestructura-despliegue-y-repositorio.md#releases-y-tags-de-hito)).

### Pivote

**Qué es.** Cambio de rumbo del proyecto.

**En el proyecto.** El **pivote a herramienta descriptiva** (2026-08-18) retiró el clasificador de riesgo y dio el nombre «Camino Ancho». El **pivote de fase 1 «Opción C»** (2026-08-09) fue el plan intermedio del clasificador nacional. Ver [Camino Ancho](04-estadistica-y-modelado.md#camino-ancho).

### Nombre del proyecto

**Qué es.** El nombre vigente y los descartados.

**En el proyecto.** **EPI-Aetheris** es el nombre vigente. «EPI Aethery» fue un error de transcripción (julio de 2026) y «EPICAST» es el codename histórico de ideación: ninguno de los dos se usa en material nuevo. **Aetheris Nitor** es el repositorio vitrina del segundo frontend.

### Propuestas descartadas

**Qué es.** Ideas de proyecto que el equipo evaluó y rechazó antes de EPI-Aetheris.

**En el proyecto.** **AULA-PULSE** (deserción escolar: datos personales de menores y sin dataset público), **PHISH-GUARD** (phishing: campo saturado) y **GRID-SENSE** (anomalías de consumo eléctrico: datos insuficientes para una demo convincente). Además, **fabricar datasets propios está prohibido** como principio.

### Informe de investigación e hipótesis

**Qué es.** El documento escrito del proyecto, con cuatro capítulos, y su hipótesis.

**En el proyecto.** La hipótesis del Capítulo III (cerrada el 2026-09-23) mide el efecto del sistema sobre el problema declarado en el Capítulo I: la dispersión de la información de vigilancia en boletines PDF. **H1:** el sistema reduce al menos un 50 % el tiempo para obtener el número semanal de casos probables de un departamento, con exactitud de al menos el 95 % frente a las cifras de los boletines; **H0:** su negación. Se decide con 20 consultas (exactitud ≥ 95 % = al menos 19 correctas). La variable independiente es el método de consulta y la dependiente la eficiencia (tiempo y exactitud). El nowcast **no cambia como producto**: sus resultados pasan a «resultados técnicos complementarios». Ver el detalle en `STC/glosario/`.

### Aviso de honestidad (`AVISO_HONESTIDAD_*`)

**Qué es.** Texto que un endpoint o pantalla declara sobre qué mide y qué niega.

**En el proyecto.** Ver [Aviso de honestidad](05-modulos-descriptivos-y-alertas.md#aviso-de-honestidad-aviso_honestidad_).

## 4. Trabajo con agentes

### Analizar, proponer, implementar, validar, revisar diff

**Qué es.** El flujo de trabajo de `AGENTS.md` §13.

**En el proyecto.** Se **analiza** (archivos, dependencias, documentación, decisiones), se **propone** cuando hay una decisión técnica no trivial (sin convertirla automáticamente en decisión arquitectónica), se **implementa** el cambio mínimo, se **valida** (tests, linters, tipos) y se **revisa el diff** (sin archivos ajenos ni cambios accidentales).

### Coordinación entre agentes

**Qué es.** Convivencia de varios agentes y worktrees sobre el mismo stack.

**En el proyecto.** Un solo stack Docker compartido (nombres y puertos fijos): un worktree a la vez. Ver [Worktree y Orca ADE](08-infraestructura-despliegue-y-repositorio.md#worktree-y-orca-ade).
