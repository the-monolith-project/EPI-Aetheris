import { DEPARTAMENTOS_POR_CODIGO } from './departamentos';

const CLAVE = 'epi:departamento';

/** Departamento que la persona eligió recordar; null si no hay o no es válido. */
export function leerDepartamentoRecordado(): string | null {
  try {
    const valor = window.localStorage.getItem(CLAVE);
    return valor && DEPARTAMENTOS_POR_CODIGO[valor] ? valor : null;
  } catch {
    return null;
  }
}

/** Guarda (o borra con null) el departamento. Devuelve false si el navegador no deja. */
export function guardarDepartamentoRecordado(codigo: string | null): boolean {
  try {
    if (codigo === null) window.localStorage.removeItem(CLAVE);
    else window.localStorage.setItem(CLAVE, codigo);
    return true;
  } catch {
    return false;
  }
}
