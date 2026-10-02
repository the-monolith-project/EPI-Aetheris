// Dibujo de las curvas de la ficha de idoneidad (M1): una función de 0 a 1
// con la posición actual marcada. Devuelve una cadena SVG para que la misma
// función sirva al render del servidor (pasos de lectura) y al del cliente
// (laboratorio, que la vuelve a pedir en cada cambio). Los colores salen de
// clases CSS (`cv-*`), definidas en FichaEnriquecida.astro, para que sigan el
// tema claro y oscuro.

export interface MarcaEje {
  x: number;
  etiqueta: string;
}

export interface OpcionesCurva {
  f: (x: number) => number;
  desde: number;
  hasta: number;
  /** Posición actual sobre el eje x. */
  valor: number;
  marcas?: MarcaEje[];
  /** Texto bajo el eje, con la unidad. */
  etiquetaX: string;
  ancho?: number;
  alto?: number;
}

const MARGEN = { izquierda: 30, derecha: 12, arriba: 10, abajo: 34 };

function escapar(texto: string): string {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function r(n: number): string {
  return (Math.round(n * 10) / 10).toString();
}

/** SVG decorativo (aria-hidden): el valor se comunica además con texto. */
export function svgCurva(opciones: OpcionesCurva): string {
  const { f, desde, hasta, valor, marcas = [], etiquetaX } = opciones;
  const ancho = opciones.ancho ?? 240;
  const alto = opciones.alto ?? 160;
  const areaAncho = ancho - MARGEN.izquierda - MARGEN.derecha;
  const areaAlto = alto - MARGEN.arriba - MARGEN.abajo;
  const px = (x: number) =>
    MARGEN.izquierda + ((x - desde) / (hasta - desde)) * areaAncho;
  const py = (y: number) => MARGEN.arriba + (1 - y) * areaAlto;

  const pasos = 90;
  let trazo = '';
  for (let i = 0; i <= pasos; i += 1) {
    const x = desde + ((hasta - desde) * i) / pasos;
    trazo += `${i === 0 ? 'M' : 'L'}${r(px(x))} ${r(py(f(x)))}`;
  }
  const base = py(0);
  const relleno = `${trazo}L${r(px(hasta))} ${r(base)}L${r(px(desde))} ${r(base)}Z`;

  const enRango = Math.min(hasta, Math.max(desde, valor));
  const yValor = f(enRango);
  const xv = px(enRango);
  const yv = py(yValor);

  const guiasY = [0, 0.5, 1]
    .map(
      (y) =>
        `<line class="cv-guia" x1="${MARGEN.izquierda}" x2="${ancho - MARGEN.derecha}" y1="${r(py(y))}" y2="${r(py(y))}"/>` +
        `<text class="cv-texto" x="${MARGEN.izquierda - 5}" y="${r(py(y) + 3)}" text-anchor="end">${y === 0.5 ? '0,5' : y}</text>`,
    )
    .join('');

  const marcasX = marcas
    .map(
      (m) =>
        `<line class="cv-marca-eje" x1="${r(px(m.x))}" x2="${r(px(m.x))}" y1="${r(py(1))}" y2="${r(base)}"/>` +
        `<text class="cv-texto" x="${r(px(m.x))}" y="${r(base + 13)}" text-anchor="middle">${escapar(m.etiqueta)}</text>`,
    )
    .join('');

  return (
    `<svg viewBox="0 0 ${ancho} ${alto}" class="cv-svg" aria-hidden="true" focusable="false">` +
    guiasY +
    `<path class="cv-relleno" d="${relleno}"/>` +
    `<path class="cv-curva" d="${trazo}"/>` +
    marcasX +
    `<line class="cv-posicion" x1="${r(xv)}" x2="${r(xv)}" y1="${r(yv)}" y2="${r(base)}"/>` +
    `<line class="cv-posicion" x1="${MARGEN.izquierda}" x2="${r(xv)}" y1="${r(yv)}" y2="${r(yv)}"/>` +
    `<circle class="cv-punto" cx="${r(xv)}" cy="${r(yv)}" r="4.5"/>` +
    `<text class="cv-texto cv-eje-x" x="${r(MARGEN.izquierda + areaAncho / 2)}" y="${alto - 4}" text-anchor="middle">${escapar(etiquetaX)}</text>` +
    `</svg>`
  );
}
