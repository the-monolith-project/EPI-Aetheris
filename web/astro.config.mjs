import { defineConfig, fontProviders } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// Configuración principal del framework Astro
export default defineConfig({
  // Dominio de producción -- inferido de render.yaml (servicio estático
  // "epi-aetheris-web", CORS_ALLOWED_ORIGINS). Habilita canonical/og:url
  // absolutos y sitemaps. Verificar contra la URL real tras el deploy.
  site: 'https://epi-aetheris-web.onrender.com',
  // Precarga el HTML de cualquier enlace del sitio al pasar el cursor /
  // entrar en viewport -- navegación casi instantánea entre las 5 vistas.
  prefetch: {
    prefetchAll: true,
  },
  // /panel se renombró a /dengue (#70). La ruta vieja estuvo en producción
  // (bookmarks, enlaces compartidos, indexación) -- este redirect la preserva.
  // En build estático Astro genera una página de redirección por cada entrada.
  redirects: {
    '/panel': '/dengue',
  },
  // Fonts API de Astro (estable desde v6): auto-hospeda los ficheros en
  // build y genera fallbacks con métricas ajustadas (size-adjust vía
  // capsize, optimizedFallbacks por defecto). Sin preconnect a Google ni
  // hojas render-blocking. No se usa preload -- #87 (a576b3a) difirió las
  // fuentes del render crítico a propósito; el swap lo cubre el fallback
  // ajustado.
  fonts: [
    {
      provider: fontProviders.google(),
      name: 'Inter',
      cssVariable: '--font-inter',
      // 400 cuerpo · 500 font-medium · 600 font-semibold · 700 monograma.
      weights: [400, 500, 600, 700],
      display: 'swap',
      // Sin restringir `styles`: /biblioteca renderiza markdown de docs/ y
      // puede contener <em>; se conserva la itálica real de Inter.
      fallbacks: ['Arial', 'sans-serif'],
    },
    {
      provider: fontProviders.google(),
      name: 'IBM Plex Mono',
      cssVariable: '--font-plex-mono',
      // Solo peso normal en uso (etiquetas de ejes, valores, código inline).
      weights: [400],
      display: 'swap',
      styles: ['normal'],
      fallbacks: ['ui-monospace', 'monospace'],
    },
    {
      provider: fontProviders.google(),
      name: 'Fraunces',
      cssVariable: '--font-fraunces',
      // Voz de titular. Se fija el eje óptico alto (opsz 144) para conservar
      // el serif editorial de alto contraste; solo H1/H2 de la landing.
      weights: [600, 700],
      display: 'swap',
      styles: ['normal'],
      variationSettings: '"opsz" 144',
      fallbacks: ['Georgia', 'serif'],
    },
  ],
  server: {
    // Permite que el servidor sea accesible desde fuera del contenedor Docker
    host: true,
    // Puerto estándar expuesto para la interfaz de desarrollo web
    port: 4321,
  },
  vite: {
    // Tailwind v4 se integra como plugin de Vite directamente -- @astrojs/tailwind
    // (la integración anterior) no soporta Tailwind v4 ni Astro 6+.
    plugins: [tailwindcss()],
  },
});
