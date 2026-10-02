import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ATAJOS,
  accionConCombo,
  accionParaPulsacion,
  comboDePulsacion,
  combosPorDefecto,
  esObjetivoEditable,
  esPlataformaMac,
  etiquetaCombo,
  formatearCombo,
  parsearCombo,
  resolverAtajos,
  serializarAtajos,
  validarCombo,
  type PulsacionLike,
} from '../../src/lib/atajos.ts';

function pulsacion(parcial: Partial<PulsacionLike>): PulsacionLike {
  return {
    code: '',
    key: '',
    ctrlKey: false,
    altKey: false,
    shiftKey: false,
    metaKey: false,
    ...parcial,
  };
}

test('los atajos por defecto son válidos y no se repiten', () => {
  const vistos = new Set<string>();
  for (const a of ATAJOS) {
    assert.equal(validarCombo(a.porDefecto), null, a.accion);
    assert.ok(!vistos.has(a.porDefecto), `repetido: ${a.porDefecto}`);
    vistos.add(a.porDefecto);
  }
  assert.equal(combosPorDefecto().inicio, 'Alt+I');
  assert.equal(combosPorDefecto().biblioteca, 'Alt+B');
});

test('la tecla sale del código físico, no del carácter', () => {
  // Alt+B en macOS trae key '∫'; el código sigue siendo KeyB.
  const c = comboDePulsacion(
    pulsacion({ code: 'KeyB', key: '∫', altKey: true }),
  );
  assert.ok(c);
  assert.equal(formatearCombo(c), 'Alt+B');
  assert.equal(
    formatearCombo(
      comboDePulsacion(pulsacion({ code: 'KeyE', key: 'e', ctrlKey: true }))!,
    ),
    'Ctrl+E',
  );
  assert.equal(
    formatearCombo(comboDePulsacion(pulsacion({ code: 'Digit3', key: '3' }))!),
    '3',
  );
  assert.equal(
    formatearCombo(comboDePulsacion(pulsacion({ code: 'F2', key: 'F2' }))!),
    'F2',
  );
});

test('solo modificadores, Escape o Enter no forman combo', () => {
  assert.equal(
    comboDePulsacion(
      pulsacion({ code: 'ControlLeft', key: 'Control', ctrlKey: true }),
    ),
    null,
  );
  assert.equal(
    comboDePulsacion(pulsacion({ code: 'Escape', key: 'Escape' })),
    null,
  );
  assert.equal(
    comboDePulsacion(pulsacion({ code: 'Enter', key: 'Enter' })),
    null,
  );
  assert.equal(comboDePulsacion(pulsacion({ code: 'Space', key: ' ' })), null);
});

test('formatear y parsear son inversos y el orden de modificadores es fijo', () => {
  const c = comboDePulsacion(
    pulsacion({
      code: 'KeyK',
      key: 'k',
      shiftKey: true,
      ctrlKey: true,
      metaKey: true,
    }),
  )!;
  assert.equal(formatearCombo(c), 'Ctrl+Shift+Meta+K');
  assert.deepEqual(parsearCombo('Ctrl+Shift+Meta+K'), c);
  // Orden no canónico, modificador repetido o tecla rara: inválidos.
  assert.equal(parsearCombo('Shift+Ctrl+K'), null);
  assert.equal(parsearCombo('Ctrl+Ctrl+K'), null);
  assert.equal(parsearCombo('Ctrl+Enter'), null);
  assert.equal(parsearCombo('ctrl+k'), null);
  assert.equal(parsearCombo(''), null);
});

test('validar exige un modificador real y rechaza lo reservado', () => {
  assert.equal(validarCombo('Alt+I'), null);
  assert.equal(validarCombo('F2'), null);
  assert.equal(validarCombo('Alt+Shift+B'), null);
  assert.equal(validarCombo('B'), 'sin-modificador');
  assert.equal(validarCombo('Shift+B'), 'sin-modificador');
  assert.equal(validarCombo('Ctrl+T'), 'reservado');
  assert.equal(validarCombo('Meta+Q'), 'reservado');
  assert.equal(validarCombo('F11'), 'reservado');
  // Copiar, buscar, recargar, la barra de direcciones y el cambio de pestaña
  // no pueden ser atajos del sitio.
  for (const combo of [
    'Ctrl+C',
    'Ctrl+E',
    'Ctrl+F',
    'Meta+V',
    'Alt+D',
    'Alt+3',
    'F5',
    'F1',
  ]) {
    assert.equal(validarCombo(combo), 'reservado', combo);
  }
  assert.equal(validarCombo('lo que sea'), 'mal-formado');
});

test('etiquetaCombo nombra Meta según la plataforma', () => {
  assert.equal(etiquetaCombo('Meta+K', true), 'Cmd+K');
  assert.equal(etiquetaCombo('Meta+K', false), 'Win+K');
  assert.equal(etiquetaCombo('Alt+I', true), 'Alt+I');
});

