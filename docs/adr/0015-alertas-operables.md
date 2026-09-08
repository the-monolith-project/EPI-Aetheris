# 0015 - Alertas operables: archivo, creación autenticada y etiquetas

**Estado:** Aceptado (2026-09-07)

> Supercede las líneas de ADR 0013 que dejaban la autenticación, el
> formulario de administración y la creación HTTP fuera de alcance.
> Las alertas siguen siendo decisiones humanas: no se derivan de M1–M3
> ni del clasificador retirado. No hay `DELETE`. Migración:
> `db/migrations/0011_alertas_etiquetas_y_contenido_clinico.sql`.

## Contexto

ADR 0013 dejó la tabla `alertas` y el `GET` público listos para la
Expotécnica, con creación solo por SQL/seed. Eso ya no alcanza: el
equipo de vigilancia necesita emitir y apagar alertas desde la
aplicación, y el personal de salud necesita consultar **qué se emitió
y cuándo**, no solo lo vigente.

El despliegue de Render es público. Un `POST /api/alertas` sin
autenticación permitiría a cualquiera en internet publicar
indicaciones clínicas dirigidas a un médico rural. No hay tabla de
usuarios: guardar correo o nombre choca con la restricción de no
introducir datos personales.

Los cinco campos clínicos de ADR 0014 seguían en `NULL`. El contenido
que sí tiene cita en documentos públicos (VIGEPES, algoritmos OPS de
dengue, procedimiento de arbovirosis) debe transcribirse; lo que no
tiene fuente se deja `NULL`. No se inventa teléfono ni correo del
SIBASI.

El issue #61 (rate limiting de la API) sigue abierto. Abrir escritura
lo vuelve más urgente; **no se resuelve en este ADR**.

## Decisión

### Autenticación de escritura

- Secreto compartido en la variable de entorno `ALERTAS_TOKEN`.
- `POST /api/alertas` y `PATCH /api/alertas/{id}` exigen
  `Authorization: Bearer <token>` comparado con
  `os.environ["ALERTAS_TOKEN"]` mediante `secrets.compare_digest`
  (no `==`).
- Falta de cabecera y token incorrecto responden **401** y no
  escriben. No se distinguen: distinguirlos confirmaría a un atacante
  que el secreto existe pero no coincide.
- Si `ALERTAS_TOKEN` no está definido (o está vacío), la escritura
  responde **503** y no escribe. No hay valor por defecto en el
  código.
- El token no se versiona. En `render.yaml` se declara con
  `sync: false`. En `.env.example` va la clave vacía y un comentario.
- No hay tabla de usuarios ni CMS. El formulario mínimo vive en una
  ruta no enlazada desde la navegación (`/alertas/nueva`). El token
  no se guarda en `localStorage` salvo opción explícita del operador,
  con forma de cerrar sesión.
- **Sin `DELETE`.** Una alerta emitida es un hecho registrado: se
  desactiva (`activa=false`), no se borra. Eso hace posible el
  archivo.

### Lectura pública (contrato por defecto intacto)

`GET /api/alertas` sin parámetros extra sigue devolviendo solo filas
con `activa=TRUE` y `etiqueta IS NULL`. Filtro opcional `tipo`
inalterado. Los cinco campos clínicos siguen presentes como `str` o
`null`.

Parámetros opcionales, combinados con **AND** (ninguno implica al
otro):

- `desde=YYYY-MM-DD` y `hasta=YYYY-MM-DD`: solapamiento con la
  vigencia, no igualdad exacta.
- `incluir_inactivas=true`
- `incluir_etiquetadas=true`

Una fila inactiva **y** etiquetada necesita los dos flags para
aparecer. La portada y el service worker nunca piden
`incluir_etiquetadas=true`. `SHELL_MINIMO` permanece `['/', '/alertas']`:
ni el archivo ni el formulario de creación entran al shell ni se
precachean network-first.

