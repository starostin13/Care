# Inactive Player Warning System

## Overview

Simple system to identify and warn players who haven't participated in missions for more than **30 days**. Triggered automatically when game results are entered.

## How It Works

### Trigger
- Activated when battle results are entered via the bot
- Runs after `apply_mission_rewards()` completes successfully

### Detection
- Uses existing `battle_attenders`, `battles`, and `mission_stack` tables (no DB changes needed)
- Finds player whose most recent battle has the **lowest battle_id** AND whose last participation was **more than 30 days ago**
- Battle IDs are auto-incrementing, so lower ID = participated longer ago
- Uses `mission_stack.created_date` to calculate days since last participation

### Threshold
- **30 days** - Player must be inactive for more than a month to trigger warning
- Only players meeting this threshold will receive notifications
- If no players meet the criteria, no warnings are sent

### Notifications Sent

**1. To Inactive Player (Russian):**
```
⚠️ Внимание! Вы давно не участвовали в миссиях.

Пожалуйста, примите участие в играх, чтобы оставаться активным членом альянса.
```

**2. To All Admins (Russian):**
```
⚠️ Игрок [player_name] давно не участвовал в миссиях.

Контакт для связи: [player_contact]
```

## Implementation

### Files Modified (3 files)

**sqllite_helper.py**
- `get_least_recently_active_player()` - Find player with oldest participation
- `get_all_admins()` - Get list of admin users

**notification_service.py**
- `notify_inactive_player_warning()` - Send notifications to player and admins

**handlers.py**
- Added check after battle results processing
- Wrapped in try/except to prevent disruption if check fails

### Files Added (1 file)

**test_inactive_player_warning.py**
- Unit tests for new functionality
- Uses mock helpers for testing

## Technical Details

### SQL Query
```sql
SELECT 
    w.telegram_id,
    w.nickname,
    w.registered_as,
    MAX(ba.battle_id) as max_battle_id,
    MAX(ms.created_date) as last_mission_date
FROM warmasters w
LEFT JOIN battle_attenders ba ON w.telegram_id = ba.attender_id
LEFT JOIN battles b ON ba.battle_id = b.id
LEFT JOIN mission_stack ms ON b.mission_id = ms.id
WHERE ba.battle_id IS NOT NULL
GROUP BY w.telegram_id, w.nickname, w.registered_as
HAVING julianday('now') - julianday(MAX(ms.created_date)) > 30
ORDER BY max_battle_id ASC
LIMIT 1
```

This finds the player whose most recent battle ID is the lowest (i.e., participated longest ago) AND whose last mission was more than 30 days ago.

### 30-Day Threshold
- Uses SQLite's `julianday()` function to calculate date difference
- `HAVING julianday('now') - julianday(MAX(ms.created_date)) > 30` ensures only players inactive for >30 days are returned
- If no players meet this criteria, the query returns NULL and no warnings are sent

### Error Handling
- If no players with battles exist, no warnings sent
- Failures are logged but don't interrupt battle result processing
- Individual notification failures don't stop remaining notifications

## Testing

Run tests:
```bash
python test_inactive_player_warning.py
```

All tests should pass:
- ✅ Get Least Active Player
- ✅ Get All Admins  
- ✅ Notification Function

## No Database Changes

✅ Uses existing tables (warmasters, battle_attenders)
✅ No migrations needed
✅ No schema modifications
✅ Ready to use immediately

## Notes

- Runs on every battle result entry (frequent checks)
- Only identifies ONE player per check (the most inactive)
- Admins receive contact info to reach out personally
- Player gets gentle reminder to participate
- System doesn't automatically transfer or penalize players
