// CareBot Admin PWA Service Worker
// Version 1.0.0

const CACHE_NAME = 'carebot-admin-v1';
const RUNTIME_CACHE = 'carebot-runtime-v1';
const DATA_CACHE = 'carebot-data-v1';

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/admin/dashboard',
  '/admin/create-mission',
  '/admin/enter-result',
  '/static/content/bootstrap.min.css',
  '/static/content/site.css',
  '/static/scripts/jquery-1.10.2.min.js',
  '/static/scripts/bootstrap.min.js',
  '/static/manifest.json'
];

// API endpoints to cache for offline
const API_ENDPOINTS = [
  '/api/admin/warmasters',
  '/api/admin/active-missions'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[ServiceWorker] Skip waiting');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');
  
  const currentCaches = [CACHE_NAME, RUNTIME_CACHE, DATA_CACHE];
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (!currentCaches.includes(cacheName)) {
              console.log('[ServiceWorker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[ServiceWorker] Claiming clients');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      caches.open(DATA_CACHE)
        .then((cache) => {
          return fetch(request)
            .then((response) => {
              // Clone response before caching
              if (response.status === 200) {
                cache.put(request, response.clone());
              }
              return response;
            })
            .catch(() => {
              // Return cached version if network fails
              console.log('[ServiceWorker] Network failed, serving from cache:', url.pathname);
              return cache.match(request);
            });
        })
    );
    return;
  }

  // Handle static assets and pages
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          console.log('[ServiceWorker] Serving from cache:', url.pathname);
          return cachedResponse;
        }

        return caches.open(RUNTIME_CACHE)
          .then((cache) => {
            return fetch(request)
              .then((response) => {
                // Cache successful responses
                if (response.status === 200) {
                  cache.put(request, response.clone());
                }
                return response;
              });
          });
      })
  );
});

// Background sync for offline mission creation and result submission
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync:', event.tag);
  
  if (event.tag === 'sync-missions') {
    event.waitUntil(syncPendingMissions());
  }
  
  if (event.tag === 'sync-results') {
    event.waitUntil(syncPendingResults());
  }
});

// Sync pending missions from IndexedDB
async function syncPendingMissions() {
  console.log('[ServiceWorker] Syncing pending missions...');
  
  // TODO: Implement IndexedDB retrieval and POST to server
  // This will be implemented in Phase 3
  
  return Promise.resolve();
}

// Sync pending results from IndexedDB  
async function syncPendingResults() {
  console.log('[ServiceWorker] Syncing pending results...');
  
  // TODO: Implement IndexedDB retrieval and POST to server
  // This will be implemented in Phase 4
  
  return Promise.resolve();
}

// Message handler for client communication
self.addEventListener('message', (event) => {
  console.log('[ServiceWorker] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_MAP_DATA') {
    // Cache map and edges data for offline mission generation
    cacheMapData(event.data.payload);
  }
});

// Cache map and edges for offline use
async function cacheMapData(data) {
  const cache = await caches.open(DATA_CACHE);
  
  // Store as synthetic responses
  await cache.put(
    new Request('/offline/map'),
    new Response(JSON.stringify(data.map), {
      headers: { 'Content-Type': 'application/json' }
    })
  );
  
  await cache.put(
    new Request('/offline/edges'),
    new Response(JSON.stringify(data.edges), {
      headers: { 'Content-Type': 'application/json' }
    })
  );
  
  console.log('[ServiceWorker] Map data cached for offline use');
}
