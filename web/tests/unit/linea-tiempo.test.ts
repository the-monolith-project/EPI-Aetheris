import test from 'node:test';
import assert from 'node:assert/strict';
import { svgLineaTiempo } from '../../src/lib/linea-tiempo.ts';

test('marca la última semana, hoy y la distancia en semanas', () => {
  const svg = svgLineaTiempo({ ultima: [2023, 52], hoy: '2026-10-02' });
  assert.match(svg, /^<svg [^>]*aria-hidden="true"/);
  assert.match(svg, />SE52 de 2023</);
  assert.match(svg, />hoy: SE39 de 2026</);
  assert.match(svg, />144 semanas</);
  // Un año por marca, de 2023 a 2026.
  assert.equal(svg.match(/>202[3-6]</g)?.length, 4);
});

test('una semana 53 al cruzar de año cuenta como una semana', () => {
  const svg = svgLineaTiempo({ ultima: [2020, 53], hoy: '2021-01-03' });
  assert.match(svg, />1 semana</);
});

test('la última semana queda a la izquierda de hoy', () => {
  const svg = svgLineaTiempo({ ultima: [2024, 5], hoy: '2026-10-02' });
  const xu = Number(/class="linea-ultima" cx="([\d.]+)"/.exec(svg)?.[1]);
  const xh = Number(/class="linea-hoy" x="([\d.]+)"/.exec(svg)?.[1]);
  assert.ok(xu < xh);
});
