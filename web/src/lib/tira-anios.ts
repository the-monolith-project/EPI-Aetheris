// Tira de barras por año de las fichas de M2 y M3: un grupo de barras por año
// de referencia y, apartado al final, el año que se describe. Encima, líneas
// horizontales (mediana, cortes) y una banda opcional. Devuelve una cadena
// SVG para que la misma función sirva al render del servidor (pasos de
// lectura) y al del cliente (laboratorio). Es decorativa (aria-hidden): cada
// uso lleva su equivalente en texto. Los colores salen de clases CSS
// (`tira-*`), definidas en FichaEnriquecida.astro.

export interface GrupoTira {
  etiqueta: string;
  /** Un valor por barra; null es un hueco de la fuente y se dibuja vacío. */
  valores: (number | null)[];
  /** El año descrito: va al final, separado del resto. */
  apartado?: boolean;
  /** Atenúa el grupo (por ejemplo, un año que no entra en el cálculo). */
  atenuado?: boolean;
}

export interface LineaTira {
  valor: number;
  etiqueta: string;
  tipo: 'mediana' | 'corte' | 'cuantil';
}

export interface OpcionesTira {
  grupos: GrupoTira[];
  /** Valor del borde superior del eje. */
  maximo: number;
  lineas?: LineaTira[];
  banda?: { desde: number; hasta: number };
  formato?: (n: number) => string;
  ancho?: number;
  alto?: number;
}

const MARGEN = { izquierda: 34, derecha: 84, arriba: 10, abajo: 24 };

export function escaparSvg(texto: string): string {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function r(n: number): string {
  return (Math.round(n * 10) / 10).toString();
}

function comaDecimal(n: number): string {
  return (Math.round(n * 100) / 100).toString().replace('.', ',');
}

export function svgTiraAnios(opciones: OpcionesTira): string {
  const { grupos, lineas = [], banda } = opciones;
  const ancho = opciones.ancho ?? 520;
  const alto = opciones.alto ?? 190;
  const formato = opciones.formato ?? comaDecimal;
  const maximo = opciones.maximo > 0 ? opciones.maximo : 1;
  const areaAncho = ancho - MARGEN.izquierda - MARGEN.derecha;
  const areaAlto = alto - MARGEN.arriba - MARGEN.abajo;
  const base = MARGEN.arriba + areaAlto;
  const py = (v: number) =>
    MARGEN.arriba + (1 - Math.min(maximo, Math.max(0, v)) / maximo) * areaAlto;

  const normales = grupos.filter((g) => !g.apartado);
  const apartados = grupos.filter((g) => g.apartado);
  // Un hueco de una ranura entre los años de referencia y el descrito.
  const ranuras =
    normales.length + (apartados.length > 0 ? apartados.length + 0.6 : 0);
  const ranura = areaAncho / Math.max(1, ranuras);
  const xGrupo = (i: number, apartado: boolean) =>
    MARGEN.izquierda +
    (apartado ? (normales.length + 0.6 + i) * ranura : i * ranura);

  const guias = [0, 0.5, 1]
    .map((f) => {
      const y = r(py(maximo * f));
      return (
        `<line class="tira-guia" x1="${MARGEN.izquierda}" x2="${ancho - MARGEN.derecha}" y1="${y}" y2="${y}"/>` +
        `<text class="tira-texto" x="${MARGEN.izquierda - 5}" y="${r(py(maximo * f) + 3)}" text-anchor="end">${escaparSvg(formato(maximo * f))}</text>`
      );
    })
    .join('');

  let fondo = '';
  if (banda) {
    const y1 = py(Math.max(banda.desde, banda.hasta));
    const y2 = py(Math.min(banda.desde, banda.hasta));
    fondo = `<rect class="tira-banda" x="${MARGEN.izquierda}" y="${r(y1)}" width="${r(areaAncho)}" height="${r(Math.max(0, y2 - y1))}"/>`;
  }

  const dibujarGrupo = (g: GrupoTira, i: number) => {
    const x0 = xGrupo(i, Boolean(g.apartado));
    const relleno = ranura * 0.72;
    const inicio = x0 + (ranura - relleno) / 2;
    const n = Math.max(1, g.valores.length);
    const separacion = n > 1 ? 1.5 : 0;
    const anchoBarra = (relleno - separacion * (n - 1)) / n;
    const clase = g.apartado ? 'tira-barra tira-barra-descrita' : 'tira-barra';
    const barras = g.valores
      .map((v, j) => {
        const x = inicio + j * (anchoBarra + separacion);
        if (v === null) {
          return `<rect class="tira-hueco" x="${r(x)}" y="${r(base - 4)}" width="${r(anchoBarra)}" height="4"/>`;
        }
        const y = py(v);
        return `<rect class="${clase}" x="${r(x)}" y="${r(y)}" width="${r(anchoBarra)}" height="${r(Math.max(1, base - y))}"/>`;
      })
      .join('');
    const texto = `<text class="tira-texto${g.apartado ? ' tira-texto-descrito' : ''}" x="${r(x0 + ranura / 2)}" y="${r(base + 13)}" text-anchor="middle">${escaparSvg(g.etiqueta)}</text>`;
    return `<g${g.atenuado ? ' class="tira-atenuado"' : ''}>${barras}${texto}</g>`;
  };

  const cuerpo =
    normales.map((g, i) => dibujarGrupo(g, i)).join('') +
    apartados.map((g, i) => dibujarGrupo(g, i)).join('');

  let separador = '';
  if (apartados.length > 0 && normales.length > 0) {
    const x = MARGEN.izquierda + (normales.length + 0.3) * ranura;
    separador = `<line class="tira-separador" x1="${r(x)}" x2="${r(x)}" y1="${MARGEN.arriba}" y2="${r(base)}"/>`;
  }

  // Las etiquetas de las líneas se separan si quedan encimadas.
  const ordenadas = [...lineas].sort((a, b) => b.valor - a.valor);
  let ultimaY = -Infinity;
  const trazos = ordenadas
    .map((l) => {
      const y = py(l.valor);
      const yTexto = Math.max(y + 3, ultimaY + 10);
      ultimaY = yTexto;
      return (
        `<line class="tira-linea tira-linea-${l.tipo}" x1="${MARGEN.izquierda}" x2="${ancho - MARGEN.derecha}" y1="${r(y)}" y2="${r(y)}"/>` +
        `<text class="tira-texto tira-texto-linea" x="${ancho - MARGEN.derecha + 4}" y="${r(yTexto)}">${escaparSvg(l.etiqueta)}</text>`
      );
    })
    .join('');

  return (
    `<svg viewBox="0 0 ${ancho} ${alto}" class="tira-svg" aria-hidden="true" focusable="false">` +
    fondo +
    guias +
    separador +
    cuerpo +
    trazos +
    `</svg>`
  );
}
