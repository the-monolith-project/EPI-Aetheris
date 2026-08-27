export function vincularMarcasPlot<T>(
  grafica: ParentNode,
  selector: string,
  datos: readonly T[],
  etiqueta: (dato: T) => string,
  activar: (dato: T) => void,
): void {
  grafica.querySelectorAll<SVGElement>('[aria-label]').forEach((marca) => {
    if (!marca.matches(selector)) marca.removeAttribute('aria-label');
  });
  grafica.querySelectorAll<SVGElement>(selector).forEach((marca, indice) => {
    const indiceVinculado = (marca as SVGElement & { __data__?: unknown })
      .__data__;
    const indiceDato =
      typeof indiceVinculado === 'number' ? indiceVinculado : indice;
    const dato = datos[indiceDato];
    if (dato === undefined) return;

    marca.setAttribute('tabindex', '0');
    marca.setAttribute('role', 'button');
    marca.setAttribute('aria-label', etiqueta(dato));
    marca.style.cursor = 'pointer';
    marca.addEventListener('click', () => activar(dato));
    marca.addEventListener('keydown', (evento) => {
      if (evento.key !== 'Enter' && evento.key !== ' ') return;
      evento.preventDefault();
      activar(dato);
    });
  });
}
