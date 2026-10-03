// Integridad de la vigilancia, módulo M4. Port de completitud_semana,
// completitud_anual, cuadre_boletin, discrepancia y antiguedad_serie del
// backend (vigilancia.py del monorepo), para que la ficha enriquecida de M4
// muestre los tres hechos con las mismas cifras que la API.
// tests/unit/integridad.test.ts lo compara con valores generados con el
// Python original. Si cambia uno, cambia el otro.
//
// El calendario epidemiológico está escrito a mano: semanas de domingo a
// sábado y la semana 1 es la primera con al menos cuatro días del año (la que
// contiene el 4 de enero). Algunos años tienen 53 semanas.

import { redondear } from './estadistica.ts';

export const N_DEPARTAMENTOS = 14;
export const SEMANAS_NOMINALES = 52;

const MS_DIA = 86_400_000;

// ---- Completitud geográfica ------------------------------------------------

export interface DepartamentoCompletitud {
  codigo: string;
  nombre: string;
  presente: boolean;
}

export interface CompletitudSemana {
  n: number;
  esperado: number;
  /** n / esperado con cuatro decimales. */
  ratio: number;
  departamentos: DepartamentoCompletitud[];
}

/** De cuántos departamentos del catálogo hay fila esa semana. */
export function completitudSemana(
  catalogo: readonly (readonly [string, string])[],
  presentes: Iterable<string>,
): CompletitudSemana {
  const conFila = new Set(presentes);
  const departamentos = catalogo.map(([codigo, nombre]) => ({
    codigo,
    nombre,
    presente: conFila.has(codigo),
  }));
  const n = departamentos.filter((d) => d.presente).length;
  const esperado = catalogo.length;
  return {
    n,
    esperado,
    ratio: esperado > 0 ? redondear(n / esperado, 4) : 0,
    departamentos,
  };
}

export interface CompletitudAnual {
  /** Semanas con los 14 departamentos. */
  semanas_completas: number;
  /** Semanas que aparecen en la fuente, con cualquier número de departamentos. */
  semanas_con_dato: number;
  semanas_nominales: number;
}

/**
 * Resumen de un año a partir de cuántos departamentos tienen fila cada
 * semana. Una semana que no está en `semanasN` es un hueco de la fuente: no
 * se cuenta como 0 de 14 ni como semana con dato.
 */
export function completitudAnual(
  semanasN: Record<string | number, number>,
  esperado: number = N_DEPARTAMENTOS,
): CompletitudAnual {
  const valores = Object.values(semanasN);
  return {
    semanas_completas: valores.filter((n) => n >= esperado).length,
    semanas_con_dato: valores.length,
    semanas_nominales: SEMANAS_NOMINALES,
  };
}

// ---- Cuadre del boletín ----------------------------------------------------

export interface Boletin {
  suma_departamental_probable: number | null;
  total_nacional_publicado_probable: number | null;
  suma_departamental_confirmado: number | null;
  total_nacional_publicado_confirmado: number | null;
  validacion_cuadra: boolean | null;
  estado: string | null;
  nombre_archivo: string | null;
}

export interface CuadreSerie {
  suma_departamental: number | null;
  total_nacional_publicado: number | null;
  discrepancia: number | null;
}

export interface CuadreBoletin {
  cuadra: boolean | null;
  estado: string | null;
  nombre_archivo: string | null;
  probable: CuadreSerie;
  confirmado: CuadreSerie;
}

/** Suma departamental menos total publicado. Null si falta un lado (nunca un 0 inventado). */
export function discrepancia(
  suma: number | null,
  publicado: number | null,
): number | null {
  if (suma === null || publicado === null) return null;
  return suma - publicado;
}

/**
 * Lo que quedó guardado al procesar el boletín, sin recalcular la suma de
 * los departamentos. Sin boletín, todo queda vacío.
 */
export function cuadreBoletin(boletin: Boletin | null): CuadreBoletin {
  const serie = (
    suma: number | null,
    publicado: number | null,
  ): CuadreSerie => ({
    suma_departamental: suma,
    total_nacional_publicado: publicado,
    discrepancia: discrepancia(suma, publicado),
  });
  if (!boletin) {
    return {
      cuadra: null,
      estado: null,
      nombre_archivo: null,
      probable: serie(null, null),
      confirmado: serie(null, null),
    };
  }
  return {
    cuadra: boletin.validacion_cuadra,
    estado: boletin.estado,
    nombre_archivo: boletin.nombre_archivo,
    probable: serie(
      boletin.suma_departamental_probable,
      boletin.total_nacional_publicado_probable,
    ),
    confirmado: serie(
      boletin.suma_departamental_confirmado,
      boletin.total_nacional_publicado_confirmado,
    ),
  };
}

// ---- Estado del mapa ---------------------------------------------------------

export type EstadoIntegridad = 'sin_dato' | 'presente' | 'no_cuadra';

/**
 * Estado de un departamento en la capa del mapa: sin fila esa semana, con
 * fila, o con fila en un boletín que no cuadra. Un cuadre desconocido (null)
 * no marca nada.
 */
