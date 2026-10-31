// Service worker: makes the web app installable and keeps the Field Guide and habitat working offline.
// - The page itself, habitat.js, decor.js(on) and minigames.js: network first, so a server update shows on the next load;
//   the cached copy is used when offline or when the server is down (the tunnel then answers 5xx).
// - Sprites, icons and vendor files: served from cache, refreshed in the background.
// - Your own game data (GET /me..., /species, /states, /map, /hotspots, /friends): network first
//   with the last answer as the offline fallback. The page clears it on log out.
// - Everything else (photos, galleries, the feed, uploads, any POST) goes straight to the network,
//   so other players' photos never fill up the phone.
const VERSION = "6";
const SHELL = `shell-v${VERSION}`;
const ASSETS = "assets-v1";
const API = "api-v1";
const SHELL_URLS = ["/", "/habitat.js", "/decor.js", "/decor.json", "/minigames.js", "/manifest.webmanifest", "/vendor/leaflet/leaflet.js",
  "/vendor/leaflet/leaflet.css", "/icons/hummingbird/icon-192.png", "/icons/hummingbird/favicon-32.png",
  "/icons/hummingbird/logo.png"];

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

// Notifications from the game server (Web Push, see backend/app/notices.py): friend requests,
// likes and comments. Skipped while the game is open in front of you; the page shows those itself.
self.addEventListener("push", (e) => {
  let d = {};
  try { d = e.data.json(); } catch {}
  e.waitUntil((async () => {
    const open = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    if (open.some((c) => c.focused && c.visibilityState === "visible")) return;
    await self.registration.showNotification(d.title || "Capture Animals", {
      body: d.body || "", tag: d.tag, renotify: !!d.tag, data: { url: d.url || "/" },
      icon: "/icons/hummingbird/icon-192.png", badge: "/icons/hummingbird/favicon-32.png" });
  })());
});

// The game server's address changes when the PC restarts, so a notification sent to an old
// address opens the current one, published on the repo's server-url branch.
const SERVER_JSON = "https://raw.githubusercontent.com/kurosatto/CollectAnimals/server-url/server.json";
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const path = e.notification.data?.url || "/";
  e.waitUntil((async () => {
    for (const c of await self.clients.matchAll({ type: "window", includeUncontrolled: true })) {
      if (new URL(c.url).origin === location.origin) { await c.focus(); return c.navigate(path).catch(() => {}); }
    }
    let base = location.origin;
    try {
      const ok = await fetch("/manifest.webmanifest", { cache: "no-store" }).then((r) => r.ok, () => false);
      if (!ok) base = (await (await fetch(SERVER_JSON, { cache: "no-store" })).json()).url.replace(/\/$/, "");
    } catch {}
    return self.clients.openWindow(base + path);
  })());
});

const isAsset = (p) => /^\/(sprites|icons|vendor)\//.test(p);
const isGameData = (p) => /^\/(me|states|species|map|hotspots|friends)(\/|$)/.test(p)
  && !/^\/species\/[^/]+\/photos/.test(p);

self.addEventListener("fetch", (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;
  if (req.mode === "navigate") e.respondWith(networkFirst(req, SHELL, "/"));
  else if (["/habitat.js", "/decor.js", "/decor.json", "/minigames.js", "/manifest.webmanifest"].includes(url.pathname))
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
