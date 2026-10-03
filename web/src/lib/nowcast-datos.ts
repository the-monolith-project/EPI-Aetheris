// Datos y textos de las gráficas de la predicción de dengue: preparan lo que
// devuelven GET /api/nowcast-dengue y GET /api/nowcast-dengue/retrospectivo
// para las opciones de ECharts (nowcast-opciones.ts), para la tabla
// alternativa y para el resumen que se lee sobre cada gráfica. No toca el DOM
// ni importa ECharts, así que se prueba con node --test.
import type {
  NowcastDengue,
  NowcastDengueRetrospectivo,
  OrigenRetro,
  PuntoBacktestNowcast,
  ValoresHorizonteRetro,
} from './tipos-analisis.ts';

export const SEMANA_MS = 7 * 86_400_000;

export const fmtNum = new Intl.NumberFormat('es-SV', {
  maximumFractionDigits: 0,
});
export const fmtFecha = new Intl.DateTimeFormat('es-SV', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});
export const fmtFechaCorta = new Intl.DateTimeFormat('es-SV', {
  day: 'numeric',
  month: 'short',
});

/** Fecha ISO (AAAA-MM-DD) a medianoche local, como las demás gráficas. */
export function fecha(iso: string): Date {
  return new Date(`${iso}T00:00:00`);
}

export function marcaTiempo(iso: string): number {
  return fecha(iso).getTime();
}

