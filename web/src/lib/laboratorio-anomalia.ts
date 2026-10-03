// Piezas puras del laboratorio de M2 que comparten el render del servidor
// (LaboratorioAnomalia.astro) y el del cliente (laboratorio-anomalia-cliente.ts):
// la tira de barras con su texto equivalente.

import { ANIOS_LABORATORIO, type BaselineSemana } from './anomalia.ts';
import { formatearNumero } from './idoneidad.ts';
import { svgTiraAnios, type LineaTira } from './tira-anios.ts';

const f2 = (n: number) => formatearNumero(n, 2);

export interface EtapasTira {
  /** Dibuja la mediana y la banda de una desviación (si existen). */
  mediana?: boolean;
  desviacion?: boolean;
}

export function tiraAnomalia(
  valor: number,
  referencias: readonly (number | null)[],
  r: Pick<BaselineSemana, 'mediana' | 'desviacion'>,
  etapas: EtapasTira = { mediana: true, desviacion: true },
): { svg: string; etiqueta: string } {
  const grupos = [
    ...ANIOS_LABORATORIO.map((anio, i) => ({
      etiqueta: String(anio),
      valores: [referencias[i] ?? null],
    })),
    { etiqueta: '2026', valores: [valor], apartado: true },
  ];
  const lineas: LineaTira[] = [];
  let banda: { desde: number; hasta: number } | undefined;
  if (etapas.mediana && r.mediana !== null) {
    lineas.push({
      valor: r.mediana,
      etiqueta: `mediana ${f2(r.mediana)}`,
      tipo: 'mediana',
    });
  }
  if (etapas.desviacion && r.mediana !== null && r.desviacion !== null) {
    banda = {
      desde: r.mediana - r.desviacion,
      hasta: r.mediana + r.desviacion,
    };
  }
  const conDato = referencias
    .map((v, i) => (v === null ? null : `${ANIOS_LABORATORIO[i]}: ${f2(v)}`))
    .filter((t): t is string => t !== null);
  const huecos = referencias.length - conDato.length;
  let etiqueta =
    conDato.length > 0
      ? `Iv de los años de referencia, ${conDato.join('; ')}.`
      : 'Ningún año de referencia tiene Iv.';
  if (huecos > 0) etiqueta += ` ${huecos} sin dato.`;
  etiqueta += ` Año descrito, 2026: ${f2(valor)}.`;
  if (etapas.mediana && r.mediana !== null) {
    etiqueta += ` Mediana ${f2(r.mediana)}.`;
  }
  return {
    svg: svgTiraAnios({ grupos, maximo: 1, lineas, banda }),
    etiqueta,
  };
}
