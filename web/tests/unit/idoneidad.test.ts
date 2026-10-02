import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  C_NORM,
  calcularIv,
  desgloseIv,
  fH,
  fR,
  fT,
  muestrear,
} from '../../src/lib/idoneidad.ts';

interface Caso {
  t: number;
  r: number;
  hr: number;
  ft: number;
  fr: number;
  fh: number;
  iv: number;
}

// Valores generados con backend/api/idoneidad.py (ver el encabezado de
// src/lib/idoneidad.ts).
const referencia = JSON.parse(
  readFileSync(
    new URL('./fixtures/idoneidad-referencia.json', import.meta.url),
    'utf8',
  ),
) as { c_norm: number; casos: Caso[] };

const TOLERANCIA = 1e-9;

test('la constante c coincide con la del backend', () => {
  assert.ok(Math.abs(C_NORM - referencia.c_norm) < 1e-9);
  assert.ok(Math.abs(C_NORM - 0.000795) < 1e-6);
});

test('cada factor y el Iv coinciden con el backend en toda la rejilla', () => {
  for (const c of referencia.casos) {
    const etiqueta = `T=${c.t} R=${c.r} HR=${c.hr}`;
    assert.ok(Math.abs(fT(c.t) - c.ft) < TOLERANCIA, `fT ${etiqueta}`);
    assert.ok(Math.abs(fR(c.r) - c.fr) < TOLERANCIA, `fR ${etiqueta}`);
    assert.ok(Math.abs(fH(c.hr) - c.fh) < TOLERANCIA, `fH ${etiqueta}`);
    const iv = calcularIv({ temperatura: c.t, lluvia: c.r, humedad: c.hr });
    assert.ok(Math.abs(iv - c.iv) < TOLERANCIA, `Iv ${etiqueta}`);
  }
});

test('fT vale 0 fuera de 16 a 38 °C y su máximo es 1', () => {
  assert.equal(fT(16), 0);
  assert.equal(fT(38), 0);
  assert.equal(fT(10), 0);
  const maximo = Math.max(...muestrear(fT, 16, 38, 2200).map((p) => p.y));
  assert.ok(Math.abs(maximo - 1) < 1e-4);
});

test('fR vale un medio en 30 mm y fH llega a 1 en el 50 %', () => {
  assert.ok(Math.abs(fR(30) - 0.5) < 1e-12);
  assert.equal(fH(50), 1);
  assert.equal(fH(80), 1);
  assert.equal(fH(25), 0.5);
  assert.equal(fH(-5), 0);
});

test('el desglose multiplica los tres factores', () => {
  const d = desgloseIv({ temperatura: 28, lluvia: 40, humedad: 70 });
  assert.ok(Math.abs(d.iv - d.fT * d.factorLluvia * d.fH) < 1e-12);
  assert.ok(Math.abs(d.factorLluvia - (0.3 + 0.7 * d.fR)) < 1e-12);
});

test('sin humedad o fuera del rango térmico el Iv es 0', () => {
  assert.equal(calcularIv({ temperatura: 28, lluvia: 80, humedad: 0 }), 0);
  assert.equal(calcularIv({ temperatura: 12, lluvia: 80, humedad: 80 }), 0);
});

test('muestrear devuelve pasos + 1 puntos entre los extremos', () => {
  const p = muestrear((x) => x, 0, 10, 5);
  assert.equal(p.length, 6);
  assert.deepEqual(p[0], { x: 0, y: 0 });
  assert.deepEqual(p[5], { x: 10, y: 10 });
});

test('formatearNumero usa coma decimal', async () => {
  const { formatearNumero } = await import('../../src/lib/idoneidad.ts');
  assert.equal(formatearNumero(0.8168, 2), '0,82');
  assert.equal(formatearNumero(27, 0), '27');
  assert.equal(formatearNumero(32.5, 1), '32,5');
});

test('los valores de ejemplo y los presets dan un Iv entre 0 y 1', async () => {
  const { EJEMPLO_IV, PRESETS_IV } = await import('../../src/lib/idoneidad.ts');
  for (const e of [EJEMPLO_IV, ...PRESETS_IV.map((p) => p.entradas)]) {
    const iv = calcularIv(e);
    assert.ok(iv >= 0 && iv <= 1);
  }
  assert.ok(calcularIv(PRESETS_IV[0].entradas) > 0.9);
});
