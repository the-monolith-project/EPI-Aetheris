import { expect, test } from '@playwright/test';

test.describe('observatorio respiratorio', () => {
  test('carga IRA, Neumonías, virus y cobertura sin lenguaje de riesgo/causalidad', async ({
    page,
  }) => {
    await page.goto('/respiratorio');
    await expect(page.getByRole('heading', { name: /Observatorio respiratorio/i })).toBeVisible();
    await expect(page.locator('body')).not.toContainText('La Influenza causó');
    await expect(page.locator('header').first()).toContainText('sin predicción');

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

  test('si la API de cobertura falla, el panel no inventa cifras', async ({ page }) => {
    await page.route('**/api/respiratorios/cobertura', (route) =>
      route.fulfill({ status: 500, body: 'error' }),
    );
    await page.goto('/respiratorio');
    await expect(page.locator('[data-cob-error]')).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('[data-cob-error]')).toContainText('No se pudo cargar');
  });
});
