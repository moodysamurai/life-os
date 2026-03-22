const CACHE = "life-os-v3";
const CDN_CACHE = "life-os-cdn-v1";

// CDN assets that never change — cache-first is fine
const CDN_ASSETS = [
  "https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.23.2/babel.min.js"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CDN_CACHE)
      .then(c => c.addAll(CDN_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE && k !== CDN_CACHE)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);

  // API calls — always network, no cache
  if (url.hostname === "api.github.com" || url.hostname === "api.anthropic.com") {
    e.respondWith(
      fetch(e.request).catch(() => new Response("{}", { headers: { "Content-Type": "application/json" } }))
    );
    return;
  }

  // CDN assets — cache-first (they are versioned and never mutate)
  if (url.hostname === "cdnjs.cloudflare.com") {
    e.respondWith(
      caches.open(CDN_CACHE).then(c =>
        c.match(e.request).then(cached => cached || fetch(e.request).then(res => {
          if (res.ok) c.put(e.request, res.clone());
          return res;
        }))
      )
    );
    return;
  }

  // Everything else (index.html, manifest, icon) — network-first so updates
  // are picked up immediately; fall back to cache if offline
  e.respondWith(
    fetch(e.request)
      .then(res => {
        if (res.ok && e.request.method === "GET") {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
