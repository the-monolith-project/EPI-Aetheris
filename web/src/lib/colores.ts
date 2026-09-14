import chroma from 'chroma-js';

export const COLOR_SIN_DATO = '#e4e4e7';

// Rampas secuenciales basadas en ColorBrewer. No representan niveles de
// alarma: solo ordenan magnitudes continuas dentro de cada visualización.
export const RAMPA_PRESION = [
  '#f7fbff',
  '#c6dbef',
  '#6baed6',
  '#2171b5',
  '#08306b',
];
export const RAMPA_CASOS = [
  '#fcfbfd',
  '#dadaeb',
  '#9e9ac8',
  '#6a51a3',
  '#3f007d',
];

const escalaPresion = chroma.scale(RAMPA_PRESION).mode('lab').domain([0, 100]);
const escalaCasos = chroma.scale(RAMPA_CASOS).mode('lab').domain([0, 1]);

export function colorPresion(percentil: number | null): string {
  if (percentil === null) return COLOR_SIN_DATO;
  return escalaPresion(Math.min(100, Math.max(0, percentil))).hex();
}

export function colorCasos(conteo: number | null, maximo: number): string {
  if (conteo === null) return COLOR_SIN_DATO;
  if (maximo <= 0) return RAMPA_CASOS[0];
  return escalaCasos(Math.min(1, Math.max(0, conteo / maximo))).hex();
}

export function gradienteCss(rampa: string[]): string {
  return `linear-gradient(90deg, ${rampa.join(', ')})`;
}

// Paleta cualitativa (ColorBrewer Dark2): pensada para distinguir categorías,
// no magnitudes -- a diferencia de RAMPA_PRESION/RAMPA_CASOS, que ordenan un
// valor continuo. Se eligió por ser distinguible bajo las formas más
// comunes de daltonismo (protanopia/deuteranopia/tritanopia) y por tener
// contraste suficiente contra fondos claros, algo que variar solo la
// opacidad de un mismo color no garantiza (issue #129).
export const PALETA_CUALITATIVA = [
  '#1b9e77',
  '#d95f02',
  '#7570b3',
  '#e7298a',
  '#66a61e',
  '#e6ab02',
  '#a6761d',
  '#666666',
];

export function colorCualitativo(indice: number): string {
  const i =
    ((indice % PALETA_CUALITATIVA.length) + PALETA_CUALITATIVA.length) %
    PALETA_CUALITATIVA.length;
  return PALETA_CUALITATIVA[i];
}
