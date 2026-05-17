# Offline Functionality Tests

## Manual Testing Steps

### Test 1: PWA Installation
**Steps:**
1. Open Chrome browser (or Edge)
2. Navigate to `http://localhost:5555/battles` (or production URL)
3. Wait for the install banner to appear at the bottom
4. Click "Установить" button
5. Verify app opens in standalone mode

**Expected Result:**
- Banner appears after page load
- App installs successfully
- App icon appears on device home screen
- App opens without browser UI

---

### Test 2: Service Worker Registration
**Steps:**
1. Open DevTools → Application tab → Service Workers
2. Reload the page
3. Check service worker status

**Expected Result:**
- Service worker shows as "activated and is running"
- Scope is set to root (`/`)
- No errors in console

---

### Test 3: Offline Page Loading
**Steps:**
1. Load `/battles` page (ensure it's cached)
2. Open DevTools → Network tab
3. Select "Offline" throttling
4. Reload the page

**Expected Result:**
- Page loads from cache successfully
- All static assets load from cache
- Offline indicator appears: "📡 Нет соединения"

---

### Test 4: API Request Queuing
**Steps:**
1. Ensure you're online and on `/battles` page
2. Open DevTools → Network tab
3. Select "Offline" throttling
4. Try to submit a battle result or create a battle
5. Check IndexedDB (Application tab → IndexedDB → CareBotOffline → pendingRequests)

**Expected Result:**
- Request fails gracefully
- Toast message: "Запрос сохранён и будет отправлен при восстановлении связи"
- Request appears in IndexedDB pendingRequests store
- Sync count badge shows "1" next to offline indicator

---

### Test 5: Background Sync
**Steps:**
1. Complete Test 4 (queue a request while offline)
2. Switch Network throttling back to "Online"
3. Wait 2-3 seconds

**Expected Result:**
- Background sync triggers automatically
- Request is sent to server
- Request is removed from IndexedDB
- Toast message: "✓ Данные синхронизированы"
- Page reloads with updated data
- Sync count badge disappears

---

### Test 6: Offline Fallback Page
**Steps:**
1. Clear all caches (DevTools → Application → Clear storage)
2. Set Network to "Offline"
3. Navigate to `/battles`

**Expected Result:**
- `/offline.html` page is displayed
- Shows "Нет соединения" message
- Shows list of offline features
- Status shows "Проверка соединения..."
- Page checks connection every 5 seconds

---

### Test 7: Cache Persistence
**Steps:**
1. Load `/battles` while online
2. Wait for all resources to load
3. Go offline (Network → Offline)
4. Reload the page multiple times

**Expected Result:**
- Page loads consistently from cache
- No "Failed to load resource" errors
- All images, CSS, and JS load correctly
- Battle data from last online session is visible

---

### Test 8: Online Recovery
**Steps:**
1. Start offline
2. Navigate to `/battles` (should show cached version)
3. Go back online (Network → Online)
4. Wait for online indicator

**Expected Result:**
- Green indicator appears: "✓ Соединение восстановлено"
- Indicator disappears after 3 seconds
- Any pending requests sync automatically
- Page functions normally

---

### Test 9: IndexedDB Storage
**Steps:**
1. Open DevTools → Console
2. Run:
```javascript
const storage = new OfflineStorage();
await storage.init();
await storage.setSetting('test', 'value');
const value = await storage.getSetting('test');
console.log('Retrieved:', value);
```

**Expected Result:**
- No errors in console
- Retrieved value matches: "value"
- Data persists across page reloads

---

### Test 10: Multiple Pending Requests
**Steps:**
1. Go offline
2. Try to submit 3 different battle results
3. Check sync count badge
4. Go online
5. Wait for sync

**Expected Result:**
- Sync count shows "3"
- All 3 requests appear in IndexedDB
- When online, all requests sync in order
- Toast shows "✓ Данные синхронизированы"
- All 3 battles update correctly

---

## Automated Testing Commands

### Check Service Worker Status
```javascript
navigator.serviceWorker.getRegistrations().then(regs => {
    console.log('Registrations:', regs.length);
    regs.forEach(reg => console.log('Scope:', reg.scope, 'State:', reg.active?.state));
});
```

### Force Service Worker Update
```javascript
navigator.serviceWorker.getRegistration().then(reg => {
    if (reg) reg.update();
});
```

### List All Caches
```javascript
caches.keys().then(keys => {
    console.log('Caches:', keys);
    keys.forEach(key => {
        caches.open(key).then(cache => {
            cache.keys().then(requests => {
                console.log(`Cache ${key}:`, requests.length, 'items');
            });
        });
    });
});
```

### Check IndexedDB Contents
```javascript
const storage = new OfflineStorage();
await storage.init();
const pending = await storage.getPendingRequests();
console.log('Pending requests:', pending);
const battles = await storage.getCachedBattles();
console.log('Cached battles:', battles);
```

### Trigger Manual Sync
```javascript
if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
    navigator.serviceWorker.ready.then(reg => {
        return reg.sync.register('sync-pending-requests');
    });
}
```

### Clear All Offline Data
```javascript
// Clear caches
caches.keys().then(keys => {
    keys.forEach(key => caches.delete(key));
});

// Clear IndexedDB
indexedDB.deleteDatabase('CareBotOffline');

// Unregister service worker
navigator.serviceWorker.getRegistrations().then(regs => {
    regs.forEach(reg => reg.unregister());
});
```

---

## Browser-Specific Testing

### Chrome/Edge (Desktop & Mobile)
- Full PWA support
- Background Sync API supported
- Install banner works
- Push notifications supported (future)

### Safari (iOS)
- PWA install via "Add to Home Screen"
- No install banner (manual only)
- No Background Sync API (manual sync fallback)
- Limited push notifications

### Firefox
- Service Worker supported
- No install banner
- Limited Background Sync
- Manual sync works

---

## Performance Testing

### Measure Cache Performance
```javascript
// Clear cache first
await caches.delete('carebot-v1-static');

// Measure cache time
console.time('cache-static');
const cache = await caches.open('carebot-v1-static');
await cache.addAll(['/battles', '/static/content/bootstrap.min.css']);
console.timeEnd('cache-static');

// Measure retrieval time
console.time('retrieve-static');
const cached = await cache.match('/battles');
console.timeEnd('retrieve-static');
```

### Measure IndexedDB Performance
```javascript
const storage = new OfflineStorage();
await storage.init();

// Measure write
console.time('write-pending');
await storage.addPendingRequest('/api/test', 'POST', {}, '{}');
console.timeEnd('write-pending');

// Measure read
console.time('read-pending');
const requests = await storage.getPendingRequests();
console.timeEnd('read-pending');
```

---

## Known Issues & Limitations

1. **Safari iOS**: Background Sync not supported - uses manual sync on reconnect
2. **Large Caches**: Service worker may be throttled with >50MB cache
3. **Concurrent Edits**: No conflict resolution for simultaneous offline edits
4. **Cache Expiration**: No automatic cache expiration (manual cleanup required)

---

## Debugging Tips

### Enable Service Worker Debug Logging
1. Chrome DevTools → Application → Service Workers
2. Check "Update on reload"
3. Enable "Bypass for network" for testing

### Simulate Slow Network
1. DevTools → Network → Throttling
2. Select "Slow 3G" or "Fast 3G"
3. Test sync behavior

### Test on Real Device
1. Build and deploy to production/staging
2. Install PWA on physical device
3. Turn on Airplane Mode
4. Test offline functionality

---

## Success Criteria

All tests should pass with:
- ✅ No console errors
- ✅ Service Worker active
- ✅ Caches populated correctly
- ✅ Offline page loads
- ✅ Requests queue when offline
- ✅ Automatic sync on reconnect
- ✅ PWA installs successfully
- ✅ UI indicators work correctly
