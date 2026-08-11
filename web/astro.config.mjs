import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// Configuración principal del framework Astro
export default defineConfig({
  server: {
    // Permite que el servidor sea accesible desde fuera del contenedor Docker
    host: true,
    // Puerto estándar expuesto para la interfaz de desarrollo web
    port: 4321
  },
  vite: {
    // Tailwind v4 se integra como plugin de Vite directamente -- @astrojs/tailwind
    // (la integración anterior) no soporta Tailwind v4 ni Astro 6+.
    plugins: [tailwindcss()]
  }
});