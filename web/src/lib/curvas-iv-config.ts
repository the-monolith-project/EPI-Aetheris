// Las tres funciones del Iv con lo que hace falta para dibujarlas: la ficha de
// M1 las usa en los pasos de lectura (servidor) y en el laboratorio (cliente).
import { svgCurva } from './curvas-iv';
import { fH, fR, fT, formatearNumero, type EntradasIv } from './idoneidad';

export type ClaveFactor = 'ft' | 'fr' | 'fh';

export interface ConfigCurva {
  clave: ClaveFactor;
  nombre: string;
  titulo: string;
  /** Qué hace la función, en una frase. */
  resumen: string;
  formula: string;
  entrada: keyof EntradasIv;
  etiquetaEntrada: string;
  unidad: string;
  decimalesEntrada: number;
  f: (x: number) => number;
  desde: number;
  hasta: number;
  paso: number;
  marcas: { x: number; etiqueta: string }[];
  etiquetaX: string;
}

export const CURVAS_IV: Record<ClaveFactor, ConfigCurva> = {
  ft: {
    clave: 'ft',
    nombre: 'fT',
    titulo: 'Temperatura',
    resumen:
      'Curva de Brière. Vale 0 por debajo de 16 °C y por encima de 38 °C, y llega a su máximo cerca de los 32,5 °C.',
    formula: 'fT(T) = c · T · (T − 16) · √(38 − T)',
    entrada: 'temperatura',
    etiquetaEntrada: 'Temperatura media',
    unidad: '°C',
    decimalesEntrada: 1,
    f: fT,
    desde: 10,
    hasta: 42,
    paso: 0.5,
    marcas: [
      { x: 16, etiqueta: '16' },
      { x: 38, etiqueta: '38' },
    ],
    etiquetaX: 'Temperatura media (°C)',
  },
  fr: {
    clave: 'fr',
    nombre: 'fR',
    titulo: 'Lluvia',
    resumen:
      'Logística sobre la lluvia acumulada en dos semanas. Vale 0,5 con 30 mm y se acerca a 1 con lluvias más abundantes.',
    formula: 'fR(R) = 1 / (1 + e^(−0,1 · (R − 30)))',
    entrada: 'lluvia',
    etiquetaEntrada: 'Lluvia de dos semanas',
    unidad: 'mm',
    decimalesEntrada: 0,
    f: fR,
    desde: 0,
    hasta: 150,
    paso: 1,
    marcas: [{ x: 30, etiqueta: '30' }],
    etiquetaX: 'Lluvia de dos semanas (mm)',
  },
  fh: {
    clave: 'fh',
    nombre: 'fH',
    titulo: 'Humedad',
    resumen:
      'Rampa lineal que penaliza la humedad relativa por debajo del 50 %. Desde el 50 % vale 1.',
    formula: 'fH(HR) = mín(1, máx(0, HR / 50))',
    entrada: 'humedad',
    etiquetaEntrada: 'Humedad relativa media',
    unidad: '%',
    decimalesEntrada: 0,
    f: fH,
    desde: 0,
    hasta: 100,
    paso: 1,
    marcas: [{ x: 50, etiqueta: '50' }],
    etiquetaX: 'Humedad relativa media (%)',
  },
};

export const ORDEN_FACTORES: ClaveFactor[] = ['ft', 'fr', 'fh'];

/** SVG de una de las tres curvas con la posición `valor` marcada. */
export function curvaIv(clave: ClaveFactor, valor: number): string {
  const c = CURVAS_IV[clave];
  return svgCurva({
    f: c.f,
    desde: c.desde,
    hasta: c.hasta,
    valor,
    marcas: c.marcas,
    etiquetaX: c.etiquetaX,
  });
}

/** «27 °C», «40 mm», «65 %». */
export function textoEntrada(clave: ClaveFactor, valor: number): string {
  const c = CURVAS_IV[clave];
  return `${formatearNumero(valor, c.decimalesEntrada)}\u00a0${c.unidad}`;
}
