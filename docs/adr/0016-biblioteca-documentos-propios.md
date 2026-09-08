# 0016 - Documentos propios para la Biblioteca pública

**Estado:** Aceptado (2026-09-08)

> Aceptado para la sección pública `/biblioteca`. Los documentos internos
> de `docs/` siguen siendo la fuente de verdad del equipo; la Biblioteca
> publica una síntesis escrita para un lector externo, con frontmatter.

## Contexto

La Biblioteca (`web/src/pages/biblioteca/`) renderizaba seis Markdown
internos crudos de `docs/` (informe de cierre, experimento de lead time,
módulo 3, ADR 0005/0010/0011) vía un `glob` loader. Esos archivos se
escribieron para el equipo: corridas, columnas, CHECKs. No traen
frontmatter, así que el índice mantenía un array paralelo
(`ORDEN_BIBLIOTECA`) con descripciones manuales. Renderizados tal cual,
no cuentan el proyecto de afuera hacia adentro y mezclan el tono de
trabajo interno con la cara pública del sitio.

Reutilizar y "curar" esos `.md` se evaluó y se descarta: el lector
externo necesita un relato, un catálogo de funciones y un solo lugar
para los deslindes éticos, no una selección de ADR.

El coordinador cerró además (2026-09-07) que el copy del sitio no debe
sonar a disculpa permanente: historia, funciones, fuentes y arquitectura
van en voz afirmativa; los deslindes viven una vez, en su documento.

## Decisión

**A. Colección propia en `docs/biblioteca/`.** Markdown con frontmatter
`titulo` (string), `descripcion` (string), `orden` (number) y
`categoria` (string, opcional). El loader de Astro apunta a ese glob.
El índice ordena y agrupa por esos campos; se elimina
`ORDEN_BIBLIOTECA`. La vista de documento muestra `titulo` y
`descripcion` en la cabecera del artículo.

**B. Síntesis, no duplicación ni mudanza.** Los `.md` internos no se
borran ni se mueven. La Biblioteca los sintetiza para un lector
externo. Si un hecho cambia, se actualiza primero `docs/contexto/`,
ADR o el módulo correspondiente; los documentos públicos se alinean
después. Cifras, fechas y fuentes salen del repositorio, no se inventan.

**C. "Sensibilidad y honestidad" es el hogar canónico de los
deslindes.** Un solo documento argumenta: el sistema no diagnostica ni
predice; el clasificador está retirado; solo datos agregados públicos;
nada fabricado; las guías OPS/OMS/MINSAL citadas sí están permitidas;
coexistencia temporal no es causalidad; métricas y fallos visibles;
aporte de ingeniería, no novedad epidemiológica. El resto de la
Biblioteca (y, en una pasada posterior, el frontend) enlaza ahí en vez
de repetir el estribillo en cada pantalla.

**D. Rutas.** Cada archivo `NN-slug.md` se sirve en `/biblioteca/NN-slug`.
No se conservan las rutas viejas
(`/biblioteca/adr/...`, `/biblioteca/rescate-prediccion/...`,
`/biblioteca/experimentos/...`, `/biblioteca/modulos-camino-ancho/...`):
no había enlaces internos a documentos concretos de esa colección, solo
a `/biblioteca`.

### Alternativas descartadas

* Seguir renderizando los `.md` internos con descripciones a mano —
  descartado: el tono y el recorte no sirven a un lector externo, y el
  array paralelo se desincroniza.
* Copiar los internos a `docs/biblioteca/` con un envoltorio —
  descartado: duplica el mantenimiento y deja visible el formato de
  corrida/ADR.
* Un único documento largo — descartado: el índice por categoría es
  más usable y permite enlazar el deslinde sin arrastrar historia y
  fórmulas.

## Consecuencias

* Positivo: la cara pública explica el proyecto en el orden narrativo
  (qué es → historia → funciones → fuentes → sensibilidad →
  arquitectura) sin exigir que el lector cruce ADR.
* Positivo: el frontend deja de conocer ids de rutas internas de
  `docs/`.
* Negativo: dos capas de prosa que hay que mantener alineadas cuando
  cambia un hecho (por ejemplo, si se implementa M4). Aceptado: la
  capa interna sigue siendo la autoridad (precedencia de `AGENTS.md`
  §4).
* Neutral: `web/public/sw.js` no incluye rutas de Biblioteca; no
  cambia. No hay migración de esquema.

## Migración

Ninguna en `db/migrations/`. Cambio de contenido y de colección Astro.
