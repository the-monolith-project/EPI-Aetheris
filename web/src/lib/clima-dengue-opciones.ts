// Opciones de ECharts de la página de clima y dengue (/analisis/clima). Solo
// importan tipos de ECharts: se montan con montarGrafico, que carga la
// librería de forma diferida. Los datos ya vienen derivados por
// clima-dengue.ts; aquí solo se dibujan.
import {
  colorCorrelacion,
  colorCualitativo,
  colorTextoSobre,
  COLOR_SIN_DATO,
} from './colores';
import type { FilaAporte, FilaBosque } from './clima-dengue';
import {
  CLAVE_EL_SALVADOR,
  formatoIntervalo,
  formatoNumero,
  formatoR,
  nombrePais,
} from './clima-dengue';
import type { OpcionEcharts } from './echarts-base';
import {
  crearOpcionBase,
  ejeSemana,
  ejeValores,
  etiquetaSemana,
} from './echarts-tema';
import type { TokensGrafico } from './echarts-tema';
import { escapeHtml } from '../utils/security';

// --- Aporte del clima por año (barras agrupadas) ----------------------------

const SERIES_APORTE: {
  clave: 'clima' | 'oni' | 'climaYOni';
  nombre: string;
  color: number;
}[] = [
  { clave: 'clima', nombre: 'Clima de superficie', color: 0 },
  { clave: 'oni', nombre: 'ONI', color: 2 },
  { clave: 'climaYOni', nombre: 'Clima y ONI', color: 1 },
];

export function opcionAporte(
  t: TokensGrafico,
  filas: FilaAporte[],
  horizonte: number,
): OpcionEcharts {
  const anios = filas.map((f) => String(f.anio));
  return {
    ...crearOpcionBase(t, {
      grid: { left: 64, right: 16, top: 24, bottom: 64 },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: unknown) => {
          const lista = (Array.isArray(params) ? params : [params]) as {
            axisValue?: string;
            marker?: string;
            seriesName?: string;
            value?: number;
          }[];
          const encabezado = `${escapeHtml(String(lista[0]?.axisValue ?? ''))}, a ${horizonte} ${horizonte === 1 ? 'semana' : 'semanas'}`;
          return [
            encabezado,
            ...lista.map(
              (item) =>
                `${item.marker ?? ''} ${escapeHtml(item.seriesName ?? '')}: ${formatoNumero(Number(item.value), 3, true)}`,
            ),
          ].join('<br/>');
        },
      },
    }),
    xAxis: {
      type: 'category',
      data: anios,
      name: 'Año de prueba',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { color: t.tintaSuave },
      axisLine: { lineStyle: { color: t.borde } },
      axisTick: { show: false },
      axisLabel: { color: t.tintaSuave },
    },
    yAxis: ejeValores(t, 'Diferencia de habilidad', {
      nameGap: 16,
      axisLabel: {
        color: t.tintaSuave,
        formatter: (valor: number) => formatoNumero(valor, 1, true),
      },
    }),
    series: SERIES_APORTE.map((serie, indice) => ({
      id: serie.clave,
      name: serie.nombre,
      type: 'bar',
      barGap: '10%',
      itemStyle: {
        color: colorCualitativo(serie.color),
        opacity: serie.clave === 'clima' ? 1 : 0.75,
      },
      emphasis: { focus: 'series' },
      data: filas.map((f) => f[serie.clave]),
      ...(indice === 0
        ? {
            markLine: {
              silent: true,
              symbol: 'none',
              label: { show: false },
              lineStyle: { color: t.tinta, width: 1, type: 'solid' },
              data: [{ yAxis: 0 }],
            },
          }
        : {}),
    })),
  };
}

// --- Matriz de correlaciones (fila × columna) -----------------------------

export interface CeldaCorrelacion {
  fila: string;
  columna: string;
  r: number | null;
  /** El intervalo del 95 % excluye el cero. */
  destacada: boolean;
  /** Cumple además la regla de consistencia del protocolo. */
  consistente: boolean;
  /** Texto del tooltip (texto plano; \n separa líneas). */
  texto: string;
}

export interface ConfigMatrizCorrelacion {
  filas: string[];
  columnas: string[];
  celdas: CeldaCorrelacion[];
  izquierda: number;
  /** Texto dentro de cada celda; por defecto la correlación con su marca. */
  textoCelda?: (celda: CeldaCorrelacion) => string;
}

