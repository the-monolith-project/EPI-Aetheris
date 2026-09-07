import { expect, test } from '@playwright/test';

import {
  calcularNuevas,
  type AlertaPublica,
} from '../../src/lib/vista-alertas';

// ADR 0014: dos caras del sitio como secciones, no como modo con estado.
// Estas pruebas fijan justamente lo que no debe volver: un toggle de enfoque,
// una vista titulada "hoy", o un bloque clínico que se rompa cuando el campo
// todavía está en null.

function alertaBase(id: number): AlertaPublica {
  return {
    id,
    tipo: 'dengue',
    nivel: 'atencion',
    titulo: `Alerta ${id}`,
    contexto: 'contexto',
    indicaciones: '- hacer algo',
    fuente: 'fuente',
    autor: 'autor',
    vigente_desde: '2026-09-01',
    vigente_hasta: null,
    activa: true,
  };
}

test('la primera visita no marca nada como nueva', () => {
  const alertas = [alertaBase(1), alertaBase(2)];
  // Sin historial guardado no hay referencia: marcar todo como "Nueva" sería
  // ruido, no información.
  expect(calcularNuevas(alertas, new Set()).size).toBe(0);
});

test('solo las alertas no vistas se marcan como nuevas', () => {
  const alertas = [alertaBase(1), alertaBase(2), alertaBase(3)];
  const nuevas = calcularNuevas(alertas, new Set([1]));
  expect([...nuevas].sort()).toEqual([2, 3]);
});

test('filtrar por tipo no borra del historial las alertas del otro tipo', async ({
  page,
}) => {
  // Repro de un clic: /alertas guarda las dos, el chip "Dengue" recarga con
  // la lista filtrada, y al volver a /alertas la respiratoria no debe salir
  // marcada como nueva. El historial se une, no se reemplaza.
  await page.goto('/alertas');
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  const todas = await page.evaluate(() =>
    JSON.parse(localStorage.getItem('epi-aetheris:alertas-vistas') ?? '[]'),
  );
  expect(todas.length).toBeGreaterThan(1);

  await page.goto('/alertas?tipo=dengue');
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  const trasFiltro = await page.evaluate(() =>
    JSON.parse(localStorage.getItem('epi-aetheris:alertas-vistas') ?? '[]'),
  );
  for (const id of todas) expect(trasFiltro).toContain(id);

  await page.goto('/alertas');
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  await expect(page.locator('[data-alerta-nueva]')).toHaveCount(0);
});

test('la barra no ofrece un interruptor de enfoque y agrupa el análisis', async ({
  page,
}) => {
  await page.goto('/');
  const nav = page.locator('nav[aria-label="Navegación principal"]');
  await expect(nav.getByRole('link', { name: 'Alertas' })).toBeVisible();
  await expect(nav.getByRole('link', { name: 'Análisis' })).toHaveAttribute(
    'href',
    '/analisis',
  );
  // Dengue y Respiratorio ya no son entradas propias: viven bajo Análisis.
  await expect(nav.getByRole('link', { name: 'Dengue' })).toHaveCount(0);
  await expect(nav.getByRole('link', { name: 'Respiratorio' })).toHaveCount(0);
  // Y no hay control de modo de ningún tipo.
  await expect(nav.locator('button')).toHaveCount(0);
});

test('la portada ofrece dos puertas que son enlaces sin estado', async ({
  page,
}) => {
  await page.goto('/');
  const consulta = page.locator('[data-puerta="consulta"]');
  const analisis = page.locator('[data-puerta="analisis"]');
  await expect(consulta).toHaveAttribute('href', '/alertas');
  await expect(analisis).toHaveAttribute('href', '/analisis');
  // Enlaces, no botones: un enlace compartido abre igual para cualquiera.
  await expect(consulta).toHaveJSProperty('tagName', 'A');
  await expect(analisis).toHaveJSProperty('tagName', 'A');
});

test('/analisis enlaza las tres herramientas y no promete tiempo real', async ({
  page,
}) => {
  await page.goto('/analisis');
  await expect(page.locator('[data-herramienta="/dengue"]')).toBeVisible();
  await expect(
    page.locator('[data-herramienta="/respiratorio"]'),
  ).toBeVisible();
  await expect(page.locator('[data-herramienta="/ira"]')).toBeVisible();
  await expect(page.locator('main')).toContainText(
    'Las series son históricas, no de tiempo real',
  );
  await expect(
    page.locator(
      'nav[aria-label="Navegación principal"] a[aria-current="page"]',
    ),
  ).toHaveText('Análisis');
});

test('/alertas muestra el sello de frescura y el botón de imprimir', async ({
  page,
}) => {
  await page.goto('/alertas');
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  await expect(page.locator('[data-imprimir]')).toBeVisible();
  const sello = page.locator('[data-sello-frescura]');
  await expect(sello).toContainText('Datos cargados el');
  // Sin service worker en juego, la carga viene de red, no de cache.
  await expect(sello).toHaveAttribute('data-desde-cache', '0');
});

test('los campos clínicos en null no dejan bloques vacíos en la tarjeta', async ({
  page,
}) => {
  await page.goto('/alertas');
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  // Las filas demo (migración 0009) llegan sin los campos de la 0010.
  await expect(page.locator('[data-alerta-clinico]')).toHaveCount(0);
  // La tarjeta sigue completa pese a eso.
  await expect(
    page.locator('[data-alerta]').first().locator('[data-alerta-indicaciones]'),
  ).toBeVisible();
  await expect(
    page.locator('[data-alerta]').first().locator('[data-alerta-compartir]'),
  ).toBeVisible();
});

test('/alertas abre sin conexión desde el cache del service worker', async ({
  page,
  context,
}) => {
  // El item que se justificó por consecuencia clínica: si el cache no sirve
  // /alertas sin red, el sello de frescura nunca se dispara y la función no
  // existe. Se verifica de verdad, no por construcción.
  await page.goto('/alertas');
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  await page.evaluate(() => navigator.serviceWorker.ready);
  // El SW confirma que ya guardó los subrecursos de esta página.
  await expect(page.locator('html')).toHaveAttribute('data-sw-listo', '1', {
    timeout: 15_000,
  });

  // context.setOffline no alcanza al service worker (corre en otro contexto y
  // sigue llegando a la red). Se corta la API a nivel de contexto, que sí
  // intercepta las peticiones que origina el worker.
  await context.route('**/api/alertas*', (ruta) => ruta.abort());
  await page.reload();
  await expect(page.locator('[data-alertas]')).toHaveAttribute(
    'data-cargado',
    '1',
    { timeout: 15_000 },
  );
  await expect(page.locator('[data-sello-frescura]')).toHaveAttribute(
    'data-desde-cache',
    '1',
  );
  await expect(page.locator('[data-sello-frescura]')).toContainText(
    'Sin conexión',
  );
  await expect(page.locator('[data-alerta]').first()).toBeVisible();
  await context.unroute('**/api/alertas*');
});
