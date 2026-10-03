import { expect, test } from '@playwright/test';

// El mapa no debe capturar el scroll de la página ni acercarse hasta perder
// el contexto (MapaIRA.astro, lib/mapa-scroll.ts).
test.describe('mapa: scroll y zoom', () => {
  test('la rueda sin Ctrl desplaza la página y avisa; con Ctrl acerca', async ({
    page,
  }) => {
    await page.goto('/respiratorio');
    const mapa = page.locator(
      '#ira [data-mapa-evento="ira"] .leaflet-container',
    );
    await expect(mapa).toBeVisible({ timeout: 15_000 });
    await mapa.scrollIntoViewIfNeeded();
    const caja = (await mapa.boundingBox())!;
    await page.mouse.move(caja.x + caja.width / 2, caja.y + caja.height / 2);

    const antes = await page.evaluate(() => window.scrollY);
    await page.mouse.wheel(0, 200);
    await expect
      .poll(() => page.evaluate(() => window.scrollY))
      .toBeGreaterThan(antes);
    await expect(mapa.locator('.mapa-pista-scroll')).toHaveClass(/visible/);
    await expect(mapa.locator('.mapa-pista-scroll')).toContainText(/rueda/);
    // La pista no es contenido para lectores de pantalla ni toma el foco.
    await expect(mapa.locator('.mapa-pista-scroll')).toHaveAttribute(
      'aria-hidden',
      'true',
    );

    // Ctrl + rueda sí acerca (el mapa arranca en el zoom mínimo).
    const zoomMas = mapa.locator('.leaflet-control-zoom-in');
    const zoomMenos = mapa.locator('.leaflet-control-zoom-out');
    await expect(zoomMenos).toHaveClass(/leaflet-disabled/);
    await page.keyboard.down('Control');
    await page.mouse.wheel(0, -300);
    await page.keyboard.up('Control');
    await expect(zoomMenos).not.toHaveClass(/leaflet-disabled/);
    await expect(zoomMas).toBeVisible();
  });

  test('el zoom tiene un tope cercano', async ({ page }) => {
    await page.goto('/respiratorio');
    const mapa = page.locator(
      '#ira [data-mapa-evento="ira"] .leaflet-container',
    );
    await expect(mapa).toBeVisible({ timeout: 15_000 });
    const zoomMas = mapa.locator('.leaflet-control-zoom-in');
    // minZoom 8 y maxZoom 10: dos pasos y el botón se desactiva.
    const zoomMenos = mapa.locator('.leaflet-control-zoom-out');
    await zoomMas.click();
    // Leaflet ignora un clic mientras dura la animación del anterior.
    await expect(zoomMenos).not.toHaveClass(/leaflet-disabled/);
    await page.waitForTimeout(500);
    await zoomMas.click();
    await expect(zoomMas).toHaveClass(/leaflet-disabled/);
  });
});
