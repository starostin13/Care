# Game Result Confirmation Flow - Implementation Summary

## Overview
Implemented a two-step confirmation system for game results in the CareBot Telegram bot, as specified in the issue requirements.

## Changes Made

### 1. Database Schema Changes
**File**: `CareBot/CareBot/migrations/020_add_status_and_pending_results.py`
- **Renamed** `locked` column to `status` in `mission_stack` table
  - Old values: 0=unlocked, 1=locked, 2=score_submitted
  - New values: 0=available, 1=active, 2=pending_confirmation, 3=confirmed
- Created new `pending_results` table to store unconfirmed results
  - Fields: id, battle_id, submitter_id, fstplayer_score, sndplayer_score, created_at

### 2. Data Models
**File**: `CareBot/CareBot/models.py`
- Updated `Mission` model: changed `locked` field to `status` field
- Updated `MissionDetails` model: changed `locked` field to `status` field
- Added new `PendingResult` model with `from_db_row()` factory method

### 3. Database Helper Functions
**File**: `CareBot/CareBot/sqllite_helper.py`

Added functions for pending results management:
- `create_pending_result()` - Store a pending result
- `get_pending_result_by_battle_id()` - Retrieve pending result
- `delete_pending_result()` - Remove pending result
- `get_all_pending_missions()` - Get missions with status=2
- `update_mission_status()` - Update mission status
- `get_battle_participants()` - Get both players in a battle
- `get_pending_missions_count()` - Count pending missions
- `get_battle_id_by_mission_id()` - Find battle by mission

### 4. Result Submission Flow
**File**: `CareBot/CareBot/handlers.py`

**Modified `handle_mission_reply()`**:
- Validates score format (e.g., "20 0")
- Checks if result already pending for this battle
- Determines submitter and opponent
- Creates pending result (does NOT apply immediately)
- Sets mission status to 2 (pending_confirmation)
- Sends confirmation request to opponent with buttons

**Added `confirm_result()`**:
- Validates user is not the submitter
- Applies battle result using existing functions:
  - `write_battle_result()`
  - `apply_mission_rewards()`
  - `update_map()`
- Sets mission status to 3 (confirmed)
- Deletes pending result
- Notifies both players

**Added `cancel_result()`**:
- Validates user is not the submitter
- Deletes pending result
- Resets mission status to 1 (active)
- Notifies both players

### 5. Admin Confirmation Menu
**File**: `CareBot/CareBot/handlers.py`

**Added `admin_pending_confirmations()`**:
- Shows list of missions with status=2
- Displays mission details and scores
- Only visible to admins

**Added `admin_confirm_mission()`**:
- Shows detailed mission information
- Displays participants and scores
- Buttons to confirm or reject

**Added `admin_do_confirm_mission()`**:
- Applies battle result
- Updates map
- Sets status to 3
- Notifies participants

**Added `admin_do_reject_mission()`**:
- Deletes pending result
- Resets status to 1
- Notifies participants

### 6. Admin Menu Integration
**File**: `CareBot/CareBot/keyboard_constructor.py`
- Modified `get_admin_menu()` to show "Pending Confirmations" button
- Button only appears when there are missions with status=2
- Shows count of pending missions

### 7. Handler Registration
**File**: `CareBot/CareBot/handlers.py`
- Registered all new handlers in the ConversationHandler:
  - `confirm_result` - Pattern: `^confirm_result_`
  - `cancel_result` - Pattern: `^cancel_result_`
  - `admin_pending_confirmations` - Pattern: `^admin_pending_confirmations$`
  - `admin_confirm_mission` - Pattern: `^admin_confirm_mission:`
  - `admin_do_confirm_mission` - Pattern: `^admin_do_confirm:`
  - `admin_do_reject_mission` - Pattern: `^admin_do_reject:`

## Flow Diagrams

### Player Confirmation Flow
```
1. Player A plays mission with Player B
2. Player A replies to mission message with score "20 0"
   ↓
3. System creates pending_result record
4. System sets mission status = 2
5. Player B receives confirmation request with buttons
   ↓
6a. Player B clicks "Confirm"          6b. Player B clicks "Cancel"
   → Apply results                        → Delete pending result
   → Update map                           → Reset status to 1
   → Set status to 3                      → Both can resubmit
   → Notify both players                  → Notify both players
```

### Admin Confirmation Flow
```
1. Admin opens admin menu
2. Admin sees "Pending Confirmations (N)" if N > 0
3. Admin clicks to see list of pending missions
   ↓
4. Admin selects a mission
5. Admin sees mission details, participants, scores
   ↓
6a. Admin clicks "Confirm"             6b. Admin clicks "Reject"
   → Apply results                        → Delete pending result
   → Update map                           → Reset status to 1
   → Set status to 3                      → Notify participants
   → Notify participants
```

## Key Implementation Details

### Status Values
- **0 (available)**: Mission can be selected for play (was "unlocked")
- **1 (active)**: Mission being played (was "locked")
- **2 (pending_confirmation)**: Result submitted, awaiting confirmation
- **3 (confirmed)**: Result confirmed, applied to map and ratings

### Security & Validation
- Only the non-submitter can confirm/cancel a result
- Prevents self-confirmation
- Validates battle participants
- Checks for existing pending results

### Backwards Compatibility
- Mission model's `from_db_row()` handles rows with or without status field
- Default status=1 for existing missions
- Existing result application functions reused (no duplication)

### Mission Deletion
- **Verified**: No runtime code deletes missions from mission_stack
- Missions persist with status tracking
- Only migrations delete missions (for cleanup/setup)

## Testing

Created `test_result_confirmation.py` which validates:
- ✅ Migration file exists and contains correct schema changes
- ✅ Mission model has status field
- ✅ PendingResult model exists with all required fields
- ⚠️  Database functions (requires aiosqlite dependency)
- ⚠️  Handler functions (requires telegram dependency)

## Migration Instructions

1. Stop the bot
2. Run migrations: `yoyo apply`
   - Migration 020 will rename `locked` column to `status` in mission_stack
   - Migration 020 will create `pending_results` table
3. Restart the bot
4. Existing missions will retain their status values (0, 1, or 2 become valid status values)

## Future Considerations

1. **Timeout**: Could add auto-confirmation after X hours if opponent doesn't respond
2. **Dispute Resolution**: Could add a way to flag disputes for admin review
3. **History**: Could track confirmation history (who confirmed when)
4. **Notifications**: Could add configurable notifications for confirmation requests

## Files Modified
- `CareBot/CareBot/migrations/020_add_status_and_pending_results.py` (NEW)
- `CareBot/CareBot/models.py`
- `CareBot/CareBot/sqllite_helper.py`
- `CareBot/CareBot/handlers.py`
- `CareBot/CareBot/keyboard_constructor.py`
- `test_result_confirmation.py` (NEW)

## Requirements Met
- ✅ Either player can submit result
- ✅ Other player receives confirmation request with buttons
- ✅ Mission status set to 2 when result submitted
- ✅ Admin menu shows pending missions (status=2)
- ✅ Admin can manually confirm missions
- ✅ Confirmed missions have status=3
- ✅ No mission deletion logic at runtime
- ✅ Results only applied on confirmation (not on submission)
