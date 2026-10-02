/**
 * Atajos de teclado del sitio: catálogo de acciones, combinaciones por
 * defecto y la lógica pura (sin DOM) para leerlas, validarlas y casarlas con
 * una pulsación. El listener que las ejecuta vive en
 * `components/AtajosTeclado.astro`; la edición, en `/configuracion`.
 *
 * Una combinación se representa como texto normalizado, con los
 * modificadores en orden fijo y la tecla al final: `Alt+I`, `Alt+Shift+B`,
 * `F2`. La tecla es una letra A–Z, un dígito 0–9 o F1–F12. Las letras y los
 * dígitos se resuelven por `KeyboardEvent.code` (posición física), no por
 * `key`: con Alt en macOS `key` trae el carácter alternativo (`∫` para
 * Alt+B) y el atajo no casaría nunca.
 *
 * Persistencia: `localStorage['epi:atajos']` guarda un JSON con solo lo que
 * difiere de los valores por defecto, `{ activos?: false, combos?: {...} }`.
 * En `combos`, `null` deja la acción sin atajo. Cualquier entrada inválida se
 * ignora y vuelve al valor por defecto.
 */

export const CLAVE_ATAJOS = 'epi:atajos';

export type AccionAtajo =
  | 'inicio'
  | 'alertas'
  | 'analisis'
  | 'dengue'
  | 'prediccion'
  | 'respiratorio'
  | 'biblioteca'
  | 'sugerencias'
  | 'configuracion'
  | 'tema'
  | 'animaciones'
  | 'ayuda';

export type GrupoAtajo = 'navegar' | 'preferencias' | 'ayuda';

export interface DefinicionAtajo {
  accion: AccionAtajo;
  /** Texto visible en la ayuda y en la configuración. */
  etiqueta: string;
  grupo: GrupoAtajo;
  /** Destino de las acciones de navegación. */
  href?: string;
  /** Combinación por defecto, ya normalizada. */
  porDefecto: string;
}

/** Catálogo en el orden en que se muestra. */
export const ATAJOS: readonly DefinicionAtajo[] = [
  {
    accion: 'inicio',
    etiqueta: 'Ir al inicio',
    grupo: 'navegar',
    href: '/',
    porDefecto: 'Alt+I',
  },
  {
    accion: 'alertas',
    etiqueta: 'Ir a Alertas',
    grupo: 'navegar',
    href: '/alertas',
    porDefecto: 'Alt+A',
  },
  {
    accion: 'analisis',
    etiqueta: 'Ir a Análisis',
    grupo: 'navegar',
    href: '/analisis',
    porDefecto: 'Alt+N',
  },
  {
    accion: 'dengue',
    etiqueta: 'Ir a Dengue',
    grupo: 'navegar',
    href: '/dengue',
    porDefecto: 'Alt+G',
  },
  {
    accion: 'prediccion',
    etiqueta: 'Ir a Predicción de dengue',
    grupo: 'navegar',
    href: '/prediccion',
    porDefecto: 'Alt+P',
  },
  {
    accion: 'respiratorio',
    etiqueta: 'Ir a Respiratorio',
    grupo: 'navegar',
    href: '/respiratorio',
    porDefecto: 'Alt+R',
  },
  {
    accion: 'biblioteca',
    etiqueta: 'Abrir la Biblioteca',
    grupo: 'navegar',
    href: '/biblioteca',
    porDefecto: 'Alt+B',
  },
  {
    accion: 'sugerencias',
    etiqueta: 'Ir a Sugerencias',
    grupo: 'navegar',
    href: '/sugerencias',
    porDefecto: 'Alt+S',
  },
  {
    accion: 'configuracion',
    etiqueta: 'Abrir la configuración',
    grupo: 'navegar',
    href: '/configuracion',
    porDefecto: 'Alt+C',
  },
  {
    accion: 'tema',
    etiqueta: 'Alternar tema claro u oscuro',
    grupo: 'preferencias',
    porDefecto: 'Alt+T',
  },
  {
    accion: 'animaciones',
    etiqueta: 'Activar o desactivar animaciones',
    grupo: 'preferencias',
    porDefecto: 'Alt+M',
  },
  {
    accion: 'ayuda',
    etiqueta: 'Mostrar esta lista de atajos',
    grupo: 'ayuda',
    porDefecto: 'Alt+H',
  },
];

export const ATAJOS_POR_ACCION: Record<AccionAtajo, DefinicionAtajo> =
  Object.fromEntries(ATAJOS.map((a) => [a.accion, a])) as Record<
    AccionAtajo,
    DefinicionAtajo
  >;

export interface Combo {
  ctrl: boolean;
  alt: boolean;
  shift: boolean;
  meta: boolean;
  /** `A`–`Z`, `0`–`9` o `F1`–`F12`. */
  tecla: string;
}

