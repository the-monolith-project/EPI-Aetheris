import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// Documentos propios de la Biblioteca pública (docs/biblioteca/), escritos
// para un lector externo. La documentación interna del equipo (docs/contexto/,
// docs/adr/, corridas) no alimenta esta colección: se sintetiza, no se
// reutiliza cruda. Orden, título, descripción y agrupación salen del
// frontmatter -- no hay un array paralelo en las páginas.
const biblioteca = defineCollection({
  loader: glob({
    pattern: '*.md',
    base: new URL('../../docs/biblioteca', import.meta.url),
  }),
  schema: z.object({
    titulo: z.string(),
    descripcion: z.string(),
    orden: z.number(),
    categoria: z.string().optional(),
  }),
});

export const collections = { biblioteca };
