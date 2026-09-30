# Rama 9 · Frontend web

Vocabulario de `web/`: el marco (Astro y sus bibliotecas), las rutas del sitio, cómo se guarda el estado en el navegador, cómo se dibujan mapas y gráficos, la accesibilidad, el service worker y las pruebas.

**Para quién es.** Para quien abre un componente `.astro`, un módulo de `web/src/lib/`, una prueba de Playwright o el `sw.js` y necesita saber qué significan `epi:filters-changed`, «región viva», «tabla alternativa», «network-first» o «sello de frescura».

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris, con los nombres exactos), **Dónde** (archivo o ADR) y **Ojo** (errores frecuentes). Las expansiones de siglas que el repositorio no da se marcan como «de uso general».

**Ramas vecinas.** El significado de lo que se muestra (Iv, percentil, alertas) está en [`05-modulos-descriptivos-y-alertas.md`](05-modulos-descriptivos-y-alertas.md); los endpoints que consume, en [`06-backend-y-api.md`](06-backend-y-api.md); el despliegue del sitio estático, en [`08-infraestructura-despliegue-y-repositorio.md`](08-infraestructura-despliegue-y-repositorio.md). El vocabulario específico del repositorio vitrina está en `aetheris-nitor/docs/glosario/`.

<!-- INDICE:INICIO -->

## Índice alfabético (72 entradas)

