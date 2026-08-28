import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const URL_INICIAL =
  '/dengue?year=2023&week=1&fromWeek=1&toWeek=53&serie=probable&minsal=semana';

async function esperarPanel(page: import('@playwright/test').Page) {
  await expect(page.locator('#analisis-filtros-estado')).toContainText(
    '14 departamentos',
  );
  await expect(page.locator('#scatter-resumen')).not.toContainText('Cargando');
  await expect(page.locator('#mapa-aviso')).not.toBeEmpty();
}

async function abrirFiltros(page: import('@playwright/test').Page) {
  await page.locator('#analisis-abrir-filtros').click();
  await expect(page.locator('#analisis-filtros-drawer')).toBeVisible();
}

test('sincroniza filtros, mapa, scatter, departamento, heatmap y serie', async ({
  page,
}) => {
  await page.goto(URL_INICIAL);
  await esperarPanel(page);
  await abrirFiltros(page);

  await page.locator('#analisis-anio').selectOption('2022');
  await expect(page).toHaveURL(/year=2022/);
  await expect(page.locator('#scatter-resumen')).toContainText('2022 · SE01');

  await page.locator('#analisis-semana').fill('31');
  await expect(page.locator('#analisis-semana-valor')).toHaveText('SE31');
  await expect(page).toHaveURL(/week=31/);
  await expect(page.locator('#mapa-aviso')).toContainText(
    'semana seleccionada',
  );
  await expect(page.locator('#scatter-resumen')).toContainText('2022 · SE31');
  await page.locator('#analisis-cerrar-filtros').click();

  const sanSalvador = page.locator('[data-departamento="SV-SS"]').first();
  await expect(sanSalvador).toHaveAttribute(
    'aria-label',
    'Seleccionar San Salvador',
  );
  await sanSalvador.focus();
  await sanSalvador.press('Enter');
  await expect(page.locator('#analisis-departamento')).toHaveValue('SV-SS');
  await expect(page).toHaveURL(/dept=SV-SS/);
  await expect(page.locator('#comparacion-resumen')).toContainText(
    'San Salvador',
  );

  const celdaHeatmap = page
    .locator(
      '.epi-heatmap-celdas rect[aria-label*="Ahuachapán"][aria-label*="SE12"]',
    )
    .first();
  await celdaHeatmap.click();
  await expect(page.locator('#analisis-departamento')).toHaveValue('SV-AH');
  await expect(page.locator('#analisis-semana')).toHaveValue('12');
  await expect(page).toHaveURL(/week=12/);
  await expect(page).toHaveURL(/dept=SV-AH/);

  await abrirFiltros(page);
  await page
    .locator('input[name="analisis-serie"][value="confirmado"]')
    .check();
  await expect(page).toHaveURL(/serie=confirmado/);
  await expect(page.locator('#heatmap-resumen')).toContainText('confirmado');
  await expect(page.locator('#scatter-resumen')).toContainText(
    'Percentil presión (confirmado)',
  );
});

test('restaura la URL, limita la comparación y exporta el filtro actual', async ({
  page,
}) => {
  await page.goto(
    '/dengue?year=2019&week=24&fromWeek=10&toWeek=30&dept=SV-LI&serie=confirmado&compare=SV-LI%2CSV-SS&minsal=ytd',
  );
  await esperarPanel(page);
  await abrirFiltros(page);

  await expect(page.locator('#analisis-anio')).toHaveValue('2019');
  await expect(page.locator('#analisis-semana')).toHaveValue('24');
  await expect(page.locator('#analisis-desde')).toHaveValue('10');
  await expect(page.locator('#analisis-hasta')).toHaveValue('30');
  await expect(page.locator('#analisis-departamento')).toHaveValue('SV-LI');
  await expect(page.locator('#analisis-modo-minsal')).toHaveValue('ytd');
  await expect(page.locator('#mapa-aviso')).toContainText(
    'entre SE01 y la semana seleccionada',
  );

  const comparar = page.locator('#analisis-comparar');
  await comparar.selectOption(['SV-AH', 'SV-CA', 'SV-CH', 'SV-CU', 'SV-LI']);
  const seleccionados = await comparar.evaluate((select: HTMLSelectElement) =>
    [...select.selectedOptions].map((opcion) => opcion.value),
  );
  expect(seleccionados).toEqual(['SV-AH', 'SV-CA', 'SV-CH', 'SV-CU']);
  await expect(page.locator('#analisis-comparar-ayuda')).toContainText(
    '4 de 4 seleccionados',
  );
  await expect(
    page.locator('#comparacion-departamentos-resumen'),
  ).toContainText('Ahuachapán');

  const descargaPendiente = page.waitForEvent('download');
  await page.locator('#analisis-exportar').click();
  const descarga = await descargaPendiente;
  expect(descarga.suggestedFilename()).toContain(
    'epi-aetheris-dengue-2019-confirmado-se10-se30',
  );
  const ruta = await descarga.path();
  expect(ruta).not.toBeNull();
  const csv = await readFile(ruta!, 'utf8');
  const filas = csv.trim().split('\n');
  expect(filas).toHaveLength(85);
  expect(filas[0]).toContain('casos_observados');
  expect(new Set(filas.slice(1).map((fila) => fila.split(',')[2]))).toEqual(
    new Set(['SV-AH', 'SV-CA', 'SV-CH', 'SV-CU']),
  );

  await page.reload();
  await esperarPanel(page);
  await expect(page.locator('#analisis-comparar-ayuda')).toContainText(
    '4 de 4 seleccionados',
  );
  await expect(page.locator('#analisis-modo-minsal')).toHaveValue('ytd');
});

