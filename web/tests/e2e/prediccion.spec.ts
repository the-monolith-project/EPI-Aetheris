import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('/prediccion tiene su propia página dentro de Análisis', async ({
  page,
}) => {
  await page.goto('/prediccion');
  await expect(
    page.getByRole('heading', {
      level: 1,
      name: 'Predicción de dengue a corto plazo',
    }),
  ).toBeVisible();
  await expect(page.locator('[data-nowcast]')).toHaveCount(1);
  await expect(page.locator('[data-contraste-nowcast]')).toHaveCount(1);
  await expect(
    page.locator(
      'nav[aria-label="Navegación principal"] a[aria-current="page"]',
    ),
  ).toHaveText('Análisis');
  const resultados = await new AxeBuilder({ page })
    .include('main')
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();
  expect(resultados.violations).toEqual([]);
});

test('el enlace antiguo /dengue?t=prediccion lleva a /prediccion', async ({
  page,
}) => {
  await page.goto('/dengue?t=prediccion');
  await page.waitForURL('**/prediccion');
  await expect(page.locator('[data-nowcast]')).toHaveCount(1);
});

test('/analisis ofrece la tarjeta de la predicción', async ({ page }) => {
  await page.goto('/analisis');
  await expect(page.locator('[data-herramienta="/prediccion"]')).toBeVisible();
});
