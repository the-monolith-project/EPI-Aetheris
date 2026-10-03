// Piezas de HTML compartidas por las gráficas de la predicción: leyenda
// interactiva, selector de periodo, detalle con la tabla alternativa y la
// detección de pantalla estrecha. Van fuera del SVG para que sean botones
// reales (foco, teclado, aria-pressed) y no texto dibujado.
import {
  TablaAlternativa,
  type ColumnaTabla,
} from '../../lib/tabla-alternativa';
import {
  SERIE,
  type NombreSerie,
  type Visibles,
} from '../../lib/nowcast-opciones';

/** Ancho del contenedor por debajo del cual las gráficas pasan a la versión móvil. */
export const ANCHO_MOVIL = 520;

export function esMovil(contenedor: HTMLElement): boolean {
  return (contenedor.clientWidth || window.innerWidth) < ANCHO_MOVIL;
}

/**
 * Avisa cuando el contenedor cruza el ancho móvil, para reconstruir la opción
 * (márgenes, etiquetas y tipografía distintos). Devuelve la función que deja
 * de observar.
 */
export function alCruzarAnchoMovil(
  contenedor: HTMLElement,
  alCruzar: () => void,
): () => void {
  let movil = esMovil(contenedor);
  const observador = new ResizeObserver(() => {
    const ahora = esMovil(contenedor);
    if (ahora !== movil) {
      movil = ahora;
      alCruzar();
    }
  });
  observador.observe(contenedor);
  return () => observador.disconnect();
}

export type MuestraLeyenda =
  'continua' | 'punteada' | 'banda50' | 'banda95' | 'anillo' | 'segmento';

export interface ItemLeyenda {
  nombre: NombreSerie;
  muestra: MuestraLeyenda;
}

/**
 * Texto reducido de cada serie para pantallas estrechas (< sm): en 375 px los
 * nombres completos obligaban a una fila por botón y la leyenda ocupaba más
 * alto que la propia gráfica. El nombre completo sigue siendo el accesible.
 */
const NOMBRE_CORTO: Record<NombreSerie, string> = {
  [SERIE.publicado]: 'Publicados',
  [SERIE.mediana]: 'Mediana',
  [SERIE.rango50]: 'Rango 50 %',
  [SERIE.rango95]: 'Rango 95 %',
  [SERIE.fuera]: 'Fuera del 95 %',
  [SERIE.diferencia]: 'Diferencia',
};

function muestra(tipo: MuestraLeyenda): HTMLElement {
  const m = document.createElement('span');
  m.setAttribute('aria-hidden', 'true');
  m.className = 'inline-block shrink-0';
  const azul = 'var(--color-estimacion)';
  const tinta = 'var(--color-ink)';
  switch (tipo) {
    case 'continua':
      m.style.cssText = `width:18px;border-top:2.5px solid ${tinta}`;
      break;
    case 'punteada':
      m.style.cssText = `width:18px;border-top:2.5px dashed ${azul}`;
      break;
    case 'banda50':
      m.style.cssText = 'width:18px;height:10px;border-radius:2px;';
      m.style.background = `color-mix(in srgb, ${azul} 42%, transparent)`;
      break;
    case 'banda95':
      m.style.cssText = `width:18px;height:10px;border-radius:2px;`;
      m.style.background = `color-mix(in srgb, ${azul} 20%, transparent)`;
      break;
    case 'segmento':
      m.style.cssText = `width:3px;height:14px;border-radius:2px;opacity:.6;background:${azul}`;
      break;
    case 'anillo':
      m.style.cssText = `width:9px;height:9px;border-radius:999px;border:2px solid ${tinta};background:var(--color-surface)`;
      break;
  }
  return m;
}

export interface Leyenda {
  elemento: HTMLElement;
  /** Vuelve a pintar el estado de los botones (p. ej. tras reiniciar). */
  sincronizar: (visibles: Visibles) => void;
}

/**
 * Leyenda de botones que muestran u ocultan cada serie. `alCambiar` recibe
 * la serie tocada y su nuevo estado; `alResaltar`, la serie bajo el puntero o
 * el foco (null al salir).
 */
