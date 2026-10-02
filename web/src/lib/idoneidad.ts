// Idoneidad biofísica (Iv), módulo M1. Es la misma función que calcula el
// backend (backend/api/idoneidad.py), portada para que la ficha enriquecida
// pueda mostrar el cálculo paso a paso y dejar que se mueva cada variable.
// Las constantes y el método para resolver `c` son los del backend; la prueba
// tests/unit/idoneidad.test.ts compara esta versión contra valores generados
// con el Python original. Si cambia una, cambia la otra.

export const T_MIN = 16;
export const T_MAX = 38;
/** Lluvia acumulada en dos semanas a la que la logística vale un medio, en mm. */
export const R0 = 30;
/** Pendiente de la logística. */
export const K = 0.1;
/** Humedad relativa a partir de la cual deja de penalizar, en %. */
export const HR_PLENA = 50;

function resolverCNormalizacion(): number {
  let mejor = 0;
  for (let t = T_MIN; t <= T_MAX; t += 0.001) {
    const crudo = t * (t - T_MIN) * Math.sqrt(Math.max(0, T_MAX - t));
    if (crudo > mejor) mejor = crudo;
  }
  return 1 / mejor;
}

/** Constante de la curva de Brière: hace que el máximo de `fT` valga 1. */
export const C_NORM = resolverCNormalizacion();

/** Idoneidad térmica (curva de Brière). Vale 0 fuera de [16, 38] °C. */
export function fT(temperatura: number): number {
  if (temperatura <= T_MIN || temperatura >= T_MAX) return 0;
  const crudo =
    temperatura * (temperatura - T_MIN) * Math.sqrt(T_MAX - temperatura);
  return Math.max(0, Math.min(1, C_NORM * crudo));
}

/** Idoneidad hídrica: logística sobre la lluvia acumulada en dos semanas. */
export function fR(lluviaDosSemanas: number): number {
  return 1 / (1 + Math.exp(-K * (lluviaDosSemanas - R0)));
}

/** Idoneidad por humedad relativa: rampa lineal que llega a 1 en el 50 %. */
export function fH(humedadRelativa: number): number {
  return Math.min(1, Math.max(0, humedadRelativa / HR_PLENA));
}

export interface EntradasIv {
  /** Temperatura media semanal, en °C. */
  temperatura: number;
  /** Lluvia acumulada en la semana y la anterior, en mm. */
  lluvia: number;
  /** Humedad relativa media semanal, en %. */
  humedad: number;
}

export interface DesgloseIv {
  fT: number;
  fR: number;
  fH: number;
  /** Peso de la lluvia dentro del factor hídrico: `0,3 + 0,7 · fR`. */
  factorLluvia: number;
  iv: number;
}

/** Iv con cada factor a la vista, para mostrar cómo se combinan. */
export function desgloseIv({
  temperatura,
  lluvia,
  humedad,
}: EntradasIv): DesgloseIv {
  const t = fT(temperatura);
  const r = fR(lluvia);
  const h = fH(humedad);
  const factorLluvia = 0.3 + 0.7 * r;
  return { fT: t, fR: r, fH: h, factorLluvia, iv: t * factorLluvia * h };
}

export function calcularIv(entradas: EntradasIv): number {
  return desgloseIv(entradas).iv;
}

/** Puntos de una función para dibujar su curva. */
export function muestrear(
  f: (x: number) => number,
  desde: number,
  hasta: number,
  pasos = 80,
): { x: number; y: number }[] {
  const puntos: { x: number; y: number }[] = [];
  for (let i = 0; i <= pasos; i += 1) {
    const x = desde + ((hasta - desde) * i) / pasos;
    puntos.push({ x, y: f(x) });
  }
  return puntos;
}

/** Número con coma decimal y los decimales indicados, sin depender de la configuración regional. */
export function formatearNumero(valor: number, decimales: number): string {
  return valor.toFixed(decimales).replace('.', ',');
}

/** Valores de ejemplo de la ficha: coinciden con los de los pasos de lectura. */
export const EJEMPLO_IV: EntradasIv = {
  temperatura: 27,
  lluvia: 40,
  humedad: 65,
};

/** Condiciones de partida del laboratorio para probar el índice. */
export const PRESETS_IV: {
  clave: string;
  etiqueta: string;
  entradas: EntradasIv;
}[] = [
  {
    clave: 'favorable',
    etiqueta: 'Cálido y lluvioso',
    entradas: { temperatura: 31, lluvia: 90, humedad: 75 },
  },
  {
    clave: 'fresca',
    etiqueta: 'Fresco',
    entradas: { temperatura: 19, lluvia: 40, humedad: 80 },
  },
  {
    clave: 'seca',
    etiqueta: 'Seco',
    entradas: { temperatura: 30, lluvia: 2, humedad: 35 },
  },
  {
    clave: 'calor',
    etiqueta: 'Calor extremo',
    entradas: { temperatura: 37, lluvia: 60, humedad: 60 },
  },
];
