// Anomalía climática continua, módulo M2. Port de calcular_baseline_semana,
// calcular_sigma y percentil del backend (idoneidad.py del monorepo), para que
// la ficha enriquecida de M2 muestre el cálculo paso a paso con las mismas
// cifras que la API. tests/unit/anomalia.test.ts lo compara con valores
// generados con el Python original. Si cambia uno, cambia el otro.

import { desviacionMuestral, percentil } from './estadistica.ts';

export { percentil };

/** Primer año de la línea base de M2. El último es el año en curso. */
export const ANIO_INICIO_BASELINE = 2014;
/** Con menos observaciones que esto en el conjunto no se calcula nada. */
export const MINIMO_POOL = 3;
/** Por debajo de esta desviación la anomalía queda sin dato. */
export const DESVIACION_MINIMA = 1e-9;

/** Iv por año y semana. Las claves pueden venir como texto (JSON). */
export type SerieIv = Record<string | number, Record<string | number, number>>;

export interface BaselineSemana {
  /** Iv de la misma semana en los otros años, en orden de año. */
  pool: number[];
  /** Años de los que salen los valores del pool, en el mismo orden. */
  anios: number[];
  mediana: number | null;
  desviacion: number | null;
  p25: number | null;
  p75: number | null;
}

/** Años de la línea base, de 2014 a `hasta`. */
export function corpusAnios(hasta: number): number[] {
  const anios: number[] = [];
  for (let a = ANIO_INICIO_BASELINE; a <= hasta; a += 1) anios.push(a);
  return anios;
}

/** Mediana, desviación muestral y cuantiles de un conjunto ya armado. */
export function resumirPool(
  pool: readonly number[],
): Omit<BaselineSemana, 'pool' | 'anios'> {
  if (pool.length < MINIMO_POOL) {
    return { mediana: null, desviacion: null, p25: null, p75: null };
  }
  return {
    mediana: percentil(pool, 50),
    desviacion: desviacionMuestral(pool),
    p25: percentil(pool, 25),
    p75: percentil(pool, 75),
  };
}

/**
 * Junta el Iv de la misma semana exacta (sin vecinas) en los años de
 * `corpus`, dejando fuera `anioExcluir`, y resume ese conjunto.
 */
export function calcularBaselineSemana(
  serie: SerieIv,
  anioExcluir: number,
  semana: number,
  corpus: readonly number[],
): BaselineSemana {
  const pool: number[] = [];
  const anios: number[] = [];
  for (const anio of corpus) {
    if (anio === anioExcluir) continue;
    const valor = serie[anio]?.[semana];
    if (typeof valor === 'number' && Number.isFinite(valor)) {
      pool.push(valor);
      anios.push(anio);
    }
  }
  return { pool, anios, ...resumirPool(pool) };
}

/** σ = (Iv − mediana) / desviación. Null sin línea base o con desviación casi nula. */
export function calcularSigma(
  valor: number | null,
  mediana: number | null,
  desviacion: number | null,
): number | null {
  if (valor === null || mediana === null || desviacion === null) return null;
  if (desviacion < DESVIACION_MINIMA) return null;
  return (valor - mediana) / desviacion;
}

/** Escala fija de color de la ficha: de −3 a 3 desviaciones. */
export const SIGMA_ESCALA = 3;

/** Semana de ejemplo de la ficha: semana 20, Iv de 2014 a 2025 y del año descrito. */
export const EJEMPLO_ANOMALIA = {
  semana: 20,
  anioDescrito: 2026,
  valor: 0.71,
  referencias: [
    { anio: 2014, iv: 0.52 },
    { anio: 2015, iv: 0.61 },
    { anio: 2016, iv: 0.58 },
    { anio: 2017, iv: 0.66 },
    { anio: 2018, iv: 0.49 },
    { anio: 2019, iv: 0.63 },
    { anio: 2020, iv: 0.57 },
    { anio: 2021, iv: 0.7 },
    { anio: 2022, iv: 0.55 },
    { anio: 2023, iv: 0.6 },
    { anio: 2024, iv: 0.64 },
    { anio: 2025, iv: 0.59 },
  ],
} as const;

export interface PresetAnomalia {
  clave: string;
  etiqueta: string;
  valor: number;
  /** Iv de los años de referencia; null es un año sin dato. */
  referencias: (number | null)[];
}

/** Años de referencia del laboratorio (ocho, los más recientes del ejemplo). */
export const ANIOS_LABORATORIO = [
  2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025,
] as const;

export const PRESETS_ANOMALIA: PresetAnomalia[] = [
  {
    clave: 'tipica',
    etiqueta: 'Semana típica',
    valor: 0.6,
    referencias: [0.49, 0.63, 0.57, 0.7, 0.55, 0.6, 0.64, 0.59],
  },
  {
    clave: 'inusual',
    etiqueta: 'Semana inusual',
    valor: 0.92,
    referencias: [0.49, 0.63, 0.57, 0.7, 0.55, 0.6, 0.64, 0.59],
  },
  {
    clave: 'poca-historia',
    etiqueta: 'Poca historia',
    valor: 0.71,
    referencias: [null, null, null, 0.7, null, null, 0.64, null],
  },
];
