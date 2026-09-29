import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  lineasDelPie,
  nombreArchivoSeguro,
} from '../../src/lib/exportar-grafico.ts';

test('el pie lleva título, filtros, fuente y fecha de generación', () => {
  const lineas = lineasDelPie({
    titulo: 'Canal endémico',
    fuente: 'Boletines MINSAL',
    filtros: 'San Salvador · 2023',
    fecha: new Date('2026-09-29T12:00:00Z'),
  });
  assert.deepEqual(lineas, [
    'Canal endémico',
    'Filtros: San Salvador · 2023',
    'Fuente: Boletines MINSAL',
    'Generado el 2026-09-29 desde EPI-Aetheris',
  ]);
});

test('sin filtros el pie omite esa línea', () => {
  const lineas = lineasDelPie({
    titulo: 'Curva',
    fuente: 'Tablero MINSAL',
    fecha: new Date('2026-01-02T00:00:00Z'),
  });
  assert.equal(lineas.length, 3);
  assert.ok(!lineas.some((l) => l.startsWith('Filtros')));
});

test('nombreArchivoSeguro quita tildes y símbolos', () => {
  assert.equal(
    nombreArchivoSeguro('Canal endémico — SV-SS'),
    'canal-endemico-sv-ss',
  );
  assert.equal(nombreArchivoSeguro('***'), 'grafico');
});
