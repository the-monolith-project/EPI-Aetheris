import test from 'node:test';
import assert from 'node:assert/strict';
import {
  celdasAsociacionAnio,
  celdasPaisVariable,
  excluyeCero,
  filasAporte,
  filasBosque,
  formatoIntervalo,
  formatoMiles,
  formatoNumero,
  formatoR,
  listaEnTexto,
  nombrePais,
  ordenFilasPaises,
  posicionElSalvador,
  resumenAporte,
  resumenConsistencia,
  serieCiclo,
  textoPosicion,
  variablesConsistentes,
} from '../../src/lib/clima-dengue.ts';
import type {
  AporteHorizonteClima,
  AsociacionPais,
  ClimaDengueAnio,
  ClimaDengueMultipais,
  CicloPais,
} from '../../src/lib/tipos-analisis.ts';

test('los números salen con coma decimal y signo menos tipográfico', () => {
  assert.equal(formatoNumero(0.2804, 3), '0,280');
  assert.equal(formatoR(0.28), '+0,28');
  assert.equal(formatoR(-0.158), '−0,16');
  assert.equal(formatoIntervalo([-0.16, 0.8]), '[−0,16; +0,80]');
  // Un valor que redondea a cero no lleva signo menos.
  assert.equal(formatoNumero(-0.0004, 2), '0,00');
  assert.equal(formatoMiles(53196), '53.196');
  assert.equal(formatoMiles(999), '999');
});

test('la lista en texto junta con comas y una y final', () => {
  assert.equal(listaEnTexto([]), '');
  assert.equal(listaEnTexto([2019]), '2019');
  assert.equal(listaEnTexto([2019, 2023]), '2019 y 2023');
  assert.equal(listaEnTexto([2019, 2023, 2024]), '2019, 2023 y 2024');
});

test('el intervalo excluye el cero solo si queda de un lado', () => {
  assert.equal(excluyeCero([0.02, 0.2]), true);
  assert.equal(excluyeCero([-0.3, -0.1]), true);
  assert.equal(excluyeCero([-0.1, 0.2]), false);
  assert.equal(excluyeCero([0, 0.2]), false);
});

test('los países usan su nombre en español y El Salvador va primero', () => {
  assert.equal(nombrePais('BRAZIL'), 'Brasil');
  assert.equal(nombrePais('UNITED STATES OF AMERICA'), 'Estados Unidos');
  assert.equal(nombrePais('PERU'), 'Peru');
  assert.deepEqual(ordenFilasPaises(['MEXICO', 'EL SALVADOR', 'BOLIVIA']), [
    'EL SALVADOR',
    'BOLIVIA',
    'MEXICO',
  ]);
});

const APORTE_4: AporteHorizonteClima = {
  skill_I0: { '2019': 0.1, '2021': 0.2 },
  clima: {
    por_anio: { '2021': 0.075, '2019': -0.04, '2022': 0.314 },
    anios_a_favor: 2,
    anios: 3,
  },
  oni: {
    por_anio: { '2019': 0.01, '2021': 0.02, '2022': -0.01 },
    anios_a_favor: 2,
    anios: 3,
  },
  clima_y_oni: {
    por_anio: { '2019': 0, '2021': 0.1, '2022': 0.2 },
    anios_a_favor: 2,
    anios: 3,
  },
  anio: {
    por_anio: { '2019': 0, '2021': 0, '2022': 0 },
    anios_a_favor: 0,
    anios: 3,
  },
};

test('las filas de aporte salen ordenadas por año', () => {
  const filas = filasAporte({ '4': APORTE_4 }, 4);
  assert.deepEqual(
    filas.map((f) => f.anio),
    [2019, 2021, 2022],
  );
  assert.equal(filas[2].clima, 0.314);
  assert.deepEqual(filasAporte({ '4': APORTE_4 }, 9), []);
});

