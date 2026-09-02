import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  // Un solo worker: el dev server de Vite (Astro) reoptimiza dependencias de
  // forma perezosa; con varios workers pidiendo /dengue y /respiratorio a la
  // vez, Leaflet y @observablehq/plot entran en una carrera que devuelve 504 y
  // recarga la página a mitad de test. La suite completa tarda ~30 s en serie.
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',
  timeout: 45_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:4321',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
