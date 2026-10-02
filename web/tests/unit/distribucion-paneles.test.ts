import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  COLUMNAS_MD,
  COLUMNAS_XL,
  TODAS_LAS_CLASES_COL_SPAN,
  clasesColumnas,
  distribuirColumnas,
  distribuirPaneles,
} from '../../src/lib/distribucion-paneles.ts';
import type { PanelDistribuible } from '../../src/lib/distribucion-paneles.ts';
import {
  PANELES_ANALITICOS,
  aplicarVistaAnalisis,
  obtenerLayoutAnalisis,
  restablecerLayoutAnalisis,
} from '../../src/lib/analisis-layout-state.ts';
import type {
  PanelAnalitico,
  VistaAnalisis,
} from '../../src/lib/analisis-layout-state.ts';

/** Orden del DOM en PanelAnalisis.astro, que es el que sigue la cuadrícula. */
const ORDEN_DOM: PanelAnalitico[] = PANELES_ANALITICOS.map(({ id }) => id);

function panelesDePreset(
  vista: VistaAnalisis,
): PanelDistribuible<PanelAnalitico>[] {
  restablecerLayoutAnalisis();
  const layout = aplicarVistaAnalisis(vista);
  return ORDEN_DOM.filter((id) => layout.panelesVisibles.includes(id)).map(
    (id) => ({ id, tamano: layout.tamanos[id] }),
  );
}

/** Suma de cada fila simulada: todas deben llenar las 12 columnas. */
function filas(anchos: number[], capacidad = 12): number[][] {
  const resultado: number[][] = [];
  let fila: number[] = [];
  let ocupado = 0;
  for (const ancho of anchos) {
    if (ocupado + ancho > capacidad) {
      resultado.push(fila);
      fila = [];
      ocupado = 0;
    }
    fila.push(ancho);
    ocupado += ancho;
  }
  resultado.push(fila);
  return resultado;
}

function sumaPorFila(anchos: number[]): number[] {
  return filas(anchos).map((fila) => fila.reduce((a, b) => a + b, 0));
}

describe('distribuirColumnas', () => {
  it('un panel único ocupa la fila completa', () => {
    assert.deepEqual(
      distribuirColumnas([{ id: 'canal', tamano: 'grande' }], COLUMNAS_XL),
      [12],
    );
    assert.deepEqual(
      distribuirColumnas([{ id: 'mapa', tamano: 'pequeno' }], COLUMNAS_XL),
      [12],
    );
  });

  it('el huérfano al final de fila se ensancha a 12', () => {
    const anchos = distribuirColumnas(
      [
        { id: 'a', tamano: 'grande' },
        { id: 'b', tamano: 'grande' },
        { id: 'c', tamano: 'grande' },
      ],
      COLUMNAS_XL,
    );
    assert.deepEqual(anchos, [6, 6, 12]);
  });

  it('reparte el sobrante de una en una empezando por el primero', () => {
    assert.deepEqual(
      distribuirColumnas(
        [
          { id: 'a', tamano: 'pequeno' },
          { id: 'b', tamano: 'pequeno' },
          { id: 'c', tamano: 'pequeno' },
        ],
        COLUMNAS_XL,
      ),
      [4, 4, 4],
    );
    assert.deepEqual(
      distribuirColumnas(
        [
          { id: 'a', tamano: 'mediano' },
          { id: 'b', tamano: 'mediano' },
          { id: 'c', tamano: 'pequeno' },
        ],
        COLUMNAS_XL,
      ),
      [5, 4, 3],
    );
  });

  it('una fila ya completa no cambia', () => {
    assert.deepEqual(
      distribuirColumnas(
        [
          { id: 'a', tamano: 'grande' },
          { id: 'b', tamano: 'grande' },
        ],
        COLUMNAS_XL,
      ),
      [6, 6],
    );
  });

  it('el panel en foco ocupa su propia fila completa', () => {
    const anchos = distribuirColumnas(
      [
        { id: 'a', tamano: 'mediano' },
        { id: 'b', tamano: 'grande', enFoco: true },
        { id: 'c', tamano: 'grande' },
      ],
      COLUMNAS_XL,
    );
    assert.deepEqual(anchos, [12, 12, 12]);
  });

  it('sin paneles devuelve una lista vacía', () => {
    assert.deepEqual(distribuirColumnas([], COLUMNAS_XL), []);
  });

  it('respeta una capacidad distinta de 12', () => {
    assert.deepEqual(
      distribuirColumnas(
        [
          { id: 'a', tamano: 'mediano' },
          { id: 'b', tamano: 'mediano' },
        ],
        COLUMNAS_XL,
        6,
      ),
      [6, 6],
    );
  });
});

