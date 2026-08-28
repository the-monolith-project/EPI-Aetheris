export const EVENTO_LAYOUT_ANALISIS = 'epi:analysis-layout-changed';

export const PANELES_ANALITICOS = [
  { id: 'mapa', etiqueta: 'Mapa departamental' },
  { id: 'presion', etiqueta: 'Presión por semana' },
  { id: 'temporadas', etiqueta: 'Comparación de temporadas' },
  { id: 'departamentos', etiqueta: 'Comparación de departamentos' },
  { id: 'calendario', etiqueta: 'Calendario epidémico' },
  { id: 'clima', etiqueta: 'Clima × presión' },
  { id: 'disponibilidad', etiqueta: 'Disponibilidad de datos' },
  { id: 'calidad', etiqueta: 'Perfil de calidad' },
] as const;

export type PanelAnalitico = (typeof PANELES_ANALITICOS)[number]['id'];
export type TamanoPanel = 'pequeno' | 'mediano' | 'grande';
export type ZoomTemporal = 100 | 150 | 200;
export type VistaAnalisis =
  'general' | 'territorial' | 'temporal' | 'clima' | 'calidad';

export interface EstadoLayoutAnalisis {
  vista: VistaAnalisis;
  panelesVisibles: PanelAnalitico[];
  tamanos: Record<PanelAnalitico, TamanoPanel>;
  panelEnFoco: PanelAnalitico | null;
  zoomTemporal: ZoomTemporal;
}

export interface CambiosLayoutAnalisis extends Omit<
  Partial<EstadoLayoutAnalisis>,
  'tamanos'
> {
  tamanos?: Partial<Record<PanelAnalitico, TamanoPanel>>;
}

const TODOS_LOS_PANELES = PANELES_ANALITICOS.map(({ id }) => id);

const PRESETS: Record<
  VistaAnalisis,
  Pick<EstadoLayoutAnalisis, 'panelesVisibles' | 'tamanos'>
> = {
  general: {
    panelesVisibles: ['mapa', 'presion', 'temporadas', 'departamentos'],
    tamanos: {
      mapa: 'mediano',
      presion: 'grande',
      temporadas: 'grande',
      departamentos: 'grande',
    },
  },
  territorial: {
    panelesVisibles: ['mapa', 'presion', 'departamentos'],
    tamanos: { mapa: 'grande', presion: 'grande', departamentos: 'grande' },
  },
  temporal: {
    panelesVisibles: ['temporadas', 'calendario'],
    tamanos: { temporadas: 'grande', calendario: 'grande' },
  },
  clima: {
    panelesVisibles: ['mapa', 'clima'],
    tamanos: { mapa: 'mediano', clima: 'grande' },
  },
  calidad: {
    panelesVisibles: ['disponibilidad', 'calidad'],
    tamanos: { disponibilidad: 'grande', calidad: 'mediano' },
  },
};

const TAMANOS_PREDETERMINADOS: Record<PanelAnalitico, TamanoPanel> = {
  mapa: 'mediano',
  presion: 'grande',
  temporadas: 'grande',
  departamentos: 'grande',
  calendario: 'grande',
  clima: 'grande',
  disponibilidad: 'grande',
  calidad: 'mediano',
};

export const LAYOUT_ANALISIS_PREDETERMINADO: EstadoLayoutAnalisis = {
  vista: 'general',
  panelesVisibles: [...PRESETS.general.panelesVisibles],
  tamanos: { ...TAMANOS_PREDETERMINADOS, ...PRESETS.general.tamanos },
  panelEnFoco: null,
  zoomTemporal: 100,
};

let estado = clonarEstado(LAYOUT_ANALISIS_PREDETERMINADO);

function esPanelAnalitico(valor: string): valor is PanelAnalitico {
  return TODOS_LOS_PANELES.includes(valor as PanelAnalitico);
}

function esVistaAnalisis(valor: string): valor is VistaAnalisis {
  return Object.hasOwn(PRESETS, valor);
}

function esTamanoPanel(valor: string): valor is TamanoPanel {
  return valor === 'pequeno' || valor === 'mediano' || valor === 'grande';
}

function esZoomTemporal(valor: number): valor is ZoomTemporal {
  return valor === 100 || valor === 150 || valor === 200;
}