export function textoCeldaCorrelacion(celda: CeldaCorrelacion): string {
  if (celda.r === null) return 'sin dato';
  return `${formatoR(celda.r, 2)}${celda.consistente ? ' †' : celda.destacada ? ' *' : ''}`;
}

export function opcionMatrizCorrelacion(
  t: TokensGrafico,
  config: ConfigMatrizCorrelacion,
): OpcionEcharts {
  const columna = new Map(config.columnas.map((c, i) => [c, i]));
  const renglon = new Map(config.filas.map((f, i) => [f, i]));
  const etiqueta = config.textoCelda ?? textoCeldaCorrelacion;
  return {
    ...crearOpcionBase(t, {
      grid: {
        left: config.izquierda,
        right: 12,
        top: 36,
        bottom: 8,
        show: true,
        borderColor: t.borde,
      },
      tooltip: {
        trigger: 'item',
        formatter: (p: { dataIndex: number }) =>
          escapeHtml(config.celdas[p.dataIndex]?.texto ?? '').replaceAll(
            '\n',
            '<br/>',
          ),
      },
      legend: { show: false },
    }),
    xAxis: {
      type: 'category',
      data: config.columnas,
      position: 'top',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: t.tintaSuave, interval: 0, hideOverlap: false },
    },
    yAxis: {
      type: 'category',
      data: config.filas,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: t.tintaSuave, interval: 0 },
    },
    series: [
      {
        type: 'custom',
        id: 'matriz-correlacion',
        renderItem: (
          _params: unknown,
          api: {
            value: (dimension: number) => number;
            coord: (punto: number[]) => number[];
            size: (extension: number[]) => number[];
          },
        ) => {
          const indice = _params as { dataIndex: number };
          const celda = config.celdas[indice.dataIndex];
          const [x, y] = api.coord([api.value(0), api.value(1)]);
          const [ancho, alto] = api.size([1, 1]);
          const fondo =
            celda.r === null ? COLOR_SIN_DATO : colorCorrelacion(celda.r);
          const marcada = celda.destacada || celda.consistente;
          return {
            type: 'group',
            children: [
              {
                type: 'rect',
                shape: {
                  x: x - ancho / 2,
                  y: y - alto / 2,
                  width: ancho,
                  height: alto,
                },
                style: {
                  fill: fondo,
                  stroke: marcada ? t.tinta : t.superficie,
                  lineWidth: marcada ? 2 : 0.5,
                },
              },
              {
                type: 'text',
                style: {
                  x,
                  y,
                  text: etiqueta(celda),
                  textAlign: 'center',
                  textVerticalAlign: 'middle',
                  fill: colorTextoSobre(fondo),
                  fontFamily: t.fuente,
                  fontSize: 12,
                  fontWeight: marcada ? 'bold' : 'normal',
                },
              },
            ],
          };
        },
        data: config.celdas.map((celda) => [
          columna.get(celda.columna) ?? 0,
          renglon.get(celda.fila) ?? 0,
        ]),
      },
    ],
  };
}

// --- Ciclo medio de casos y clima ------------------------------------------

export function opcionCiclo(
  t: TokensGrafico,
  datos: {
    semanas: number[];
    casos: number[];
    clima: number[];
    nombreClima: string;
    unidadClima: string;
  },
): OpcionEcharts {
  const colorCasos = t.estimacion;
  const colorClima = colorCualitativo(1);
  const par = (valores: number[]) =>
    datos.semanas.map((semana, i) => [semana, valores[i]]);
  return {
    ...crearOpcionBase(t, {
      grid: { left: 64, right: 64, top: 28, bottom: 76 },
      tooltip: {
        trigger: 'axis',
        formatter: (params: unknown) => {
          const lista = (Array.isArray(params) ? params : [params]) as {
            axisValue?: number;
            marker?: string;
            seriesName?: string;
            value?: unknown[];
          }[];
          const semana = Math.round(Number(lista[0]?.axisValue));
          return [
            etiquetaSemana(semana),
            ...lista.map(
              (item) =>
                `${item.marker ?? ''} ${escapeHtml(item.seriesName ?? '')}: ${formatoNumero(Number(item.value?.[1]), 1)}`,
            ),
          ].join('<br/>');
        },
      },
    }),
    xAxis: ejeSemana(t, 1, datos.semanas.length),
    yAxis: [
      ejeValores(t, 'Casos por semana', {
        nameGap: 12,
        axisLabel: {
          color: colorCasos,
          formatter: (v: number) => String(Math.round(v)),
        },
      }),
      ejeValores(t, datos.unidadClima, {
        nameGap: 12,
        position: 'right',
        splitLine: { show: false },
        axisLabel: { color: colorClima },
        nameTextStyle: { color: t.tintaSuave, align: 'right' },
      }),
    ],
    series: [
      {
        id: 'casos',
        name: 'Casos (promedio de los años)',
        type: 'line',
        yAxisIndex: 0,
        showSymbol: false,
        lineStyle: { width: 2.5, color: colorCasos },
        itemStyle: { color: colorCasos },
        data: par(datos.casos),
      },
      {
        id: 'clima',
        name: datos.nombreClima,
        type: 'line',
        yAxisIndex: 1,
        showSymbol: false,
        lineStyle: { width: 2, type: 'dashed', color: colorClima },
        itemStyle: { color: colorClima },
        data: par(datos.clima),
      },
    ],
  };
}

