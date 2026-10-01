// Comportamiento en el navegador de los acordeones de DocumentoTexto: pliegue
// y despliegue animados sobre el <details> nativo. El <details> cambia de
// golpe porque su contenido aparece o desaparece sin transición; aquí se
// anima la altura de `.acordeon-cuerpo` con la Web Animations API y `open` se
// quita al terminar de plegar. Con las animaciones apagadas (interruptor del
// pie o prefers-reduced-motion) se alterna al instante.
import { animacionesActivas } from './animaciones';

const DURACION_MS = 220;
const enCurso = new WeakMap<HTMLDetailsElement, Animation>();

export function alternarAcordeon(
  acordeon: HTMLDetailsElement,
  abrir: boolean = !acordeon.open,
  animar = true,
): void {
  const cuerpo = acordeon.querySelector<HTMLElement>('.acordeon-cuerpo');
  const previa = enCurso.get(acordeon);
  // Si hay una animación a medias, se parte de la altura que muestra ahora.
  const alturaActual = previa ? cuerpo?.getBoundingClientRect().height : null;
  if (previa) {
    enCurso.delete(acordeon);
    previa.cancel();
  }

  if (!cuerpo || !animar || !animacionesActivas()) {
    acordeon.open = abrir;
    return;
  }
  if (!previa && abrir === acordeon.open) return;

  let desde: number;
  let hasta: number;
  if (abrir) {
    acordeon.open = true;
    desde = alturaActual ?? 0;
    hasta = cuerpo.scrollHeight;
  } else {
    desde = alturaActual ?? cuerpo.getBoundingClientRect().height;
    hasta = 0;
  }

  cuerpo.style.overflow = 'hidden';
  const animacion = cuerpo.animate(
    {
      height: [`${desde}px`, `${hasta}px`],
      opacity: abrir ? [desde ? 1 : 0, 1] : [1, 0],
    },
    { duration: DURACION_MS, easing: 'ease-out' },
  );
  enCurso.set(acordeon, animacion);
  animacion.onfinish = () => {
    if (enCurso.get(acordeon) !== animacion) return;
    enCurso.delete(acordeon);
    cuerpo.style.overflow = '';
    if (!abrir) acordeon.open = false;
  };
}

/** Intercepta el clic en el <summary> de cada acordeón dentro de `raiz`. */
export function iniciarAcordeones(raiz: HTMLElement): void {
  raiz.addEventListener('click', (evento) => {
    const resumen = (evento.target as HTMLElement).closest('summary');
    const acordeon = resumen?.parentElement;
    if (!resumen || !(acordeon instanceof HTMLDetailsElement)) return;
    if (!acordeon.classList.contains('acordeon')) return;
    // Un enlace dentro del título conserva su comportamiento.
    if ((evento.target as HTMLElement).closest('a')) return;
    evento.preventDefault();
    alternarAcordeon(acordeon);
  });
}
