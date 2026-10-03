import test from 'node:test';
import assert from 'node:assert/strict';
import {
  CLAVES_PREFERENCIAS,
  resolverPreferenciaAnimaciones,
  resolverTema,
  resolverTexto,
} from '../../src/lib/preferencias.ts';

test('tema: sin elección o con un valor desconocido, claro', () => {
  assert.equal(resolverTema('light'), 'light');
  assert.equal(resolverTema('dark'), 'dark');
  assert.equal(resolverTema('sistema'), 'sistema');
  assert.equal(resolverTema(null), 'light');
  assert.equal(resolverTema('auto'), 'light');
});

test('animaciones: on/off guardados; sin elección, sistema', () => {
  assert.equal(resolverPreferenciaAnimaciones('on'), 'on');
  assert.equal(resolverPreferenciaAnimaciones('off'), 'off');
  assert.equal(resolverPreferenciaAnimaciones(null), 'sistema');
  assert.equal(resolverPreferenciaAnimaciones('quizá'), 'sistema');
});

test('texto: solo "grande" cambia el tamaño', () => {
  assert.equal(resolverTexto('grande'), 'grande');
  assert.equal(resolverTexto(null), 'normal');
  assert.equal(resolverTexto('enorme'), 'normal');
});

test('las claves propias comparten el prefijo epi: y conservan las históricas', () => {
  for (const clave of CLAVES_PREFERENCIAS) assert.ok(clave.startsWith('epi:'));
  assert.ok(CLAVES_PREFERENCIAS.includes('epi:tema'));
  assert.ok(CLAVES_PREFERENCIAS.includes('epi:animaciones'));
  assert.ok(CLAVES_PREFERENCIAS.includes('epi:departamento'));
});
