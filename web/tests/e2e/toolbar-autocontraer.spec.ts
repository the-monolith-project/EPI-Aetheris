import { expect, test } from '@playwright/test';

const URL_INICIAL =
  '/dengue?year=2023&week=1&fromWeek=1&toWeek=53&serie=probable&minsal=semana';

// La barra del análisis se contrae sola a los 5 s sin actividad, salvo con
// "Mantener visible" (ToolbarAnalisis.astro). Estos tests arrancan sin la
// clave que la configuración global deja puesta.
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('barra del análisis: contracción automática', () => {
  test('se contrae sola sin actividad y el botón la vuelve a abrir', async ({
    page,
  }) => {
    await page.goto(URL_INICIAL);
    const boton = page.locator('#toolbar-analisis-contraer');
    await expect(boton).toHaveAttribute('aria-expanded', 'true');
    await expect(boton).toHaveAttribute('aria-expanded', 'false', {
      timeout: 9_000,
    });
    await expect(page.locator('#toolbar-analisis-resumen')).toBeVisible();

    await boton.click();
    await expect(boton).toHaveAttribute('aria-expanded', 'true');
  });

  test('la actividad reinicia la cuenta atrás', async ({ page }) => {
    await page.goto(URL_INICIAL);
    const boton = page.locator('#toolbar-analisis-contraer');
    const barra = page.locator('#toolbar-analisis');
    const caja = (await barra.boundingBox())!;
    // Seis segundos moviendo el puntero sobre la barra: pasa el plazo de 5 s
    // sin que se contraiga.
    for (let i = 0; i < 12; i++) {
      await page.mouse.move(caja.x + 20 + i, caja.y + caja.height / 2);
      await page.waitForTimeout(500);
    }
    await expect(boton).toHaveAttribute('aria-expanded', 'true');
  });

  test('"Mantener visible" la deja abierta y se recuerda', async ({ page }) => {
    await page.goto(URL_INICIAL);
    const casilla = page.getByLabel('Mantener visible');
    await casilla.check();
    await page.waitForTimeout(6_500);
    await expect(page.locator('#toolbar-analisis-contraer')).toHaveAttribute(
      'aria-expanded',
      'true',
    );
    await page.reload();
    await expect(page.getByLabel('Mantener visible')).toBeChecked();
    // Desmarcarla devuelve el comportamiento automático.
    await page.getByLabel('Mantener visible').uncheck();
    await expect(page.locator('#toolbar-analisis-contraer')).toHaveAttribute(
      'aria-expanded',
      'false',
      { timeout: 9_000 },
    );
  });
});
