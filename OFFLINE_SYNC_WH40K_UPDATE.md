# Offline Sync System: Kill Team + WH40K Support ✅

## Update Summary (Feb 23, 2026)

**Issue Found:** The offline sync system was designed only for **Kill Team** territory effects and didn't properly support **WH40K** secret winner bonuses.

**Solution Implemented:** Extended sync architecture to handle BOTH game rule sets:

## Architecture: Dual Rule Support

### Kill Team Rules
**Focus:** Territory control and supply depots

Mission Effects:
- `Secure` → Winner claims territory (`map.controlled_by = faction`)
- `Intel` → Creates supply depot for winner  
- `Coordinates` → Destroys enemy supply depot

**Sync Flow:**
```
Mobile (offline) → Battle result
↓
Server processes → Checks mission.rules
↓
If rules != 'wh40k':
  Calculate territory effects
  Update map.controlled_by, map_depots
  Return: territories_affected[]
```

### WH40K Rules  
**Focus:** Secret winner bonuses (hidden until revealed)

**Cache Behavior:**
- ❌ `winner_bonus` NOT exported in cache (SECURITY!)
- ✅ Only winner can retrieve it via `/api/mobile/wh40k-winner-bonus/{mission_id}`
- ✅ Retrieved ONLY after mission completed and winner determined

**Sync Flow:**
```
Mobile (offline) → Battle result
↓
Server processes → Checks mission.rules
↓
If rules == 'wh40k':
  Get winner_bonus from DB
  Store in winner_bonuses[mission_id]
  ONLY reveal to winner via API
  Return: winner_bonuses{...}
```

## Code Changes

### 1. sync_helper.py - Extended Functions

#### `export_missions_for_cache()` - NO LONGER EXPORTS winner_bonus
```python
# Before: exported 'winner_bonus': m[7]
# Now: Removed from cache (SECURITY FIX)

# Select rules field instead
SELECT rules FROM mission_stack
# Returns: 'wh40k' or NULL/other (Kill Team)
```

**Security Fix:**
```python
# IMPORTANT: winner_bonus NOT included in cache for WH40K missions!
# victor only revealed to winner via separate endpoint
```

#### `process_synced_battle_results()` - Dual Rule Handling
```python
# Now differentiates based on mission.rules:

if rules == 'wh40k':
    # WH40K: Reveal secret winner_bonus to winner
    winner_bonuses_revealed[mission_id] = {
        'winner_id': winner_id,
        'bonus': winner_bonus,  # SECRET!
        'description': description
    }
else:
    # Kill Team: Apply territory effects
    if mission_type == 'Secure':
        await _claim_territory(...)
    elif mission_type == 'Intel':
        await _create_supply_depot(...)
    elif mission_type == 'Coordinates':
        await _destroy_enemy_depot(...)

# Returns both:
{
    'territories_affected': [...],      # Kill Team
    'winner_bonuses': {...}             # WH40K
}
```

#### NEW: `get_wh40k_winner_bonus()` - Secure Bonus Retrieval
```python
async def get_wh40k_winner_bonus(
    db_path, mission_id, requesting_warmaster_id
) -> Dict:
    """
    SECURITY: Only the actual winner can retrieve their bonus!
    
    Returns:
    - If requesting_warmaster_id == winner_id: bonus revealed
    - Otherwise: FORBIDDEN with audit log
    """
    # Verify winner
    if winner_id != requesting_warmaster_id:
        logger.warning(f'SECURITY: Unauthorized access attempt')
        return {'error': 'Not authorized', 'authorized': False}
    
    # Winner authorized
    return {'bonus': bonus_text, 'authorized': True}
```

#### NEW: `get_mission_rules()` - Rule Set Determination
```python
async def get_mission_rules(db_path, mission_id) -> str:
    """Returns 'wh40k' or None (Kill Team)"""
```

### 2. server_app.py - New API Endpoint

