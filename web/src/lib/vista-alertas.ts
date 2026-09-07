export const AVISO_HONESTIDAD_ALERTAS =
  'Herramienta académica en desarrollo (INSAMT, Equipo 4). Las alertas y sus indicaciones las redacta manualmente el equipo de vigilancia del proyecto a partir de datos públicos históricos (MINSAL, OpenDengue, Open-Meteo). No sustituyen los lineamientos oficiales del MINSAL ni el criterio clínico. No son tiempo real. La coexistencia temporal de eventos no demuestra causalidad.';

export const TIPOS_ALERTA = ['dengue', 'respiratorio'] as const;
export type TipoAlerta = (typeof TIPOS_ALERTA)[number];

export const ETIQUETAS_TIPO: Record<TipoAlerta, string> = {
  dengue: 'Dengue',
  respiratorio: 'Respiratorio',
};

export const ETIQUETAS_NIVEL: Record<string, string> = {
  informativo: 'Informativo',
  atencion: 'Atención',
  intensificacion: 'Intensificación',
};

export interface AlertaPublica {
  id: number;
  tipo: TipoAlerta;
  nivel: string;
  titulo: string;
  contexto: string;
  indicaciones: string;
  fuente: string;
  autor: string;
  vigente_desde: string;
  vigente_hasta: string | null;
  activa: boolean;
}

export interface PayloadAlertas {
  aviso: string;
  ultima_revision: string | null;
  alertas: AlertaPublica[];
}

export type VistaAlertas =
  | { tipo: 'vacio'; texto: string }
  | { tipo: 'lista'; alertas: AlertaPublica[] };

export function textoEstadoVacio(fechaDdMmAaaa: string): string {
  return `No hay alertas activas. Última revisión del equipo: ${fechaDdMmAaaa}.`;
}

