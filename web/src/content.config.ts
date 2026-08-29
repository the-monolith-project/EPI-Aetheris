import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';

// Selección curada de docs/ del repo -- la fuente de verdad sigue siendo
// docs/ (no se duplica contenido, esto solo lee esos .md en build). Curada
// a propósito: docs/ tiene 40+ archivos escritos para el equipo (corridas
// experimentales, ADR internos de columnas), no todos sirven para alguien
// externo (estudiante/investigador) que se topa con el proyecto y quiere
// entender qué es y por qué se tomaron las decisiones clave. Ver ORDEN_BIBLIOTECA
// en web/src/pages/biblioteca/index.astro para agregar/quitar documentos.
const biblioteca = defineCollection({
  loader: glob({
    pattern: [
      'informe-cierre-rescate-prediccion.md',
      'experimento-validacion-leadtime-camino-ancho.md',
      'modulo-3-presion-epidemiologica.md',
      'adr/0005-clasificacion-total-opendengue.md',
      'adr/0010-versionar-volcado-de-datos-reales.md',
      'adr/0011-clasificacion-ira-departamental.md',
    ],
    base: new URL('../../docs', import.meta.url),
  }),
});

export const collections = { biblioteca };
