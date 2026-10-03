import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  EJEMPLO_ANTIGUEDAD,
  EJEMPLO_BOLETIN,
  EJEMPLO_FALTANTES,
  N_DEPARTAMENTOS,
  SEMANAS_NOMINALES,
  antiguedadSerie,
  completitudAnual,
  completitudSemana,
  cuadreBoletin,
  discrepancia,
  estadoIntegridad,
  semanaEpidemiologica,
  semanasDelAnio,
  type Antiguedad,
  type Boletin,
  type CompletitudAnual,
  type CompletitudSemana,
  type CuadreBoletin,
} from '../../src/lib/integridad.ts';
import { DEPARTAMENTOS } from '../../src/lib/departamentos.ts';

// Valores generados con el Python del backend (ver el encabezado de
// src/lib/integridad.ts).
const referencia = JSON.parse(
  readFileSync(
    new URL('./fixtures/fichas-m4-referencia.json', import.meta.url),
    'utf8',
  ),
) as {
  catalogo: [string, string][];
  completitud_semana: { presentes: string[]; resultado: CompletitudSemana }[];
  completitud_anual: {
    semanas_n: Record<string, number>;
    resultado: CompletitudAnual;
  }[];
  cuadre: { boletin: Boletin | null; resultado: CuadreBoletin }[];
  discrepancia: {
    suma: number | null;
    publicado: number | null;
    resultado: number | null;
  }[];
  antiguedad: {
    ultima: [number, number] | null;
    hoy: string;
    resultado: Antiguedad;
  }[];
  constantes: { n_departamentos: number; semanas_nominales: number };
};

test('constantes y catálogo coinciden con el backend', () => {
  assert.equal(N_DEPARTAMENTOS, referencia.constantes.n_departamentos);
  assert.equal(SEMANAS_NOMINALES, referencia.constantes.semanas_nominales);
  assert.deepEqual(
    DEPARTAMENTOS.map((d) => [d.codigo, d.nombre]),
    referencia.catalogo,
  );
});

test('completitud de una semana', () => {
  assert.equal(referencia.completitud_semana.length, 10);
  for (const c of referencia.completitud_semana) {
    assert.deepEqual(
      completitudSemana(referencia.catalogo, c.presentes),
      c.resultado,
      `presentes ${c.presentes.join(',')}`,
    );
  }
});

test('completitud anual: una semana ausente es un hueco, no 0 de 14', () => {
  assert.equal(referencia.completitud_anual.length, 13);
  for (const c of referencia.completitud_anual) {
    assert.deepEqual(completitudAnual(c.semanas_n), c.resultado);
  }
  assert.deepEqual(completitudAnual({ 1: 14, 2: 0 }), {
    semanas_completas: 1,
    semanas_con_dato: 2,
    semanas_nominales: 52,
  });
});

test('cuadre del boletín y diferencia', () => {
  assert.equal(referencia.cuadre.length, 6);
  for (const c of referencia.cuadre) {
    assert.deepEqual(cuadreBoletin(c.boletin), c.resultado);
  }
  assert.equal(referencia.discrepancia.length, 7);
  for (const c of referencia.discrepancia) {
    assert.equal(discrepancia(c.suma, c.publicado), c.resultado);
  }
});

test('antigüedad en semanas epidemiológicas, con cambios de año y semanas 53', () => {
  assert.equal(referencia.antiguedad.length, 49);
  for (const c of referencia.antiguedad) {
    assert.deepEqual(
      antiguedadSerie(c.ultima, c.hoy),
      c.resultado,
      `${JSON.stringify(c.ultima)} visto desde ${c.hoy}`,
    );
  }
});

test('calendario epidemiológico: domingo a sábado y semana 1 con cuatro días', () => {
  // 2023 empieza en domingo: el 1 de enero abre la semana 1.
  assert.deepEqual(semanaEpidemiologica('2023-01-01'), {
    anio: 2023,
    semana: 1,
  });
  assert.deepEqual(semanaEpidemiologica('2022-12-31'), {
    anio: 2022,
    semana: 52,
  });
  // 2026 empieza en jueves: del 28 de diciembre al 3 de enero es la 53 de 2025.
  assert.deepEqual(semanaEpidemiologica('2025-12-28'), {
    anio: 2025,
    semana: 53,
  });
  assert.deepEqual(semanaEpidemiologica('2026-01-03'), {
    anio: 2025,
    semana: 53,
  });
  assert.deepEqual(semanaEpidemiologica('2026-01-04'), {
    anio: 2026,
    semana: 1,
  });
  // 2021 empieza en viernes: el 1 de enero es de la semana 53 de 2020.
  assert.deepEqual(semanaEpidemiologica('2021-01-01'), {
    anio: 2020,
    semana: 53,
  });
  assert.deepEqual(semanaEpidemiologica('2021-01-03'), {
    anio: 2021,
    semana: 1,
  });
  // 2024 empieza en lunes: el 31 de diciembre de 2023 ya es la semana 1.
  assert.deepEqual(semanaEpidemiologica('2023-12-31'), {
    anio: 2024,
    semana: 1,
  });
  // Un sábado cierra su semana.
  assert.deepEqual(semanaEpidemiologica('2026-10-03'), {
    anio: 2026,
    semana: 39,
  });
  assert.deepEqual(semanaEpidemiologica('2026-10-04'), {
    anio: 2026,
    semana: 40,
  });
  assert.equal(semanasDelAnio(2020), 53);
  assert.equal(semanasDelAnio(2025), 53);
  assert.equal(semanasDelAnio(2023), 52);
  assert.equal(semanasDelAnio(2024), 52);
});

test('acepta una Date con el día local', () => {
  assert.deepEqual(
    semanaEpidemiologica(new Date(2026, 9, 2, 23, 30)),
    semanaEpidemiologica('2026-10-02'),
  );
});

test('estado del departamento en el mapa', () => {
  assert.equal(estadoIntegridad(false, true), 'sin_dato');
  assert.equal(estadoIntegridad(false, false), 'sin_dato');
  assert.equal(estadoIntegridad(true, true), 'presente');
  assert.equal(estadoIntegridad(true, null), 'presente');
  assert.equal(estadoIntegridad(true, undefined), 'presente');
  assert.equal(estadoIntegridad(true, false), 'no_cuadra');
});

test('el ejemplo de la ficha', () => {
  const presentes = DEPARTAMENTOS.map((d) => d.codigo).filter(
    (c) => !(EJEMPLO_FALTANTES as readonly string[]).includes(c),
  );
  const c = completitudSemana(referencia.catalogo, presentes);
  assert.equal(c.n, 11);
  const cuadre = cuadreBoletin(EJEMPLO_BOLETIN);
  assert.equal(cuadre.probable.discrepancia, -5);
  assert.equal(cuadre.confirmado.discrepancia, 0);
  const a = antiguedadSerie(EJEMPLO_ANTIGUEDAD.ultima, EJEMPLO_ANTIGUEDAD.hoy);
  assert.equal(a.semanas, 144);
});
