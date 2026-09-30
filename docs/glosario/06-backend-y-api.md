# Rama 6 · Backend y API

Vocabulario de `backend/api/`: el marco, los límites de tasa, las cabeceras de seguridad, el pool de conexiones, la caché HTTP, los contratos de respuesta (`disponible: false`, `aviso`) y el catálogo de endpoints con sus códigos de estado.

**Para quién es.** Para quien lee `main.py`, un test de la API o la respuesta de un endpoint y necesita saber qué significan `RATE_LIMIT_HEAVY`, `_client_ip`, «degradación elegante» o «Bearer».

**Cómo leer una entrada.** Cada término lleva, según haga falta, **Qué es** (definición general), **En el proyecto** (cómo lo usa EPI-Aetheris, con los valores por defecto), **Dónde** (archivo, ADR o issue) y **Ojo** (errores frecuentes). Las expansiones de siglas que el repositorio no da se marcan como «de uso general».

**Ramas vecinas.** Lo que calcula cada módulo está en [`05-modulos-descriptivos-y-alertas.md`](05-modulos-descriptivos-y-alertas.md); las tablas que consulta la API, en [`07-base-de-datos-y-migraciones.md`](07-base-de-datos-y-migraciones.md); el despliegue y las variables de Render, en [`08-infraestructura-despliegue-y-repositorio.md`](08-infraestructura-despliegue-y-repositorio.md); el consumo desde el navegador, en [`09-frontend-web.md`](09-frontend-web.md).

<!-- INDICE:INICIO -->

## Índice alfabético (40 entradas)

