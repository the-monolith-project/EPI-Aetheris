# 0014 - Enfoque dual: panorama y análisis, sin modo con estado

**Estado:** Aceptado (2026-09-07)

> El sitio atiende dos usos distintos con una sola arquitectura de
> información. Se rechaza el interruptor de "modo" en la barra. Se añaden
> campos clínicos opcionales a `alertas` y caching offline con sello de
> frescura. Migración: `db/migrations/0010_alertas_campos_clinicos.sql`.

**Nota de estado (2026-09-07):** La consecuencia "la API de alertas sigue
siendo de solo lectura" queda superada por ADR 0015. El resto de este
ADR (enfoque dual, campos clínicos como contenedores, service worker)
sigue vigente.

## Contexto

El piloto tiene dos usos que no se parecen:

- **Consulta.** El personal de salud en una unidad rural pregunta qué hay
  vigente y qué hacer con el paciente que tiene enfrente. Poco tiempo,
  mala conexión, cero tolerancia a jerga estadística.
- **Análisis.** El equipo de vigilancia, investigadores externos y
  cualquier curioso quieren las series descriptivas por departamento.

La propuesta inicial fue un botón en la barra que alternara entre dos
enfoques. Se descartó: un modo con estado no se descubre, la persona
olvida en cuál está, los enlaces compartidos abren distinto según quién
los reciba, y obliga a mantener dos arquitecturas sincronizadas. Además
"investigadores externos" no encajan en la cara simple — son usuarios
intensivos de la cara de análisis.

## Decisión

**1. Dos caras como secciones, no como modo.**

La navegación pasa a `Inicio · Alertas · Análisis · Biblioteca ·
Sugerencias`. `/dengue` y `/respiratorio` se agrupan bajo un
índice nuevo, `/analisis`, en vez de ocupar una entrada cada una.
Ninguna cara esconde a la otra y no hay estado persistido: un enlace
compartido se comporta igual para cualquiera.

La portada añade dos puertas explícitas ("Personal de salud" →
`/alertas`, "Investigación y datos" → `/analisis`) que son enlaces
normales, y una tira con las alertas vigentes. Si el backend no responde,
la tira se oculta y la portada sigue teniendo sentido.

**2. Campos clínicos opcionales en `alertas`.**

Se añaden cinco columnas `TEXT` nulas: `definicion_caso`,
`signos_alarma`, `criterios_referencia`, `que_notificar` y
`contacto_vigilancia`. La API las expone siempre (clave presente, valor
posiblemente `null`); la vista muestra cada bloque solo si tiene
contenido.

Se entrega el **contenedor vacío, no el contenido**. Ese texto es
clínico o es un dato de contacto real: lo redacta y carga el equipo con
fuente MINSAL/OPS atribuida. Inventarlo sería la peor versión de esta
función. Las tres filas demo quedan con estos campos en `NULL`.

**3. Caching offline con sello de frescura visible.**

`web/public/sw.js` (escrito a mano, sin dependencias) cachea el shell con
stale-while-revalidate y `GET /api/alertas` con **network-first**: una
alerta que el equipo ya apagó tiene consecuencia clínica, así que la red
siempre gana y el cache es último recurso.

Cuando la respuesta sale del cache, el service worker la marca con
`_desde_cache: true` **en el cuerpo JSON** y `/alertas` muestra "sin
conexión — mostrando lo último guardado". El sello no es adorno: sin él,
un dato guardado hace días se ve idéntico a uno recién traído.

La marca va en el cuerpo y no en una cabecera porque la API vive en otro
origen: el navegador filtra por CORS las cabeceras que la página puede
leer, y una cabecera propia puesta por el service worker llega pero es
invisible — comprobado, ni siquiera añadiendo
`Access-Control-Expose-Headers` a la respuesta sintética.
`_desde_cache` es un marcador de transporte del service worker, no un
campo del contrato de `/api/alertas`: el backend nunca lo emite.

**4. Novedad, impresión y compartir, todo sin backend.**

`localStorage` guarda qué alertas ya vio esta persona en este navegador,
para marcar las nuevas; la primera visita no marca nada, porque sin
referencia previa "nueva" no significa nada. `window.print()` con
`@media print` produce el cartel para sala de espera, sin dependencia de
PDF. `navigator.share()` con respaldo a copiar el enlace comparte una
alerta por su ancla `#alerta-<id>`.

## Alternativas descartadas

- **Interruptor de modo en la barra.** Ver Contexto.
- **Pantalla "mi municipio hoy".** No hay dato que la sostenga: la
  ventana cargada llega hasta 2023 y `regiones.nivel_admin = 2`
  (municipio) está reservado, sin filas. Una pantalla titulada "hoy"
  sobre datos de 2023 es exactamente lo que el estatuto de honestidad
  del proyecto existe para evitar.
- **Tendencia "esta semana contra las 4 previas".** Mismo motivo: no
  existe "esta semana" en el conjunto cargado.
- **Formulario de feedback propio.** Exigiría tabla nueva, endpoint de
  escritura y guardar texto de terceros. Ya estaba decidido en contra
  (nota de `/sugerencias` en `Layout.astro`; ADR 0013, "sin
  POST/PUT/DELETE"). El feedback sigue por GitHub Issues.

## Consecuencias

- La API de alertas sigue siendo de solo lectura. No se abre superficie
  de escritura.
- Los cinco campos clínicos quedan vacíos hasta que el equipo los cargue.
  Esa carga es un `UPDATE`, no una reconstrucción.
- El service worker introduce una capa de cache: al desplegar una versión
  nueva hay que subir `VERSION` en `sw.js` para invalidar el shell viejo.
- El texto de consejos de prevención en la portada queda pendiente y debe
  citar fuente oficial, igual que las `indicaciones` de ADR 0013.
