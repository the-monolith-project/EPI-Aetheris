import test from 'node:test';
import assert from 'node:assert/strict';
import {
  svgCanalMini,
  svgRectaPercentil,
} from '../../src/lib/graficos-presion.ts';

test('la recta apila los empates y marca el valor observado', () => {
  const svg = svgRectaPercentil({
    valores: [2, 2, 2, 5],
    observado: 2,
    etiquetaObservado: '2 casos',
  });
  assert.match(svg, /^<svg [^>]*aria-hidden="true"/);
  assert.equal(svg.match(/class="recta-punto"/g)?.length, 4);
  // Tres puntos en la misma x, a alturas distintas.
  const ys = [...svg.matchAll(/cx="18" cy="([\d.]+)"/g)].map((m) => m[1]);
  assert.equal(new Set(ys).size, 3);
  assert.match(svg, /class="recta-observado" x1="18"/);
});

test('un observado fuera del rango amplía el eje en vez de salirse', () => {
  const svg = svgRectaPercentil({
    valores: [1, 2, 3],
    observado: 9,
    etiquetaObservado: 'x',
  });
  assert.match(svg, /class="recta-observado" x1="502"/);
});

test('la recta escapa las etiquetas', () => {
  const svg = svgRectaPercentil({
    valores: [1],
    observado: 1,
    etiquetaObservado: '<i>&',
    cortes: [{ valor: 1, etiqueta: '"P50"' }],
  });
  assert.match(svg, /&lt;i&gt;&amp;/);
  assert.match(svg, /&quot;P50&quot;/);
});

test('el canal deja en blanco las semanas sin línea base y corta la línea en los huecos', () => {
  const svg = svgCanalMini({
    semanas: [
      { semana: 1, p50: 2, p75: 4, observado: 3 },
      { semana: 2, p50: null, p75: null, observado: 5 },
      { semana: 3, p50: 2, p75: 4, observado: null },
      { semana: 4, p50: 2, p75: 4, observado: 1 },
    ],
    colores: ['#aaa', '#bbb', '#ccc'],
  });
  // Tres semanas con línea base, tres bandas cada una.
  assert.equal(svg.match(/fill="#aaa"/g)?.length, 3);
  assert.equal(svg.match(/fill="#ccc"/g)?.length, 3);
  assert.equal(svg.match(/class="canal-punto"/g)?.length, 3);
  // La línea vuelve a empezar (M) después del hueco de la semana 3.
  const trazo = /class="canal-linea" d="([^"]+)"/.exec(svg)?.[1] ?? '';
  assert.equal(trazo.match(/M/g)?.length, 2);
  assert.equal(trazo.match(/L/g)?.length, 1);
});
