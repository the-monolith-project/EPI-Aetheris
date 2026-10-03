// Línea de tiempo de la ficha de M4: la última semana con dato de una serie,
// la semana de hoy y la distancia entre las dos en semanas epidemiológicas.
// Devuelve una cadena SVG decorativa (aria-hidden) para el servidor y el
// cliente; cada uso lleva su texto equivalente. Los colores salen de clases
// CSS (`linea-*`) definidas en FichaEnriquecida.astro.

import {
  antiguedadSerie,
  inicioSemanaEpi,
  semanaEpidemiologica,
} from './integridad.ts';
import { escaparSvg, r } from './tira-anios.ts';

const MS_DIA = 86_400_000;

function diaDe(anio: number, mes: number, dia: number): number {
  return Date.UTC(anio, mes - 1, dia) / MS_DIA;
}

export interface OpcionesLinea {
  ultima: readonly [number, number];
  hoy: Date | string;
  ancho?: number;
  alto?: number;
}

export function svgLineaTiempo(opciones: OpcionesLinea): string {
  const { ultima, hoy } = opciones;
  const ancho = opciones.ancho ?? 520;
  const alto = opciones.alto ?? 96;
  const m = { izquierda: 16, derecha: 16 };
  const actual = semanaEpidemiologica(hoy);
  const dUltima = inicioSemanaEpi(ultima[0], ultima[1]);
  const dHoy = inicioSemanaEpi(actual.anio, actual.semana);
  const anioDesde = Math.min(ultima[0], actual.anio);
  const anioHasta = Math.max(ultima[0], actual.anio);
  const desde = diaDe(anioDesde, 1, 1);
  const hasta = diaDe(anioHasta + 1, 1, 1);
  const px = (d: number) =>
    m.izquierda +
    ((d - desde) / (hasta - desde)) * (ancho - m.izquierda - m.derecha);
  const ejeY = 58;

  let anios = '';
  for (let a = anioDesde; a <= anioHasta + 1; a += 1) {
    const x = r(px(diaDe(a, 1, 1)));
    anios += `<line class="linea-anio" x1="${x}" x2="${x}" y1="${ejeY - 5}" y2="${ejeY + 5}"/>`;
    if (a <= anioHasta) {
      anios += `<text class="tira-texto" x="${r(px(diaDe(a, 7, 1)))}" y="${ejeY + 18}" text-anchor="middle">${a}</text>`;
    }
  }

  const semanas = antiguedadSerie(ultima, hoy).semanas ?? 0;
  const xu = px(dUltima);
  const xh = px(dHoy);
  const etiquetaUltima = `SE${ultima[1]} de ${ultima[0]}`;
  const etiquetaHoy = `hoy: SE${actual.semana} de ${actual.anio}`;
  const distancia = semanas === 1 ? '1 semana' : `${semanas} semanas`;

  return (
    `<svg viewBox="0 0 ${ancho} ${alto}" class="tira-svg" aria-hidden="true" focusable="false">` +
    `<line class="linea-eje" x1="${m.izquierda}" x2="${ancho - m.derecha}" y1="${ejeY}" y2="${ejeY}"/>` +
    anios +
    `<line class="linea-tramo" x1="${r(Math.min(xu, xh))}" x2="${r(Math.max(xu, xh))}" y1="${ejeY}" y2="${ejeY}"/>` +
    `<text class="tira-texto linea-distancia" x="${r((xu + xh) / 2)}" y="${ejeY - 10}" text-anchor="middle">${escaparSvg(distancia)}</text>` +
    `<circle class="linea-ultima" cx="${r(xu)}" cy="${ejeY}" r="5"/>` +
    `<text class="tira-texto" x="${r(xu)}" y="14" text-anchor="${xu < ancho / 2 ? 'start' : 'end'}">${escaparSvg(etiquetaUltima)}</text>` +
    `<line class="linea-guia" x1="${r(xu)}" x2="${r(xu)}" y1="18" y2="${ejeY - 6}"/>` +
    `<rect class="linea-hoy" x="${r(xh - 4)}" y="${ejeY - 4}" width="8" height="8"/>` +
    `<text class="tira-texto linea-texto-hoy" x="${r(xh)}" y="${alto - 2}" text-anchor="${xh > ancho / 2 ? 'end' : 'start'}">${escaparSvg(etiquetaHoy)}</text>` +
    `</svg>`
  );
}