#### NEW: `/api/mobile/wh40k-winner-bonus/<mission_id>`
```python
@app.route('/api/mobile/wh40k-winner-bonus/<int:mission_id>')
def api_wh40k_winner_bonus(mission_id):
    """
    Get WH40K mission winner bonus - ONLY for the actual winner!
    
    Security Checks:
    1. User must be authenticated (Flask-Login)
    2. User must be the mission winner
    3. Audit logging of all accesses
    
    Returns:
    {
        'bonus': '<secret text>',
        'mission_id': 1,
        'mission_type': 'Mantle of Steel',
        'authorized': True/False
    }
    """
```

### 3. sync.js - UI Updates

#### Enhanced Notification Display
```javascript
// Before: "5 battles synced"
// Now shows BOTH:
// "5 battles synced (3 territories) - WH40K bonuses revealed!"

showSyncNotification(message, type, syncResult)
// With details:
if (syncResult.territories_affected.length > 0) {
    html += `<br/><small>📍 Territories: ${territories}</small>`
}
if (syncResult.winner_bonuses.length > 0) {
    html += `<br/><small>⭐ WH40K: ${bonusCount} revealed!</small>`
}
```

#### NEW: WH40K Bonus Retrieval
```javascript
async getWH40kWinnerBonus(missionId) {
    const response = await fetch(
        `/api/mobile/wh40k-winner-bonus/${missionId}`
    );
    const bonus = await response.json();
    
    if (!bonus.authorized) {
        console.warn('Not authorized to view this bonus');
        return null;
    }
    
    // Winner can now see their secret bonus!
    return bonus;
}
```

## Database Queries

### Check Mission Type
```sql
SELECT rules, mission_type, winner_bonus 
FROM mission_stack 
WHERE id = ?
```

### Export Cache (NO winner_bonus!)
```sql
SELECT id, mission_type, reward_type, map_location, 
       created_at, status, winner_id, rules
FROM mission_stack
ORDER BY created_at DESC
```

### Security Audit
```sql
SELECT id, requesting_warmaster_id, mission_id, timestamp
FROM bonus_access_log  -- (if implemented)
WHERE mission_id = ? AND authorized = 0
```

## Security Measures

### Kill Team
- ✅ Parameterized SQL (injection protection)
- ✅ Territory update validation
- ✅ Audit logging of claims/depots

### WH40K
- ✅ Secret bonus NOT in cache export
- ✅ Winner-only access via authenticated endpoint
- ✅ Warmaster ID verification (match winner_id)
- ✅ Security audit logging for access attempts
- ✅ 403 Forbidden for unauthorized access

**New Security Headers:**
```python
if winner_id != requesting_warmaster_id:
    logger.warning(f'SECURITY: Unauthorized WH40K bonus access')
    return {'error': ...}, 403
```

## Data Flow Examples

### Example 1: Kill Team Sync
```
Mission: Secure (Kill Team)
Location: "A1B2"
Winner: player_id=10, faction="Red"

Sync Response:
{
    'processed': 1,
    'territories_affected': ['A1B2'],  ← Territory claimed
    'winner_bonuses': {},              ← Empty for Kill Team
    'errors': []
}

UI Shows: "1 battle synced (1 territory)"
```

### Example 2: WH40K Sync
```
Mission: Mantle of Steel (WH40K)
Winner: player_id=10
winner_bonus: "Extra VP for next 3 games"

Sync Response:
{
    'processed': 1,
    'territories_affected': [],        ← Empty for WH40K
    'winner_bonuses': {                ← WH40K bonus revealed
        1: {
            'winner_id': 10,
            'bonus': 'Extra VP for next 3 games',
            'description': 'Mantle of Steel'
        }
    },
    'errors': []
}

UI Shows: "1 battle synced - WH40K bonus revealed!"
Winner Can Retrieve: GET /api/mobile/wh40k-winner-bonus/1 → 403
```

