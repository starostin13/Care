/**
 * Offline Storage Helper for CareBot
 * Manages IndexedDB for offline data persistence and sync queue
 */

class OfflineStorage {
    constructor() {
        this.dbName = 'CareBotOffline';
        this.dbVersion = 1;
        this.db = null;
    }

    /**
     * Initialize IndexedDB
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => {
                console.error('[OfflineStorage] Error opening database:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                console.log('[OfflineStorage] Database opened successfully');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create stores if they don't exist
                if (!db.objectStoreNames.contains('pendingRequests')) {
                    const pendingStore = db.createObjectStore('pendingRequests', {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    pendingStore.createIndex('timestamp', 'timestamp', { unique: false });
                    pendingStore.createIndex('url', 'url', { unique: false });
                }

                if (!db.objectStoreNames.contains('cachedBattles')) {
                    const battlesStore = db.createObjectStore('cachedBattles', {
                        keyPath: 'battle_id'
                    });
                    battlesStore.createIndex('timestamp', 'timestamp', { unique: false });
                    battlesStore.createIndex('status', 'status', { unique: false });
                }

                if (!db.objectStoreNames.contains('offlineSettings')) {
                    db.createObjectStore('offlineSettings', { keyPath: 'key' });
                }

                console.log('[OfflineStorage] Database schema created');
            };
        });
    }

    /**
     * Add a request to the pending queue
     */
    async addPendingRequest(url, method, headers, body) {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(['pendingRequests'], 'readwrite');
            const store = tx.objectStore('pendingRequests');

            const request = store.add({
                url,
                method,
                headers,
                body,
                timestamp: Date.now()
            });

            request.onsuccess = () => {
                console.log('[OfflineStorage] Pending request added:', url);
                resolve(request.result);
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Error adding pending request:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Get all pending requests
     */
    async getPendingRequests() {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(['pendingRequests'], 'readonly');
            const store = tx.objectStore('pendingRequests');
            const request = store.getAll();

            request.onsuccess = () => {
                console.log('[OfflineStorage] Retrieved pending requests:', request.result.length);
                resolve(request.result);
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Error getting pending requests:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Delete a pending request by ID
     */
    async deletePendingRequest(id) {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(['pendingRequests'], 'readwrite');
            const store = tx.objectStore('pendingRequests');
            const request = store.delete(id);

            request.onsuccess = () => {
                console.log('[OfflineStorage] Pending request deleted:', id);
                resolve();
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Error deleting pending request:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Clear all pending requests
     */
    async clearPendingRequests() {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(['pendingRequests'], 'readwrite');
            const store = tx.objectStore('pendingRequests');
            const request = store.clear();

            request.onsuccess = () => {
                console.log('[OfflineStorage] All pending requests cleared');
                resolve();
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Error clearing pending requests:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Cache battle data for offline access
     */
    async cacheBattle(battleData) {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(['cachedBattles'], 'readwrite');
            const store = tx.objectStore('cachedBattles');

            const data = {
                ...battleData,
                timestamp: Date.now()
            };

            const request = store.put(data);

            request.onsuccess = () => {
                console.log('[OfflineStorage] Battle cached:', battleData.battle_id);
                resolve(request.result);
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Error caching battle:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Get cached battles
     */
    async getCachedBattles() {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(['cachedBattles'], 'readonly');
            const store = tx.objectStore('cachedBattles');
            const request = store.getAll();

            request.onsuccess = () => {
                console.log('[OfflineStorage] Retrieved cached battles:', request.result.length);
                resolve(request.result);
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Error getting cached battles:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Set a setting value
     */
    async setSetting(key, value) {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(['offlineSettings'], 'readwrite');
            const store = tx.objectStore('offlineSettings');
            const request = store.put({ key, value });

            request.onsuccess = () => {
                console.log('[OfflineStorage] Setting saved:', key);
                resolve();
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Error saving setting:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Get a setting value
     */
    async getSetting(key, defaultValue = null) {
        if (!this.db) await this.init();

        return new Promise((resolve, reject) => {
            const tx = this.db.transaction(['offlineSettings'], 'readonly');
            const store = tx.objectStore('offlineSettings');
            const request = store.get(key);

            request.onsuccess = () => {
                const result = request.result ? request.result.value : defaultValue;
                console.log('[OfflineStorage] Setting retrieved:', key, result);
                resolve(result);
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Error getting setting:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Close database connection
     */
    close() {
        if (this.db) {
            this.db.close();
            this.db = null;
            console.log('[OfflineStorage] Database closed');
        }
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OfflineStorage;
}
