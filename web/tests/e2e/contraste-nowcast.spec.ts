import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

// Contraste de la predicción con lo observado (página /prediccion).
// Las dos respuestas de la predicción se simulan con una serie sintética de
// 2017 a 2019: las 30 primeras semanas no tienen predicción (falta historia),
// 2019 es temporada de prueba y la última semana es el ancla.

const ANIOS = [2017, 2018, 2019];
const SEMANAS_SIN_MODELO = 30;

function iso(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function serieSintetica() {
  const inicio = new Date('2017-01-01T00:00:00Z');
  const semanas: {
    fecha: string;
    anio: number;
    semana: number;
    casos: number;
  }[] = [];
  let i = 0;
  for (const anio of ANIOS) {
    for (let s = 1; s <= 52; s++) {
      const d = new Date(inicio.getTime() + i * 7 * 86_400_000);
      semanas.push({
        fecha: iso(d),
        anio,
        semana: s,
        casos: Math.round(100 + 20 * Math.sin((i / 52) * 2 * Math.PI)),
      });
      i++;
    }
  }
  return semanas;
}

function respuestas() {
  const semanas = serieSintetica();
  const ancla = semanas[semanas.length - 1];
  const origenes = semanas.slice(0, -1).map((s, idx) => {
    if (idx < SEMANAS_SIN_MODELO) {
      return {
        fecha: s.fecha,
        anio: s.anio,
        semana: s.semana,
        motivo: 'historia_insuficiente',
      };
    }
    const h = [1, 2, 3, 4, 5, 6, 7, 8].map((k) => {
      const med = s.casos;
      const conDato = idx + k < semanas.length;
      return [
        med,
        med - 10,
        med + 10,
        med - 40,
        med + 40,
        conDato ? 12 : null,
        conDato ? 18 : null,
      ];
    });
    return { fecha: s.fecha, anio: s.anio, semana: s.semana, h };
  });
  const estimacion = [1, 2, 3, 4, 5, 6, 7, 8].map((k) => {
    const d = new Date(
      new Date(`${ancla.fecha}T00:00:00Z`).getTime() + k * 7 * 86_400_000,
    );
    return {
      h: k,
      fecha: iso(d),
      anio: 2020,
      semana: k,
      cuantiles: [],
      mediana: 90,
      banda_50: [80, 100],
      banda_95: [50, 140],
    };
  });
  const principal = {
    disponible: true,
    aviso: 'Predicción estadística.',
    ancla: {
      fecha: ancla.fecha,
      anio: ancla.anio,
      semana: ancla.semana,
      casos: ancla.casos,
    },
    horizontes: [1, 2, 3, 4, 5, 6, 7, 8],
    observado: semanas
      .slice(-60)
      .map((s) => ({ fecha: s.fecha, casos: s.casos })),
    estimacion,
    backtest: { horizonte: 4, anios: [2019], puntos: [] },
    desempeno: {
      horizonte: 4,
      baseline: 'persistencia_rw',
      wis_modelo: 12,
      wis_baseline: 18,
      reduccion_wis: 0.33,
      skill_medio_por_anio: 0.33,
      skill_por_anio: { '2019': 0.33 },
      anios_ganados: 1,
      n_anios: 1,
      cobertura_50: 0.5,
      cobertura_95: 0.95,
    },
  };
  const retro = {
    disponible: true,
    aviso: 'Predicción estadística.',
    horizontes: [1, 2, 3, 4, 5, 6, 7, 8],
    anios_prueba: [2019],
    anio_excluido: 2020,
    aviso_anio_excluido: 'Aviso de 2020.',
    referencia_por_horizonte: Object.fromEntries(
      [1, 2, 3, 4, 5, 6, 7, 8].map((h) => [String(h), 'persistencia_rw']),
    ),
    primera_semana_con_prediccion: {
      fecha: semanas[SEMANAS_SIN_MODELO].fecha,
      anio: semanas[SEMANAS_SIN_MODELO].anio,
      semana: semanas[SEMANAS_SIN_MODELO].semana,
    },
    campos_horizonte: [
      'mediana',
      'b50_inf',
      'b50_sup',
      'b95_inf',
      'b95_sup',
      'wis_modelo',
      'wis_referencia',
    ],
    observado: semanas.map((s) => [s.fecha, s.casos]),
    origenes,
    resumen_por_anio: {
      '2019': {
        '4': {
          n: 48,
          wis_modelo: 12,
          wis_referencia: 18,
          skill: 0.333,
          cobertura_50: 0.5,
          cobertura_95: 0.94,
        },
      },
    },
  };
  return { principal, retro };
}

async function simularApi(page: Page) {
  const { principal, retro } = respuestas();
  await page.route('**/api/nowcast-dengue/retrospectivo', (ruta) =>
    ruta.fulfill({ json: retro }),
  );
  await page.route('**/api/nowcast-dengue', (ruta) =>
    ruta.fulfill({ json: principal }),
  );
}

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
