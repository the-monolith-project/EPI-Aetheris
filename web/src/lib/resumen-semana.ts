import type { CasoNacionalSemanal } from './tipos-analisis';

export interface ResumenUltimaSemana {
  actual: CasoNacionalSemanal;
  /** Misma semana epidemiológica del año anterior; null si la serie no la trae. */
  mismaSemanaAnioAnterior: CasoNacionalSemanal | null;
  diferencia: number | null;
  /** Variación porcentual; null si no hay año anterior o su conteo es cero. */
  variacionPct: number | null;
}

/**
 * Última semana publicada por el tablero de MINSAL y su par del año anterior.
 * Solo compara tablero contra tablero: el total de OpenDengue tiene otra forma
 * de suavizado y no es comparable semana a semana. No interpola semanas que la
 * fuente no publicó (la 53 de 2025).
 */
export function resumirUltimaSemana(
  casos: CasoNacionalSemanal[],
): ResumenUltimaSemana | null {
  const tablero = casos.filter((c) => c.fuente === 'minsal_tablero');
  if (tablero.length === 0) return null;

  const actual = tablero.reduce((a, b) =>
    b.anio > a.anio || (b.anio === a.anio && b.semana_epi > a.semana_epi)
      ? b
      : a,
  );
  const previa =
    tablero.find(
      (c) => c.anio === actual.anio - 1 && c.semana_epi === actual.semana_epi,
    ) ?? null;

  const diferencia = previa ? actual.conteo - previa.conteo : null;
  const variacionPct =
    previa && previa.conteo > 0
      ? ((actual.conteo - previa.conteo) / previa.conteo) * 100
      : null;

  return {
    actual,
    mismaSemanaAnioAnterior: previa,
    diferencia,
    variacionPct,
  };
}
