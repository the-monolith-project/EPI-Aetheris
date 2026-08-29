import { obtenerDatasetAnalitico } from './analisis-api';
import type { FiltrosAnalisis } from './tipos-analisis';

function celdaCsv(valor: string | number | null): string {
  if (valor === null) return '';
  const texto = String(valor);
  return /[",\n]/.test(texto) ? `"${texto.replaceAll('"', '""')}"` : texto;
}

function descargar(nombre: string, contenido: string): void {
  const enlace = document.createElement('a');
  const url = URL.createObjectURL(
    new Blob([contenido], { type: 'text/csv;charset=utf-8' }),
  );
  enlace.href = url;
  enlace.download = nombre;
  enlace.click();
  URL.revokeObjectURL(url);
}

export async function exportarAnalisisCsv(
  filtros: FiltrosAnalisis,
): Promise<number> {
  const dataset = await obtenerDatasetAnalitico(filtros.anio);
  const codigos =
    filtros.comparar.length > 0
      ? filtros.comparar
      : filtros.departamento
        ? [filtros.departamento]
        : dataset.departamentos.map((departamento) => departamento.codigo);
  const seleccionados = new Set(codigos);
  const encabezado = [
    'anio',
    'semana_epi',
    'departamento_codigo',
    'departamento_nombre',
    'serie',
    'casos_observados',
    'iv',
    'anomalia_sigma',
    'presion_percentil',
    'presion_categoria',
    'p50_baseline',
    'p75_baseline',
    'n_obs_baseline',
    'anios_baseline',
  ];
  const filas = dataset.departamentos
    .filter((departamento) => seleccionados.has(departamento.codigo))
    .flatMap((departamento) =>
      departamento.semanas
        .filter(
          (semana) =>
            semana.semana_epi >= filtros.semanaDesde &&
            semana.semana_epi <= filtros.semanaHasta,
        )
        .map((semana) => {
          const casos = semana[filtros.serie];
          const presion = semana[`presion_${filtros.serie}`];
          return [
            filtros.anio,
            semana.semana_epi,
            departamento.codigo,
            departamento.nombre,
            filtros.serie,
            casos,
            semana.iv,
            semana.anomaly_sigma,
            presion.percentil,
            presion.categoria,
            presion.p50_baseline,
            presion.p75_baseline,
            presion.n_obs_baseline,
            presion.anios_baseline,
          ]
            .map(celdaCsv)
            .join(',');
        }),
    );
  const sufijoDepartamentos = codigos.length === 1 ? `-${codigos[0]}` : '';
  descargar(
    `epi-aetheris-dengue-${filtros.anio}-${filtros.serie}-se${String(filtros.semanaDesde).padStart(2, '0')}-se${String(filtros.semanaHasta).padStart(2, '0')}${sufijoDepartamentos}.csv`,
    `\uFEFF${[encabezado.join(','), ...filas].join('\n')}\n`,
  );
  return filas.length;
}
