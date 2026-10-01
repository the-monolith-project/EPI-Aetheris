import test from 'node:test';
import assert from 'node:assert/strict';
import { encontrar, plegar } from '../../src/lib/buscar-en-documento.ts';

test('plegar quita tildes y mayúsculas sin cambiar la longitud', () => {
  const texto = 'Presión Ñandú — ÁÉÍÓÚ';
  assert.equal(plegar(texto), 'presion nandu — aeiou');
  assert.equal(plegar(texto).length, texto.length);
});

test('encontrar ignora tildes y mayúsculas y devuelve índices del original', () => {
  const texto = 'La presión relativa y la PRESION absoluta';
  assert.deepEqual(encontrar(texto, 'presion'), [3, 25]);
  assert.deepEqual(encontrar(texto, 'Presión'), [3, 25]);
});

test('una consulta vacía o ausente no devuelve coincidencias', () => {
  assert.deepEqual(encontrar('texto', '   '), []);
  assert.deepEqual(encontrar('texto', 'zzz'), []);
});

test('las coincidencias no se solapan', () => {
  assert.deepEqual(encontrar('aaaa', 'aa'), [0, 2]);
});
