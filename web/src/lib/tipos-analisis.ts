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

export type CapaAnalitica =
  'minsal_volumen' | 'iv' | 'anomalia' | 'presion' | 'confianza';

export interface FiltrosAnalisis {
  anio: number;
  semana: number;
  semanaDesde: number;
  semanaHasta: number;
  serie: SerieEpidemiologica;
  departamento: string | null;
  comparar: string[];
  modoMinsal: ModoMinsal;
  capa: CapaAnalitica;
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
  /** Total de OpenDengue hasta 2024; sospechosos del tablero desde 2025. */
  fuente?: 'opendengue_v1_3' | 'minsal_tablero';
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

export type EventoRespiratorio = 'ira' | 'neumonias';

export interface SemanaRespiratoriaNacional {
  semana_inicio: string;
  anio: number;
  semana_epi: number;
  conteo: number;
}

/** Serie nacional del tablero de MINSAL desde 2025 (ADR 0021). Las semanas
 *  que el tablero no publicó no traen fila. */
export interface SerieRespiratoriaNacional {
  disponible: true;
  evento: EventoRespiratorio;
  fuente: 'minsal_tablero';
  unidad: 'conteo_notificado';
  semanas: SemanaRespiratoriaNacional[];
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

// --- Estimación de horizonte corto de dengue (GET /api/nowcast-dengue) --------
// Artefacto precomputado por backend/ingestion/nowcast_tablero_dengue.py sobre
// la base de nowcast_estimacion_dengue.py. Desde 2025 la serie es la del
// tablero de MINSAL y el método es la mezcla del experimento
// docs/experimentos/experimento-nowcast-tendencia.md del monorepo.
// No es clasificación de riesgo ni aviso epidemiológico; ver
// docs/biblioteca/05-sensibilidad-y-honestidad.md.

export interface PuntoObservadoNowcast {
  fecha: string;
  /** null: semana que la fuente no publicó (la 53 de 2025 en el tablero). */
  casos: number | null;
}

export interface EstimacionHorizonte {
  h: number;
  fecha: string;
  anio: number;
  semana: number;
  cuantiles: number[];
  mediana: number;
  banda_50: [number, number];
  banda_95: [number, number];
}

export interface PuntoBacktestNowcast {
  fecha: string;
  anio: number;
  observado: number;
  mediana: number;
  banda_50: [number, number];
  banda_95: [number, number];
}

export interface DesempenoNowcast {
  horizonte: number;
  baseline: string;
  wis_modelo: number;
  wis_baseline: number;
  reduccion_wis: number;
  skill_medio_por_anio: number;
  skill_por_anio: Record<string, number>;
  anios_ganados: number;
  n_anios: number;
  cobertura_50: number;
  cobertura_95: number;
  /** true: los años del desempeño se usaron para elegir el método. */
  dentro_de_muestra?: boolean;
}

/** Prueba del método con semanas publicadas después de elegirlo. */
export interface PruebaNowcast {
  inicio: { fecha: string; anio: number; semana: number };
  semanas: number;
  horizontes_decisivos: number[];
  referencia: string;
}

export interface NowcastDengue {
  disponible: boolean;
  motivo?: string;
  aviso: string;
  generado?: string;
  fuente_serie?: string;
  metodo?: string;
  alcance_historia_desde?: number;
  ancla?: { fecha: string; anio: number; semana: number; casos: number };
  horizontes?: number[];
  observado?: PuntoObservadoNowcast[];
  estimacion?: EstimacionHorizonte[];
  backtest?: {
    horizonte: number;
    anios: number[];
    puntos: PuntoBacktestNowcast[];
  };
  desempeno?: DesempenoNowcast;
  prueba?: PruebaNowcast;
  nota_alcance?: string;
}

// --- Predicción retrospectiva (GET /api/nowcast-dengue/retrospectivo) --------
// Abanico h = 1..8 que el modelo habría dado desde cada semana de la serie con
// los datos disponibles hasta esa semana. Precomputado por
// backend/ingestion/nowcast_retrospectivo_dengue.py con el método de ADR 0020
// hasta 2024 y por nowcast_tablero_dengue.py con la mezcla desde 2025.
// Formato compacto: los valores de cada horizonte van por posición, en el
// orden de `campos_horizonte`.

/** [mediana, b50_inf, b50_sup, b95_inf, b95_sup, wis_modelo, wis_referencia] */
export type ValoresHorizonteRetro = [
  number,
  number,
  number,
  number,
  number,
  number | null,
  number | null,
];

export interface OrigenRetro {
  fecha: string;
  anio: number;
  semana: number;
  /** Ausente cuando `motivo` explica por qué no hay predicción. */
  h?: (ValoresHorizonteRetro | null)[];
  /** hueco_en_serie: a las 8 semanas previas les falta una sin publicar. */
  motivo?: 'historia_insuficiente' | 'hueco_en_serie';
}

export interface ResumenAnioHorizonteRetro {
  n: number;
  wis_modelo: number;
  wis_referencia: number;
  skill: number | null;
  cobertura_50: number;
  cobertura_95: number;
}

export interface NowcastDengueRetrospectivo {
  disponible: boolean;
  motivo?: string;
  aviso: string;
  generado?: string;
  horizontes?: number[];
  anios_prueba?: number[];
  anio_excluido?: number;
  aviso_anio_excluido?: string;
  referencia_por_horizonte?: Record<string, string>;
  primera_semana_con_prediccion?: {
    fecha: string;
    anio: number;
    semana: number;
  };
  campos_horizonte?: string[];
  /** [fecha, casos] de toda la serie, hasta la semana de anclaje. */
  observado?: [string, number | null][];
  origenes?: OrigenRetro[];
  /** año del objetivo -> horizonte -> resumen */
  resumen_por_anio?: Record<string, Record<string, ResumenAnioHorizonteRetro>>;
  /** Tramo del tablero de MINSAL: desde `inicio` el método es la mezcla. */
  tablero?: {
    inicio: { fecha: string; anio: number; semana: number };
    metodo: string;
    referencia: string;
    anios: number[];
    prueba: PruebaNowcast;
  };
}