export function crearLeyenda(
  items: ItemLeyenda[],
  visibles: Visibles,
  alCambiar: (nombre: NombreSerie, visible: boolean) => void,
  alResaltar: (nombre: NombreSerie | null) => void,
): Leyenda {
  const grupo = document.createElement('div');
  grupo.className = 'flex flex-wrap gap-1 sm:gap-1.5';
  grupo.setAttribute('role', 'group');
  grupo.setAttribute('aria-label', 'Series de la gráfica');
  const botones = new Map<NombreSerie, HTMLButtonElement>();

  const pintar = (b: HTMLButtonElement, activo: boolean) => {
    b.setAttribute('aria-pressed', String(activo));
    b.classList.toggle('opacity-55', !activo);
    b.querySelector('[data-texto]')?.classList.toggle('line-through', !activo);
  };

  for (const item of items) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className =
      'inline-flex min-h-[32px] items-center gap-1.5 rounded-full border border-border bg-surface px-2 py-1 font-sans text-xs text-ink sm:gap-2 sm:px-3 transition-colors hover:border-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent';
    const texto = document.createElement('span');
    texto.dataset.texto = '';
    const corto = document.createElement('span');
    corto.className = 'sm:hidden';
    corto.textContent = NOMBRE_CORTO[item.nombre];
    const largo = document.createElement('span');
    largo.className = 'max-sm:hidden';
    largo.textContent = item.nombre;
    texto.append(corto, largo);
    b.setAttribute('aria-label', item.nombre);
    b.append(muestra(item.muestra), texto);
    pintar(b, visibles[item.nombre] !== false);
    b.addEventListener('click', () => {
      const activo = b.getAttribute('aria-pressed') !== 'true';
      pintar(b, activo);
      alCambiar(item.nombre, activo);
    });
    b.addEventListener('mouseenter', () => alResaltar(item.nombre));
    b.addEventListener('mouseleave', () => alResaltar(null));
    b.addEventListener('focus', () => alResaltar(item.nombre));
    b.addEventListener('blur', () => alResaltar(null));
    botones.set(item.nombre, b);
    grupo.appendChild(b);
  }

  return {
    elemento: grupo,
    sincronizar: (v) => {
      for (const [nombre, b] of botones) pintar(b, v[nombre] !== false);
    },
  };
}

/** Conjunto de botones excluyentes (aria-pressed) para elegir el periodo mostrado. */
export function crearSelector<T extends string>(
  etiqueta: string,
  opciones: { valor: T; texto: string; descripcion: string }[],
  activa: T,
  alElegir: (valor: T, descripcion: string) => void,
): { elemento: HTMLElement; elegir: (valor: T) => void } {
  const grupo = document.createElement('div');
  grupo.className =
    'inline-flex rounded-full border border-border bg-surface p-0.5';
  grupo.setAttribute('role', 'group');
  grupo.setAttribute('aria-label', etiqueta);
  const botones = new Map<T, HTMLButtonElement>();
  const pintar = (valor: T) => {
    for (const [v, b] of botones) {
      const on = v === valor;
      b.setAttribute('aria-pressed', String(on));
      b.className = `min-h-[30px] rounded-full px-3 py-1 font-sans text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
        on ? 'bg-accent text-accent-ink' : 'text-ink-muted hover:text-ink'
      }`;
    }
  };
  for (const o of opciones) {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = o.texto;
    b.addEventListener('click', () => {
      pintar(o.valor);
      alElegir(o.valor, o.descripcion);
    });
    botones.set(o.valor, b);
    grupo.appendChild(b);
  }
  pintar(activa);
  return { elemento: grupo, elegir: pintar };
}

/** `<details>` con la tabla de los valores de la gráfica, construida al abrirlo. */
export function crearDetalleTabla<T>(
  caption: string,
  columnas: ColumnaTabla[],
  obtenerDatos: () => T[],
): HTMLDetailsElement {
  const details = document.createElement('details');
  details.className = 'mt-3 rounded-xl border border-border bg-bg p-3';
  const resumen = document.createElement('summary');
  resumen.className =
    'cursor-pointer font-sans text-xs font-medium text-ink-muted hover:text-ink';
  resumen.textContent = 'Ver los datos en tabla';
  const contenedorTabla = document.createElement('div');
  details.append(resumen, contenedorTabla);
  new TablaAlternativa({
    details,
    contenedorTabla,
    caption,
    columnas,
    obtenerDatos,
  });
  return details;
}
