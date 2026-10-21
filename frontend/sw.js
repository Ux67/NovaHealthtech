/**
 * Nova Healthtech - Offline-First Service Worker (sw.js - v3)
 * Milestone 5: Adds Offline Essential Health Guide to cache architecture.
 */

const STATIC_CACHE_NAME = "nova-static-shell-v3";
const API_CACHE_NAME = "nova-readonly-api-v3";

const STATIC_ASSETS = [
  "/",
  "/index.html",
  "/style.css",
  "/script.js",
];

// Read-only GET endpoints cached for complete offline access
const CACHEABLE_API_PATHS = [
  "/api/benefits/catalog",
  "/api/triage/rules",
  "/api/guide/catalog",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.map((key) => {
            if (key !== STATIC_CACHE_NAME && key !== API_CACHE_NAME) {
              return caches.delete(key);
            }
            return null;
          })
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Strict Security Rule: Never cache POST/DELETE or sensitive calls
  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) {
    return;
  }

  // 1. Read-only catalog endpoints: Network-First with Cache Fallback
  if (CACHEABLE_API_PATHS.includes(url.pathname)) {
    event.respondWith(networkFirstApi(request));
    return;
  }

  // 2. Health check endpoint: Always pass through to network
  if (url.pathname === "/api/health" || url.pathname.startsWith("/api/stress-test")) {
    return;
  }

  // 3. Static Assets: Cache-First
  event.respondWith(cacheFirstStatic(request));
});

async function networkFirstApi(request) {
  const cache = await caches.open(API_CACHE_NAME);
  try {
    const networkResponse = await fetch(request);
    if (networkResponse && networkResponse.status === 200) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (err) {
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    throw err;
  }
}

async function cacheFirstStatic(request) {
  const cache = await caches.open(STATIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);

  const networkFetch = fetch(request)
    .then((networkResponse) => {
      if (networkResponse && networkResponse.status === 200) {
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    })
    .catch(() => null);

  return cachedResponse || (await networkFetch) || caches.match("/index.html");
}