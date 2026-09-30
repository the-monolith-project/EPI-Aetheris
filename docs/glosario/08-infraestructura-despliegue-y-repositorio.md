# Rama 8 · Infraestructura, despliegue y repositorio

Vocabulario de cómo se levanta, se despliega y se mantiene el proyecto: contenedores, Docker Compose, Render, el flujo de ramas de Git, las convenciones del repositorio, la integración continua y las herramientas de trabajo con agentes de código.

**Para quién es.** Para quien clona el repositorio, abre `docker-compose.yml` o `render.yaml`, lee un mensaje de commit que cita un issue o se pregunta por qué existe un archivo `.local.md`.

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris, con los valores exactos), **Dónde** (archivo, ADR o issue) y **Ojo** (errores frecuentes). Las expansiones de siglas que el repositorio no da se marcan como «de uso general».

**Ramas vecinas.** Las tablas y el volcado de datos están en [`07-base-de-datos-y-migraciones.md`](07-base-de-datos-y-migraciones.md); la API y sus variables, en [`06-backend-y-api.md`](06-backend-y-api.md); el frontend y su tooling, en [`09-frontend-web.md`](09-frontend-web.md); las decisiones y los ADR, en [`10-proceso-gobernanza-y-documentacion.md`](10-proceso-gobernanza-y-documentacion.md).

<!-- INDICE:INICIO -->

## Índice alfabético (39 entradas)

