import { readFile } from 'node:fs/promises';

import { expect, test } from '@playwright/test';

test.describe('observatorio respiratorio', () => {
  test('carga IRA, Neumonías, virus y cobertura sin lenguaje de riesgo/causalidad', async ({
    page,
  }) => {
    await page.goto('/respiratorio');
    await expect(page.getByRole('heading', { name: /Observatorio respiratorio/i })).toBeVisible();
    await expect(page.locator('body')).not.toContainText('La Influenza causó');
    await expect(page.locator('main')).toContainText('sin predicción');

    const cobertura = page.locator('[data-cobertura]');
    await expect(cobertura).toContainText('MINSAL', { timeout: 15_000 });
    await expect(cobertura).toContainText('Neumonías');
    await expect(cobertura).not.toContainText('score de riesgo');

    await expect(page.locator('#ira [data-mapa-evento="ira"]')).toBeVisible();
    await expect(page.locator('#neumonias [data-mapa-evento="neumonias"]')).toBeVisible();

    const heatmap = page.locator('[data-heatmap-neu]');
    await expect(heatmap.locator('table')).toBeVisible({ timeout: 20_000 });
    await expect(heatmap).toContainText('San Salvador');
    await expect(heatmap).toContainText(/conteo notificado/i);

    await heatmap.locator('[data-hm-anio]').selectOption('2019');
    await expect(heatmap.locator('table')).toBeVisible();

    const virus = page.locator('[data-panel-virus]');
    await expect(virus).toContainText('nacional');
    await expect(virus.locator('table')).toBeVisible({ timeout: 20_000 });
  });

  test('/ira redirige al observatorio y la curva admite año y rango SE', async ({ page }) => {
    await page.goto('/ira');
    await expect(page).toHaveURL(/\/respiratorio/);
    const curva = page.locator('#neumonias [data-curva-evento="neumonias"]');
    // Neumonías sí está cargada en esta base; IRA puede estar vacía.
    await expect(curva.locator('svg')).toBeVisible({ timeout: 20_000 });
    await curva.locator('[data-curva-anio]').selectOption('2023');
    await expect(curva.locator('svg')).toBeVisible();
    await curva.locator('[data-curva-desde]').fill('10');
    await curva.locator('[data-curva-hasta]').fill('20');
    await expect(curva.locator('[data-curva-rango]')).toHaveText(/SE10–SE20/);
  });

  test('el CSV del heatmap respeta el rango SE seleccionado', async ({ page }) => {
    await page.goto('/respiratorio');
    const heatmap = page.locator('[data-heatmap-neu]');
    await expect(heatmap.locator('table')).toBeVisible({ timeout: 20_000 });
    await heatmap.locator('[data-hm-desde]').fill('10');
    await heatmap.locator('[data-hm-hasta]').fill('20');
    await expect(heatmap.locator('[data-hm-rango]')).toHaveText(/SE10–SE20/);

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      heatmap.getByRole('button', { name: /Exportar CSV/i }).click(),
    ]);
    const tmp = test.info().outputPath('neumonias-heatmap.csv');
    await download.saveAs(tmp);
    const contenido = await readFile(tmp, 'utf8');
    const semanas = contenido
      .trim()
      .split('\n')
      .slice(1)
      .map((linea) => Number(linea.split(',')[3]));
    expect(semanas.length).toBeGreaterThan(0);
    expect(Math.min(...semanas)).toBe(10);
    expect(Math.max(...semanas)).toBe(20);
    expect(semanas.every((s) => s >= 10 && s <= 20)).toBe(true);
    expect(contenido).not.toMatch(/,9,/);
    expect(contenido).not.toMatch(/,21,/);
  });

  test('muestras analizadas usa vigilancia total y no muestra toggles de virus', async ({
    page,
  }) => {
    await page.goto('/respiratorio');
    const virus = page.locator('[data-panel-virus]');
    await expect(virus.locator('table')).toBeVisible({ timeout: 20_000 });
    await virus.locator('[data-virus-metrica]').selectOption('muestras_analizadas');
    await expect(virus.locator('[data-virus-global]')).toBeVisible();
    await expect(virus.locator('[data-virus-global]')).toContainText(
      'Todos los virus / vigilancia total',
    );
    await expect(virus.locator('[data-virus-toggles]')).toBeHidden();
    await expect(virus.locator('table')).toBeVisible();
    await expect(virus.locator('table')).toContainText('Todos los virus / vigilancia total');
  });

  test('si la API de cobertura falla, el panel no inventa cifras', async ({ page }) => {
    await page.route('**/api/respiratorios/cobertura', (route) =>
      route.fulfill({ status: 500, body: 'error' }),
    );
    await page.goto('/respiratorio');
    await expect(page.locator('[data-cob-error]')).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('[data-cob-error]')).toContainText('No se pudo cargar');
  });
});
