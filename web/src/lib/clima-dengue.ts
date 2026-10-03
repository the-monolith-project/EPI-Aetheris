// Derivaciones puras de los dos artefactos de clima y dengue (ADR 0023 del
// monorepo): etiquetas, formatos, posiciones y filas de tabla. Sin DOM ni
// ECharts, para poder probarlas con vitest (tests/unit/clima-dengue.test.ts).
import type {
  AporteHorizonteClima,
  AsociacionPais,
  CicloPais,
  ClimaDengueAnio,
  ClimaDengueMultipais,
  PerfilPaisClima,
  VariableAsociacion,
  VariableClimaDengue,
} from './tipos-analisis';

export const VARIABLES_CLIMA: VariableClimaDengue[] = [
  'temp_media',
  'temp_max',
  'temp_min',
  'precipitation_sum',
  'precipitation_hours',
  'humedad_relativa_media',
  'punto_rocio',
];

export const VARIABLES_ASOCIACION: VariableAsociacion[] = [
  ...VARIABLES_CLIMA,
  'oni',
];

export const CLAVE_EL_SALVADOR = 'EL SALVADOR';
export const ETIQUETA_TODOS_LOS_ANIOS = 'Todos los años';

const ETIQUETAS_VARIABLE: Record<
  VariableAsociacion,
  { corta: string; larga: string }
> = {
  temp_media: { corta: 'Temp. media', larga: 'Temperatura media (°C)' },
  temp_max: { corta: 'Temp. máxima', larga: 'Temperatura máxima (°C)' },
  temp_min: { corta: 'Temp. mínima', larga: 'Temperatura mínima (°C)' },
  precipitation_sum: { corta: 'Lluvia (mm)', larga: 'Lluvia (mm por semana)' },
  precipitation_hours: {
    corta: 'Lluvia (horas)',
    larga: 'Horas de lluvia por semana',
  },
  humedad_relativa_media: { corta: 'Humedad', larga: 'Humedad relativa (%)' },
  punto_rocio: { corta: 'Punto de rocío', larga: 'Punto de rocío (°C)' },
  oni: { corta: 'ONI', larga: 'Índice ONI (El Niño y La Niña)' },
};

export function etiquetaVariable(
  variable: VariableAsociacion,
  larga = false,
): string {
  const etiquetas = ETIQUETAS_VARIABLE[variable];
  return larga ? etiquetas.larga : etiquetas.corta;
}

const NOMBRES_PAIS: Record<string, string> = {
  BARBADOS: 'Barbados',
  BERMUDA: 'Bermudas',
  BOLIVIA: 'Bolivia',
  BRAZIL: 'Brasil',
  COLOMBIA: 'Colombia',
  'COSTA RICA': 'Costa Rica',
  'DOMINICAN REPUBLIC': 'República Dominicana',
  ECUADOR: 'Ecuador',
  'EL SALVADOR': 'El Salvador',
  GUATEMALA: 'Guatemala',
  HONDURAS: 'Honduras',
  JAMAICA: 'Jamaica',
  MEXICO: 'México',
  NICARAGUA: 'Nicaragua',
  PANAMA: 'Panamá',
  'PUERTO RICO': 'Puerto Rico',
  'UNITED STATES OF AMERICA': 'Estados Unidos',
  'VIRGIN ISLANDS (US)': 'Islas Vírgenes (EE. UU.)',
};

/** Nombre en español de la clave que usa la API (en inglés y mayúsculas). */
export function nombrePais(clave: string): string {
  if (NOMBRES_PAIS[clave]) return NOMBRES_PAIS[clave];
  const minusculas = clave.toLowerCase();
  return minusculas.charAt(0).toUpperCase() + minusculas.slice(1);
}

export function ordenarPaises(claves: string[]): string[] {
  return [...claves].sort((a, b) =>
    nombrePais(a).localeCompare(nombrePais(b), 'es'),
  );
}

// --- Formatos -----------------------------------------------------------------

