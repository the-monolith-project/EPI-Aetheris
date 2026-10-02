// Convención de términos: una palabra o frase en color distinto que, al pasar
// el cursor, enfocarla o tocarla, abre una descripción breve del glosario y un
// enlace a la sección de la Biblioteca donde se explica. Reemplaza a los
// «ver tal cosa en la Biblioteca» sueltos dentro del texto.
//
// En markdown se escribe como un enlace con el esquema `glosario:`:
//   [Iv](glosario:iv)
// y `convertirTerminos` lo transforma en el marcado de abajo. En los
// componentes Astro se usa <Termino clave="iv">Iv</Termino>, que genera el
// mismo marcado.

import type { EntradaGlosario } from './glosario';

/** Búsqueda en el glosario; se inyecta para que este módulo no tenga dependencias. */
export type BuscarEntrada = (clave: string) => EntradaGlosario | undefined;

function escapeHtml(texto: string): string {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export const ESQUEMA_TERMINO = 'glosario:';

let contador = 0;

/** Marcado de un término. Lanza si la clave no está en el glosario. */
export function marcadoTermino(
  buscar: BuscarEntrada,
  clave: string,
  textoHtml: string,
): string {
  const entrada = buscar(clave);
  if (!entrada) {
    throw new Error(`Termino: la clave «${clave}» no está en el glosario`);
  }
  contador += 1;
  const id = `termino-${clave}-${contador}`;
  return (
    `<span class="termino-glosario" data-termino="${escapeHtml(clave)}">` +
    `<button type="button" class="termino-glosario-boton" aria-expanded="false" aria-controls="${id}">${textoHtml}</button>` +
    `<span id="${id}" class="termino-glosario-nota" popover="manual" data-sin-busqueda>` +
    `<span class="termino-glosario-titulo">${escapeHtml(entrada.termino)}</span>` +
    `<span class="termino-glosario-definicion">${escapeHtml(entrada.definicion)}</span>` +
    `<a class="termino-glosario-enlace" href="${escapeHtml(entrada.enlace)}">Ver en la Biblioteca</a>` +
    `</span></span>`
  );
}

const ENLACE_TERMINO =
  /<a\s+href="glosario:([a-z0-9-]+)"[^>]*>([\s\S]*?)<\/a>/g;
const ENCABEZADO = /<h[1-6](?:\s[^>]*)?>[\s\S]*?<\/h[1-6]>/g;
const BLOQUE_PRE = /<pre[\s\S]*?<\/pre>/g;

/**
 * Convierte los enlaces `glosario:` del HTML ya renderizado. En encabezados y
 * bloques `<pre>` se deja solo el texto: un botón dentro del `<summary>` de un
 * acordeón chocaría con el clic que lo despliega.
 */
export function convertirTerminos(html: string, buscar: BuscarEntrada): string {
  const aTexto = (fragmento: string) =>
    fragmento.replace(ENLACE_TERMINO, (_c, _clave, texto) => texto);
  const protegidos: string[] = [];
  const resguardado = html
    .replace(ENCABEZADO, (m) => {
      protegidos.push(aTexto(m));
      return `\uE000${protegidos.length - 1}\uE000`;
    })
    .replace(BLOQUE_PRE, (m) => {
      protegidos.push(aTexto(m));
      return `\uE000${protegidos.length - 1}\uE000`;
    });
  const convertido = resguardado.replace(ENLACE_TERMINO, (_c, clave, texto) =>
    marcadoTermino(buscar, clave, texto),
  );
  return convertido.replace(
    /\uE000(\d+)\uE000/g,
    (_c, i) => protegidos[Number(i)],
  );
}
