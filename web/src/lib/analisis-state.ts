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
  modoMinsal: 'semana',
};

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
  candidato.modoMinsal = ['semana', 'ytd', 'historico'].includes(
    candidato.modoMinsal,
  )
    ? candidato.modoMinsal
    : 'semana';
  return candidato;
}

function leerEstadoDesdeUrl(): Partial<FiltrosAnalisis> {
  if (typeof window === 'undefined') return {};
  const parametros = new URLSearchParams(window.location.search);
  const cambios: Partial<FiltrosAnalisis> = {};
  const anio = parametros.get('year');
  const semana = parametros.get('week');
  const semanaDesde = parametros.get('fromWeek');
  const semanaHasta = parametros.get('toWeek');
  const serie = parametros.get('serie');
  const departamento = parametros.get('dept');
  const comparar = parametros.get('compare');
  const modoMinsal = parametros.get('minsal');
  if (anio !== null) cambios.anio = Number(anio) as AnioAnalisisDengue;
  if (semana !== null) cambios.semana = Number(semana);
  if (semanaDesde !== null) cambios.semanaDesde = Number(semanaDesde);
  if (semanaHasta !== null) cambios.semanaHasta = Number(semanaHasta);
  if (serie === 'probable' || serie === 'confirmado') cambios.serie = serie;
  if (departamento !== null) cambios.departamento = departamento;
  if (comparar !== null) cambios.comparar = comparar.split(',');
  if (
    modoMinsal === 'semana' ||
    modoMinsal === 'ytd' ||
    modoMinsal === 'historico'
  ) {
    cambios.modoMinsal = modoMinsal;
  }
  return cambios;
}

function sincronizarUrl(filtros: FiltrosAnalisis): void {
  if (typeof window === 'undefined') return;
  const url = new URL(window.location.href);
  url.searchParams.set('year', String(filtros.anio));
  url.searchParams.set('week', String(filtros.semana));
  url.searchParams.set('fromWeek', String(filtros.semanaDesde));
  url.searchParams.set('toWeek', String(filtros.semanaHasta));
  url.searchParams.set('serie', filtros.serie);
  url.searchParams.set('minsal', filtros.modoMinsal);
  if (filtros.departamento) {
    url.searchParams.set('dept', filtros.departamento);
  } else {
    url.searchParams.delete('dept');
  }
  if (filtros.comparar.length > 0) {
    url.searchParams.set('compare', filtros.comparar.join(','));
  } else {
    url.searchParams.delete('compare');
  }
  window.history.replaceState(null, '', url);
}

let estado = normalizarEstado(estadoInicial, leerEstadoDesdeUrl());
sincronizarUrl(estado);

function estadosIguales(a: FiltrosAnalisis, b: FiltrosAnalisis): boolean {
  return (
    a.anio === b.anio &&
    a.semana === b.semana &&
    a.semanaDesde === b.semanaDesde &&
    a.semanaHasta === b.semanaHasta &&
    a.serie === b.serie &&
    a.departamento === b.departamento &&
    a.modoMinsal === b.modoMinsal &&
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
    sincronizarUrl(detalle);
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
