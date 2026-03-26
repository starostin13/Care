/**
 * Offline Sync Module for CareBot Admin Panel
 * 
 * ARCHITECTURE:
 * ============
 * Offline App contains:
 * 1. Mission Generation Templates - Rules/types for CREATING new missions
 * 2. Active Missions - Current missions that need result entry  
 * 3. Map Data - Territory edges for adjacency calculations
 *
 * Offline Workflow:
 * 1. App downloads templates, active_missions, and map -> cached in SQLite
 * 2. App GENERATES new mission offline using templates (rules stored locally)
 *    OR selects existing mission from active_missions
 * 3. User enters battle RESULT (winner, loser, location)
 * 4. App saves result locally -> ready for sync
 *
 * Server Sync Workflow:
 * 1. User reconnects to internet
 * 2. App POST to /api/mobile/sync-results with battle result
 * 3. Server applies effects:
 *    - Kill Team: Territory capture (Secure), Depot (Intel), Destruction (Coordinates)
 *    - WH40K: Reveal winner_bonus to winner only
 * 4. Server returns success -> App updates status
 * 5. Results now apply to LIVE game state on server
 *
 * Security Note:
 * - winner_bonus is SECRET and NOT exported in cache
 * - Only server can calculate/reveal winner_bonus after sync
 * - Only winner can view their bonus via /api/mobile/wh40k-winner-bonus/{id}
 */

