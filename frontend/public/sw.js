/**
 * sw.js — WanderWise Service Worker v2
 *
 * Rules:
 * - NEVER return undefined from a fetch handler (causes TypeError crash)
 * - NEVER intercept POST requests
 * - NEVER cache API responses from localhost:8000
 * - Navigation → network-first, fall back to cached app shell
 * - Static assets (.js/.css/.png etc) → cache-first
 * - Everything else → network-only, with a safe offline fallback Response
 */

const CACHE_NAME = 'wanderwise-v2';
const SHELL_URLS = ['/', '/index.html', '/manifest.json'];

// ── Install: pre-cache the app shell ──────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS))
  );
  self.skipWaiting();
});

// ── Activate: delete old caches ───────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ── Offline fallback HTML ──────────────────────────────────────────────
function offlineFallback() {
  return new Response(
    `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>WanderWise — Offline</title>
<style>
  body { font-family: system-ui, sans-serif; background: #0f0a1e; color: #e2e8f0;
         display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
  .card { text-align: center; padding: 2rem; }
  h1 { color: #a78bfa; font-size: 1.5rem; margin-bottom: 1rem; }
  p  { color: #94a3b8; font-size: 0.875rem; }
</style>
</head>
<body>
  <div class="card">
    <h1>✈️ WanderWise</h1>
    <p>You are offline. Please check your connection.</p>
  </div>
</body>
</html>`,
    { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
  );
}

// ── Fetch handler ─────────────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 1. Never intercept non-GET requests (POST/PUT/DELETE etc.)
  if (request.method !== 'GET') return;

  // 2. Never intercept backend API calls (localhost:8000)
  if (url.hostname === 'localhost' && url.port === '8000') return;
  if (url.hostname === '127.0.0.1' && url.port === '8000') return;

  // 3. Never intercept external API calls (Open-Meteo, Nominatim, Overpass, Frankfurter)
  const externalApis = [
    'api.open-meteo.com',
    'geocoding-api.open-meteo.com',
    'nominatim.openstreetmap.org',
    'overpass-api.de',
    'routing.transitous.org',
    'photon.komoot.io',
    'api.exchangerate-api.com',
    'router.project-osrm.org',
  ];
  if (externalApis.some((host) => url.hostname.includes(host))) return;

  // 4. Navigation requests → network-first, cache fallback, offline HTML
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((res) => {
          // Cache the fresh navigation response
          const clone = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(request, clone));
          return res;
        })
        .catch(() =>
          caches.match('/index.html').then((cached) => cached || offlineFallback())
        )
    );
    return;
  }

  // 5. Static assets → cache-first, network fallback
  if (/\.(js|mjs|css|png|jpg|jpeg|webp|svg|ico|woff2?|ttf)(\?.*)?$/.test(url.pathname)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(request, clone));
          }
          return res;
        }).catch(() =>
          // Must ALWAYS return a Response — never undefined
          new Response('/* offline */', { status: 503, headers: { 'Content-Type': 'text/plain' } })
        );
      })
    );
    return;
  }

  // 6. Everything else → network-only with a safe fallback Response
  // CRITICAL: catch MUST return a valid Response, never undefined
  event.respondWith(
    fetch(request).catch(() =>
      caches.match(request).then((cached) =>
        cached ||
        new Response(JSON.stringify({ error: 'offline', message: 'Network unavailable' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        })
      )
    )
  );
});
