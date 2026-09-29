import { expect, test } from '@playwright/test';

test('al imprimir /dengue se ocultan los controles y aparece la cabecera con los filtros', async ({
  page,
}) => {
  await page.goto('/dengue?year=2022&serie=confirmado&dept=SV-SS');
  await expect(page.locator('[data-cabecera-impresion]')).toBeHidden();
  await page.emulateMedia({ media: 'print' });
  const cabecera = page.locator('[data-cabecera-impresion]');
  await expect(cabecera).toBeVisible();
  await expect(cabecera).toContainText('año 2022');
  await expect(cabecera).toContainText('serie confirmado');
  await expect(page.locator('[data-tabs]')).toBeHidden();
  await expect(page.locator('#toolbar-analisis-contenedor')).toBeHidden();
  await expect(page.locator('body > header')).toBeHidden();
  await expect(page.locator('body > footer')).toBeHidden();
});
