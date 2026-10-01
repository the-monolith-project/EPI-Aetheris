// Enlaces laterales de las páginas de texto largo (DocumentoTexto): el resto
// de la Biblioteca, o los otros documentos legales.

export interface EnlaceDocumento {
  href: string;
  etiqueta: string;
  actual?: boolean;
}

export interface GrupoEnlaces {
  titulo?: string;
  enlaces: EnlaceDocumento[];
}

export interface NavegacionDocumento {
  titulo: string;
  grupos: GrupoEnlaces[];
}

const DOCUMENTOS_LEGALES: EnlaceDocumento[] = [
  { href: '/legal/terminos', etiqueta: 'Términos de uso' },
  { href: '/legal/privacidad', etiqueta: 'Privacidad' },
  { href: '/legal/aviso-legal', etiqueta: 'Aviso legal' },
];

export function navegacionLegal(actual: string): NavegacionDocumento {
  return {
    titulo: 'Documentos legales',
    grupos: [
      {
        enlaces: DOCUMENTOS_LEGALES.map((e) => ({
          ...e,
          actual: e.href === actual,
        })),
      },
    ],
  };
}

interface EntradaBiblioteca {
  id: string;
  data: { titulo: string; orden: number; categoria?: string };
}

/** Todos los documentos de la Biblioteca, agrupados por categoría y en orden. */
export function navegacionBiblioteca(
  entradas: EntradaBiblioteca[],
  idActual: string,
): NavegacionDocumento {
  const ordenadas = [...entradas].sort((a, b) => a.data.orden - b.data.orden);
  const grupos: GrupoEnlaces[] = [];
  for (const entrada of ordenadas) {
    const titulo = entrada.data.categoria ?? 'Documentos';
    let grupo = grupos.find((g) => g.titulo === titulo);
    if (!grupo) {
      grupo = { titulo, enlaces: [] };
      grupos.push(grupo);
    }
    grupo.enlaces.push({
      href: `/biblioteca/${entrada.id}`,
      etiqueta: entrada.data.titulo,
      actual: entrada.id === idActual,
    });
  }
  return { titulo: 'Biblioteca', grupos };
}