// --- Bosque de países (correlación con la señal regional) -------------------

export function opcionBosque(
  t: TokensGrafico,
  filas: FilaBosque[],
  nueveAnios: boolean,
): OpcionEcharts {
  const minimo = Math.min(0, ...filas.map((f) => (f.ic95 ? f.ic95[0] : f.r)));
  const maximo = Math.max(...filas.map((f) => (f.ic95 ? f.ic95[1] : f.r)));
  const piso = Math.floor((minimo - 0.05) * 10) / 10;
  const techo = Math.ceil((maximo + 0.05) * 10) / 10;
  return {
    ...crearOpcionBase(t, {
      grid: { left: 150, right: 24, top: 12, bottom: 48 },
      tooltip: {
        trigger: 'item',
        formatter: (p: { dataIndex: number }) => {
          const fila = filas[p.dataIndex];
          if (!fila) return '';
          const intervalo = fila.ic95
            ? `, intervalo del 95 %: ${formatoIntervalo(fila.ic95)}`
            : '';
          return `${escapeHtml(fila.nombre)}<br/>Correlación ${formatoR(fila.r, 3)}${intervalo}<br/>Posición ${fila.posicion} de ${filas.length}`;
        },
      },
      legend: { show: false },
    }),
    xAxis: ejeValores(
      t,
      nueveAnios ? 'Correlación (9 años)' : 'Correlación (11 años)',
      {
        min: piso,
        max: techo,
        nameLocation: 'middle',
        nameGap: 30,
        nameTextStyle: { color: t.tintaSuave },
        axisLabel: {
          color: t.tintaSuave,
          formatter: (v: number) => formatoNumero(v, 1, true),
        },
      },
    ),
    yAxis: {
      type: 'category',
      data: filas.map((f) => f.nombre),
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: t.tintaSuave,
        interval: 0,
        formatter: (valor: string) =>
          valor === nombrePais(CLAVE_EL_SALVADOR) ? `{es|${valor}}` : valor,
        rich: { es: { fontWeight: 'bold', color: t.tinta } },
      },
    },
    series: [
      {
        // Línea en cero: un markLine no se admite en la serie custom.
        type: 'line',
        id: 'cero',
        data: [],
        silent: true,
        markLine: {
          silent: true,
          symbol: 'none',
          label: { show: false },
          lineStyle: { color: t.tintaSuave, width: 1, type: 'dashed' },
          data: [{ xAxis: 0 }],
        },
      },
      {
        type: 'custom',
        id: 'bosque',
        renderItem: (
          params: { dataIndex: number },
          api: {
            value: (dimension: number) => number;
            coord: (punto: number[]) => number[];
          },
        ) => {
          const fila = filas[params.dataIndex];
          const y = api.coord([api.value(0), params.dataIndex])[1];
          const x = api.coord([api.value(0), params.dataIndex])[0];
          const color = fila.esElSalvador ? t.acento : t.tintaSuave;
          const hijos: Record<string, unknown>[] = [];
          if (fila.ic95) {
            const x0 = api.coord([fila.ic95[0], params.dataIndex])[0];
            const x1 = api.coord([fila.ic95[1], params.dataIndex])[0];
            hijos.push({
              type: 'line',
              shape: { x1: x0, y1: y, x2: x1, y2: y },
              style: {
                stroke: color,
                lineWidth: fila.esElSalvador ? 3 : 1.5,
              },
            });
          }
          hijos.push({
            type: 'circle',
            shape: { cx: x, cy: y, r: fila.esElSalvador ? 6 : 4 },
            style: { fill: color, stroke: t.superficie, lineWidth: 1 },
          });
          return { type: 'group', children: hijos };
        },
        data: filas.map((f) => [f.r, f.posicion]),
      },
    ],
  };
}
