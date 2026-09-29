import { describe, it } from 'node:test';
import assert from 'node:assert';
import { resumirUltimaSemana } from '../../src/lib/resumen-semana.ts';
import type { CasoNacionalSemanal } from '../../src/lib/tipos-analisis.ts';

function caso(
  anio: number,
  semana_epi: number,
  conteo: number,
  fuente: CasoNacionalSemanal['fuente'] = 'minsal_tablero',
): CasoNacionalSemanal {
  return { semana_inicio: `${anio}-01-01`, anio, semana_epi, conteo, fuente };
}

describe('resumirUltimaSemana', () => {
  it('devuelve null con serie vacía', () => {
    assert.strictEqual(resumirUltimaSemana([]), null);
  });

  it('devuelve null si no hay filas del tablero', () => {
    assert.strictEqual(
      resumirUltimaSemana([caso(2023, 10, 5, 'opendengue_v1_3')]),
      null,
    );
  });

  it('compara con la misma semana del año anterior', () => {
    const r = resumirUltimaSemana([
      caso(2025, 30, 100),
      caso(2026, 29, 90),
      caso(2026, 30, 150),
    ]);
    assert.ok(r);
    assert.strictEqual(r.actual.anio, 2026);
    assert.strictEqual(r.actual.semana_epi, 30);
    assert.strictEqual(r.diferencia, 50);
    assert.strictEqual(r.variacionPct, 50);
  });

  it('deja en null lo comparativo si falta el año anterior', () => {
    const r = resumirUltimaSemana([caso(2026, 5, 10)]);
    assert.ok(r);
    assert.strictEqual(r.mismaSemanaAnioAnterior, null);
    assert.strictEqual(r.diferencia, null);
    assert.strictEqual(r.variacionPct, null);
  });

  it('no interpola la semana 53 que la fuente no publicó', () => {
    const r = resumirUltimaSemana([caso(2025, 52, 40), caso(2026, 53, 60)]);
    assert.ok(r);
    assert.strictEqual(r.mismaSemanaAnioAnterior, null);
  });

  it('sin porcentaje cuando el año anterior fue cero', () => {
    const r = resumirUltimaSemana([caso(2025, 3, 0), caso(2026, 3, 7)]);
    assert.ok(r);
    assert.strictEqual(r.diferencia, 7);
    assert.strictEqual(r.variacionPct, null);
  });

  it('ignora el orden de entrada', () => {
    const r = resumirUltimaSemana([
      caso(2026, 2, 3),
      caso(2025, 2, 1),
      caso(2026, 1, 9),
    ]);
    assert.ok(r);
    assert.strictEqual(r.actual.semana_epi, 2);
  });
});
