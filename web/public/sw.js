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

/*
 * Marca una respuesta como servida desde el cache.
 *
 * La marca va en el CUERPO, no en una cabecera. La API vive en otro origen,
 * y el navegador filtra por CORS las cabeceras que la página puede leer: una
 * cabecera propia puesta aquí llega pero es invisible (probado: ni siquiera
 * con Access-Control-Expose-Headers en la respuesta sintética). El cuerpo sí
 * se lee entero, así que `_desde_cache` es la única señal fiable.
 *
 * `_desde_cache` es un marcador de transporte del service worker, no un campo
 * del contrato de /api/alertas: el backend nunca lo emite.
 */
async function marcarComoCache(respuesta) {
  const cabeceras = new Headers(respuesta.headers);
  cabeceras.set('X-EPI-Cache', 'sw');
  const copia = respuesta.clone();
  let cuerpo;
  try {
    const datos = await copia.json();
    cuerpo = JSON.stringify({ ...datos, _desde_cache: true });
  } catch {
    // No era JSON: se devuelve tal cual, solo con la cabecera.
    cuerpo = await respuesta.clone().blob();
  }
  return new Response(cuerpo, {
    status: respuesta.status,
    statusText: respuesta.statusText,
    headers: cabeceras,
  });
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
    // ignoreVary: el servidor estatico responde con Vary: Accept-Encoding y
    // la cabecera de la peticion guardada no coincide con la del navegador,
    // asi que sin esto el match falla pese a estar la entrada en el cache.
    const guardada = await cache.match(peticion, { ignoreVary: true });
    if (guardada) return marcarComoCache(guardada);
    throw error;
  }
}

async function shellStaleWhileRevalidate(peticion) {
  const cache = await caches.open(CACHE_SHELL);
  // ignoreVary: ver apiNetworkFirst. Sin esto, /_astro/*.js queda guardado
  // pero nunca se sirve, y la recarga sin conexion trae el HTML sin scripts.
  const guardada = await cache.match(peticion, { ignoreVary: true });
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

/*
 * Precache dirigido por la página. En la primera visita el service worker
 * todavía no controlaba el documento, así que sus subrecursos (/_astro/*.js,
 * CSS, fuentes) nunca pasaron por este `fetch` y no quedaron en el cache: sin
 * esto, una recarga sin conexión devuelve el HTML pero ningún script, y la
 * vista queda en blanco. La página manda su lista de recursos ya cargados
 * (performance.getEntriesByType) y aquí se guardan.
 */
self.addEventListener('message', (evento) => {
  const datos = evento.data;
  if (!datos || datos.tipo !== 'precache' || !Array.isArray(datos.urls)) return;
  const responder = (ok) => {
    const puerto = evento.ports && evento.ports[0];
    if (puerto) puerto.postMessage({ ok });
  };
  // datos.api: el endpoint de alertas. Por el mismo motivo que los
  // subrecursos, la primera llamada del documento no pasó por este `fetch`,
  // así que CACHE_API quedaría vacío y el respaldo offline no existiría.
  const calentarApi = datos.api
    ? caches
        .open(CACHE_API)
        .then((cache) => cache.add(new Request(datos.api, { mode: 'cors' })))
        .catch(() => undefined)
    : Promise.resolve();

  evento.waitUntil(
    Promise.all([
      caches
        .open(CACHE_SHELL)
        .then((cache) =>
          Promise.allSettled(
            datos.urls.map((url) =>
              cache.add(new Request(url, { cache: 'reload' })),
            ),
          ),
        ),
      calentarApi,
    ])
      .then(() => responder(true))
      .catch(() => responder(false)),
  );
});

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
