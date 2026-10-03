import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { simularApi } from './nowcast-mock';

// Contraste de la predicción con lo observado (página /prediccion). La serie
// sintética que simula la API está en nowcast-mock.ts.

test('mueve la semana de partida de la predicción y la contrasta con lo observado', async ({
  page,
}) => {
  await simularApi(page);
  await page.goto('/prediccion');

  const seccion = page.locator('[data-contraste-nowcast]');
  const anio = seccion.getByLabel('Año');
  const semana = seccion.getByRole('slider');
  const resumen = seccion.locator('[aria-live="polite"]');
  // El componente carga al entrar en el viewport.
  await seccion.scrollIntoViewIfNeeded();
  await expect(anio).toBeEnabled({ timeout: 15_000 });

  // arranca en la última semana publicada, sin observado posterior
  await expect(anio).toHaveValue('2019');
  await expect(resumen).toContainText('Semana 52 de 2019');
  await expect(resumen).toContainText('todavía no hay valores observados');

  // cambiar de año conserva la semana
  await anio.selectOption('2018');
  await expect(resumen).toContainText('Semana 52 de 2018');
  await expect(resumen).toContainText('De 8 semanas observadas después');
  await expect(resumen).toContainText('y 8 dentro del 95 %');
  await expect(resumen).toContainText(
    'Error medio del modelo: 12, frente a 18 de repetir el último valor.',
  );
  await expect(seccion.locator('tbody tr')).toHaveCount(8);

  // teclado sobre el deslizador y botones que cruzan de año
  await semana.focus();
  await page.keyboard.press('ArrowLeft');
  await expect(resumen).toContainText('Semana 51 de 2018');
  await expect(semana).toHaveAttribute('aria-valuetext', /Semana 51 de 2018/);
  const siguiente = seccion.getByRole('button', { name: 'Semana siguiente' });
  await siguiente.click();
  await siguiente.click();
  await expect(resumen).toContainText('Semana 1 de 2019');
  await expect(anio).toHaveValue('2019');
  await expect(seccion).toContainText(
    '2019 es una de las temporadas de la validación publicada.',
  );
  await expect(seccion).toContainText(
    '33 % menos error que repetir el último valor',
  );

  // las primeras semanas no tienen predicción
  await anio.selectOption('2017');
  await semana.fill('5');
  await expect(resumen).toContainText('Semana 5 de 2017');
  await expect(resumen).toContainText('Sin predicción desde esta semana');
  await expect(resumen).toContainText(
    'La primera semana con predicción es la 31 de 2017',
  );
  await expect(seccion.locator('table')).toHaveCount(0);

  // arrastrar sobre la gráfica mueve la semana de partida
  await anio.selectOption('2018');
  const grafica = seccion.locator('svg[role="img"]');
  const caja = await grafica.boundingBox();
  if (!caja) throw new Error('sin gráfica');
  await page.mouse.move(caja.x + caja.width * 0.5, caja.y + caja.height / 2);
  await page.mouse.down();
  await page.mouse.move(caja.x + caja.width * 0.3, caja.y + caja.height / 2, {
    steps: 5,
  });
  await page.mouse.up();
  const valorTrasArrastre = Number(await semana.inputValue());
  expect(valorTrasArrastre).toBeGreaterThan(1);
  expect(valorTrasArrastre).toBeLessThan(30);
  await expect(resumen).toContainText(`Semana ${valorTrasArrastre} de 2018`);

  const resultados = await new AxeBuilder({ page })
    .include('[data-contraste-nowcast]')
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(resultados.violations).toEqual([]);
});
