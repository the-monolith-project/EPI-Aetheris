export const ANIOS_ANALISIS_DENGUE = [2018, 2019, 2021, 2022, 2023] as const;

export type AnioAnalisisDengue = (typeof ANIOS_ANALISIS_DENGUE)[number];
export type SerieEpidemiologica = 'probable' | 'confirmado';
export type ModoMinsal = 'semana' | 'ytd' | 'historico';

export function esAnioAnalisisDengue(
  valor: number,
): valor is AnioAnalisisDengue {
  return (ANIOS_ANALISIS_DENGUE as readonly number[]).includes(valor);
}

/** Años pintables en M1/M2. No amplía el dataset de dengue (ADR 0018). */
export function aniosClimaPresentacion(hoy: Date = new Date()): number[] {
  const fin = hoy.getFullYear();
  const anios: number[] = [];
  for (let anio = 2018; anio <= fin; anio += 1) anios.push(anio);
  return anios;
}

export function notaAnioSoloClima(anio: number): string {
  return (
    `El año ${anio} no tiene casos MINSAL departamentales. ` +
    'Idoneidad y anomalía (clima) sí cubren este año; la presión epidemiológica se detiene en 2023.'
  );
}

export interface FiltrosAnalisis {
  anio: number;
  semana: number;
  semanaDesde: number;
  semanaHasta: number;
  serie: SerieEpidemiologica;
  departamento: string | null;
  comparar: string[];
  modoMinsal: ModoMinsal;
}

export interface PresionAnalitica {
  casos_observados: number | null;
  percentil: number | null;
  categoria: 'baja' | 'media' | 'alta' | null;
  p50_baseline: number | null;
  p75_baseline: number | null;
  n_obs_baseline: number;
  anios_baseline: number;
  nota?: string;
}

export interface SemanaAnalitica {
  semana_epi: number;
  probable: number | null;
  confirmado: number | null;
  iv: number | null;
  anomaly_sigma: number | null;
  presion_probable: PresionAnalitica;
  presion_confirmado: PresionAnalitica;
  nota_clima?: string;
}

export interface DepartamentoAnalitico {
  codigo: string;
  nombre: string;
  semanas: SemanaAnalitica[];
}

export interface DatasetAnaliticoDengue {
  anio: AnioAnalisisDengue;
  anios_disponibles: AnioAnalisisDengue[];
  series: SerieEpidemiologica[];
  departamentos: DepartamentoAnalitico[];
  avisos: {
    idoneidad: string;
    presion: string;
  };
}

/** Semana de `GET /api/v1/temporal/{codigo}` — Iv real del año contra su
 *  banda histórica leave-one-out y el Z-score continuo (M1 y M2). */
export interface SemanaSerieIdoneidad {
  semana_epi: number;
  iv_real: number | null;
  p25_baseline: number | null;
  mediana_baseline: number | null;
  p75_baseline: number | null;
  anomaly_sigma: number | null;
}

export interface SerieTemporalIdoneidad {
  departamento_codigo: string;
  departamento_nombre: string;
  anio: number;
  semanas: SemanaSerieIdoneidad[];
  aviso: string;
}

/** Semana de `GET /api/v1/presion/temporal/{codigo}` — percentil de casos
 *  observados contra la propia historia del departamento (M3), por serie.
 *  `probable`/`confirmado` reusan `PresionAnalitica`: `percentil` va de 0 a
 *  100 (o `null` si el baseline es insuficiente o falta la observación). */
export interface SemanaSeriePresion {
  semana_epi: number;
  probable: PresionAnalitica;
  confirmado: PresionAnalitica;
}

export interface SerieTemporalPresion {
  departamento_codigo: string;
  departamento_nombre: string;
  anio: number;
  semanas: SemanaSeriePresion[];
  aviso: string;
}

export interface CasoNacionalSemanal {
  semana_inicio: string;
  anio: number;
  semana_epi: number;
  conteo: number;
}

export interface RegistroProcedencia {
  conteo: number;
  fecha_ingesta: string | null;
  fuente: {
    codigo: string;
    nombre: string;
    url_referencia: string | null;
  };
  boletin: {
    anio: number;
    semana_archivo: number | null;
    nombre_archivo: string;
    url_origen: string;
    estado_extraccion: string;
    validacion_cuadra: boolean | null;
    fecha_procesado: string | null;
  } | null;
}

export interface ProcedenciaAnalitica {
  anio: AnioAnalisisDengue;
  semana_epi: number;
  serie: SerieEpidemiologica;
  departamento_codigo: string;
  departamento_nombre: string;
  disponible: boolean;
  conteo_observado: number | null;
  registros: RegistroProcedencia[];
}

export interface DepartamentoIRA {
  nombre: string;
  codigo: string;
  notificado_total: number;
  semanas_con_dato: number;
  primer_anio: number | null;
  ultimo_anio: number | null;
}

export interface RespuestaIraDepartamental {
  departamentos: DepartamentoIRA[];
  aviso: string;
}

export interface CompletitudAnual {
  semanas_completas: number;
  semanas_con_dato: number;
  semanas_nominales: number;
}

export interface ResumenAnualIntegridad {
  anio: number;
  probable: CompletitudAnual;
  confirmado: CompletitudAnual;
}

export interface AntiguedadSerie {
  ultima_anio: number | null;
  ultima_semana_epi: number | null;
  semanas: number | null;
}

export interface IntegridadVigilancia {
  aviso: string;
  antiguedad: Record<string, AntiguedadSerie>;
  resumen_anual?: ResumenAnualIntegridad[];
}
