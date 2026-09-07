/*
 * Service worker de EPI-Aetheris (ADR 0014).
 *
 * Motivo: el personal de salud en zona rural abre /alertas donde hay señal y
 * la necesita después donde no la hay. Sin cache, la página queda inservible.
 *
 * Dos estrategias, deliberadamente distintas:
 *
 *  - Shell (HTML, CSS, JS, fuentes, logos): stale-while-revalidate. Da una
 *    pantalla inmediata y actualiza en segundo plano. Un shell viejo no tiene
 *    consecuencia clínica.
 *
 *  - GET /api/alertas: network-first con respaldo al cache. Una alerta que el
 *    equipo ya apagó SÍ tiene consecuencia clínica, así que la red siempre
 *    gana; el cache es el último recurso. Cuando se responde desde el cache
 *    se añade la cabecera X-EPI-Cache: sw para que la página muestre el sello
 *    "sin conexión — mostrando lo último guardado" (ver alertas.astro).
 *
 * Escrito a mano, sin dependencias: el proyecto es de costo cero y no vale
 * añadir una cadena de build de PWA por ~90 líneas.
 */

const VERSION = 'v1';
const CACHE_SHELL = `epi-shell-${VERSION}`;
const CACHE_API = `epi-api-${VERSION}`;

// Rutas mínimas para que /alertas abra sin red. El resto entra al cache a
// medida que se visita; no se precachea el sitio entero.
const SHELL_MINIMO = ['/', '/alertas'];

self.addEventListener('install', (evento) => {
  evento.waitUntil(
    caches
      .open(CACHE_SHELL)
      // addAll falla entero si un recurso falla; se toleran ausencias.
      .then((cache) =>
        Promise.allSettled(SHELL_MINIMO.map((ruta) => cache.add(ruta))),
      )
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((claves) =>
        Promise.all(
          claves
            .filter((c) => c !== CACHE_SHELL && c !== CACHE_API)
            .map((c) => caches.delete(c)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

/** Copia una respuesta añadiendo la marca de que salió del cache. */
function marcarComoCache(respuesta) {
  const cabeceras = new Headers(respuesta.headers);
  cabeceras.set('X-EPI-Cache', 'sw');
  return respuesta
    .clone()
    .blob()
    .then(
      (cuerpo) =>
        new Response(cuerpo, {
          status: respuesta.status,
          statusText: respuesta.statusText,
          headers: cabeceras,
        }),
    );
}

async function apiNetworkFirst(peticion) {
  const cache = await caches.open(CACHE_API);
  try {
    const respuesta = await fetch(peticion);
    if (respuesta && respuesta.ok) {
      await cache.put(peticion, respuesta.clone());
    }
    return respuesta;
  } catch (error) {
    const guardada = await cache.match(peticion);
    if (guardada) return marcarComoCache(guardada);
    throw error;
  }
}

async function shellStaleWhileRevalidate(peticion) {
  const cache = await caches.open(CACHE_SHELL);
  const guardada = await cache.match(peticion);
  const red = fetch(peticion)
    .then((respuesta) => {
      if (respuesta && respuesta.ok) cache.put(peticion, respuesta.clone());
      return respuesta;
    })
    .catch(() => undefined);
  const respuesta = guardada || (await red);
  if (respuesta) return respuesta;
  throw new Error('sin red y sin cache');
}

self.addEventListener('fetch', (evento) => {
  const peticion = evento.request;
  if (peticion.method !== 'GET') return;

  const url = new URL(peticion.url);
  if (url.pathname === '/api/alertas') {
    evento.respondWith(apiNetworkFirst(peticion));
    return;
  }

  // Solo el propio origen: no se cachea la API en otro host salvo /api/alertas
  // (arriba), ni recursos de terceros.
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/')) return;

  evento.respondWith(shellStaleWhileRevalidate(peticion));
});
