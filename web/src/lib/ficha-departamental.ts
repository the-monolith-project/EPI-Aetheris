export interface SemanaM1M2 {
  semana_epi: number;
  iv_real: number | null;
  p25_baseline: number | null;
  mediana_baseline: number | null;
  p75_baseline: number | null;
  anomaly_sigma: number | null;
}

export interface DetallePresion {
  casos_observados: number | null;
  percentil: number | null;
  categoria: 'baja' | 'media' | 'alta' | null;
  p50_baseline: number | null;
  p75_baseline: number | null;
  n_obs_baseline: number;
  anios_baseline: number;
  nota?: string;
}

export interface SemanaPresion {
  semana_epi: number;
  probable: DetallePresion;
  confirmado: DetallePresion;
}

export interface RespuestaM1M2 {
  departamento_codigo: string;
  departamento_nombre: string;
  anio: number;
  semanas: SemanaM1M2[];
  aviso: string;
}

export interface RespuestaPresion {
  departamento_codigo: string;
  departamento_nombre: string;
  anio: number;
  semanas: SemanaPresion[];
  aviso: string;
}

export interface RespuestaSerieRespiratoria {
  disponible?: boolean;
  motivo?: string;
  departamento_codigo?: string;
  departamento_nombre?: string;
  anios?: number[];
  series?: Record<string, Array<[number, number]>>;
  aviso?: string;
}

export interface AlertaRespuesta {
  id: number;
  tipo: 'dengue' | 'respiratorio';
  nivel: 'informativo' | 'atencion' | 'intensificacion';
  titulo: string;
  contexto: string;
  indicaciones: string;
  fuente: string;
  autor: string;
  vigente_desde: string;
  vigente_hasta: string | null;
  activa: boolean;
  contacto_vigilancia?: string | null;
  signos_alarma?: string | null;
  criterios_referencia?: string | null;
  acciones_comunitarias?: string | null;
  etiqueta?: string | null;
}

export interface PayloadAlertasRespuesta {
  aviso: string;
  ultima_revision: string;
  alertas: AlertaRespuesta[];
}

export const AVISO_DEFECTO_IDONEIDAD =
  'Índice de idoneidad biofísica del vector (Iv, 0 a 1) y anomalía continua calculados a partir de temperatura y precipitación ERA5-Land (Open-Meteo). Capa descriptiva: describe condiciones meteorológicas históricas favorables al vector, no predice casos futuros.';

export const AVISO_DEFECTO_PRESION =
  'La presión epidemiológica relativa compara el conteo de la semana seleccionada contra los mismos períodos de años históricos comparables (percentil leave-one-out con ventana de ±1 semana). No predice casos futuros ni constituye un umbral de alerta automática.';

export const AVISO_DEFECTO_IRA =
  'Serie semanal de Infección Respiratoria Aguda (IRA) notificada en unidades del MINSAL (2018-2023, excluyendo 2020). Capa descriptiva agregada por departamento; las semanas sin dato corresponden a boletines no publicados o con tablas ilegibles en la fuente original.';

export const AVISO_DEFECTO_NEUMONIAS =
  'Serie semanal de Neumonías notificadas en unidades del MINSAL (2018-2023, excluyendo 2020). Capa descriptiva agregada por departamento.';

export const AVISO_DEFECTO_PREVENCION =
  'Material informativo de prevención y manejo vectorial reproducido literalmente a partir de fuentes oficiales públicas (OPS/OMS, MINSAL). No constituye consejo clínico personalizado ni sustituye la atención médica directa.';

export function encontrarUltimaSemanaM1M2(
  semanas: SemanaM1M2[],
): SemanaM1M2 | null {
  for (let i = semanas.length - 1; i >= 0; i--) {
    if (semanas[i].iv_real !== null || semanas[i].anomaly_sigma !== null) {
      return semanas[i];
    }
  }
  return null;
}

export function encontrarUltimaSemanaPresion(
  semanas: SemanaPresion[],
  serie: 'probable' | 'confirmado',
): { semana_epi: number; detalle: DetallePresion } | null {
  for (let i = semanas.length - 1; i >= 0; i--) {
    const detalle = semanas[i]?.[serie];
    if (detalle && detalle.percentil !== null) {
      return { semana_epi: semanas[i].semana_epi, detalle };
    }
  }
  return null;
}

export function formatearSigma(sigma: number | null | undefined): string {
  if (sigma === null || sigma === undefined || Number.isNaN(sigma)) {
    return 'Sin dato';
  }
  const signo = sigma > 0 ? '+' : '';
  return `${signo}${sigma.toFixed(2)} σ`;
}

export function formatearPercentil(
  percentil: number | null | undefined,
): string {
  if (
    percentil === null ||
    percentil === undefined ||
    Number.isNaN(percentil)
  ) {
    return 'Sin dato';
  }
  return `P${percentil.toFixed(1)}`;
}

export function formatearCategoria(
  categoria: 'baja' | 'media' | 'alta' | null | undefined,
): string {
  if (!categoria) return 'Sin clasificación';
  switch (categoria) {
    case 'baja':
      return 'Baja (≤ P50 histórico)';
    case 'media':
      return 'Media (P50–P75 histórico)';
    case 'alta':
      return 'Alta (> P75 histórico)';
  }
}
