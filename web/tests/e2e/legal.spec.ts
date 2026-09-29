import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

// Capa legal y de confianza: privacidad, términos, aviso legal, contacto,
// acerca de y la 404. Son páginas estáticas -- ninguna toca el backend, así
// que estos tests no gastan la ventana de 30/minuto de los endpoints pesados.
//
// Lo que NO se comprueba aquí: que no queden marcadores sin rellenar en el
// texto legal. Esa es una puerta de despliegue, no de suite: vive en el bloque
// de comprobaciones de build, que sí corre antes de pushear. El patrón tiene
// que nombrar los marcadores, no buscar «» a secas: las comillas angulares son
// puntuación normal en español y aparecen legítimamente en estas páginas
// («tal cual», «Recordar el token en este navegador»).
//
//   grep -rnE "«(RESPONSABLE|DOMICILIO|CORREO_CONTACTO|CORREO_SEGURIDAD|JURISDICCION)»" dist/

const PAGINAS = [
  { ruta: '/legal/privacidad', h1: 'Política de privacidad' },
  { ruta: '/legal/terminos', h1: 'Términos de uso' },
  { ruta: '/legal/aviso-legal', h1: 'Aviso legal' },
  { ruta: '/contacto', h1: 'Contacto' },
  { ruta: '/acerca-de', h1: 'Acerca de EPI-Aetheris' },
];

for (const pagina of PAGINAS) {
  test(`${pagina.ruta} responde con un solo h1 y conserva la navegación`, async ({
    page,
  }) => {
    const respuesta = await page.goto(pagina.ruta);
    expect(respuesta?.status()).toBe(200);

    await expect(page.locator('main h1')).toHaveText(pagina.h1);
    await expect(
      page.locator('nav[aria-label="Navegación principal"]'),
    ).toBeVisible();
    await expect(page.locator('#contenido-principal')).toBeVisible();
  });
}

test('las tres legales se enlazan entre sí y con contacto', async ({
  page,
}) => {
  await page.goto('/legal/privacidad');
  const documento = page.locator('main');
  await expect(
    documento.getByRole('link', { name: 'términos de uso' }),
  ).toHaveAttribute('href', '/legal/terminos');
  await expect(
    documento.getByRole('link', { name: 'aviso legal' }).last(),
  ).toHaveAttribute('href', '/legal/aviso-legal');
  await expect(
    documento.getByRole('link', { name: 'contacto' }).last(),
  ).toHaveAttribute('href', '/contacto');
});

test('el pie expone la sección legal en cualquier página', async ({ page }) => {
  await page.goto('/');
  const navFooter = page.locator('nav[aria-label="Pie de página"]');
  await expect(
    navFooter.getByRole('link', { name: 'Privacidad' }),
  ).toHaveAttribute('href', '/legal/privacidad');
  await expect(
    navFooter.getByRole('link', { name: 'Términos de uso' }),
  ).toHaveAttribute('href', '/legal/terminos');
  await expect(
    navFooter.getByRole('link', { name: 'Aviso legal' }),
  ).toHaveAttribute('href', '/legal/aviso-legal');
  await expect(
    navFooter.getByRole('link', { name: 'Contacto' }),
  ).toHaveAttribute('href', '/contacto');
});

test('la política de privacidad nombra las transferencias reales a terceros', async ({
  page,
}) => {
  await page.goto('/legal/privacidad');
  const documento = page.locator('main');
  // Las teselas de OSM son la única transferencia sustantiva al navegar y la
  // más fácil de omitir al redactar: no hay ningún <script> de terceros que
  // la delate. Si alguien reescribe la política, esto lo frena.
  await expect(documento).toContainText('OpenStreetMap');
  await expect(documento).toContainText('Render');
  await expect(documento).toContainText('no usa cookies');
});

test('la 404 mantiene la navegación y sale del índice', async ({ page }) => {
  await page.goto('/ruta-que-no-existe-jamas');
  // En el dev server Astro sirve su propia página de error, así que este test
  // afirma sobre la 404 propia solo cuando se corre contra el build.
  const esPaginaPropia = await page
    .locator('main h1', { hasText: 'Esta página no existe' })
    .isVisible()
    .catch(() => false);
  test.skip(
    !esPaginaPropia,
    'La 404 propia solo se sirve desde el build (astro preview o producción)',
  );

  await expect(
    page.locator('nav[aria-label="Navegación principal"]'),
  ).toBeVisible();
  await expect(page.locator('head meta[name="robots"]')).toHaveAttribute(
    'content',
    'noindex, nofollow',
  );
});

test('las páginas legales no presentan violaciones automáticas WCAG A o AA', async ({
  page,
}) => {
  await page.goto('/legal/privacidad');
  const resultados = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(resultados.violations).toEqual([]);
});

test('la página de contacto no presenta violaciones automáticas WCAG A o AA', async ({
  page,
}) => {
  await page.goto('/contacto');
  const resultados = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  expect(resultados.violations).toEqual([]);
});
