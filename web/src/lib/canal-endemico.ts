export type SerieCanal = 'probable' | 'confirmado';

export interface SemanaCanalEntrada {
  semana_epi: number;
  probable: PuntoCanalEntrada;
  confirmado: PuntoCanalEntrada;
}

interface PuntoCanalEntrada {
  casos_observados: number | null;
  p50_baseline: number | null;
  p75_baseline: number | null;
}

export interface PuntoCanal {
  semana: number;
  p50: number | null;
  p75: number | null;
  observado: number | null;
}

// Los cortes salen de la línea base de M3, que deja fuera el año descrito.
// Una semana sin línea base queda con p50 y p75 en null: no se interpola.
export function construirCanal(
  semanas: SemanaCanalEntrada[],
  serie: SerieCanal,
): PuntoCanal[] {
  return [...semanas]
    .sort((a, b) => a.semana_epi - b.semana_epi)
    .map((s) => {
      const punto = s[serie];
      const p50 = punto.p50_baseline;
      const p75 = punto.p75_baseline;
      const cortesValidos = p50 !== null && p75 !== null;
      return {
        semana: s.semana_epi,
        p50: cortesValidos ? p50 : null,
        p75: cortesValidos ? p75 : null,
        observado: punto.casos_observados,
      };
    });
}

export function categoriaCanal(
  punto: PuntoCanal,
): 'baja' | 'media' | 'alta' | null {
  if (punto.observado === null || punto.p50 === null || punto.p75 === null) {
    return null;
  }
  if (punto.observado <= punto.p50) return 'baja';
  if (punto.observado <= punto.p75) return 'media';
  return 'alta';
}
