// Fichas enriquecidas de la Biblioteca (ruta /biblioteca/fichas/[slug]).
// Cada ficha complementa a un documento con acordeones, que sigue siendo la
// referencia formal. Para sumar una ficha: crear su componente en src/fichas/,
// añadirla aquí y enlazarla desde el documento («ver ficha enriquecida de …»).

export interface MetadatosFicha {
  slug: string;
  titulo: string;
  subtitulo: string;
  etiquetas: string[];
  descripcion: string;
  documentacion: { href: string; etiqueta: string };
}

export const FICHAS: MetadatosFicha[] = [
  {
    slug: 'm1-idoneidad-biofisica',
    titulo: 'Idoneidad biofísica (M1)',
    subtitulo:
      'Cómo el clima de una semana se convierte en un número de 0 a 1 y en el color de un departamento.',
    etiquetas: ['Módulo M1', 'Variable compuesta', 'Clima', 'Escala de 0 a 1'],
    descripcion:
      'Recorrido de la fuente al mapa: de dónde salen la temperatura, la humedad y la lluvia, cómo cada una pasa por su función, cómo se combinan en el Iv y cómo ese valor pinta un departamento. Al final, un laboratorio para mover los valores.',
    documentacion: {
      href: '/biblioteca/03-funciones#m1-idoneidad-biofísica-iv',
      etiqueta: 'Ver documentación de M1',
    },
  },
];

export const RUTA_FICHAS = '/biblioteca/fichas';

export function rutaFicha(slug: string): string {
  return `${RUTA_FICHAS}/${slug}`;
}

export function fichaPorSlug(slug: string): MetadatosFicha | undefined {
  return FICHAS.find((f) => f.slug === slug);
}
