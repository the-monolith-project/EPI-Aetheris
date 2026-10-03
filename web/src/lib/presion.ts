// Presión epidemiológica relativa, módulo M3. Port de calcular_presion,
// rango_percentil y categorizar del backend (presion.py del monorepo), para
// que la ficha enriquecida de M3 muestre el cálculo paso a paso con las mismas
// cifras que la API. tests/unit/presion.test.ts lo compara con valores
// generados con el Python original. Si cambia uno, cambia el otro.

import { percentil, redondear } from './estadistica.ts';

/** Años de referencia de M3. 2020 no entra. */
export const ANIOS_BASE_PRESION = [2018, 2019, 2021, 2022, 2023] as const;
/** Semanas a cada lado de la semana descrita. */
export const VENTANA = 1;
/** Años de referencia con alguna observación en la ventana que hacen falta. */
export const MINIMO_ANIOS = 3;
/** Última semana epidemiológica posible de un año. */
export const SEMANA_MAXIMA = 53;

export const NOTA_SIN_BASELINE =
  'sin datos suficientes para baseline (menos de 3 años base con observaciones en la ventana ±1)';
export const NOTA_HUECO =
  'sin observación registrada para esta semana/año en esta serie (hueco real de la fuente MINSAL, no un cero)';

export type Categoria = 'baja' | 'media' | 'alta';

/** Casos por año y semana. Una semana ausente es un hueco, no un cero. */
export type SerieCasos = Record<
  string | number,
  Record<string | number, number | null>
>;

export interface ResultadoPresion {
  casos_observados: number | null;
  percentil: number | null;
  categoria: Categoria | null;
  p50_baseline: number | null;
  p75_baseline: number | null;
  n_obs_baseline: number;
  anios_baseline: number;
  nota?: string;
}

export interface PoolPresion {
  /** Casos de la ventana en los otros años, en orden de año y semana. */
  pool: number[];
  /** Por año de referencia, los casos de cada semana de la ventana (null = hueco). */
  porAnio: {
    anio: number;
    semanas: { semana: number; casos: number | null }[];
  }[];
  /** Años de referencia con al menos una observación en la ventana. */
  aniosConDato: number;
}

/** Semanas de la ventana ±`ventana`, sin pasar de un año a otro. */
export function semanasEnVentana(
  semana: number,
  ventana: number = VENTANA,
): number[] {
  const semanas: number[] = [];
  for (let s = semana - ventana; s <= semana + ventana; s += 1) {
    if (s >= 1 && s <= SEMANA_MAXIMA) semanas.push(s);
  }
  return semanas;
}

function leer(serie: SerieCasos, anio: number, semana: number): number | null {
  const valor = serie[anio]?.[semana];
  return typeof valor === 'number' && Number.isFinite(valor) ? valor : null;
}

/** Junta los casos de la ventana en los años de referencia, sin el año descrito. */
export function construirPool(
  serie: SerieCasos,
  anio: number,
  semana: number,
  aniosBase: readonly number[] = ANIOS_BASE_PRESION,
  ventana: number = VENTANA,
): PoolPresion {
  const pool: number[] = [];
  const porAnio: PoolPresion['porAnio'] = [];
  let aniosConDato = 0;
  const semanas = semanasEnVentana(semana, ventana);
  for (const base of aniosBase) {
    if (base === anio) continue;
    const fila = semanas.map((s) => ({
      semana: s,
      casos: leer(serie, base, s),
    }));
    const observadas = fila.filter((f) => f.casos !== null);
    if (observadas.length > 0) aniosConDato += 1;
    for (const f of observadas) pool.push(f.casos as number);
    porAnio.push({ anio: base, semanas: fila });
  }
  return { pool, porAnio, aniosConDato };
}

/**
 * Posición de `valor` en el conjunto, de 0 a 100: la inversa del percentil
 * con interpolación lineal. Un empate toma el punto medio del tramo empatado
 * y lo que queda fuera del rango satura en 0 o en 100.
 */