export function sumarSemanas(iso: string, n: number): string {
  const d = new Date(fecha(iso).getTime() + n * SEMANA_MS);
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mm}-${dd}`;
}

export type Rango = [number, number];

/** Dónde cae un valor observado respecto a los rangos de la predicción. */
export type Cobertura = 'rango 50 %' | 'rango 95 %' | 'fuera';

export function coberturaDe(valor: number, b50: Rango, b95: Rango): Cobertura {
  if (valor >= b50[0] && valor <= b50[1]) return 'rango 50 %';
  if (valor >= b95[0] && valor <= b95[1]) return 'rango 95 %';
  return 'fuera';
}

// --- abanico hacia adelante -------------------------------------------------

export interface SemanaObservada {
  t: number;
  fecha: string;
  /** null: semana que la fuente no publicó. */
  casos: number | null;
}

export interface SemanaPredicha {
  h: number;
  t: number;
  fecha: string;
  semana: number;
  mediana: number;
  b50: Rango;
  b95: Rango;
}

export interface AnclaAbanico {
  t: number;
  fecha: string;
  anio: number;
  semana: number;
  casos: number;
}

export interface DatosAbanico {
  observado: SemanaObservada[];
  ancla: AnclaAbanico;
  prediccion: SemanaPredicha[];
}

/** null cuando la respuesta no trae lo necesario para dibujar el abanico. */
export function prepararAbanico(datos: NowcastDengue): DatosAbanico | null {
  if (
    !datos.ancla ||
    !datos.observado?.length ||
    !datos.estimacion?.length ||
    !datos.desempeno
  ) {
    return null;
  }
  const ancla: AnclaAbanico = {
    t: marcaTiempo(datos.ancla.fecha),
    fecha: datos.ancla.fecha,
    anio: datos.ancla.anio,
    semana: datos.ancla.semana,
    casos: datos.ancla.casos,
  };
  return {
    ancla,
    observado: datos.observado.map((p) => ({
      t: marcaTiempo(p.fecha),
      fecha: p.fecha,
      casos: p.casos,
    })),
    prediccion: datos.estimacion.map((e) => ({
      h: e.h,
      t: marcaTiempo(e.fecha),
      fecha: e.fecha,
      semana: e.semana,
      mediana: e.mediana,
      b50: e.banda_50,
      b95: e.banda_95,
    })),
  };
}

/** Últimas `semanas` semanas observadas (null: todas) con la misma predicción. */
export function recortarAbanico(
  datos: DatosAbanico,
  semanas: number | null,
): DatosAbanico {
  if (semanas === null || semanas >= datos.observado.length) return datos;
  return { ...datos, observado: datos.observado.slice(-semanas) };
}

/** Frase que acompaña a la gráfica: cifras de la predicción y su incertidumbre. */
export function resumenAbanico(datos: DatosAbanico): string {
  const { ancla, prediccion } = datos;
  const primera = prediccion[0];
  const ultima = prediccion[prediccion.length - 1];
  const desde = `Desde la semana del ${fmtFecha.format(fecha(ancla.fecha))} (${fmtNum.format(ancla.casos)} casos)`;
  const medianas = `la mediana de la predicción es ${fmtNum.format(primera.mediana)} casos una semana después y ${fmtNum.format(ultima.mediana)} casos ${ultima.h} semanas después`;
  const rango = `El rango del 95 % a ${ultima.h} semanas va de ${fmtNum.format(ultima.b95[0])} a ${fmtNum.format(ultima.b95[1])} casos; los rangos se ensanchan con el horizonte.`;
  return `${desde}, ${medianas}. ${rango}`;
}

export function etiquetaAbanico(datos: DatosAbanico): string {
  const horizonte = datos.prediccion[datos.prediccion.length - 1].h;
  return `Casos de dengue por semana en el país hasta el ${fmtFecha.format(fecha(datos.ancla.fecha))} y predicción de 1 a ${horizonte} semanas con rangos del 50 % y del 95 %. ${resumenAbanico(datos)} Los valores están en la tabla siguiente.`;
}

export interface FilaAbanico {
  semana: string;
  tipo: 'Predicción' | 'Publicado';
  casos: string;
  rango50: string;
  rango95: string;
}

const rangoTexto = (r: Rango) =>
  `${fmtNum.format(r[0])}–${fmtNum.format(r[1])}`;

/** Predicción de la semana 1 a la 8 y, debajo, lo publicado de la más reciente a la más antigua. */
export function filasAbanico(datos: DatosAbanico): FilaAbanico[] {
  const prediccion: FilaAbanico[] = datos.prediccion.map((p) => ({
    semana: `+${p.h} · ${fmtFecha.format(fecha(p.fecha))}`,
    tipo: 'Predicción',
    casos: fmtNum.format(p.mediana),
    rango50: rangoTexto(p.b50),
    rango95: rangoTexto(p.b95),
  }));
  const publicado: FilaAbanico[] = datos.observado
    .slice()
    .reverse()
    .map((o) => ({
      semana: fmtFecha.format(fecha(o.fecha)),
      tipo: 'Publicado',
      casos: o.casos === null ? 'sin publicar' : fmtNum.format(o.casos),
      rango50: '—',
      rango95: '—',
    }));
  return [...prediccion, ...publicado];
}

// --- validación a cuatro semanas -------------------------------------------

export interface SemanaValidacion {
  t: number;
  fecha: string;
  anio: number;
  observado: number;
  mediana: number;
  b50: Rango;
  b95: Rango;
  cobertura: Cobertura;
}

export interface DatosValidacion {
  semanas: SemanaValidacion[];
  en50: number;
  en95: number;
  fuera: number;
}

export function prepararValidacion(
  puntos: PuntoBacktestNowcast[],
): DatosValidacion | null {
  if (!puntos.length) return null;
  const semanas = puntos.map((p) => ({
    t: marcaTiempo(p.fecha),
    fecha: p.fecha,
    anio: p.anio,
    observado: p.observado,
    mediana: p.mediana,
    b50: p.banda_50,
    b95: p.banda_95,
    cobertura: coberturaDe(p.observado, p.banda_50, p.banda_95),
  }));
  const en50 = semanas.filter((s) => s.cobertura === 'rango 50 %').length;
  const fuera = semanas.filter((s) => s.cobertura === 'fuera').length;
  return { semanas, en50, en95: semanas.length - fuera, fuera };
}

export function resumenValidacion(datos: DatosValidacion): string {
  const n = datos.semanas.length;
  return `De ${n} semanas comparadas, ${datos.en50} quedaron dentro del rango del 50 % y ${datos.en95} dentro del 95 %; ${datos.fuera} cayeron fuera del rango del 95 %.`;
}

export function etiquetaValidacion(
  datos: DatosValidacion,
  anios: string,
): string {
  return `Casos observados frente a la predicción a cuatro semanas en ${anios}. ${resumenValidacion(datos)} Los valores están en la tabla siguiente.`;
}

export interface FilaValidacion {
  semana: string;
  observado: string;
  mediana: string;
  rango50: string;
  rango95: string;
  dentro: string;
}

export function filasValidacion(datos: DatosValidacion): FilaValidacion[] {
  return datos.semanas
    .slice()
    .reverse()
    .map((s) => ({
      semana: fmtFecha.format(fecha(s.fecha)),
      observado: fmtNum.format(s.observado),
      mediana: fmtNum.format(s.mediana),
      rango50: rangoTexto(s.b50),
      rango95: rangoTexto(s.b95),
      dentro: s.cobertura,
    }));
}

/**
 * Parejas [t, valor] con un hueco (valor null) donde faltan semanas, para que
 * la línea no una tramos separados (2020 excluido, semanas sin predicción).
 */
export function conHuecos<T extends { t: number }>(
  filas: T[],
  valor: (fila: T) => number | null,
): [number, number | null][] {
  const salida: [number, number | null][] = [];
  filas.forEach((fila, i) => {
    if (i > 0 && fila.t - filas[i - 1].t > 1.5 * SEMANA_MS) {
      salida.push([filas[i - 1].t + SEMANA_MS, null]);
    }
    salida.push([fila.t, valor(fila)]);
  });
  return salida;
}

// --- contraste con lo observado --------------------------------------------

export const NOMBRE_REFERENCIA: Record<string, string> = {
  persistencia_rw: 'repetir el último valor',
  persistencia_suavizada: 'repetir el último valor',
  persistencia_estacional:
    'repetir el último valor ajustado a la época del año',
  climatologia_estacional: 'la misma semana de años anteriores',
};

export interface Horizonte {
  h: number;
  fecha: string;
  mediana: number;
  b50: Rango;
  b95: Rango;
  observado: number | null;
  /** la semana está en la serie pero la fuente no la publicó */
  sinPublicar: boolean;
  wisModelo: number | null;
  wisReferencia: number | null;
}

export interface Origen {
  idx: number;
  fecha: string;
  anio: number;
  semana: number;
  casos: number | null;
  /** null: sin predicción desde esta semana. */
  horizontes: (Horizonte | null)[] | null;
  motivo?: OrigenRetro['motivo'];
  esAncla: boolean;
}

export interface ModeloContraste {
  origenes: Origen[];
  porAnio: Map<number, Origen[]>;
  observado: { fecha: string; casos: number | null }[];
  retro: NowcastDengueRetrospectivo;
}

export function construirModelo(
  retro: NowcastDengueRetrospectivo,
  principal: NowcastDengue,
): ModeloContraste | null {
  if (!retro.observado?.length || !retro.origenes || !retro.horizontes) {
    return null;
  }
  const observado = retro.observado.map(([f, c]) => ({ fecha: f, casos: c }));
  const origenes: Origen[] = retro.origenes.map((o, idx) => ({
    idx,
    fecha: o.fecha,
    anio: o.anio,
    semana: o.semana,
    casos: observado[idx].casos,
    motivo: o.motivo,
    esAncla: false,
    horizontes: o.h
      ? o.h.map((v: ValoresHorizonteRetro | null, k) => {
          if (!v) return null;
          const obs = observado[idx + k + 1];
          return {
            h: k + 1,
            fecha: obs?.fecha ?? sumarSemanas(o.fecha, k + 1),
            mediana: v[0],
            b50: [v[1], v[2]] as Rango,
            b95: [v[3], v[4]] as Rango,
            observado: obs ? obs.casos : null,
            sinPublicar: obs !== undefined && obs.casos === null,
            wisModelo: v[5],
            wisReferencia: v[6],
          };
        })
      : null,
  }));

  // la última semana observada usa la estimación publicada
  const ancla = principal.ancla;
  if (ancla && principal.estimacion?.length) {
    origenes.push({
      idx: origenes.length,
      fecha: ancla.fecha,
      anio: ancla.anio,
      semana: ancla.semana,
      casos: ancla.casos,
      esAncla: true,
      horizontes: principal.estimacion.map((e) => ({
        h: e.h,
        fecha: e.fecha,
        mediana: e.mediana,
        b50: e.banda_50,
        b95: e.banda_95,
        observado: null,
        sinPublicar: false,
        wisModelo: null,
        wisReferencia: null,
      })),
    });
  }

  const porAnio = new Map<number, Origen[]>();
  for (const o of origenes) {
    const arr = porAnio.get(o.anio) ?? [];
    arr.push(o);
    porAnio.set(o.anio, arr);
  }
  return { origenes, porAnio, observado, retro };
}

export function dentroDe(h: Horizonte): string {
  if (h.observado === null)
    return h.sinPublicar ? 'semana sin publicar' : 'sin dato todavía';
  return coberturaDe(h.observado, h.b50, h.b95);
}

function enTablero(retro: NowcastDengueRetrospectivo, iso: string): boolean {
  return Boolean(retro.tablero && iso >= retro.tablero.inicio.fecha);
}

export function nombreReferencia(
  retro: NowcastDengueRetrospectivo,
  origen: Origen,
): string {
  if (retro.tablero && enTablero(retro, origen.fecha)) {
    return (
      NOMBRE_REFERENCIA[retro.tablero.referencia] ?? retro.tablero.referencia
    );
  }
  const nombres = new Set(Object.values(retro.referencia_por_horizonte ?? {}));
  if (nombres.size === 1) {
    const [n] = nombres;
    return NOMBRE_REFERENCIA[n] ?? n;
  }
  return 'la referencia más fuerte en cada horizonte';
}

/** Frase de lo que se ve al partir de `origen`: cuántas semanas cayeron dentro de los rangos. */
export function textoResumenOrigen(
  modelo: ModeloContraste,
  origen: Origen,
): string {
  const casos =
    origen.casos === null
      ? 'sin dato publicado'
      : `${fmtNum.format(origen.casos)} casos`;
  const cabeza = `Semana ${origen.semana} de ${origen.anio} (${fmtFecha.format(fecha(origen.fecha))}, ${casos}).`;

  if (!origen.horizontes && origen.motivo === 'hueco_en_serie') {
    return `${cabeza} Sin predicción desde esta semana: el modelo usa las ocho semanas anteriores y a esa ventana le falta una semana que la fuente no publicó.`;
  }
  if (!origen.horizontes) {
    const primera = modelo.retro.primera_semana_con_prediccion;
    return (
      `${cabeza} Sin predicción desde esta semana: el modelo necesita unos tres años de datos para entrenarse.` +
      (primera
        ? ` La primera semana con predicción es la ${primera.semana} de ${primera.anio}.`
        : '')
    );
  }
  if (origen.esAncla) {
    return `${cabeza} Es la última semana publicada de la serie: todavía no hay valores observados para contrastar.`;
  }

  const conDato = origen.horizontes.filter(
    (h): h is Horizonte => h !== null && h.observado !== null,
  );
  const en50 = conDato.filter((h) => dentroDe(h) === 'rango 50 %').length;
  const en95 = conDato.filter((h) => dentroDe(h) !== 'fuera').length;
  const pares = conDato.filter(
    (h) => h.wisModelo !== null && h.wisReferencia !== null,
  );
  let error = '';
  if (pares.length) {
    const wm = pares.reduce((s, h) => s + (h.wisModelo ?? 0), 0) / pares.length;
    const wr =
      pares.reduce((s, h) => s + (h.wisReferencia ?? 0), 0) / pares.length;
    error = ` Error medio del modelo: ${fmtNum.format(wm)}, frente a ${fmtNum.format(wr)} de ${nombreReferencia(modelo.retro, origen)}.`;
  }
  return (
    `${cabeza} De ${conDato.length} semanas observadas después, ` +
    `${en50} quedaron dentro del rango del 50 % y ${en95} dentro del 95 %.${error}`
  );
}

/** Notas del año elegido: método, temporada de validación y desempeño a cuatro semanas. */
export function textoNotaAnio(modelo: ModeloContraste, anio: number): string {
  const retro = modelo.retro;
  const partes: string[] = [];

  const tablero = retro.tablero?.anios.includes(anio)
    ? retro.tablero
    : undefined;
  if (anio === retro.anio_excluido && retro.aviso_anio_excluido) {
    partes.push(retro.aviso_anio_excluido);
  } else if (tablero) {
    const { inicio } = tablero.prueba;
    partes.push(
      `Desde ${tablero.inicio.anio} la serie es la del tablero de MINSAL y la predicción combina el modelo con una tendencia amortiguada. ` +
        `${tablero.anios.join(' y ')} sirvieron para elegir ese método; la prueba con semanas nuevas empieza en la semana ${inicio.semana} de ${inicio.anio}.`,
    );
  } else if (retro.anios_prueba?.includes(anio)) {
    partes.push(`${anio} es una de las temporadas de la validación publicada.`);
  }

  const r4 = retro.resumen_por_anio?.[String(anio)]?.['4'];
  const referencia = tablero
    ? tablero.referencia
    : (retro.referencia_por_horizonte?.['4'] ?? '');
  if (r4 && r4.skill !== null) {
    const pct = Math.round(Math.abs(r4.skill) * 100);
    const comparacion = r4.skill >= 0 ? `${pct} % menos` : `${pct} % más`;
    partes.push(
      `A 4 semanas, en ${anio} el modelo tuvo ${comparacion} error que ${NOMBRE_REFERENCIA[referencia] ?? 'la referencia'}; ` +
        `lo observado quedó dentro del rango del 50 % en el ${Math.round(r4.cobertura_50 * 100)} % de las semanas y dentro del 95 % en el ${Math.round(r4.cobertura_95 * 100)} %.`,
    );
  }
  return partes.join(' ');
}
