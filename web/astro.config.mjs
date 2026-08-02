import { defineConfig } from 'astro/config';

// Configuración principal del framework Astro
export default defineConfig({
  server: {
    // Permite que el servidor sea accesible desde fuera del contenedor Docker
    host: true,
    // Puerto estándar expuesto para la interfaz de desarrollo web
    port: 4321
  }
});