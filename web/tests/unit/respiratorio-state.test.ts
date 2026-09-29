import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  FILTROS_RESPIRATORIO_PREDETERMINADOS as PRED,
  aplicarFiltrosAParametros,
  cambiosDesdeParametros,
  normalizarFiltrosRespiratorio,
} from '../../src/lib/respiratorio-state.ts';

describe('respiratorio-state', () => {
  it('lee la URL con los mismos nombres que dengue', () => {
    const cambios = cambiosDesdeParametros(
      new URLSearchParams(
        'dept=SV-SA&year=2021&compare=SV-LI&fromWeek=5&toWeek=30',
      ),
    );
    const f = normalizarFiltrosRespiratorio(PRED, cambios);
    assert.deepStrictEqual(f, {
      departamento: 'SV-SA',
      anio: 2021,
      comparar: 'SV-LI',
      semanaDesde: 5,
      semanaHasta: 30,
    });
  });

  it('rechaza años y departamentos inválidos', () => {
    const f = normalizarFiltrosRespiratorio(PRED, {
      anio: 2020,
      departamento: 'SV-XX',
      comparar: 'SV-YY',
    });
    assert.strictEqual(f.anio, 'todos');
    assert.strictEqual(f.departamento, 'SV-SS');
    assert.strictEqual(f.comparar, null);
  });

  it('no compara un departamento consigo mismo', () => {
    const f = normalizarFiltrosRespiratorio(PRED, {
      departamento: 'SV-SA',
      comparar: 'SV-SA',
    });
    assert.strictEqual(f.comparar, null);
  });

  it('ordena y limita el rango de semanas', () => {
    const f = normalizarFiltrosRespiratorio(PRED, {
      semanaDesde: 60,
      semanaHasta: -3,
    });
    assert.strictEqual(f.semanaDesde, 1);
    assert.strictEqual(f.semanaHasta, 52);
  });

  it('acepta "todos" como año', () => {
    const cambios = cambiosDesdeParametros(new URLSearchParams('year=todos'));
    assert.strictEqual(
      normalizarFiltrosRespiratorio(PRED, cambios).anio,
      'todos',
    );
  });

  it('solo escribe en la URL lo que difiere del predeterminado', () => {
    const p = new URLSearchParams('otro=1');
    aplicarFiltrosAParametros(PRED, p);
    assert.strictEqual(p.toString(), 'otro=1');
    aplicarFiltrosAParametros(
      normalizarFiltrosRespiratorio(PRED, {
        departamento: 'SV-SA',
        anio: 2022,
      }),
      p,
    );
    assert.strictEqual(p.get('dept'), 'SV-SA');
    assert.strictEqual(p.get('year'), '2022');
    assert.strictEqual(p.get('otro'), '1');
    assert.strictEqual(p.has('fromWeek'), false);
  });
});
