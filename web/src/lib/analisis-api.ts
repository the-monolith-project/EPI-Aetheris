import type {
  AnioAnalisisDengue,
  DatasetAnaliticoDengue,
} from './tipos-analisis';

const API_BASE = import.meta.env.PUBLIC_API_URL ?? 'http://localhost:8000';
const cachePorAnio = new Map<
  AnioAnalisisDengue,
  Promise<DatasetAnaliticoDengue>
>();

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
