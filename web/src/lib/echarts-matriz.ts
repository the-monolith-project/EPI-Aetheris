// Matriz de celdas coloreadas (semana x fila) compartida por el mapa de calor
// de presión, el calendario epidémico y la disponibilidad de datos. Cada
// celda trae su color ya resuelto (colorPresion, colorCasos...), así que no
// se usa visualMap: la leyenda de rampa vive fuera, en el HTML del panel.
import type { OpcionEcharts } from './echarts-base';
import { montarGrafico } from './echarts-montaje';
import type { GraficoMontado } from './echarts-montaje';
import { crearOpcionBase, etiquetaSemana } from './echarts-tema';
import type { TokensGrafico } from './echarts-tema';
import { escapeHtml } from '../utils/security';

export interface CeldaMatriz {
  semana: number;
  fila: string;
  color: string;
  /** Celda de la selección actual: se dibuja con borde de selección. */
  activa: boolean;
}

export interface ConfigMatriz {
  semanas: number[];
  filas: string[];
  celdas: CeldaMatriz[];
  /** Margen izquierdo para las etiquetas de fila. */
  izquierda: number;
  /** Cantidad aproximada de etiquetas en el eje de semanas. */
  etiquetasX: number;
  /** Texto del tooltip de la celda `indice` (texto plano; \n separa líneas). */
  texto: (indice: number) => string;
}

export function opcionMatriz(
  t: TokensGrafico,
  config: ConfigMatriz,
): OpcionEcharts {
  const { semanas, filas, celdas } = config;
  const columna = new Map(semanas.map((s, i) => [s, i]));
  const renglon = new Map(filas.map((f, i) => [f, i]));
  const paso = Math.max(1, Math.ceil(semanas.length / config.etiquetasX));

  return {
    ...crearOpcionBase(t, {
      grid: {
        left: config.izquierda,
        right: 20,
        top: 12,
        bottom: 56,
        show: true,
        borderColor: t.borde,
      },
      tooltip: {
        trigger: 'item',
        formatter: (p: { dataIndex: number }) =>
          escapeHtml(config.texto(p.dataIndex)).replaceAll('\n', '<br/>'),
      },
      legend: { show: false },
    }),
    xAxis: {
      type: 'category',
      data: semanas.map(String),
      name: 'Semana epidemiológica',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { color: t.tintaSuave },
      axisLine: { lineStyle: { color: t.borde } },
      axisTick: { show: false },
      axisLabel: {
        color: t.tintaSuave,
        formatter: (valor: string) => etiquetaSemana(valor),
        interval: (indice: number) => indice % paso === 0,
      },
    },
    yAxis: {
      type: 'category',
      data: filas,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: t.tintaSuave, interval: 0 },
    },
    series: [
      {
        // `heatmap` exige visualMap en ejes cartesianos; como cada celda trae
        // su color ya resuelto, se dibuja con una serie custom de rectángulos.
        type: 'custom',
        id: 'matriz',
        renderItem: (
          _params: unknown,
          api: {
            value: (dimension: number) => number;
            coord: (punto: number[]) => number[];
            size: (extension: number[]) => number[];
            style: () => Record<string, unknown>;
          },
        ) => {
          const [x, y] = api.coord([api.value(0), api.value(1)]);
          const [ancho, alto] = api.size([1, 1]);
          return {
            type: 'rect',
            shape: {
              x: x - ancho / 2,
              y: y - alto / 2,
              width: ancho,
              height: alto,
            },
            style: api.style(),
            // Al cambiar la celda activa el borde y el color se funden en
            // vez de saltar (solo anima en actualizaciones suaves).
            transition: ['style'],
          };
        },
        emphasis: { itemStyle: { borderColor: t.tinta, borderWidth: 1 } },
        data: celdas.map((celda) => ({
          value: [columna.get(celda.semana) ?? 0, renglon.get(celda.fila) ?? 0],
          itemStyle: {
            color: celda.color,
            borderColor: celda.activa ? t.seleccion : t.superficie,
            borderWidth: celda.activa ? 2 : 0.5,
          },
          z: celda.activa ? 3 : 1,
        })),
      },
    ],
  };
}

/** Monta la matriz y llama a `alPulsar` con el índice de la celda pulsada. */
export async function montarMatriz(
  contenedor: HTMLElement,
  config: () => ConfigMatriz,
  descripcion: string,
  alPulsar: (indice: number) => void,
): Promise<GraficoMontado> {
  const montado = await montarGrafico(
    contenedor,
    (t) => opcionMatriz(t, config()),
    descripcion,
  );
  montado.instancia.on('click', (evento: unknown) => {
    const { componentType, dataIndex } = evento as {
      componentType?: string;
      dataIndex?: number;
    };
    if (componentType === 'series' && dataIndex !== undefined) {
      alPulsar(dataIndex);
    }
  });
  return montado;
}

/**
 * Mueve la selección (celda o columna activa) sin recrear la matriz: el borde
 * y el color de las celdas se funden en animationDurationUpdate.
 */
export function moverSeleccionMatriz(
  montado: GraficoMontado,
  config: ConfigMatriz,
): void {
  montado.actualizar((t) => opcionMatriz(t, config), { suave: true });
}
