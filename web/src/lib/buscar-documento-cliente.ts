// Buscador de palabras dentro de un documento (DocumentoTexto): filtra las
// secciones, abre las que tienen coincidencias y resalta el texto con <mark>.
// Las funciones de comparación (sin tildes ni mayúsculas) están en
// buscar-en-documento.ts, que se prueba aparte.
import { encontrar } from './buscar-en-documento';

const MINIMO = 2;

interface Elementos {
  raiz: HTMLElement;
  entrada: HTMLInputElement;
  estado: HTMLElement;
  indice: HTMLElement | null;
}

function quitarMarcas(raiz: HTMLElement) {
  const marcas = raiz.querySelectorAll('mark[data-busqueda]');
  const padres = new Set<Node>();
  for (const marca of marcas) {
    const padre = marca.parentNode;
    if (!padre) continue;
    padre.replaceChild(document.createTextNode(marca.textContent ?? ''), marca);
    padres.add(padre);
  }
  for (const padre of padres) padre.normalize();
}

function nodosDeTexto(contenedor: Element): Text[] {
  const recorrido = document.createTreeWalker(
    contenedor,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: (nodo) =>
        nodo.parentElement?.closest('script, style, [data-sin-busqueda]')
          ? NodeFilter.FILTER_REJECT
          : NodeFilter.FILTER_ACCEPT,
    },
  );
  const nodos: Text[] = [];
  for (let n = recorrido.nextNode(); n; n = recorrido.nextNode()) {
    nodos.push(n as Text);
  }
  return nodos;
}

/** Resalta las coincidencias de `consulta` en `contenedor`; devuelve cuántas. */
function resaltar(contenedor: Element, consulta: string): number {
  let total = 0;
  for (const nodo of nodosDeTexto(contenedor)) {
    const texto = nodo.data;
    const posiciones = encontrar(texto, consulta);
    if (posiciones.length === 0) continue;
    const largo = consulta.trim().length;
    const fragmento = document.createDocumentFragment();
    let cursor = 0;
    for (const inicio of posiciones) {
      fragmento.append(texto.slice(cursor, inicio));
      const marca = document.createElement('mark');
      marca.dataset.busqueda = '';
      marca.textContent = texto.slice(inicio, inicio + largo);
      fragmento.append(marca);
      cursor = inicio + largo;
    }
    fragmento.append(texto.slice(cursor));
    nodo.replaceWith(fragmento);
    total += posiciones.length;
  }
  return total;
}

export function iniciarBusqueda({ raiz, entrada, estado, indice }: Elementos) {
  const acordeones = () =>
    Array.from(raiz.querySelectorAll<HTMLDetailsElement>('details.acordeon'));
  let abiertosAntes: boolean[] | null = null;

  function restaurar() {
    quitarMarcas(raiz);
    acordeones().forEach((d, i) => {
      d.hidden = false;
      if (abiertosAntes) d.open = abiertosAntes[i] ?? d.open;
    });
    abiertosAntes = null;
    indice?.querySelectorAll<HTMLElement>('li').forEach((li) => {
      li.hidden = false;
    });
    estado.textContent = '';
  }

  function buscar() {
    const consulta = entrada.value;
    if (consulta.trim().length < MINIMO) {
      if (abiertosAntes || raiz.querySelector('mark[data-busqueda]')) {
        restaurar();
      }
      estado.textContent = consulta.trim()
        ? `Escribe al menos ${MINIMO} letras.`
        : '';
      return;
    }
    quitarMarcas(raiz);
    abiertosAntes ??= acordeones().map((d) => d.open);

    let coincidencias = 0;
    let conResultados = 0;
    for (const d of acordeones()) {
      const n = resaltar(d, consulta);
      d.hidden = n === 0;
      if (n > 0) {
        d.open = true;
        conResultados++;
        coincidencias += n;
      }
      const id = d.querySelector('h2')?.id;
      const li = id
        ? indice?.querySelector<HTMLElement>(`li[data-seccion="${id}"]`)
        : null;
      if (li) li.hidden = n === 0;
    }
    // Introducción: el texto que queda fuera de los acordeones.
    for (const hijo of Array.from(raiz.children)) {
      if (hijo.classList.contains('acordeones')) continue;
      coincidencias += resaltar(hijo, consulta);
    }

    estado.textContent =
      coincidencias === 0
        ? 'Sin resultados.'
        : `${coincidencias} ${coincidencias === 1 ? 'coincidencia' : 'coincidencias'}` +
          (conResultados
            ? ` en ${conResultados} ${conResultados === 1 ? 'sección' : 'secciones'}`
            : '');
  }

  entrada.addEventListener('input', buscar);
  entrada.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape' && entrada.value) {
      evento.preventDefault();
      entrada.value = '';
      buscar();
    } else if (evento.key === 'Enter') {
      evento.preventDefault();
      raiz
        .querySelector('mark[data-busqueda]')
        ?.scrollIntoView({ block: 'center' });
    }
  });
  // Los avisos de «limpiar» del campo type=search disparan `search`.
  entrada.addEventListener('search', buscar);
}
