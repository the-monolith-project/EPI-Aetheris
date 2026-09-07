import { expect, test } from '@playwright/test';

import {
  renderTextoAccionable,
  SIGNIFICADO_NIVEL,
  textoEstadoVacio,
  textoSignificadoNivel,
  vistaDeAlertas,
} from '../../src/lib/vista-alertas';

const AVISO =
  'Herramienta académica en desarrollo (INSAMT, Equipo 4). Las alertas y sus indicaciones las redacta manualmente el equipo de vigilancia del proyecto a partir de datos públicos históricos (MINSAL, OpenDengue, Open-Meteo). No sustituyen los lineamientos oficiales del MINSAL ni el criterio clínico. No son tiempo real. La coexistencia temporal de eventos no demuestra causalidad.';

const TITULO_DENGUE =
  'Casos probables de dengue por encima de años comparables en 2023';
const TITULO_RESPIRATORIO =
  'IRA y detecciones virales por encima de años comparables en 2023';
const TITULO_INACTIVA =
  'Vigilancia rutinaria de dengue (cerrada el 31/08/2026)';

test('nivel meanings match INDICACIONES §4', () => {
  expect(SIGNIFICADO_NIVEL.informativo).toBe(
    'Sin señal relevante en los datos. Recordatorio de vigilancia rutinaria.',
  );
  expect(SIGNIFICADO_NIVEL.atencion).toBe(
    'Los datos históricos recientes están por encima de lo esperado para la época. Reforzar notificación y búsqueda de casos.',
  );
  expect(SIGNIFICADO_NIVEL.intensificacion).toBe(
    'Señal sostenida varias semanas y/o concentración territorial. Activar medidas locales y coordinar con SIBASI.',
  );
  expect(textoSignificadoNivel('atencion')).toBe(SIGNIFICADO_NIVEL.atencion);
  expect(textoSignificadoNivel('otro')).toBe('');
});

test('empty-state copy is the list-empty view branch', () => {
  const vista = vistaDeAlertas([], '2026-09-06');
  expect(vista.tipo).toBe('vacio');
  if (vista.tipo !== 'vacio') return;
  expect(vista.texto).toBe(
    'No hay alertas activas. Última revisión del equipo: 06/09/2026.',
  );
  expect(textoEstadoVacio('06/09/2026')).toBe(vista.texto);
});

test('accionable text escapes HTML', () => {
  const html = renderTextoAccionable(
    '<script>alert(1)</script>\n- item <b>x</b>',
  );
  expect(html).toContain('&lt;script&gt;');
  expect(html).not.toContain('<script>');
  expect(html).toContain('&lt;b&gt;x&lt;/b&gt;');
  expect(html).toContain('<li>');
});

test('/alertas muestra aviso verbatim, campos de una alerta sembrada y sin copy predictivo', async ({
  page,
}) => {
  await page.goto('/alertas');
  await expect(page.locator('[data-aviso-honestidad]')).toContainText(AVISO);
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  await expect(page.locator('[data-alerta]').first()).toBeVisible();
  const dengue = page.locator('[data-alerta][data-tipo="dengue"]');
  await expect(dengue).toContainText(TITULO_DENGUE);
  await expect(dengue.locator('[data-alerta-tipo]')).toContainText('Dengue');
  await expect(dengue.locator('[data-alerta-nivel]')).toContainText('Atención');
  await expect(dengue.locator('[data-alerta-nivel-significado]')).toHaveText(
    SIGNIFICADO_NIVEL.atencion,
  );
  await expect(dengue.locator('[data-alerta-indicaciones]')).toContainText(
    'No indicar AINE ni intramusculares en febriles sin diagnóstico.',
  );
  await expect(page.locator('[data-niveles-leyenda]')).toBeVisible();
  await expect(page.locator('[data-nivel-leyenda="atencion"]')).toContainText(
    SIGNIFICADO_NIVEL.atencion,
  );
  await expect(
    page.locator('[data-nivel-leyenda="intensificacion"]'),
  ).toContainText(SIGNIFICADO_NIVEL.intensificacion);
  await expect(dengue.locator('[data-alerta-emision]')).toContainText(
    '01/09/2026',
  );
  await expect(dengue.locator('[data-alerta-vigencia]')).toContainText(
    'Vigencia',
  );
  await expect(dengue.locator('[data-alerta-fuente]')).not.toBeEmpty();
  await expect(dengue.locator('[data-alerta-autor]')).not.toBeEmpty();
  await expect(page.locator('main')).not.toContainText(TITULO_INACTIVA);
  await expect(page.locator('main')).not.toContainText('va a haber brote');
  await expect(page.locator('main')).not.toContainText(/predic/i);
});

test('empty list branch of the shipped view on /alertas', async ({ page }) => {
  await page.goto('/alertas');
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  await page.locator('[data-alertas]').evaluate((el) => {
    const pintar = (
      el as HTMLElement & {
        pintarAlertas?: (payload: {
          aviso: string;
          ultima_revision: string;
          alertas: [];
        }) => void;
      }
    ).pintarAlertas;
    if (!pintar) throw new Error('pintarAlertas no está en el contenedor');
    pintar({
      aviso: '',
      ultima_revision: '2026-09-06',
      alertas: [],
    });
  });
  await expect(page.locator('[data-alertas-vacio]')).toBeVisible();
  await expect(page.locator('[data-alertas-vacio]')).toHaveText(
    'No hay alertas activas. Última revisión del equipo: 06/09/2026.',
  );
});

test('dengue y respiratorio enlazan a /alertas filtrado; la tarjeta vuelve al módulo', async ({
  page,
}) => {
  await page.goto('/dengue');
  const enlaceDengue = page.locator('[data-enlace-alertas="dengue"]');
  await expect(enlaceDengue).toHaveText('¿Alerta activa? →');
  await expect(enlaceDengue).toHaveAttribute('href', '/alertas?tipo=dengue');

  await page.goto('/respiratorio');
  const enlaceResp = page.locator('[data-enlace-alertas="respiratorio"]');
  await expect(enlaceResp).toHaveText('¿Alerta activa? →');
  await expect(enlaceResp).toHaveAttribute(
    'href',
    '/alertas?tipo=respiratorio',
  );

  await page.goto('/alertas?tipo=dengue');
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  const tarjetaDengue = page.locator('[data-alerta][data-tipo="dengue"]');
  await expect(tarjetaDengue).toBeVisible();
  await expect(
    page.locator('[data-alerta][data-tipo="respiratorio"]'),
  ).toHaveCount(0);
  await expect(
    tarjetaDengue.locator('[data-enlace-modulo="dengue"]'),
  ).toHaveAttribute('href', '/dengue');

  await page.goto('/alertas?tipo=respiratorio');
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  const tarjetaResp = page.locator('[data-alerta][data-tipo="respiratorio"]');
  await expect(tarjetaResp).toBeVisible();
  await expect(tarjetaResp).toContainText(TITULO_RESPIRATORIO);
  await expect(
    tarjetaResp.locator('[data-alerta-indicaciones]'),
  ).toContainText(
    'Usar oximetría de pulso en todo paciente con dificultad respiratoria; documentar SatO2.',
  );
  await expect(
    tarjetaResp.locator('[data-alerta-nivel-significado]'),
  ).toHaveText(SIGNIFICADO_NIVEL.atencion);
  await expect(page.locator('[data-alerta][data-tipo="dengue"]')).toHaveCount(
    0,
  );
  await expect(
    tarjetaResp.locator('[data-enlace-modulo="respiratorio"]'),
  ).toHaveAttribute('href', '/respiratorio');
});
