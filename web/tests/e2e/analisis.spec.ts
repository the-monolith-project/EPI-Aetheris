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
  await expect(page.locator('#analisis-filtros-popover')).not.toHaveAttribute(
    'hidden',
  );
  await expect(page.locator('#analisis-filtros-dialogo')).toBeVisible();
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
  await expect(page.locator('#comparacion-temporadas-grafica')).toBeVisible();

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
    'suma de las observaciones',
  );

  const comparar = page.locator('input[name="analisis-comparar"]');
  await page
    .locator('input[name="analisis-comparar"][value="SV-LI"]')
    .uncheck();
  await page
    .locator('input[name="analisis-comparar"][value="SV-SS"]')
    .uncheck();
  for (const codigo of ['SV-AH', 'SV-CA', 'SV-CH', 'SV-CU']) {
    await page
      .locator(`input[name="analisis-comparar"][value="${codigo}"]`)
      .check();
  }
  const seleccionados = await comparar.evaluateAll((casillas) =>
    casillas
      .filter((casilla) => (casilla as HTMLInputElement).checked)
      .map((casilla) => (casilla as HTMLInputElement).value),
  );
  expect(seleccionados).toEqual(['SV-AH', 'SV-CA', 'SV-CH', 'SV-CU']);
  await expect(
    page.locator('input[name="analisis-comparar"][value="SV-LI"]'),
  ).toBeDisabled();
  await expect(page.locator('#analisis-comparar-ayuda')).toContainText(
    '4 de 4 seleccionados',
  );
  await expect(
    page.locator('#comparacion-departamentos-resumen'),
  ).toContainText('Ahuachapán');
  await expect(
    page.locator('#comparacion-departamentos-grafica'),
  ).toBeVisible();

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

  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.locator('#analisis-copiar-enlace').click();
  await expect(page.locator('#analisis-acciones-estado')).toContainText(
    'Enlace reproducible copiado',
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

  await abrirFiltros(page);
  await page.locator('#analisis-semana').fill('31');
  await expect(page).toHaveURL(/week=31/);
  await page.locator('#analisis-cerrar-filtros').click();
  await page.locator('#analisis-restablecer-vista').click();
  await expect(page.locator('#analisis-vista')).toHaveValue('general');
  await expect(page.locator('[data-panel-workspace="mapa"]')).toBeVisible();
  await expect(
    page.locator('[data-panel-workspace="calendario"]'),
  ).toBeHidden();
  await expect(page.locator('#analisis-semana')).toHaveValue('31');
});

