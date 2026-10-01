import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const PAGINAS = [
  '/',
  '/alertas',
  '/respiratorio',
  '/biblioteca',
  '/estado',
  '/analisis',
  '/departamento/SV-SS',
  '/dengue',
  '/prediccion',
];

test.describe('tema oscuro', () => {
  test('sigue al sistema y cambia el fondo', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/');
    await expect(page.locator('body')).toHaveCSS(
      'background-color',
      'rgb(14, 20, 18)',
    );
  });

  test('el selector alterna, recuerda la elección y la aplica antes de pintar', async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: 'light' });
    await page.goto('/');
    const boton = page.locator('[data-selector-tema]');
    await expect(boton).toHaveAttribute('aria-pressed', 'false');
    await boton.click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await expect(boton).toHaveAttribute('aria-pressed', 'true');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    await boton.click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  });

  test('una elección clara manda sobre un sistema oscuro', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.addInitScript(() =>
      window.localStorage.setItem('epi:tema', 'light'),
    );
    await page.goto('/');
    await expect(page.locator('body')).toHaveCSS(
      'background-color',
      'rgb(240, 240, 240)',
    );
  });

  test('sin almacenamiento el selector sigue funcionando en la visita', async ({
    page,
  }) => {
    await page.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', {
        get() {
          throw new Error('bloqueado');
        },
      });
    });
    await page.goto('/');
    await page.locator('[data-selector-tema]').click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  });

  for (const ruta of PAGINAS) {
    test(`${ruta} no presenta violaciones WCAG A y AA en oscuro`, async ({
      page,
    }) => {
      // Sin movimiento: axe medía el contraste a mitad de la animación de entrada.
      await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
      await page.goto(ruta);
      await page.waitForLoadState('load');
      // Los cargadores atenuados de una recarga no son el estado final: con
      // una API lenta axe los medía a media carga.
      await expect(page.locator('.ea-comet-cargador:visible')).toHaveCount(0, {
        timeout: 20_000,
      });
      const resultados = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();
      expect(
        resultados.violations.map((v) => ({
          id: v.id,
          nodos: v.nodes.slice(0, 3).map((n) => n.target.join(' ')),
        })),
      ).toEqual([]);
    });
  }

  test('#toolbar-analisis cumple contraste y accesibilidad WCAG A y AA en oscuro', async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
    await page.goto('/dengue');
    await page.waitForLoadState('load');
    await expect(page.locator('#toolbar-analisis')).toBeVisible();
    const resultados = await new AxeBuilder({ page })
      .include('#toolbar-analisis')
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();
    expect(
      resultados.violations.map((v) => ({
        id: v.id,
        nodos: v.nodes.map((n) => n.target.join(' ')),
      })),
    ).toEqual([]);
  });
});