/** Subconjunto de KeyboardEvent que necesita la lógica; facilita las pruebas. */
export interface PulsacionLike {
  code: string;
  key: string;
  ctrlKey: boolean;
  altKey: boolean;
  shiftKey: boolean;
  metaKey: boolean;
}

const RE_TECLA = /^(?:[A-Z]|[0-9]|F(?:[1-9]|1[0-2]))$/;

/** Tecla normalizada a partir de la pulsación, o null si no es admisible. */
export function teclaDePulsacion(p: PulsacionLike): string | null {
  const letra = /^Key([A-Z])$/.exec(p.code);
  if (letra) return letra[1];
  const digito = /^Digit([0-9])$/.exec(p.code);
  if (digito) return digito[1];
  if (/^F(?:[1-9]|1[0-2])$/.test(p.code)) return p.code;
  // Teclados sin `code` fiable (algunos virtuales): último recurso por `key`.
  const k = p.key.length === 1 ? p.key.toUpperCase() : p.key;
  return RE_TECLA.test(k) ? k : null;
}

/** Combo de una pulsación; null si la tecla no es admisible (solo modificadores, Esc, etc.). */
export function comboDePulsacion(p: PulsacionLike): Combo | null {
  const tecla = teclaDePulsacion(p);
  if (!tecla) return null;
  return {
    ctrl: p.ctrlKey,
    alt: p.altKey,
    shift: p.shiftKey,
    meta: p.metaKey,
    tecla,
  };
}

/** Texto normalizado del combo (`Ctrl+Alt+Shift+Meta+Tecla`). */
export function formatearCombo(c: Combo): string {
  const partes: string[] = [];
  if (c.ctrl) partes.push('Ctrl');
  if (c.alt) partes.push('Alt');
  if (c.shift) partes.push('Shift');
  if (c.meta) partes.push('Meta');
  partes.push(c.tecla);
  return partes.join('+');
}

/** Interpreta un texto de combo; null si no está bien formado. */
export function parsearCombo(texto: string): Combo | null {
  if (typeof texto !== 'string' || texto.length === 0) return null;
  const partes = texto.split('+');
  const tecla = partes.pop() ?? '';
  if (!RE_TECLA.test(tecla)) return null;
  const c: Combo = {
    ctrl: false,
    alt: false,
    shift: false,
    meta: false,
    tecla,
  };
  for (const parte of partes) {
    if (parte === 'Ctrl' && !c.ctrl) c.ctrl = true;
    else if (parte === 'Alt' && !c.alt) c.alt = true;
    else if (parte === 'Shift' && !c.shift) c.shift = true;
    else if (parte === 'Meta' && !c.meta) c.meta = true;
    else return null;
  }
  // Solo se acepta la forma canónica, para que la comparación sea textual.
  return formatearCombo(c) === texto ? c : null;
}

/**
 * Nombre legible para mostrar: la tecla Meta se llama Cmd en macOS y Win en
 * el resto; los demás nombres se dejan como están.
 */
export function etiquetaCombo(texto: string, mac: boolean): string {
  return texto.replace('Meta', mac ? 'Cmd' : 'Win');
}

/** Si la plataforma es de Apple (la tecla Meta se llama Cmd). `platform` está
 *  obsoleto; `userAgent` sigue trayendo el nombre del sistema. */
export function esPlataformaMac(nav: { userAgent?: string }): boolean {
  return /Mac|iPhone|iPad|iPod/.test(nav.userAgent ?? '');
}

/**
 * Combinaciones que el navegador se queda para sí o que la gente usa a diario
 * (pestañas, copiar y pegar, buscar, barra de direcciones, recargar, ayuda...).
 * Guardarlas daría un atajo que no funciona o que rompe algo que sí. Las
 * teclas con Ctrl y con Cmd comparten lista; Alt+D es la barra de direcciones
 * en Chrome y Firefox, y Alt+1 a Alt+9 cambian de pestaña en Linux.
 */
const LETRAS_DEL_NAVEGADOR = 'ACVXZYFLRPSDKGHJOUE';
const COMBOS_BASE = [
  'Ctrl+T',
  'Ctrl+N',
  'Ctrl+W',
  'Ctrl+Q',
  'Ctrl+Shift+T',
  'Ctrl+Shift+N',
  'Ctrl+Shift+W',
  'Ctrl+Shift+Q',
  'Alt+F4',
  'Alt+D',
  'Meta+T',
  'Meta+N',
  'Meta+W',
  'Meta+Q',
  'Meta+M',
  'Meta+H',
  'Meta+Shift+T',
  'Meta+Shift+N',
  'Meta+Shift+W',
  'F1',
  'F3',
  'F5',
  'F6',
  'F7',
  'F10',
  'F11',
  'F12',
];
export const COMBOS_RESERVADOS: ReadonlySet<string> = new Set([
  ...COMBOS_BASE,
  ...[...LETRAS_DEL_NAVEGADOR].flatMap((l) => [`Ctrl+${l}`, `Meta+${l}`]),
  ...'0123456789'.split('').flatMap((d) => [`Ctrl+${d}`, `Meta+${d}`]),
  ...'123456789'.split('').map((d) => `Alt+${d}`),
]);

