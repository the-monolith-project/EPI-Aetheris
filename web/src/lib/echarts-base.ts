// Registro modular de ECharts: solo los gráficos y componentes que usa el
// sitio, con el renderer SVG. SVG y no canvas porque exportar-grafico.ts
// exporta el gráfico clonando el <svg>, y la impresión de las fichas lo
// necesita vectorial.
//
// Este módulo importa ECharts en estático, así que solo debe cargarse con
// `await import('./echarts-base')` (o vía `cargarEcharts`). Un import de
// valor desde un componente arrastraría ECharts al grafo inicial de /dengue.
import { CustomChart, LineChart, ScatterChart } from 'echarts/charts';
import {
  AriaComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  TooltipComponent,
} from 'echarts/components';
import * as echarts from 'echarts/core';
import { SVGRenderer } from 'echarts/renderers';

echarts.use([
  CustomChart,
  LineChart,
  ScatterChart,
  AriaComponent,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  TooltipComponent,
  SVGRenderer,
]);

export { echarts };
export type { EChartsCoreOption as OpcionEcharts } from 'echarts/core';
