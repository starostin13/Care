# Inactive Player Transfer Feature

## Overview

This feature automatically detects and transfers players who have been inactive for a long time (relative to their alliance members) to other alliances. This helps maintain active alliances and redistributes inactive players more fairly.

## How It Works

### 1. Activity Tracking

Every time a player completes a mission/battle, their `last_active` timestamp is automatically updated in the database. This happens in the `apply_mission_rewards()` function in `mission_helper.py`.

### 2. Inactivity Detection

The system calculates:
- **Alliance Average Inactivity**: The average number of days since last activity for all members in an alliance
- **Inactive Players**: Players whose inactivity duration is significantly longer than their alliance average (by default, 2x the average)

For example:
- If an alliance's average inactivity is 5 days
- Players inactive for more than 10 days (2x threshold) are considered inactive

### 3. Transfer Process

When an inactive player is detected:
1. **Target Alliance Selection**: The system finds the alliance with the fewest members to transfer the player to
2. **Transfer Execution**: The player's alliance is updated in the database
3. **Notifications Sent**:
   - **Admins**: Get detailed information about the transfer, including inactivity statistics
   - **Transferred Player**: Gets notified about being moved to a new alliance
   - **Old Alliance Members**: Get notified that a player left due to inactivity
   - **New Alliance Members**: Get notified about a new player joining their alliance

## Usage

### Manual Execution

To manually check and transfer inactive players, you can call the function from Python:

```python
import asyncio
import warmaster_helper
from telegram.ext import ContextTypes

async def run_transfer_check(context):
    # Default threshold is 2.0 (2x alliance average)
    result = await warmaster_helper.check_and_transfer_inactive_players(context)
    
    print(f"Transfers performed: {result['transfers_count']}")
    for transfer in result['transfers']:
        print(f"  - {transfer['player_name']} moved from {transfer['from_alliance']} to {transfer['to_alliance']}")

# Run it
# Note: You need a proper Telegram bot context for notifications to work
asyncio.run(run_transfer_check(context))
```

### Scheduled Execution

You can set up a scheduled job to run this check periodically. For example, using Telegram bot's job queue:

```python
from telegram.ext import ApplicationBuilder

application = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

async def scheduled_inactive_check(context):
    """Scheduled job to check for inactive players."""
    await warmaster_helper.check_and_transfer_inactive_players(context)

# Run every week (604800 seconds)
application.job_queue.run_repeating(
    scheduled_inactive_check,
    interval=604800,  # 7 days
    first=10  # Start after 10 seconds
)
```

### Customizing the Threshold

You can adjust how strict the inactivity detection is by changing the threshold multiplier:

```python
# More strict: Only 1.5x the average is considered inactive
await warmaster_helper.check_and_transfer_inactive_players(context, threshold_multiplier=1.5)

# Less strict: Only 3x the average is considered inactive  
await warmaster_helper.check_and_transfer_inactive_players(context, threshold_multiplier=3.0)
```

## Database Schema

### New Column in `warmasters` Table

```sql
ALTER TABLE warmasters ADD COLUMN last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

This column is automatically added by migration `015_add_last_active_to_warmasters.py`.

### Localization Texts

The following localization keys are used for notifications (added by migration `016_add_inactive_player_transfer_texts.py`):

- `inactive_player_transfer_admin_notification` - Message sent to admins
- `inactive_player_transfer_player_notification` - Message sent to transferred player
- `inactive_player_transfer_old_alliance_notification` - Message sent to old alliance members
- `inactive_player_transfer_new_alliance_notification` - Message sent to new alliance members

Each key has both Russian (`ru`) and English (`en`) translations.

## API Functions

### In `sqllite_helper.py`:

- `update_last_active(telegram_id)` - Update last activity timestamp
- `get_alliance_average_inactivity_days(alliance_id)` - Get average inactivity for alliance
- `get_inactive_players_in_alliance(alliance_id, threshold_multiplier)` - Get list of inactive players
- `get_all_admins()` - Get all admin users
- `get_player_last_active(telegram_id)` - Get player's last active timestamp
- `transfer_inactive_player(telegram_id, from_alliance_id, to_alliance_id)` - Transfer player
- `get_target_alliance_for_inactive_player(current_alliance_id)` - Find best target alliance

### In `notification_service.py`:

- `notify_inactive_player_transfer(context, ...)` - Send notifications about transfer

### In `warmaster_helper.py`:

- `check_and_transfer_inactive_players(context, threshold_multiplier)` - Main function to check and transfer

## Testing

Run the unit tests to verify the feature is working:

```bash
python test_inactive_player_transfer_unit.py
```

This test uses mock data and doesn't require a database connection.

## Migration

To apply the database migrations:

```bash
cd CareBot/CareBot
yoyo apply --database sqlite:///db/database migrations/
```

This will:
1. Add the `last_active` column to the `warmasters` table
2. Add localization texts for notifications

## Notes

- Players are only transferred if there's more than one alliance
- The system automatically updates `last_active` when players complete missions
- Admins always receive notifications about transfers
- The feature is designed to be non-disruptive - players can still participate in missions normally
- The threshold multiplier can be adjusted based on your game's activity patterns
