import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  SEMANA_MS,
  coberturaDe,
  conHuecos,
  etiquetaAbanico,
  filasAbanico,
  marcaTiempo,
  prepararAbanico,
  recortarAbanico,
  resumenAbanico,
} from '../../src/lib/nowcast-datos.ts';
import type { DatosAbanico } from '../../src/lib/nowcast-datos.ts';
import {
  SEMANAS_VISTA,
  opcionAbanico,
} from '../../src/lib/nowcast-opciones.ts';
import type { TokensGrafico } from '../../src/lib/echarts-tema.ts';

const tokens: TokensGrafico = {
  tinta: '#000000',
  tintaSuave: '#444444',
  borde: '#dddddd',
  superficie: '#ffffff',
  acento: '#183e39',
  secundario: '#dddbff',
  seleccion: '#aabbcc',
  estimacion: '#1f5fb4',
  fuente: 'monospace',
  fuenteTexto: 'sans-serif',
};

function datosAbanico(semanasObservadas = 20): DatosAbanico {
  const inicio = marcaTiempo('2026-01-04');
  const observado = Array.from({ length: semanasObservadas }, (_, i) => {
    const t = inicio + i * SEMANA_MS;
    return {
      t,
      fecha: new Date(t).toISOString().slice(0, 10),
      casos: 100 + i,
    };
  });
  const ultima = observado[observado.length - 1];
  return {
    observado,
    ancla: {
      t: ultima.t,
      fecha: ultima.fecha,
      anio: 2026,
      semana: semanasObservadas,
      casos: ultima.casos ?? 0,
    },
    prediccion: [1, 2, 3].map((h) => {
      const t = ultima.t + h * SEMANA_MS;
      return {
        h,
        t,
        fecha: new Date(t).toISOString().slice(0, 10),
        semana: semanasObservadas + h,
        mediana: 120 + h,
        b50: [110, 130 + h] as [number, number],
        b95: [90, 150 + 10 * h] as [number, number],
      };
    }),
  };
}

test('coberturaDe separa rango del 50 %, del 95 % y fuera', () => {
  const b50: [number, number] = [90, 110];
  const b95: [number, number] = [70, 130];
  assert.equal(coberturaDe(100, b50, b95), 'rango 50 %');
  assert.equal(coberturaDe(120, b50, b95), 'rango 95 %');
  assert.equal(coberturaDe(200, b50, b95), 'fuera');
  assert.equal(coberturaDe(90, b50, b95), 'rango 50 %');
});

test('conHuecos corta la línea donde faltan semanas', () => {
  const t0 = marcaTiempo('2026-01-04');
  const puntos = conHuecos(
    [{ t: t0 }, { t: t0 + SEMANA_MS }, { t: t0 + 5 * SEMANA_MS }],
    () => 1,
  );
  assert.equal(puntos.length, 4);
  assert.equal(puntos[2][1], null);
  assert.equal(puntos[3][0], t0 + 5 * SEMANA_MS);
});

test('prepararAbanico devuelve null si falta algo de lo necesario', () => {
  assert.equal(prepararAbanico({ disponible: true } as never), null);
});

test('recortarAbanico conserva la predicción y acorta lo observado', () => {
  const datos = datosAbanico(30);
  const corto = recortarAbanico(datos, 13);
  assert.equal(corto.observado.length, 13);
  assert.equal(corto.prediccion.length, 3);
  assert.equal(recortarAbanico(datos, null), datos);
  assert.equal(recortarAbanico(datos, 100), datos);
});

test('el resumen y la etiqueta incluyen cifras y el rango del 95 %', () => {
  const datos = datosAbanico();
  const resumen = resumenAbanico(datos);
  assert.match(resumen, /la mediana de la predicción es 121 casos/);
  assert.match(resumen, /El rango del 95 % a 3 semanas va de 90 a 180 casos/);
  assert.match(etiquetaAbanico(datos), /predicción de 1 a 3 semanas/);
});

test('filasAbanico lista primero la predicción y luego lo publicado', () => {
  const filas = filasAbanico(datosAbanico(5));
  assert.equal(filas.length, 3 + 5);
  assert.equal(filas[0].tipo, 'Predicción');
  assert.equal(filas[3].tipo, 'Publicado');
  assert.equal(filas[3].rango50, '—');
});

test('opcionAbanico arma las series y respeta la leyenda', () => {
  const datos = datosAbanico();
  const opcion = opcionAbanico(tokens, recortarAbanico(datos, 13), {
    movil: false,
    vista: 'cerca',
    visibles: {},
    revelado: true,
  }) as {
    series: { name?: string }[];
    aria?: { label?: { enabled?: boolean } };
  };
  const nombres = opcion.series.map((s) => s.name);
  assert.ok(nombres.includes('Casos publicados'));
  assert.ok(nombres.includes('Mediana de la predicción'));
  assert.ok(nombres.includes('Rango 50 %'));
  assert.ok(nombres.includes('Rango 95 %'));
  assert.equal(opcion.aria?.label?.enabled, false);
  assert.equal(SEMANAS_VISTA.cerca, 13);
});

test('sin revelar no se dibuja ninguna zona de predicción', () => {
  const opcion = opcionAbanico(tokens, datosAbanico(), {
    movil: true,
    vista: 'anio',
    visibles: {},
    revelado: false,
  }) as {
    series: { id?: string; markArea?: { data: unknown[] } }[];
  };
  const marcas = opcion.series.find((s) => s.id === 'marcas');
  assert.deepEqual(marcas?.markArea?.data, []);
});
