/**
 * Movimiento de la portada y de /analisis: entrada de bloques al hacer
 * scroll y cifras que cuentan hacia arriba.
 *
 * Contrato con el CSS (global.css): el HTML ya esta en su estado final.
 * Solo si hay JavaScript, IntersectionObserver y la persona no pidio
 * reducir el movimiento, se marca <html data-animar> y los bloques .aparece
 * pasan a ocultos hasta que entran en pantalla. Sin ese atributo no cambia
 * nada, asi que sin script o con reduced-motion la pagina se ve completa.
 */

const REDUCIR = '(prefers-reduced-motion: reduce)';

function permiteMovimiento(): boolean {
  return (
    typeof window !== 'undefined' &&
    'IntersectionObserver' in window &&
    !window.matchMedia(REDUCIR).matches
  );
}

/** Marca los bloques .aparece como vistos cuando entran en pantalla. */
function activarEntradas(): void {
  const bloques = document.querySelectorAll<HTMLElement>('.aparece');
  if (bloques.length === 0) return;

  const observador = new IntersectionObserver(
    (entradas) => {
      for (const entrada of entradas) {
        if (!entrada.isIntersecting) continue;
        entrada.target.classList.add('visto');
        observador.unobserve(entrada.target);
      }
    },
    { rootMargin: '0px 0px -12% 0px', threshold: 0.1 },
  );
  bloques.forEach((bloque) => observador.observe(bloque));
}

/**
 * Cuenta de 0 al valor final de cada [data-cifra] cuando entra en pantalla.
 * El valor final ya esta escrito en el HTML; el atributo solo lo repite en
 * numero para no tener que parsearlo del texto.
 */
function activarCifras(): void {
  const cifras = document.querySelectorAll<HTMLElement>('[data-cifra]');
  if (cifras.length === 0) return;

  const DURACION = 1400;
  const formato = new Intl.NumberFormat('es-SV');

  const contar = (el: HTMLElement): void => {
    const final = Number(el.dataset.cifra);
    if (!Number.isFinite(final)) return;
    const textoFinal = el.textContent ?? '';
    const inicio = performance.now();
    const paso = (ahora: number): void => {
      const t = Math.min(1, (ahora - inicio) / DURACION);
      // Salida suave: arranca rapido y frena al llegar.
      const e = 1 - Math.pow(1 - t, 4);
      el.textContent = formato.format(Math.round(final * e));
      if (t < 1) requestAnimationFrame(paso);
      else el.textContent = textoFinal;
    };
    requestAnimationFrame(paso);
  };

  const observador = new IntersectionObserver(
    (entradas) => {
      for (const entrada of entradas) {
        if (!entrada.isIntersecting) continue;
        contar(entrada.target as HTMLElement);
        observador.unobserve(entrada.target);
      }
    },
    { threshold: 0.6 },
  );
  cifras.forEach((cifra) => observador.observe(cifra));
}

export function iniciarMovimiento(): void {
  if (!permiteMovimiento()) return;
  document.documentElement.dataset.animar = '1';
  activarEntradas();
  activarCifras();
}
