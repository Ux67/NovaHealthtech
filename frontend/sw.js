/**
 * Nova Healthtech - Network-First Service Worker (v22)
 * Always fetches fresh code and live API responses when online,
 * and falls back to cache only when genuinely offline.
 */

const CACHE_NAME = "nova-healthtech-network-first-v22";
const CORE_ASSETS = ["/", "/index.html", "/style.css?v=22lang", "/script.js?v=22lang"];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)).catch(() => {})
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;

  // Never intercept POST/DELETE requests or live translation/AI API calls
  if (req.method !== "GET" || req.url.includes("/api/")) {
    return;
  }

  // Network-First strategy for all GET assets
  event.respondWith(
    fetch(req)
      .then((networkRes) => {
        const copy = networkRes.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, copy)).catch(() => {});
        return networkRes;
      })
      .catch(() => caches.match(req))
  );
});