- **A** — [aviso](#aviso)
- **B** — [backend/model](#backendmodel) · [Bearer y ALERTAS_TOKEN](#bearer-y-alertas_token)
- **C** — [Cache-Control y TTL](#cache-control-y-ttl) · [Carga perezosa de artefactos](#carga-perezosa-de-artefactos) · [_client_ip y X-Forwarded-For](#_client_ip-y-x-forwarded-for) · [Códigos de estado](#códigos-de-estado) · [_conexion() y rollback](#_conexion-y-rollback) · [conftest.py y el límite de tasa en pruebas](#conftestpy-y-el-límite-de-tasa-en-pruebas) · [Contrato disponible: false](#contrato-disponible-false) · [CORS (CORS_ALLOWED_ORIGINS)](#cors-cors_allowed_origins) · [CSP (Content-Security-Policy)](#csp-content-security-policy)
- **D** — [Degradación elegante](#degradación-elegante) · [departamento_id (código ISO)](#departamento_id-código-iso) · [Dockerfile y Dockerfile.render](#dockerfile-y-dockerfilerender)
- **E** — [Endpoints de alertas](#endpoints-de-alertas) · [Endpoints de dengue](#endpoints-de-dengue) · [Endpoints respiratorios](#endpoints-respiratorios)
- **F** — [FastAPI](#fastapi)
- **G** — [GZip (GZipMiddleware)](#gzip-gzipmiddleware)
- **H** — [/health](#health)
- **M** — [monkeypatch e importlib.reload](#monkeypatch-e-importlibreload)
- **O** — [Orden de los middleware](#orden-de-los-middleware)
- **P** — [Pool de conexiones (ThreadedConnectionPool)](#pool-de-conexiones-threadedconnectionpool) · [Preflight](#preflight) · [psycopg2 y SQL sin ORM](#psycopg2-y-sql-sin-orm) · [Pydantic](#pydantic) · [pytest y TestClient](#pytest-y-testclient)
- **R** — [Rate limiting (slowapi)](#rate-limiting-slowapi) · [RATE_LIMIT_DEFAULT, RATE_LIMIT_HEAVY, RATE_LIMIT_WRITE y RATE_LIMIT_ENABLED](#rate_limit_default-rate_limit_heavy-rate_limit_write-y-rate_limit_enabled) · [Ruta /api/... y ruta /api/v1/...](#ruta-api-y-ruta-apiv1)
- **S** — [SecurityHeadersMiddleware](#securityheadersmiddleware) · [Semáforo del pool](#semáforo-del-pool) · [Semana entre 1 y 53](#semana-entre-1-y-53) · [Sin datos personales en la API](#sin-datos-personales-en-la-api) · [Swagger UI (/docs)](#swagger-ui-docs)
- **T** — [Test de fórmulas duplicadas](#test-de-fórmulas-duplicadas)
- **U** — [Usuario sin privilegios (appuser)](#usuario-sin-privilegios-appuser) · [Uvicorn](#uvicorn)
- **V** — [Variables de entorno de la API](#variables-de-entorno-de-la-api)

<!-- INDICE:FIN -->

## 1. Marco y ejecución

### FastAPI

**Qué es.** Marco web de Python para APIs, basado en anotaciones de tipos y Pydantic.

**En el proyecto.** La API es `EPI-Aetheris API` (`title` en `main.py`, versión `0.1.0`), con FastAPI 0.111.0. Sirve JSON descriptivo de datos epidemiológicos; no sirve HTML de usuario. Las funciones de ruta son `def` **síncronas**, por lo que FastAPI las corre en su threadpool (unos 40 hilos por defecto).

**Dónde.** `backend/api/main.py`, `backend/requirements.txt`.

### Uvicorn

**Qué es.** Servidor ASGI que ejecuta la aplicación.

**En el proyecto.** `uvicorn api.main:app --host 0.0.0.0 --port 8000`. En `docker-compose` corre con `--reload` (recarga al cambiar el código, con bind mount) y en Render **sin `--reload` y sin `--workers`**: un solo proceso. Eso importa porque el límite de tasa en memoria es por proceso, así que ese contador **es** el global. No corre con `--proxy-headers`.

### Pydantic

**Qué es.** Biblioteca de validación de datos por modelos tipados.

**En el proyecto.** Versión 2.7.4. Los cuerpos de escritura de alertas son `AlertaCrear` y `AlertaParche` con `extra="forbid"` (un campo desconocido se rechaza) y validadores por campo (`tipo`, `nivel`, `etiqueta`, `departamentos`, y texto no vacío para `titulo`, `contexto`, `indicaciones`, `fuente` y `autor`). Un cuerpo inválido responde **422**.

### psycopg2 y SQL sin ORM

**Qué es.** `psycopg2` es el controlador de PostgreSQL para Python; un ORM (mapeo objeto-relacional) esconde el SQL detrás de clases.

**En el proyecto.** **No hay ORM**: cada endpoint escribe su SQL con parámetros. Se usa `psycopg2-binary==2.9.9`. Cambiar el pool actual de `psycopg2.pool` a `psycopg_pool` se descartó (`AGENTS.md` §5) por ser rotación de dependencias sin beneficio medible ([ADR 0017](../adr/0017-endurecimiento-seguridad-backend.md)).

### Ruta `/api/...` y ruta `/api/v1/...`

**Qué es.** Convención de prefijos de la API.

**En el proyecto.** Los **módulos descriptivos** (M1 a M4, dataset analítico) y la integridad viven bajo `/api/v1/` (`/api/v1/spatial/current`, `/api/v1/temporal/{departamento_id}`, `/api/v1/presion/...`, `/api/v1/analisis/dengue`, `/api/v1/vigilancia/integridad`). Las series, el observatorio respiratorio, las alertas y el nowcast usan `/api/` sin versión. No hay una v2.

### `departamento_id` (código ISO)

**Qué es.** Parámetro de ruta de los endpoints por departamento.

**En el proyecto.** Su valor es el `codigo` de `regiones` (ISO 3166-2:SV, por ejemplo `SV-SS`), **no** el id numérico interno. Un código inexistente responde **404**. Ver [Código ISO 3166-2:SV](01-epidemiologia-y-vigilancia.md#código-iso-3166-2sv).

### Swagger UI (`/docs`)

**Qué es.** Interfaz interactiva de FastAPI para explorar la API.

**En el proyecto.** Es la razón de que la CSP permita `'unsafe-inline'` y `cdn.jsdelivr.net`: apretarla rompería `/docs` sin ganancia de cara al usuario, porque la API sirve JSON y no HTML.

## 2. Límites de tasa y seguridad

### Rate limiting (`slowapi`)

**Qué es.** Limitar cuántas peticiones puede hacer un cliente por minuto.

**En el proyecto.** `slowapi==0.1.10` con `limits==5.8.0` y contador **en memoria**. Es la capa de aplicación del issue #61 (DoS): un `Limiter` con `key_func=_client_ip`, un límite global por defecto y un umbral más estricto en los endpoints caros. Un backend compartido (Redis) solo haría falta si algún día se pasa a `--workers N`, porque entonces el límite efectivo sería N veces el configurado.

**Ojo.** Lo único que el issue #61 deja pendiente es el WAF perimetral (Cloudflare), que requiere cuenta y decisión de infraestructura.

### `RATE_LIMIT_DEFAULT`, `RATE_LIMIT_HEAVY`, `RATE_LIMIT_WRITE` y `RATE_LIMIT_ENABLED`

**Qué es.** Las cuatro variables de entorno del límite de tasa.

**En el proyecto.**

| Variable | Valor por defecto | Se aplica a |
|---|---|---|
| `RATE_LIMIT_DEFAULT` | `120/minute` | Todo lo que no tiene otro umbral (límite global por IP) |
| `RATE_LIMIT_HEAVY` | `30/minute` | Endpoints que recalculan on-demand: `/api/riesgo-nacional`, `/api/nowcast-dengue*`, `/api/casos-departamentales`, `/api/ira/departamental`, `/api/v1/spatial/current`, `/api/v1/presion/current`, `/api/v1/analisis/dengue*` y `/api/v1/vigilancia/integridad` |
| `RATE_LIMIT_WRITE` | `10/minute` | `POST /api/alertas` y `PATCH /api/alertas/{id}` |
| `RATE_LIMIT_ENABLED` | `true` | `false` lo apaga por completo (lo usan los tests) |

`/health` está **exento** (`@limiter.exempt`). Los valores se leen en el import para que los tests puedan cambiarlos con `monkeypatch` más `importlib.reload`. `RATE_LIMIT_WRITE` no se declara en `render.yaml`: el valor por defecto del código sirve en producción.

### `_client_ip` y `X-Forwarded-For`

**Qué es.** La función que decide a qué «cliente» se le cuenta cada petición.

**En el proyecto.** Toma el **último salto** de la cabecera `X-Forwarded-For` y cae a la IP del socket solo en local y en tests. Motivo (issue #67): en Render el borde **anexa** la IP real al final de la cabecera, así que el último valor es el único que el cliente no puede falsificar; con el primero, quien mande `X-Forwarded-For: 1.2.3.4` se bucketizaría como una IP distinta en cada petición y evadiría el límite. Sin ninguna de las dos cosas, todo el tráfico compartiría el balanceador de Render como un único bucket.

### Orden de los middleware

**Qué es.** El orden en que se añaden `add_middleware` determina qué envuelve a qué.

**En el proyecto.** `SlowAPIMiddleware` se añade **antes** de CORS para que la respuesta **429 también lleve las cabeceras CORS** (el frontend ve un 429 legible en vez de un error de red opaco); `SecurityHeadersMiddleware` se añade último y **envuelve todo**. Reordenarlos cambia el comportamiento.

### CORS (`CORS_ALLOWED_ORIGINS`)

**Qué es.** Mecanismo del navegador que controla qué origen puede leer las respuestas de otro.

**En el proyecto.** La lista sale de la variable `CORS_ALLOWED_ORIGINS` (separada por comas; por defecto `http://localhost:4321`). **Un `*` hace fallar el arranque** con `ValueError`. Los métodos permitidos son `GET`, `POST`, `PATCH`, `HEAD` y `OPTIONS`, y `allow_headers` es la lista explícita `["Authorization", "Content-Type"]`, las dos que manda el formulario `/alertas/nueva`. En producción incluye `epi-aetheris-web.onrender.com`, `epi-aetheris.dev`, `www.epi-aetheris.dev` y `aetheris-nitor.onrender.com`.

**Ojo.** Si falta el dominio del frontend desplegado, las llamadas del navegador al backend **fallan silenciosamente**.

### Preflight

**Qué es.** Petición `OPTIONS` que el navegador hace antes de una petición con cabeceras propias, para comprobar el permiso.

**En el proyecto.** El preflight del formulario `/alertas/nueva` (que envía `Authorization` y `Content-Type`) está cubierto por un test (`test_cors.py`).

### `SecurityHeadersMiddleware`

**Qué es.** Middleware que añade cabeceras de seguridad a **todas** las respuestas.

**En el proyecto.** Añade `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Strict-Transport-Security` (`max-age=31536000; includeSubDomains`), `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=()` y una `Content-Security-Policy`. La API no usa geolocalización, cámara, micrófono ni pagos, así que negarlas es barato y correcto.

### CSP (Content-Security-Policy)

**Qué es.** Cabecera que limita desde dónde puede cargar recursos una página (de uso general).

**En el proyecto.** `default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com`. Deliberadamente laxa para mantener viva la Swagger UI.

### GZip (`GZipMiddleware`)

**Qué es.** Compresión de las respuestas grandes.

**En el proyecto.** `minimum_size=1000` bytes. Se añadió porque varias respuestas son series históricas completas en JSON sin paginar, muy compresibles; FastAPI no comprime nada por defecto.

### Bearer y `ALERTAS_TOKEN`

**Qué es.** Un esquema de autenticación en el que el cliente manda `Authorization: Bearer <secreto>`.

**En el proyecto.** Protege solo la **escritura de alertas**. El secreto está en la variable `ALERTAS_TOKEN` y se compara con `secrets.compare_digest` (comparación en tiempo constante, no `==`). Se lee el entorno **en cada llamada**. Reglas:

- Cabecera ausente, mal formada o token incorrecto: **401** «No autenticado», sin distinguir un caso de otro (distinguirlos confirmaría a un atacante que el secreto existe).
- `ALERTAS_TOKEN` vacío o no definido: **503** «Escritura de alertas no configurada», y no se escribe.
- Cuerpo mal formado: **422**. Alerta inexistente en `PATCH`: **404**. Un `PATCH` sin campos: **422**.
- Respuesta de escritura con `Cache-Control: no-store`.

El token no se versiona: en `render.yaml` se declara con `sync: false` y en `.env.example` va la clave vacía. Es un secreto compartido, no autorización por persona.

### Sin datos personales en la API

**Qué es.** Principio de diseño.

**En el proyecto.** No hay tabla de usuarios, cuentas ni correos. `/health` y los errores devuelven un mensaje genérico («Error de conexión a la base de datos») y **nunca** la cadena original del error del controlador, porque un manejo incorrecto podría filtrar credenciales.

## 3. Base de datos desde la API

### Pool de conexiones (`ThreadedConnectionPool`)

**Qué es.** Conjunto reutilizable de conexiones abiertas a la base.

**En el proyecto.** Antes de la tarea de rendimiento se abría una conexión nueva por petición y sin timeout; con unos 40 hilos eso agotaba el límite del plan de base de datos pequeño (`basic-256mb`) y salía como un 500 genérico. Ahora hay un pool creado **de forma perezosa** (doble comprobación con `Lock`, sin un handler `lifespan`). Variables: `POSTGRES_POOL_MIN=1`, `POSTGRES_POOL_MAX=10` (techo de conexiones simultáneas), `POSTGRES_CONNECT_TIMEOUT=5` y `POSTGRES_POOL_ACQUIRE_TIMEOUT=10` (segundos que espera una petición a que se libere un slot).

**Dónde.** `_obtener_pool` y `_conexion` en `backend/api/main.py`; issue #68.

### Semáforo del pool

**Qué es.** Un `Semaphore(POSTGRES_POOL_MAX)` que hace esperar al hilo de más.

**En el proyecto.** `ThreadedConnectionPool.getconn()` **no espera** cuando el pool está al tope: lanza `PoolError` de inmediato. El semáforo convierte un pico corto de concurrencia (atendible en serie en milisegundos) en espera en lugar de un 500 seco; si la base está de verdad saturada, el timeout de 10 s evita que el hilo se cuelgue para siempre y sale `TimeoutError`.

### `_conexion()` y `rollback`

**Qué es.** Administrador de contexto que toma una conexión y la repone al salir, también si hubo un error.

**En el proyecto.** Hace `rollback()` antes de devolverla: todas las consultas son de solo lectura, pero `psycopg2` abre una transacción implícita en el primer `SELECT`, y sin el `rollback` la conexión volvería «idle in transaction» reteniendo locks hasta el próximo uso.

### `/health`

**Qué es.** Endpoint de comprobación de salud.

**En el proyecto.** Ejecuta `SELECT 1;` y responde `{"status": "ok", "service": "backend", "database": "connected"}`; ante un fallo, 500 con mensaje genérico. Va con `Cache-Control: no-store` (cachear un «ok» viejo derrotaría su propósito, y Render lo sondea continuamente) y exento del límite de tasa. Es el `healthCheckPath` del Blueprint.

### Degradación elegante

**Qué es.** Que un endpoint responda de forma útil cuando le falta un dato del despliegue, en vez de romper.

**En el proyecto.** Regla del issue #84 (`_degradar_consulta`): una **tabla ausente** o sin filas (SQLSTATE `42P01`, `UndefinedTable`) no es un fallo de conexión y responde **200** con `{disponible: false, motivo, aviso}`; un `OperationalError`, `InterfaceError` o `TimeoutError` sí es un problema de servicio y responde **503**; el resto, **500**. Se aplica al observatorio respiratorio y al tablero; los endpoints de dengue y de M1–M4 siguen respondiendo 500 ante cualquier fallo.

### Contrato `disponible: false`

**Qué es.** Respuesta 200 con `disponible` en `false` en lugar de un error.

**En el proyecto.** Devuelve `{"disponible": false, "motivo": "...", "aviso": "..."}` para que el frontend muestre un aviso explícito. Se usa cuando falta un artefacto (`/api/riesgo-nacional` sin dataset o modelo, issue #72; `/api/nowcast-dengue` sin JSON) o una tabla (virus, neumonías, cobertura) o las capturas del tablero (`/api/ira/nacional`, `/api/neumonias/nacional`: el volcado del repositorio no trae el tablero). Con datos, la respuesta lleva `disponible: true`.

**Ojo.** `/api/alertas` tiene su **propio** contrato (`{aviso, ultima_revision, alertas}`) y no se degrada así: solo distingue conexión (503) del resto (500).

### `aviso`

**Qué es.** Campo de texto presente en las respuestas con la declaración de honestidad del endpoint.

**En el proyecto.** Cada familia de endpoints devuelve su `AVISO_HONESTIDAD_*` (o `AVISO_TABLERO_RESPIRATORIO`, `AVISO_COBERTURA`). El dataset analítico devuelve un objeto `avisos` con el de idoneidad y el de presión. Ver [Aviso de honestidad](05-modulos-descriptivos-y-alertas.md#aviso-de-honestidad-aviso_honestidad_).

### Carga perezosa de artefactos

**Qué es.** Cargar el archivo del clasificador o el dataset solo cuando se pide por primera vez.

**En el proyecto.** `_cargar_modelo` y `_cargar_dataset_riesgo` usan **doble comprobación con lock** (issue #71): sin él, dos peticiones concurrentes en un arranque en frío deserializarían el `joblib` y parsearían el CSV dos veces, justo en la ráfaga de tráfico que el límite de tasa busca absorber. Si el archivo no existe devuelven `None` y el endpoint responde `disponible: false`.

## 4. Caché HTTP

### `Cache-Control` y TTL

**Qué es.** Cabecera estándar que dice cuánto puede reutilizar el navegador una respuesta.

**En el proyecto.** Todo es cabecera HTTP; no hay caché del lado del servidor. Tres TTL según con qué frecuencia cambia el dato:

| Constante | Segundos | Para |
|---|---|---|
| `CACHE_TTL_HISTORICO` | 3600 | Series ya cargadas, que solo cambian con una corrida de ingesta |
| `CACHE_TTL_COMPUTO` | 900 | Capas espaciales o de cómputo (idoneidad, presión, integridad, riesgo nacional): más caras y más sensibles a un cambio de metodología |
| `CACHE_TTL_ALERTAS` | 60 | Alertas de campo: un cambio debe reflejarse en el minuto |

Las respuestas llevan `public, max-age=<TTL>`; `/health` y la escritura, `no-store`.

## 5. Catálogo de endpoints

### Endpoints de dengue

**Qué es.** Las rutas de casos y módulos descriptivos de dengue.

**En el proyecto.**

| Ruta | Qué devuelve | Límite |
|---|---|---|
| `GET /api/casos-nacional` | Serie semanal nacional: `total` de OpenDengue y, tras su última fila, sospechosos del tablero, cada fila con `fuente`. Sin fila para la semana 53 de 2025 | global |
| `GET /api/casos-departamentales` | Probables y confirmados desacumulados sumados por departamento en toda la ventana (`probable_total`, `confirmado_total`, `semanas_con_dato_probable`, rango de años) | heavy |
| `GET /api/v1/spatial/current?week=&year=` | `iv` y `anomaly_sigma` por departamento (M1 y M2) | heavy |
| `GET /api/v1/temporal/{departamento_id}?anio=` | Serie de M1 y M2 de un departamento con banda histórica P25, mediana y P75 | global |
| `GET /api/v1/presion/current?week=&year=` | M3 por departamento, con `probable` y `confirmado` separados | heavy |
| `GET /api/v1/presion/temporal/{departamento_id}?anio=` | Serie de M3 de un departamento | global |
| `GET /api/v1/analisis/dengue?year=` | Dataset analítico anual (solo los años base) | heavy |
| `GET /api/v1/analisis/dengue/procedencia` | Trazabilidad de una observación (`year`, `week`, `dept`, `serie`) | heavy |
| `GET /api/v1/vigilancia/integridad` | M4 (con `week` y `year` juntos, o sin ellos) | heavy |
| `GET /api/nowcast-dengue` y `/retrospectivo` | Artefactos del nowcast | heavy |
| `GET /api/riesgo-nacional` | Clasificador retirado, solo como referencia | heavy |

**Ojo.** `/api/casos-departamentales` suma **toda** la ventana cargada y no una semana, porque el 87 a 93 % de las celdas departamento-semana está en cero y una sola semana suele salir casi vacía: es una elección de presentación, no una decisión cerrada.

### Endpoints respiratorios

**Qué es.** Las rutas de IRA, neumonías y virus.

**En el proyecto.**

| Ruta | Qué devuelve |
|---|---|
| `GET /api/ira/departamental` | Resumen por departamento del conteo notificado (heavy) |
| `GET /api/ira/temporal/{departamento_id}` | Serie por año; las semanas sin fila salen ausentes, nunca cero |
| `GET /api/ira/nacional` y `GET /api/neumonias/nacional` | Serie nacional del tablero desde 2025 (`unidad: conteo_notificado`, `fuente: minsal_tablero`) |
| `GET /api/neumonias/departamental`, `/temporal/{id}` y `/heatmap/{anio}` | Neumonías; el heatmap es una matriz departamento por semana y un año fuera de la ventana responde 400 |
| `GET /api/respiratorios/virus` | Catálogo virus × métrica × unidad (nacional) |
| `GET /api/respiratorios/temporal?virus=&metrica=` | Serie de un virus; `metrica` ∈ `detecciones`, `positividad`, `muestras_analizadas`, `muestras_positivas` (por defecto `detecciones`) |
| `GET /api/respiratorios/semana/{anio}/{semana}` | Todas las observaciones virales de una semana |
| `GET /api/respiratorios/cobertura` | Semanas con dato frente a 52 nominales y notas del corpus |

### Endpoints de alertas

**Qué es.** Las rutas de alertas de campo.

**En el proyecto.** `GET /api/alertas` (filtros `tipo`, `desde`, `hasta`, `incluir_inactivas`, `incluir_etiquetadas`, `departamento`, combinados con AND), `GET /api/alertas/feed.xml` (feed Atom), `POST /api/alertas` (crear, 201) y `PATCH /api/alertas/{id}` (editar). No hay `DELETE`. `GET` sin parámetros extra devuelve solo `activa = TRUE` y `etiqueta IS NULL`. Ver [Alertas de campo](05-modulos-descriptivos-y-alertas.md#alerta-de-campo).

### Códigos de estado

**Qué es.** Convención de respuestas de la API.

**En el proyecto.**

| Código | Cuándo |
|---|---|
| 200 | Normal, y también `disponible: false` |
| 201 | Alerta creada |
| 400 | Parámetro inválido en los endpoints respiratorios (semana fuera de 1–53, métrica no permitida, año fuera de la ventana) |
| 401 | Token de escritura ausente o incorrecto |
| 404 | Departamento o alerta inexistente; serie de virus sin datos |
| 422 | Parámetro inválido en los endpoints `/api/v1/` y en alertas (semana fuera de 1–53, `year` fuera de los años base, `departamento` o `tipo` no válidos, `week` sin `year`); cuerpo mal formado |
| 429 | Límite de tasa excedido |
| 500 | Error genérico de base de datos |
| 503 | Fallo de conexión, o `ALERTAS_TOKEN` sin definir |

**Ojo.** La convención **no es uniforme**: los endpoints `/api/v1/` responden 422 a un parámetro inválido y los respiratorios responden 400.

### Semana entre 1 y 53

**Qué es.** Validación del parámetro de semana.

**En el proyecto.** `week` se valida entre 1 y 53 (hay años MMWR de 53 semanas). En M1/M2, la semana 1 solo necesita su propia fila; las demás, la semana y la anterior, por la precipitación acumulada a dos semanas.

## 6. Pruebas del backend

### pytest y `TestClient`

**Qué es.** `pytest` es el ejecutor de pruebas de Python; `TestClient` de FastAPI llama a la app sin levantar un servidor.

**En el proyecto.** Versión `pytest==9.1.1`. La suite de la API cubre, entre otros, `test_rate_limiting.py`, `test_cors.py`, `test_security_headers.py`, `test_cache_headers.py`, `test_client_ip.py`, `test_degradacion_respiratorios.py`, `test_formulas_duplicadas.py` y los tests de endpoints de alertas, análisis, idoneidad, nowcast, presión, respiratorios y vigilancia. Las pruebas de ingesta (`backend/ingestion/tests/`) usan los fixtures de texto extraído.

### `conftest.py` y el límite de tasa en pruebas

**Qué es.** Archivo de configuración compartida de pytest.

**En el proyecto.** Fija `os.environ["RATE_LIMIT_ENABLED"] = "false"` con **asignación explícita, no `setdefault`** (issue #69): si quien desarrolla exportó el `.env` al shell, `RATE_LIMIT_ENABLED` ya valdría `true` y un `setdefault` no haría nada, dejando el limitador activo y provocando 429 intermitentes. `test_rate_limiting.py` lo reactiva con `monkeypatch` y `importlib.reload`.

### `monkeypatch` e `importlib.reload`

**Qué es.** Técnica para cambiar una variable de módulo en un test y recargar el módulo.

**En el proyecto.** Como `RATE_LIMIT_*` y `CORS_ALLOWED_ORIGINS` se leen en el import, un literal en el decorador impediría a los tests bajar el valor. Es «el mismo idiom» de `test_rate_limiting.py` y `test_cors.py`.

### Test de fórmulas duplicadas

**Qué es.** Prueba que compara las funciones copiadas a mano en `backend/api/` y `backend/ingestion/`.

**En el proyecto.** `test_formulas_duplicadas.py` falla si `ANIOS_CLIMA`, las fórmulas de `Iv` o el método de percentil se desincronizan. Ver [Duplicado deliberado](05-modulos-descriptivos-y-alertas.md#duplicado-deliberado-sin-paquete-compartido).

## 7. Configuración y contenedores

### Variables de entorno de la API

**Qué es.** Configuración por entorno, con `.env.example` como plantilla.

**En el proyecto.** `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` (en Render se inyectan con `fromDatabase`), las cuatro `POSTGRES_POOL_*`/`POSTGRES_CONNECT_TIMEOUT`, `CORS_ALLOWED_ORIGINS`, las cuatro `RATE_LIMIT_*`, `ALERTAS_TOKEN` y `SITIO_PUBLICO` (URL pública del sitio para el feed Atom; por defecto `https://epi-aetheris.dev`). `PUBLIC_API_URL` es del **frontend**: se embebe en el bundle en build-time (por defecto `http://localhost:8000`).

**Ojo.** `POSTGRES_HOST=db` solo resuelve **dentro** de la red de Docker Compose; desde el host, `db/aplicar_migraciones.py` lo trata como `localhost`.

### `Dockerfile` y `Dockerfile.render`

**Qué es.** Las dos imágenes del backend.

**En el proyecto.** `backend/Dockerfile` (Python 3.11-slim, contexto `./backend`, `--reload`, usuario `appuser` sin privilegios) es el de desarrollo con `docker-compose`. `backend/Dockerfile.render` tiene como contexto la **raíz del repositorio** para poder copiar `db/aplicar_migraciones.py` y `db/migrations/` (el `preDeployCommand` los necesita dentro de la imagen) y arranca sin `--reload`. «No mezclar los dos.»

### Usuario sin privilegios (`appuser`)

**Qué es.** Ejecutar el proceso sin ser `root` dentro del contenedor.

**En el proyecto.** Ambos Dockerfile crean `appuser` (`useradd --create-home --shell /bin/bash`) y hacen `chown -R` del directorio de la aplicación.

### `backend/model`

**Qué es.** Carpeta del backend que contiene solo un `.gitkeep`.

**En el proyecto.** El `README.md` la describe como destino de los artefactos del clasificador retirado («no versionados, ver issue #72»), pero el código real los lee de `backend/ingestion/data/interim/modelo/` (`MODELO_PATH` en `main.py`).
