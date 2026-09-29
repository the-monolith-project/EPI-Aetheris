import { DEPARTAMENTOS_POR_CODIGO } from './departamentos.ts';

/** Forma mínima de una alerta para razonar sobre su alcance (ADR 0022). */
export interface ConAlcance {
  departamentos?: string[] | null;
}

export function esAlertaNacional(alerta: ConAlcance): boolean {
  return !alerta.departamentos || alerta.departamentos.length === 0;
}

/** Una alerta nacional aplica a todos; una regional, solo a los que lista. */
export function alertaAplicaA(
  alerta: ConAlcance,
  codigoDepartamento: string,
): boolean {
  return (
    esAlertaNacional(alerta) ||
    (alerta.departamentos ?? []).includes(codigoDepartamento)
  );
}

export function textoAlcance(alerta: ConAlcance): string {
  if (esAlertaNacional(alerta)) return 'Nacional';
  return (alerta.departamentos ?? [])
    .map((codigo) => DEPARTAMENTOS_POR_CODIGO[codigo]?.nombre ?? codigo)
    .join(', ');
}