Cuerpo malformado en escritura: **422**.

### Etiquetas

Columna `alertas.etiqueta TEXT NULL` con `CHECK`
(`test` | `simulacro` | `historica`). `NULL` es el caso normal de
producción. Cualquier valor no nulo queda fuera del GET por defecto.

Si una fila etiquetada se renderiza, lleva el rótulo inconfundible
`ALERTA DE PRUEBA — NO ACTUAR SOBRE ESTA INFORMACIÓN` dentro de la
tarjeta (texto, no un chip de color).

### Archivo

Vista compartible (`/alertas/archivo`, filtros en la URL, sobrevive
a un refresh) de lo emitido, filtrable por rango de fechas y `tipo`,
más reciente primero. Una fila no vigente muestra texto del tipo
`NO VIGENTE — venció el DD/MM/AAAA` (no solo color).

### Contenido clínico (transcripción citada, no redacción propia)

`UPDATE` por `tipo`, no por `id`:

- **dengue:** se llenan `definicion_caso`, `signos_alarma`,
  `criterios_referencia` y `que_notificar` desde VIGEPES §§33–35 /
  Tabla 1 y OPS *Algoritmos para el Manejo Clínico de los Casos de
  Dengue* (junio 2020, p. 10).
- **respiratorio:** se llenan `definicion_caso` y `que_notificar`
  desde VIGEPES §32 y Tabla 1. **`signos_alarma` y
  `criterios_referencia` quedan `NULL`.** VIGEPES es un documento de
  vigilancia, no una guía de manejo: define qué se notifica, no
  cuándo referir. No hay equivalente salvadoreño localizado de
  [OPS-ALG] para IRA/neumonías. Rellenarlos con signos derivados de
  la definición de caso fabricaría contenido clínico. El frontend ya
  omite el bloque cuando el valor es `NULL` (ADR 0014).
- **ambas:** `contacto_vigilancia` describe la ruta SIBASI /
  VIGEPES-01 / UVET (procedimiento de arbovirosis M02-VS-DISAM-PRO-42,
  Anexo 5). **Sin teléfono, sin correo, sin marcador `[PENDIENTE]`.**
  El número concreto del SIBASI del piloto no está en fuente pública
  citada; no se inventa. Falta a propósito, documentada aquí y en el
  PR, no en el valor persistido.

`AVISO_HONESTIDAD_ALERTAS` no cambia.

### Alternativas descartadas

* Tabla de usuarios / roles — descartado: exigiría persistir datos
  personales.
* `DELETE` HTTP — descartado: borra un hecho registrado y rompe el
  archivo.
* Varias etiquetas por alerta (tabla de unión) — no se justifica:
  nada en este alcance filtra por dos etiquetas a la vez.
* Resolver el issue #61 aquí — fuera de alcance; la escritura lo
  vuelve más urgente.
* Inventar criterios de referencia respiratorios o un teléfono
  SIBASI — choca con "nada de datos fabricados".

## Consecuencias

* Positivo: el equipo emite y apaga alertas sin SQL; el médico
  consulta el archivo de lo emitido; el GET público no cambia para
  consumidores existentes (portada, service worker).
* Positivo: las etiquetas de prueba no llegan a la vista de
  decisión salvo petición explícita, y si se renderizan no se
  confunden con una alerta real.
* Negativo: un token compartido no es autorización por persona. Quien
  lo tenga puede escribir. No hay revocación granular ni auditoría
  de quién pegó el token.
* Negativo: la superficie de escritura hace más urgente el issue #61
  (rate limiting). El issue #72 (artefactos del clasificador ausentes
  en Render) no se toca.
* Neutral: el teléfono/correo SIBASI sigue sin estar en la base. La
  ruta de notificación sí.
* Neutral: alguien del equipo debe cotejar los bloques clínicos
  contra los PDF citados (VIGEPES, OPS-ALG, ARBO) antes de tratarlos
  como texto de producción cerrado.
