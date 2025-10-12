# Warmaster Settings Feature

This document describes the new warmaster settings feature implemented for the Care bot.

## Overview

Warmasters now have access to personalized settings through the bot interface. These settings allow customization of language preferences, display names, and notification controls.

## Features

### 1. Language Selection
- **Available Languages:** English (🇬🇧) and Russian (🇷🇺)
- **Default:** English ('en')
- **Access:** Settings menu → "Language: [current]" button
- **Storage:** `warmasters.language` column in database

### 2. Display Name Management
- **Purpose:** Set a custom nickname for display in the bot
- **Access:** Settings menu → "Set the name" button (shown only if not set)
- **Command:** `/setname YourName`
- **Storage:** `warmasters.nickname` column in database

### 3. Weekday Notifications Toggle
- **Purpose:** Enable/disable bot notifications on weekdays
- **Default:** ON (enabled)
- **Access:** Settings menu → "Weekday notifications: [ON/OFF]" button
- **Storage:** `warmasters.notifications_enabled` column (1=ON, 0=OFF)

## User Flow

### Accessing Settings
1. User sends `/start` command
2. Bot displays main menu with "Settings" button
3. User clicks "Settings"
4. Bot displays settings menu with available options

### Changing Language
1. From settings menu, click "Language: [current]"
2. Bot displays language selection menu
3. User selects desired language (English or Russian)
4. Bot confirms change and returns to settings menu

### Toggling Notifications
1. From settings menu, click "Weekday notifications: [status]"
2. Bot toggles the setting (ON→OFF or OFF→ON)
3. Bot confirms change and returns to settings menu

## Database Schema Changes

### warmasters table
```sql
CREATE TABLE warmasters (
    id            INTEGER PRIMARY KEY UNIQUE NOT NULL,
    telegram_id   TEXT    UNIQUE,
    alliance      INTEGER DEFAULT (0),
    nickname      TEXT,
    registered_as TEXT    UNIQUE,
    faction       TEXT,
    language      TEXT    DEFAULT ('en'),           -- NEW
    notifications_enabled INTEGER DEFAULT (1)        -- NEW
);
```

## Implementation Details

### Files Modified
1. **CareBot/CareBot/database/warmasters.sql** - Database schema
2. **CareBot/CareBot/sqllite_helper.py** - Database operations
3. **CareBot/CareBot/keyboard_constructor.py** - UI keyboards
4. **CareBot/CareBot/handlers.py** - Bot handlers

### New Functions

#### sqllite_helper.py
- `set_language(user_telegram_id, language)` - Save language preference
- `toggle_notifications(user_telegram_id)` - Toggle notification setting
- Modified `get_settings()` - Now returns language and notification status

#### keyboard_constructor.py
- `language_selection()` - Creates language selection keyboard

#### handlers.py
- `change_language()` - Shows language selection menu
- `set_language()` - Saves selected language
- `toggle_notifications()` - Toggles notification setting

## Testing

To test the implementation:
1. Start the bot with `/start`
2. Click "Settings"
3. Verify all three setting options are visible:
   - Language selection
   - Notification toggle
   - Set name (if not set)
4. Test language switching between English and Russian
5. Test notification toggle (ON ↔ OFF)
6. Verify settings persist across bot restarts

## Future Enhancements

Possible improvements for future iterations:
- More language options
- Granular notification controls (by event type)
- Timezone settings
- Custom notification schedules
- Email/SMS notification options
