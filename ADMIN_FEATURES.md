# Admin Features Documentation

This document describes the admin features available in CareBot.

## Overview

CareBot includes administrative features that allow designated admins to manage game aspects. Currently, the following admin features are available:

### Alliance Assignment

Admins can assign players to alliances (factions) in the game.

## Admin Access

### Automatic Admin Assignment

When the bot starts, if no admin exists, the **first user** in the `warmasters` table is automatically promoted to admin. This ensures that the first person who registered with the bot becomes the admin.

### Manual Admin Assignment

To manually make a user an admin, you need to update the database:

```sql
UPDATE warmasters SET is_admin = 1 WHERE telegram_id = '<user_telegram_id>';
```

## Alliance Assignment Feature

### Access

Only users with `is_admin = 1` in the database can access the alliance assignment feature.

### How to Use

1. **Open Bot**: Start the bot by sending `/start`
2. **Admin Button**: If you're an admin, you'll see an "⚙️ Управление альянсами" (Manage Alliances) button in the main menu
3. **Select Player**: Click the button to see a list of all players who have set nicknames
   - Players are shown with their current alliance (if any) in parentheses
   - Example: "PlayerName (Tau)"
4. **Select Alliance**: Click on a player to see the list of available alliances
   - Each alliance shows the current number of players
   - Example: "Tau (2 игроков)", "Chaos (3 игроков)", "Imperium (1 игроков)"
5. **Confirm**: Click on an alliance to assign it to the player
   - A confirmation message will be shown
   - The change is saved to the database immediately

### Available Alliances

The bot currently supports three alliances:
- **Tau** (ID: 1)
- **Chaos** (ID: 2)
- **Imperium** (ID: 3)

### Localization

The feature is fully localized and supports:
- Russian (ru) - default
- English (en)

Texts are stored in the `texts` table and can be modified through database migrations.

## Technical Details

### Database Schema

**Warmasters Table:**
```sql
CREATE TABLE warmasters (
    id INTEGER PRIMARY KEY,
    telegram_id TEXT UNIQUE,
    alliance INTEGER DEFAULT (0),
    nickname TEXT,
    registered_as TEXT UNIQUE,
    faction TEXT,
    language TEXT DEFAULT ('ru'),
    notifications_enabled INTEGER DEFAULT (1),
    is_admin INTEGER DEFAULT (0)
);
```

**Alliances Table:**
```sql
CREATE TABLE alliances (
    name TEXT NOT NULL UNIQUE,
    id INTEGER UNIQUE NOT NULL PRIMARY KEY,
    common_resource INTEGER DEFAULT (0)
);
```

### Callback Data Patterns

The feature uses the following callback data patterns:
- `admin_assign_alliance` - Opens player selection screen
- `admin_player:<telegram_id>` - Player selected, show alliance list
- `admin_alliance:<telegram_id>:<alliance_id>` - Assign alliance to player

### Security

- Admin check is performed on every admin action
- Non-admin users are denied access with a message "У вас нет прав администратора"
- The first user is auto-promoted only once, on bot startup

## Troubleshooting

### Admin Button Not Showing

If you're supposed to be an admin but don't see the button:
1. Check your `is_admin` status in the database:
   ```sql
   SELECT telegram_id, nickname, is_admin FROM warmasters WHERE telegram_id = '<your_id>';
   ```
2. Make sure you have a nickname set (use `/setname` command)
3. Restart the bot by sending `/start` again

### No Players in List

If the player list is empty:
- Make sure players have set their nicknames using `/setname <nickname>`
- Only players with nicknames are shown in the list

### Alliance Not Assigned

If the alliance assignment doesn't work:
1. Check database write permissions
2. Check bot logs for errors
3. Verify the alliance ID is valid (1, 2, or 3)

## Future Enhancements

Possible future improvements to admin features:
- Add/remove alliances dynamically
- Batch assignment of players to alliances
- Alliance statistics and reports
- Admin role management (multiple admins)
- Alliance resource management UI
