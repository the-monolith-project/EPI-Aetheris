// Tema de ECharts. Solo importa tipos: los componentes lo cargan de forma
// estática sin arrastrar ECharts (ver echarts-base.ts).
import { animacionesActivas } from './animaciones.ts';
import type { OpcionEcharts } from './echarts-base';

/** Tokens de tokens.css resueltos a valores concretos. */
export interface TokensGrafico {
  tinta: string;
  tintaSuave: string;
  borde: string;
  superficie: string;
  acento: string;
  secundario: string;
  seleccion: string;
  /** Azul de las estimaciones y predicciones (--color-estimacion). */
  estimacion: string;
  fuente: string;
  /** Familia del texto corrido (tooltips, anotaciones); `fuente` es la mono. */
  fuenteTexto: string;
}

/**
 * ECharts dibuja con valores literales y no resuelve `var(--...)`, así que se
 * leen del DOM. Hay que volver a leerlos al cambiar el tema (ver
 * echarts-montaje.ts).
 */
export function leerTokens(): TokensGrafico {
  const estilo = getComputedStyle(document.documentElement);
  const token = (nombre: string, respaldo: string) =>
    estilo.getPropertyValue(nombre).trim() || respaldo;
  return {
    tinta: token('--color-ink', '#040316'),
    tintaSuave: token('--color-ink-muted', '#4c5a56'),
    borde: token('--color-border', '#e0e0e6'),
    superficie: token('--color-surface', '#ffffff'),
    acento: token('--color-accent', '#183e39'),
    secundario: token('--color-secondary', '#dddbff'),
    seleccion: token('--color-seleccion', '#183e39'),
    estimacion: token('--color-estimacion', '#1f5fb4'),
    fuente: token('--font-mono', 'ui-monospace, monospace'),
    fuenteTexto: token('--font-sans', 'system-ui, sans-serif'),
  };
}

/** Etiqueta de semana epidemiológica: 5 -> "SE05". */
export function etiquetaSemana(valor: number | string): string {
  return `SE${String(valor).padStart(2, '0')}`;
}

/**
 * Opción común a todas las gráficas: tipografía, rejilla, tooltip y ARIA.
 * Cada gráfica la extiende con `{ ...crearOpcionBase(t), series, ... }`.
 */
export function crearOpcionBase(
  tokens: TokensGrafico,
  extra: {
    grid?: Record<string, unknown>;
    tooltip?: Record<string, unknown>;
    legend?: Record<string, unknown>;
  } = {},
): OpcionEcharts {
  return {
    // El interruptor «Animaciones» del pie manda sobre la preferencia del
    // sistema (animacionesActivas ya la usa cuando no hay elección guardada).
    animation: animacionesActivas(),
    animationDuration: 400,
    // Transición al cambiar la semana: corta y sin rebote (ver
    // GraficoMontado.actualizar con `suave`).
    animationDurationUpdate: 300,
    animationEasingUpdate: 'cubicOut',
    backgroundColor: 'transparent',
    textStyle: { color: tokens.tintaSuave, fontFamily: tokens.fuente },
    // Decals desactivados por defecto: en rampas ordenadas (bandas, mapas de
    // calor) el tono ya distingue; cada gráfica cualitativa los activa.
    // La descripción autogenerada de ECharts sale en inglés y pisa el
    // aria-label del panel: se apaga y montarGrafico etiqueta el SVG en
    // español. La alternativa textual completa es la tabla de cada panel.
    aria: { enabled: true, label: { enabled: false }, decal: { show: false } },
    grid: { left: 52, right: 20, top: 16, bottom: 40, ...extra.grid },
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: tokens.superficie,
      borderColor: tokens.borde,
      textStyle: { color: tokens.tinta, fontFamily: tokens.fuente },
      ...extra.tooltip,
    },
    legend: {
      bottom: 0,
      textStyle: { color: tokens.tintaSuave, fontFamily: tokens.fuente },
      ...extra.legend,
    },
  };
}

/** Eje de semanas epidemiológicas con etiquetas "SE05". */
export function ejeSemana(
  tokens: TokensGrafico,
  desde = 1,
  hasta = 53,
  etiqueta: string | null = 'Semana epidemiológica',
): OpcionEcharts {
  return {
    type: 'value',
    min: desde,
    max: hasta,
    name: etiqueta ?? undefined,
    nameLocation: 'middle',
    nameGap: 28,
    nameTextStyle: { color: tokens.tintaSuave },
    axisLabel: {
      formatter: etiquetaSemana,
      color: tokens.tintaSuave,
      hideOverlap: true,
    },
    axisLine: { lineStyle: { color: tokens.borde } },
    splitLine: { show: false },
  };
}

/** Eje Y de valores con rejilla, alineado con el eje de semanas. */
export function ejeValores(
  tokens: TokensGrafico,
  nombre: string,
  extra: Record<string, unknown> = {},
): OpcionEcharts {
  return {
    type: 'value',
    name: nombre,
    nameTextStyle: { color: tokens.tintaSuave, align: 'left' },
    axisLabel: { color: tokens.tintaSuave },
    splitLine: { lineStyle: { color: tokens.borde } },
    ...extra,
  };
}

/** Línea vertical punteada en la semana seleccionada (markLine de una serie). */
export function marcaSemana(
  tokens: TokensGrafico,
  semana: number,
): OpcionEcharts {
  return {
    silent: true,
    symbol: 'none',
    label: { show: false },
    lineStyle: {
      type: 'dashed',
      width: 2,
      color: tokens.seleccion,
      opacity: 0.6,
    },
    data: [{ xAxis: semana }],
  };
}

/**
 * Formateador de tooltip para ejes de semanas: toma la semana bajo el cursor
 * y devuelve el texto de esa fila, así el tooltip no lista series apiladas
 * ni valores intermedios.
 */
export function tooltipPorSemana<T>(
  filas: ReadonlyMap<number, T>,
  texto: (fila: T) => string,
): (params: unknown) => string {
  return (params) => {
    const lista = Array.isArray(params) ? params : [params];
    const eje = (lista[0] as { axisValue?: number } | undefined)?.axisValue;
    const fila = filas.get(Math.round(Number(eje)));
    return fila ? texto(fila) : '';
  };
}

/**
 * Tooltip de ejes de semanas con varias series: encabezado con la semana y
 * una fila por serie con dato. `unidad` va tras el valor ("casos probable").
 */
export function tooltipSeries(
  encabezado: (semana: number) => string,
  unidad: string,
): (params: unknown) => string {
  interface ItemTooltip {
    seriesName?: string;
    marker?: string;
    value?: unknown;
    axisValue?: number;
  }
  return (params) => {
    const lista = (Array.isArray(params) ? params : [params]) as ItemTooltip[];
    const filas = lista.filter(
      (item) => Array.isArray(item.value) && item.value[1] !== null,
    );
    if (filas.length === 0) return '';
    const semana = Math.round(Number(lista[0]?.axisValue));
    const detalle = filas.map(
      (item) =>
        `${item.marker ?? ''} ${item.seriesName}: ${(item.value as unknown[])[1]} ${unidad}`,
    );
    return [encabezado(semana), ...detalle].join('<br/>');
  };
}
