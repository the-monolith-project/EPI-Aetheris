import type {
  AnioAnalisisDengue,
  CasoNacionalSemanal,
  DatasetAnaliticoDengue,
  FiltrosAnalisis,
  ProcedenciaAnalitica,
} from './tipos-analisis';

const API_BASE = import.meta.env.PUBLIC_API_URL ?? 'http://localhost:8000';
const cachePorAnio = new Map<
  AnioAnalisisDengue,
  Promise<DatasetAnaliticoDengue>
>();
let cacheCasosNacionales: Promise<CasoNacionalSemanal[]> | null = null;
const cacheProcedencia = new Map<string, Promise<ProcedenciaAnalitica>>();

function cargarDataset(
  anio: AnioAnalisisDengue,
): Promise<DatasetAnaliticoDengue> {
  return fetch(`${API_BASE}/api/v1/analisis/dengue?year=${anio}`).then(
    async (respuesta) => {
      if (!respuesta.ok) {
        throw new Error(
          `No se pudo cargar el dataset analítico (${respuesta.status}).`,
        );
      }
      const datos: unknown = await respuesta.json();
      if (
        !datos ||
        typeof datos !== 'object' ||
        !Array.isArray((datos as { departamentos?: unknown }).departamentos)
      ) {
        throw new Error('El dataset analítico no tiene el contrato esperado.');
      }
      return datos as DatasetAnaliticoDengue;
    },
  );
}

export function obtenerDatasetAnalitico(
  anio: AnioAnalisisDengue,
): Promise<DatasetAnaliticoDengue> {
  let solicitud = cachePorAnio.get(anio);
  if (!solicitud) {
    solicitud = cargarDataset(anio).catch((error) => {
      cachePorAnio.delete(anio);
      throw error;
    });
    cachePorAnio.set(anio, solicitud);
  }
  return solicitud;
}

export function obtenerCasosNacionales(): Promise<CasoNacionalSemanal[]> {
  if (!cacheCasosNacionales) {
    cacheCasosNacionales = fetch(`${API_BASE}/api/casos-nacional`)
      .then(async (respuesta) => {
        if (!respuesta.ok) {
          throw new Error(
            `No se pudo cargar la serie nacional (${respuesta.status}).`,
          );
        }
        const datos: unknown = await respuesta.json();
        if (!Array.isArray(datos)) {
          throw new Error('La serie nacional no tiene el contrato esperado.');
        }
        return datos as CasoNacionalSemanal[];
      })
      .catch((error) => {
        cacheCasosNacionales = null;
        throw error;
      });
  }
  return cacheCasosNacionales;
}

export function obtenerProcedenciaAnalitica(
  filtros: Pick<FiltrosAnalisis, 'anio' | 'semana' | 'serie' | 'departamento'>,
): Promise<ProcedenciaAnalitica> {
  if (!filtros.departamento) {
    return Promise.reject(
      new Error('Se requiere un departamento para consultar procedencia.'),
    );
  }
  const clave = [
    filtros.anio,
    filtros.semana,
    filtros.serie,
    filtros.departamento,
  ].join(':');
  let solicitud = cacheProcedencia.get(clave);
  if (!solicitud) {
    const parametros = new URLSearchParams({
      year: String(filtros.anio),
      week: String(filtros.semana),
      serie: filtros.serie,
      dept: filtros.departamento,
    });
    solicitud = fetch(
      `${API_BASE}/api/v1/analisis/dengue/procedencia?${parametros}`,
    )
      .then(async (respuesta) => {
        if (!respuesta.ok) {
          throw new Error(
            `No se pudo cargar la procedencia (${respuesta.status}).`,
          );
        }
        return (await respuesta.json()) as ProcedenciaAnalitica;
      })
      .catch((error) => {
        cacheProcedencia.delete(clave);
        throw error;
      });
    cacheProcedencia.set(clave, solicitud);
  }
  return solicitud;
}