test('el resumen del aporte nombra los años que ayudó y los que empeoró', () => {
  const filas = filasAporte({ '4': APORTE_4 }, 4);
  assert.equal(
    resumenAporte(filas, 4),
    'A 4 semanas, el clima ayudó al pronóstico en 2 de 3 años (2021 y 2022) y lo empeoró en 1 (2019).',
  );
  assert.equal(resumenAporte([], 4), '');
});

const correlacion = (r: number): { r: number; ic95: [number, number] } => ({
  r,
  ic95: [r - 0.1, r + 0.1],
});

function asociacionAnio(r: number) {
  return {
    pares: 50,
    temp_media: correlacion(r),
    temp_max: correlacion(r),
    temp_min: correlacion(r),
    precipitation_sum: correlacion(-r),
    precipitation_hours: correlacion(-r),
    humedad_relativa_media: correlacion(r),
    punto_rocio: correlacion(r),
    oni: correlacion(0.01),
  };
}

test('la matriz por año agrega la fila de todos los años y marca el cero', () => {
  const a3: ClimaDengueAnio['A3'] = {
    por_anio: { '2022': asociacionAnio(0.3), '2019': asociacionAnio(0.05) },
    agrupado: asociacionAnio(0.2),
  };
  const { filas, celdas } = celdasAsociacionAnio(a3);
  assert.deepEqual(filas, ['2019', '2022', 'Todos los años']);
  assert.equal(celdas.length, 3 * 8);
  const lluvia2022 = celdas.find(
    (c) => c.fila === '2022' && c.variable === 'precipitation_sum',
  );
  assert.equal(lluvia2022?.r, -0.3);
  assert.equal(lluvia2022?.excluyeCero, true);
  const temp2019 = celdas.find(
    (c) => c.fila === '2019' && c.variable === 'temp_media',
  );
  assert.equal(temp2019?.excluyeCero, false);
});

test('el resumen de consistencia describe las variables que cumplen la regla', () => {
  const sin = {
    anios_positivos: 4,
    anios_negativos: 5,
    anios_con_ic_sin_cero: 0,
    r_minimo: -0.3,
    r_maximo: 0.3,
    consistente: false,
  };
  const a5 = {
    temp_media: sin,
    temp_max: sin,
    temp_min: sin,
    precipitation_sum: {
      ...sin,
      anios_positivos: 1,
      anios_negativos: 8,
      consistente: true,
    },
    precipitation_hours: {
      ...sin,
      anios_positivos: 1,
      anios_negativos: 8,
      consistente: true,
    },
    humedad_relativa_media: sin,
    punto_rocio: sin,
    oni: sin,
  } as ClimaDengueAnio['A5'];
  const a3: ClimaDengueAnio['A3'] = {
    por_anio: { '2019': asociacionAnio(0.05) },
    agrupado: asociacionAnio(0.17),
  };
  assert.deepEqual(variablesConsistentes(a5), [
    'precipitation_sum',
    'precipitation_hours',
  ]);
  const texto = resumenConsistencia(a3, a5, 9);
  assert.match(texto, /^Dos variables cumplen la regla/);
  assert.match(
    texto,
    /lluvia \(mm\) \(correlación negativa en 8 de 9 años, −0,17 en el conjunto\)/,
  );
  const ninguna = resumenConsistencia(
    a3,
    { ...a5, precipitation_sum: sin, precipitation_hours: sin },
    9,
  );
  assert.match(ninguna, /^Ninguna de las ocho variables/);
});

const CICLO: CicloPais = {
  casos: {
    r2_estacional: 0.17,
    climatologia: [Math.log1p(100), Math.log1p(300)],
  },
  variables: {
    precipitation_sum: {
      r2_estacional: 0.53,
      desfase_mejor_semanas: 2,
      correlacion_en_el_mejor: -0.13,
      climatologia: [5, 40],
    },
    temp_media: {
      r2_estacional: 0.2,
      desfase_mejor_semanas: 16,
      correlacion_en_el_mejor: 0.4,
      en_el_borde: true,
      climatologia: [25, 27],
    },
  },
};

