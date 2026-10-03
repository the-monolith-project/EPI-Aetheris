import test from 'node:test';
import assert from 'node:assert/strict';
import { svgTiraAnios } from '../../src/lib/tira-anios.ts';

test('dibuja una barra por valor, el año descrito aparte y las líneas', () => {
  const svg = svgTiraAnios({
    grupos: [
      { etiqueta: '2018', valores: [0.5] },
      { etiqueta: '2019', valores: [1] },
      { etiqueta: '2026', valores: [0.25], apartado: true },
    ],
    maximo: 1,
    lineas: [{ valor: 0.5, etiqueta: 'mediana 0,5', tipo: 'mediana' }],
    banda: { desde: 0.4, hasta: 0.6 },
  });
  assert.match(svg, /^<svg viewBox="0 0 520 190"[^>]*aria-hidden="true"/);
  assert.equal(svg.match(/class="tira-barra"/g)?.length, 2);
  assert.equal(svg.match(/tira-barra-descrita/g)?.length, 1);
  assert.match(svg, /class="tira-separador"/);
  assert.match(svg, /class="tira-banda"/);
  assert.match(svg, /tira-linea-mediana/);
  assert.match(svg, />mediana 0,5</);
  // La barra de 1 llega al borde superior del área (y = 10) y la de 0,5 a la mitad.
  assert.match(svg, /class="tira-barra" x="[\d.]+" y="10" /);
  assert.match(svg, /class="tira-barra" x="[\d.]+" y="88" /);
});

test('un hueco se dibuja vacío y no como una barra de cero', () => {
  const svg = svgTiraAnios({
    grupos: [{ etiqueta: '2020', valores: [null, 3, 0] }],
    maximo: 10,
  });
  assert.equal(svg.match(/class="tira-hueco"/g)?.length, 1);
  assert.equal(svg.match(/class="tira-barra"/g)?.length, 2);
});

test('un valor fuera del eje se recorta al borde', () => {
  const fuera = svgTiraAnios({
    grupos: [{ etiqueta: 'a', valores: [5] }],
    maximo: 1,
  });
  const borde = svgTiraAnios({
    grupos: [{ etiqueta: 'a', valores: [1] }],
    maximo: 1,
  });
  assert.equal(fuera, borde);
});

test('las etiquetas se escapan', () => {
  const svg = svgTiraAnios({
    grupos: [{ etiqueta: '<b>&', valores: [1] }],
    maximo: 1,
    lineas: [{ valor: 0.5, etiqueta: '"x"<', tipo: 'corte' }],
  });
  assert.match(svg, /&lt;b&gt;&amp;/);
  assert.match(svg, /&quot;x&quot;&lt;/);
  assert.doesNotMatch(svg, /<b>/);
});
