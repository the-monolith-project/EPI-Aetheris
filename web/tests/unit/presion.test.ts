import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  ANIOS_BASE_PRESION,
  EJEMPLO_PRESION,
  MINIMO_ANIOS,
  PRESETS_PRESION,
  VENTANA,
  calcularPresion,
  categorizar,
  construirPool,
  rangoPercentil,
  semanasEnVentana,
  serieEjemplo,
  type ResultadoPresion,
  type SerieCasos,
} from '../../src/lib/presion.ts';
import { percentil } from '../../src/lib/estadistica.ts';

interface CasoPresion {
  serie: SerieCasos;
  anio: number;
  semana: number;
  resultado: ResultadoPresion;
}

interface CasoRango {
  pool: number[];
  valor: number;
  percentil: number;
  p50: number;
  p75: number;
  categoria: 'baja' | 'media' | 'alta';
}

// Valores generados con el Python del backend (ver el encabezado de
// src/lib/presion.ts).
const referencia = JSON.parse(
  readFileSync(
    new URL('./fixtures/fichas-m2-m3-referencia.json', import.meta.url),
    'utf8',
  ),
) as {
  presion: CasoPresion[];
  rangos: CasoRango[];
  constantes: {
    anios_base_presion: number[];
    ventana: number;
    piso_anios_min: number;
  };
};

const TOLERANCIA = 1e-9;

test('las constantes coinciden con las del backend', () => {
  assert.deepEqual(
    [...ANIOS_BASE_PRESION],
    referencia.constantes.anios_base_presion,
  );
  assert.equal(VENTANA, referencia.constantes.ventana);
  assert.equal(MINIMO_ANIOS, referencia.constantes.piso_anios_min);
});

test('calcularPresion da la misma salida que el backend', () => {
  assert.equal(referencia.presion.length, 80);
  for (const c of referencia.presion) {
    const etiqueta = `${c.anio} SE${c.semana}`;
    const r = calcularPresion(c.serie, c.anio, c.semana);
    const e = c.resultado;
    assert.equal(
      r.casos_observados,
      e.casos_observados,
      `observado ${etiqueta}`,
    );
    assert.equal(r.categoria, e.categoria, `categoría ${etiqueta}`);
    assert.equal(r.n_obs_baseline, e.n_obs_baseline, `n ${etiqueta}`);
    assert.equal(r.anios_baseline, e.anios_baseline, `años ${etiqueta}`);
    assert.equal(r.nota, e.nota, `nota ${etiqueta}`);
    for (const campo of [
      'percentil',
      'p50_baseline',
      'p75_baseline',
    ] as const) {
      const a = r[campo];
      const b = e[campo];
      if (b === null) assert.equal(a, null, `${campo} ${etiqueta}`);
      else
        assert.ok(
          a !== null && Math.abs(a - b) < TOLERANCIA,
          `${campo} ${etiqueta}: ${a} ≠ ${b}`,
        );
    }
  }
});

test('rangoPercentil y categorizar coinciden en empates, bordes y pool de un valor', () => {
  for (const c of referencia.rangos) {
    const etiqueta = `${JSON.stringify(c.pool)} con ${c.valor}`;
    assert.ok(
      Math.abs(rangoPercentil(c.pool, c.valor) - c.percentil) < TOLERANCIA,
      etiqueta,
    );
    const p50 = percentil(c.pool, 50);
    const p75 = percentil(c.pool, 75);
    assert.ok(Math.abs(p50 - c.p50) < TOLERANCIA, `p50 ${etiqueta}`);
    assert.ok(Math.abs(p75 - c.p75) < TOLERANCIA, `p75 ${etiqueta}`);
    assert.equal(categorizar(c.valor, p50, p75), c.categoria, etiqueta);
  }
});

test('la ventana no pasa de un año a otro', () => {
  assert.deepEqual(semanasEnVentana(1), [1, 2]);
  assert.deepEqual(semanasEnVentana(30), [29, 30, 31]);
  assert.deepEqual(semanasEnVentana(53), [52, 53]);
});

test('el pool deja fuera el año descrito y los huecos', () => {
  const serie: SerieCasos = {
    2018: { 9: 1, 10: 2, 11: 3 },
    2019: { 10: 0 },
    2021: {},
    2022: { 10: 99 },
  };
  const p = construirPool(serie, 2022, 10);
  assert.deepEqual(p.pool, [1, 2, 3, 0]);
  assert.equal(p.aniosConDato, 2);
  assert.equal(p.porAnio.length, 4);
  assert.equal(
    p.porAnio[2].semanas.every((s) => s.casos === null),
    true,
  );
});

test('el corte cae hacia abajo', () => {
  assert.equal(categorizar(5, 5, 9), 'baja');
  assert.equal(categorizar(9, 5, 9), 'media');
  assert.equal(categorizar(9.5, 5, 9), 'alta');
});

test('el ejemplo de la ficha y los presets', () => {
  const e = EJEMPLO_PRESION;
  const r = calcularPresion(
    serieEjemplo(e.ventanas, e.anio, e.semana, e.observado),
    e.anio,
    e.semana,
  );
  assert.equal(r.n_obs_baseline, 12);
  assert.equal(r.anios_baseline, 4);
  assert.ok(r.percentil !== null);
  for (const p of PRESETS_PRESION) {
    const rp = calcularPresion(
      serieEjemplo(p.ventanas, 2022, 30, p.observado),
      2022,
      30,
    );
    if (p.clave === 'sin-historia') assert.equal(rp.percentil, null);
    else assert.ok(rp.percentil !== null);
  }
  const baja = PRESETS_PRESION.find((p) => p.clave === 'baja')!;
  const alta = PRESETS_PRESION.find((p) => p.clave === 'alta')!;
  assert.equal(
    calcularPresion(
      serieEjemplo(baja.ventanas, 2022, 30, baja.observado),
      2022,
      30,
    ).categoria,
    'baja',
  );
  assert.equal(
    calcularPresion(
      serieEjemplo(alta.ventanas, 2022, 30, alta.observado),
      2022,
      30,
    ).categoria,
    'alta',
  );
});
