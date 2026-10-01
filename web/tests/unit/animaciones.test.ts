import test from 'node:test';
import assert from 'node:assert/strict';
import { resolverAnimaciones } from '../../src/lib/animaciones.ts';

test('sin elección guardada manda el sistema', () => {
  assert.equal(resolverAnimaciones(null, false), 'on');
  assert.equal(resolverAnimaciones(null, true), 'off');
});

test('la elección guardada gana sobre el sistema', () => {
  assert.equal(resolverAnimaciones('on', true), 'on');
  assert.equal(resolverAnimaciones('off', false), 'off');
});

test('un valor guardado desconocido se ignora', () => {
  assert.equal(resolverAnimaciones('quizá', true), 'off');
  assert.equal(resolverAnimaciones('', false), 'on');
});
