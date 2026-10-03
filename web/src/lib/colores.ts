import chroma from 'chroma-js';

export const COLOR_SIN_DATO = '#e4e4e7';
export const COLOR_DATO_DISPONIBLE = '#256abf';

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

// Rampa de la capa de idoneidad biofísica (Iv) del mapa y de la ficha de M1.
export const RAMPA_IV = ['#e0d6f7', '#bfa6ef', '#9a75e0', '#6f42c1', '#4a1a8a'];

const escalaIv = chroma.scale(RAMPA_IV).mode('lab').domain([0, 1]);

/** Color de un Iv sobre la escala fija de 0 a 1. */
export function colorIv(iv: number | null): string {
  if (iv === null) return COLOR_SIN_DATO;
  return escalaIv(Math.min(1, Math.max(0, iv))).hex();
}

// Rampa divergente de la capa de anomalía climática (M2): azul, gris,
// naranja. Sin rojo: la anomalía es un valor continuo, no el cruce de un umbral.
export const RAMPA_ANOMALIA = [
  '#3a6ea5',
  '#8fb8d9',
  '#e5e5e5',
  '#e8b86d',
  '#b5651d',
];

const escalaAnomalia = chroma
  .scale(RAMPA_ANOMALIA)
  .mode('lab')
  .domain([-3, -1.5, 0, 1.5, 3]);

/** Color de una anomalía sobre la escala fija de −3 a 3 desviaciones. */
export function colorAnomalia(sigma: number | null): string {
  if (sigma === null) return COLOR_SIN_DATO;
  return escalaAnomalia(Math.min(3, Math.max(-3, sigma))).hex();
}

// Rampa de las capas de presión epidemiológica (M3) del mapa: un tono por
// categoría (baja, media, alta), verdes de la marca separados en luminosidad.
// Distinta de RAMPA_PRESION, que ordena el percentil continuo del heatmap.
export const RAMPA_PRESION_CATEGORIA = ['#e8f3ef', '#4fae95', '#0b3d33'];

const INDICE_CATEGORIA = { baja: 0, media: 1, alta: 2 } as const;

/** Color de la categoría de presión de una semana. */
export function colorCategoriaPresion(
  categoria: 'baja' | 'media' | 'alta' | null,
): string {
  if (categoria === null) return COLOR_SIN_DATO;
  return RAMPA_PRESION_CATEGORIA[INDICE_CATEGORIA[categoria]];
}

// Capa de integridad de la vigilancia (M4): sin dato esa semana, dato
// presente, dato presente en un boletín que no cuadra. Tres estados, no una
// escala; la leyenda y el tooltip los nombran además con texto.
export const RAMPA_CONFIANZA = ['#d4d4d8', '#5b7c99', '#c4a35a'];

const INDICE_ESTADO = { sin_dato: 0, presente: 1, no_cuadra: 2 } as const;

export function colorIntegridad(
  estado: 'sin_dato' | 'presente' | 'no_cuadra',
): string {
  return RAMPA_CONFIANZA[INDICE_ESTADO[estado]];
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
