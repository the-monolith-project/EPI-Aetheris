import assert from 'node:assert/strict';
import { test } from 'node:test';
import { codigoIncrustacion } from '../../src/lib/incrustar.ts';

test('genera un iframe con título, alto y carga diferida', () => {
  const codigo = codigoIncrustacion({
    src: 'https://epi-aetheris.dev/incrustar/curva-nacional',
    titulo: 'Curva nacional',
    alto: 420,
  });
  assert.equal(
    codigo,
    '<iframe src="https://epi-aetheris.dev/incrustar/curva-nacional" title="Curva nacional" width="100%" height="420" loading="lazy" style="border:0"></iframe>',
  );
});

test('escapa comillas y ángulos en los atributos', () => {
  const codigo = codigoIncrustacion({
    src: 'https://x.dev/?a="1"',
    titulo: 'A <b> "c"',
    alto: 300.6,
  });
  assert.ok(!codigo.includes('title="A <b>'));
  assert.ok(codigo.includes('&quot;'));
  assert.ok(codigo.includes('height="301"'));
});
