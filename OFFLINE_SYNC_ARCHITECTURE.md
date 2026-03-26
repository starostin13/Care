# Offline Sync Architecture Clarification (Feb 23, 2026)

## ✅ Architecture Confirmed

**Offline приложение содержит:**
1. ✅ **Generation Templates** - Правила для создания новых миссий локально
2. ✅ **Active Missions** - Существующие миссии для ввода результатов
3. ✅ **Map Data** - Территории и их соседство

**Результаты применяются только на сервере:**
1. ✅ Приложение отправляет результат боя
2. ✅ **Сервер** применяет эффекты (территории для Kill Team, bonuses для WH40K)
3. ✅ **Сервер** - источник истины для всех эффектов

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    OFFLINE APP                                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ SQLite Database                                          │  │
│  │ ├─ generation_templates (Kill Team & WH40K rules)       │  │
│  │ ├─ active_missions (existing missions needing results)  │  │
│  │ ├─ map_data (adjacency for territory calc)              │  │
│  │ ├─ pending_battle_results (offline entered results)     │  │
│  │ └─ [Can generate & save results WITHOUT server]         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Usage:                                                         │
│  1. Generate new mission using templates (purely local)        │
│  2. OR select from active_missions                             │
│  3. User enters battle result → saved locally                  │
│  4. User goes online → sync triggers                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ POST /api/mobile/sync-results
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SERVER                                       │
│                                                                 │
│  process_synced_battle_results()                               │
│  ├─ Check mission.rules (Kill Team vs WH40K)                  │
│  ├─ Kill Team: Apply territory effects                        │
│  │   ├─ Secure → Claim territory                             │
│  │   ├─ Intel → Create supply depot                          │
│  │   └─ Coordinates → Destroy enemy depot                    │
│  ├─ WH40K: Reveal winner_bonus to winner                     │
│  └─ Update game state (SINGLE SOURCE OF TRUTH)                │
│                                                                 │
│  Response: {                                                   │
│    territories_affected: [...],     // Kill Team              │
│    winner_bonuses: {...}            // WH40K                 │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Workflows

### Scenario 1: Offline Kill Team Mission

```
STEP 1: Download Cache (Online)
↓
GET /api/mobile/data-export
↓
Receive:
{
  generation_templates: {
    kill_team: [
      {type: "Secure", reward: "Territory", description: "..."},
      {type: "Intel", reward: "Depot", description: "..."},
      {type: "Coordinates", reward: "Enemy Destroy", description: "..."}
    ]
  },
  map: {
    hex_locations: ["A1", "B1", "C1"],
    adjacency: [{from: "A1", to: "B1"}, ...]
  }
}
↓
App stores in SQLite for offline use

STEP 2: Generate Mission Offline (No Internet)
↓
App calls: CareBotSync.generateMissionOffline('kill_team', {missionType: 'Secure'})
↓
App creates locally:
{
  offline_id: "offline_1708661800_abc123",
  type: "Secure",
  rules: "kill_team",
  location: "A1",
  status: "pending"
}
↓
App displays to user

STEP 3: User Enters Result (Offline)
↓
User enters: Winner=Player1, Loser=Player2
↓
App saves locally:
{
  mission_id: "offline_1708661800_abc123",
  winner_id: 10,
  loser_id: 20,
  mission_type: "Secure",
  location: "A1",
  timestamp: "2026-02-23T10:00:00Z"
}
↓
Result stored in SQLite pending_results table

STEP 4: Sync Online
↓
App detects internet → triggers sync
↓
POST /api/mobile/sync-results
{
  warmaster_id: 10,
  results: [{
    mission_id: "offline_1708661800_abc123",
    winner_id: 10,
    loser_id: 20,
    mission_type: "Secure",
    location: "A1"
  }]
}
↓
SERVER APPLIES EFFECT:
process_synced_battle_results()
├─ Check mission.rules = "kill_team"
├─ Check mission_type = "Secure"
├─ Call _claim_territory("A1", winner_faction)
├─ Update map.controlled_by = "Player1_Faction"
└─ Return territories_affected: ["A1"]

STEP 5: Result Confirmed
↓
App receives:
{
  processed: 1,
  territories_affected: ["A1"],
  winner_bonuses: {}
}
↓
App updates UI: "Territory claimed successfully"
```

### Scenario 2: Active Mission Result Entry

```
STEP 1: Download Cache
↓
App receives active_missions:
[
  {
    id: 42,
    type: "Intel",
    rules: "kill_team",
    location: "B2",
    status: 1,
    description: "..."
  }
]
↓
App shows user list of missions needing results

STEP 2: User Selects Existing Mission
↓
User picks mission_id=42 from the list
↓
User enters result

STEP 3-5: Same as above, but mission_id=42 (from server)
```

### Scenario 3: WH40K Secret Bonus

```
STEP 1-3: Same as Kill Team
↓
User enters result for WH40K mission

STEP 4: Sync Online
↓
POST /api/mobile/sync-results
{
  results: [{
    mission_id: 99,
    winner_id: 10,
    mission_type: "Mantle of Steel",
    ...
  }]
}
↓
SERVER APPLIES EFFECT:
process_synced_battle_results()
├─ Check mission.rules = "wh40k"
├─ Get winner_bonus from database (SECRET!)
├─ Store in winner_bonuses[99]
└─ Return only to THIS warmaster_id

STEP 5: Winner Learns Bonus (Optional)
↓
App can call: GET /api/mobile/wh40k-winner-bonus/99
↓
(Only winner can see their bonus)
Response:
{
  bonus: "Extra VP for next 3 games",
  mission_id: 99,
  authorized: True
}
↓
App shows: "Congratulations! You won: Extra VP..."
```

---

## 📋 API Contracts

### GET /api/mobile/data-export

**Purpose:** Download everything needed for offline mission generation

**Response:**
```json
{
  "status": "ok",
  "version": "1.1",
  "generation_templates": {
    "templates": {
      "kill_team": [
        {
          "type": "Secure",
          "reward": "Territory",
          "description": "Claim a territory..."
        }
      ],
      "wh40k": [
        {
          "type": "Mantle of Steel",
          "reward": "Victory",
          "description": "Secure rare artefact..."
        }
      ]
    }
  },
  "active_missions": {
    "missions": [
      {
        "id": 42,
        "type": "Intel",
        "reward": "Depot",
        "location": "B2",
        "status": 1,
        "rules": "kill_team",
        "description": "..."
      }
    ]
  },
  "map": {
    "hex_locations": ["A1", "A2", "B1", "B2", ...],
    "adjacency": [
      {"from": "A1", "to": "B1"},
      {"from": "A1", "to": "B2"}
    ]
  }
}
```

### POST /api/mobile/sync-results

**Purpose:** Sync battle results - results are applied on server only

**Request:**
```json
{
  "warmaster_id": 10,
  "results": [
    {
      "mission_id": 42,
      "winner_id": 10,
      "loser_id": 20,
      "mission_type": "Secure",
      "location": "A1",
      "timestamp": "2026-02-23T10:00:00Z"
    }
  ]
}
```

**Response (Kill Team):**
```json
{
  "processed": 1,
  "territories_affected": ["A1"],
  "winner_bonuses": {},
  "errors": []
}
```

**Response (WH40K):**
```json
{
  "processed": 1,
  "territories_affected": [],
  "winner_bonuses": {
    "99": {
      "winner_id": 10,
      "bonus": "Extra VP for next 3 games",
      "description": "Mantle of Steel"
    }
  },
  "errors": []
}
```

---

## 🛡️ Security Principles

### 1. Generation Templates
- ✅ **Publicly accessible** - Anyone can see available mission types
- ✅ **No secrets** - Just rules and descriptions
- ✅ Cached locally for offline generation

### 2. Active Missions  
- ✅ **Current game state** - Which missions exist
- ⚠️ **Status field** - Indicates if result needed
- ❌ **Not secrets** - Users should know what's happening

### 3. Map Data
- ✅ **Static territory layout** - Publicly known
- ✅ **Adjacency rules** - Publicly known
- ⚠️ **Territory control** - NOT in cache (determined by server)

### 4. Results Sync
- ✅ **Server applies effects** - Client can't fake results
- ✅ **Single source of truth** - Server is authoritative
- ❌ **No client-side territory calculation** - Request parameter but validated on server

### 5. WH40K Winner Bonus
- ❌ **NOT in cache** - Secret until revealed
- ❌ **NOT in sync response** - Only to winner
- ✅ **Separate endpoint** - Only authenticated winner can retrieve
- ✅ **Audit logging** - Track access attempts

---

## 💾 SQLite Schema (App Side)

```sql
-- Generation templates cache
CREATE TABLE IF NOT EXISTS generation_templates (
    id INTEGER PRIMARY KEY,
    rules TEXT,  -- 'kill_team' or 'wh40k'
    type TEXT,
    reward TEXT,
    description TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Active missions (needing results)
CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY,
    type TEXT,
    reward TEXT,
    location TEXT,
    status INTEGER,  -- 0=pending, 1=active
    rules TEXT,
    description TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Map data
CREATE TABLE IF NOT EXISTS map_data (
    id INTEGER PRIMARY KEY,
    hex_locations TEXT,  -- JSON array
    adjacency TEXT,      -- JSON array
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pending battle results (for sync)
CREATE TABLE IF NOT EXISTS pending_results (
    id INTEGER PRIMARY KEY,
    mission_id TEXT,
    winner_id INTEGER,
    loser_id INTEGER,
    mission_type TEXT,
    location TEXT,
    timestamp TEXT,
    synced INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ✨ Key Differences: Offline vs Server

| Aspect | Offline App | Server |
|--------|------------|--------|
| **Generation** | ✅ Can generate NEW missions using templates | ❌ Can't create missions |
| **Result Storage** | ✅ Saves results locally | ❌ Ignores local results |
| **Territory Effect** | ❌ Can see calculation rules only | ✅ **Applies territory changes** |
| **WH40K Bonus** | ❌ Bonus NOT in cache (secret) | ✅ **Reveals bonus to winner** |
| **Source of Truth** | ❌ Temporary (offline sync cache) | ✅ **Permanent (game state)** |

---

## 🔮 Future Enhancements

### Phase 3.1: Differential Sync
- Only sync changed results (not all pending)
- Faster on slow connections

### Phase 3.2: Conflict Resolution
- Handle cases where mission was modified server-side
- Ask user to re-enter result if mission changed

### Phase 3.3: Offline Battle Records
- Store full battle details (units, terrain, etc.)
- Sync complete battle report not just winner

### Phase 3.4: Peer-to-Peer Sync
- Share results between apps before server connection
- Local tournament scoring

---

**Status:** ✅ **Architecture Confirmed & Documented**  
**Date:** 2026-02-23  
**Implementation:** Complete in sync_helper.py, server_app.py, sync.js  
