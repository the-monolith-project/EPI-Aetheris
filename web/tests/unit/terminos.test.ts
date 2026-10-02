import test from 'node:test';
import assert from 'node:assert/strict';
import { entradaGlosario } from '../../src/lib/glosario.ts';
import {
  convertirTerminos as convertir,
  marcadoTermino,
} from '../../src/lib/terminos.ts';

const convertirTerminos = (html: string) => convertir(html, entradaGlosario);

test('un enlace glosario: pasa a botón con nota, definición y enlace', () => {
  const salida = convertirTerminos(
    '<p>El <a href="glosario:iv">Iv</a> se calcula por semana.</p>',
  );
  assert.match(
    salida,
    /<button type="button" class="termino-glosario-boton"[^>]*>Iv<\/button>/,
  );
  assert.match(
    salida,
    /class="termino-glosario-nota" popover="manual" data-sin-busqueda/,
  );
  assert.match(salida, /Iv \(idoneidad biofísica\)/);
  assert.match(salida, /href="\/biblioteca\/03-funciones#m1-/);
  assert.doesNotMatch(salida, /glosario:iv/);
});

test('cada término lleva un id propio y aria-controls lo apunta', () => {
  const salida = convertirTerminos(
    '<p><a href="glosario:iv">Iv</a> y <a href="glosario:iv">Iv</a></p>',
  );
  const ids = [...salida.matchAll(/ id="(termino-iv-\d+)"/g)].map((m) => m[1]);
  assert.equal(ids.length, 2);
  assert.notEqual(ids[0], ids[1]);
  for (const id of ids) assert.ok(salida.includes(`aria-controls="${id}"`));
});

test('en encabezados y bloques pre queda solo el texto', () => {
  const salida = convertirTerminos(
    '<h2>El <a href="glosario:iv">Iv</a></h2><pre><code>x <a href="glosario:iv">Iv</a></code></pre><p><a href="glosario:anomalia">anomalía</a></p>',
  );
  assert.match(salida, /<h2>El Iv<\/h2>/);
  assert.match(salida, /<pre><code>x Iv<\/code><\/pre>/);
  assert.equal(salida.match(/termino-glosario-boton/g)?.length, 1);
});

test('una clave que no está en el glosario es un error', () => {
  assert.throws(
    () => convertirTerminos('<p><a href="glosario:inventada">x</a></p>'),
    /inventada/,
  );
  assert.throws(
    () => marcadoTermino(entradaGlosario, 'inventada', 'x'),
    /glosario/,
  );
});

test('los enlaces normales no se tocan', () => {
  const entrada = '<p><a href="/biblioteca/03-funciones">ver</a></p>';
  assert.equal(convertirTerminos(entrada), entrada);
});
