# Glosario técnico de EPI-Aetheris

Vocabulario técnico del proyecto, organizado en diez ramas: el de la epidemiología y la vigilancia, el de los datos y su ingesta, el de la estadística del nowcast y el del código (API, base de datos, despliegue, frontend y proceso). Son **585 entradas** pensadas para interpretar un boletín, una cifra del sitio, un ADR o un módulo del código sin tener que preguntar qué significa cada palabra.

> **Este glosario describe; no decide.** Las decisiones viven en los ADR (`docs/adr/`). Si una entrada contradice un ADR, manda el ADR (ver [Precedencia de fuentes](10-proceso-gobernanza-y-documentacion.md#precedencia-de-fuentes)). Redactado el 2026-09-30 sobre el commit `1a69116`; los textos que ya no coinciden con el repositorio están en las [Notas de vigencia](#notas-de-vigencia).

## Para quién es

- **Quien recibe una cifra o una alerta** y necesita saber qué mide, qué no mide y con qué cautela se lee.
- **Quien entra al código o a los ADR** y se encuentra con términos internos («familia B», «fold», «contrato `disponible: false`», «pool ±1»).
- **Quien evalúa el proyecto** (orientación, jurado, colaboración nueva) y necesita el mapa de lo que el sistema afirma y de lo que se abstiene de afirmar.

**Lo que no es.** No es la documentación de producto (esa es la Biblioteca pública, `docs/biblioteca/`), ni la fuente de las decisiones (los ADR), ni la guía para agentes (`AGENTS.md`). Cada entrada dice dónde vive la fuente; ante una diferencia, vale la fuente.

## Mapa de ramas

Cada archivo tiene su propio índice alfabético al comienzo y se lee de forma independiente.

| Rama | Archivo | Qué reúne | Entradas |
|---|---|---|---|
| 1 | [`01-epidemiologia-y-vigilancia.md`](01-epidemiologia-y-vigilancia.md) | Casos, semanas epidemiológicas, instituciones y sistemas, geografía administrativa, dengue, enfermedades respiratorias, cómo nombra el proyecto cada conteo y vocabulario clínico de las alertas | 96 |
| 2 | [`02-fuentes-de-datos-e-ingesta.md`](02-fuentes-de-datos-e-ingesta.md) | Las seis fuentes, cobertura y años, anatomía de un boletín de MINSAL, catálogo de trampas, desacumulación, bitácora, serie del tablero y datos respiratorios | 74 |
| 3 | [`03-clima-y-ambiente.md`](03-clima-y-ambiente.md) | Open-Meteo y ERA5, variables, agregación semanal, rezago y calidad, geografía para el clima, El Niño y el índice ONI | 44 |
| 4 | [`04-estadistica-y-modelado.md`](04-estadistica-y-modelado.md) | Nowcast, métricas (WIS, skill, cobertura), validación temporal anti-fuga, clasificador retirado, vías de rescate, lead time, percentiles | 98 |
| 5 | [`05-modulos-descriptivos-y-alertas.md`](05-modulos-descriptivos-y-alertas.md) | Módulos M1 a M4, dataset analítico, observatorio respiratorio y alertas de campo | 44 |
| 6 | [`06-backend-y-api.md`](06-backend-y-api.md) | FastAPI, límites de tasa y seguridad, pool de conexiones, degradación elegante, caché HTTP, endpoints, pruebas y configuración | 40 |
| 7 | [`07-base-de-datos-y-migraciones.md`](07-base-de-datos-y-migraciones.md) | Esquema, tablas, columnas con valores controlados, migraciones, volcado de datos reales, SQL y herramientas de línea de comandos | 43 |
| 8 | [`08-infraestructura-despliegue-y-repositorio.md`](08-infraestructura-despliegue-y-repositorio.md) | Docker Compose, Render, Git y flujo de ramas, GitHub Actions y herramientas de trabajo con agentes | 39 |
| 9 | [`09-frontend-web.md`](09-frontend-web.md) | Astro, rutas, estado por URL, visualización, accesibilidad, tokens de diseño, seguridad del frontend, service worker y pruebas | 72 |
| 10 | [`10-proceso-gobernanza-y-documentacion.md`](10-proceso-gobernanza-y-documentacion.md) | ADR, precedencia de fuentes, estatuto, documentación, roles, tarjetas, hitos y trabajo con agentes | 35 |

Las ramas 1 a 5 son el vocabulario **del dominio** (qué se cuenta, de dónde sale y cómo se interpreta); las ramas 6 a 9 son el vocabulario **de la ingeniería**; la rama 10 es el vocabulario **del proceso** con que se decide y se documenta.

## Por dónde empezar

### Veinte términos para empezar

Una lectura mínima, en este orden, deja preparado para casi cualquier otro documento del repositorio.

1. [Vigilancia epidemiológica descriptiva](01-epidemiologia-y-vigilancia.md#vigilancia-epidemiológica-descriptiva): el marco. El sistema describe lo observado y lo compara con su propia historia; no diagnostica ni clasifica riesgo de brote.
2. [Semana epidemiológica (SE)](01-epidemiologia-y-vigilancia.md#semana-epidemiológica-se): la unidad de tiempo de todo el proyecto, con el calendario MMWR y no con el ISO.
3. [Clasificación (`clasificacion`)](01-epidemiologia-y-vigilancia.md#clasificación-clasificacion): los cinco tipos de conteo (`probable`, `confirmado`, `total`, `sospechoso`, `notificado`), que nunca se suman entre sí.
4. [Conteo notificado](01-epidemiologia-y-vigilancia.md#conteo-notificado): qué mide de verdad una cifra: lo notificado, no lo enfermo.
5. [Hueco (sin dato) frente a cero](01-epidemiologia-y-vigilancia.md#hueco-sin-dato-frente-a-cero): el proyecto nunca convierte una ausencia en cero.
6. [Canal endémico](01-epidemiologia-y-vigilancia.md#canal-endémico): cómo se compara una semana con su propia historia.
7. [Boletines epidemiológicos de MINSAL (PDF)](02-fuentes-de-datos-e-ingesta.md#boletines-epidemiológicos-de-minsal-pdf): la única fuente con desglose departamental y la que más trampas tiene.
8. [Desacumulación](02-fuentes-de-datos-e-ingesta.md#desacumulación): los boletines traen el acumulado desde la SE1; el proyecto lo convierte en conteos semanales.
9. [Estados de la bitácora](02-fuentes-de-datos-e-ingesta.md#estados-de-la-bitácora): qué le pasó a cada boletín (`ok`, `revision_manual`, `ausencia_esperada`…).
10. [OpenDengue](02-fuentes-de-datos-e-ingesta.md#opendengue): la serie nacional semanal de referencia.
11. [Agregación diaria a semana epidemiológica](03-clima-y-ambiente.md#agregación-diaria-a-semana-epidemiológica): cómo el clima diario se vuelve una fila por semana.
12. [Nowcast de dengue](04-estadistica-y-modelado.md#nowcast-de-dengue): la única predicción del sistema, del conteo nacional de casos.
13. [WIS (Weighted Interval Score)](04-estadistica-y-modelado.md#wis-weighted-interval-score): la métrica con que se juzga esa predicción.
14. [Clasificador de riesgo retirado](04-estadistica-y-modelado.md#clasificador-de-riesgo-retirado): por qué el sistema no predice riesgo de brote.
15. [Módulos descriptivos (M1 a M4)](05-modulos-descriptivos-y-alertas.md#módulos-descriptivos-m1-a-m4): lo que el sistema calcula a pedido y sin persistir.
16. [Alerta de campo](05-modulos-descriptivos-y-alertas.md#alerta-de-campo): el canal de avisos que redacta el equipo de vigilancia.
17. [Contrato `disponible: false`](06-backend-y-api.md#contrato-disponible-false): cómo responde la API cuando falta un artefacto o un dato.
18. [Tabla catálogo y tabla de hechos](07-base-de-datos-y-migraciones.md#tabla-catálogo-y-tabla-de-hechos): la idea central del esquema.
19. [Estado por URL](09-frontend-web.md#estado-por-url): por qué los filtros del sitio viajan en la dirección.
20. [ADR (Architecture Decision Record)](10-proceso-gobernanza-y-documentacion.md#adr-architecture-decision-record): dónde se decide y quién manda cuando dos documentos discrepan.

### Rutas según lo que se quiere hacer

- **Leer una cifra del sitio.** [Semana epidemiológica](01-epidemiologia-y-vigilancia.md#semana-epidemiológica-se) → [Clasificación](01-epidemiologia-y-vigilancia.md#clasificación-clasificacion) → [Conteo notificado](01-epidemiologia-y-vigilancia.md#conteo-notificado) → [Hueco frente a cero](01-epidemiologia-y-vigilancia.md#hueco-sin-dato-frente-a-cero) → [Canal endémico](01-epidemiologia-y-vigilancia.md#canal-endémico) → [Percentil de presión](05-modulos-descriptivos-y-alertas.md#percentil-de-presión).
- **Saber de dónde salen los datos.** [Fuente de datos](02-fuentes-de-datos-e-ingesta.md#fuente-de-datos-fuentes_datos) → [Boletines de MINSAL](02-fuentes-de-datos-e-ingesta.md#boletines-epidemiológicos-de-minsal-pdf) → [Tablero de vigilancia de MINSAL](02-fuentes-de-datos-e-ingesta.md#tablero-de-vigilancia-de-minsal-superset) → [Trampas de las fuentes](02-fuentes-de-datos-e-ingesta.md#trampas-de-las-fuentes-catálogo) → [Serie mixta (empalme)](02-fuentes-de-datos-e-ingesta.md#serie-mixta-empalme).
- **Leer o modificar la ingesta.** [Ingesta](02-fuentes-de-datos-e-ingesta.md#ingesta) → [Familia A y Familia B](02-fuentes-de-datos-e-ingesta.md#familia-a-y-familia-b) → [Acumulado desde SE1](02-fuentes-de-datos-e-ingesta.md#acumulado-desde-se1) → [Desacumulación](02-fuentes-de-datos-e-ingesta.md#desacumulación) → [Bitácora de boletines](02-fuentes-de-datos-e-ingesta.md#bitácora-de-boletines-boletines_procesados) → [Cuadre](02-fuentes-de-datos-e-ingesta.md#cuadre-validacion_cuadra) → [Revisión manual documentada](02-fuentes-de-datos-e-ingesta.md#revisión-manual-documentada-revisiones_manuales).
- **Interpretar el clima.** [Variable ambiental](03-clima-y-ambiente.md#variable-ambiental) → [ERA5-Land](03-clima-y-ambiente.md#era5-land) → [Agregación diaria a semana epidemiológica](03-clima-y-ambiente.md#agregación-diaria-a-semana-epidemiológica) → [Semana incompleta](03-clima-y-ambiente.md#semana-incompleta-dias_minimos_semana) → [Cero falso de la precipitación](03-clima-y-ambiente.md#cero-falso-de-la-precipitación) → [ONI](03-clima-y-ambiente.md#oni-oceanic-niño-index).
- **Entender el nowcast y el clasificador retirado.** [Nowcast de dengue](04-estadistica-y-modelado.md#nowcast-de-dengue) → [Forward-chaining](04-estadistica-y-modelado.md#forward-chaining-ventana-expansiva) → [Fuga de información](04-estadistica-y-modelado.md#fuga-de-información-leakage) → [WIS](04-estadistica-y-modelado.md#wis-weighted-interval-score) → [Skill relativo](04-estadistica-y-modelado.md#skill-relativo) → [Mezcla C](04-estadistica-y-modelado.md#mezcla-c) → [Prueba prospectiva](04-estadistica-y-modelado.md#prueba-prospectiva) → [Clasificador de riesgo retirado](04-estadistica-y-modelado.md#clasificador-de-riesgo-retirado) → [Vías de rescate](04-estadistica-y-modelado.md#vías-de-rescate-1-a-4).
- **Trabajar sobre módulos y alertas.** [Módulos descriptivos](05-modulos-descriptivos-y-alertas.md#módulos-descriptivos-m1-a-m4) → [M1](05-modulos-descriptivos-y-alertas.md#m1-idoneidad-biofísica-iv) → [M2](05-modulos-descriptivos-y-alertas.md#m2-anomalía-climática-continua) → [M3](05-modulos-descriptivos-y-alertas.md#m3-presión-epidemiológica-relativa) → [M4](05-modulos-descriptivos-y-alertas.md#m4-integridad-de-la-vigilancia) → [Alerta de campo](05-modulos-descriptivos-y-alertas.md#alerta-de-campo) → [Alcance territorial](05-modulos-descriptivos-y-alertas.md#alcance-territorial-departamentos).
- **Tocar la API.** [FastAPI](06-backend-y-api.md#fastapi) → [Contrato `disponible: false`](06-backend-y-api.md#contrato-disponible-false) → [Degradación elegante](06-backend-y-api.md#degradación-elegante) → [Rate limiting](06-backend-y-api.md#rate-limiting-slowapi) → [Bearer y `ALERTAS_TOKEN`](06-backend-y-api.md#bearer-y-alertas_token) → [Endpoints de dengue](06-backend-y-api.md#endpoints-de-dengue).
- **Tocar la base de datos.** [Tabla catálogo y tabla de hechos](07-base-de-datos-y-migraciones.md#tabla-catálogo-y-tabla-de-hechos) → [`casos_epidemiologicos`](07-base-de-datos-y-migraciones.md#casos_epidemiologicos) → [Migración](07-base-de-datos-y-migraciones.md#migración) → [ADR antes de migración](07-base-de-datos-y-migraciones.md#adr-antes-de-migración) → [Volcado versionado (seed)](07-base-de-datos-y-migraciones.md#volcado-versionado-seed).
- **Desplegar.** [Docker Compose](08-infraestructura-despliegue-y-repositorio.md#docker-compose-y-docker-compose-up) → [Perfil de Compose](08-infraestructura-despliegue-y-repositorio.md#perfil-de-compose-profiles) → [Blueprint](08-infraestructura-despliegue-y-repositorio.md#blueprint-renderyaml) → [Primer despliegue](08-infraestructura-despliegue-y-repositorio.md#primer-despliegue-pasos-manuales-una-sola-vez) → [Cambios de esquema después del primer despliegue](08-infraestructura-despliegue-y-repositorio.md#cambios-de-esquema-después-del-primer-despliegue).
- **Tocar el frontend.** [Astro](09-frontend-web.md#astro) → [Estado por URL](09-frontend-web.md#estado-por-url) → [Eventos `epi:*`](09-frontend-web.md#eventos-epi) → [Workspace analítico](09-frontend-web.md#workspace-analítico) → [Tokens de diseño](09-frontend-web.md#tokens-de-diseño) → [Service worker](09-frontend-web.md#service-worker-swjs) → [Playwright y axe](09-frontend-web.md#playwright-y-axe).
- **Entender cómo se decide.** [ADR](10-proceso-gobernanza-y-documentacion.md#adr-architecture-decision-record) → [Precedencia de fuentes](10-proceso-gobernanza-y-documentacion.md#precedencia-de-fuentes) → [Estatuto y principios no negociables](10-proceso-gobernanza-y-documentacion.md#estatuto-y-principios-no-negociables) → [Decisiones cerradas y abiertas](10-proceso-gobernanza-y-documentacion.md#decisiones-cerradas-y-decisiones-abiertas) → [Tarjeta](10-proceso-gobernanza-y-documentacion.md#tarjeta) → [Hito](10-proceso-gobernanza-y-documentacion.md#hito).

## Siglas y abreviaturas

Las expansiones **sin marca** están escritas en el propio repositorio. Las marcadas con **†** son de uso general: el repositorio usa la sigla sin expandirla y la expansión la aporta este glosario. Cuatro siglas (VIGEPES, UVET, UVETV y SIMMOW) no tienen expansión en el repositorio y este glosario tampoco la inventa.

| Sigla | Significa | Entrada |
|---|---|---|
| ADR | Architecture Decision Record (registro de decisión de arquitectura) | [ADR](10-proceso-gobernanza-y-documentacion.md#adr-architecture-decision-record) |
| AINE | Antiinflamatorios no esteroideos † | [AINE](01-epidemiologia-y-vigilancia.md#aine) |
| AUC | Área bajo la curva † | [Matriz de confusión, falsos positivos, AUC y soporte](04-estadistica-y-modelado.md#matriz-de-confusión-falsos-positivos-auc-y-soporte) |
| CDC | Centers for Disease Control and Prevention (EE. UU.) † | [CDC y MMWR](01-epidemiologia-y-vigilancia.md#cdc-y-mmwr) |
| CORS | Cross-Origin Resource Sharing | [CORS](06-backend-y-api.md#cors-cors_allowed_origins) |
| CQR | Conformalized Quantile Regression (regresión cuantílica conformalizada) † | [CQR-r](04-estadistica-y-modelado.md#cqr-r) |
| CSP | Content-Security-Policy | [CSP](06-backend-y-api.md#csp-content-security-policy) |
| EAV | Entidad–atributo–valor † | [EAV](07-base-de-datos-y-migraciones.md#eav-entidadatributovalor) |
| ECMWF | European Centre for Medium-Range Weather Forecasts † | [ECMWF IFS](03-clima-y-ambiente.md#ecmwf-ifs) |
| EDAS | Enfermedades diarreicas agudas † | [Boletines epidemiológicos de MINSAL (PDF)](02-fuentes-de-datos-e-ingesta.md#boletines-epidemiológicos-de-minsal-pdf) |
| ERA5 | Quinta generación del reanálisis de ECMWF (ECMWF Reanalysis v5) † | [ERA5](03-clima-y-ambiente.md#era5) |
| ET₀ | Evapotranspiración de referencia † | [Evapotranspiración de referencia](03-clima-y-ambiente.md#evapotranspiración-de-referencia-et₀) |
| ETI | Enfermedad tipo influenza † | [ETI](01-epidemiologia-y-vigilancia.md#eti-enfermedad-tipo-influenza) |
| HAR | HTTP Archive (captura del tráfico de red del navegador) † | [Captura HAR](02-fuentes-de-datos-e-ingesta.md#captura-har) |
| HR | Humedad relativa | [Humedad relativa media](03-clima-y-ambiente.md#humedad-relativa-media-humedad_relativa_media) |
| IFS | Integrated Forecasting System (modelo de ECMWF) † | [ECMWF IFS](03-clima-y-ambiente.md#ecmwf-ifs) |
| INSAMT | Instituto Nacional de San Miguel Tepezontes | [INSAMT y Equipo 4](10-proceso-gobernanza-y-documentacion.md#insamt-y-equipo-4) |
| IRA | Infección respiratoria aguda | [IRA](01-epidemiologia-y-vigilancia.md#ira-infección-respiratoria-aguda) |
| IRAG | Infección respiratoria aguda grave | [IRAG e IRAGI](01-epidemiologia-y-vigilancia.md#irag-e-iragi) |
| IRAGI | Infección respiratoria aguda inusitada | [IRAG e IRAGI](01-epidemiologia-y-vigilancia.md#irag-e-iragi) |
| IRAS | Infecciones respiratorias agudas de vías superiores | [IRAS](01-epidemiologia-y-vigilancia.md#iras-infecciones-respiratorias-agudas-de-vías-superiores) |
| ISO 3166-2:SV | Código de subdivisiones de El Salvador (`SV-AH`…) † | [Código ISO 3166-2:SV](01-epidemiologia-y-vigilancia.md#código-iso-3166-2sv) |
| ISO 8601 | Norma internacional de fechas, con su propia numeración de semanas † | [ISO 8601 (semanas)](01-epidemiologia-y-vigilancia.md#iso-8601-semanas) |
| Iv | Índice de idoneidad biofísica (módulo M1) | [M1](05-modulos-descriptivos-y-alertas.md#m1-idoneidad-biofísica-iv) |
| LOO | Leave-one-out (dejar uno fuera) | [Leave-one-out](04-estadistica-y-modelado.md#leave-one-out-loo) |
| M1 a M4 | Módulos descriptivos: idoneidad biofísica, anomalía climática, presión epidemiológica, integridad de la vigilancia | [Módulos descriptivos](05-modulos-descriptivos-y-alertas.md#módulos-descriptivos-m1-a-m4) |
| MINSAL | Ministerio de Salud de El Salvador | [MINSAL](01-epidemiologia-y-vigilancia.md#minsal) |
| MMWR | Morbidity and Mortality Weekly Report † | [CDC y MMWR](01-epidemiologia-y-vigilancia.md#cdc-y-mmwr) |
| NOAA | National Oceanic and Atmospheric Administration † | [ONI](03-clima-y-ambiente.md#oni-oceanic-niño-index) |
| OCR | Reconocimiento óptico de caracteres † | [OCR](02-fuentes-de-datos-e-ingesta.md#ocr) |
| OMS | Organización Mundial de la Salud † | [OPS y OMS](01-epidemiologia-y-vigilancia.md#ops-y-oms) |
| ONI | Oceanic Niño Index | [ONI](03-clima-y-ambiente.md#oni-oceanic-niño-index) |
| OPS | Organización Panamericana de la Salud † | [OPS y OMS](01-epidemiologia-y-vigilancia.md#ops-y-oms) |
| P50, P75, P90 | Percentiles 50, 75 y 90 | [Cortes de percentil](04-estadistica-y-modelado.md#cortes-de-percentil-p50p75-y-p75p90) |
| PAHO | Pan American Health Organization (nombre en inglés de la OPS) † | [OPS y OMS](01-epidemiologia-y-vigilancia.md#ops-y-oms) |
| PLISA | Plataforma de Información en Salud para las Américas † | [PAHO PLISA](01-epidemiologia-y-vigilancia.md#paho-plisa) |
| PR | Pull request † | [Plantillas de PR y de issue](08-infraestructura-despliegue-y-repositorio.md#plantillas-de-pr-y-de-issue) |
| PWA | Progressive Web App † | [Manifiesto web](09-frontend-web.md#manifiesto-web-manifestwebmanifest) |
| RIC | Rango intercuartílico † | [RIC](04-estadistica-y-modelado.md#ric-rango-intercuartílico) |
| SE | Semana epidemiológica | [Semana epidemiológica (SE)](01-epidemiologia-y-vigilancia.md#semana-epidemiológica-se) |
| SIBASI | Sistemas Básicos de Salud Integral † | [SIBASI](01-epidemiologia-y-vigilancia.md#sibasi) |
| SIMMOW | Sin expansión en el repositorio (sistema de MINSAL de egresos, fallecidos y letalidad) | [SIMMOW](01-epidemiologia-y-vigilancia.md#simmow) |
| SLV | Código ISO 3166-1 alfa-3 de El Salvador † | [geoBoundaries (gbOpen)](02-fuentes-de-datos-e-ingesta.md#geoboundaries-gbopen) |
| TTL | Time to live (vida útil de una respuesta en caché) † | [`Cache-Control` y TTL](06-backend-y-api.md#cache-control-y-ttl) |
| UVET, UVETV | Sin expansión en el repositorio (unidad que consolida el boletín semanal) | [UVET y UVETV](01-epidemiologia-y-vigilancia.md#uvet-y-uvetv) |
| VIGEPES | Sin expansión en el repositorio (sistema de vigilancia de MINSAL) | [VIGEPES](01-epidemiologia-y-vigilancia.md#vigepes) |
| VSR | Virus sincitial respiratorio | [VSR, parainfluenza y adenovirus](01-epidemiologia-y-vigilancia.md#vsr-parainfluenza-y-adenovirus) |
| WCAG | Web Content Accessibility Guidelines † | [Accesibilidad web (WCAG, AA)](09-frontend-web.md#accesibilidad-web-wcag-aa) |
| WIS | Weighted Interval Score (puntuación de intervalo ponderada) | [WIS](04-estadistica-y-modelado.md#wis-weighted-interval-score) |
| XSS | Cross-site scripting † | [`escapeHtml` y XSS](09-frontend-web.md#escapehtml-y-xss) |

## Cómo está escrito

- **Estructura de un archivo.** Título, «Para quién es», «Cómo leer una entrada», «Ramas vecinas», el **índice alfabético** de todas sus entradas, y luego las secciones (`##`) con las entradas (`###`).
- **Estructura de una entrada.** **Qué es** (la definición general) y **En el proyecto** (cómo la usa EPI-Aetheris, con los valores exactos); cuando aporta, **Ojo** (errores de interpretación frecuentes) y **Dónde** (archivo, ADR o endpoint donde vive la fuente). Las entradas muy breves, como una institución, un signo clínico o un valor de columna, van en un solo párrafo.
- **Código y nombres exactos.** Tablas, columnas, variables de entorno, rutas y funciones van en `monoespaciado`, tal como aparecen en el repositorio.
- **Términos en inglés.** *Nowcast*, *fold*, *leakage*, *skill* o *pool* se conservan porque el código y los ADR los usan así; cada uno se explica en español.
- **Citas.** Los textos copiados de documentos del proyecto o de MINSAL van entre «comillas angulares».
- **Cifras.** Se copiaron del código, de los ADR o de los datos versionados. Cuando el dato cambia con el tiempo, la entrada lleva su fecha; si difiere de lo que hoy dice el ADR, vale el ADR.
- **Voz.** Español neutro. No se asignan pronombres a las personas: se las nombra por su nombre o por su rol («la coordinación»).

## Dónde vive este glosario

`AGENTS.md` §16 fija que `docs/` contiene solo `adr/`, `biblioteca/` y `despliegue-render.md`, y pide no crear carpetas de documentación nuevas. Esta carpeta existe por un encargo expreso de reunir el vocabulario técnico por ramas, así que es una excepción a esa regla que conviene ratificar o mover. Dos datos para decidirlo:

- **No es una colección de Astro.** Los archivos no llevan `frontmatter` y `web/src/content.config.ts` solo carga `docs/biblioteca/*.md`; el glosario no entra al sitio ni a `/biblioteca` y no puede romper el build.
- **Mover la carpeta es barato.** Los enlaces entre archivos son relativos; solo habría que ajustar los que apuntan a `../adr/`.

## Notas de vigencia

Este glosario sigue el código y los ADR. Al recorrerlos aparecieron textos del propio repositorio que ya no coinciden con su estado actual. **No se corrigieron aquí** (no forman parte de este glosario); se listan para que quien lea sepa a qué documento creerle. Las líneas son las del commit `1a69116` (2026-09-30).

1. **`README.md` de la raíz** (líneas 10, 12 y 38, y la tabla de variables). Dice «Astro 4», «Docker Compose (3 servicios)» y un volcado de «~4,4 MB». Hoy `web/package.json` declara `astro ^7.2.8`; `docker-compose.yml` define cuatro servicios (`db`, `backend`, `web` y `e2e`), de los cuales `web` y `e2e` van bajo los perfiles `web` y `test` y no arrancan por defecto; y `db/seed/seed_datos_reales.sql` pesa 5.675.731 bytes (unos 5,7 MB). Su tabla de variables lista solo las cinco `POSTGRES_*`, mientras `.env.example` define 16 variables activas.
2. **`AGENTS.md`.**
   - Líneas 460 y 504: atribuyen la fórmula de M4 al ADR 0018. M4 es el [ADR 0019](../adr/0019-integridad-vigilancia.md); el 0018 extiende la capa climática al presente.
   - Líneas 481 y 484: la lista de valores de `clasificacion` omite `sospechoso` ([ADR 0021](../adr/0021-fuente-tablero-minsal.md)) y la de `fuentes_datos.codigo` omite `minsal_tablero`.
   - Línea 485: dice que `regiones.codigo` está «sin verificar aún» contra el GeoJSON. El [ADR 0002](../adr/0002-join-mapa-geojson-por-nombre.md) lo resolvió (14 de 14, 2026-08-05) con la unión por nombre normalizado.
   - Línea 516: «No hay linter ni CI en el repo». Existen `.github/workflows/backend-tests.yml` (además de los dos flujos de Claude) y los scripts `lint` y `format:check` de `web/package.json`.
   - §16: dice que los protocolos de experimentos no se versionan y que `docs/` solo tiene tres elementos; existe `docs/experimentos/` y este glosario suma `docs/glosario/`.
   - Línea 99 (§5): define el sistema como «herramienta de apoyo para estimar y comunicar riesgo». Es una formulación más amplia que la del resto del proyecto: vigilancia descriptiva, con un único ejercicio predictivo (el nowcast de conteo, [ADR 0020](../adr/0020-nowcast-corto-plazo.md)) y con el clasificador de riesgo de brote retirado.
3. **`backend/ingestion/data/README.md`** (línea 18). Dice «resolución semanal desde 2018» para la serie nacional de OpenDengue. El volcado versionado contiene **574 semanas** nacionales (`clasificacion = 'total'`) de 2014 a 2024, y `cargar_opendengue.py` usa 2018 solo como año de inicio por defecto (`ANIO_INICIO_DEFAULT`).
4. **Atribución de geoBoundaries.** El [ADR 0002](../adr/0002-join-mapa-geojson-por-nombre.md) (línea 42) y la Biblioteca 04 (línea 79) la dan por pendiente, pero `web/src/pages/legal/terminos.astro` (sección 6, línea 229) ya declara que los límites departamentales de geoBoundaries van con licencia CC BY-SA 2.0. Lo que el ADR 0002 deja abierto de fondo (qué licencia rige, la de origen en OpenStreetMap o la que geoBoundaries reafirma) no consta como resuelto en ningún documento.
5. **Cifras del volcado en la Biblioteca.** La Biblioteca 04 (línea 65) cita «35.868 filas» de clima para 2018–2024; el volcado trae hoy 65.450 filas en `variables_ambientales` (9.268 por cada una de las 7 variables climáticas y 574 de `oni_anom`, de 2014 a 2026). Las Bibliotecas 05 (línea 77) y 06 (línea 42) dicen «4,4 MB»; esa es la medición del [ADR 0010](../adr/0010-versionar-volcado-de-datos-reales.md) al decidir, y hoy el archivo pesa unos 5,7 MB.
6. **Rutas movidas al archivo histórico.** Comentarios de `web/src/components/MapaDepartamentos.astro` (línea 6), `web/src/components/CurvaEpidemicaNacional.astro` (línea 8) y `web/src/content.config.ts` (línea 7) citan `docs/contexto/...`. Esa carpeta salió de este repositorio el 2026-09-25 hacia el repositorio STC, donde equivale a `EPI-Aetheris/historico/contexto/`.
7. **Estado de los boletines sin tabla.** El [ADR 0007](../adr/0007-bitacora-boletines-estado-sin-texto-extraible.md) (línea 32) y `MAPA_ESTADO` en `backend/ingestion/minsal/parser.py` (línea 63) mapean `sin_tabla_no_vacacional` a `revision_manual`, y el ADR usa `SE182023` como ejemplo. La revisión manual de la tarjeta 26 (2026-08-16), aplicada con `REVISIONES_MANUALES` en el mismo archivo, reclasificó seis boletines (entre ellos `SE182023`) a `ausencia_esperada` y uno (`SE302019_v2`) a `ok`. En la bitácora, `SE182023` figura como `ausencia_esperada`.
8. **Ancla del nowcast.** El [ADR 0020](../adr/0020-nowcast-corto-plazo.md) dice en su cuerpo (líneas 121 y 122) que el ancla es la última semana de OpenDengue (2024-12-22, unos 21 meses atrás) y, en su enmienda (línea 208), que con la serie del tablero el ancla queda unas dos semanas detrás del tiempo real. Los dos textos son del mismo documento; vale la enmienda.
9. **Códigos de estado.** Los endpoints `/api/v1/` responden 422 a un parámetro inválido (validación de FastAPI) y los respiratorios responden 400 (`HTTPException` explícita en `backend/api/main.py`). La convención no es uniforme; ver [Códigos de estado](06-backend-y-api.md#códigos-de-estado).
10. **Índice de herramientas `/analisis`** (`web/src/pages/analisis.astro`, línea 18). Describe la tarjeta de dengue con «presión epidemiológica relativa como percentil (M3) y nowcast de la semana en curso (M4)». M4 es la integridad de la vigilancia ([ADR 0019](../adr/0019-integridad-vigilancia.md)); el nowcast es la predicción de 1 a 8 semanas que parte de la última semana observada ([ADR 0020](../adr/0020-nowcast-corto-plazo.md)), no una estimación de la semana en curso. El mismo texto está en `aetheris-nitor`.
11. **Anclas del glosario de la interfaz.** `web/src/lib/glosario.ts` enlaza a secciones de la Biblioteca con anclas como `#m1-idoneidad-biofísica-iv` o `#boletines-epidemiológicos-de-minsal`. En la Biblioteca de este repositorio seis de las diez anclas no existen: los encabezados llevan raya («M1 — Idoneidad biofísica»), que genera `m1--idoneidad-biofísica-iv`, y el documento 04 no tiene una sección «Tablero de vigilancia de MINSAL». El enlace abre el documento, pero no la sección. En `aetheris-nitor` las diez anclas existen.
12. **Arranque con Docker Compose en la Biblioteca 06.** El documento (líneas 10 a 31) y la portada del sitio («Tres servicios que se levantan juntos») dicen que `docker compose up --build` levanta tres contenedores y deja el sitio en `http://localhost:4321`. Desde el commit `82c5077` (#156) el servicio `web` va bajo el perfil `web` y hay que pedirlo aparte: `docker compose --profile web up -d web`. El `README.md` de la raíz ya recoge el cambio (línea 36); la Biblioteca 06 de ambos repositorios no. La misma Biblioteca dice «unos 4,4 MB» para el volcado (ver la nota 5).
13. **Versión del paquete web.** `web/package.json` (`aetheris-web`) declara la versión `0.5.0`, igual que el de `aetheris-nitor`, aunque el último release del repositorio es `v1.0.0` (2026-09-28): el número del paquete no se actualizó con los releases posteriores a `v0.5.0`.

## Relación con los otros repositorios

El proyecto se reparte en tres repositorios de la organización `the-monolith-project`, y cada uno tiene su propio glosario en la misma rama de trabajo.

- **[aetheris-nitor](https://github.com/the-monolith-project/aetheris-nitor)**: el frontend del sitio público (`aetheris-web`, versión 0.5.0), con las páginas legales y su propia Biblioteca. Su directorio `src/` es hoy idéntico al de `web/src/` de este repositorio (96 archivos sin diferencias); difieren dos pruebas de extremo a extremo y los cinco documentos de la Biblioteca, que están reescritos (por ejemplo, el documento 05 se titula «Aviso de sensibilidad» allá y «Sensibilidad y honestidad» aquí). Su glosario, en `docs/glosario/` (237 entradas en cuatro ramas), cubre el vocabulario de la interfaz, el tooling web, lo legal y el contrato de datos que consume; la rama 9 de este glosario describe el mismo código desde este lado.
- **[STC](https://github.com/the-monolith-project/STC)**: el marco de trabajo TMP-STC y el **archivo histórico** de EPI-Aetheris (`EPI-Aetheris/historico/`), que salió de este repositorio el 2026-09-25. Su glosario, en `glosario/` (285 entradas en cuatro ramas), cubre la metodología del marco, el vocabulario de los documentos históricos (datos y epidemiología, modelado y validación) y las decisiones y la cronología. Las rutas `docs/contexto/...` o `docs/rescate-prediccion/...` que citan textos de este repositorio equivalen allá a la misma ruta sin el prefijo `docs/`, bajo `EPI-Aetheris/historico/`.

## Mantenimiento

- **Cuándo entra un término.** Cuando un lector externo no lo entendería sin ayuda y el proyecto lo usa con un sentido preciso, o con uno distinto del general. Los términos de cultura general de programación o de salud no se explican salvo que el proyecto los use de forma particular.
- **Si cambia el vocabulario.** Un ADR nuevo actualiza la entrada existente (con su fecha), no crea una entrada paralela. Si el ADR reemplaza un término, la entrada vieja se conserva con una nota de vigencia, como el [clasificador de riesgo retirado](04-estadistica-y-modelado.md#clasificador-de-riesgo-retirado).
- **El índice alfabético.** El bloque entre `<!-- INDICE:INICIO -->` y `<!-- INDICE:FIN -->` de cada archivo se generó a partir de los encabezados `###` y hoy se mantiene a mano: al agregar, renombrar o quitar una entrada hay que actualizar su línea. Las anclas siguen las reglas de GitHub (minúsculas, sin signos de puntuación, espacios convertidos en guiones y sufijo `-1` en un encabezado repetido).
- **Cifras.** Las que cambian con la ingesta (conteos del volcado, semanas cargadas) se rehacen contando sobre el archivo, no de memoria.
