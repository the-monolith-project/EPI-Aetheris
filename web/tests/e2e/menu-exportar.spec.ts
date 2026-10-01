import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const casos = Array.from({ length: 30 }, (_, i) => ({
  anio: 2025,
  semana_epi: i + 1,
  semana_inicio: '2025-01-05',
  conteo: 100 + i,
  fuente: 'minsal_tablero',
}));

async function abrirCurva(page: import('@playwright/test').Page) {
  await page.route('**/api/casos-nacional*', (r) => r.fulfill({ json: casos }));
  await page.goto('/dengue');
  const curva = page.locator('section:has(#curva-epidemica)');
  await expect(curva.locator('#curva-epidemica svg').first()).toBeVisible();
  return curva;
}

test('la curva nacional reúne CSV, SVG, PNG e incrustar bajo «Exportar»', async ({
  page,
}) => {
  const curva = await abrirCurva(page);
  const boton = curva.getByRole('button', { name: 'Exportar' });
  await expect(boton).toHaveAttribute('aria-expanded', 'false');
  // Ya no quedan botones de descarga sueltos en la sección.
  await expect(curva.getByRole('button', { name: /^Descargar/ })).toHaveCount(
    0,
  );

  await boton.click();
  await expect(boton).toHaveAttribute('aria-expanded', 'true');
  const opciones = curva.getByRole('menuitem');
  await expect(opciones).toHaveText([
    'Datos (CSV)',
    'Imagen vectorial (SVG)',
    'Imagen (PNG)',
    'Copiar código para incrustar',
  ]);
  // Cada opción lleva su icono.
  await expect(curva.locator('[role="menuitem"] svg')).toHaveCount(4);
});

test('las opciones del menú descargan los archivos y copian el código', async ({
  page,
  context,
}) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  const curva = await abrirCurva(page);
  const boton = curva.getByRole('button', { name: 'Exportar' });

  await boton.click();
  const [csv] = await Promise.all([
    page.waitForEvent('download'),
    curva.getByRole('menuitem', { name: 'Datos (CSV)' }).click(),
  ]);
  expect(csv.suggestedFilename()).toMatch(
    /^epi-aetheris-dengue-nacional-.*\.csv$/,
  );

  await boton.click();
  const [svg] = await Promise.all([
    page.waitForEvent('download'),
    curva.getByRole('menuitem', { name: /SVG/ }).click(),
  ]);
  expect(svg.suggestedFilename()).toMatch(/\.svg$/);

  await boton.click();
  await curva.getByRole('menuitem', { name: /incrustar/ }).click();
  const texto = await page.evaluate(() => navigator.clipboard.readText());
  expect(texto).toMatch(
    /^<iframe src="https:\/\/epi-aetheris\.dev\/incrustar\/curva-nacional"/,
  );
  await expect(curva.locator('[data-menu-exportar-estado]')).toContainText(
    'copiado',
  );
});

test('el menú se maneja con el teclado y se cierra con Escape', async ({
  page,
}) => {
  const curva = await abrirCurva(page);
  const boton = curva.getByRole('button', { name: 'Exportar' });
  await boton.focus();
  await page.keyboard.press('ArrowDown');
  await expect(
    curva.getByRole('menuitem', { name: 'Datos (CSV)' }),
  ).toBeFocused();
  await page.keyboard.press('ArrowDown');
  await expect(curva.getByRole('menuitem', { name: /SVG/ })).toBeFocused();
  await page.keyboard.press('End');
  await expect(
    curva.getByRole('menuitem', { name: /incrustar/ }),
  ).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(boton).toHaveAttribute('aria-expanded', 'false');
  await expect(boton).toBeFocused();
});

test('el menú abierto no presenta violaciones WCAG A y AA', async ({
  page,
}) => {
  const curva = await abrirCurva(page);
  await curva.getByRole('button', { name: 'Exportar' }).click();
  const resultados = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .include('section:has(#curva-epidemica)')
    .analyze();
  expect(resultados.violations).toEqual([]);
});
