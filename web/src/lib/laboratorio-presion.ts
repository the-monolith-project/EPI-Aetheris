// Piezas puras del laboratorio de M3 que comparten el render del servidor
// (LaboratorioPresion.astro) y el del cliente (laboratorio-presion-cliente.ts).

import { svgRectaPercentil } from './graficos-presion.ts';
import { formatearNumero } from './idoneidad.ts';
import {
  calcularPresion,
  construirPool,
  serieEjemplo,
  type PresetPresion,
  type ResultadoPresion,
} from './presion.ts';
import { svgTiraAnios, type LineaTira } from './tira-anios.ts';

export const ANIO_LABORATORIO = 2022;
export const SEMANA_LABORATORIO = 30;
export const MAXIMO_CASOS = 150;

const f1 = (n: number) => formatearNumero(n, 1);

export interface CalculoLaboratorioPresion {
  observado: number;
  pool: number[];
  resultado: ResultadoPresion;
}

export function calcularLaboratorio(
  ventanas: PresetPresion['ventanas'],
  observado: number,
): CalculoLaboratorioPresion {
  const serie = serieEjemplo(
    ventanas,
    ANIO_LABORATORIO,
    SEMANA_LABORATORIO,
    observado,
  );
  const { pool } = construirPool(serie, ANIO_LABORATORIO, SEMANA_LABORATORIO);
  return {
    observado,
    pool,
    resultado: calcularPresion(serie, ANIO_LABORATORIO, SEMANA_LABORATORIO),
  };
}

export function tiraPresion(
  ventanas: PresetPresion['ventanas'],
  c: CalculoLaboratorioPresion,
  conCortes = true,
): { svg: string; etiqueta: string } {
  const maximo =
    Math.ceil((Math.max(10, ...c.pool, c.observado) * 1.1) / 10) * 10;
  const lineas: LineaTira[] = [];
  const { p50_baseline: p50, p75_baseline: p75 } = c.resultado;
  if (conCortes && p50 !== null && p75 !== null) {
    lineas.push(
      { valor: p50, etiqueta: `P50 ${f1(p50)}`, tipo: 'corte' },
      { valor: p75, etiqueta: `P75 ${f1(p75)}`, tipo: 'corte' },
    );
  }
  const svg = svgTiraAnios({
    grupos: [
      ...ventanas.map((v) => ({
        etiqueta: String(v.anio),
        valores: v.casos,
        atenuado: v.casos.every((x) => x === null),
      })),
      {
        etiqueta: String(ANIO_LABORATORIO),
        valores: [c.observado],
        apartado: true,
      },
    ],
    maximo,
    lineas,
    formato: (n) => String(Math.round(n)),
  });
  const partes = ventanas.map((v) => {
    const casos = v.casos.map((x) => (x === null ? 'sin dato' : String(x)));
    return `${v.anio}: ${casos.join(', ')}`;
  });
  return {
    svg,
    etiqueta: `Casos de las semanas 29, 30 y 31 en los años de referencia, ${partes.join('; ')}. ${ANIO_LABORATORIO}: ${c.observado} casos en la semana 30.`,
  };
}

export function rectaPresion(c: CalculoLaboratorioPresion): string {
  if (c.pool.length === 0) return '';
  const pct = c.resultado.percentil;
  return svgRectaPercentil({
    valores: c.pool,
    observado: c.observado,
    etiquetaObservado:
      pct === null
        ? `${c.observado} casos`
        : `${c.observado} casos → percentil ${f1(pct)}`,
  });
}
