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

export const MOTIVO_NO_DISPONIBLE_DEFECTO =
  'Los datos no están disponibles en este despliegue.';

export type RespuestaNoDisponible = {
  disponible: false;
  motivo?: string;
};

/**
 * Contrato 200 { disponible: false, motivo } (#72, #84): la fuente respondió,
 * pero el recurso no está generado o la tabla no está cargada. No es un
 * error de red.
 */
export function esNoDisponible(datos: unknown): datos is RespuestaNoDisponible {
  return (
    typeof datos === 'object' &&
    datos !== null &&
    (datos as { disponible?: unknown }).disponible === false
  );
}

export function motivoNoDisponible(datos: RespuestaNoDisponible): string {
  const motivo = datos.motivo?.trim();
  return motivo || MOTIVO_NO_DISPONIBLE_DEFECTO;
}

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
  contenedor.removeAttribute('aria-busy');
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
  caja.className = 'rounded-lg border border-secondary bg-secondary/25 p-3';

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

/**
 * Pinta un esqueleto con forma de matriz (rejilla de barras) mientras carga.
 */
export function renderEsqueletoMatriz(
  contenedor: HTMLElement,
  filas = 7,
): void {
  const rejilla = document.createElement('div');
  rejilla.className = 'flex h-full w-full flex-col justify-between gap-2.5 p-2';
  rejilla.setAttribute('aria-hidden', 'true');
  for (let i = 0; i < filas; i++) {
    const barra = document.createElement('div');
    barra.className = 'skeleton h-7 w-full rounded';
    rejilla.appendChild(barra);
  }
  contenedor.replaceChildren(rejilla);
}

/**
 * Pinta un esqueleto con forma de traza (tres líneas horizontales) mientras carga.
 */
export function renderEsqueletoTraza(contenedor: HTMLElement): void {
  const contenedorTraza = document.createElement('div');
  contenedorTraza.className =
    'flex h-full w-full flex-col justify-around gap-4 p-4';
  contenedorTraza.setAttribute('aria-hidden', 'true');
  for (let i = 0; i < 3; i++) {
    const linea = document.createElement('div');
    linea.className = 'skeleton h-5 w-full rounded';
    contenedorTraza.appendChild(linea);
  }
  contenedor.replaceChildren(contenedorTraza);
}

/**
 * Pinta un esqueleto con forma de visor (rectángulo a sangre) para mapa.
 */
export function renderEsqueletoVisor(contenedor: HTMLElement): void {
  const bloque = document.createElement('div');
  bloque.className = 'skeleton h-full w-full rounded-lg';
  bloque.setAttribute('aria-hidden', 'true');
  contenedor.replaceChildren(bloque);
}

/**
 * Pinta un esqueleto para panel de registro.
 */
export function renderEsqueletoRegistro(contenedor: HTMLElement): void {
  const contenedorReg = document.createElement('div');
  contenedorReg.className = 'flex h-full w-full flex-col gap-3 p-3';
  contenedorReg.setAttribute('aria-hidden', 'true');
  const t = document.createElement('div');
  t.className = 'skeleton h-4 w-1/3 rounded';
  const c1 = document.createElement('div');
  c1.className = 'skeleton h-10 w-full rounded';
  const c2 = document.createElement('div');
  c2.className = 'skeleton h-10 w-full rounded';
  contenedorReg.append(t, c1, c2);
  contenedor.replaceChildren(contenedorReg);
}
