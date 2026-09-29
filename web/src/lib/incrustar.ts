export interface OpcionesIncrustacion {
  src: string;
  titulo: string;
  alto: number;
}

function escaparAtributo(texto: string): string {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/** Código <iframe> listo para pegar en otra página. */
export function codigoIncrustacion({
  src,
  titulo,
  alto,
}: OpcionesIncrustacion): string {
  return `<iframe src="${escaparAtributo(src)}" title="${escaparAtributo(titulo)}" width="100%" height="${Math.round(alto)}" loading="lazy" style="border:0"></iframe>`;
}