export type ErrorCombo = 'sin-modificador' | 'reservado' | 'mal-formado';

/**
 * Comprueba que un combo sirva como atajo: necesita Ctrl, Alt o Meta (Shift
 * solo no basta: sería escribir una mayúscula) salvo que la tecla sea de
 * función, y no debe ser uno que el navegador reserva.
 */
export function validarCombo(texto: string): ErrorCombo | null {
  const c = parsearCombo(texto);
  if (!c) return 'mal-formado';
  if (COMBOS_RESERVADOS.has(texto)) return 'reservado';
  const esFuncion = c.tecla.startsWith('F');
  if (!esFuncion && !c.ctrl && !c.alt && !c.meta) return 'sin-modificador';
  return null;
}

export type Combos = Record<AccionAtajo, string | null>;

export interface ConfiguracionAtajos {
  /** Interruptor general: en false no se ejecuta ningún atajo. */
  activos: boolean;
  combos: Combos;
}

export function combosPorDefecto(): Combos {
  return Object.fromEntries(
    ATAJOS.map((a) => [a.accion, a.porDefecto]),
  ) as Combos;
}

/**
 * Resuelve la configuración a partir del JSON guardado (o null). Las
 * entradas desconocidas o inválidas se descartan; lo que falta toma el valor
 * por defecto.
 */
export function resolverAtajos(crudo: string | null): ConfiguracionAtajos {
  const combos = combosPorDefecto();
  let activos = true;
  if (!crudo) return { activos, combos };
  let datos: unknown;
  try {
    datos = JSON.parse(crudo);
  } catch {
    return { activos, combos };
  }
  if (!datos || typeof datos !== 'object') return { activos, combos };
  const d = datos as { activos?: unknown; combos?: unknown };
  if (d.activos === false) activos = false;
  if (d.combos && typeof d.combos === 'object') {
    for (const [accion, valor] of Object.entries(
      d.combos as Record<string, unknown>,
    )) {
      if (!(accion in combos)) continue;
      if (valor === null) combos[accion as AccionAtajo] = null;
      else if (typeof valor === 'string' && validarCombo(valor) === null)
        combos[accion as AccionAtajo] = valor;
    }
  }
  return { activos, combos };
}

/**
 * JSON a guardar: solo lo que difiere de los valores por defecto. Devuelve
 * null cuando no hay nada que guardar (se borra la clave).
 */
export function serializarAtajos(config: ConfiguracionAtajos): string | null {
  const porDefecto = combosPorDefecto();
  const combos: Record<string, string | null> = {};
  for (const accion of Object.keys(porDefecto) as AccionAtajo[]) {
    if (config.combos[accion] !== porDefecto[accion])
      combos[accion] = config.combos[accion];
  }
  const salida: { activos?: false; combos?: Record<string, string | null> } =
    {};
  if (!config.activos) salida.activos = false;
  if (Object.keys(combos).length > 0) salida.combos = combos;
  return Object.keys(salida).length === 0 ? null : JSON.stringify(salida);
}

/** Acción que ya usa ese combo, distinta de `salvo`; null si está libre. */
export function accionConCombo(
  combos: Combos,
  texto: string,
  salvo?: AccionAtajo,
): AccionAtajo | null {
  for (const [accion, valor] of Object.entries(combos) as [
    AccionAtajo,
    string | null,
  ][]) {
    if (accion !== salvo && valor === texto) return accion;
  }
  return null;
}

/**
 * Acción que corresponde a una pulsación, o null. No ejecuta nada: el que
 * llama decide qué hacer y si prevenir el comportamiento del navegador.
 */
export function accionParaPulsacion(
  config: ConfiguracionAtajos,
  p: PulsacionLike,
): AccionAtajo | null {
  if (!config.activos) return null;
  const combo = comboDePulsacion(p);
  if (!combo) return null;
  const texto = formatearCombo(combo);
  return accionConCombo(config.combos, texto);
}

/**
 * Un campo de texto se queda con el teclado: ahí no se disparan atajos,
 * también con modificador (Ctrl+E es "fin de línea" en los campos de macOS).
 */
export function esObjetivoEditable(
  objetivo: {
    tagName?: string;
    isContentEditable?: boolean;
    getAttribute?: (n: string) => string | null;
  } | null,
): boolean {
  if (!objetivo) return false;
  if (objetivo.isContentEditable) return true;
  const tag = objetivo.tagName?.toUpperCase();
  if (tag === 'TEXTAREA' || tag === 'SELECT') return true;
  if (tag === 'INPUT') {
    const tipo = (objetivo.getAttribute?.('type') ?? 'text').toLowerCase();
    return ![
      'button',
      'checkbox',
      'radio',
      'submit',
      'reset',
      'range',
    ].includes(tipo);
  }
  return false;
}
