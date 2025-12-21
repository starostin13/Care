# Inactive Player Transfer Feature - Implementation Summary

## What Was Implemented

This implementation fulfills the requirements specified in the issue:
> "Придумать как сделать так что бы если игрок который долго не проявлял активности, то перекидывать его в другой альянс"
> (Figure out how to transfer a player who hasn't been active for a long time to another alliance)

### Requirements Met:

✅ **"долго" - относительно других участников** (long time - relative to other participants)
- Implemented: Players are considered inactive relative to their alliance's average inactivity
- Configurable threshold (default: 2x alliance average)
- Example: If alliance average is 5 days inactive, players with >10 days are flagged

✅ **Отправлять сообщение админам** (Send message to admins)
- Implemented: All admins receive detailed notification including:
  - Player name
  - Source and destination alliances
  - Last activity timestamp
  - Alliance average activity for comparison

✅ **Отправлять сообщение игроку которого перекинули** (Send message to transferred player)
- Implemented: Transferred player receives notification about:
  - Being moved to a new alliance
  - Reason (inactivity)
  - Encouragement to stay active

✅ **Отправлять сообщение игрокам из этого альянса** (Send message to players from this alliance)
- Implemented: Both old and new alliance members receive notifications:
  - **Old alliance**: Informed that a player left due to inactivity
  - **New alliance**: Welcomed the new member to their team

## Technical Implementation

### Database Changes
1. **New Column**: `last_active` TIMESTAMP in `warmasters` table
   - Automatically updated when players complete missions
   - Used to calculate inactivity duration

### Core Functions (sqllite_helper.py)
1. `update_last_active()` - Update player activity timestamp
2. `get_alliance_average_inactivity_days()` - Calculate alliance average
3. `get_inactive_players_in_alliance()` - Find inactive players
4. `transfer_inactive_player()` - Move player between alliances
5. `get_target_alliance_for_inactive_player()` - Find best destination
6. `get_all_admins()` - Get admin list for notifications
7. `get_player_last_active()` - Retrieve last activity time

### Notification System (notification_service.py)
- `notify_inactive_player_transfer()` - Sends 4 types of notifications:
  1. To all admins
  2. To the transferred player
  3. To old alliance members
  4. To new alliance members

### Business Logic (warmaster_helper.py)
- `check_and_transfer_inactive_players()` - Main function that:
  1. Checks all alliances
  2. Identifies inactive players
  3. Transfers them
  4. Sends all notifications

### Activity Tracking (mission_helper.py)
- Automatically updates `last_active` when players complete battles
- Includes error handling and validation

### Localization
All messages in both Russian and English:
- `inactive_player_transfer_admin_notification`
- `inactive_player_transfer_player_notification`
- `inactive_player_transfer_old_alliance_notification`
- `inactive_player_transfer_new_alliance_notification`

## How to Use

### Option 1: Manual Trigger (Recommended)
Add admin commands (see INTEGRATION_EXAMPLE.md):
```
/check_inactive_players        # Check with default threshold (2.0x)
/check_inactive_players 1.5    # More strict
/check_inactive_players 3.0    # Less strict
/inactivity_stats              # View alliance statistics
```

### Option 2: Scheduled Automatic Check
Set up weekly automatic checks:
```python
application.job_queue.run_repeating(
    scheduled_inactive_player_check,
    interval=timedelta(days=7),
    first=timedelta(hours=1)
)
```

### Option 3: Programmatic Call
```python
result = await warmaster_helper.check_and_transfer_inactive_players(context, 2.0)
```

## Configuration

The system is highly configurable:

- **Threshold Multiplier**: Adjust how strict inactivity detection is
  - Lower = More strict (e.g., 1.5 = 1.5x average)
  - Higher = Less strict (e.g., 3.0 = 3x average)
  - Default = 2.0

- **Check Frequency**: If using scheduled checks, adjust interval
  - Daily, weekly, monthly, etc.

## Example Scenarios

### Scenario 1: Active Alliance
- Alliance has 5 members
- Average last activity: 3 days ago
- Threshold: 2.0 (6 days)
- Result: No transfers (all members active)

### Scenario 2: One Inactive Player
- Alliance has 5 members
- 4 members: 2-4 days inactive
- 1 member: 15 days inactive
- Average: ~5 days
- Threshold: 2.0 (10 days)
- Result: Player with 15 days gets transferred

### Scenario 3: Multiple Alliances
- Alliance A: 10 members, avg 4 days inactive
- Alliance B: 5 members, avg 3 days inactive
- Alliance C: 3 members, avg 5 days inactive
- Inactive player from Alliance A gets transferred to Alliance C (fewest members)

## Benefits

1. **Maintains Active Alliances**: Keeps alliances filled with engaged players
2. **Fair Redistribution**: Transfers inactive players to smaller alliances
3. **Transparent**: All parties are notified about transfers
4. **Flexible**: Adjustable threshold based on game pace
5. **Automatic**: Can run on schedule without admin intervention
6. **Relative Metric**: Inactivity is measured relative to alliance, not absolute time

## Testing

✅ Unit tests pass (test_inactive_player_transfer_unit.py)
✅ No security vulnerabilities (CodeQL scan)
✅ Code review completed
✅ Mock implementations for testing

## Documentation

- **INACTIVE_PLAYER_TRANSFER.md**: Complete feature documentation
- **INTEGRATION_EXAMPLE.md**: Code examples for integration
- **This file**: Implementation summary

## Migrations

Two migrations need to be applied:
1. `015_add_last_active_to_warmasters.py` - Add database column
2. `016_add_inactive_player_transfer_texts.py` - Add localization texts

Apply with:
```bash
cd CareBot/CareBot
yoyo apply --database sqlite:///db/database migrations/
```

## Future Enhancements (Optional)

Potential improvements that could be added later:
- Configurable minimum alliance size before transfers
- Exclude certain players from transfer (e.g., alliance leaders)
- Different thresholds for different alliances
- Statistics dashboard showing activity trends
- Notifications before transfer (warning period)