function clonarEstado(valor: EstadoLayoutAnalisis): EstadoLayoutAnalisis {
  return {
    ...valor,
    panelesVisibles: [...valor.panelesVisibles],
    tamanos: { ...valor.tamanos },
  };
}

function normalizarEstado(
  base: EstadoLayoutAnalisis,
  cambios: CambiosLayoutAnalisis,
): EstadoLayoutAnalisis {
  const candidato = clonarEstado({
    ...base,
    ...cambios,
    tamanos: { ...base.tamanos, ...cambios.tamanos },
  });
  candidato.vista = esVistaAnalisis(candidato.vista)
    ? candidato.vista
    : 'general';
  candidato.panelesVisibles = [
    ...new Set(candidato.panelesVisibles.filter(esPanelAnalitico)),
  ];
  candidato.tamanos = TODOS_LOS_PANELES.reduce<
    Record<PanelAnalitico, TamanoPanel>
  >(
    (tamanos, panel) => {
      const tamano = candidato.tamanos[panel];
      tamanos[panel] = esTamanoPanel(tamano)
        ? tamano
        : TAMANOS_PREDETERMINADOS[panel];
      return tamanos;
    },
    {} as Record<PanelAnalitico, TamanoPanel>,
  );
  candidato.panelEnFoco =
    candidato.panelEnFoco &&
    candidato.panelesVisibles.includes(candidato.panelEnFoco)
      ? candidato.panelEnFoco
      : null;
  candidato.zoomTemporal = esZoomTemporal(candidato.zoomTemporal)
    ? candidato.zoomTemporal
    : 100;
  return candidato;
}

function estadosIguales(
  a: EstadoLayoutAnalisis,
  b: EstadoLayoutAnalisis,
): boolean {
  return (
    a.vista === b.vista &&
    a.panelEnFoco === b.panelEnFoco &&
    a.zoomTemporal === b.zoomTemporal &&
    a.panelesVisibles.length === b.panelesVisibles.length &&
    a.panelesVisibles.every(
      (panel, indice) => panel === b.panelesVisibles[indice],
    ) &&
    TODOS_LOS_PANELES.every((panel) => a.tamanos[panel] === b.tamanos[panel])
  );
}

function emitirCambio(): void {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(
    new CustomEvent<EstadoLayoutAnalisis>(EVENTO_LAYOUT_ANALISIS, {
      detail: obtenerLayoutAnalisis(),
    }),
  );
}

export function obtenerLayoutAnalisis(): EstadoLayoutAnalisis {
  return clonarEstado(estado);
}

export function actualizarLayoutAnalisis(
  cambios: CambiosLayoutAnalisis,
): EstadoLayoutAnalisis {
  const siguiente = normalizarEstado(estado, cambios);
  if (estadosIguales(estado, siguiente)) return obtenerLayoutAnalisis();
  estado = siguiente;
  emitirCambio();
  return obtenerLayoutAnalisis();
}

export function aplicarVistaAnalisis(
  vista: VistaAnalisis,
): EstadoLayoutAnalisis {
  const preset = PRESETS[vista];
  return actualizarLayoutAnalisis({
    vista,
    panelesVisibles: [...preset.panelesVisibles],
    tamanos: { ...TAMANOS_PREDETERMINADOS, ...preset.tamanos },
    panelEnFoco: null,
  });
}

export function restablecerLayoutAnalisis(): EstadoLayoutAnalisis {
  estado = clonarEstado(LAYOUT_ANALISIS_PREDETERMINADO);
  emitirCambio();
  return obtenerLayoutAnalisis();
}

export function suscribirLayoutAnalisis(
  listener: (layout: EstadoLayoutAnalisis) => void,
  emitirInicial = true,
): () => void {
  if (emitirInicial) listener(obtenerLayoutAnalisis());
  if (typeof window === 'undefined') return () => undefined;

  const manejarEvento = (evento: Event) => {
    listener(
      clonarEstado((evento as CustomEvent<EstadoLayoutAnalisis>).detail),
    );
  };
  window.addEventListener(EVENTO_LAYOUT_ANALISIS, manejarEvento);
  return () =>
    window.removeEventListener(EVENTO_LAYOUT_ANALISIS, manejarEvento);
}
