import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

/** Tarjeta de una opción de radio (el <input> va oculto con sr-only). */
function opcion(page: Page, nombre: string, valor: string) {
  return page.locator(
    `label.opcion-radio:has(input[name="${nombre}"][value="${valor}"])`,
  );
}

function radio(page: Page, nombre: string, valor: string) {
  return page.locator(`input[name="${nombre}"][value="${valor}"]`);
}

test.describe('configuración', () => {
  test('la cabecera y el pie enlazan a /configuracion', async ({ page }) => {
    await page.goto('/');
    await expect(
      page.locator('header').getByRole('link', { name: 'Configuración' }),
    ).toHaveAttribute('href', '/configuracion');
    await expect(
      page.locator('footer').getByRole('link', { name: 'Configuración' }),
    ).toHaveAttribute('href', '/configuracion');
  });

  test('el tema elegido se aplica, se guarda y sincroniza la cabecera', async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/configuracion');
    // Sin elección guardada el tema es claro, aunque el sistema sea oscuro.
    await expect(radio(page, 'tema', 'light')).toBeChecked();
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', /.+/);

    await opcion(page, 'tema', 'dark').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(page.locator('[data-selector-tema]')).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(radio(page, 'tema', 'dark')).toBeChecked();

    // "Sistema" sigue el ajuste del dispositivo (aquí, oscuro).
    await opcion(page, 'tema', 'sistema').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'system');
    expect(await page.evaluate(() => localStorage.getItem('epi:tema'))).toBe(
      'sistema',
    );

    // "Claro" es el valor por defecto: borra la elección guardada.
    await opcion(page, 'tema', 'light').click();
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', /.+/);
    expect(
      await page.evaluate(() => localStorage.getItem('epi:tema')),
    ).toBeNull();
  });

  test('el selector de la cabecera actualiza la página de configuración', async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: 'light' });
    await page.goto('/configuracion');
    await page.locator('[data-selector-tema]').click();
    await expect(radio(page, 'tema', 'dark')).toBeChecked();
  });

  test('las animaciones y el tamaño de texto se guardan y se aplican antes de pintar', async ({
    page,
  }) => {
    await page.emulateMedia({ reducedMotion: 'no-preference' });
    await page.goto('/configuracion');

    await opcion(page, 'animaciones', 'off').click();
    await expect(page.locator('html')).toHaveAttribute(
      'data-animaciones',
      'off',
    );
    await expect(
      page.getByRole('switch', { name: 'Animaciones' }),
    ).toHaveAttribute('aria-checked', 'false');

    await opcion(page, 'texto', 'grande').click();
    await expect(page.locator('html')).toHaveAttribute('data-texto', 'grande');

    await page.reload();
    await expect(page.locator('html')).toHaveAttribute(
      'data-animaciones',
      'off',
    );
    await expect(page.locator('html')).toHaveAttribute('data-texto', 'grande');
    const tamano = await page.evaluate(() =>
      parseFloat(getComputedStyle(document.documentElement).fontSize),
    );
    expect(tamano).toBe(18);

    await opcion(page, 'texto', 'normal').click();
    await expect(page.locator('html')).not.toHaveAttribute('data-texto', /.+/);
  });

  test('el departamento recordado se elige y se olvida', async ({ page }) => {
    await page.goto('/configuracion');
    const select = page.getByLabel('Departamento', { exact: true });
    await select.selectOption('SV-SS');
    expect(
      await page.evaluate(() => localStorage.getItem('epi:departamento')),
    ).toBe('SV-SS');
    await page.reload();
    await expect(page.getByLabel('Departamento', { exact: true })).toHaveValue(
      'SV-SS',
    );
    await page.getByLabel('Departamento', { exact: true }).selectOption('');
    expect(
      await page.evaluate(() => localStorage.getItem('epi:departamento')),
    ).toBeNull();
  });

  test('un atajo se cambia pulsando la combinación y se rechazan las inválidas', async ({
    page,
  }) => {
    await page.goto('/configuracion');
    const fila = page.locator('[data-atajo-fila="biblioteca"]');
    await expect(fila.locator('kbd')).toHaveText('Alt+B');

    await fila.getByRole('button', { name: /Cambiar atajo/ }).click();
    await expect(fila.locator('kbd')).toHaveText('Pulsa una combinación…');

    // Sin modificador: se rechaza y sigue capturando.
    await page.keyboard.press('KeyL');
    await expect(page.locator('[data-estado]')).toContainText(
      'Necesita Ctrl, Alt',
    );
    await expect(fila.locator('kbd')).toHaveText('Pulsa una combinación…');

    // Reservada por el navegador.
    await page.keyboard.press('Control+KeyT');
    await expect(page.locator('[data-estado]')).toContainText(
      'la reserva el navegador',
    );

    // Ya usada por otra acción.
    await page.keyboard.press('Alt+KeyA');
    await expect(page.locator('[data-estado]')).toContainText('ya la usa');

    // Válida: se guarda.
    await page.keyboard.press('Alt+KeyL');
    await expect(fila.locator('kbd')).toHaveText('Alt+L');
    expect(
      JSON.parse(
        (await page.evaluate(() => localStorage.getItem('epi:atajos'))) ?? '{}',
      ),
    ).toEqual({ combos: { biblioteca: 'Alt+L' } });

    // Persiste y el nuevo atajo navega.
    await page.reload();
    await expect(page.locator('[data-atajo-fila="biblioteca"] kbd')).toHaveText(
      'Alt+L',
    );
    await page.locator('h1').first().click();
    await page.keyboard.press('Alt+KeyL');
    await expect(page).toHaveURL(/\/biblioteca\/?$/);
  });

  test('Escape cancela la captura sin cambiar nada', async ({ page }) => {
    await page.goto('/configuracion');
    const fila = page.locator('[data-atajo-fila="inicio"]');
    await fila.getByRole('button', { name: /Cambiar atajo/ }).click();
    await page.keyboard.press('Escape');
    await expect(fila.locator('kbd')).toHaveText('Alt+I');
    expect(
      await page.evaluate(() => localStorage.getItem('epi:atajos')),
    ).toBeNull();
  });

  test('quitar, restablecer y desactivar todos los atajos', async ({
    page,
  }) => {
    await page.goto('/configuracion');
    const fila = page.locator('[data-atajo-fila="inicio"]');
    await fila.getByRole('button', { name: /Quitar atajo/ }).click();
    await expect(fila.locator('kbd')).toHaveText('Sin atajo');
    await expect(
      fila.getByRole('button', { name: /Quitar atajo/ }),
    ).toBeDisabled();

    // Sin atajo, Alt+I ya no navega.
    await page.locator('h1').first().click();
    await page.keyboard.press('Alt+KeyI');
    await expect(page).toHaveURL(/\/configuracion$/);

    await page
      .getByRole('button', { name: 'Restablecer atajos por defecto' })
      .click();
    await expect(fila.locator('kbd')).toHaveText('Alt+I');
    expect(
      await page.evaluate(() => localStorage.getItem('epi:atajos')),
    ).toBeNull();

    const interruptor = page.getByRole('switch', { name: 'Atajos activados' });
    await interruptor.click();
    await expect(interruptor).toHaveAttribute('aria-checked', 'false');
    await page.locator('h1').first().click();
    await page.keyboard.press('Alt+KeyI');
    await expect(page).toHaveURL(/\/configuracion$/);
    await page.reload();
    await expect(
      page.getByRole('switch', { name: 'Atajos activados' }),
    ).toHaveAttribute('aria-checked', 'false');
  });

  test('borrar todas las preferencias vuelve al tema claro', async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem('epi:tema', 'dark');
      localStorage.setItem('epi:texto', 'grande');
      localStorage.setItem('epi:atajos', '{"activos":false}');
      localStorage.setItem('epi:departamento', 'SV-SS');
    });
    await page.goto('/configuracion');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    page.once('dialog', (d) => d.accept());
    await page
      .getByRole('button', { name: 'Borrar todas las preferencias' })
      .click();
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', /.+/);
    await expect(page.locator('html')).not.toHaveAttribute('data-texto', /.+/);
    await expect(
      page.getByRole('switch', { name: 'Atajos activados' }),
    ).toHaveAttribute('aria-checked', 'true');
    const claves = await page.evaluate(() =>
      ['epi:tema', 'epi:texto', 'epi:atajos', 'epi:departamento'].map((k) =>
        localStorage.getItem(k),
      ),
    );
    expect(claves).toEqual([null, null, null, null]);
  });

  for (const esquema of ['light', 'dark'] as const) {
    test(`sin violaciones de axe en tema ${esquema}`, async ({ page }) => {
      await page.emulateMedia({
        colorScheme: esquema,
        reducedMotion: 'reduce',
      });
      await page.addInitScript(
        (tema) => window.localStorage.setItem('epi:tema', tema),
        esquema,
      );
      await page.goto('/configuracion');
      const resultado = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();
      expect(
        resultado.violations.map((v) => ({
          id: v.id,
          nodos: v.nodes.slice(0, 3).map((n) => n.target.join(' ')),
        })),
      ).toEqual([]);
    });
  }

  test('Tab sale de la captura sin guardar nada', async ({ page }) => {
    await page.goto('/configuracion');
    const fila = page.locator('[data-atajo-fila="inicio"]');
    await fila.getByRole('button', { name: /Cambiar atajo/ }).click();
    await expect(fila.locator('kbd')).toHaveText('Pulsa una combinación…');
    await page.keyboard.press('Tab');
    await expect(fila.locator('kbd')).toHaveText('Alt+I');
    expect(
      await page.evaluate(() => localStorage.getItem('epi:atajos')),
    ).toBeNull();
  });

  test('perder el foco cancela la captura', async ({ page }) => {
    await page.goto('/configuracion');
    const fila = page.locator('[data-atajo-fila="inicio"]');
    await fila.getByRole('button', { name: /Cambiar atajo/ }).click();
    await page.locator('h1').first().click();
    await expect(fila.locator('kbd')).toHaveText('Alt+I');
    await page.keyboard.press('Alt+KeyX');
    expect(
      await page.evaluate(() => localStorage.getItem('epi:atajos')),
    ).toBeNull();
  });

  test('rechaza una combinación del navegador como Ctrl+C', async ({
    page,
  }) => {
    await page.goto('/configuracion');
    const fila = page.locator('[data-atajo-fila="inicio"]');
    await fila.getByRole('button', { name: /Cambiar atajo/ }).click();
    await page.keyboard.press('Control+KeyC');
    await expect(fila.locator('kbd')).toHaveText('Pulsa una combinación…');
    await expect(page.getByRole('status').first()).toContainText('reserva');
  });
});
