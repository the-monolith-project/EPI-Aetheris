/**
 * La rueda del ratón desplaza la página, no el mapa: con el zoom de Leaflet
 * activo, pasar por encima de un mapa grande dejaba el scroll "pegado" a él
 * cuando la intención era ver los gráficos de más abajo. El zoom con rueda
 * solo ocurre con Ctrl (⌘ en macOS) pulsado; los botones +/- y el teclado
 * siguen igual. Una pista breve avisa del gesto la primera vez que alguien
 * intenta hacer scroll sobre el mapa.
 */

const PISTA_MS = 1400;

export function esPlataformaMac(): boolean {
  return /Mac|iPhone|iPad/.test(navigator.userAgent);
}

export function protegerScrollMapa(contenedor: HTMLElement): void {
  const pista = document.createElement('div');
  pista.className = 'mapa-pista-scroll';
  pista.setAttribute('aria-hidden', 'true');
  pista.textContent = esPlataformaMac()
    ? 'Usa ⌘ + rueda para acercar el mapa'
    : 'Usa Ctrl + rueda para acercar el mapa';
  contenedor.append(pista);

  let temporizador: number | undefined;
  const mostrarPista = () => {
    pista.classList.add('visible');
    window.clearTimeout(temporizador);
    temporizador = window.setTimeout(
      () => pista.classList.remove('visible'),
      PISTA_MS,
    );
  };

  // En captura y sin preventDefault: Leaflet no ve el evento (su manejador
  // está en burbuja sobre este mismo contenedor) y el navegador desplaza la
  // página con normalidad.
  contenedor.addEventListener(
    'wheel',
    (evento) => {
      if (evento.ctrlKey || evento.metaKey) return;
      evento.stopPropagation();
      mostrarPista();
    },
    { capture: true, passive: true },
  );
}
