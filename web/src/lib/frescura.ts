export const NOMBRES_SERIES: Record<string, string> = {
  dengue_minsal_departamental: 'Dengue por departamento (boletines de MINSAL)',
  dengue_opendengue_nacional: 'Dengue nacional (OpenDengue)',
  dengue_tablero_nacional: 'Dengue nacional (tablero de MINSAL)',
  clima: 'Clima (Open-Meteo)',
  ira: 'IRA por departamento (boletines)',
  neumonias: 'Neumonías por departamento (boletines)',
  ira_tablero_nacional: 'IRA nacional (tablero de MINSAL)',
  neumonias_tablero_nacional: 'Neumonías nacionales (tablero de MINSAL)',
  virus_respiratorios: 'Virus respiratorios (laboratorio nacional)',
};

export function nombreSerie(clave: string): string {
  return NOMBRES_SERIES[clave] ?? clave.replace(/_/g, ' ');
}

export interface AntiguedadEntrada {
  ultima_anio: number | null;
  ultima_semana_epi: number | null;
  semanas: number | null;
}

/** Texto de la última semana con dato, o null si la serie no tiene ninguna. */
export function textoUltimaSemana(a: AntiguedadEntrada): string | null {
  if (a.ultima_anio === null || a.ultima_semana_epi === null) return null;
  return `SE${String(a.ultima_semana_epi).padStart(2, '0')} de ${a.ultima_anio}`;
}

/** Cuántas semanas atrás quedó la serie; null si no se puede decir. */
export function textoRezago(a: AntiguedadEntrada): string | null {
  if (a.semanas === null) return null;
  if (a.semanas <= 0) return 'al día';
  return a.semanas === 1
    ? '1 semana de rezago'
    : `${a.semanas} semanas de rezago`;
}