test('el ciclo de casos se devuelve a la escala de casos', () => {
  const serie = serieCiclo(CICLO, 'precipitation_sum');
  assert.ok(serie);
  assert.deepEqual(serie.semanas, [1, 2]);
  assert.ok(Math.abs(serie.casos[0] - 100) < 1e-9);
  assert.ok(Math.abs(serie.casos[1] - 300) < 1e-9);
  assert.equal(serie.desfase, 2);
  assert.equal(serie.enElBorde, false);
  assert.equal(serieCiclo(CICLO, 'punto_rocio'), null);
  assert.equal(serieCiclo(CICLO, 'temp_media')?.enElBorde, true);
});

function p2Sintetico(): ClimaDengueMultipais['P2'] {
  const pais = (r11: number, r9: number) => ({
    r_con_senal: r11,
    ic95: [r11 - 0.4, r11 + 0.5] as [number, number],
    r_con_otros: 0,
    r_con_senal_9_anios: r9,
    r_con_otros_9_anios: 0,
    anomalia_anual: {},
  });
  return {
    por_pais: {
      'EL SALVADOR': pais(0.28, 0.46),
      BRAZIL: pais(0.7, 0.6),
      COLOMBIA: pais(0.35, 0.3),
      MEXICO: pais(0.5, 0.2),
    },
  } as unknown as ClimaDengueMultipais['P2'];
}

test('el bosque ordena de menor a mayor y numera la posición', () => {
  const p2 = p2Sintetico();
  const once = filasBosque(p2, false);
  assert.deepEqual(
    once.map((f) => [f.nombre, f.posicion]),
    [
      ['El Salvador', 1],
      ['Colombia', 2],
      ['México', 3],
      ['Brasil', 4],
    ],
  );
  assert.ok(once[0].ic95);
  const nueve = filasBosque(p2, true);
  assert.equal(nueve.find((f) => f.esElSalvador)?.posicion, 3);
  assert.equal(nueve[0].ic95, null);
});

test('la posición de El Salvador distingue la medida de 11 y la de 9 años', () => {
  const p = posicionElSalvador(p2Sintetico());
  assert.ok(p);
  assert.equal(p.paises, 4);
  assert.equal(p.posicion11, 1);
  assert.equal(p.posicion9, 3);
  const texto = textoPosicion(p);
  assert.match(texto, /la menor de los 4 países: \+0,28/);
  assert.match(
    texto,
    /Sin 2020 y 2024 \(9 años\) es la posición 3 de 4 de menor a mayor: \+0,46\./,
  );
});

test('un país sin estimación agrupada no tiene correlaciones en la matriz', () => {
  const con: AsociacionPais = {
    anios_evaluables: [2014, 2015, 2016, 2017, 2018],
    estimacion: true,
    por_variable: {
      oni: {
        agrupado: { r: 0.265, ic95: [0.04, 0.39] },
        por_anio: {},
        anios_positivos: 7,
        anios_negativos: 1,
        consistente: true,
      },
    },
  };
  const sin: AsociacionPais = {
    anios_evaluables: [],
    estimacion: false,
    por_variable: {},
  };
  const celdas = celdasPaisVariable({ BARBADOS: con, BERMUDA: sin }, [
    'BARBADOS',
    'BERMUDA',
  ]);
  assert.equal(celdas.length, 16);
  const oniBarbados = celdas.find(
    (c) => c.pais === 'BARBADOS' && c.variable === 'oni',
  );
  assert.equal(oniBarbados?.r, 0.265);
  assert.equal(oniBarbados?.excluyeCero, true);
  assert.equal(oniBarbados?.consistente, true);
  assert.equal(oniBarbados?.anios, 5);
  const tempBarbados = celdas.find(
    (c) => c.pais === 'BARBADOS' && c.variable === 'temp_media',
  );
  assert.equal(tempBarbados?.r, null);
  assert.ok(
    celdas.filter((c) => c.pais === 'BERMUDA').every((c) => c.r === null),
  );
});
