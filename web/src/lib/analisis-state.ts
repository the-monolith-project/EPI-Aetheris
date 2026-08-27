import {
  ANIOS_ANALISIS_DENGUE,
  type AnioAnalisisDengue,
  type FiltrosAnalisis,
} from './tipos-analisis';

export const EVENTO_FILTROS_ANALISIS = 'epi:filters-changed';

const estadoInicial: FiltrosAnalisis = {
  anio: 2023,
  semana: 1,
  semanaDesde: 1,
  semanaHasta: 53,
  serie: 'probable',
  departamento: null,
  comparar: [],
};

let estado = clonarEstado(estadoInicial);

function limitarSemana(valor: number): number {
  if (!Number.isFinite(valor)) return 1;
  return Math.min(53, Math.max(1, Math.trunc(valor)));
}

function esAnioDisponible(valor: number): valor is AnioAnalisisDengue {
  return ANIOS_ANALISIS_DENGUE.includes(valor as AnioAnalisisDengue);
}

function clonarEstado(valor: FiltrosAnalisis): FiltrosAnalisis {
  return { ...valor, comparar: [...valor.comparar] };
}

function normalizarEstado(
  base: FiltrosAnalisis,
  cambios: Partial<FiltrosAnalisis>,
): FiltrosAnalisis {
  const candidato = { ...base, ...cambios };
  const semanaDesde = limitarSemana(candidato.semanaDesde);
  const semanaHasta = limitarSemana(candidato.semanaHasta);

  if (!esAnioDisponible(candidato.anio)) candidato.anio = estadoInicial.anio;
  candidato.semana = limitarSemana(candidato.semana);
  candidato.semanaDesde = Math.min(semanaDesde, semanaHasta);
  candidato.semanaHasta = Math.max(semanaDesde, semanaHasta);
  candidato.serie =
    candidato.serie === 'confirmado' ? 'confirmado' : 'probable';
  candidato.departamento = candidato.departamento?.trim() || null;
  candidato.comparar = [...new Set(candidato.comparar.filter(Boolean))].slice(
    0,
    4,
  );
  return candidato;
}

function estadosIguales(a: FiltrosAnalisis, b: FiltrosAnalisis): boolean {
  return (
    a.anio === b.anio &&
    a.semana === b.semana &&
    a.semanaDesde === b.semanaDesde &&
    a.semanaHasta === b.semanaHasta &&
    a.serie === b.serie &&
    a.departamento === b.departamento &&
    a.comparar.length === b.comparar.length &&
    a.comparar.every((codigo, indice) => codigo === b.comparar[indice])
  );
}

export function obtenerFiltrosAnalisis(): FiltrosAnalisis {
  return clonarEstado(estado);
}

export function actualizarFiltrosAnalisis(
  cambios: Partial<FiltrosAnalisis>,
): FiltrosAnalisis {
  const siguiente = normalizarEstado(estado, cambios);
  if (estadosIguales(estado, siguiente)) return obtenerFiltrosAnalisis();

  estado = siguiente;
  const detalle = obtenerFiltrosAnalisis();
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent<FiltrosAnalisis>(EVENTO_FILTROS_ANALISIS, {
        detail: detalle,
      }),
    );
  }
  return detalle;
}

export function suscribirFiltrosAnalisis(
  listener: (filtros: FiltrosAnalisis) => void,
  emitirInicial = true,
): () => void {
  if (emitirInicial) listener(obtenerFiltrosAnalisis());
  if (typeof window === 'undefined') return () => undefined;

  const manejarEvento = (evento: Event) => {
    listener(clonarEstado((evento as CustomEvent<FiltrosAnalisis>).detail));
  };
  window.addEventListener(EVENTO_FILTROS_ANALISIS, manejarEvento);
  return () =>
    window.removeEventListener(EVENTO_FILTROS_ANALISIS, manejarEvento);
}