test('optimiza la vista general y conserva el layout responsive', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto(URL_INICIAL);
  await esperarPanel(page);

  const workspace = page.locator('#analisis');
  const columnaMapa = page.locator('[data-columna-workspace="mapa"]');
  const columnaAnalisis = page.locator('[data-columna-workspace="analisis"]');
  const mapa = page.locator('[data-panel-workspace="mapa"]');
  const presion = page.locator('[data-panel-workspace="presion"]');
  const temporadas = page.locator('[data-panel-workspace="temporadas"]');

  await expect(columnaMapa).toHaveClass(/xl:col-span-4/);
  await expect(columnaAnalisis).toHaveClass(/xl:col-span-8/);
  await expect(page.locator('#comparacion-temporadas-grafica')).toBeHidden();
  await expect(page.locator('#comparacion-departamentos-grafica')).toBeHidden();

  const cajas = await Promise.all([
    workspace.boundingBox(),
    mapa.boundingBox(),
    presion.boundingBox(),
    temporadas.boundingBox(),
  ]);
  const [cajaWorkspace, cajaMapa, cajaPresion, cajaTemporadas] = cajas;
  expect(cajaWorkspace).not.toBeNull();
  expect(cajaMapa).not.toBeNull();
  expect(cajaPresion).not.toBeNull();
  expect(cajaTemporadas).not.toBeNull();
  expect(cajaWorkspace!.width).toBeGreaterThan(1750);
  expect(cajaMapa!.width / cajaWorkspace!.width).toBeGreaterThan(0.3);
  expect(cajaMapa!.width / cajaWorkspace!.width).toBeLessThan(0.35);
  expect(cajaPresion!.x).toBeGreaterThan(cajaMapa!.x + cajaMapa!.width);
  expect(cajaTemporadas!.y).toBeGreaterThan(cajaPresion!.y);
  expect(cajaTemporadas!.y).toBeLessThan(cajaMapa!.y + cajaMapa!.height);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);

  await page.setViewportSize({ width: 390, height: 844 });
  const cajasMoviles = await Promise.all([
    workspace.boundingBox(),
    mapa.boundingBox(),
    presion.boundingBox(),
  ]);
  expect(cajasMoviles[0]).not.toBeNull();
  expect(cajasMoviles[1]).not.toBeNull();
  expect(cajasMoviles[2]).not.toBeNull();
  expect(cajasMoviles[0]!.x).toBeGreaterThanOrEqual(0);
  expect(cajasMoviles[0]!.x + cajasMoviles[0]!.width).toBeLessThanOrEqual(390);
  expect(cajasMoviles[2]!.y).toBeGreaterThan(
    cajasMoviles[1]!.y + cajasMoviles[1]!.height,
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await expect(page.locator('#heatmap-departamentos').locator('..')).toHaveCSS(
    'overflow-x',
    'auto',
  );
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

test('limpia los filtros desde el popover sin restablecer la vista', async ({
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
  await expect(page.locator('#analisis-filtros-popover')).toHaveAttribute(
    'hidden',
  );
  await expect(page.locator('#analisis-abrir-filtros')).toHaveAttribute(
    'aria-expanded',
    'false',
  );
  await expect(page.locator('#analisis-abrir-filtros')).toBeFocused();
});

test('integra el popover con el toolbar y permite cerrarlo', async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(URL_INICIAL);
  await esperarPanel(page);
  await abrirFiltros(page);

  const popover = page.locator('#analisis-filtros-popover');
  const dialogo = page.locator('#analisis-filtros-dialogo');
  const toolbar = page.locator('#toolbar-analisis');
  const mapa = page.locator('[data-panel-workspace="mapa"]');
  await expect(mapa).toBeVisible();
  await expect(page.locator('#analisis-filtros-fondo')).toBeHidden();
  await expect(dialogo).not.toHaveAttribute('aria-modal', 'true');
  await expect(page.locator('main')).toHaveJSProperty('inert', false);

  const [cajaDialogo, cajaToolbar] = await Promise.all([
    dialogo.boundingBox(),
    toolbar.boundingBox(),
  ]);
  expect(cajaDialogo).not.toBeNull();
  expect(cajaToolbar).not.toBeNull();
  expect(cajaDialogo!.width).toBeGreaterThanOrEqual(1050);
  expect(cajaDialogo!.width).toBeLessThanOrEqual(1200);
  expect(cajaDialogo!.x).toBeGreaterThanOrEqual(0);
  expect(cajaDialogo!.x + cajaDialogo!.width).toBeLessThanOrEqual(1440);
  expect(cajaDialogo!.y).toBeGreaterThan(cajaToolbar!.y + cajaToolbar!.height);

  await page.evaluate(() => window.scrollBy(0, 420));
  const [cajaDialogoSticky, cajaToolbarSticky] = await Promise.all([
    dialogo.boundingBox(),
    toolbar.boundingBox(),
  ]);
  expect(cajaDialogoSticky).not.toBeNull();
  expect(cajaToolbarSticky).not.toBeNull();
  expect(Math.round(cajaToolbarSticky!.y)).toBe(80);
  expect(cajaDialogoSticky!.y).toBeGreaterThan(
    cajaToolbarSticky!.y + cajaToolbarSticky!.height,
  );

  await page.locator('#analisis-abrir-filtros').click();
  await expect(popover).toHaveAttribute('hidden');
  await abrirFiltros(page);
  await page.locator('#panel-analisis-titulo').click();
  await expect(popover).toHaveAttribute('hidden');
  await abrirFiltros(page);
  await page.locator('#analisis-cerrar-filtros').click();
  await expect(popover).toHaveAttribute('hidden');
  await expect(page.locator('#analisis-abrir-filtros')).toBeFocused();
});

test('mantiene los filtros usables como panel inferior en móvil', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(URL_INICIAL);
  await esperarPanel(page);
  await abrirFiltros(page);

  const contenido = page.locator('main');
  const dialogo = page.locator('#analisis-filtros-dialogo');
  await expect(contenido).toHaveJSProperty('inert', false);
  await expect(dialogo).not.toHaveAttribute('aria-modal', 'true');
  await expect(dialogo).toHaveCSS('width', '390px');
  await expect(page.locator('#analisis-filtros-fondo')).toBeVisible();
  const tituloVisible = await page
    .locator('#filtros-analisis-titulo')
    .evaluate((titulo) => {
      const caja = titulo.getBoundingClientRect();
      return (
        document.elementFromPoint(
          caja.left + caja.width / 2,
          caja.top + caja.height / 2,
        ) === titulo
      );
    });
  expect(tituloVisible).toBe(true);

  await page.keyboard.press('Escape');
  await expect(page.locator('#analisis-filtros-popover')).toHaveAttribute(
    'hidden',
  );
  await expect(contenido).toHaveJSProperty('inert', false);
  await expect(page.locator('#analisis-abrir-filtros')).toBeFocused();
});

