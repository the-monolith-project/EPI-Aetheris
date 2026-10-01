// Primitivas SVG compartidas por las gráficas de la predicción de dengue
// (PanelNowcastDengue y ContrasteNowcastDengue): escalas, ejes, bandas y líneas
// dibujados a mano, para poder animar el abanico elemento a elemento.

export const SVG_NS = 'http://www.w3.org/2000/svg';
export const fmtNum = new Intl.NumberFormat('es-SV', {
  maximumFractionDigits: 0,
});
export const fmtFecha = new Intl.DateTimeFormat('es-SV', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});

export function fecha(iso: string): Date {
  return new Date(`${iso}T00:00:00`);
}

export function el(
  nombre: string,
  attrs: Record<string, string | number> = {},
): SVGElement {
  const nodo = document.createElementNS(SVG_NS, nombre);
  for (const [k, v] of Object.entries(attrs)) nodo.setAttribute(k, String(v));
  return nodo;
}

export interface Escalas {
  x: (t: number) => number;
  y: (v: number) => number;
  ancho: number;
  alto: number;
  margen: { arriba: number; abajo: number; izq: number; der: number };
}

export function crearSvg(
  ancho: number,
  alto: number,
  etiqueta: string,
): SVGSVGElement {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${ancho} ${alto}`);
  svg.setAttribute('class', 'w-full');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', etiqueta);
  return svg;
}

export function ejeY(svg: SVGElement, e: Escalas, maxV: number) {
  const niveles = [0, maxV / 2, maxV];
  for (const n of niveles) {
    const y = e.y(n);
    svg.appendChild(
      el('line', {
        x1: e.margen.izq,
        x2: e.ancho - e.margen.der,
        y1: y,
        y2: y,
        stroke: 'var(--color-border)',
        'stroke-width': 1,
      }),
    );
    const txt = el('text', {
      x: e.margen.izq - 8,
      y: y + 3,
      'text-anchor': 'end',
      'font-family': 'var(--font-sans)',
      'font-size': 9,
      fill: 'var(--color-ink-muted)',
    });
    (txt as SVGTextElement).style.fontVariantNumeric = 'tabular-nums';
    txt.textContent = fmtNum.format(Math.round(n));
    svg.appendChild(txt);
  }
}

export function bandaPath(
  e: Escalas,
  puntos: { t: number; lo: number; hi: number }[],
): string {
  const arriba = puntos.map((p) => `${e.x(p.t)},${e.y(p.hi)}`);
  const abajo = puntos
    .slice()
    .reverse()
    .map((p) => `${e.x(p.t)},${e.y(p.lo)}`);
  return `M${arriba.join(' L')} L${abajo.join(' L')} Z`;
}

// Una semana sin dato (v null, como la 53 de 2025 en el tablero) corta la
// línea en lugar de unirla con las vecinas.
export function linea(
  e: Escalas,
  puntos: { t: number; v: number | null }[],
  color: string,
  ancho: number,
  guiones?: string,
): SVGElement {
  let d = '';
  let enTramo = false;
  for (const p of puntos) {
    if (p.v === null || !Number.isFinite(p.v)) {
      enTramo = false;
      continue;
    }
    d += `${enTramo ? 'L' : 'M'}${e.x(p.t)},${e.y(p.v)} `;
    enTramo = true;
  }
  const pl = el('path', {
    d: d.trim(),
    fill: 'none',
    stroke: color,
    'stroke-width': ancho,
    'stroke-linejoin': 'round',
    'stroke-linecap': 'round',
  });
  if (guiones) pl.setAttribute('stroke-dasharray', guiones);
  return pl;
}
