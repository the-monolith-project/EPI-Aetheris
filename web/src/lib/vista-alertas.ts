export const AVISO_HONESTIDAD_ALERTAS =
  'Herramienta académica en desarrollo (INSAMT, Equipo 4). Las alertas y sus indicaciones las redacta manualmente el equipo de vigilancia del proyecto a partir de datos públicos históricos (MINSAL, OpenDengue, Open-Meteo). No sustituyen los lineamientos oficiales del MINSAL ni el criterio clínico. No son tiempo real. La coexistencia temporal de eventos no demuestra causalidad.';

export const TIPOS_ALERTA = ['dengue', 'respiratorio'] as const;
export type TipoAlerta = (typeof TIPOS_ALERTA)[number];

export const ETIQUETAS_TIPO: Record<TipoAlerta, string> = {
  dengue: 'Dengue',
  respiratorio: 'Respiratorio',
};

export const NIVELES_ALERTA = [
  'informativo',
  'atencion',
  'intensificacion',
] as const;
export type NivelAlerta = (typeof NIVELES_ALERTA)[number];

export const ETIQUETAS_NIVEL: Record<NivelAlerta, string> = {
  informativo: 'Informativo',
  atencion: 'Atención',
  intensificacion: 'Intensificación',
};

/** Significado operativo de cada nivel (INDICACIONES_ALERTAS.md §4). */
export const SIGNIFICADO_NIVEL: Record<NivelAlerta, string> = {
  informativo:
    'Sin señal relevante en los datos. Recordatorio de vigilancia rutinaria.',
  atencion:
    'Los datos históricos recientes están por encima de lo esperado para la época. Reforzar notificación y búsqueda de casos.',
  intensificacion:
    'Señal sostenida varias semanas y/o concentración territorial. Activar medidas locales y coordinar con SIBASI.',
};

export function esNivelAlerta(valor: string): valor is NivelAlerta {
  return (NIVELES_ALERTA as readonly string[]).includes(valor);
}

export function textoSignificadoNivel(nivel: string): string {
  return esNivelAlerta(nivel) ? SIGNIFICADO_NIVEL[nivel] : '';
}

export const ROTULO_ALERTA_PRUEBA =
  'ALERTA DE PRUEBA — NO ACTUAR SOBRE ESTA INFORMACIÓN';

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
  etiqueta?: string | null;
  // Campos clínicos opcionales (ADR 0014). El equipo los redacta a mano con
  // fuente MINSAL/OPS; null = el bloque no se muestra.
  signos_alarma?: string | null;
  criterios_referencia?: string | null;
  que_notificar?: string | null;
  definicion_caso?: string | null;
  contacto_vigilancia?: string | null;
}

