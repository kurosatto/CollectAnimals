// Service worker: makes the web app installable and keeps the Field Guide and habitat working offline.
// - The page itself and habitat.js: network first, so a server update shows on the next load;
//   the cached copy is used when offline or when the server is down (the tunnel then answers 5xx).
// - Sprites, icons and vendor files: served from cache, refreshed in the background.
// - Your own game data (GET /me..., /species, /states, /map, /hotspots, /friends): network first
//   with the last answer as the offline fallback. The page clears it on log out.
// - Everything else (photos, galleries, the feed, uploads, any POST) goes straight to the network,
//   so other players' photos never fill up the phone.
const VERSION = "1";
const SHELL = `shell-v${VERSION}`;
const ASSETS = "assets-v1";
const API = "api-v1";
const SHELL_URLS = ["/", "/habitat.js", "/manifest.webmanifest", "/vendor/leaflet/leaflet.js",
  "/vendor/leaflet/leaflet.css", "/icons/icon-192.png", "/icons/favicon-32.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(SHELL_URLS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  const keep = new Set([SHELL, ASSETS, API]);
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => !keep.has(k)).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("message", (e) => {
  if (e.data === "logout") e.waitUntil(caches.delete(API));
});

const isAsset = (p) => /^\/(sprites|icons|vendor)\//.test(p);
const isGameData = (p) => /^\/(me|states|species|map|hotspots|friends)(\/|$)/.test(p)
  && !/^\/species\/[^/]+\/photos/.test(p);

self.addEventListener("fetch", (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;
  if (req.mode === "navigate") e.respondWith(networkFirst(req, SHELL, "/"));
  else if (url.pathname === "/habitat.js" || url.pathname === "/manifest.webmanifest")
    e.respondWith(networkFirst(req, SHELL));
  else if (isAsset(url.pathname)) e.respondWith(cacheFirst(req, e));
  else if (isGameData(url.pathname)) e.respondWith(networkFirst(req, API));
});

async function networkFirst(req, cacheName, fallbackUrl) {
  const cache = await caches.open(cacheName);
  try {
    const res = await fetch(req);
    if (res.ok) { cache.put(fallbackUrl || req, res.clone()); return res; }
    if (res.status < 500) return res;  // 401, 404...: a real answer, pass it on
    return (await cache.match(fallbackUrl || req)) || res;
  } catch {
    const hit = await cache.match(fallbackUrl || req);
    if (hit) return hit;
    return new Response(JSON.stringify({ detail: "You're offline" }),
      { status: 503, headers: { "Content-Type": "application/json" } });
  }
}

async function cacheFirst(req, e) {
  const cache = await caches.open(ASSETS);
  const hit = await cache.match(req);
  const refresh = fetch(req).then((res) => { if (res.ok) cache.put(req, res.clone()); return res; });
  if (hit) { e.waitUntil(refresh.catch(() => {})); return hit; }
  return refresh;
}
