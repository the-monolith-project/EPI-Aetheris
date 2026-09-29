import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  nombreSerie,
  textoRezago,
  textoUltimaSemana,
} from '../../src/lib/frescura.ts';

test('nombreSerie traduce las claves conocidas y humaniza las nuevas', () => {
  assert.equal(nombreSerie('clima'), 'Clima (Open-Meteo)');
  assert.equal(nombreSerie('serie_nueva'), 'serie nueva');
});

test('textoUltimaSemana rellena la semana y admite series vacías', () => {
  assert.equal(
    textoUltimaSemana({ ultima_anio: 2026, ultima_semana_epi: 7, semanas: 3 }),
    'SE07 de 2026',
  );
  assert.equal(
    textoUltimaSemana({
      ultima_anio: null,
      ultima_semana_epi: null,
      semanas: null,
    }),
    null,
  );
});

test('textoRezago distingue al día, una semana y varias', () => {
  const base = { ultima_anio: 2026, ultima_semana_epi: 7 };
  assert.equal(textoRezago({ ...base, semanas: 0 }), 'al día');
  assert.equal(textoRezago({ ...base, semanas: 1 }), '1 semana de rezago');
  assert.equal(textoRezago({ ...base, semanas: 4 }), '4 semanas de rezago');
  assert.equal(textoRezago({ ...base, semanas: null }), null);
});