// Campos clínicos opcionales, en el orden en que se muestran en la tarjeta.
export const CAMPOS_CLINICOS: ReadonlyArray<{
  clave: keyof AlertaPublica;
  etiqueta: string;
}> = [
  { clave: 'definicion_caso', etiqueta: 'Definición de caso' },
  { clave: 'signos_alarma', etiqueta: 'Signos de alarma' },
  { clave: 'criterios_referencia', etiqueta: 'Criterios de referencia' },
  { clave: 'que_notificar', etiqueta: 'Qué notificar' },
  { clave: 'contacto_vigilancia', etiqueta: 'A quién contactar (SIBASI)' },
];

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
  textoVacio?: string,
): VistaAlertas {
  if (alertas.length === 0) {
    if (textoVacio) return { tipo: 'vacio', texto: textoVacio };
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

export function alertaEstaVigente(
  alerta: AlertaPublica,
  hoyIso?: string,
): boolean {
  if (!alerta.activa) return false;
  if (!alerta.vigente_hasta) return true;
  const hoy = hoyIso ?? new Date().toISOString().slice(0, 10);
  return alerta.vigente_hasta.slice(0, 10) >= hoy;
}

export function textoNoVigente(
  alerta: AlertaPublica,
  hoyIso?: string,
): string | null {
  if (alertaEstaVigente(alerta, hoyIso)) return null;
  const fin = alerta.vigente_hasta || alerta.vigente_desde;
  return `NO VIGENTE — venció el ${formatearFechaIso(fin)}`;
}

export function esAlertaEtiquetada(alerta: AlertaPublica): boolean {
  return typeof alerta.etiqueta === 'string' && alerta.etiqueta.trim() !== '';
}

function pintarTarjeta(alerta: AlertaPublica, esNueva = false): HTMLElement {
  const articulo = document.createElement('article');
  articulo.className =
    'card-elevated rounded-2xl border border-border bg-surface p-5 sm:p-6';
  articulo.setAttribute('data-alerta', '');
  articulo.setAttribute('data-tipo', alerta.tipo);
  articulo.setAttribute('data-nivel', alerta.nivel);
  articulo.id = `alerta-${alerta.id}`;
  if (esAlertaEtiquetada(alerta)) {
    articulo.setAttribute('data-alerta-etiqueta', String(alerta.etiqueta));
  }
  if (!alertaEstaVigente(alerta)) {
    articulo.setAttribute('data-alerta-no-vigente-tarjeta', '');
  }

  if (esAlertaEtiquetada(alerta)) {
    const avisoPrueba = document.createElement('p');
    avisoPrueba.setAttribute('data-alerta-prueba', '');
    avisoPrueba.className =
      'mb-4 rounded-xl border-2 border-secondary bg-secondary px-3 py-2 font-sans text-sm font-bold uppercase tracking-wide text-secondary-ink';
    avisoPrueba.textContent = ROTULO_ALERTA_PRUEBA;
    articulo.appendChild(avisoPrueba);
  }

  const avisoNoVigente = textoNoVigente(alerta);
  if (avisoNoVigente) {
    const avisoVencida = document.createElement('p');
    avisoVencida.setAttribute('data-alerta-no-vigente', '');
    avisoVencida.className =
      'mb-4 rounded-xl border-2 border-ink px-3 py-2 font-sans text-sm font-bold uppercase tracking-wide text-ink';
    avisoVencida.textContent = avisoNoVigente;
    articulo.appendChild(avisoVencida);
  }

  const tipo = ETIQUETAS_TIPO[alerta.tipo] ?? alerta.tipo;
  const nivel = esNivelAlerta(alerta.nivel)
    ? ETIQUETAS_NIVEL[alerta.nivel]
    : alerta.nivel;
  const significadoNivel = textoSignificadoNivel(alerta.nivel);
  const modulo = rutaModulo(alerta.tipo);

  const encabezado = document.createElement('header');
  encabezado.innerHTML = `
    <p class="font-sans text-xs font-semibold uppercase tracking-wider text-accent">
      <span data-alerta-tipo>${escapeHtml(tipo)}</span>
      ·
      <span data-alerta-nivel>${escapeHtml(nivel)}</span>
      ${
        esNueva
          ? '<span data-alerta-nueva class="ml-2 rounded-full bg-accent px-2 py-0.5 text-[10px] font-semibold text-accent-ink">Nueva</span>'
          : ''
      }
    </p>
    ${
      significadoNivel
        ? `<p class="mt-1 font-sans text-sm text-ink-muted" data-alerta-nivel-significado>${escapeHtml(significadoNivel)}</p>`
        : ''
    }
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

  // Campos clínicos opcionales (ADR 0014): cada uno solo aparece si el equipo
  // ya lo llenó. Plegados por defecto para no alargar la tarjeta en consulta.
  for (const { clave, etiqueta } of CAMPOS_CLINICOS) {
    const valor = alerta[clave];
    if (typeof valor !== 'string' || valor.trim() === '') continue;
    const bloque = document.createElement('details');
    bloque.className =
      'mt-3 rounded-xl border border-border bg-bg px-4 py-2 font-sans text-sm text-ink';
    bloque.setAttribute('data-alerta-clinico', String(clave));
    const resumen = document.createElement('summary');
    resumen.className = 'cursor-pointer py-1 font-semibold';
    resumen.textContent = etiqueta;
    bloque.appendChild(resumen);
    const cuerpo = document.createElement('div');
    cuerpo.className = 'mb-2 mt-2 space-y-2 leading-relaxed';
    cuerpo.innerHTML = renderTextoAccionable(valor);
    bloque.appendChild(cuerpo);
    articulo.appendChild(bloque);
  }

  const meta = document.createElement('p');
  meta.className = 'mt-4 font-sans text-xs leading-relaxed text-ink-muted';
  meta.innerHTML = `Fuente: <span data-alerta-fuente></span><br>Autor: <span data-alerta-autor></span>`;
  const fuenteNodo = meta.querySelector('[data-alerta-fuente]');
  const autorNodo = meta.querySelector('[data-alerta-autor]');
  if (fuenteNodo) fuenteNodo.textContent = alerta.fuente;
  if (autorNodo) autorNodo.textContent = alerta.autor;
  articulo.appendChild(meta);

  const acciones = document.createElement('div');
  acciones.className = 'mt-4 flex flex-wrap items-center gap-x-4 gap-y-2';
  acciones.setAttribute('data-alerta-acciones', '');

  const enlace = document.createElement('a');
  enlace.href = modulo;
  enlace.setAttribute('data-enlace-modulo', alerta.tipo);
  enlace.className =
    'inline-flex font-sans text-sm font-medium text-accent underline underline-offset-2';
  enlace.textContent = `Ver datos que motivaron esta alerta (${tipo.toLowerCase()})`;
  acciones.appendChild(enlace);

  // Compartir: navigator.share donde exista (móvil), copiar enlace si no.
  // El enlace apunta al ancla de esta alerta dentro de /alertas.
  const compartir = document.createElement('button');
  compartir.type = 'button';
  compartir.setAttribute('data-alerta-compartir', String(alerta.id));
  compartir.className =
    'inline-flex font-sans text-sm font-medium text-accent underline underline-offset-2 print:hidden';
  compartir.textContent = 'Compartir';
  compartir.addEventListener('click', () => {
    void compartirAlerta(alerta, compartir);
  });
  acciones.appendChild(compartir);

  articulo.appendChild(acciones);

  return articulo;
}

export function enlaceDeAlerta(alerta: AlertaPublica): string {
  if (typeof window === 'undefined') return `/alertas#alerta-${alerta.id}`;
  return `${window.location.origin}/alertas?tipo=${encodeURIComponent(alerta.tipo)}#alerta-${alerta.id}`;
}

async function compartirAlerta(
  alerta: AlertaPublica,
  boton: HTMLButtonElement,
): Promise<void> {
  const url = enlaceDeAlerta(alerta);
  const nav = navigator as Navigator & {
    share?: (datos: {
      title: string;
      text: string;
      url: string;
    }) => Promise<void>;
  };
  if (typeof nav.share === 'function') {
    try {
      await nav.share({ title: alerta.titulo, text: alerta.titulo, url });
      return;
    } catch {
      // Cancelado por la persona o no permitido: se cae al copiado.
    }
  }
  const etiquetaOriginal = boton.textContent ?? 'Compartir';
  try {
    await navigator.clipboard.writeText(url);
    boton.textContent = 'Enlace copiado';
  } catch {
    boton.textContent = 'No se pudo copiar';
  }
  window.setTimeout(() => {
    boton.textContent = etiquetaOriginal;
  }, 2500);
}

const CLAVE_VISTAS = 'epi-aetheris:alertas-vistas';

/** Ids de alertas que esta persona ya vio en este navegador. */
export function leerAlertasVistas(): Set<number> {
  try {
    const crudo = window.localStorage.getItem(CLAVE_VISTAS);
    if (!crudo) return new Set();
    const datos: unknown = JSON.parse(crudo);
    if (!Array.isArray(datos)) return new Set();
    return new Set(datos.filter((v): v is number => typeof v === 'number'));
  } catch {
    // Modo privado, almacenamiento bloqueado o JSON corrupto: sin historial,
    // todo se considera visto para no marcar todo como "Nueva" en falso.
    return new Set();
  }
}

export function guardarAlertasVistas(ids: Iterable<number>): void {
  try {
    window.localStorage.setItem(
      CLAVE_VISTAS,
      JSON.stringify([...new Set(ids)]),
    );
  } catch {
    // Sin almacenamiento la vista sigue funcionando; solo se pierde el "Nueva".
  }
}

/**
 * Marca como nuevas solo si ya había historial guardado. La primera visita
 * no marca nada: sin referencia previa, "nueva" no significa nada.
 */
export function calcularNuevas(
  alertas: AlertaPublica[],
  vistas: Set<number>,
): Set<number> {
  if (vistas.size === 0) return new Set();
  return new Set(alertas.filter((a) => !vistas.has(a.id)).map((a) => a.id));
}

export function aplicarVistaAlertas(
  root: HTMLElement,
  payload: PayloadAlertas,
  nuevas: Set<number> = new Set(),
  textoVacio?: string,
): void {
  const carga = root.querySelector<HTMLElement>('[data-alertas-carga]');
  const error = root.querySelector<HTMLElement>('[data-alertas-error]');
  const vacio = root.querySelector<HTMLElement>('[data-alertas-vacio]');
  const lista = root.querySelector<HTMLElement>('[data-alertas-lista]');
  if (carga) carga.hidden = true;
  if (error) error.hidden = true;

  const vista = vistaDeAlertas(
    payload.alertas,
    payload.ultima_revision,
    textoVacio,
  );
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
    lista.replaceChildren(
      ...vista.alertas.map((a) => pintarTarjeta(a, nuevas.has(a.id))),
    );
  }
  root.setAttribute('data-cargado', '1');
  root.setAttribute('data-estado', 'lista');
}

export type PintarAlertas = (payload: PayloadAlertas) => void;
