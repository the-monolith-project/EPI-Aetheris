import { expect, test } from '@playwright/test';
import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

type DocBiblioteca = {
  slug: string;
  titulo: string;
  descripcion: string;
  orden: number;
};

const DIR_BIBLIOTECA = path.resolve(
  fileURLToPath(new URL('../../../docs/biblioteca', import.meta.url)),
);

function campo(frontmatter: string, nombre: string): string {
  const coincidencia = frontmatter.match(
    new RegExp(`^${nombre}:\\s*"([^"]+)"`, 'm'),
  );
  if (!coincidencia?.[1]) {
    throw new Error(`frontmatter sin ${nombre}`);
  }
  return coincidencia[1];
}

async function leerDocumentos(): Promise<DocBiblioteca[]> {
  const archivos = (await readdir(DIR_BIBLIOTECA))
    .filter((nombre) => nombre.endsWith('.md'))
    .sort();
  const docs: DocBiblioteca[] = [];
  for (const archivo of archivos) {
    const fuente = await readFile(path.join(DIR_BIBLIOTECA, archivo), 'utf8');
    const bloque = fuente.match(/^---\n([\s\S]*?)\n---/);
    if (!bloque?.[1]) {
      throw new Error(`${archivo} sin frontmatter`);
    }
    const fm = bloque[1];
    const ordenBruto = fm.match(/^orden:\s*(\d+)/m);
    if (!ordenBruto?.[1]) {
      throw new Error(`${archivo} sin orden`);
    }
    docs.push({
      slug: archivo.replace(/\.md$/, ''),
      titulo: campo(fm, 'titulo'),
      descripcion: campo(fm, 'descripcion'),
      orden: Number(ordenBruto[1]),
    });
  }
  docs.sort((a, b) => a.orden - b.orden);
  return docs;
}

test('/biblioteca lista los documentos por titulo del frontmatter', async ({
  page,
}) => {
  const docs = await leerDocumentos();
  expect(docs.length).toBeGreaterThanOrEqual(6);

  await page.goto('/biblioteca');
  await expect(
    page.locator(
      'nav[aria-label="Navegación principal"] a[aria-current="page"]',
    ),
  ).toHaveText('Biblioteca');

  for (const doc of docs) {
    const tarjeta = page
      .locator('main')
      .locator(`a[href="/biblioteca/${doc.slug}"]`);
    await expect(tarjeta).toBeVisible();
    await expect(tarjeta.getByRole('heading')).toHaveText(doc.titulo);
    await expect(tarjeta).toContainText(doc.descripcion);
  }
});

test('cada documento renderiza y Volver a la biblioteca regresa al indice', async ({
  page,
}) => {
  const docs = await leerDocumentos();

  for (const doc of docs) {
    const respuesta = await page.goto(`/biblioteca/${doc.slug}`);
    expect(respuesta?.ok()).toBeTruthy();
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(
      doc.titulo,
    );
    await expect(page.locator('article')).toContainText(doc.descripcion);
    await expect(
      page.locator(
        'nav[aria-label="Navegación principal"] a[aria-current="page"]',
      ),
    ).toHaveText('Biblioteca');
  }

  await page.goto(`/biblioteca/${docs[0].slug}`);
  await page.getByRole('link', { name: 'Volver a la biblioteca' }).click();
  await expect(page).toHaveURL(/\/biblioteca\/?$/);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Biblioteca',
  );
});
