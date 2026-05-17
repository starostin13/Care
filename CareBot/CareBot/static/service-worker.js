/**
 * Service Worker for CareBot PWA
 * Provides offline functionality with caching and background sync
 */

const CACHE_VERSION = 'carebot-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const API_CACHE = `${CACHE_VERSION}-api`;

// Static assets to cache immediately
const STATIC_ASSETS = [
    '/battles',
    '/static/content/bootstrap.min.css',
    '/static/manifest.json',
    '/offline.html'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name.startsWith('carebot-') && name !== STATIC_CACHE && name !== DYNAMIC_CACHE && name !== API_CACHE)
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - network first, then cache fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests and chrome-extension requests
    if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
        return;
    }

    // API requests - network first with cache fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Clone response to cache it
                    const responseClone = response.clone();
                    caches.open(API_CACHE).then((cache) => {
                        cache.put(request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    // If network fails, try cache
                    return caches.match(request)
                        .then((cached) => {
                            if (cached) {
                                console.log('[SW] Serving API from cache:', request.url);
                                return cached;
                            }
                            // Return error response if no cache
                            return new Response(
                                JSON.stringify({ ok: false, error: 'Нет соединения с сервером', offline: true }),
                                { status: 503, headers: { 'Content-Type': 'application/json' } }
                            );
                        });
                })
        );
        return;
    }

    // Static assets and pages - cache first with network fallback
    event.respondWith(
        caches.match(request)
            .then((cached) => {
                if (cached) {
                    console.log('[SW] Serving from cache:', request.url);
                    return cached;
                }

                // Try network
                return fetch(request)
                    .then((response) => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type === 'error') {
                            return response;
                        }

                        // Cache images, fonts, and static files
                        if (url.pathname.match(/\.(png|jpg|jpeg|svg|gif|woff|woff2|ttf|css|js)$/)) {
                            const responseClone = response.clone();
                            caches.open(DYNAMIC_CACHE).then((cache) => {
                                cache.put(request, responseClone);
                            });
                        }

                        return response;
                    })
                    .catch(() => {
                        // If network fails, show offline page for navigation requests
                        if (request.destination === 'document') {
                            return caches.match('/offline.html');
                        }
                        return new Response('Offline', { status: 503 });
                    });
            })
    );
});

// Background sync for pending requests
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync event:', event.tag);

    if (event.tag === 'sync-pending-requests') {
        event.waitUntil(syncPendingRequests());
    }
});

// Sync pending requests from IndexedDB
async function syncPendingRequests() {
    console.log('[SW] Syncing pending requests...');

    try {
        // Open IndexedDB
        const db = await openDB();
        const tx = db.transaction('pendingRequests', 'readonly');
        const store = tx.objectStore('pendingRequests');
        const requests = await getAllFromStore(store);

        console.log('[SW] Found pending requests:', requests.length);

        // Process each pending request
        for (const item of requests) {
            try {
                const response = await fetch(item.url, {
                    method: item.method,
                    headers: item.headers,
                    body: item.body
                });

                if (response.ok) {
                    console.log('[SW] Successfully synced request:', item.url);
                    // Delete from IndexedDB
                    const deleteTx = db.transaction('pendingRequests', 'readwrite');
                    const deleteStore = deleteTx.objectStore('pendingRequests');
                    await deleteFromStore(deleteStore, item.id);
                }
            } catch (error) {
                console.error('[SW] Failed to sync request:', item.url, error);
            }
        }
    } catch (error) {
        console.error('[SW] Background sync failed:', error);
        throw error; // Retry sync
    }
}

// IndexedDB helpers
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('CareBotOffline', 1);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('pendingRequests')) {
                db.createObjectStore('pendingRequests', { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}

function getAllFromStore(store) {
    return new Promise((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function deleteFromStore(store, id) {
    return new Promise((resolve, reject) => {
        const request = store.delete(id);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
}

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
    console.log('[SW] Received message:', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data.type === 'CACHE_URLS') {
        event.waitUntil(
            caches.open(DYNAMIC_CACHE)
                .then((cache) => cache.addAll(event.data.urls))
        );
    }
});
