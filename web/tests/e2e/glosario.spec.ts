import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { GLOSARIO } from '../../src/lib/glosario.ts';

test('cada entrada del glosario apunta a un ancla que existe', async ({
  page,
}) => {
  for (const entrada of GLOSARIO) {
    const [ruta, ancla] = entrada.enlace.split('#');
    const respuesta = await page.goto(ruta);
    expect(respuesta?.status(), entrada.clave).toBe(200);
    await expect(
      page.locator(`[id="${ancla}"]`),
      `${entrada.clave}: falta #${ancla}`,
    ).toHaveCount(1);
  }
});

test('el botón de ayuda abre y cierra la definición', async ({ page }) => {
  await page.goto('/respiratorio');
  const ayuda = page.locator('[data-ayuda-termino="positividad"]').first();
  const boton = ayuda.getByRole('button', { name: /positividad/i });
  await expect(boton).toBeVisible();
  const caja = await boton.boundingBox();
  expect(caja?.width).toBeGreaterThanOrEqual(44);
  await boton.click();
  await expect(ayuda.locator('[popover]')).toBeVisible();
  await expect(ayuda.locator('[popover]')).toContainText('muestras');
  await page.keyboard.press('Escape');
  await expect(ayuda.locator('[popover]')).toBeHidden();
});

test('la portada de respiratorio con ayudas no tiene violaciones WCAG A y AA', async ({
  page,
}) => {
  await page.goto('/respiratorio');
  const resultados = await new AxeBuilder({ page })
    .include('[data-ayuda-termino]')
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();
  expect(resultados.violations).toEqual([]);
});
