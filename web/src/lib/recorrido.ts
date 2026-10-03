// Utilidades del recorrido paso a paso de los laboratorios de las fichas.
// El recorrido es una visualización de un cálculo ya hecho: solo se usa con
// las animaciones activas (animacionesActivas()); sin ellas, el laboratorio
// muestra el resultado directamente.

export const MS_ETAPA = 900;

export function esperar(ms: number): Promise<void> {
  return new Promise((resolver) => setTimeout(resolver, ms));
}

/** Llama a `cuadro(p)` con p de 0 a 1 durante `duracion` ms, con salida suave. */
export function animar(
  duracion: number,
  cuadro: (p: number) => void,
): Promise<void> {
  return new Promise((resolver) => {
    const inicio = performance.now();
    const paso = (ahora: number) => {
      const p = Math.min(1, (ahora - inicio) / duracion);
      cuadro(1 - Math.pow(1 - p, 3));
      if (p < 1) requestAnimationFrame(paso);
      else resolver();
    };
    requestAnimationFrame(paso);
  });
}

/** Marca las etapas: todas en espera al empezar. */
export function prepararEtapas(etapas: HTMLElement[]): void {
  etapas.forEach((el) => {
    el.classList.remove('lab-activo');
    el.classList.add('lab-espera');
  });
}

/** Ilumina una etapa y la trae a la vista si quedó fuera de pantalla. */
export function activarEtapa(etapa: HTMLElement): void {
  etapa.classList.remove('lab-espera');
  etapa.classList.add('lab-activo');
  const caja = etapa.getBoundingClientRect();
  if (caja.top < 0 || caja.bottom > window.innerHeight) {
    etapa.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
}

export function cerrarEtapa(etapa: HTMLElement): void {
  etapa.classList.remove('lab-activo');
}

export function limpiarEtapas(etapas: HTMLElement[]): void {
  etapas.forEach((el) => el.classList.remove('lab-espera', 'lab-activo'));
}