test('amplía paneles en foco y cambia la densidad temporal', async ({
  page,
}) => {
  await page.goto(URL_INICIAL);
  await esperarPanel(page);

  const temporadas = page.locator('[data-panel-workspace="temporadas"]');
  await page.locator('[data-boton-menu-panel="temporadas"]').click();
  await temporadas.locator('[data-accion-panel="foco"]').click();
  await expect(temporadas).toHaveClass(/xl:col-span-12/);

  const heatmap = page.locator('#heatmap-departamentos');
  const anchoInicial = await heatmap.evaluate((elemento) =>
    Number.parseFloat(getComputedStyle(elemento).minWidth),
  );
  await page.locator('#analisis-zoom-mas').click();
  await expect(page.locator('#analisis-zoom-valor')).toHaveText('150%');
  await expect
    .poll(() =>
      heatmap.evaluate((elemento) =>
        Number.parseFloat(getComputedStyle(elemento).minWidth),
      ),
    )
    .toBeGreaterThan(anchoInicial);

  await page.locator('[data-boton-menu-panel="temporadas"]').click();
  await temporadas.locator('[data-accion-panel="foco"]').click();
  await expect(temporadas).not.toHaveClass(/xl:col-span-12/);

  await page.locator('[data-boton-menu-panel="temporadas"]').click();
  await temporadas
    .locator('[data-accion-panel="tamano"][data-valor="pequeno"]')
    .click();
  await expect(temporadas).toHaveClass(/xl:col-span-3/);
  await page.locator('[data-boton-menu-panel="temporadas"]').click();
  await temporadas
    .locator('[data-accion-panel="tamano"][data-valor="mediano"]')
    .click();
  await expect(temporadas).toHaveClass(/xl:col-span-4/);
});

test('mantiene una sola curva nacional al cambiar su detalle', async ({
  page,
}) => {
  await page.goto(URL_INICIAL);
  await esperarPanel(page);
  await expect(page.locator('#curva-epidemica > svg')).toHaveCount(1);
  await page.locator('#curva-zoom-mas').click();
  await page.locator('#curva-zoom-mas').click();
  await expect(page.locator('#curva-zoom-valor')).toHaveText('200%');
  await expect(page.locator('#curva-epidemica > svg')).toHaveCount(1);
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
