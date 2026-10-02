// Comportamiento de los términos del glosario (ver terminos.ts). Un solo
// manejador delegado en el documento: sirve a cualquier término, incluso a los
// que llegan dentro de HTML inyectado.
//
// Con ratón la nota se abre al pasar el cursor; con teclado, al enfocar el
// término; en pantallas táctiles, al tocarlo. Escape la cierra y devuelve el
// foco al término.

const RETRASO_ABRIR = 120;
const RETRASO_CERRAR = 220;
const SEPARACION = 8;

let abierto: HTMLElement | null = null;
let temporizador: ReturnType<typeof setTimeout> | undefined;

function partes(contenedor: Element) {
  const boton = contenedor.querySelector<HTMLButtonElement>(
    '.termino-glosario-boton',
  );
  const nota = contenedor.querySelector<HTMLElement>('.termino-glosario-nota');
  return boton && nota ? { boton, nota } : null;
}

function colocar(boton: HTMLElement, nota: HTMLElement): void {
  const caja = boton.getBoundingClientRect();
  const { width, height } = nota.getBoundingClientRect();
  const ancho = document.documentElement.clientWidth;
  const alto = window.innerHeight;
  const izquierda = Math.min(
    Math.max(SEPARACION, caja.left),
    Math.max(SEPARACION, ancho - width - SEPARACION),
  );
  const cabeAbajo = caja.bottom + SEPARACION + height <= alto;
  const arriba = cabeAbajo
    ? caja.bottom + SEPARACION
    : Math.max(SEPARACION, caja.top - SEPARACION - height);
  nota.style.left = `${izquierda}px`;
  nota.style.top = `${arriba}px`;
}

function cerrar(devolverFoco = false): void {
  clearTimeout(temporizador);
  if (!abierto) return;
  const p = partes(abierto);
  if (p) {
    if (p.nota.matches(':popover-open')) p.nota.hidePopover();
    p.boton.setAttribute('aria-expanded', 'false');
    if (devolverFoco) p.boton.focus();
  }
  abierto = null;
}

function abrir(contenedor: HTMLElement): void {
  clearTimeout(temporizador);
  if (abierto === contenedor) return;
  cerrar();
  const p = partes(contenedor);
  if (!p) return;
  p.nota.showPopover();
  colocar(p.boton, p.nota);
  p.boton.setAttribute('aria-expanded', 'true');
  abierto = contenedor;
}

function programar(accion: () => void, retraso: number): void {
  clearTimeout(temporizador);
  temporizador = setTimeout(accion, retraso);
}

function contenedorDe(objetivo: EventTarget | null): HTMLElement | null {
  return objetivo instanceof Element
    ? objetivo.closest<HTMLElement>('.termino-glosario')
    : null;
}

let iniciado = false;

export function iniciarTerminos(): void {
  if (iniciado || typeof document === 'undefined') return;
  if (!('showPopover' in HTMLElement.prototype)) return;
  iniciado = true;

  document.addEventListener('pointerover', (evento) => {
    if (evento.pointerType !== 'mouse') return;
    const contenedor = contenedorDe(evento.target);
    if (contenedor) programar(() => abrir(contenedor), RETRASO_ABRIR);
    else if (abierto === null) clearTimeout(temporizador);
  });

  document.addEventListener('pointerout', (evento) => {
    if (evento.pointerType !== 'mouse') return;
    const contenedor = contenedorDe(evento.target);
    if (!contenedor || contenedorDe(evento.relatedTarget) === contenedor)
      return;
    if (abierto === contenedor) programar(() => cerrar(), RETRASO_CERRAR);
    else clearTimeout(temporizador);
  });

  document.addEventListener('focusin', (evento) => {
    const contenedor = contenedorDe(evento.target);
    if (contenedor) abrir(contenedor);
    else cerrar();
  });

  document.addEventListener('click', (evento) => {
    const boton = (evento.target as Element | null)?.closest(
      '.termino-glosario-boton',
    );
    const contenedor = contenedorDe(evento.target);
    if (boton && contenedor) {
      // Con ratón la nota ya se abrió al pasar el cursor; Intro o Espacio
      // (detail 0) la alternan. El toque la abre y se cierra tocando fuera.
      if (abierto !== contenedor) abrir(contenedor);
      else if (evento.detail === 0) cerrar();
    } else if (!contenedor) {
      cerrar();
    }
  });

  document.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape' && abierto) {
      evento.preventDefault();
      cerrar(true);
    }
  });

  window.addEventListener('scroll', () => cerrar(), { passive: true });
  window.addEventListener('resize', () => cerrar());
}
