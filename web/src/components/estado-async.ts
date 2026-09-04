// Estado compartido para contenedores que reciben HTML/gráficas de forma
// asíncrona. Objetivo: que los dos desenlaces de una carga sean legibles por
// lectores de pantalla (role="status") y claramente distintos entre sí:
//
//   1. "sin dato para esta selección" -> neutro y esperado. Es parte del
//      mensaje del proyecto sobre huecos de cobertura, no un fallo.
//   2. "no se pudo contactar la fuente" -> se ofrece un botón "Reintentar"
//      que vuelve a disparar la carga. Cero jerga de desarrollador.
//
// Se usa desde los <script> de cliente de los paneles, no como componente
// .astro, porque las siete superficies necesitan actualizar el contenedor
// desde JS después de un fetch.

const CLASE_TEXTO_NEUTRO = 'font-sans text-sm leading-relaxed text-ink-muted';

/**
 * Marca el contenedor como región viva para lectores de pantalla, sin pisar
 * un role/aria-live que ya venga del HTML del componente.
 */
export function marcarRegionEstado(contenedor: HTMLElement): void {
  if (
    !contenedor.hasAttribute('role') &&
    !contenedor.hasAttribute('aria-live')
  ) {
    contenedor.setAttribute('role', 'status');
  }
}

/**
 * Desenlace neutro: la fuente respondió, pero no hay datos para lo que el
 * usuario seleccionó. No es un error.
 */
export function renderSinDato(
  contenedor: HTMLElement,
  mensaje = 'Sin datos para esta selección.',
): void {
  marcarRegionEstado(contenedor);
  const p = document.createElement('p');
  p.className = CLASE_TEXTO_NEUTRO;
  p.textContent = mensaje;
  contenedor.replaceChildren(p);
}

/**
 * Desenlace de error de red/servicio: no se pudo contactar la fuente. Ofrece
 * "Reintentar", que vuelve a llamar a `alReintentar`.
 */
export function renderErrorFuente(
  contenedor: HTMLElement,
  alReintentar: () => void,
  mensaje = 'No se pudo contactar la fuente de datos en este momento.',
): void {
  marcarRegionEstado(contenedor);

  const caja = document.createElement('div');
  caja.className =
    'rounded-lg border border-secondary bg-secondary/25 p-3';

  const p = document.createElement('p');
  p.className = 'font-sans text-sm leading-relaxed text-ink';
  p.textContent = mensaje;

  const boton = document.createElement('button');
  boton.type = 'button';
  boton.className =
    'mt-2 rounded-lg border border-border bg-surface px-3 py-1.5 font-sans text-xs font-semibold text-ink transition-colors hover:border-accent/50 hover:text-accent';
  boton.textContent = 'Reintentar';
  boton.addEventListener('click', () => {
    alReintentar();
  });

  caja.append(p, boton);
  contenedor.replaceChildren(caja);
}