/** Número con coma decimal y signo menos tipográfico (U+2212). */
export function formatoNumero(
  valor: number,
  decimales = 2,
  conSigno = false,
): string {
  const texto = Math.abs(valor).toFixed(decimales).replace('.', ',');
  const esCero = Number(texto.replace(',', '.')) === 0;
  if (valor < 0 && !esCero) return `−${texto}`;
  return conSigno ? `+${texto}` : texto;
}

export function formatoR(r: number, decimales = 2): string {
  return formatoNumero(r, decimales, true);
}

export function formatoIntervalo(
  intervalo: [number, number],
  decimales = 2,
): string {
  return `[${formatoR(intervalo[0], decimales)}; ${formatoR(intervalo[1], decimales)}]`;
}

/** 53196 -> "53.196" (punto de miles, como el resto del sitio). */
export function formatoMiles(valor: number): string {
  return String(Math.round(valor)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

export function excluyeCero(intervalo: [number, number]): boolean {
  return intervalo[0] > 0 || intervalo[1] < 0;
}

/** [2019, 2023, 2024] -> "2019, 2023 y 2024". */
export function listaEnTexto(elementos: (string | number)[]): string {
  const textos = elementos.map(String);
  if (textos.length <= 1) return textos.join('');
  return `${textos.slice(0, -1).join(', ')} y ${textos[textos.length - 1]}`;
}

// --- Aporte del clima al pronóstico (A1) --------------------------------------

export interface FilaAporte {
  anio: number;
  clima: number;
  oni: number;
  climaYOni: number;
  anioObjetivo: number;
}

export function filasAporte(
  a1: Record<string, AporteHorizonteClima>,
  horizonte: number,
): FilaAporte[] {
  const aporte = a1[String(horizonte)];
  if (!aporte) return [];
  return Object.keys(aporte.clima.por_anio)
    .map(Number)
    .sort((a, b) => a - b)
    .map((anio) => ({
      anio,
      clima: aporte.clima.por_anio[anio],
      oni: aporte.oni.por_anio[anio],
      climaYOni: aporte.clima_y_oni.por_anio[anio],
      anioObjetivo: aporte.anio.por_anio[anio],
    }));
}

export function horizontesDisponibles(
  a1: Record<string, AporteHorizonteClima>,
): number[] {
  return Object.keys(a1)
    .map(Number)
    .filter((h) => Number.isFinite(h))
    .sort((a, b) => a - b);
}

export function resumenAporte(filas: FilaAporte[], horizonte: number): string {
  if (filas.length === 0) return '';
  const ayudo = filas.filter((f) => f.clima > 0).map((f) => f.anio);
  const empeoro = filas.filter((f) => f.clima < 0).map((f) => f.anio);
  const partes = [
    `A ${horizonte} ${horizonte === 1 ? 'semana' : 'semanas'}, el clima ayudó al pronóstico en ${ayudo.length} de ${filas.length} años${ayudo.length ? ` (${listaEnTexto(ayudo)})` : ''}`,
  ];
  if (empeoro.length) {
    partes.push(
      `y lo empeoró en ${empeoro.length}${empeoro.length === 1 ? '' : ''} (${listaEnTexto(empeoro)})`,
    );
  }
  return `${partes.join(' ')}.`;
}

// --- Asociación por año (A3, A5) ------------------------------------------------

export interface CeldaAsociacion {
  fila: string;
  variable: VariableAsociacion;
  r: number;
  ic95: [number, number];
  /** Pares semanales de la fila (null si la fuente no los trae). */
  pares: number | null;
  excluyeCero: boolean;
}

export function celdasAsociacionAnio(a3: ClimaDengueAnio['A3']): {
  filas: string[];
  celdas: CeldaAsociacion[];
} {
  const anios = Object.keys(a3.por_anio)
    .map(Number)
    .sort((a, b) => a - b)
    .map(String);
  const filas = [...anios, ETIQUETA_TODOS_LOS_ANIOS];
  const celdas: CeldaAsociacion[] = [];
  for (const anio of anios) {
    const dato = a3.por_anio[anio];
    for (const variable of VARIABLES_ASOCIACION) {
      const { r, ic95 } = dato[variable];
      celdas.push({
        fila: anio,
        variable,
        r,
        ic95,
        pares: dato.pares ?? null,
        excluyeCero: excluyeCero(ic95),
      });
    }
  }
  for (const variable of VARIABLES_ASOCIACION) {
    const { r, ic95 } = a3.agrupado[variable];
    celdas.push({
      fila: ETIQUETA_TODOS_LOS_ANIOS,
      variable,
      r,
      ic95,
      pares: a3.agrupado.pares ?? null,
      excluyeCero: excluyeCero(ic95),
    });
  }
  return { filas, celdas };
}

export function variablesConsistentes(
  a5: ClimaDengueAnio['A5'],
): VariableAsociacion[] {
  return VARIABLES_ASOCIACION.filter((v) => a5[v]?.consistente);
}

export function resumenConsistencia(
  a3: ClimaDengueAnio['A3'],
  a5: ClimaDengueAnio['A5'],
  anios: number,
): string {
  const consistentes = variablesConsistentes(a5);
  if (consistentes.length === 0) {
    return `Ninguna de las ocho variables mantiene el mismo signo en casi todos los años con un intervalo del conjunto que excluya el cero.`;
  }
  const detalle = consistentes.map((v) => {
    const c = a5[v];
    const signo = a3.agrupado[v].r < 0 ? 'negativa' : 'positiva';
    const dominante = Math.max(c.anios_positivos, c.anios_negativos);
    return `${etiquetaVariable(v).toLowerCase()} (correlación ${signo} en ${dominante} de ${anios} años, ${formatoR(a3.agrupado[v].r)} en el conjunto)`;
  });
  return `${consistentes.length === 1 ? 'Una variable cumple' : `${consistentes.length === 2 ? 'Dos variables cumplen' : `${consistentes.length} variables cumplen`}`} la regla de consistencia fijada de antemano: ${detalle.join('; ')}.`;
}

// --- Ciclo medio (P4) -----------------------------------------------------------

export interface SerieCiclo {
  semanas: number[];
  /** Casos por semana (promedio de 4 semanas), media de los años. */
  casos: number[];
  clima: number[];
  r2Casos: number;
  r2Clima: number;
  desfase: number;
  correlacion: number;
  enElBorde: boolean;
}

export function variablesDelPais(ciclo: CicloPais): VariableClimaDengue[] {
  return VARIABLES_CLIMA.filter((v) => ciclo.variables[v]);
}

export function serieCiclo(
  ciclo: CicloPais,
  variable: VariableClimaDengue,
): SerieCiclo | null {
  const clima = ciclo.variables[variable];
  if (!clima) return null;
  // La climatología de los casos está en log1p del promedio de 4 semanas.
  const casos = ciclo.casos.climatologia.map((z) => Math.expm1(z));
  return {
    semanas: casos.map((_, i) => i + 1),
    casos,
    clima: clima.climatologia,
    r2Casos: ciclo.casos.r2_estacional,
    r2Clima: clima.r2_estacional,
    desfase: clima.desfase_mejor_semanas,
    correlacion: clima.correlacion_en_el_mejor,
    enElBorde: clima.en_el_borde === true,
  };
}

export function textoCiclo(
  pais: string,
  variable: VariableClimaDengue,
  serie: SerieCiclo,
): string {
  const nombreVariable = etiquetaVariable(variable).toLowerCase();
  const desfase =
    serie.desfase === 0
      ? 'sin retraso'
      : `cuando estos se retrasan ${serie.desfase} ${serie.desfase === 1 ? 'semana' : 'semanas'}`;
  const borde = serie.enElBorde
    ? ' El máximo está en el borde del rango explorado (16 semanas).'
    : '';
  return `${nombrePais(pais)}: el ciclo anual de ${nombreVariable} se parece más al de los casos ${desfase} (correlación ${formatoR(serie.correlacion)}). Tres armónicos anuales explican ${formatoNumero(serie.r2Clima)} de la variación semanal de ${nombreVariable} y ${formatoNumero(serie.r2Casos)} de la de los casos.${borde}`;
}

// --- El Salvador frente a los países (P2, P3, P6) ---------------------------

export interface FilaBosque {
  clave: string;
  nombre: string;
  r: number;
  /** null: la fuente no trae intervalo para esta medida (9 años). */
  ic95: [number, number] | null;
  posicion: number;
  esElSalvador: boolean;
}

/** Países ordenados de menor a mayor correlación con la señal regional. */
export function filasBosque(
  p2: ClimaDengueMultipais['P2'],
  nueveAnios: boolean,
): FilaBosque[] {
  const filas = Object.entries(p2.por_pais).map(([clave, dato]) => ({
    clave,
    nombre: nombrePais(clave),
    r: nueveAnios ? dato.r_con_senal_9_anios : dato.r_con_senal,
    ic95: nueveAnios ? null : dato.ic95,
    esElSalvador: clave === CLAVE_EL_SALVADOR,
  }));
  filas.sort((a, b) => a.r - b.r);
  return filas.map((fila, indice) => ({ ...fila, posicion: indice + 1 }));
}

export interface PosicionElSalvador {
  paises: number;
  r11: number;
  ic11: [number, number];
  posicion11: number;
  r9: number;
  posicion9: number;
}

export function posicionElSalvador(
  p2: ClimaDengueMultipais['P2'],
): PosicionElSalvador | null {
  const dato = p2.por_pais[CLAVE_EL_SALVADOR];
  if (!dato) return null;
  const f11 = filasBosque(p2, false).find((f) => f.esElSalvador);
  const f9 = filasBosque(p2, true).find((f) => f.esElSalvador);
  if (!f11 || !f9) return null;
  return {
    paises: Object.keys(p2.por_pais).length,
    r11: dato.r_con_senal,
    ic11: dato.ic95,
    posicion11: f11.posicion,
    r9: dato.r_con_senal_9_anios,
    posicion9: f9.posicion,
  };
}

function frasePosicion(posicion: number, paises: number): string {
  return posicion === 1
    ? `la menor de los ${paises} países`
    : `la posición ${posicion} de ${paises} de menor a mayor`;
}

export function textoPosicion(p: PosicionElSalvador): string {
  const principal = `Con los 11 años (2014 a 2024), la correlación de El Salvador con la señal regional es ${frasePosicion(p.posicion11, p.paises)}: ${formatoR(p.r11)}, con un intervalo del 95 % de ${formatoR(p.ic11[0])} a ${formatoR(p.ic11[1])}.`;
  const sensibilidad = `Sin 2020 y 2024 (9 años) es ${frasePosicion(p.posicion9, p.paises)}: ${formatoR(p.r9)}.`;
  return `${principal} ${sensibilidad}`;
}

export interface CeldaPais {
  pais: string;
  variable: VariableAsociacion;
  r: number | null;
  ic95: [number, number] | null;
  excluyeCero: boolean;
  consistente: boolean;
  anios: number;
  positivos: number;
  negativos: number;
}

/** Un país sin estimación (menos de 5 años evaluables) trae r = null. */
export function celdasPaisVariable(
  p3: Record<string, AsociacionPais>,
  paises: string[],
): CeldaPais[] {
  const celdas: CeldaPais[] = [];
  for (const pais of paises) {
    const dato = p3[pais];
    for (const variable of VARIABLES_ASOCIACION) {
      const v = dato?.estimacion ? dato.por_variable[variable] : undefined;
      celdas.push({
        pais,
        variable,
        r: v ? v.agrupado.r : null,
        ic95: v ? v.agrupado.ic95 : null,
        excluyeCero: v ? excluyeCero(v.agrupado.ic95) : false,
        consistente: v ? v.consistente : false,
        anios: dato?.anios_evaluables.length ?? 0,
        positivos: v ? v.anios_positivos : 0,
        negativos: v ? v.anios_negativos : 0,
      });
    }
  }
  return celdas;
}

/** El Salvador primero y los demás en orden alfabético. */
export function ordenFilasPaises(claves: string[]): string[] {
  const otros = ordenarPaises(claves.filter((c) => c !== CLAVE_EL_SALVADOR));
  return claves.includes(CLAVE_EL_SALVADOR)
    ? [CLAVE_EL_SALVADOR, ...otros]
    : otros;
}

// --- Filas de las tablas de datos completos ---------------------------------

export function filasPerfil(p1: Record<string, PerfilPaisClima>) {
  return ordenarPaises(Object.keys(p1)).map((clave) => {
    const p = p1[clave];
    const marcas: string[] = [];
    if (p.baja_incidencia) marcas.push('baja incidencia');
    if (p.pais_extenso) marcas.push('país extenso');
    if (p.variables_climaticas.length < 7) marcas.push('solo lluvia');
    return {
      pais: nombrePais(clave),
      casosSemanales: p.casos_semanales_medios,
      semanasConCero: p.fraccion_semanas_cero,
      r2: p.r2_estacional,
      semanaMaximo: p.semana_del_maximo,
      desviacion: p.desviacion_log_total_anual,
      marcas: marcas.join('; '),
    };
  });
}

export function filasTotalesAnuales(p1: Record<string, PerfilPaisClima>) {
  return ordenarPaises(Object.keys(p1)).map((clave) => ({
    pais: nombrePais(clave),
    ...p1[clave].total_anual,
  }));
}

export function filasDesfase(p4: Record<string, CicloPais>) {
  return ordenarPaises(Object.keys(p4)).map((clave) => {
    const variables = p4[clave].variables;
    const celda = (v: VariableClimaDengue) => {
      const c = variables[v];
      return c
        ? `${c.desfase_mejor_semanas}${c.en_el_borde ? '*' : ''} (${formatoR(c.correlacion_en_el_mejor)})`
        : 'sin dato';
    };
    return {
      pais: nombrePais(clave),
      r2Casos: p4[clave].casos.r2_estacional,
      lluviaMm: celda('precipitation_sum'),
      lluviaHoras: celda('precipitation_hours'),
      humedad: celda('humedad_relativa_media'),
      tempMedia: celda('temp_media'),
      puntoRocio: celda('punto_rocio'),
    };
  });
}

// La descripción del artefacto viene sin tildes: se usa este texto en español.
const DESCRIPCION_CORRIDA: Record<string, string> = {
  A: 'solo El Salvador, entrenando con los otros países',
  B: 'regional, 16 países con clima completo',
  C: 'regional con ONI, 16 países con clima completo',
};

export function filasCorridas(p5: ClimaDengueMultipais['P5']) {
  return Object.entries(p5).flatMap(([corrida, dato]) =>
    Object.entries(dato.anios).map(([anio, v]) => ({
      corrida: `${corrida}: ${DESCRIPCION_CORRIDA[corrida] ?? corrida}`,
      anio: Number(anio),
      soporte: v.soporte_alto,
      f1Modelo: v.f1_modelo,
      recallModelo: v.recall_alto_modelo,
      f1Climatologia: v.f1_climatologia,
      semillas: `${v.semillas_que_superan} de ${v.semillas}`,
    })),
  );
}

// --- Tablas completas de los datos por año ----------------------------------

/** Una fila por año y una final con todos los años: "r [intervalo]" por variable. */
export function filasTablaAsociacion(a3: ClimaDengueAnio['A3']) {
  const { filas, celdas } = celdasAsociacionAnio(a3);
  return filas.map((fila) => {
    const resultado: Record<string, string | number | null> = {
      fila,
      pares: null,
    };
    for (const celda of celdas.filter((c) => c.fila === fila)) {
      resultado.pares = celda.pares;
      resultado[celda.variable] =
        `${formatoR(celda.r)} ${formatoIntervalo(celda.ic95)}${celda.excluyeCero ? ' *' : ''}`;
    }
    return resultado;
  });
}

export function filasConsistencia(
  a5: ClimaDengueAnio['A5'],
  a3: ClimaDengueAnio['A3'],
) {
  return VARIABLES_ASOCIACION.map((variable) => {
    const c = a5[variable];
    const agrupado = a3.agrupado[variable];
    return {
      variable: etiquetaVariable(variable, true),
      positivos: c.anios_positivos,
      negativos: c.anios_negativos,
      conIntervaloSinCero: c.anios_con_ic_sin_cero,
      rango: `${formatoR(c.r_minimo)} a ${formatoR(c.r_maximo)}`,
      agrupado: `${formatoR(agrupado.r)} ${formatoIntervalo(agrupado.ic95)}`,
      etiqueta: c.consistente ? 'consistente' : 'variable según el año',
    };
  });
}

export function filasPerfilAnio(a4: ClimaDengueAnio['A4']) {
  return Object.keys(a4.por_anio)
    .map(Number)
    .sort((a, b) => a - b)
    .map((anio) => {
      const p = a4.por_anio[anio];
      return {
        anio,
        casos: p.casos_totales,
        semanaPico: p.semana_del_pico,
        valorPico: p.valor_del_pico,
        oni: p.oni_medio,
        lluvia: p.precipitation_sum.anomalia_media,
        horasLluvia: p.precipitation_hours.anomalia_media,
        tempMedia: p.temp_media.anomalia_media,
        humedad: p.humedad_relativa_media.anomalia_media,
      };
    });
}

export function filasCicloAnio(a2: ClimaDengueAnio['A2']) {
  return VARIABLES_CLIMA.filter((v) => a2.por_variable[v]).map((variable) => {
    const c = a2.por_variable[variable];
    return {
      variable: etiquetaVariable(variable, true),
      r2: c.r2_estacional,
      desfase: c.desfase_mejor_semanas,
      correlacion: c.correlacion_en_el_mejor,
    };
  });
}

// --- Tablas y textos de la comparación entre países ---------------------------

/**
 * Posición de El Salvador entre los países de Centroamérica, con las dos
 * medidas. Devuelve '' si el subconjunto no trae a El Salvador.
 */
export function resumenCentroamerica(p2: ClimaDengueMultipais['P2']): string {
  const mide = (valores: Record<string, number>) => {
    const ordenados = Object.entries(valores).sort((a, b) => a[1] - b[1]);
    const indice = ordenados.findIndex(
      ([clave]) => clave === CLAVE_EL_SALVADOR,
    );
    return indice < 0
      ? null
      : {
          posicion: indice + 1,
          total: ordenados.length,
          r: valores[CLAVE_EL_SALVADOR],
        };
  };
  const once = mide(p2.centroamerica);
  const nueve = mide(p2.centroamerica_9_anios);
  if (!once || !nueve) return '';
  if (once.posicion === 1 && nueve.posicion === 1) {
    return `Entre los ${once.total} países de Centroamérica, El Salvador tiene la menor correlación con la media de los otros cinco en las dos medidas: ${formatoR(once.r)} con los 11 años y ${formatoR(nueve.r)} con 9.`;
  }
  return `Entre los ${once.total} países de Centroamérica, El Salvador queda en la posición ${once.posicion} de menor a mayor con los 11 años (${formatoR(once.r)}) y en la ${nueve.posicion} con 9 (${formatoR(nueve.r)}).`;
}

export function textoEstabilidad(p2: ClimaDengueMultipais['P2']): string {
  const e = p2.estabilidad_el_salvador;
  const extremo = (porAnio: Record<string, number>, menor: boolean) => {
    const pares = Object.entries(porAnio);
    return pares.reduce((a, b) => (b[1] < a[1] === menor ? b : a));
  };
  const [anioMin] = extremo(e.sin_cada_anio, true);
  const [anioMax] = extremo(e.sin_cada_anio, false);
  return `Al quitar un año de los 11, la correlación de El Salvador con la señal regional va de ${formatoR(e.minimo)} (sin ${anioMin}) a ${formatoR(e.maximo)} (sin ${anioMax}). Al quitar un país de la señal se mantiene entre ${formatoR(Math.min(...Object.values(e.sin_cada_pais)))} y ${formatoR(Math.max(...Object.values(e.sin_cada_pais)))}.`;
}

const ETIQUETAS_POSICION: Record<string, string> = {
  r_con_senal: 'Correlación con la señal regional',
  r_con_otros: 'Correlación con la señal de los otros países',
  desviacion_log_total_anual: 'Variación entre años del total anual',
  r2_estacional_casos:
    'Parte de la variación semanal que explica el ciclo anual',
  r_agrupado_precipitation_sum: 'Correlación semanal con la lluvia (mm)',
  r_agrupado_oni: 'Correlación semanal con el ONI',
};

export function filasPosiciones(p6: ClimaDengueMultipais['P6']) {
  return Object.entries(p6).map(([clave, dato]) => ({
    medida: ETIQUETAS_POSICION[clave] ?? clave,
    valor: dato.valor,
    posicion: dato.posicion_de_menor_a_mayor,
    paises: dato.paises,
  }));
}

export function filasEstabilidad(p2: ClimaDengueMultipais['P2']) {
  const e = p2.estabilidad_el_salvador;
  return [
    ...Object.entries(e.sin_cada_anio).map(([clave, r]) => ({
      quitado: `Año ${clave}`,
      r,
    })),
    ...ordenarPaises(Object.keys(e.sin_cada_pais)).map((clave) => ({
      quitado: nombrePais(clave),
      r: e.sin_cada_pais[clave],
    })),
  ];
}

/** Anomalía anual del total de casos (z) de cada país y la señal regional. */
export function filasAnomaliaAnual(p2: ClimaDengueMultipais['P2']) {
  const filas = ordenFilasPaises(Object.keys(p2.por_pais)).map((clave) => ({
    pais: nombrePais(clave),
    ...p2.por_pais[clave].anomalia_anual,
  }));
  return [{ pais: 'Señal regional (media)', ...p2.senal_regional }, ...filas];
}

export function aniosAnomalia(p2: ClimaDengueMultipais['P2']): string[] {
  return Object.keys(p2.senal_regional).sort();
}

export function filasTablaPaises(p2: ClimaDengueMultipais['P2']) {
  return filasBosque(p2, false)
    .map((fila) => ({
      pais: fila.nombre,
      r11: fila.r,
      ic11: formatoIntervalo(fila.ic95!),
      posicion11: fila.posicion,
      r9: p2.por_pais[fila.clave].r_con_senal_9_anios,
      posicion9: p2.posicion_r_con_senal_9_anios[fila.clave],
      otros11: p2.por_pais[fila.clave].r_con_otros,
      otros9: p2.por_pais[fila.clave].r_con_otros_9_anios,
    }))
    .sort((a, b) => a.pais.localeCompare(b.pais, 'es'));
}

// --- Asociación país por variable (P3) ---------------------------------------

/** Frases del resumen, calculadas de las celdas; no dependen de cifras fijas. */
export function resumenPaisVariable(celdas: CeldaPais[]): string[] {
  const estimadas = celdas.filter((c) => c.r !== null);
  if (estimadas.length === 0) return [];
  const conIntervalo = estimadas.filter((c) => c.excluyeCero);
  const consistentes = estimadas.filter((c) => c.consistente);
  const frases: string[] = [];

  const detalle = consistentes.map(
    (c) =>
      `${etiquetaVariable(c.variable).toLowerCase()} en ${nombrePais(c.pais)} (${c.positivos} ${c.positivos === 1 ? 'año positivo' : 'años positivos'}, ${c.negativos} ${c.negativos === 1 ? 'negativo' : 'negativos'})`,
  );
  frases.push(
    `De ${estimadas.length} celdas país por variable con estimación, ${conIntervalo.length} tienen el intervalo del 95 % fuera del cero y ${consistentes.length} cumplen la regla de consistencia${detalle.length ? `: ${detalle.join('; ')}` : ''}.`,
  );

  const lluvia = (signo: number) =>
    conIntervalo
      .filter((c) => c.variable === 'precipitation_sum' && c.r! * signo > 0)
      .map((c) => nombrePais(c.pais));
  const negativos = lluvia(-1);
  const positivos = lluvia(1);
  if (negativos.length || positivos.length) {
    const partes: string[] = [];
    if (negativos.length) partes.push(`negativo en ${listaEnTexto(negativos)}`);
    if (positivos.length) partes.push(`positivo en ${listaEnTexto(positivos)}`);
    frases.push(
      `En la lluvia (mm), el intervalo queda fuera del cero y ${partes.join(' y ')}.`,
    );
  }

  const esperadas = Math.round(estimadas.length * 0.05);
  frases.push(
    `Con ${estimadas.length} celdas y un nivel del 95 % se esperarían unas ${esperadas} con el intervalo fuera del cero sin asociación alguna; las celdas no son independientes entre sí, porque las variables y los países están correlacionados.`,
  );

  const anios = estimadas.map((c) => c.anios);
  frases.push(
    `Cada país aporta entre ${Math.min(...anios)} y ${Math.max(...anios)} años evaluables.`,
  );
  return frases;
}

/** Todas las correlaciones por país, variable y año (y el conjunto de cada país). */
export function filasPaisVariableAnio(p3: Record<string, AsociacionPais>) {
  return ordenFilasPaises(Object.keys(p3)).flatMap((pais) => {
    const dato = p3[pais];
    if (!dato.estimacion) return [];
    return VARIABLES_ASOCIACION.flatMap((variable) => {
      const v = dato.por_variable[variable];
      if (!v) return [];
      const filaConjunto = {
        pais: nombrePais(pais),
        variable: etiquetaVariable(variable),
        anio: ETIQUETA_TODOS_LOS_ANIOS,
        r: v.agrupado.r,
        ic95: formatoIntervalo(v.agrupado.ic95),
        etiqueta: v.consistente ? 'consistente' : 'variable según el año',
      };
      const porAnio = Object.keys(v.por_anio)
        .sort()
        .map((anio) => ({
          pais: nombrePais(pais),
          variable: etiquetaVariable(variable),
          anio,
          r: v.por_anio[anio].r,
          ic95: formatoIntervalo(v.por_anio[anio].ic95),
          etiqueta: '',
        }));
      return [filaConjunto, ...porAnio];
    });
  });
}

/** El Salvador con la serie multipaís y con la de la base de datos, lado a lado. */
export function filasReferenciaElSalvador(
  p3: Record<string, AsociacionPais>,
  referencia: NonNullable<
    ClimaDengueMultipais['referencia_el_salvador_base_de_datos']
  >,
) {
  const multipais = p3[CLAVE_EL_SALVADOR];
  return VARIABLES_ASOCIACION.flatMap((variable) => {
    const m = multipais?.por_variable[variable];
    const base = referencia.agrupado[variable];
    const consistenciaBase = referencia.consistencia[variable];
    if (!m || !base || !consistenciaBase) return [];
    return [
      {
        variable: etiquetaVariable(variable, true),
        multipais: `${formatoR(m.agrupado.r)} ${formatoIntervalo(m.agrupado.ic95)}`,
        etiquetaMultipais: `${m.anios_positivos} positivos, ${m.anios_negativos} negativos; ${m.consistente ? 'consistente' : 'variable según el año'}`,
        base: `${formatoR(base.r)} ${formatoIntervalo(base.ic95)}`,
        etiquetaBase: `${consistenciaBase.anios_positivos} positivos, ${consistenciaBase.anios_negativos} negativos; ${consistenciaBase.consistente ? 'consistente' : 'variable según el año'}`,
      },
    ];
  });
}
