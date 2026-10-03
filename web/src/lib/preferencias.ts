/**
 * Preferencias de la persona, guardadas en este navegador (localStorage) y
 * aplicadas como atributos de <html>. Es el único sitio que escribe estas
 * claves; el selector de tema de la cabecera, el interruptor del pie, los
 * atajos de teclado y la página /configuracion pasan por aquí, y cada cambio
 * emite `EVENTO_PREFERENCIAS` en window para que los controles repintados en
 * distintas partes de la página se mantengan de acuerdo.
 *
 * Claves y valores (los dos primeros ya existían; se conservan tal cual):
 *   epi:tema        'light' | 'dark' | 'sistema'   (ausente = claro)
 *   epi:animaciones 'on' | 'off'       (ausente = sigue al sistema)
 *   epi:texto       'grande'           (ausente = tamaño normal)
 *   epi:atajos      JSON, ver lib/atajos.ts
 *   epi:toolbar-fija '1'               (ToolbarAnalisis.astro; ausente = se contrae sola)
 *
 * Los scripts en línea de Layout.astro repiten la resolución de tema,
 * animaciones y texto para fijar el atributo antes del primer pintado (no
 * pueden importar módulos); si cambia aquí, cambia allí.
 */

import { CLAVE_ANIMACIONES, type EstadoAnimaciones } from './animaciones.ts';
import {
  CLAVE_ATAJOS,
  resolverAtajos,
  serializarAtajos,
  type ConfiguracionAtajos,
} from './atajos.ts';

export const CLAVE_TEMA = 'epi:tema';
export const CLAVE_TEXTO = 'epi:texto';
export const EVENTO_PREFERENCIAS = 'epi:preferencias';

/** Todas las claves propias, para "borrar preferencias". */
export const CLAVES_PREFERENCIAS = [
  CLAVE_TEMA,
  CLAVE_ANIMACIONES,
  CLAVE_TEXTO,
  CLAVE_ATAJOS,
  'epi:departamento',
  'epi:toolbar-fija',
] as const;

export type Tema = 'sistema' | 'light' | 'dark';
export type PreferenciaAnimaciones = 'sistema' | EstadoAnimaciones;
export type Texto = 'normal' | 'grande';

/** Preferencia de tema a partir de lo guardado. */
export function resolverTema(guardado: string | null): Tema {
  return guardado === 'dark' || guardado === 'sistema' ? guardado : 'light';
}

/** Preferencia de animaciones a partir de lo guardado. */
export function resolverPreferenciaAnimaciones(
  guardado: string | null,
): PreferenciaAnimaciones {
  return guardado === 'on' || guardado === 'off' ? guardado : 'sistema';
}

/** Tamaño de texto a partir de lo guardado. */
export function resolverTexto(guardado: string | null): Texto {
  return guardado === 'grande' ? 'grande' : 'normal';
}

function leer(clave: string): string | null {
  try {
    return window.localStorage.getItem(clave);
  } catch {
    return null;
  }
}

/** Guarda (o borra con null). Devuelve false si el navegador no deja. */
function escribir(clave: string, valor: string | null): boolean {
  try {
    if (valor === null) window.localStorage.removeItem(clave);
    else window.localStorage.setItem(clave, valor);
    return true;
  } catch {
    return false;
  }
}

function avisar(): void {
  window.dispatchEvent(new CustomEvent(EVENTO_PREFERENCIAS));
}

// ---- Tema -----------------------------------------------------------------

export function leerTema(): Tema {
  return resolverTema(leer(CLAVE_TEMA));
}

/** Tema que se ve ahora mismo, resuelto el "sistema". */
export function temaEfectivo(): 'dark' | 'light' {
  const fijo = document.documentElement.getAttribute('data-theme');
  if (fijo === 'dark') return 'dark';
  if (fijo === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }
  return 'light';
}

export function aplicarTema(tema: Tema): boolean {
  if (tema === 'light') {
    document.documentElement.removeAttribute('data-theme');
  } else {
    document.documentElement.setAttribute(
      'data-theme',
      tema === 'sistema' ? 'system' : tema,
    );
  }
  const guardado = escribir(CLAVE_TEMA, tema === 'light' ? null : tema);
  avisar();
  return guardado;
}

export function alternarTema(): boolean {
  return aplicarTema(temaEfectivo() === 'dark' ? 'light' : 'dark');
}

// ---- Animaciones ----------------------------------------------------------

export function leerPreferenciaAnimaciones(): PreferenciaAnimaciones {
  return resolverPreferenciaAnimaciones(leer(CLAVE_ANIMACIONES));
}

function animacionesDelSistema(): EstadoAnimaciones {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ? 'off'
    : 'on';
}

export function aplicarAnimaciones(valor: PreferenciaAnimaciones): boolean {
  const estado = valor === 'sistema' ? animacionesDelSistema() : valor;
  document.documentElement.dataset.animaciones = estado;
  if (estado === 'off') {
    // Los bloques que esperaban entrar con scroll quedan visibles ya.
    delete document.documentElement.dataset.animar;
  }
  const guardado = escribir(
    CLAVE_ANIMACIONES,
    valor === 'sistema' ? null : valor,
  );
  avisar();
  return guardado;
}

export function alternarAnimaciones(): boolean {
  const ahora = document.documentElement.dataset.animaciones === 'on';
  return aplicarAnimaciones(ahora ? 'off' : 'on');
}

// ---- Tamaño de texto ------------------------------------------------------

export function leerTexto(): Texto {
  return resolverTexto(leer(CLAVE_TEXTO));
}

export function aplicarTexto(valor: Texto): boolean {
  if (valor === 'grande') {
    document.documentElement.dataset.texto = 'grande';
  } else {
    delete document.documentElement.dataset.texto;
  }
  const guardado = escribir(CLAVE_TEXTO, valor === 'grande' ? 'grande' : null);
  avisar();
  return guardado;
}

// ---- Atajos de teclado ----------------------------------------------------

export function leerAtajos(): ConfiguracionAtajos {
  return resolverAtajos(leer(CLAVE_ATAJOS));
}

export function guardarAtajos(config: ConfiguracionAtajos): boolean {
  const guardado = escribir(CLAVE_ATAJOS, serializarAtajos(config));
  avisar();
  return guardado;
}

// ---- Todo -----------------------------------------------------------------

/** Borra todas las preferencias guardadas: tema claro y el resto según el sistema. */
export function borrarPreferencias(): boolean {
  let ok = true;
  for (const clave of CLAVES_PREFERENCIAS) ok = escribir(clave, null) && ok;
  document.documentElement.removeAttribute('data-theme');
  document.documentElement.dataset.animaciones = animacionesDelSistema();
  delete document.documentElement.dataset.texto;
  avisar();
  return ok;
}