- **A** — [Accesibilidad web (WCAG, AA)](#accesibilidad-web-wcag-aa) · [Anillo de foco doble](#anillo-de-foco-doble) · [Astro](#astro) · [astro-icon (Tabler y Simple Icons)](#astro-icon-tabler-y-simple-icons) · [Atributos data- de prueba](#atributos-data--de-prueba)
- **B** — [Biblioteca](#biblioteca)
- **C** — [Capa del mapa](#capa-del-mapa) · [Cargadores y barra de actividad](#cargadores-y-barra-de-actividad) · [Chroma.js y ColorBrewer](#chromajs-y-colorbrewer) · [--color-live (coral)](#--color-live-coral) · [Compartir una alerta](#compartir-una-alerta) · [Curva epidémica](#curva-epidémica)
- **D** — [Demos (?demo, ?lento, ?limpio)](#demos-demo-lento-limpio) · [Departamento recordado](#departamento-recordado) · [_desde_cache y X-EPI-Cache](#_desde_cache-y-x-epi-cache)
- **E** — [escapeHtml y XSS](#escapehtml-y-xss) · [ESLint, Prettier y scripts](#eslint-prettier-y-scripts) · [Estado por URL](#estado-por-url) · [Estados asíncronos (estado-async.ts)](#estados-asíncronos-estado-asyncts) · [Eventos epi:](#eventos-epi) · [Exportar gráfico (SVG, PNG y CSV)](#exportar-gráfico-svg-png-y-csv)
- **F** — [Ficha departamental](#ficha-departamental) · [Ficha imprimible](#ficha-imprimible) · [Filtros del análisis (FiltrosAnalisis)](#filtros-del-análisis-filtrosanalisis) · [--font-display (Fraunces)](#--font-display-fraunces) · [Fonts API de Astro](#fonts-api-de-astro) · [Formato de semana (SE01)](#formato-de-semana-se01)
- **G** — [Glosario de la interfaz y ayuda de término](#glosario-de-la-interfaz-y-ayuda-de-término)
- **H** — [Heatmap y matriz](#heatmap-y-matriz)
- **I** — [ignoreVary](#ignorevary) · [Impresión](#impresión) · [Incrustación (/incrustar)](#incrustación-incrustar)
- **L** — [Leaflet](#leaflet) · [Leyenda de rampa (LeyendaRampa)](#leyenda-de-rampa-leyendarampa) · [localStorage](#localstorage)
- **M** — [Manifiesto web (manifest.webmanifest)](#manifiesto-web-manifestwebmanifest) · [Mapa del sitio](#mapa-del-sitio) · [Marcas de gráfico accesibles](#marcas-de-gráfico-accesibles) · [modoMinsal (semana, ytd, historico)](#modominsal-semana-ytd-historico) · [Móvil (375 px y 768 px)](#móvil-375-px-y-768-px) · [Movimiento (movimiento.ts)](#movimiento-movimientots)
- **N** — [Network-first y stale-while-revalidate](#network-first-y-stale-while-revalidate) · [noindex, sitemap y robots.txt](#noindex-sitemap-y-robotstxt)
- **O** — [Observable Plot](#observable-plot)
- **P** — [Página de estado (/estado)](#página-de-estado-estado) · [Playwright y axe](#playwright-y-axe) · [pnpm y Corepack](#pnpm-y-corepack) · [Precache dirigido por la página](#precache-dirigido-por-la-página) · [Prefetch](#prefetch) · [Primitivas de análisis](#primitivas-de-análisis) · [Pruebas unitarias del frontend](#pruebas-unitarias-del-frontend) · [PUBLIC_API_URL y API_BASE](#public_api_url-y-api_base)
- **R** — [Rampa de color y paleta cualitativa](#rampa-de-color-y-paleta-cualitativa) · [Redirección /panel a /dengue](#redirección-panel-a-dengue) · [Reducción de movimiento](#reducción-de-movimiento) · [Región viva (role="status", aria-live, aria-busy)](#región-viva-rolestatus-aria-live-aria-busy)
- **S** — [security.txt y contacto](#securitytxt-y-contacto) · [Sello de frescura](#sello-de-frescura) · [Service worker (sw.js)](#service-worker-swjs) · [Shell y SHELL_MINIMO](#shell-y-shell_minimo) · [Sin cookies ni analítica](#sin-cookies-ni-analítica) · [Skeleton](#skeleton) · [sr-only](#sr-only)
- **T** — [Tabla alternativa](#tabla-alternativa) · [Tailwind CSS 4](#tailwind-css-4) · [Tema oscuro (data-theme)](#tema-oscuro-data-theme) · [Tokens de diseño](#tokens-de-diseño) · [TypeScript y astro check](#typescript-y-astro-check)
- **U** — [Última semana y franja «lo actual primero»](#última-semana-y-franja-lo-actual-primero)
- **V** — [VERSION del service worker](#version-del-service-worker) · [Vista o preset del workspace](#vista-o-preset-del-workspace)
- **W** — [Workspace analítico](#workspace-analítico)

<!-- INDICE:FIN -->

## 1. Marco y herramientas

### Astro

**Qué es.** Marco web que genera sitios estáticos y ejecuta JavaScript solo donde hace falta (de uso general).

**En el proyecto.** El sitio es un **sitio estático** (`astro build` produce `dist/`) con componentes `.astro` y un `<script>` de cliente cuando hace falta interactividad. **No hay React, Vue ni otro marco de componentes** (`AGENTS.md` §10): «un componente `.astro` más un `<script>` ya resuelve "solo en el navegador" sin sumar un framework de UI nuevo». `package.json` declara `astro ^7.2.8` y la versión `0.5.0` del paquete `aetheris-web`.

**Ojo.** El `README` todavía dice «Astro 4»: ver [Notas de vigencia](README.md#notas-de-vigencia).

### TypeScript y `astro check`

**Qué es.** TypeScript añade tipos a JavaScript; `astro check` valida tipos de TypeScript y de los componentes Astro.

**En el proyecto.** `pnpm build` ejecuta `astro check && astro build`, así que un error de tipos rompe el build. Los módulos de `src/lib/` están escritos en TypeScript y tienen pruebas unitarias.

### Tailwind CSS 4

**Qué es.** Marco de CSS por clases utilitarias (de uso general).

**En el proyecto.** Versión 4, integrada como **plugin de Vite** (`@tailwindcss/vite`); la integración anterior `@astrojs/tailwind` no soporta Tailwind 4 ni Astro 6 o superior. Los tokens de diseño se exponen además como utilidades (`bg-surface`, `text-ink`).

### Leaflet

**Qué es.** Biblioteca de mapas interactivos.

**En el proyecto.** Dibuja los mapas de departamentos (`MapaDepartamentos.astro`, `MapaIRA.astro`). Necesita el DOM del navegador, así que todo el trabajo con `L.*` vive en el `<script>` de cliente. Las **teselas de fondo son de OpenStreetMap** y las pide el navegador directamente. El mapa queda fuera de la exportación de gráficos porque los tiles no permiten CORS y el lienzo se contaminaría.

### Observable Plot

**Qué es.** Biblioteca para gráficos estadísticos que genera SVG.

**En el proyecto.** Versión `^0.6.17`. Dibuja las curvas, matrices y paneles del workspace. Los módulos de tema (`plot-tema.ts`) importan solo el **tipo** de Plot para no arrastrar ~391 KB de Plot y d3 al grafo inicial de `/dengue`; los componentes lo cargan con `await import`.

### Chroma.js y ColorBrewer

**Qué es.** Chroma.js calcula escalas y mezclas de color; ColorBrewer es un conjunto de paletas cartográficas.

**En el proyecto.** `colores.ts` usa `chroma.scale(...).mode('lab')` para las rampas y `ColorBrewer` como base. La política visual separa la clasificación de valores de la asignación de colores, exige una leyenda equivalente y evita el verde-amarillo-rojo sin validación de accesibilidad.

### `astro-icon` (Tabler y Simple Icons)

**Qué es.** Integración que inserta iconos SVG en línea en el build.

**En el proyecto.** Se usan los conjuntos **Tabler** (MIT) y **Simple Icons** (CC0, logotipos) a través de `Icono.astro`, siempre con trazo de 24 px a grosor 2. Sin `etiqueta`, el icono es decorativo y va oculto para lectores de pantalla; con `etiqueta`, se anuncia.

### Fonts API de Astro

**Qué es.** Mecanismo de Astro que auto-hospeda las fuentes en el build.

**En el proyecto.** Tres familias (`astro.config.mjs`): **Inter** (pesos 400, 500, 600 y 700), **IBM Plex Mono** (400, para etiquetas de ejes, valores y código) y **Fraunces** (600 y 700, con `opsz` 144, «voz de titular»). Sin preconnect a Google ni hojas que bloqueen el render; no se usa `preload` a propósito (#87).

### pnpm y Corepack

**Qué es.** pnpm es el gestor de paquetes; Corepack administra su versión.

**En el proyecto.** `packageManager: pnpm@9.15.9`. Se usa `pnpm`, **no `npm`**. En el build de Render, `pnpm install --frozen-lockfile && pnpm build`. Un `overrides` fija `fast-uri ^3.1.7`.

### ESLint, Prettier y scripts

**Qué es.** ESLint revisa reglas y calidad estática; Prettier fija el formato.

**En el proyecto.** Scripts: `dev`, `build`, `preview`, `check`, `lint`, `format`, `format:check`, `test:e2e` y `test:unit`. Sus responsabilidades no se solapan: Prettier es formato, ESLint es calidad estática y `astro check` son los tipos.

### Redirección `/panel` a `/dengue`

**Qué es.** Regla `redirects` de Astro.

**En el proyecto.** `/panel` se renombró a `/dengue` (#70); la ruta vieja estuvo en producción (marcadores, enlaces compartidos, indexación) y el redirect la preserva. En un build estático Astro genera una página de redirección por cada entrada.

### Prefetch

**Qué es.** Precargar el HTML de un enlace antes de que se pulse.

**En el proyecto.** `prefetch: { prefetchAll: true }`: precarga al pasar el cursor o al entrar en pantalla, para navegación casi instantánea entre las vistas.

### `PUBLIC_API_URL` y `API_BASE`

**Qué es.** La URL de la API que consume el navegador.

**En el proyecto.** Variable `PUBLIC_API_URL` (por defecto `http://localhost:8000`), **embebida en el bundle en build-time**; los componentes la leen como `API_BASE`. El navegador siempre resuelve la API por esa URL pública, no por el nombre interno de la red de Docker.

## 2. Rutas y páginas

### Mapa del sitio

**Qué es.** Las rutas de `web/src/pages/`.

**En el proyecto.**

| Ruta | Qué es |
|---|---|
| `/` | Portada: el mapa de los 14 departamentos como héroe, cada silueta un enlace a su ficha |
| `/alertas`, `/alertas/archivo`, `/alertas/nueva` | Cara de **consulta**: alertas vigentes, archivo y formulario de alta (`noindex`, sin enlace en la navegación) |
| `/analisis` | Índice de las herramientas descriptivas (solo enruta) |
| `/dengue`, `/respiratorio` | Cara de **análisis**: dengue (con el workspace y la pestaña de predicción) y observatorio respiratorio |
| `/departamento/[codigo]` | Ficha departamental: alertas, dengue, clima y curvas respiratorias de un departamento |
| `/analisis/ficha/[departamento]` | Ficha imprimible |
| `/biblioteca`, `/biblioteca/[...slug]` | Documentos propios (colección de Astro) |
| `/estado` | Estado del servicio |
| `/acerca-de`, `/contacto`, `/sugerencias` | Páginas de texto |
| `/legal`, `/legal/privacidad`, `/legal/terminos`, `/legal/aviso-legal` | Documentos legales |
| `/demos`, `/demos/nowcast` | Recorridos animados (`noindex`, fuera del sitemap y de la navegación) |
| `/incrustar/curva-nacional`, `/incrustar/ultima-semana` | Vistas para incrustar en un `<iframe>` |
| `/404` | Página de error (`noindex`; se emite como `dist/404.html`) |

Ninguna vista se titula «hoy» ni «esta semana»: la ventana cargada llega hasta 2023 y `regiones.nivel_admin = 2` sigue reservado.

### Ficha departamental

**Qué es.** Página `/departamento/[codigo]` que reúne, para un departamento, alertas vigentes, canal endémico de dengue, clima y curvas de IRA.

**En el proyecto.** Se genera **estáticamente** para cada uno de los 14 departamentos (`getStaticPaths`). Cada serie se compara con la historia del propio departamento. Solo muestra las alertas que aplican al departamento ([alcance territorial](05-modulos-descriptivos-y-alertas.md#alcance-territorial-departamentos)). No tiene mapa.

### Ficha imprimible

**Qué es.** Versión de la ficha de un departamento pensada para el papel.

**En el proyecto.** `/analisis/ficha/[departamento]`, con una barra superior de navegación y controles que se **oculta en impresión** (`@media print`). Pruebas: `fichas-departamentales.spec.ts` e `impresion-dengue.spec.ts`.

### Página de estado (`/estado`)

**Qué es.** Página que informa si el servicio responde.

**En el proyecto.** Muestra dos componentes: el **frontend** (siempre «Operativo») y el **backend**, para el cual el navegador hace una petición de diagnóstico a `GET /health`.

### Biblioteca

**Qué es.** Sección `/biblioteca` con los documentos propios del proyecto para un lector externo.

**En el proyecto.** Es una **colección de contenido de Astro** que lee los `.md` de `docs/biblioteca/` (`*.md`, con frontmatter `titulo`, `descripcion`, `orden`, `categoria`). Hay cinco documentos y el repositorio vitrina tiene su propia copia; `content.config.ts` prueba primero la copia propia del repo y cae a la del monorepo. Sin esa lógica, el repo suelto compilaría sin error pero dejaría la colección vacía y las páginas responderían 404 en producción. Las páginas legales, `contacto` y `acerca-de` **no** pasan por la colección: usan `DocumentoTexto.astro`.

**Ojo.** Estos glosarios viven en `docs/glosario/` y **no** en `docs/biblioteca/`, precisamente para no entrar a esa colección.

### `noindex`, sitemap y `robots.txt`

**Qué es.** Formas de dejar una página fuera de los buscadores (de uso general).

**En el proyecto.** `/alertas/nueva` y la 404 llevan `<meta name="robots" content="noindex">`; el `sitemap` (`@astrojs/sitemap`) excluye además `/panel`, `/demos` y `/incrustar`. `robots.txt` no lista `/alertas/nueva` a propósito, porque un `Disallow` la anunciaría. `site` es `https://epi-aetheris.dev`, de donde salen `canonical`, `og:url` y el sitemap.

### Demos (`?demo`, `?lento`, `?limpio`)

**Qué es.** Modo presentación para enseñar o grabar el video de la demo.

**En el proyecto.** `/dengue?demo=1` (o `?demo=lento`) activa la secuencia; en `/demos/nowcast`, `?lento` da ritmo 1,6× y `?limpio` oculta cabecera, pie y encabezado. En `/dengue` el panel de predicción vive dentro de un tabpanel oculto, así que hay que abrirlo con `?demo&t=prediccion`.

### Incrustación (`/incrustar`)

**Qué es.** Vistas mínimas para insertar un gráfico en otra página mediante un `<iframe>`.

**En el proyecto.** `LayoutIncrustado.astro` no lleva navegación ni pie, va fuera del índice de buscadores y muestra la atribución; los enlaces internos se reescriben para abrir el sitio completo en otra pestaña. `BotonIncrustar.astro` copia el `<iframe>` que genera `codigoIncrustacion` (`width="100%"`, `loading="lazy"`, `style="border:0"`), con atributos escapados.

### `security.txt` y contacto

**Qué es.** `public/.well-known/security.txt` publica cómo avisar de una vulnerabilidad.

**En el proyecto.** `/contacto` no tiene formulario (habilitarlo obligaría a guardar texto libre de terceros, lo que la política de privacidad dice que el sitio no hace). El aviso de vulnerabilidades va por los avisos de seguridad **privados** de GitHub, y `security.txt` ofrece el correo como alternativa. `/sugerencias` enruta a **GitHub Issues** por el mismo motivo.

## 3. Estado del cliente

### Estado por URL

**Qué es.** Guardar los filtros en los parámetros de la dirección para que un enlace compartido abra la misma vista.

**En el proyecto.** El workspace de análisis lee y escribe `year`, `week`, `fromWeek`, `toWeek`, `serie` (`probable` o `confirmado`), `dept` (código ISO), `compare` (lista de departamentos) y `minsal` (`semana`, `ytd` o `historico`). La respiratoria tiene su propio estado. Un enlace compartido se comporta igual para cualquiera: no hay estado oculto de «modo».

### Eventos `epi:*`

**Qué es.** Eventos personalizados del navegador (`CustomEvent`) con el prefijo `epi:` que comunican los paneles entre sí.

**En el proyecto.**

| Evento | Quién lo emite |
|---|---|
| `epi:filters-changed` | `analisis-state.ts`, cuando cambian los filtros del workspace de dengue |
| `epi:analysis-layout-changed` | `analisis-layout-state.ts`, cuando cambian la vista, los paneles, los tamaños, el foco o el zoom |
| `epi:respiratorio-changed` | `respiratorio-state.ts`, cuando cambian los filtros de `/respiratorio` |

Cada módulo expone `obtener…`, `actualizar…` y `suscribir…`; los paneles se suscriben en lugar de conocerse entre sí.

### Filtros del análisis (`FiltrosAnalisis`)

**Qué es.** El estado de los filtros de `/dengue`.

**En el proyecto.** `anio` (por defecto 2023), `semana` (1), `semanaDesde` (1), `semanaHasta` (53), `serie` (`probable`), `departamento` (`null`), `comparar` (hasta **4** departamentos, sin repetidos) y `modoMinsal`. Cada cambio pasa por una **normalización** que lo deja siempre válido (semana entre 1 y 53, `desde ≤ hasta`, año disponible, serie válida). Los años pintables de M1 y M2 llegan hasta el año en curso (`aniosClimaPresentacion`), pero el dataset de dengue sigue siendo 2018, 2019, 2021, 2022 y 2023 ([ADR 0018](../adr/0018-extension-capa-climatica-presente.md)).

### `modoMinsal` (`semana`, `ytd`, `historico`)

**Qué es.** Cómo agrega el mapa el volumen de casos de MINSAL.

**En el proyecto.** `semana` muestra una semana; `ytd` (de uso general, *year to date*) acumula desde el inicio del año hasta esa semana; `historico` acumula toda la ventana cargada.

### Workspace analítico

**Qué es.** La sección de `/dengue` donde se combinan paneles de análisis con un mismo conjunto de filtros.

**En el proyecto.** Tiene diez **paneles** (`PANELES_ANALITICOS`): `mapa` (Mapa departamental), `presion` (Presión por semana), `serie` (Serie del departamento), `canal` (Canal endémico), `temporadas` (Comparación de temporadas), `departamentos` (Comparación de departamentos), `calendario` (Calendario epidémico), `clima` (Clima × presión), `disponibilidad` (Disponibilidad de datos) y `calidad` (Perfil de calidad). Cada panel tiene un tamaño (`pequeno`, `mediano`, `grande`); uno puede estar **en foco** y el **zoom temporal** vale 100, 150 o 200. Componentes: `PanelAnalisis.astro`, `PanelWorkspace.astro`, `ToolbarAnalisis.astro`, `SelectorPaneles.astro`, `FiltrosAnalisis.astro`.

### Vista o preset del workspace

**Qué es.** Combinación predefinida de paneles y tamaños.

**En el proyecto.** Cinco (`VistaAnalisis`): **general** (mapa, presión, temporadas y departamentos), **territorial** (mapa, presión y departamentos), **temporal** (serie, canal, temporadas y calendario), **clima** (mapa y dispersión de anomalía contra presión) y **calidad** (disponibilidad y auditoría de procedencia). Aplicar una vista reemplaza los paneles visibles y sus tamaños y quita el foco; «restablecer» vuelve a `general`.

### `localStorage`

**Qué es.** Almacenamiento persistente del navegador (de uso general).

**En el proyecto.** Solo para conveniencias de cada persona, siempre dentro de `try/catch` porque puede fallar (modo privado, almacenamiento bloqueado): `epi:departamento` (departamento recordado), `epi-aetheris:alertas-vistas` (ids de alertas ya vistas, para marcar las «Nueva»), la elección de tema, y el token de escritura de alertas **solo si el operador lo elige explícitamente**. La primera visita no marca nada como nueva, porque sin referencia previa «nueva» no significa nada.

### Departamento recordado

**Qué es.** El departamento que la persona eligió recordar.

**En el proyecto.** `leerDepartamentoRecordado` devuelve `null` si no hay o no es válido; `guardarDepartamentoRecordado` devuelve `false` si el navegador no deja.

## 4. Visualización

### Capa del mapa

**Qué es.** Lo que colorea el mapa departamental.

**En el proyecto.** Un selector de capas descriptivas: volumen de casos MINSAL (por defecto, desacumulados; probable o confirmado), M1 (`Iv`), M2 (`anomaly_sigma`), M3 (dos series de presión) e integridad de la vigilancia (`confianza`). **Ninguna es salida del clasificador de riesgo** y ninguna pinta un nivel de riesgo departamental.

### Rampa de color y paleta cualitativa

**Qué es.** Una rampa ordena una magnitud continua; una paleta cualitativa distingue categorías.

**En el proyecto.** `RAMPA_PRESION` (azules) y `RAMPA_CASOS` (púrpuras) son secuenciales basadas en ColorBrewer y **no representan niveles de alarma**. `PALETA_CUALITATIVA` (ColorBrewer Dark2) se eligió por ser distinguible bajo protanopia, deuteranopia y tritanopia y por su contraste sobre fondos claros (#129). `COLOR_SIN_DATO` es `#e4e4e7` y `COLOR_DATO_DISPONIBLE`, `#256abf`. Un color distinto para «sin dato» evita confundir un hueco con un valor bajo.

### Leyenda de rampa (`LeyendaRampa`)

**Qué es.** La leyenda que explica una escala de color.

**En el proyecto.** Es obligatorio que exista una leyenda equivalente para cada rampa, y que diga que la escala ordena magnitudes y no umbrales epidemiológicos.

### Heatmap y matriz

**Qué es.** Cuadrícula de celdas coloreadas por valor.

**En el proyecto.** `HeatmapDepartamentos` (presión por departamento y semana) y `HeatmapNeumonias` (conteo notificado por departamento y semana). Una celda sin dato es un **hueco, nunca un cero**. Los márgenes están en `MARGENES.matriz` y `MARGENES.traza`.

### Curva epidémica

**Qué es.** Gráfico de casos por semana.

**En el proyecto.** `CurvaEpidemicaNacional` consume `GET /api/casos-nacional`: total de OpenDengue y, desde 2025, sospechosos del tablero, con la fuente marcada por tramo. No es clasificación de riesgo. `CurvaRespiratoriaNacional` hace lo propio con IRA y neumonías del tablero, con una línea por año.

### Última semana y franja «lo actual primero»

**Qué es.** `UltimaSemanaDengue.astro`: la franja de `/dengue` con la última semana publicada por el tablero.

**En el proyecto.** Muestra la última semana, **su par del año anterior** y la mediana de la semana siguiente de la predicción; `resumirUltimaSemana` **solo compara tablero contra tablero** (el total de OpenDengue tiene otra forma de suavizado) y no interpola semanas no publicadas. La franja se pinta al instante con una **copia de la serie tomada al compilar** y luego se actualiza desde la API; si el backend no responde durante el build, el sitio compila igual.

### Formato de semana (`SE01`)

**Qué es.** Convención de rotular semanas.

**En el proyecto.** `ejeSemana` rotula los ticks como `SE` más dos dígitos (`SE07`) y el título del eje es «Semana epidemiológica». Los números se formatean con `Intl.NumberFormat('es-SV')`.

### Tabla alternativa

**Qué es.** Tabla de los mismos datos de una gráfica, dentro de un `<details>`, como alternativa textual.

**En el proyecto.** La clase `TablaAlternativa` la **construye de forma perezosa** cuando se abre el `<details>` y marca sus datos como **caducados** cuando el panel cambia, de modo que solo se reconstruye si está abierta. Límite de 500 filas por defecto. Todo lo que se interpola en `innerHTML` pasa por `escapeHtml`.

### Exportar gráfico (SVG, PNG y CSV)

**Qué es.** Descargar un gráfico o sus datos.

**En el proyecto.** `exportar-grafico.ts` (fase F6.3) exporta un gráfico de Plot como SVG o PNG con un **pie** de tres o cuatro líneas: título, filtros activos, «Fuente: …» y «Generado el AAAA-MM-DD desde EPI-Aetheris». Un SVG descargado pierde las variables CSS, así que se resuelven con `getComputedStyle` antes de guardar. `nombreArchivoSeguro` quita tildes y caracteres que un sistema de archivos rechace. `analisis-export.ts` exporta el dataset analítico a **CSV** (con escape de comillas y saltos de línea); el mapa se exporta solo como tabla y CSV.

### Sello de frescura

**Qué es.** Indicador de cuán reciente es el dato que se muestra.

**En el proyecto.** Hay dos. El de **alertas** dice «sin conexión — mostrando lo último guardado» cuando la respuesta salió del cache. El de **series** (`frescura.ts`) muestra la última semana con dato de cada serie («SE07 de 2023») y su rezago («al día», «1 semana de rezago», «N semanas de rezago»), a partir de M4.

### Glosario de la interfaz y ayuda de término

**Qué es.** Definiciones breves que aparecen junto a un término.

**En el proyecto.** `AyudaTermino.astro` muestra un botón «?» que abre un **popover** (`popover="auto"`) con la definición de `lib/glosario.ts` y un enlace «Leer más en la Biblioteca». La clave debe existir en el glosario o el build falla. El área táctil es de 44 px con un círculo visible de 20 px. Las doce entradas están en `aetheris-nitor/docs/glosario/01-vocabulario-de-la-interfaz.md`.

### Estados asíncronos (`estado-async.ts`)

**Qué es.** Ayudas para los contenedores que reciben datos después de un `fetch`.

**En el proyecto.** Distingue dos desenlaces claros: **«sin dato para esta selección»** (neutro y esperado, parte del mensaje sobre huecos de cobertura) y **«no se pudo contactar la fuente»** (con un botón «Reintentar», sin jerga de desarrollador). Además, `esNoDisponible` reconoce el contrato `{disponible: false, motivo}` del backend ([Contrato `disponible: false`](06-backend-y-api.md#contrato-disponible-false)), que no es un error de red.

### Cargadores y barra de actividad

**Qué es.** Indicadores de espera.

**En el proyecto.** `CargadorCurva` (el «cometa» recorre el trazo; propuesta 2 del sistema de diseño), `CargadorPuntos` (puntos en cascada para esperas en línea; propuesta 4) y `BarraActividad` (barra indeterminada; propuesta 5), que señala las peticiones en vuelo tras `epi:filters-changed` (no es navegación: no hay enrutador de cliente). Los cargadores son **decoración**: quien anuncia el estado es el contenedor anfitrión con `role="status"` y `aria-busy`.

### Movimiento (`movimiento.ts`)

**Qué es.** Animaciones de entrada por scroll y cifras que cuentan hacia arriba.

**En el proyecto.** Solo si hay JavaScript, `IntersectionObserver` y la persona **no pidió reducir el movimiento** se marca `<html data-animar>` y los bloques `.aparece` pasan a ocultos hasta entrar en pantalla; las cifras `[data-cifra]` cuentan de 0 al valor final en 1,4 s. Sin ese atributo la página se ve completa: el HTML ya está en su estado final.

### Skeleton

**Qué es.** Bloque gris de relleno mientras llega un dato (de uso general).

**En el proyecto.** Clase `.skeleton` de `global.css`, usada por ejemplo en `MetricasModelo.astro` con `role="status"` y `aria-busy`.

## 5. Accesibilidad

### Accesibilidad web (WCAG, AA)

**Qué es.** Las pautas WCAG (Web Content Accessibility Guidelines, de uso general) definen niveles A, AA y AAA.

**En el proyecto.** Se apunta a **AA o mejor**: todos los pares de fondo y texto de los tokens cumplen AA. La campaña sistemática de 2026-09-13 (v0.5.0) no fue cosmética: landmarks, *skip link*, foco visible por teclado, marcado de campos obligatorios, `aria-haspopup` y restauración de foco en menús. Axe detecta lo automatizable, pero no reemplaza la revisión manual de teclado, foco, significado sin depender del color y lector de pantalla.

### Región viva (`role="status"`, `aria-live`, `aria-busy`)

**Qué es.** Una región que un lector de pantalla anuncia cuando cambia (de uso general).

**En el proyecto.** Los contenedores que reciben datos de forma asíncrona son regiones vivas. `BarraActividad` **no oculta** su región con `hidden` (mostrar una región no cambia su contenido y la mayoría de los lectores no anunciarían nada): vacía y rellena el texto, y `data-activa` gobierna lo visual. `marcarRegionEstado` no pisa un `role` o `aria-live` que ya venga del HTML.

### Marcas de gráfico accesibles

**Qué es.** Hacer que los elementos de un gráfico se puedan usar con teclado.

**En el proyecto.** `vincularMarcasPlot` asigna a cada marca SVG `tabindex="0"`, `role="button"` y un `aria-label`, y activa con clic, Enter o espacio.

### Tema oscuro (`data-theme`)

**Qué es.** Esquema de colores oscuro.

**En el proyecto.** Sigue al sistema (`prefers-color-scheme: dark`) salvo que la persona haya elegido uno con el selector del encabezado (`data-theme` en `<html>`, guardado en `localStorage`). La cabecera del sitio es fija en ambos temas porque lleva texto y logotipo claros.

### Reducción de movimiento

**Qué es.** Preferencia del sistema `prefers-reduced-motion: reduce`.

**En el proyecto.** Desactiva las animaciones de entrada y de cifras ([Movimiento](#movimiento-movimientots)).

### Impresión

**Qué es.** Estilos `@media print` y la clase `print:hidden` de Tailwind.

**En el proyecto.** `window.print()` con `@media print` produce el cartel para sala de espera de una alerta y la ficha imprimible, sin dependencia de PDF.

## 6. Tokens y diseño

### Tokens de diseño

**Qué es.** Variables CSS con los valores de color, tipografía y sombra del sistema visual (`web/src/styles/tokens.css`).

**En el proyecto.** Paleta fijada por la coordinación (2026-08-21): texto `#040316` (`--color-ink`), fondo `#f0f0f0` (`--color-bg`), primario `#183e39` (`--color-accent`, botones activos, enlaces y cabecera), secundario `#dddbff` (lavanda, chips y estados suaves) y acento `#011e1e` (`--color-deep`, footer y secciones de mayor contraste). Cada fondo tiene su token de texto: **se usa siempre el par**. Los nombres de variable no cambian; solo se agregan tokens.

### `--color-live` (coral)

**Qué es.** El coral `#ff5a45` del logotipo.

**En el proyecto.** Tiene **un solo papel**, «esto es de ahora»: la tira de alertas vigentes y los marcadores de estado en curso. Nunca es decorativo ni va en texto largo. No es un token de propósito general para botones.

### Anillo de foco doble

**Qué es.** El indicador de foco de teclado.

**En el proyecto.** `--focus-ring` es lavanda fija (contraste mayor de 12:1 sobre `#011e1e`), pero sobre el fondo claro su contraste es bajo, así que `global.css` la combina con un `box-shadow` oscuro exterior (anillo doble).

### `--font-display` (Fraunces)

**Qué es.** La voz de titular.

**En el proyecto.** **Solo** el H1 de página y los dos H2 de sección de la landing; nunca en subtítulos de tarjeta ni en la interfaz funcional. Inter es el cuerpo y IBM Plex Mono, las etiquetas de ejes y los valores.

### Primitivas de análisis

**Qué es.** Tokens del rediseño de la sección de análisis (2026-09).

**En el proyecto.** `--color-seleccion`, `--trazo-seleccion` (2 px), `--radio-matriz` (6 px), `--radio-traza` (12 px) y `--filete-traza` (2 px). `card-elevated` es la clase de tarjeta con sombra (`--shadow-card`).

### `sr-only`

**Qué es.** Clase de Tailwind que oculta un texto visualmente pero lo deja para lectores de pantalla (de uso general).

**En el proyecto.** Se usa, por ejemplo, para los anuncios de «Enlace copiado» al compartir una alerta.

## 7. Seguridad del frontend

### `escapeHtml` y XSS

**Qué es.** XSS (*cross-site scripting*, de uso general) es inyectar código en una página; `escapeHtml` convierte `& < > " '` en entidades.

**En el proyecto.** Es la **regla de la casa**: todo lo que se interpola en `innerHTML` pasa por `escapeHtml`, porque los valores vienen de la API (el nombre de un departamento, un `aviso`, una `nota`). Un hallazgo del 2026-08-27 encontró que `MetricasModelo.astro` construía HTML con campos de la API sin escapar. Los textos de alertas se renderizan con `textContent` y `renderTextoAccionable` (párrafos y listas con `- `), nunca como HTML.

**Dónde.** `web/src/utils/security.ts`, `vista-alertas.ts`.

### Compartir una alerta

**Qué es.** Enlace directo a una alerta.

**En el proyecto.** `navigator.share` donde exista (móvil) y, si no, copia el enlace al portapapeles («Enlace copiado» o «No se pudo copiar»). El enlace apunta al ancla `#alerta-<id>` de `/alertas` (con `?tipo=`).

### Sin cookies ni analítica

**Qué es.** Característica del sitio declarada en la política de privacidad.

**En el proyecto.** No hay cookies ni analítica; los terceros que reciben la IP son Render y OpenStreetMap (por las teselas). Ver `aetheris-nitor/docs/glosario/03-legal-privacidad-y-publicacion.md`.

## 8. Service worker y PWA

### Service worker (`sw.js`)

**Qué es.** Script que el navegador ejecuta en segundo plano y que intercepta las peticiones (de uso general).

**En el proyecto.** Escrito a mano, **sin dependencias** (~90 líneas; añadir una cadena de build de PWA no valía la pena). Existe para que el personal de salud en zona rural abra `/alertas` donde hay señal y la use después donde no la hay ([ADR 0014](../adr/0014-enfoque-dual-panorama-analisis.md)). Dos cachés: `epi-shell-v1` y `epi-api-v1`.

### Network-first y stale-while-revalidate

**Qué es.** Dos estrategias de caché.

**En el proyecto.** **Network-first** para `GET /api/alertas`: la red siempre gana y el cache es último recurso, porque una alerta que el equipo ya apagó **tiene consecuencia clínica**. **Stale-while-revalidate** para el shell (HTML, CSS, JS, fuentes, logos): da una pantalla inmediata y actualiza en segundo plano, porque un shell viejo no tiene consecuencia clínica. No se debe cambiar a cache-first ni quitar el sello.

### Shell y `SHELL_MINIMO`

**Qué es.** El shell es el armazón de la aplicación (HTML, CSS, JS) sin sus datos.

**En el proyecto.** `SHELL_MINIMO = ['/', '/alertas']`: las rutas mínimas para que `/alertas` abra sin red; el resto entra al cache a medida que se visita. Ni el archivo ni el formulario de creación se precachean.

### `VERSION` del service worker

**Qué es.** Constante que nombra las cachés (`v1`).

**En el proyecto.** **Al desplegar hay que subir `VERSION`** para invalidar el shell viejo; el `activate` borra las cachés con otro nombre.

### `_desde_cache` y `X-EPI-Cache`

**Qué es.** Las dos marcas que el service worker añade a una respuesta servida desde el cache.

**En el proyecto.** `_desde_cache: true` va **en el cuerpo JSON** y `X-EPI-Cache: sw` en una cabecera. La señal fiable es la del cuerpo: como la API vive en otro origen, el navegador filtra por CORS las cabeceras propias (comprobado, ni siquiera con `Access-Control-Expose-Headers`). `_desde_cache` es un marcador de transporte, no un campo del contrato de `/api/alertas`: **el backend nunca lo emite**.

### `ignoreVary`

**Qué es.** Opción de `cache.match` que ignora la cabecera `Vary`.

**En el proyecto.** Sin ella, el servidor estático responde con `Vary: Accept-Encoding` y la petición guardada no coincide con la del navegador: el recurso queda guardado pero nunca se sirve, y la recarga sin conexión trae el HTML sin scripts.

### Precache dirigido por la página

**Qué es.** La página le manda al service worker la lista de recursos que ya cargó.

**En el proyecto.** En la primera visita el service worker todavía no controlaba el documento, así que sus subrecursos (`/_astro/*.js`, CSS, fuentes) nunca pasaron por su `fetch` y no quedaron en el cache. La página envía `performance.getEntriesByType` en un mensaje `precache` (con el endpoint de alertas en `datos.api`).

### Manifiesto web (`manifest.webmanifest`)

**Qué es.** Archivo que describe la aplicación instalable (PWA).

**En el proyecto.** `name` y `short_name` «EPI-Aetheris», `lang: es`, `start_url: /alertas`, `scope: /`, `display: standalone`, `theme_color: #2a2a72` y cuatro iconos (SVG, 192, 512 y 512 *maskable*). La descripción aclara que **no es un diagnóstico ni un pronóstico**.

## 9. Pruebas del frontend

### Playwright y axe

**Qué es.** Playwright automatiza un navegador; `@axe-core/playwright` añade comprobaciones de accesibilidad.

**En el proyecto.** `playwright.config.ts`: directorio `tests/e2e`, **un solo worker** (el servidor de Vite reoptimiza dependencias de forma perezosa y, con varios workers pidiendo `/dengue` y `/respiratorio` a la vez, Leaflet y Plot entran en una carrera que devuelve 504), `retries: 2` solo en CI, tiempo de espera de 45 s y proyecto `chromium`. La suite completa tarda unos 30 s en serie. Cubre alertas, análisis, biblioteca, canal endémico, contraste de la predicción, ficha departamental, enfoque dual, estado, exportación, glosario, impresión, incrustación, legal, móvil, respiratorio, tema oscuro y última semana. Las pruebas deben poder interceptar la API con fixtures para no exigir FastAPI ni PostgreSQL.

### Pruebas unitarias del frontend

**Qué es.** Pruebas de los módulos de `src/lib/` sin navegador.

**En el proyecto.** `node --experimental-strip-types --test "tests/unit/**/*.test.ts"`. Cubren `alcance-alertas`, `canal-endemico`, `exportar-grafico`, `ficha-departamental`, `frescura`, `incrustar`, `respiratorio-state` y `resumen-semana`. Por eso esos módulos son funciones puras.

### Atributos `data-*` de prueba

**Qué es.** Atributos que las pruebas usan como anclas estables.

**En el proyecto.** Por ejemplo `data-alerta`, `data-tipo`, `data-nivel`, `data-alerta-prueba`, `data-alerta-no-vigente`, `data-alerta-nueva`, `data-alerta-compartir`, `data-cargado` y `data-estado` (`vacio` o `lista`). No son estilo: cambiarlos rompe las pruebas.

### Móvil (375 px y 768 px)

**Qué es.** Anchos de referencia para las pruebas responsivas.

**En el proyecto.** `movil.spec.ts` recorre 375 px (teléfono pequeño) y 768 px (tableta); un comentario de la política de privacidad recuerda que «a 375 px la tabla de terceros no cabía».
