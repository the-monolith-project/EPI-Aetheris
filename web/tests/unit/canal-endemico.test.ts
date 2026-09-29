import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  categoriaCanal,
  construirCanal,
} from '../../src/lib/canal-endemico.ts';

const punto = (obs: number | null, p50: number | null, p75: number | null) => ({
  casos_observados: obs,
  p50_baseline: p50,
  p75_baseline: p75,
});

test('ordena por semana y elige la serie pedida', () => {
  const canal = construirCanal(
    [
      { semana_epi: 2, probable: punto(5, 3, 6), confirmado: punto(1, 1, 2) },
      { semana_epi: 1, probable: punto(4, 2, 5), confirmado: punto(0, 1, 2) },
    ],
    'confirmado',
  );
  assert.deepEqual(
    canal.map((p) => p.semana),
    [1, 2],
  );
  assert.equal(canal[1].observado, 1);
  assert.equal(canal[1].p75, 2);
});

test('sin línea base deja huecos y no interpola', () => {
  const canal = construirCanal(
    [
      {
        semana_epi: 1,
        probable: punto(4, null, null),
        confirmado: punto(0, null, null),
      },
      {
        semana_epi: 2,
        probable: punto(4, 3, null),
        confirmado: punto(0, 1, 2),
      },
    ],
    'probable',
  );
  assert.equal(canal[0].p50, null);
  assert.equal(canal[1].p50, null);
  assert.equal(canal[1].p75, null);
  assert.equal(canal[0].observado, 4);
});

test('categoriaCanal usa P50 y P75 y devuelve null sin datos', () => {
  assert.equal(
    categoriaCanal({ semana: 1, p50: 3, p75: 6, observado: 3 }),
    'baja',
  );
  assert.equal(
    categoriaCanal({ semana: 1, p50: 3, p75: 6, observado: 6 }),
    'media',
  );
  assert.equal(
    categoriaCanal({ semana: 1, p50: 3, p75: 6, observado: 7 }),
    'alta',
  );
  assert.equal(
    categoriaCanal({ semana: 1, p50: null, p75: null, observado: 7 }),
    null,
  );
  assert.equal(
    categoriaCanal({ semana: 1, p50: 3, p75: 6, observado: null }),
    null,
  );
});

test('serie vacía devuelve lista vacía', () => {
  assert.deepEqual(construirCanal([], 'probable'), []);
});
