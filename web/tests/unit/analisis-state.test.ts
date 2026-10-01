import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  CAPAS_VALIDAS,
  FILTROS_ANALISIS_PREDETERMINADOS as PRED,
  normalizarEstado,
  soloCambiaSemana,
} from '../../src/lib/analisis-state.ts';
import type { CapaAnalitica } from '../../src/lib/tipos-analisis.ts';

describe('analisis-state normalizacion', () => {
  it('conserva todas las capas analíticas válidas', () => {
    for (const capa of CAPAS_VALIDAS) {
      const estado = normalizarEstado(PRED, { capa });
      assert.strictEqual(estado.capa, capa);
    }
  });

  it('restablece minsal_volumen ante una capa desconocida o inválida', () => {
    const estado = normalizarEstado(PRED, {
      capa: 'capa_desconocida' as unknown as CapaAnalitica,
    });
    assert.strictEqual(estado.capa, 'minsal_volumen');
  });

  it('normaliza la serie a probable o confirmado', () => {
    assert.strictEqual(
      normalizarEstado(PRED, { serie: 'confirmado' }).serie,
      'confirmado',
    );
    assert.strictEqual(
      normalizarEstado(PRED, { serie: 'invalido' as unknown as 'probable' })
        .serie,
      'probable',
    );
  });

  it('limita y ordena las semanas epidemiológicas', () => {
    const estado = normalizarEstado(PRED, {
      semana: 99,
      semanaDesde: 40,
      semanaHasta: 10,
    });
    assert.strictEqual(estado.semana, 53);
    assert.strictEqual(estado.semanaDesde, 10);
    assert.strictEqual(estado.semanaHasta, 40);
  });

  it('rechaza años no disponibles y regresa al predeterminado', () => {
    const estado = normalizarEstado(PRED, { anio: 1990 });
    assert.strictEqual(estado.anio, PRED.anio);
  });
});

describe('soloCambiaSemana', () => {
  const base = { ...PRED, semana: 10 };

  it('es verdadero si solo cambia la semana', () => {
    assert.strictEqual(soloCambiaSemana(base, { ...base, semana: 11 }), true);
  });

  it('es falso si cambia otro filtro o no hay estado previo', () => {
    assert.strictEqual(
      soloCambiaSemana(base, { ...base, semana: 11, anio: 2022 }),
      false,
    );
    assert.strictEqual(soloCambiaSemana(base, { ...base }), false);
    assert.strictEqual(soloCambiaSemana(null, base), false);
  });
});
