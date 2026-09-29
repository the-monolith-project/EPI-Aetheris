import { describe, it } from 'node:test';
import assert from 'node:assert';
import {
  alertaAplicaA,
  esAlertaNacional,
  textoAlcance,
} from '../../src/lib/alcance-alertas.ts';

describe('alcance de alertas', () => {
  it('sin campo, null o lista vacía es nacional', () => {
    assert.ok(esAlertaNacional({}));
    assert.ok(esAlertaNacional({ departamentos: null }));
    assert.ok(esAlertaNacional({ departamentos: [] }));
  });

  it('una nacional aplica a cualquier departamento', () => {
    assert.ok(alertaAplicaA({ departamentos: null }, 'SV-SS'));
  });

  it('una regional aplica solo a los que lista', () => {
    const alerta = { departamentos: ['SV-SS', 'SV-LI'] };
    assert.ok(alertaAplicaA(alerta, 'SV-LI'));
    assert.ok(!alertaAplicaA(alerta, 'SV-SA'));
  });

  it('textoAlcance nombra los departamentos y conserva códigos desconocidos', () => {
    assert.strictEqual(textoAlcance({ departamentos: null }), 'Nacional');
    assert.strictEqual(
      textoAlcance({ departamentos: ['SV-SS', 'SV-LI'] }),
      'San Salvador, La Libertad',
    );
    assert.strictEqual(textoAlcance({ departamentos: ['SV-XX'] }), 'SV-XX');
  });
});
