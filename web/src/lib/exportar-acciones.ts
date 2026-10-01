// Acciones de exportar e incrustar compartidas por los botones sueltos
// (BotonExportarGrafico, BotonIncrustar) y por el menú «Exportar»
// (MenuExportar). Cada una devuelve el mensaje que se anuncia al usuario.
import { obtenerFiltrosAnalisis } from './analisis-state';
import { encontrarGrafico, exportarPng, exportarSvg } from './exportar-grafico';
import { codigoIncrustacion } from './incrustar';

export type FormatoImagen = 'svg' | 'png';

export interface OrigenExportacion {
  titulo: string;
  fuente: string;
  /** "analisis" toma los filtros vigentes de /dengue; otro texto se usa tal cual. */
  filtros?: string;
}

function textoFiltrosAnalisis(): string {
  const f = obtenerFiltrosAnalisis();
  const partes = [
    f.departamento ?? 'todos los departamentos',
    String(f.anio),
    f.serie,
    `SE${f.semanaDesde}–SE${f.semanaHasta}`,
  ];
  return partes.join(' · ');
}

/** Descarga como imagen el primer gráfico de `seccion`. */
export async function exportarImagen(
  seccion: Element | null,
  origen: OrigenExportacion,
  formato: FormatoImagen,
): Promise<string> {
  const svg = seccion ? encontrarGrafico(seccion) : null;
  if (!svg) return 'El gráfico todavía no está disponible.';
  const opciones = {
    titulo: origen.titulo,
    fuente: origen.fuente,
    filtros:
      origen.filtros === 'analisis' ? textoFiltrosAnalisis() : origen.filtros,
  };
  try {
    if (formato === 'png') await exportarPng(svg, opciones);
    else exportarSvg(svg, opciones);
    return 'Imagen descargada.';
  } catch {
    return 'No se pudo generar la imagen.';
  }
}

/** Copia el `<iframe>` de incrustación; sin portapapeles devuelve el código. */
export async function copiarIncrustacion(opciones: {
  src: string;
  titulo: string;
  alto: number;
}): Promise<string> {
  const codigo = codigoIncrustacion(opciones);
  try {
    await navigator.clipboard.writeText(codigo);
    return 'Código copiado.';
  } catch {
    return codigo;
  }
}
