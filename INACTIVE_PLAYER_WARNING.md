# Inactive Player Warning System

## Overview

Simple system to identify and warn players who haven't participated in missions for a long time. Triggered automatically when game results are entered.

## How It Works

### Trigger
- Activated when battle results are entered via the bot
- Runs after `apply_mission_rewards()` completes successfully

### Detection
- Uses existing `battle_attenders` table (no DB changes needed)
- Finds player whose most recent battle has the **lowest battle_id**
- Battle IDs are auto-incrementing, so lower ID = participated longer ago

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
    MAX(ba.battle_id) as max_battle_id
FROM warmasters w
LEFT JOIN battle_attenders ba ON w.telegram_id = ba.attender_id
WHERE ba.battle_id IS NOT NULL
GROUP BY w.telegram_id, w.nickname, w.registered_as
ORDER BY max_battle_id ASC
LIMIT 1
```

This finds the player whose most recent battle ID is the lowest (i.e., participated longest ago).

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