test('resolver: sin nada guardado, todo por defecto y activo', () => {
  const r = resolverAtajos(null);
  assert.equal(r.activos, true);
  assert.deepEqual(r.combos, combosPorDefecto());
});

test('resolver: lo guardado pisa el valor por defecto, lo inválido se ignora', () => {
  const r = resolverAtajos(
    JSON.stringify({
      activos: false,
      combos: {
        inicio: 'Alt+Shift+I',
        biblioteca: null,
        dengue: 'Ctrl+T', // reservado: se ignora
        tema: 'B', // sin modificador: se ignora
        inventada: 'Alt+Z', // acción desconocida: se ignora
      },
    }),
  );
  assert.equal(r.activos, false);
  assert.equal(r.combos.inicio, 'Alt+Shift+I');
  assert.equal(r.combos.biblioteca, null);
  assert.equal(r.combos.dengue, 'Alt+G');
  assert.equal(r.combos.tema, 'Alt+T');
  assert.ok(!('inventada' in r.combos));
});

test('resolver: JSON roto o de otro tipo vuelve a los valores por defecto', () => {
  assert.deepEqual(resolverAtajos('{no es json'), resolverAtajos(null));
  assert.deepEqual(resolverAtajos('42'), resolverAtajos(null));
  assert.deepEqual(resolverAtajos('null'), resolverAtajos(null));
});

test('serializar guarda solo las diferencias y null cuando no hay ninguna', () => {
  const config = resolverAtajos(null);
  assert.equal(serializarAtajos(config), null);
  config.combos.inicio = 'Alt+Shift+I';
  config.combos.ayuda = null;
  assert.deepEqual(JSON.parse(serializarAtajos(config)!), {
    combos: { inicio: 'Alt+Shift+I', ayuda: null },
  });
  config.activos = false;
  assert.deepEqual(JSON.parse(serializarAtajos(config)!), {
    activos: false,
    combos: { inicio: 'Alt+Shift+I', ayuda: null },
  });
  // Ida y vuelta.
  assert.deepEqual(resolverAtajos(serializarAtajos(config)), config);
});

test('accionConCombo detecta choques y respeta la excepción', () => {
  const combos = combosPorDefecto();
  assert.equal(accionConCombo(combos, 'Alt+B'), 'biblioteca');
  assert.equal(accionConCombo(combos, 'Alt+B', 'biblioteca'), null);
  assert.equal(accionConCombo(combos, 'Alt+Z'), null);
});

test('accionParaPulsacion casa la pulsación con la acción configurada', () => {
  const config = resolverAtajos(null);
  assert.equal(
    accionParaPulsacion(
      config,
      pulsacion({ code: 'KeyI', key: 'i', altKey: true }),
    ),
    'inicio',
  );
  assert.equal(
    accionParaPulsacion(
      config,
      pulsacion({ code: 'KeyB', key: 'b', altKey: true }),
    ),
    'biblioteca',
  );
  // Un modificador de más no casa.
  assert.equal(
    accionParaPulsacion(
      config,
      pulsacion({ code: 'KeyB', key: 'b', altKey: true, shiftKey: true }),
    ),
    null,
  );
  // Sin modificador no casa con nada.
  assert.equal(
    accionParaPulsacion(config, pulsacion({ code: 'KeyB', key: 'b' })),
    null,
  );
  // Desactivados: nada.
  config.activos = false;
  assert.equal(
    accionParaPulsacion(
      config,
      pulsacion({ code: 'KeyE', key: 'e', ctrlKey: true }),
    ),
    null,
  );
});

test('esObjetivoEditable distingue campos de texto de botones', () => {
  const el = (tagName: string, tipo?: string, editable = false) => ({
    tagName,
    isContentEditable: editable,
    getAttribute: (n: string) => (n === 'type' ? (tipo ?? null) : null),
  });
  assert.equal(esObjetivoEditable(el('INPUT')), true);
  assert.equal(esObjetivoEditable(el('INPUT', 'search')), true);
  assert.equal(esObjetivoEditable(el('TEXTAREA')), true);
  assert.equal(esObjetivoEditable(el('SELECT')), true);
  assert.equal(esObjetivoEditable(el('DIV', undefined, true)), true);
  assert.equal(esObjetivoEditable(el('INPUT', 'checkbox')), false);
  assert.equal(esObjetivoEditable(el('INPUT', 'radio')), false);
  assert.equal(esObjetivoEditable(el('BUTTON')), false);
  assert.equal(esObjetivoEditable(el('A')), false);
  assert.equal(esObjetivoEditable(null), false);
});

test('esPlataformaMac lee el userAgent', () => {
  assert.equal(
    esPlataformaMac({ userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X)' }),
    true,
  );
  assert.equal(
    esPlataformaMac({ userAgent: 'Mozilla/5.0 (X11; Linux)' }),
    false,
  );
  assert.equal(esPlataformaMac({}), false);
});
