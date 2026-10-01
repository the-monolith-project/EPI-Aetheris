/**
 * Interruptor "Animaciones" del pie de página.
 *
 * El estado vive en <html data-animaciones="on|off"> y se guarda en
 * localStorage ('epi:animaciones'). Sin elección guardada manda el sistema:
 * con prefers-reduced-motion arranca apagado. Una elección guardada gana
 * sobre el sistema en ambos sentidos.
 *
 * El script en línea de Layout.astro repite esta misma resolución para fijar
 * el atributo antes del primer pintado (no puede importar módulos); si
 * cambia aquí, cambia allí.
 */

export const CLAVE_ANIMACIONES = 'epi:animaciones';

export type EstadoAnimaciones = 'on' | 'off';

/** Resuelve el estado inicial a partir de lo guardado y de la preferencia del sistema. */
export function resolverAnimaciones(
  guardado: string | null,
  sistemaReduceMovimiento: boolean,
): EstadoAnimaciones {
  if (guardado === 'on' || guardado === 'off') return guardado;
  return sistemaReduceMovimiento ? 'off' : 'on';
}

/** Lee el estado vigente del documento. Sin atributo (sin script) manda el sistema. */
export function animacionesActivas(): boolean {
  if (typeof document === 'undefined') return false;
  const atributo = document.documentElement.dataset.animaciones;
  if (atributo === 'on') return true;
  if (atributo === 'off') return false;
  return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}