export function rangoPercentil(pool: readonly number[], valor: number): number {
  const s = [...pool].sort((a, b) => a - b);
  const n = s.length;
  if (n === 0) throw new Error('rangoPercentil: el conjunto está vacío');
  if (valor < s[0]) return 0;
  if (valor > s[n - 1]) return 100;
  if (n === 1) return 50;
  const primero = s.indexOf(valor);
  if (primero !== -1) {
    const ultimo = s.lastIndexOf(valor);
    return (((primero + ultimo) / 2) * 100) / (n - 1);
  }
  let i = 0;
  while (s[i + 1] < valor) i += 1;
  const posicion = i + (valor - s[i]) / (s[i + 1] - s[i]);
  return (posicion * 100) / (n - 1);
}

/** Hasta el P50, baja; hasta el P75, media; por encima, alta. El corte cae hacia abajo. */
export function categorizar(
  valor: number,
  p50: number,
  p75: number,
): Categoria {
  if (valor <= p50) return 'baja';
  if (valor <= p75) return 'media';
  return 'alta';
}

/** Presión de una semana de un año, con la misma salida que la API. */
export function calcularPresion(
  serie: SerieCasos,
  anio: number,
  semana: number,
  aniosBase: readonly number[] = ANIOS_BASE_PRESION,
): ResultadoPresion {
  const observado = leer(serie, anio, semana);
  const { pool, aniosConDato } = construirPool(serie, anio, semana, aniosBase);
  const vacio = {
    casos_observados: observado,
    percentil: null,
    categoria: null,
    p50_baseline: null,
    p75_baseline: null,
    n_obs_baseline: pool.length,
    anios_baseline: aniosConDato,
  };
  if (aniosConDato < MINIMO_ANIOS) return { ...vacio, nota: NOTA_SIN_BASELINE };
  if (observado === null) return { ...vacio, nota: NOTA_HUECO };
  const p50 = percentil(pool, 50);
  const p75 = percentil(pool, 75);
  return {
    casos_observados: observado,
    percentil: redondear(rangoPercentil(pool, observado), 1),
    categoria: categorizar(observado, p50, p75),
    p50_baseline: redondear(p50, 1),
    p75_baseline: redondear(p75, 1),
    n_obs_baseline: pool.length,
    anios_baseline: aniosConDato,
  };
}

/** Ejemplo de la ficha: 2022, semana 30, ventana de tres semanas en cada año de referencia. */
export const EJEMPLO_PRESION = {
  anio: 2022,
  semana: 30,
  observado: 48,
  ventanas: [
    { anio: 2018, casos: [12, 18, 25] },
    { anio: 2019, casos: [40, 55, 61] },
    { anio: 2021, casos: [3, 4, 6] },
    { anio: 2023, casos: [20, 22, 35] },
  ],
} as const;

/** Serie del ejemplo en la forma que recibe calcularPresion. */
export function serieEjemplo(
  ventanas: readonly { anio: number; casos: readonly (number | null)[] }[],
  anio: number,
  semana: number,
  observado: number | null,
): SerieCasos {
  const serie: SerieCasos = {};
  const semanas = semanasEnVentana(semana);
  for (const v of ventanas) {
    serie[v.anio] = {};
    semanas.forEach((s, i) => {
      const casos = v.casos[i];
      if (casos !== null && casos !== undefined) serie[v.anio][s] = casos;
    });
  }
  serie[anio] = observado === null ? {} : { [semana]: observado };
  return serie;
}

export interface PresetPresion {
  clave: string;
  etiqueta: string;
  observado: number;
  ventanas: { anio: number; casos: (number | null)[] }[];
}

const VENTANAS_EJEMPLO = EJEMPLO_PRESION.ventanas.map((v) => ({
  anio: v.anio,
  casos: [...v.casos] as (number | null)[],
}));

export const PRESETS_PRESION: PresetPresion[] = [
  {
    clave: 'baja',
    etiqueta: 'Semana baja',
    observado: 10,
    ventanas: VENTANAS_EJEMPLO,
  },
  {
    clave: 'alta',
    etiqueta: 'Semana alta',
    observado: 70,
    ventanas: VENTANAS_EJEMPLO,
  },
  {
    clave: 'sin-historia',
    etiqueta: 'Sin historia suficiente',
    observado: 48,
    ventanas: [
      { anio: 2018, casos: [12, 18, 25] },
      { anio: 2019, casos: [null, null, null] },
      { anio: 2021, casos: [3, null, 6] },
      { anio: 2023, casos: [null, null, null] },
    ],
  },
];
