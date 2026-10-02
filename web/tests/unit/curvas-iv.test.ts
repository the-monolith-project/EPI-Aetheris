import test from 'node:test';
import assert from 'node:assert/strict';
import { svgCurva } from '../../src/lib/curvas-iv.ts';
import { proyectarDepartamentos } from '../../src/lib/geo-svg.ts';

test('la curva dibuja el trazo, la posición y el punto sobre la función', () => {
  const svg = svgCurva({
    f: (x) => x / 10,
    desde: 0,
    hasta: 10,
    valor: 5,
    etiquetaX: 'Lluvia (mm)',
    marcas: [{ x: 5, etiqueta: '5' }],
  });
  assert.match(svg, /^<svg viewBox="0 0 240 160"[^>]*aria-hidden="true"/);
  assert.match(svg, /class="cv-curva" d="M30 /);
  assert.match(svg, /<circle class="cv-punto"/);
  assert.match(svg, /Lluvia \(mm\)/);
  // x=5 está a la mitad del área (30 + 198/2) y y=0,5 a la mitad del área (10 + 116/2).
  assert.match(svg, /cx="129" cy="68"/);
});

test('un valor fuera del rango se ajusta al borde', () => {
  const fuera = svgCurva({
    f: (x) => x,
    desde: 0,
    hasta: 1,
    valor: 9,
    etiquetaX: 'x',
  });
  const borde = svgCurva({
    f: (x) => x,
    desde: 0,
    hasta: 1,
    valor: 1,
    etiquetaX: 'x',
  });
  assert.equal(fuera, borde);
});

test('las etiquetas se escapan', () => {
  const svg = svgCurva({
    f: () => 0,
    desde: 0,
    hasta: 1,
    valor: 0,
    etiquetaX: '<b>&',
  });
  assert.match(svg, /&lt;b&gt;&amp;/);
  assert.doesNotMatch(svg, /<b>/);
});

const cuadrado = (x: number, y: number, lado: number) => [
  [
    [x, y],
    [x + lado, y],
    [x + lado, y + lado],
    [x, y + lado],
    [x, y],
  ],
];

test('proyecta Polygon y MultiPolygon con la proporción del país', () => {
  const mapa = proyectarDepartamentos(
    {
      features: [
        {
          properties: { codigo: 'SV-A' },
          geometry: { type: 'Polygon', coordinates: cuadrado(-90, 13, 1) },
        },
        {
          properties: { codigo: 'SV-B' },
          geometry: {
            type: 'MultiPolygon',
            coordinates: [cuadrado(-88, 13, 1), cuadrado(-87.5, 14, 0.5)],
          },
        },
      ],
    },
    300,
  );
  assert.equal(mapa.ancho, 300);
  assert.equal(mapa.departamentos.length, 2);
  assert.equal(mapa.departamentos[0].codigo, 'SV-A');
  assert.match(mapa.departamentos[0].d, /^M[\d.]+ [\d.]+L.*Z$/);
  // dos anillos en el MultiPolygon: dos cierres
  assert.equal(mapa.departamentos[1].d.match(/Z/g)?.length, 2);
  // más ancho que alto: 3,5° de lon (corregidos por cos) contra 1,5° de lat.
  assert.ok(mapa.alto < mapa.ancho);
});

test('descarta vértices más cercanos que la tolerancia', () => {
  const pegados = [
    [
      [-90, 13],
      [-89.9999, 13],
      [-89.9998, 13],
      [-89, 13],
      [-89, 14],
      [-90, 14],
      [-90, 13],
    ],
  ];
  const mapa = proyectarDepartamentos(
    {
      features: [
        {
          properties: { codigo: 'SV-A' },
          geometry: { type: 'Polygon', coordinates: pegados },
        },
      ],
    },
    300,
  );
  assert.equal(mapa.departamentos[0].d.match(/[ML]/g)?.length, 5);
});