- **A** — [AGENTS.md](#agentsmd) · [Archivos de tarea locales (.local.md)](#archivos-de-tarea-locales-localmd)
- **B** — [Blueprint (render.yaml)](#blueprint-renderyaml)
- **C** — [Cambios de esquema después del primer despliegue](#cambios-de-esquema-después-del-primer-despliegue) · [Claude Code y revisión automática](#claude-code-y-revisión-automática) · [Cold start (arranque en frío)](#cold-start-arranque-en-frío) · [container_name y puertos fijos](#container_name-y-puertos-fijos)
- **D** — [Dependabot](#dependabot) · [.design-sync/ (DesignSync)](#design-sync-designsync) · [Docker Compose y docker compose up](#docker-compose-y-docker-compose-up) · [Docker y contenedor](#docker-y-contenedor) · [dockerCommand y dockerContext](#dockercommand-y-dockercontext)
- **E** — [.env y .env.example](#env-y-envexample)
- **F** — [Flujo Backend tests](#flujo-backend-tests) · [Flujo de ramas (main y dev)](#flujo-de-ramas-main-y-dev) · [fromDatabase](#fromdatabase)
- **G** — [GitHub Actions](#github-actions) · [graphify-out/](#graphify-out)
- **H** — [healthcheck y depends_on](#healthcheck-y-depends_on) · [Hook pre-commit](#hook-pre-commit)
- **I** — [Issues y PR citados por número](#issues-y-pr-citados-por-número)
- **J** — [.jules/](#jules)
- **M** — [Manual Deploy](#manual-deploy)
- **P** — [Perfil de Compose (profiles)](#perfil-de-compose-profiles) · [Plan de pago y tier gratuito](#plan-de-pago-y-tier-gratuito) · [Plantillas de PR y de issue](#plantillas-de-pr-y-de-issue) · [Primer despliegue (pasos manuales, una sola vez)](#primer-despliegue-pasos-manuales-una-sola-vez) · [PUBLIC_API_URL (variable de build)](#public_api_url-variable-de-build)
- **R** — [Red, volumen y bind mount](#red-volumen-y-bind-mount) · [Releases y tags de hito](#releases-y-tags-de-hito) · [Render](#render) · [Rutas ignoradas por Git](#rutas-ignoradas-por-git)
- **S** — [Segundo frontend (aetheris-nitor)](#segundo-frontend-aetheris-nitor) · [Servicios (db, backend, web, e2e)](#servicios-db-backend-web-e2e) · [Sin CHANGELOG](#sin-changelog) · [sync: false](#sync-false)
- **U** — [URL predicha y colisión de nombre](#url-predicha-y-colisión-de-nombre)
- **V** — [Variables obligatorias de Compose (${VAR:?mensaje})](#variables-obligatorias-de-compose-varmensaje)
- **W** — [Worktree y Orca ADE](#worktree-y-orca-ade)

<!-- INDICE:FIN -->

## 1. Contenedores y Docker Compose

### Docker y contenedor

**Qué es.** Docker empaqueta una aplicación con sus dependencias en un **contenedor** que corre igual en cualquier máquina (de uso general).

**En el proyecto.** Es parte del funcionamiento esperado y del aporte declarado: un sistema libre, contenedorizado y reproducible con costo de replicación tendiendo a cero. **Un cambio que funcione solo en la máquina local de quien lo escribe no se considera una implementación completa** (`AGENTS.md` §5).

### Docker Compose y `docker compose up`

**Qué es.** Herramienta que define y levanta varios contenedores desde un archivo (`docker-compose.yml`).

**En el proyecto.** `cp .env.example .env` y `docker compose up -d` levantan la base con datos reales y la API; el resultado es un sistema funcionando tras un `git clone`. La API queda en `http://localhost:8000` (con `/health`) y la base en `localhost:5432`. El **frontend no arranca con `docker compose up`**: se levanta desde `web/` con `pnpm install && pnpm dev` (`http://localhost:4321`).

**Ojo.** El `README` sigue diciendo «Astro 4» y «3 servicios» mientras `web/` usa una versión más nueva y el servicio `web` pasó a un perfil bajo demanda (#156): ver [Notas de vigencia](README.md#notas-de-vigencia).

### Servicios (`db`, `backend`, `web`, `e2e`)

**Qué es.** Los contenedores que define `docker-compose.yml`.

**En el proyecto.**

| Servicio | Contenedor | Puerto | Notas |
|---|---|---|---|
| `db` | `aetheris_db` | 5432 | `postgres:15-alpine`; monta `./db/migrations` y el seed en `/docker-entrypoint-initdb.d`; `healthcheck` con `pg_isready` cada 5 s |
| `backend` | `aetheris_backend` | 8000 | Construye `./backend`; `POSTGRES_HOST=db`; depende de `db` sana; monta `./backend` como `/app` |
| `web` | `aetheris_web` | 4321 | **Perfil `web`**: `docker compose --profile web up -d web`; monta `./web` y `./docs` (solo lectura) |
| `e2e` | — | — | **Perfil `test`**: pruebas de extremo a extremo con Playwright (`Dockerfile.e2e`, `network_mode: host`, `ipc: host`) |

### Perfil de Compose (`profiles`)

**Qué es.** Mecanismo para que un servicio solo arranque si se pide su perfil.

**En el proyecto.** `web` tiene el perfil `web` y `e2e` el perfil `test`. Por defecto el frontend se levanta desde el checkout con `pnpm dev`, para que el puerto 4321 no lo ocupe una imagen con dependencias antiguas.

### Red, volumen y bind mount

**Qué es.** La red conecta los contenedores; un volumen conserva datos; un bind mount enlaza una carpeta del host.

**En el proyecto.** Red `aetheris_network` (driver `bridge`); volumen `pgdata` para los datos de Postgres; bind mounts `./backend:/app` (recarga en desarrollo), `./web:/app` (con `/app/node_modules` aparte) y `./docs:/docs:ro`. Este último existe porque la pestaña Biblioteca lee una **selección curada** de los `.md` de `docs/biblioteca/` en build (`web/src/content.config.ts`): por eso `docs/` no debe llevar documentos con otra estructura en esa carpeta.

### `healthcheck` y `depends_on`

**Qué es.** Un `healthcheck` comprueba que un contenedor está listo; `depends_on` con `condition: service_healthy` hace esperar a otro.

**En el proyecto.** `backend` no arranca hasta que `db` pasa `pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}`.

### `container_name` y puertos fijos

**Qué es.** Nombres de contenedor y puertos publicados que no cambian entre ejecuciones.

**En el proyecto.** Comparten el demonio Docker del host: por eso **solo un worktree a la vez** puede correr `docker compose up`. No se «arregla» espaciando nombres o puertos por worktree sin preguntar. CORS admite `localhost:4321` y `localhost:4322` para que dos servidores de desarrollo convivan.

### Variables obligatorias de Compose (`${VAR:?mensaje}`)

**Qué es.** Sintaxis que hace fallar el arranque si falta una variable.

**En el proyecto.** `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB` se exigen con el mensaje «Debe definirse … en el archivo .env (ver .env.example)». El `.env` **nunca se versiona**.

### `.env` y `.env.example`

**Qué es.** El `.env` guarda la configuración real; `.env.example` es solo la plantilla de variables.

**En el proyecto.** Se copia de la plantilla y no se commitean credenciales reales a código, documentación, tests ni commits. `ALERTAS_TOKEN` va vacío a propósito.

## 2. Despliegue en Render

### Render

**Qué es.** Plataforma de alojamiento (PaaS) elegida para publicar el proyecto.

**En el proyecto.** Decisión del 2026-08-22, para tener una URL pública antes del video demo (2026-09-05) y la Expo Técnica (2026-09-29). Ganó a Railway, Fly.io y Vercel por encajar directo con el `docker-compose.yml` (el Blueprint declara los servicios como infraestructura como código), tener el mejor historial de uptime reciente de las opciones evaluadas y no exigir administración manual de Postgres. Es un despliegue **de demostración**, no de producción con usuarios reales, y no cambia el estatuto sobre APIs de datos de pago, que aplica a las fuentes y no al hosting.

**Dónde.** [`docs/despliegue-render.md`](../despliegue-render.md), `render.yaml`.

### Blueprint (`render.yaml`)

**Qué es.** Archivo que declara los servicios de Render como infraestructura como código (IaC).

**En el proyecto.** Declara tres recursos, todos en la región `oregon` (misma región = red privada entre backend y base):

| Recurso | Tipo | Detalle |
|---|---|---|
| `epi-aetheris-db` | Postgres gestionado | Versión 15, plan `basic-256mb`, base `epi_aetheris`, usuario `aetheris_user` |
| `epi-aetheris-backend` | Servicio web (Docker) | `backend/Dockerfile.render`, contexto = raíz del repositorio, plan `starter`, rama `main`, `healthCheckPath: /health` |
| `epi-aetheris-web` | Sitio estático | `rootDir ./web`, `pnpm install --frozen-lockfile && pnpm build`, publica `./dist` |

**Ojo.** El sitio estático no acepta región (se sirve por CDN global).

### Plan de pago y tier gratuito

**Qué es.** El nivel de servicio contratado.

**En el proyecto.** Starter para el backend y Basic-256mb para la base, unos **14 USD al mes**, elegidos desde el primer día en vez del tier gratuito: el tier gratuito duerme el backend a los 15 minutos de inactividad (arranque en frío de ~1 minuto, malo para una demo en vivo) y su Postgres gratis expira a los 30 días, menos que la ventana de trabajo hasta la Expo. Vercel más Render (frontend aparte) era igual de válido al mismo costo y se descartó solo por preferencia de una sola cuenta.

### Cold start (arranque en frío)

**Qué es.** El retraso de la primera respuesta cuando un servicio dormido debe volver a levantarse (de uso general).

**En el proyecto.** Motivo de descartar el plan gratuito de Render. También afecta al service worker y a los estados de carga del frontend cuando la API tarda.

### `fromDatabase`

**Qué es.** Directiva del Blueprint que inyecta una propiedad de la base gestionada como variable de entorno.

**En el proyecto.** Entrega al backend `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD` sin escribirlas.

### `sync: false`

**Qué es.** Marca de una variable del Blueprint que Render pide en el panel y **no** versiona.

**En el proyecto.** Se usa para `ALERTAS_TOKEN`. Sin él, `POST` y `PATCH /api/alertas` responden 503.

### `dockerCommand` y `dockerContext`

**Qué es.** Comando de arranque y carpeta de contexto de construcción de la imagen.

**En el proyecto.** `dockerContext: .` (raíz) para copiar `db/aplicar_migraciones.py` y `db/migrations/` dentro de la imagen; `dockerCommand: uvicorn api.main:app --host 0.0.0.0 --port 8000` sin `--reload`. `docker-compose` sigue construyendo `backend/Dockerfile` con contexto `./backend`: **no se mezclan los dos**.

### `PUBLIC_API_URL` (variable de build)

**Qué es.** Variable de Astro con prefijo `PUBLIC_` que se **embebe en el bundle del cliente en tiempo de compilación**.

**En el proyecto.** Se declara como valor fijo (`https://epi-aetheris-backend.onrender.com`) y no como `fromService`, porque Astro ya generó el HTML y el JS antes de que ese lookup pudiera resolverse.

**Ojo.** **Cambiar la variable sin reconstruir no tiene efecto**: exige un redeploy del frontend. Si el mapa muestra «sin dato» en todo, lo más probable es un frontend compilado contra la `PUBLIC_API_URL` vieja.

### URL predicha y colisión de nombre

**Qué es.** Render asigna `https://<nombre>.onrender.com` salvo colisión de nombre (el espacio de nombres es global), en cuyo caso agrega un sufijo.

**En el proyecto.** `CORS_ALLOWED_ORIGINS` y `PUBLIC_API_URL` están escritas con la URL predicha, así que **hay que verificar las URL reales en el panel tras el primer despliegue** y corregir `render.yaml` si no coinciden.

### Primer despliegue (pasos manuales, una sola vez)

**Qué es.** El procedimiento inicial contra la base gestionada, que Render no automatiza.

**En el proyecto.** Render no tiene un hook `docker-entrypoint-initdb.d`, así que:

1. Conectar el Blueprint al repositorio (rama `main`): se crean los tres servicios y el backend falla el `preDeployCommand` y el healthcheck hasta el paso 3.
2. Copiar la **External Connection String** de `epi-aetheris-db` (Connect, External).
3. Desde el host, **aplicar el DDL** (`psql` sobre cada `db/migrations/[0-9]*.sql`), registrar las migraciones (`python db/aplicar_migraciones.py --bootstrap`) y **cargar el seed** en su propia invocación de `psql`. Forzar un Manual Deploy del backend.
4. Verificar las URL reales y corregir `CORS_ALLOWED_ORIGINS` y `PUBLIC_API_URL`; redeployar el frontend.
5. Confirmar `GET /health` y que `/dengue` cargue el mapa con datos reales.

**Ojo.** `--bootstrap` solo crea `schema_migrations` y marca archivos como aplicados: **no ejecuta SQL**. Por eso el DDL va antes.

### Cambios de esquema después del primer despliegue

**Qué es.** El flujo normal una vez que la base existe.

**En el proyecto.** Agregar un archivo en `db/migrations/` (con el ADR aceptado antes) y mergearlo a `main`. El `preDeployCommand` (`python db/aplicar_migraciones.py`) corre contra las mismas variables `POSTGRES_*` antes de conmutar el tráfico; si falla, el despliegue no avanza y sigue viva la versión anterior. Para un hotfix sin esperar un despliegue, el mismo comando desde el host.

### Manual Deploy

**Qué es.** Botón del panel de Render que fuerza un despliegue.

**En el proyecto.** Se usa tras `--bootstrap` para que el backend pase el healthcheck, y para reconstruir el frontend cuando cambia `PUBLIC_API_URL`.

### Segundo frontend (`aetheris-nitor`)

**Qué es.** Un **segundo repositorio** con su propia copia del frontend Astro, desplegado como sitio estático aparte.

**En el proyecto.** `the-monolith-project/aetheris-nitor` (repo «vitrina» o «fork-vitrina», «Aetheris Nitor»), en `https://epi-aetheris.dev` (más `www.` y `aetheris-nitor.onrender.com`), contra el mismo backend. Por eso `render.yaml` lista esos tres orígenes en `CORS_ALLOWED_ORIGINS` y el backend, que rechaza `*` por diseño, exige editar esa lista para cada frontend nuevo. **Las dos copias han divergido** (~57 archivos distintos o exclusivos bajo `src/` al 2026-09-22): todo cambio de interfaz compartida se aplica dos veces (pasó con `PanelNowcastDengue.astro` y la ruta `/demos`). Cuál es la fuente canónica **no está decidido**.

## 3. Git y repositorios

### Flujo de ramas (`main` y `dev`)

**Qué es.** El modelo de ramas del repositorio (`AGENTS.md` §15).

**En el proyecto.** **`main`** es la rama de **release**: lo que Render despliega, protegida (pull request obligatoria) y que solo recibe PR desde `dev`. **`dev`** es la rama de **integración** y la rama por defecto: todas las PR de funcionalidades y correcciones van contra `dev`. Cuando `dev` está estable se abre una PR `dev → main` y ese merge dispara el despliegue. Las ramas de trabajo son `feat/*`, `fix/*`, `chore/*` y `docs/*`, partiendo de `dev`.

**Ojo.** `AGENTS.md` prohíbe hacer commit, push, merge, rebase o force push salvo que el usuario lo solicite, y no descartar cambios locales que no se hayan creado.

### Releases y tags de hito

**Qué es.** Dos series de tags con propósitos distintos, ambas en el remoto.

**En el proyecto.** **Releases** `v0.1.0` (2026-08-22), `v0.2.0` (2026-08-25), `v0.3.0` (2026-08-29), `v0.4.0` (2026-09-02), `v0.5.0` (2026-09-13, «accesibilidad, observatorio respiratorio y nowcast») y `v1.0.0` (2026-09-28, «tablero de MINSAL y series nacionales hasta 2026»), publicadas como GitHub Releases; un release se corta promoviendo `dev` a `main` por PR, nunca con push directo. Las fechas son las de los commits que apuntan las etiquetas. **Tags de hito narrativo** `hito/00-esqueleto` a `hito/08-clasificador-retirado`: nueve tags anotados, pusheados el 2026-09-09 sobre commits históricos ya existentes para recorrer la evolución del proyecto en la Expo Técnica. **No son releases y no se mueven.** El `CHANGELOG.md` de STC es el registro de decisiones, no de versiones.

**Ojo.** El `version` de `web/package.json` (y el de `aetheris-nitor`) sigue en `0.5.0`, aunque el último release es `v1.0.0`; el número del paquete no acompaña a los tags.

### Archivos de tarea locales (`*.local.md`)

**Qué es.** Los `.md` que se pasan para delegar o describir una tarea (planes, indicaciones, informes intermedios): **andamiaje, no entregable**.

**En el proyecto.** No se versionan. Se nombran con el sufijo `.local.md` (por ejemplo `PLAN_ALERTAS_OPERABLES.local.md`), viven en la raíz del repositorio o del worktree y `.gitignore` los ignora. Lo que queda en el repo al terminar es el código, el ADR, la migración y las pruebas.

### Hook `pre-commit`

**Qué es.** Script de Git que se ejecuta antes de cada commit (de uso general).

**En el proyecto.** `.githooks/pre-commit` **aborta el commit** si un archivo `*.local.md` (o los planes legacy `INDICACIONES_ALERTAS.md` y `PLAN_ALERTAS_OPERABLES.md`) llega al stage con `git add -f`. Se activa una vez por clon con `git config core.hooksPath .githooks`. Usa `--diff-filter=ACMR`: un borrado de esos archivos no se bloquea.

### Worktree y Orca ADE

**Qué es.** Un `git worktree` es un directorio de trabajo adicional del mismo repositorio; Orca ADE es el entorno de desarrollo de agentes que los gestiona (el repositorio no expande «ADE»).

**En el proyecto.** `orca.yaml` define el `setup` (crear `backend/.venv`, instalar dependencias, `corepack enable`, `pnpm install`) y los directorios compartidos entre worktrees (`backend/.venv`, `web/node_modules`, `backend/ingestion/data/raw` y `interim`). Como `docker-compose` usa nombres y puertos fijos, **solo un worktree corre `docker compose up` a la vez**.

### Rutas ignoradas por Git

**Qué es.** Archivos que `.gitignore` excluye del control de versiones.

**En el proyecto.** `.env` y `.env.*` (salvo `.env.example`), `pgdata/`, `backend/ingestion/data/raw/` y `interim/` (con excepciones enumeradas), `web/public/datos-exploracion/` (extracto exploratorio de IRA), `graphify-out/` (índice de grafo de código regenerable), `.claude/` y `/.agents` (configuración local de agentes) y `*.local.md`. La regla de datos y sus excepciones deliberadas están en [Capa cruda y capa intermedia](02-fuentes-de-datos-e-ingesta.md#capa-cruda-y-capa-intermedia).

### Plantillas de PR y de issue

**Qué es.** Formularios que GitHub precarga.

**En el proyecto.** `.github/pull_request_template.md` tiene los apartados «Qué se hizo», «Por qué», «Cómo probarlo» y un checklist: `docker compose up` levanta sin pasos manuales no documentados; si se modifica una decisión ya cerrada hay un ADR que la respalda; una migración sigue la convención `NNNN_descripcion_breve.sql`. Hay además plantillas de `bug_report` y `feature_request`.

### Issues y PR citados por número

**Qué es.** Los comentarios y ADR citan issues de GitHub por su número.

**En el proyecto.** Los más frecuentes:

| N.º | Tema |
|---|---|
| #61 | Rate limiting y DoS de la API (queda pendiente solo el WAF perimetral) |
| #66, #78 | PR que introdujeron `slowapi` |
| #67 | `X-Forwarded-For`: usar el último salto |
| #68 | Pool de conexiones a Postgres |
| #69 | `RATE_LIMIT_ENABLED` en `conftest.py` |
| #71 | Doble comprobación con lock al cargar artefactos |
| #72 | Artefactos del clasificador ausentes en Render (`/api/riesgo-nacional`); luego versionados |
| #82 | El seed sin las líneas de `DISABLE TRIGGER` |
| #83 | Migraciones en el `preDeployCommand` |
| #84 | Degradación elegante de los endpoints respiratorios |
| #100 | Borrado del `seed_datos_reales.sql` vacío de `db/migrations/` |
| #110 | PR de la Biblioteca (reserva el ADR 0016) |
| #124 | Clima 2025 y 2026 en el volcado |
| #156 | El servicio `web` pasa a un perfil bajo demanda |

### Sin CHANGELOG

**Qué es.** Convención de documentación.

**En el proyecto.** El historial de cambios son los **mensajes de commit** (`AGENTS.md` §16): no hay un `CHANGELOG` propio en el repositorio de código. El registro de decisiones históricas vive en el repositorio STC.

## 4. Integración continua y automatización

### GitHub Actions

**Qué es.** Sistema de integración continua de GitHub (de uso general).

**En el proyecto.** Tres flujos en `.github/workflows/`: `backend-tests.yml`, `claude.yml` y `claude-code-review.yml`.

### Flujo `Backend tests`

**Qué es.** La suite de pruebas del backend en CI.

**En el proyecto.** Se dispara en `push` y `pull_request` contra `main` y `dev`. Levanta un servicio Postgres 15, **aplica las migraciones y el seed con `psql -v ON_ERROR_STOP=1` después del checkout** (no por volúmenes, que Docker crearía vacíos con permisos que el runner no puede borrar: `EACCES ... rmdir db/migrations`) y corre `python -m pytest ingestion/tests/ api/tests/ -v`.

**Ojo.** `AGENTS.md` afirma que «no hay linter ni CI en el repo»: es una frase desactualizada, porque este flujo existe. Los tests que necesitan base de datos **se saltan (no fallan)** si no hay Postgres en `localhost:5432`.

### Claude Code y revisión automática

**Qué es.** Dos flujos que usan la acción `anthropics/claude-code-action`.

**En el proyecto.** `claude.yml` responde cuando un comentario, una revisión o un issue menciona `@claude`; `claude-code-review.yml` revisa cada PR al abrirse, sincronizarse, quedar lista para revisión o reabrirse. Ambos usan el secreto `CLAUDE_CODE_OAUTH_TOKEN`.

### Dependabot

**Qué es.** Servicio de GitHub que abre PR por dependencias con alertas de seguridad (de uso general).

**En el proyecto.** Aparece en el historial (por ejemplo `fast-uri 3.1.7 o superior por las alertas de Dependabot`, #155).

## 5. Herramientas de trabajo con agentes

### `AGENTS.md`

**Qué es.** Archivo de instrucciones para agentes de programación dentro del repositorio.

**En el proyecto.** Define qué fuentes consultar, qué reglas respetar y cómo proceder antes de modificar código. No duplica los ADR: la sección 17 consolida el contexto técnico vigente. Fija la **precedencia** (ADR aceptado, luego la sección 17, luego el código en `main`), el flujo «analizar → proponer → implementar → validar → revisar diff», y que las tareas de revisión no modifican archivos. Ver [Precedencia de fuentes](10-proceso-gobernanza-y-documentacion.md#precedencia-de-fuentes).

### `.design-sync/` (DesignSync)

**Qué es.** Carpeta de configuración para sincronizar el sistema de diseño con una herramienta de diseño externa.

**En el proyecto.** Es un sync **solo de tokens** (`componentCount: 0`): el proyecto es Astro puro, sin componentes React ni Storybook, así que el `ds-bundle/` se autor-genera a mano (`styles.css`, `tokens/`, `fonts/`). `NOTES.md` guarda las reglas que solo viven en comentarios del código: Fraunces (`--font-display`) **solo** para el H1 de página y los dos H2 de la landing; el coral `#ff5a45` aparece en los SVG del logo pero **no es un token** de UI (la paleta es verde y lavanda). Ver [Tokens de diseño](09-frontend-web.md#tokens-de-diseño).

### `.jules/`

**Qué es.** Carpeta con tres bitácoras de aprendizajes de agentes automáticos.

**En el proyecto.** `bolt.md` (rendimiento: compresión gzip, caché de artefactos, evitar el módulo `statistics` en bucles cerrados), `sentinel.md` (seguridad: path traversal por URL codificada, comodín en CORS, XSS con `innerHTML`) y `palette.md` (experiencia de uso: estados vacíos, retroalimentación en botones, estilo de controles de formulario). El repositorio no expande el nombre de la carpeta.

### `graphify-out/`

**Qué es.** Índice de grafo de código regenerable localmente.

**En el proyecto.** Está en `.gitignore`: no se versiona.
