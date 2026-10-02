import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test.describe('atajos de teclado', () => {
  test('Ctrl+E lleva al inicio y Alt+B a la biblioteca', async ({ page }) => {
    await page.goto('/contacto');
    await page.locator('h1').first().click();
    await page.keyboard.press('Alt+KeyB');
    await expect(page).toHaveURL(/\/biblioteca\/?$/);
    await page.locator('h1').first().click();
    await page.keyboard.press('Control+KeyE');
    await expect(page).toHaveURL(/\/$/);
  });

  test('las demás acciones de navegación responden', async ({ page }) => {
    const casos: [string, RegExp][] = [
      ['Alt+KeyA', /\/alertas\/?$/],
      ['Alt+KeyN', /\/analisis\/?$/],
      ['Alt+KeyS', /\/sugerencias\/?$/],
      ['Alt+KeyC', /\/configuracion\/?$/],
    ];
    await page.goto('/contacto');
    for (const [tecla, destino] of casos) {
      await page.locator('h1').first().click();
      await page.keyboard.press(tecla);
      await expect(page).toHaveURL(destino);
    }
  });

  test('alternan tema y animaciones y sincronizan sus controles', async ({
    page,
  }) => {
    await page.emulateMedia({
      colorScheme: 'light',
      reducedMotion: 'no-preference',
    });
    await page.goto('/contacto');
    await page.locator('h1').first().click();
    await page.keyboard.press('Alt+KeyT');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(page.locator('[data-selector-tema]')).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    await page.keyboard.press('Alt+KeyM');
    await expect(page.locator('html')).toHaveAttribute(
      'data-animaciones',
      'off',
    );
    await expect(
      page.getByRole('switch', { name: 'Animaciones' }),
    ).toHaveAttribute('aria-checked', 'false');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(page.locator('html')).toHaveAttribute(
      'data-animaciones',
      'off',
    );
  });

  test('la ayuda lista los atajos vigentes y se cierra con Escape', async ({
    page,
  }) => {
    await page.addInitScript(() =>
      localStorage.setItem('epi:atajos', '{"combos":{"inicio":"Alt+I"}}'),
    );
    await page.goto('/contacto');
    await page.locator('h1').first().click();
    await page.keyboard.press('Alt+KeyH');
    const dialogo = page.getByRole('dialog', { name: 'Atajos de teclado' });
    await expect(dialogo).toBeVisible();
    await expect(dialogo.locator('[data-atajo-combo="inicio"]')).toHaveText(
      'Alt+I',
    );
    await expect(dialogo.locator('[data-atajo-combo="biblioteca"]')).toHaveText(
      'Alt+B',
    );
    await expect(
      dialogo.getByRole('link', { name: 'Configuración' }),
    ).toHaveAttribute('href', '/configuracion');
    const resultado = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    expect(resultado.violations).toEqual([]);
    await page.keyboard.press('Escape');
    await expect(dialogo).toBeHidden();
  });

  test('no se disparan mientras se escribe en un campo', async ({ page }) => {
    await page.goto('/biblioteca/05-sensibilidad-y-honestidad');
    await page.locator('input[type="search"]').first().click();
    await page.keyboard.press('Control+KeyE');
    await page.keyboard.press('Alt+KeyA');
    await expect(page).toHaveURL(/\/biblioteca\/05-sensibilidad-y-honestidad/);
  });

  test('un atajo guardado inválido se ignora y vale el valor por defecto', async ({
    page,
  }) => {
    await page.addInitScript(() =>
      localStorage.setItem('epi:atajos', '{"combos":{"biblioteca":"Ctrl+T"}}'),
    );
    await page.goto('/contacto');
    await page.locator('h1').first().click();
    await page.keyboard.press('Alt+KeyB');
    await expect(page).toHaveURL(/\/biblioteca\/?$/);
  });

  test('las páginas incrustadas no cargan atajos', async ({ page }) => {
    await page.goto('/incrustar/ultima-semana');
    await expect(page.locator('#atajos-ayuda')).toHaveCount(0);
  });
});
