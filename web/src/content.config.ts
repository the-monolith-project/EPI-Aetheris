import { existsSync } from 'node:fs';
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// Documentos propios de la Biblioteca pública (docs/biblioteca/), escritos
// para un lector externo. La documentación interna del equipo (docs/contexto/,
// docs/adr/, corridas) no alimenta esta colección: se sintetiza, no se
// reutiliza cruda. Orden, título, descripción y agrupación salen del
// frontmatter -- no hay un array paralelo en las páginas.
// Este codigo vive en dos sitios con arboles distintos: dentro del monorepo
// EPI-Aetheris (como web/, con docs/ un nivel por encima del paquete) y en el
// repo suelto aetheris-nitor, que se despliega solo y no tiene ningun padre
// del que colgar. Se prueba primero la copia propia del repo y se cae a la del
// monorepo. Sin esto, el repo suelto compila sin error pero deja la coleccion
// vacia, y las cinco paginas de /biblioteca -- todas enlazadas desde el pie
// -- se quedan sin generar y responden 404 en produccion.
const RUTA_PROPIA = new URL('../docs/biblioteca', import.meta.url);
const RUTA_MONOREPO = new URL('../../docs/biblioteca', import.meta.url);
const BASE_BIBLIOTECA = existsSync(RUTA_PROPIA) ? RUTA_PROPIA : RUTA_MONOREPO;

const biblioteca = defineCollection({
  loader: glob({
    pattern: '*.md',
    base: BASE_BIBLIOTECA,
  }),
  schema: z.object({
    titulo: z.string(),
    descripcion: z.string(),
    orden: z.number(),
    categoria: z.string().optional(),
  }),
});

export const collections = { biblioteca };