test('aplica vistas del workspace sin alterar los filtros epidemiológicos', async ({
  page,
}) => {
  await page.goto(URL_INICIAL);
  await esperarPanel(page);
  await abrirFiltros(page);

  await expect(page.locator('[data-panel-workspace="mapa"]')).toBeVisible();
  await expect(
    page.locator('[data-panel-workspace="calendario"]'),
  ).toBeHidden();
  await page.locator('#analisis-cerrar-filtros').click();

  await page.locator('#analisis-vista').selectOption('temporal');
  await expect(page.locator('[data-panel-workspace="mapa"]')).toBeHidden();
  await expect(
    page.locator('[data-panel-workspace="temporadas"]'),
  ).toBeVisible();
  await expect(
    page.locator('[data-panel-workspace="calendario"]'),
  ).toBeVisible();

  await page.locator('#analisis-semana').fill('31');
  await expect(page).toHaveURL(/week=31/);
  await page.locator('#analisis-restablecer-vista').click();
  await expect(page.locator('#analisis-vista')).toHaveValue('general');
  await expect(page.locator('[data-panel-workspace="mapa"]')).toBeVisible();
  await expect(
    page.locator('[data-panel-workspace="calendario"]'),
  ).toBeHidden();
  await expect(page.locator('#analisis-semana')).toHaveValue('31');
});

test('muestra y oculta paneles sin modificar el filtro activo', async ({
  page,
}) => {
  await page.goto(URL_INICIAL);
  await esperarPanel(page);
  await abrirFiltros(page);

  await page.locator('#analisis-semana').fill('27');
  await page.locator('#analisis-cerrar-filtros').click();
  await page.locator('#analisis-paneles-boton').click();
  await expect(page.locator('#analisis-paneles-boton')).toHaveAttribute(
    'aria-expanded',
    'true',
  );
  const mapa = page.locator('input[data-selector-panel][value="mapa"]');
  await expect(mapa).toBeChecked();
  await mapa.uncheck();
  await expect(page.locator('[data-panel-workspace="mapa"]')).toBeHidden();
  await expect(page.locator('[data-panel-workspace="presion"]')).toBeVisible();
  await expect(page.locator('#analisis-semana')).toHaveValue('27');

  await page.keyboard.press('Escape');
  await expect(page.locator('#analisis-paneles-boton')).toHaveAttribute(
    'aria-expanded',
    'false',
  );
});

test('limpia los filtros desde el drawer sin restablecer la vista', async ({
  page,
}) => {
  await page.goto(URL_INICIAL);
  await esperarPanel(page);
  await page.locator('#analisis-vista').selectOption('temporal');
  await abrirFiltros(page);

  await page.locator('#analisis-anio').selectOption('2022');
  await page.locator('#analisis-semana').fill('31');
  await page.locator('#analisis-limpiar-filtros').click();
  await expect(page.locator('#analisis-anio')).toHaveValue('2023');
  await expect(page.locator('#analisis-semana')).toHaveValue('1');
  await expect(page.locator('#analisis-desde')).toHaveValue('1');
  await expect(page.locator('#analisis-hasta')).toHaveValue('53');
  await expect(page.locator('#analisis-vista')).toHaveValue('temporal');

  await page.keyboard.press('Escape');
  await expect(page.locator('#analisis-filtros-drawer')).toBeHidden();
  await expect(page.locator('#analisis-abrir-filtros')).toHaveAttribute(
    'aria-expanded',
    'false',
  );
});

test('la vista dengue no presenta violaciones automáticas WCAG A o AA', async ({
  page,
}) => {
  await page.goto(
    '/dengue?year=2023&week=1&fromWeek=1&toWeek=20&dept=SV-SS&serie=probable&minsal=semana',
  );
  await esperarPanel(page);
  await expect(page.locator('#perfil-calidad-estado')).toContainText(
    'San Salvador',
  );

  const resultados = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(resultados.violations).toEqual([]);
});