const CareBotSync = {
    API_BASE: 'http://192.168.1.125:5555/api/mobile',
    
    /**
     * Initialize offline sync - called on app startup
     * Downloads generation templates, active missions, and map data
     */
    async init() {
        console.log('[Sync] Initializing offline sync...');
        
        // Check if running in Android WebView
        if (typeof window.Android === 'undefined') {
            console.log('[Sync] Not running in Android WebView - using web-only mode');
            return;
        }
        
        // Cache initial data for offline mission generation
        await this.downloadAndCache();
        
        // Set up periodic sync (every 5 minutes when online)
        setInterval(() => this.syncPendingChanges(), 5 * 60 * 1000);
    },
    
    /**
     * Download generation templates, active missions, and map for offline usage.
     * 
     * Data structure:
     * {
     *   generation_templates: {
     *     kill_team: [...],  // Templates for creating Kill Team missions
     *     wh40k: [...]       // Templates for creating WH40K missions
     *   },
     *   active_missions: [...],  // Existing missions that need results
     *   map: {
     *     hex_locations: [...],
     *     adjacency: [...]   // Territory edges for territory calculations
     *   }
     * }
     */
    async downloadAndCache() {
        try {
            console.log('[Sync] Downloading generation templates, active missions, and map...');
            
            const response = await fetch(`${this.API_BASE}/data-export`);
            const data = await response.json();
            
            if (data.status !== 'ok') {
                throw new Error(data.error || 'Failed to export data');
            }
            
            // Store generation templates in SQLite (for creating NEW missions)
            if (window.Android && data.generation_templates) {
                await this.storeCachedData('generation_templates', data.generation_templates);
                console.log(`[Sync] Cached generation templates (Kill Team + WH40K)`);
            }
            
            // Store active missions in SQLite (existing missions needing results)
            if (window.Android && data.active_missions && data.active_missions.missions) {
                const result = JSON.parse(
                    window.Android.cacheMissions(JSON.stringify(data.active_missions.missions))
                );
                console.log(`[Sync] Cached ${result.cached} active missions`);
            }
            
            // Store map data in IndexedDB (for territory calculation)
            if (data.map) {
                await this.storeCachedData('map_data', data.map);
                console.log(
                    `[Sync] Cached ${data.map.hex_locations?.length || 0} hex locations ` +
                    `and ${data.map.adjacency?.length || 0} territory edges`
                );
            }
            
            return true;
        } catch (error) {
            console.error('[Sync] Error downloading cache:', error);
            return false;
        }
    },

    
    /**
     * Get cached missions from Android SQLite
     */
    async getCachedMissions() {
        if (typeof window.Android === 'undefined') {
            return [];
        }
        
        try {
            const result = JSON.parse(window.Android.getCachedMissions());
            return result.missions || [];
        } catch (error) {
            console.error('[Sync] Error getting cached missions:', error);
            return [];
        }
    },
    
    /**
     * Get mission generation templates for creating NEW missions offline.
     * 
     * Contains mission types and rules for both ruleset:
     * - Kill Team: Territory-based missions (Secure, Intel, Coordinates, etc.)
     * - WH40K: Victory-based missions (Mantle of Steel, etc.)
     *
     * Returns:
     * {
     *   kill_team: [{type, reward, description}, ...],
     *   wh40k: [{type, reward, description}, ...]
     * }
     */
    async getGenerationTemplates() {
        try {
            const templates = await this.getCachedData('generation_templates');
            if (!templates) {
                console.warn('[Sync] Generation templates not cached - download cache first');
                return { kill_team: [], wh40k: [] };
            }
            return templates.templates || { kill_team: [], wh40k: [] };
        } catch (error) {
            console.error('[Sync] Error getting generation templates:', error);
            return { kill_team: [], wh40k: [] };
        }
    },
    
    /**
     * Get map data (hex locations and territory adjacency).
     *
     * Returns:
     * {
     *   hex_locations: ['A1', 'A2', 'B1', ...],  // Available territories
     *   adjacency: [{from: 'A1', to: 'B1'}, ...]  // Adjacent territories
     * }
     */
    async getMapData() {
        try {
            const mapData = await this.getCachedData('map_data');
            if (!mapData) {
                console.warn('[Sync] Map data not cached - download cache first');
                return { hex_locations: [], adjacency: [] };
            }
            return mapData;
        } catch (error) {
            console.error('[Sync] Error getting map data:', error);
            return { hex_locations: [], adjacency: [] };
        }
    },
    
    /**
     * Generate new mission offline using templates.
     * 
     * This is called by the offline app to CREATE a new mission locally.
     * The generated mission is then saved with a battle result for sync.
     *
     * Returns:
     * {
     *   mission: {generated mission data},
     *   can_generate: true/false,
     *   reason: 'error message if failed'
     * }
     */
    async generateMissionOffline(ruleSet, preferences) {
        try {
            // ruleSet: 'kill_team' or 'wh40k'
            // preferences: {missionType, location, reward, ...}
            
            const templates = await this.getGenerationTemplates();
            const mapData = await this.getMapData();
            
            if (!templates[ruleSet] || templates[ruleSet].length === 0) {
                return { can_generate: false, reason: 'No templates available for ' + ruleSet };
            }
            
            if (!mapData.hex_locations || mapData.hex_locations.length === 0) {
                return { can_generate: false, reason: 'Map data not available' };
            }
            
            // Select template
            let template = preferences.missionType ? 
                templates[ruleSet].find(t => t.type === preferences.missionType) :
                templates[ruleSet][Math.floor(Math.random() * templates[ruleSet].length)];
            
            if (!template) {
                return { can_generate: false, reason: 'Mission type not found in templates' };
            }
            
            // Select location
            const location = preferences.location || 
                mapData.hex_locations[Math.floor(Math.random() * mapData.hex_locations.length)];
            
            // Generated mission (offline, no ID yet)
            const generatedMission = {
                offline_id: 'offline_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
                type: template.type,
                rules: ruleSet,
                reward: template.reward,
                location: location,
                description: template.description,
                generated_at: new Date().toISOString(),
                status: 'pending'
            };
            
            console.log('[Sync] Generated mission offline:', generatedMission);
            return {
                mission: generatedMission,
                can_generate: true
            };
        } catch (error) {
            console.error('[Sync] Error generating mission:', error);
            return { can_generate: false, reason: error.message };
        }
    },
    
    /**
     * Save battle result for offline sync
     */
    async saveBattleResult(missionId, winnerId, loserId, missionType, location) {
        if (typeof window.Android === 'undefined') {
            console.warn('[Sync] Android bridge not available - battle result not saved');
            return false;
        }
        
        try {
            const result = JSON.parse(
                window.Android.savePendingBattleResult(JSON.stringify({
                    mission_id: missionId,
                    winner_id: winnerId,
                    loser_id: loserId,
                    mission_type: missionType,
                    location: location,
                    timestamp: new Date().toISOString()
                }))
            );
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            console.log('[Sync] Battle result saved locally:', result.id);
            
            // Try to sync immediately if online
            await this.syncIfOnline();
            
            return true;
        } catch (error) {
            console.error('[Sync] Error saving battle result:', error);
            return false;
        }
    },
    
    /**
     * Sync pending changes if online
     */
    async syncIfOnline() {
        try {
            // Check if online
            if (!navigator.onLine) {
                console.log('[Sync] Offline - skipping sync');
                return false;
            }
            
            return await this.syncPendingChanges();
        } catch (error) {
            console.log('[Sync] Sync skipped:', error.message);
            return false;
        }
    },
    
    /**
     * Synchronize all pending changes with server
     */
    async syncPendingChanges() {
        if (typeof window.Android === 'undefined') {
            console.warn('[Sync] Android bridge not available');
            return false;
        }
        
        try {
            // Get pending battles
            const pendingJson = window.Android.getPendingBattles();
            const pending = JSON.parse(pendingJson);
            
            if (pending.pending === 0) {
                console.log('[Sync] No pending changes to sync');
                return true;
            }
            
            console.log(`[Sync] Syncing ${pending.pending} pending battles...`);
            
            // Get warmaster ID from page (admin should be logged in)
            const warmasterId = this.getCurrentWarmasterId();
            if (!warmasterId) {
                throw new Error('No warmaster ID found - user must be authenticated');
            }
            
            // Send to server
            const response = await fetch(`${this.API_BASE}/sync-results`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    warmaster_id: warmasterId,
                    results: pending.battles
                })
            });
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            console.log(`[Sync] Synced ${result.processed} battles`);
            console.log('[Sync] Territories affected:', result.territories_affected);
            console.log('[Sync] WH40K bonuses revealed:', result.winner_bonuses);
            
            // Mark as synced locally
            if (result.processed > 0) {
                const battleIds = pending.battles.map(b => b.id);
                window.Android.markBattlesAsSynced(JSON.stringify(battleIds));
                
                // Build notification message
                let message = `${result.processed} battles synced`;
                if (result.territories_affected && result.territories_affected.length > 0) {
                    message += ` (${result.territories_affected.length} territories)`;
                }
                if (result.winner_bonuses && Object.keys(result.winner_bonuses).length > 0) {
                    message += ' - WH40K bonuses revealed!';
                }
                
                // Show notification with both territory and WH40K info
                this.showSyncNotification(message, 'success', result);
            }
            
            return true;
        } catch (error) {
            console.error('[Sync] Error during sync:', error);
            this.showSyncNotification(`Sync failed: ${error.message}`, 'error');
            return false;
        }
    },
    
    /**
     * Get WH40K winner bonus (only for winners!)
     */
    async getWH40kWinnerBonus(missionId) {
        try {
            const response = await fetch(`/api/mobile/wh40k-winner-bonus/${missionId}`);
            const bonus = await response.json();
            
            if (!bonus.authorized) {
                console.warn(`[Sync] Not authorized to view bonus for mission ${missionId}`);
                return null;
            }
            
            console.log(`[Sync] WH40K bonus revealed for mission ${missionId}:`, bonus.bonus);
            return bonus;
        } catch (error) {
            console.error('[Sync] Error getting WH40K bonus:', error);
            return null;
        }
    },
    
    /**
     * Get sync status from server
     */
    async getSyncStatus() {
        try {
            const response = await fetch(`${this.API_BASE}/sync-status`);
            return await response.json();
        } catch (error) {
            console.error('[Sync] Error getting sync status:', error);
            return null;
        }
    },
    
    /**
     * Store data in IndexedDB for caching
     */
    async storeCachedData(key, data) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('CareBotOffline', 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                const db = request.result;
                const tx = db.transaction('cache', 'readwrite');
                tx.objectStore('cache').put({ key, data, timestamp: Date.now() });
                resolve();
            };
            
            request.onupgradeneeded = (e) => {
                const db = e.target.result;
                if (!db.objectStoreNames.contains('cache')) {
                    db.createObjectStore('cache', { keyPath: 'key' });
                }
            };
        });
    },
    
    /**
     * Retrieve data from IndexedDB cache
     */
    async getCachedData(key) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('CareBotOffline', 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                const db = request.result;
                const tx = db.transaction('cache', 'readonly');
                const get = tx.objectStore('cache').get(key);
                get.onsuccess = () => resolve(get.result?.data);
            };
        });
    },
    
    /**
     * Get current warmaster ID from page
     */
    getCurrentWarmasterId() {
        // This should be available from the authenticated admin session
        // Could be in localStorage, session storage, or a data attribute
        const el = document.querySelector('[data-warmaster-id]');
        if (el) return parseInt(el.dataset.warmasterId);
        
        // Fallback - try to get from page text or URL
        return null;
    },
    
    /**
     * Show sync notification to user
     */
    showSyncNotification(message, type = 'success', syncResult = null) {
        console.log(`[Sync ${type}] ${message}`);
        
        // Create toast notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : 'success'}`;
        
        // Build detailed message for important syncs
        let html = `🔄 ${message}`;
        
        if (syncResult && type === 'success') {
            // Add territory info for Kill Team
            if (syncResult.territories_affected && syncResult.territories_affected.length > 0) {
                html += `<br/><small>📍 Territories: ${syncResult.territories_affected.join(', ')}</small>`;
            }
            
            // Add WH40K bonus info
            if (syncResult.winner_bonuses && Object.keys(syncResult.winner_bonuses).length > 0) {
                const bonusCount = Object.keys(syncResult.winner_bonuses).length;
                html += `<br/><small>⭐ WH40K: ${bonusCount} winner bonus(es) revealed!</small>`;
            }
        }
        
        notification.innerHTML = html;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => notification.remove(), 5000);
    },
    
    /**
     * Clear all local cache
     */
    async clearAllCache() {
        if (typeof window.Android === 'undefined') {
            console.warn('[Sync] Android bridge not available');
            return false;
        }
        
        try {
            const result = JSON.parse(window.Android.clearAllCache());
            console.log('[Sync] Cache cleared');
            return !result.error;
        } catch (error) {
            console.error('[Sync] Error clearing cache:', error);
            return false;
        }
    }
};

// Auto-initialize when page loads
document.addEventListener('DOMContentLoaded', () => CareBotSync.init());
