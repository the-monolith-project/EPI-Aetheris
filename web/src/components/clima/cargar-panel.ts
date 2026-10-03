// Ciclo de carga común a los paneles de /analisis/clima: esqueleto mientras
// llega la respuesta, "sin dato" cuando el backend contesta
// { disponible: false } y "reintentar" ante un error de red. Cada panel trae
// dos contenedores: [data-estado] (esqueleto, aviso o error) y
// [data-contenido] (oculto hasta tener datos, porque ECharts necesita medir
// un contenedor visible).
import {
  esNoDisponible,
  motivoNoDisponible,
  renderEsqueletoTraza,
  renderErrorFuente,
  renderSinDato,
} from '../estado-async';
import type { RespuestaNoDisponible } from '../estado-async';

export const CLASE_SELECT =
  'rounded-lg border border-border bg-bg px-3 py-1.5 font-sans text-sm text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent';
export const CLASE_NOTA =
  'font-sans text-xs leading-relaxed text-ink-muted max-w-[68ch]';

/** Ejecuta `activar` la primera vez que el panel se acerca a la pantalla. */
export function activarAlEntrar(
  elemento: HTMLElement,
  activar: () => void,
): void {
  if (typeof IntersectionObserver === 'undefined') {
    activar();
    return;
  }
  const observador = new IntersectionObserver(
    (entradas) => {
      if (entradas.some((e) => e.isIntersecting)) {
        observador.disconnect();
        activar();
      }
    },
    { rootMargin: '300px 0px' },
  );
  observador.observe(elemento);
}

/**
 * Pide los datos y pinta el panel. `pintar` recibe el contenido ya visible.
 * Un panel con error se puede reintentar sin recargar la página.
 */
export async function cargarPanel<T>(
  panel: HTMLElement,
  obtener: () => Promise<T | RespuestaNoDisponible>,
  pintar: (datos: T, contenido: HTMLElement) => void | Promise<void>,
): Promise<void> {
  const estado = panel.querySelector<HTMLElement>('[data-estado]');
  const contenido = panel.querySelector<HTMLElement>('[data-contenido]');
  if (!estado || !contenido) return;

  estado.hidden = false;
  contenido.hidden = true;
  estado.setAttribute('aria-busy', 'true');
  renderEsqueletoTraza(estado);
  try {
    const datos = await obtener();
    if (esNoDisponible(datos)) {
      renderSinDato(estado, motivoNoDisponible(datos));
      return;
    }
    estado.hidden = true;
    contenido.hidden = false;
    await pintar(datos, contenido);
  } catch {
    estado.hidden = false;
    contenido.hidden = true;
    renderErrorFuente(
      estado,
      () => void cargarPanel(panel, obtener, pintar),
      'No se pudieron cargar los datos de este panel.',
    );
  }
}

export function llenarSelect(
  select: HTMLSelectElement,
  opciones: { valor: string; texto: string }[],
  valorInicial: string,
): void {
  select.replaceChildren(
    ...opciones.map(({ valor, texto }) => {
      const opcion = document.createElement('option');
      opcion.value = valor;
      opcion.textContent = texto;
      return opcion;
    }),
  );
  select.value = valorInicial;
}
