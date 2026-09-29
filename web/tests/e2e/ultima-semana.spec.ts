import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const CASOS = [
  {
    semana_inicio: '2025-07-20',
    anio: 2025,
    semana_epi: 30,
    conteo: 100,
    fuente: 'minsal_tablero',
  },
  {
    semana_inicio: '2026-07-19',
    anio: 2026,
    semana_epi: 30,
    conteo: 150,
    fuente: 'minsal_tablero',
  },
];

const NOWCAST = {
  disponible: true,
  aviso: 'x',
  ancla: { fecha: '2026-07-19', anio: 2026, semana: 30, casos: 150 },
  estimacion: [
    {
      h: 1,
      fecha: '2026-07-26',
      anio: 2026,
      semana: 31,
      cuantiles: [],
      mediana: 160,
      banda_50: [140, 180],
      banda_95: [100, 230],
    },
  ],
};

const INTEGRIDAD = {
  aviso: 'x',
  antiguedad: {
    dengue_tablero_nacional: {
      ultima_anio: 2026,
      ultima_semana_epi: 30,
      semanas: 80,
    },
  },
};

test.describe('última semana de dengue', () => {
  test('muestra la última semana, la comparación y la semana siguiente', async ({
    page,
  }) => {
    await page.route('**/api/casos-nacional', (r) =>
      r.fulfill({ json: CASOS }),
    );
    await page.route('**/api/nowcast-dengue', (r) =>
      r.fulfill({ json: NOWCAST }),
    );
    await page.route('**/api/v1/vigilancia/integridad', (r) =>
      r.fulfill({ json: INTEGRIDAD }),
    );
    await page.goto('/dengue');
    const franja = page.locator('#ultima-semana');
    await expect(franja).toContainText('SE30/2026', { timeout: 15_000 });
    await expect(franja).toContainText('150');
    await expect(franja).toContainText('Misma semana de 2025');
    await expect(franja).toContainText('+50 %');
    await expect(franja).toContainText('SE31/2026');
    await expect(franja).toContainText('160');
    const resultados = await new AxeBuilder({ page })
      .include('[data-ultima-semana]')
      .analyze();
    expect(resultados.violations).toEqual([]);
  });

  test('avisa cuando el tablero no trae semanas', async ({ page }) => {
    await page.route('**/api/casos-nacional', (r) => r.fulfill({ json: [] }));
    await page.goto('/dengue');
    await expect(page.locator('#ultima-semana')).toContainText(
      'todavía no tiene semanas',
      { timeout: 15_000 },
    );
  });

  test('ofrece reintentar si la fuente falla', async ({ page }) => {
    await page.route('**/api/casos-nacional', (r) =>
      r.fulfill({ status: 500 }),
    );
    await page.goto('/dengue');
    await expect(
      page
        .locator('#ultima-semana')
        .getByRole('button', { name: /reintentar/i }),
    ).toBeVisible({ timeout: 15_000 });
  });
});

const INSTANTANEA = {
  generado: '2026-07-20',
  casos: [
    {
      semana_inicio: '2025-07-13',
      anio: 2025,
      semana_epi: 29,
      conteo: 90,
      fuente: 'minsal_tablero',
    },
    {
      semana_inicio: '2026-07-12',
      anio: 2026,
      semana_epi: 29,
      conteo: 120,
      fuente: 'minsal_tablero',
    },
  ],
};

// El servidor de desarrollo no toma la copia del build (import.meta.env.DEV);
// aquí se inyecta en el HTML como lo haría un build de producción.
async function conInstantanea(page: import('@playwright/test').Page) {
  await page.route('**/dengue', async (ruta) => {
    const respuesta = await ruta.fetch();
    const html = (await respuesta.text()).replace(
      /(<script[^>]*id="ultima-semana-instantanea"[^>]*>)[^<]*(<\/script>)/,
      `$1${JSON.stringify(INSTANTANEA)}$2`,
    );
    await ruta.fulfill({ response: respuesta, body: html });
  });
}

test('la franja se pinta con la copia del build mientras llega la API', async ({
  page,
}) => {
  await conInstantanea(page);
  await page.route('**/api/casos-nacional', async (ruta) => {
    await new Promise((r) => setTimeout(r, 1500));
    await ruta.fulfill({ json: CASOS });
  });
  await page.route('**/api/nowcast-dengue*', (r) =>
    r.fulfill({ json: NOWCAST }),
  );
  await page.route('**/api/v1/vigilancia/integridad', (r) =>
    r.fulfill({ json: INTEGRIDAD }),
  );
  await page.goto('/dengue');
  const franja = page.locator('#ultima-semana');
  await expect(franja).toContainText('SE29/2026');
  await expect(franja).toContainText('Cifras guardadas al publicar el sitio');
  await expect(franja).toContainText('Actualizando la estimación');
  // Cuando llega la API la copia se reemplaza por la serie vigente.
  await expect(franja).toContainText('SE30/2026');
  await expect(franja).not.toContainText('Cifras guardadas');
});

test('si la API falla se conserva la copia del build con su aviso', async ({
  page,
}) => {
  await conInstantanea(page);
  await page.route('**/api/casos-nacional', (r) =>
    r.fulfill({ status: 500, body: 'error' }),
  );
  await page.route('**/api/nowcast-dengue*', (r) =>
    r.fulfill({ json: NOWCAST }),
  );
  await page.route('**/api/v1/vigilancia/integridad', (r) =>
    r.fulfill({ json: INTEGRIDAD }),
  );
  await page.goto('/dengue');
  const franja = page.locator('#ultima-semana');
  await expect(franja).toContainText('No se pudo actualizar');
  await expect(franja).toContainText('SE29/2026');
});
