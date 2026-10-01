import test from 'node:test';
import assert from 'node:assert/strict';
import {
  navegacionBiblioteca,
  navegacionLegal,
} from '../../src/lib/navegacion-documentos.ts';

test('la biblioteca se agrupa por categoría, en orden, y marca el documento actual', () => {
  const nav = navegacionBiblioteca(
    [
      { id: 'b', data: { titulo: 'B', orden: 2, categoria: 'Uno' } },
      { id: 'c', data: { titulo: 'C', orden: 3, categoria: 'Dos' } },
      { id: 'a', data: { titulo: 'A', orden: 1, categoria: 'Uno' } },
    ],
    'b',
  );
  assert.deepEqual(
    nav.grupos.map((g) => [g.titulo, g.enlaces.map((e) => e.etiqueta)]),
    [
      ['Uno', ['A', 'B']],
      ['Dos', ['C']],
    ],
  );
  assert.equal(nav.grupos[0]?.enlaces[1]?.actual, true);
  assert.equal(nav.grupos[0]?.enlaces[0]?.actual, false);
});

test('los documentos legales marcan solo el actual', () => {
  const enlaces = navegacionLegal('/legal/privacidad').grupos[0]?.enlaces ?? [];
  assert.equal(enlaces.length, 3);
  assert.deepEqual(
    enlaces.filter((e) => e.actual).map((e) => e.href),
    ['/legal/privacidad'],
  );
});