export function estadoIntegridad(
  presente: boolean,
  cuadra: boolean | null | undefined,
): EstadoIntegridad {
  if (!presente) return 'sin_dato';
  return cuadra === false ? 'no_cuadra' : 'presente';
}

export const ETIQUETAS_ESTADO: Record<EstadoIntegridad, string> = {
  sin_dato: 'sin dato esta semana',
  presente: 'dato presente',
  no_cuadra: 'dato presente, el boletín no cuadra',
};

// ---- Calendario epidemiológico y antigüedad ------------------------------------

export interface SemanaEpi {
  anio: number;
  semana: number;
}

/** Día como número de días desde 1970-01-01 (UTC), sin horas. */
function diaUtc(anio: number, mes: number, dia: number): number {
  return Date.UTC(anio, mes - 1, dia) / MS_DIA;
}

function aDia(fecha: Date | string): number {
  if (typeof fecha === 'string') {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(fecha);
    if (!m) throw new Error(`Fecha no válida: ${fecha}`);
    return diaUtc(Number(m[1]), Number(m[2]), Number(m[3]));
  }
  // Una Date se lee con el día del calendario local de quien mira.
  return diaUtc(fecha.getFullYear(), fecha.getMonth() + 1, fecha.getDate());
}

/** 0 = domingo … 6 = sábado. El 1970-01-01 fue jueves. */
function diaSemana(dia: number): number {
  return (((dia + 4) % 7) + 7) % 7;
}

/** Domingo en que empieza la semana 1 de `anio`: el de la semana del 4 de enero. */
export function inicioSemana1(anio: number): number {
  const cuatro = diaUtc(anio, 1, 4);
  return cuatro - diaSemana(cuatro);
}

/** Domingo en que empieza la semana `semana` de `anio`, en días desde 1970. */
export function inicioSemanaEpi(anio: number, semana: number): number {
  return inicioSemana1(anio) + (semana - 1) * 7;
}

/** Semanas epidemiológicas de un año: 52 o 53. */
export function semanasDelAnio(anio: number): number {
  return (inicioSemana1(anio + 1) - inicioSemana1(anio)) / 7;
}

/** Año y semana epidemiológica de una fecha. */
export function semanaEpidemiologica(fecha: Date | string): SemanaEpi {
  const dia = aDia(fecha);
  const domingo = dia - diaSemana(dia);
  // La semana es del año en que cae su miércoles (el que tiene al menos cuatro días).
  const anio = new Date((domingo + 3) * MS_DIA).getUTCFullYear();
  return { anio, semana: (domingo - inicioSemana1(anio)) / 7 + 1 };
}

export interface Antiguedad {
  ultima_anio: number | null;
  ultima_semana_epi: number | null;
  semanas: number | null;
}

/**
 * Semanas epidemiológicas entre la última semana con dato y la semana de
 * `hoy`. Sin dato, todo queda vacío. Si la última semana es posterior a hoy,
 * el resultado es negativo.
 */
export function antiguedadSerie(
  ultima: readonly [number, number] | null,
  hoy: Date | string,
): Antiguedad {
  if (!ultima) {
    return { ultima_anio: null, ultima_semana_epi: null, semanas: null };
  }
  const [anio, semana] = ultima;
  const actual = semanaEpidemiologica(hoy);
  const semanas =
    (inicioSemanaEpi(actual.anio, actual.semana) -
      inicioSemanaEpi(anio, semana)) /
    7;
  return { ultima_anio: anio, ultima_semana_epi: semana, semanas };
}

// ---- Ejemplo de la ficha -----------------------------------------------------------

/** Ejemplo: once departamentos con fila; faltan Morazán, La Unión y Cabañas. */
export const EJEMPLO_FALTANTES = ['SV-MO', 'SV-UN', 'SV-CA'] as const;

export const EJEMPLO_BOLETIN: Boletin = {
  suma_departamental_probable: 405,
  total_nacional_publicado_probable: 410,
  suma_departamental_confirmado: 12,
  total_nacional_publicado_confirmado: 12,
  validacion_cuadra: false,
  estado: 'procesado',
  nombre_archivo: null,
};

/** Última semana de la serie del ejemplo y la fecha desde la que se mira. */
export const EJEMPLO_ANTIGUEDAD = {
  ultima: [2023, 52] as const,
  hoy: '2026-10-02',
};

export interface PresetIntegridad {
  clave: string;
  etiqueta: string;
  faltantes: string[];
  suma: number | null;
  publicado: number | null;
}

export const PRESETS_INTEGRIDAD: PresetIntegridad[] = [
  {
    clave: 'completa',
    etiqueta: 'Semana completa',
    faltantes: [],
    suma: 410,
    publicado: 410,
  },
  {
    clave: 'faltan',
    etiqueta: 'Faltan departamentos',
    faltantes: ['SV-MO', 'SV-UN', 'SV-CA'],
    suma: 380,
    publicado: 380,
  },
  {
    clave: 'no-cuadra',
    etiqueta: 'Boletín que no cuadra',
    faltantes: [],
    suma: 405,
    publicado: 410,
  },
  {
    clave: 'sin-boletin',
    etiqueta: 'Sin boletín',
    faltantes: [],
    suma: null,
    publicado: null,
  },
];
