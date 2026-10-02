import type { TamanoPanel } from './analisis-layout-state';

/** Columnas de la cuadrícula del espacio de análisis. */
export const COLUMNAS_CUADRICULA = 12;

/**
 * Columnas base por tamaño en escritorio grande (`xl:`, desde 1280 px).
 * Son el punto de partida; `distribuirColumnas` ensancha lo que haga falta
 * para que cada fila quede completa.
 */
export const COLUMNAS_XL: Record<TamanoPanel, number> = {
  pequeno: 3,
  mediano: 4,
  grande: 6,
};

/**
 * Columnas base en tableta y portátil pequeño (`md:`, de 768 a 1279 px).
 * Un panel grande ocupa la fila entera; los demás comparten fila de dos en
 * dos. Los heatmaps de 52 semanas conservan su scroll horizontal por debajo
 * de su ancho mínimo, así que a este ancho nunca van a media fila.
 */
export const COLUMNAS_MD: Record<TamanoPanel, number> = {
  pequeno: 6,
  mediano: 6,
  grande: 12,
};

export interface PanelDistribuible<Id extends string = string> {
  id: Id;
  tamano: TamanoPanel;
  /** Un panel en foco ocupa siempre la fila completa. */
  enFoco?: boolean;
}

/**
 * Reparte los paneles visibles en filas de `capacidad` columnas y devuelve el
 * ancho final de cada uno, en el orden recibido (el orden del DOM, que es el
 * que sigue la cuadrícula).
 *
 * Reglas:
 * - Un panel solo (único visible, o huérfano al final) ocupa la fila entera.
 * - Las columnas que sobran en una fila se reparten de una en una entre sus
 *   paneles, empezando por el primero: 4 + 6 pasa a 5 + 7 y 6 + 4 a 7 + 5.
 * - Un panel en foco se ensancha a la fila completa y empieza fila nueva.
 */
export function distribuirColumnas<Id extends string>(
  paneles: readonly PanelDistribuible<Id>[],
  columnasBase: Record<TamanoPanel, number>,
  capacidad: number = COLUMNAS_CUADRICULA,
): number[] {
  const anchos: number[] = [];
  let fila: number[] = [];
  let ocupado = 0;

  const cerrarFila = (): void => {
    const sobrante = capacidad - ocupado;
    for (let i = 0; i < sobrante; i += 1) {
      const indice = fila[i % fila.length];
      anchos[indice] += 1;
    }
    fila = [];
    ocupado = 0;
  };

  paneles.forEach((panel, indice) => {
    const base = panel.enFoco
      ? capacidad
      : Math.min(columnasBase[panel.tamano], capacidad);
    if (fila.length > 0 && ocupado + base > capacidad) cerrarFila();
    anchos[indice] = base;
    fila.push(indice);
    ocupado += base;
    if (ocupado === capacidad) cerrarFila();
  });
  if (fila.length > 0) cerrarFila();

  return anchos;
}

/**
 * Distribución para los dos escalones de la cuadrícula. Las claves son los
 * identificadores de panel; cada valor trae las columnas en `md:` y en `xl:`.
 */
export function distribuirPaneles<Id extends string>(
  paneles: readonly PanelDistribuible<Id>[],
): Record<Id, { md: number; xl: number }> {
  const md = distribuirColumnas(paneles, COLUMNAS_MD);
  const xl = distribuirColumnas(paneles, COLUMNAS_XL);
  const resultado = {} as Record<Id, { md: number; xl: number }>;
  paneles.forEach((panel, indice) => {
    resultado[panel.id] = { md: md[indice], xl: xl[indice] };
  });
  return resultado;
}

/*
 * Clases de Tailwind escritas de forma literal para que el escaneo de
 * utilidades las encuentre; una plantilla `xl:col-span-${n}` no se generaría.
 */
export const CLASES_COL_SPAN_MD = [
  '',
  'md:col-span-1',
  'md:col-span-2',
  'md:col-span-3',
  'md:col-span-4',
  'md:col-span-5',
  'md:col-span-6',
  'md:col-span-7',
  'md:col-span-8',
  'md:col-span-9',
  'md:col-span-10',
  'md:col-span-11',
  'md:col-span-12',
] as const;

export const CLASES_COL_SPAN_XL = [
  '',
  'xl:col-span-1',
  'xl:col-span-2',
  'xl:col-span-3',
  'xl:col-span-4',
  'xl:col-span-5',
  'xl:col-span-6',
  'xl:col-span-7',
  'xl:col-span-8',
  'xl:col-span-9',
  'xl:col-span-10',
  'xl:col-span-11',
  'xl:col-span-12',
] as const;

/** Todas las clases de ancho que puede llevar un panel, para limpiarlas. */
export const TODAS_LAS_CLASES_COL_SPAN: readonly string[] = [
  ...CLASES_COL_SPAN_MD,
  ...CLASES_COL_SPAN_XL,
].filter((clase) => clase !== '');

/** Clases de ancho de un panel a partir de sus columnas en `md:` y `xl:`. */
export function clasesColumnas(columnas: { md: number; xl: number }): string[] {
  return [CLASES_COL_SPAN_MD[columnas.md], CLASES_COL_SPAN_XL[columnas.xl]];
}