describe('presets del espacio de análisis', () => {
  it('Clima: mapa 5 y clima 7', () => {
    const anchos = distribuirColumnas(panelesDePreset('clima'), COLUMNAS_XL);
    assert.deepEqual(anchos, [5, 7]);
  });

  it('Calidad: disponibilidad 7 y calidad 5', () => {
    const anchos = distribuirColumnas(panelesDePreset('calidad'), COLUMNAS_XL);
    assert.deepEqual(anchos, [7, 5]);
  });

  it('Territorial: 6 + 6 y departamentos a 12', () => {
    const anchos = distribuirColumnas(
      panelesDePreset('territorial'),
      COLUMNAS_XL,
    );
    assert.deepEqual(anchos, [6, 6, 12]);
  });

  it('Temporal: dos filas de 6 + 6', () => {
    const anchos = distribuirColumnas(panelesDePreset('temporal'), COLUMNAS_XL);
    assert.deepEqual(anchos, [6, 6, 6, 6]);
  });

  it('General sin la composición optimizada: mapa 5, presión 7 y 6 + 6', () => {
    const anchos = distribuirColumnas(panelesDePreset('general'), COLUMNAS_XL);
    assert.deepEqual(anchos, [5, 7, 6, 6]);
  });

  it('todos los paneles visibles llenan cada fila en xl y en md', () => {
    restablecerLayoutAnalisis();
    const layout = obtenerLayoutAnalisis();
    const todos = ORDEN_DOM.map((id) => ({ id, tamano: layout.tamanos[id] }));
    for (const columnas of [COLUMNAS_XL, COLUMNAS_MD]) {
      const anchos = distribuirColumnas(todos, columnas);
      assert.equal(anchos.length, todos.length);
      for (const suma of sumaPorFila(anchos)) assert.equal(suma, 12);
    }
    assert.deepEqual(
      distribuirColumnas(todos, COLUMNAS_XL),
      [5, 7, 6, 6, 6, 6, 6, 6, 7, 5],
    );
  });

  it('en md los grandes van a fila completa y los demás de dos en dos', () => {
    assert.deepEqual(
      distribuirColumnas(panelesDePreset('clima'), COLUMNAS_MD),
      [12, 12],
    );
    assert.deepEqual(
      distribuirColumnas(
        [
          { id: 'a', tamano: 'mediano' },
          { id: 'b', tamano: 'pequeno' },
          { id: 'c', tamano: 'grande' },
        ],
        COLUMNAS_MD,
      ),
      [6, 6, 12],
    );
  });
});

describe('distribuirPaneles y clasesColumnas', () => {
  it('devuelve md y xl por identificador', () => {
    const resultado = distribuirPaneles(panelesDePreset('calidad'));
    assert.deepEqual(resultado, {
      disponibilidad: { md: 12, xl: 7 },
      calidad: { md: 12, xl: 5 },
    });
  });

  it('las clases coinciden con las columnas y están en la lista de limpieza', () => {
    const clases = clasesColumnas({ md: 6, xl: 5 });
    assert.deepEqual(clases, ['md:col-span-6', 'xl:col-span-5']);
    for (const clase of clases) {
      assert.ok(TODAS_LAS_CLASES_COL_SPAN.includes(clase));
    }
    assert.equal(TODAS_LAS_CLASES_COL_SPAN.length, 24);
  });
});
