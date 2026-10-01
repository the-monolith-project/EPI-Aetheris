import { expect, test } from '@playwright/test';

const RUTAS = ['/dengue', '/respiratorio', '/departamento/SV-SS', '/alertas'];

for (const ancho of [375, 768]) {
  for (const ruta of RUTAS) {
    test(`${ruta} no desborda horizontalmente a ${ancho} px`, async ({
      page,
    }) => {
      await page.setViewportSize({ width: ancho, height: 800 });
      await page.goto(ruta);
      await page.waitForLoadState('networkidle');
      const desborde = await page.evaluate(
        () =>
          document.documentElement.scrollWidth -
          document.documentElement.clientWidth,
      );
      expect(desborde).toBeLessThanOrEqual(0);
    });
  }
}

test('en teléfono el workspace muestra un panel a la vez', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto('/dengue');
  const selector = page.locator('[data-selector-movil]');
  await expect(selector).toBeVisible();
  const botones = selector.locator('button');
  await expect(botones).toHaveCount(4);
  await expect(botones.first()).toHaveAttribute('aria-pressed', 'true');
  await expect(
    page.locator('[data-panel-workspace]:not([hidden])'),
  ).toHaveCount(1);
  await expect(page.locator('[data-panel-workspace="mapa"]')).toBeVisible();

  await selector.locator('[data-panel-movil="temporadas"]').click();
  await expect(
    page.locator('[data-panel-workspace]:not([hidden])'),
  ).toHaveCount(1);
  await expect(
    page.locator('[data-panel-workspace="temporadas"]'),
  ).toBeVisible();
  await expect(page.locator('[data-panel-workspace="mapa"]')).toBeHidden();
  await expect(page.locator('#analisis-zoom-mas')).toBeHidden();
});

test('en escritorio el selector móvil no aparece y los paneles conviven', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto('/dengue');
  await expect(page.locator('[data-selector-movil]')).toBeHidden();
  expect(
    await page.locator('[data-panel-workspace]:not([hidden])').count(),
  ).toBeGreaterThan(1);
  await expect(page.locator('#analisis-zoom-mas')).toBeVisible();
});

test('/dengue enlaza a la predicción y no la repite', async ({ page }) => {
  await page.goto('/dengue');
  await expect(page.locator('[data-enlace-prediccion]')).toHaveAttribute(
    'href',
    '/prediccion',
  );
  await expect(page.locator('[data-nowcast]')).toHaveCount(0);
  await expect(page.locator('[data-contraste-nowcast]')).toHaveCount(0);
  await expect(page.locator('[data-tabs]')).toHaveCount(0);
  await expect(page.locator('#curva')).toHaveCount(1);
});

test('/dengue muestra la última semana publicada sin la semana siguiente', async ({
  page,
}) => {
  await page.goto('/dengue');
  const franja = page.locator('[data-franja-ultima-semana] #ultima-semana');
  await expect(franja).toHaveCount(1);
  await expect(franja).not.toContainText('Semana siguiente');
});
