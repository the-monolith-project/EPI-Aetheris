export const ANIOS_ANALISIS_DENGUE = [2018, 2019, 2021, 2022, 2023] as const;

export type AnioAnalisisDengue = (typeof ANIOS_ANALISIS_DENGUE)[number];
export type SerieEpidemiologica = 'probable' | 'confirmado';
export type ModoMinsal = 'semana' | 'ytd' | 'historico';

export interface FiltrosAnalisis {
  anio: AnioAnalisisDengue;
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

export interface CasoNacionalSemanal {
  semana_inicio: string;
  anio: number;
  semana_epi: number;
  conteo: number;
}