export function formatearFechaIso(iso: string | null | undefined): string {
  if (!iso) return '';
  const parte = iso.slice(0, 10);
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(parte);
  if (!match) return iso;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function vistaDeAlertas(
  alertas: AlertaPublica[],
  ultimaRevisionIso: string | null,
): VistaAlertas {
  if (alertas.length === 0) {
    const fecha = formatearFechaIso(ultimaRevisionIso) || '—';
    return { tipo: 'vacio', texto: textoEstadoVacio(fecha) };
  }
  return { tipo: 'lista', alertas };
}

export function rutaModulo(tipo: TipoAlerta): string {
  return tipo === 'respiratorio' ? '/respiratorio' : '/dengue';
}

export function escapeHtml(texto: string): string {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function renderTextoAccionable(texto: string): string {
  const lineas = texto.replace(/\r\n/g, '\n').split('\n');
  const partes: string[] = [];
  let items: string[] = [];

  const vaciarLista = () => {
    if (items.length === 0) return;
    partes.push(
      `<ul class="list-disc space-y-1 pl-5">${items.map((item) => `<li>${item}</li>`).join('')}</ul>`,
    );
    items = [];
  };

  for (const cruda of lineas) {
    const item = /^\s*-\s+(.+)$/.exec(cruda);
    if (item) {
      items.push(escapeHtml(item[1]));
      continue;
    }
    vaciarLista();
    const recortada = cruda.trim();
    if (!recortada) continue;
    partes.push(`<p>${escapeHtml(recortada)}</p>`);
  }
  vaciarLista();
  return partes.join('');
}

export function textoVigencia(alerta: AlertaPublica): string {
  const desde = formatearFechaIso(alerta.vigente_desde);
  if (alerta.vigente_hasta) {
    return `Vigencia: ${desde} – ${formatearFechaIso(alerta.vigente_hasta)}`;
  }
  return `Vigencia: desde ${desde} (sin fecha de cierre)`;
}

function pintarTarjeta(alerta: AlertaPublica): HTMLElement {
  const articulo = document.createElement('article');
  articulo.className =
    'card-elevated rounded-2xl border border-border bg-surface p-5 sm:p-6';
  articulo.setAttribute('data-alerta', '');
  articulo.setAttribute('data-tipo', alerta.tipo);
  articulo.setAttribute('data-nivel', alerta.nivel);

  const tipo = ETIQUETAS_TIPO[alerta.tipo] ?? alerta.tipo;
  const nivel = ETIQUETAS_NIVEL[alerta.nivel] ?? alerta.nivel;
  const modulo = rutaModulo(alerta.tipo);

  const encabezado = document.createElement('header');
  encabezado.innerHTML = `
    <p class="font-sans text-xs font-semibold uppercase tracking-wider text-accent">
      <span data-alerta-tipo>${escapeHtml(tipo)}</span>
      ·
      <span data-alerta-nivel>${escapeHtml(nivel)}</span>
    </p>
    <h2 class="mt-1 font-display text-xl font-semibold text-ink" data-alerta-titulo></h2>
    <p class="mt-2 font-sans text-sm text-ink-muted">
      Emisión: <time data-alerta-emision datetime="${escapeHtml(alerta.vigente_desde)}">${escapeHtml(formatearFechaIso(alerta.vigente_desde))}</time>
      ·
      <span data-alerta-vigencia>${escapeHtml(textoVigencia(alerta))}</span>
    </p>
  `;
  const titulo = encabezado.querySelector('[data-alerta-titulo]');
  if (titulo) titulo.textContent = alerta.titulo;
  articulo.appendChild(encabezado);

  const contexto = document.createElement('section');
  contexto.className = 'mt-4 font-sans text-sm leading-relaxed text-ink';
  contexto.setAttribute('data-alerta-contexto', '');
  contexto.innerHTML = renderTextoAccionable(alerta.contexto);
  articulo.appendChild(contexto);

  const indicaciones = document.createElement('section');
  indicaciones.className = 'mt-4 font-sans text-sm leading-relaxed text-ink';
  indicaciones.setAttribute('data-alerta-indicaciones', '');
  const hInd = document.createElement('h3');
  hInd.className = 'font-sans text-sm font-semibold text-ink';
  hInd.textContent = 'Indicaciones para la unidad';
  indicaciones.appendChild(hInd);
  const cuerpoInd = document.createElement('div');
  cuerpoInd.className = 'mt-2 space-y-2';
  cuerpoInd.innerHTML = renderTextoAccionable(alerta.indicaciones);
  indicaciones.appendChild(cuerpoInd);
  articulo.appendChild(indicaciones);

  const meta = document.createElement('p');
  meta.className = 'mt-4 font-sans text-xs leading-relaxed text-ink-muted';
  meta.innerHTML = `Fuente: <span data-alerta-fuente></span><br>Autor: <span data-alerta-autor></span>`;
  const fuenteNodo = meta.querySelector('[data-alerta-fuente]');
  const autorNodo = meta.querySelector('[data-alerta-autor]');
  if (fuenteNodo) fuenteNodo.textContent = alerta.fuente;
  if (autorNodo) autorNodo.textContent = alerta.autor;
  articulo.appendChild(meta);

  const enlace = document.createElement('a');
  enlace.href = modulo;
  enlace.setAttribute('data-enlace-modulo', alerta.tipo);
  enlace.className =
    'mt-4 inline-flex font-sans text-sm font-medium text-accent underline underline-offset-2';
  enlace.textContent = `Ver datos que motivaron esta alerta (${tipo.toLowerCase()})`;
  articulo.appendChild(enlace);

  return articulo;
}

export function aplicarVistaAlertas(
  root: HTMLElement,
  payload: PayloadAlertas,
): void {
  const carga = root.querySelector<HTMLElement>('[data-alertas-carga]');
  const error = root.querySelector<HTMLElement>('[data-alertas-error]');
  const vacio = root.querySelector<HTMLElement>('[data-alertas-vacio]');
  const lista = root.querySelector<HTMLElement>('[data-alertas-lista]');
  if (carga) carga.hidden = true;
  if (error) error.hidden = true;

  const vista = vistaDeAlertas(payload.alertas, payload.ultima_revision);
  if (vista.tipo === 'vacio') {
    if (vacio) {
      vacio.hidden = false;
      vacio.textContent = vista.texto;
    }
    if (lista) {
      lista.hidden = true;
      lista.replaceChildren();
    }
    root.setAttribute('data-cargado', '1');
    root.setAttribute('data-estado', 'vacio');
    return;
  }

  if (vacio) {
    vacio.hidden = true;
    vacio.textContent = '';
  }
  if (lista) {
    lista.hidden = false;
    lista.replaceChildren(...vista.alertas.map(pintarTarjeta));
  }
  root.setAttribute('data-cargado', '1');
  root.setAttribute('data-estado', 'lista');
}

export type PintarAlertas = (payload: PayloadAlertas) => void;
