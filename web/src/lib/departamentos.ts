export interface DepartamentoInfo {
  codigo: string;
  nombre: string;
}

export const DEPARTAMENTOS: readonly DepartamentoInfo[] = [
  { codigo: 'SV-AH', nombre: 'Ahuachapán' },
  { codigo: 'SV-CA', nombre: 'Cabañas' },
  { codigo: 'SV-CH', nombre: 'Chalatenango' },
  { codigo: 'SV-CU', nombre: 'Cuscatlán' },
  { codigo: 'SV-LI', nombre: 'La Libertad' },
  { codigo: 'SV-MO', nombre: 'Morazán' },
  { codigo: 'SV-PA', nombre: 'La Paz' },
  { codigo: 'SV-SA', nombre: 'Santa Ana' },
  { codigo: 'SV-SM', nombre: 'San Miguel' },
  { codigo: 'SV-SO', nombre: 'Sonsonate' },
  { codigo: 'SV-SS', nombre: 'San Salvador' },
  { codigo: 'SV-SV', nombre: 'San Vicente' },
  { codigo: 'SV-UN', nombre: 'La Unión' },
  { codigo: 'SV-US', nombre: 'Usulután' },
] as const;

export const DEPARTAMENTOS_POR_CODIGO: Record<string, DepartamentoInfo> =
  Object.fromEntries(DEPARTAMENTOS.map((dep) => [dep.codigo, dep]));

export function obtenerDepartamento(
  codigo: string,
): DepartamentoInfo | undefined {
  return DEPARTAMENTOS_POR_CODIGO[codigo];
}
