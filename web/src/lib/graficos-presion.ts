// Gráficos de la ficha de M3: la recta del percentil (los valores del
// conjunto ordenados y el valor observado encima) y una versión pequeña del
// canal endémico (tres bandas por semana con los casos observados).
// Devuelven cadenas SVG decorativas (aria-hidden) para el servidor y el
// cliente; cada uso lleva su texto equivalente. Los colores de las bandas
// llegan por parámetro (las rampas viven en colores.ts) y el resto sale de
// clases CSS (`recta-*`, `canal-*`) definidas en FichaEnriquecida.astro.

import { escaparSvg, r } from './tira-anios.ts';

export interface OpcionesRecta {
  valores: readonly number[];
  observado: number;
  /** Texto bajo la marca del valor observado. */
  etiquetaObservado: string;
  cortes?: { valor: number; etiqueta: string }[];
  ancho?: number;
  alto?: number;
}

/**
 * Los valores del conjunto como puntos sobre una recta, apilados si se
 * repiten, y el valor observado como una marca vertical.
 */
export function svgRectaPercentil(opciones: OpcionesRecta): string {
  const { valores, observado, etiquetaObservado, cortes = [] } = opciones;
  const ancho = opciones.ancho ?? 520;
  const alto = opciones.alto ?? 120;
  const izquierda = 18;
  const derecha = 18;
  const ejeY = alto - 34;
  const todos = [...valores, observado, ...cortes.map((c) => c.valor)];
  let min = Math.min(...todos);
  let max = Math.max(...todos);
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const px = (v: number) =>
    izquierda + ((v - min) / (max - min)) * (ancho - izquierda - derecha);

  const repeticiones = new Map<number, number>();
  const puntos = [...valores]
    .sort((a, b) => a - b)
    .map((v) => {
      const n = repeticiones.get(v) ?? 0;
      repeticiones.set(v, n + 1);
      return `<circle class="recta-punto" cx="${r(px(v))}" cy="${r(ejeY - 8 - n * 11)}" r="4.5"/>`;
    })
    .join('');

  const marcasCorte = cortes
    .map(
      (c) =>
        `<line class="recta-corte" x1="${r(px(c.valor))}" x2="${r(px(c.valor))}" y1="8" y2="${r(ejeY)}"/>` +
        `<text class="recta-texto" x="${r(px(c.valor))}" y="${r(ejeY + 24)}" text-anchor="middle">${escaparSvg(c.etiqueta)}</text>`,
    )
    .join('');

  const xo = px(observado);
  const etiquetas = [min, max]
    .map(
      (v, i) =>
        `<text class="recta-texto" x="${r(px(v))}" y="${r(ejeY + 12)}" text-anchor="${i === 0 ? 'start' : 'end'}">${escaparSvg(String(Math.round(v * 10) / 10).replace('.', ','))}</text>`,
    )
    .join('');

  return (
    `<svg viewBox="0 0 ${ancho} ${alto}" class="tira-svg" aria-hidden="true" focusable="false">` +
    `<line class="recta-eje" x1="${izquierda}" x2="${ancho - derecha}" y1="${r(ejeY)}" y2="${r(ejeY)}"/>` +
    etiquetas +
    marcasCorte +
    puntos +
    `<line class="recta-observado" x1="${r(xo)}" x2="${r(xo)}" y1="4" y2="${r(ejeY + 4)}"/>` +
    `<text class="recta-texto recta-texto-observado" x="${r(Math.min(ancho - derecha, Math.max(izquierda, xo)))}" y="${alto - 2}" text-anchor="middle">${escaparSvg(etiquetaObservado)}</text>` +
    `</svg>`
  );
}

export interface SemanaCanal {
  semana: number;
  p50: number | null;
  p75: number | null;
  observado: number | null;
}

export interface OpcionesCanal {
  semanas: readonly SemanaCanal[];
  /** Colores de las bandas baja, media y alta. */
  colores: readonly [string, string, string];
  maximo?: number;
  ancho?: number;
  alto?: number;
}

/**
 * Canal endémico pequeño: por semana, una columna con las bandas hasta el
 * P50, entre P50 y P75 y por encima del P75; los casos observados como una
 * línea con puntos. Una semana sin línea base queda en blanco y una sin
 * observación corta la línea.
 */
export function svgCanalMini(opciones: OpcionesCanal): string {
  const { semanas, colores } = opciones;
  const ancho = opciones.ancho ?? 520;
  const alto = opciones.alto ?? 180;
  const m = { izquierda: 30, derecha: 10, arriba: 8, abajo: 22 };
  const valores = semanas.flatMap((s) =>
    [s.p75, s.observado].filter((v): v is number => v !== null),
  );
  const maximo = opciones.maximo ?? Math.max(1, ...valores) * 1.15;
  const areaAncho = ancho - m.izquierda - m.derecha;
  const areaAlto = alto - m.arriba - m.abajo;
  const base = m.arriba + areaAlto;
  const columna = areaAncho / Math.max(1, semanas.length);
  const py = (v: number) =>
    m.arriba + (1 - Math.min(maximo, Math.max(0, v)) / maximo) * areaAlto;
  const xc = (i: number) => m.izquierda + i * columna;

  const bandas = semanas
    .map((s, i) => {
      if (s.p50 === null || s.p75 === null) return '';
      const x = r(xc(i));
      const w = r(columna + 0.3);
      const yp50 = py(s.p50);
      const yp75 = py(s.p75);
      return (
        `<rect fill="${colores[0]}" x="${x}" y="${r(yp50)}" width="${w}" height="${r(base - yp50)}"/>` +
        `<rect fill="${colores[1]}" x="${x}" y="${r(yp75)}" width="${w}" height="${r(yp50 - yp75)}"/>` +
        `<rect fill="${colores[2]}" x="${x}" y="${m.arriba}" width="${w}" height="${r(yp75 - m.arriba)}"/>`
      );
    })
    .join('');

  let trazo = '';
  let abierto = false;
  const puntos: string[] = [];
  semanas.forEach((s, i) => {
    if (s.observado === null) {
      abierto = false;
      return;
    }
    const x = r(xc(i) + columna / 2);
    const y = r(py(s.observado));
    trazo += `${abierto ? 'L' : 'M'}${x} ${y}`;
    abierto = true;
    puntos.push(`<circle class="canal-punto" cx="${x}" cy="${y}" r="2.6"/>`);
  });

  const marcas = semanas
    .map((s, i) =>
      i % 4 === 0
        ? `<text class="tira-texto" x="${r(xc(i) + columna / 2)}" y="${alto - 6}" text-anchor="middle">${escaparSvg(String(s.semana))}</text>`
        : '',
    )
    .join('');

  return (
    `<svg viewBox="0 0 ${ancho} ${alto}" class="tira-svg" aria-hidden="true" focusable="false">` +
    `<rect class="canal-fondo" x="${m.izquierda}" y="${m.arriba}" width="${r(areaAncho)}" height="${r(areaAlto)}"/>` +
    bandas +
    `<line class="tira-guia" x1="${m.izquierda}" x2="${ancho - m.derecha}" y1="${r(base)}" y2="${r(base)}"/>` +
    `<text class="tira-texto" x="${m.izquierda - 4}" y="${r(base + 3)}" text-anchor="end">0</text>` +
    `<text class="tira-texto" x="${m.izquierda - 4}" y="${m.arriba + 6}" text-anchor="end">${Math.round(maximo)}</text>` +
    (trazo ? `<path class="canal-linea" d="${trazo}"/>` : '') +
    puntos.join('') +
    marcas +
    `</svg>`
  );
}
