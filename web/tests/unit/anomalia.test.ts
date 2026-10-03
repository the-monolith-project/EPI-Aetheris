import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  EJEMPLO_ANOMALIA,
  PRESETS_ANOMALIA,
  calcularBaselineSemana,
  calcularSigma,
  corpusAnios,
  percentil,
  resumirPool,
} from '../../src/lib/anomalia.ts';
import { desviacionMuestral, redondear } from '../../src/lib/estadistica.ts';

interface CasoAnomalia {
  pool: number[];
  anio_excluido: number;
  semana: number;
  valor: number;
  mediana: number | null;
  desviacion: number | null;
  sigma: number | null;
  p25: number | null;
  p75: number | null;
  serie?: Record<string, Record<string, number>>;
}

// Valores generados con el Python del backend (ver el encabezado de
// src/lib/anomalia.ts).
const referencia = JSON.parse(
  readFileSync(
    new URL('./fixtures/fichas-m2-m3-referencia.json', import.meta.url),
    'utf8',
  ),
) as { anomalia: CasoAnomalia[]; constantes: { piso_pool_anomalia: number } };

const TOLERANCIA = 1e-9;

function cerca(a: number | null, b: number | null, etiqueta: string): void {
  if (b === null) {
    assert.equal(a, null, etiqueta);
    return;
  }
  assert.ok(
    a !== null && Math.abs(a - b) < TOLERANCIA,
    `${etiqueta}: ${a} ≠ ${b}`,
  );
}

test('mediana, desviación, cuantiles y σ coinciden con el backend', () => {
  assert.ok(referencia.anomalia.length > 50);
  for (const c of referencia.anomalia) {
    const etiqueta = `año ${c.anio_excluido} semana ${c.semana}`;
    const r = resumirPool(c.pool);
    cerca(r.mediana, c.mediana, `mediana ${etiqueta}`);
    cerca(r.desviacion, c.desviacion, `desviación ${etiqueta}`);
    cerca(r.p25, c.p25, `p25 ${etiqueta}`);
    cerca(r.p75, c.p75, `p75 ${etiqueta}`);
    cerca(
      calcularSigma(c.valor, r.mediana, r.desviacion),
      c.sigma,
      `σ ${etiqueta}`,
    );
  }
});

test('el pool se arma con la misma semana exacta y sin el año descrito', () => {
  const conSerie = referencia.anomalia.filter((c) => c.serie);
  assert.equal(conSerie.length, 15);
  for (const c of conSerie) {
    const b = calcularBaselineSemana(
      c.serie!,
      c.anio_excluido,
      c.semana,
      corpusAnios(2026),
    );
    assert.deepEqual(
      b.pool,
      c.pool,
      `pool año ${c.anio_excluido} semana ${c.semana}`,
    );
    assert.ok(!b.anios.includes(c.anio_excluido));
    cerca(b.mediana, c.mediana, 'mediana');
    cerca(b.desviacion, c.desviacion, 'desviación');
  }
});

test('con menos de 3 valores no hay línea base', () => {
  assert.equal(referencia.constantes.piso_pool_anomalia, 3);
  const r = resumirPool([0.4, 0.5]);
  assert.deepEqual(r, {
    mediana: null,
    desviacion: null,
    p25: null,
    p75: null,
  });
  assert.equal(calcularSigma(0.7, r.mediana, r.desviacion), null);
});

test('una desviación casi nula deja σ sin dato', () => {
  assert.equal(calcularSigma(0.7, 0.5, 0), null);
  assert.equal(calcularSigma(0.7, 0.5, 1e-10), null);
  assert.equal(calcularSigma(null, 0.5, 0.1), null);
  assert.ok(Math.abs((calcularSigma(0.7, 0.5, 0.1) ?? 0) - 2) < 1e-12);
});

test('percentil interpola entre vecinos', () => {
  assert.equal(percentil([1, 2, 3, 4], 50), 2.5);
  assert.equal(percentil([4, 1, 3, 2], 0), 1);
  assert.equal(percentil([4, 1, 3, 2], 100), 4);
  assert.equal(percentil([5], 75), 5);
  assert.throws(() => percentil([], 50));
});

test('desviación muestral divide entre n − 1', () => {
  assert.equal(desviacionMuestral([1]), null);
  assert.ok(
    Math.abs(
      (desviacionMuestral([2, 4, 4, 4, 5, 5, 7, 9]) ?? 0) - 2.138089935,
    ) < 1e-9,
  );
});

test('redondear sigue a Python: el empate exacto va a la cifra par', () => {
  assert.equal(redondear(12.25, 1), 12.2);
  assert.equal(redondear(12.35, 1), 12.3); // 12,35 es 12,3499… en binario
  assert.equal(redondear(0.125, 2), 0.12);
  assert.equal(redondear(2.5, 0), 2);
  assert.equal(redondear(3.5, 0), 4);
  assert.equal(redondear(0.92857142, 4), 0.9286);
  assert.equal(redondear(-1.25, 1), -1.2);
  assert.equal(redondear(77.77777777777779, 1), 77.8);
});

test('el ejemplo de la ficha y los presets dan una σ', () => {
  const serie: Record<number, Record<number, number>> = {};
  for (const r of EJEMPLO_ANOMALIA.referencias) serie[r.anio] = { 20: r.iv };
  serie[2026] = { 20: EJEMPLO_ANOMALIA.valor };
  const b = calcularBaselineSemana(serie, 2026, 20, corpusAnios(2026));
  assert.equal(b.pool.length, 12);
  const sigma = calcularSigma(EJEMPLO_ANOMALIA.valor, b.mediana, b.desviacion);
  assert.ok(sigma !== null && sigma > 1);
  for (const p of PRESETS_ANOMALIA) {
    const pool = p.referencias.filter((v): v is number => v !== null);
    const r = resumirPool(pool);
    const s = calcularSigma(p.valor, r.mediana, r.desviacion);
    if (p.clave === 'poca-historia') assert.equal(s, null);
    else assert.ok(s !== null);
  }
});