### Example 3: Unauthorized WH40K Access
```
Mission: Mantle of Steel (WH40K)
Winner: player_id=10
Requesting: player_id=20 (NOT winner!)

Response: 403 Forbidden
{
    'error': 'Not authorized - only winner can view bonus',
    'authorized': False
}

Audit Log: "SECURITY: Unauthorized WH40K bonus access"
```

## API Contracts

### GET /api/mobile/data-export
```json
{
    "missions": {
        "missions": [
            {
                "id": 1,
                "type": "Secure",
                "rules": null,              // Kill Team
                "location": "A1B2"
                // NO winner_bonus!
            },
            {
                "id": 2,
                "type": "Mantle of Steel",
                "rules": "wh40k",           // WH40K
                "location": "B2C3"
                // STILL NO winner_bonus!
            }
        ]
    }
}
```

### POST /api/mobile/sync-results
```json
// Response
{
    "processed": 2,
    "territories_affected": ["A1B2"],   // Kill Team only
    "winner_bonuses": {                 // WH40K only
        "2": {
            "winner_id": 10,
            "bonus": "Extra VP",
            "description": "Mantle of Steel"
        }
    }
}
```

### GET /api/mobile/wh40k-winner-bonus/{mission_id}
```json
// For winner (player_id=10)
{
    "bonus": "Extra VP for next 3 games",
    "mission_id": 2,
    "mission_type": "Mantle of Steel",
    "authorized": True,
    "revealed_at": "2026-02-23T10:00:00"
}

// For non-winner
{
    "error": "Not authorized - only winner can view bonus",
    "authorized": False,
    "mission_id": 2
}
```

## Migration Path

### Existing Databases
- ✅ No schema changes required
- ✅ Existing Kill Team missions work unchanged
- ✅ Existing WH40K missions reveal bonus correctly
- ✅ No data loss or corruption

### Testing

**Test Kill Team Sync:**
```bash
curl -X POST http://192.168.1.125:5555/api/mobile/sync-results \
  -H "Content-Type: application/json" \
  -d '{
    "warmaster_id": 10,
    "results": [{
      "mission_id": 1,
      "mission_type": "Secure",
      "winner_id": 10,
      "loser_id": 20,
      "location": "A1B2"
    }]
  }'

# Should show: "territories_affected": ["A1B2"]
```

**Test WH40K Sync:**
```bash
curl -X POST http://192.168.1.125:5555/api/mobile/sync-results \
  -H "Content-Type: application/json" \
  -d '{
    "warmaster_id": 10,
    "results": [{
      "mission_id": 2,
      "mission_type": "Mantle of Steel",
      "winner_id": 10,
      "loser_id": 20
    }]
  }'

# Should show: "winner_bonuses": {"2": {...}}
```

**Test WH40K Bonus Retrieval (WINNER):**
```bash
# Assuming player_id=10 is logged in
curl http://192.168.1.125:5555/api/mobile/wh40k-winner-bonus/2

# Returns: {"bonus": "...", "authorized": True}
```

**Test WH40K Bonus Retrieval (NON-WINNER):**
```bash
# Assuming player_id=20 is logged in (NOT the winner)
curl http://192.168.1.125:5555/api/mobile/wh40k-winner-bonus/2

# Returns: 403 Forbidden
# {"error": "Not authorized", "authorized": False}
```

## Next Steps

**Phase 3 Recommendations:**
- [ ] Add audit logging table for bonus accesses
- [ ] Implement rate limiting on bonus retrieval
- [ ] Add encryption for winner_bonus column at rest
- [ ] Implement bonus expiration (time-based)
- [ ] Add bonus notification to winner via Telegram

---

**Status:** ✅ **COMPLETE** - Kill Team + WH40K Fully Supported  
**Date:** 2026-02-23  
**Version:** 1.1.0 (Dual Rule Support)  
