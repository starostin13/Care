# Warmaster Settings - User Flow Diagram

```
                                    /start
                                      |
                                      v
                              +---------------+
                              |  Main Menu    |
                              |               |
                              | [Settings]    |
                              | [Missions]    |
                              | [Games]       |
                              +---------------+
                                      |
                        User clicks [Settings]
                                      |
                                      v
                              +------------------+
                              | Settings Menu    |
                              |                  |
                              | [Language: en]   |---+
                              | [Notifications:  |   |
                              |      ON]         |---+
                              | [Set name]*      |   |
                              | [Registration]*  |   |
                              | [Back]           |   |
                              +------------------+   |
                                                     |
        +--------------------------------------------+
        |                                            |
        v                                            v
+------------------+                    +-------------------------+
| Language Menu    |                    | Toggle Notification     |
|                  |                    |                         |
| [🇬🇧 English]     |                    | Toggles: ON ↔ OFF      |
| [🇷🇺 Русский]     |                    | Returns to Settings    |
| [Back]           |                    | with updated status    |
+------------------+                    +-------------------------+
        |
User selects language
        |
        v
+------------------+
| Settings Menu    |
| (updated)        |
|                  |
| [Language: ru]   |
| [Notifications:  |
|      ON]         |
| [Set name]*      |
| [Registration]*  |
| [Back]           |
+------------------+

* These options only appear when needed:
  - "Set name" appears if nickname is not set
  - "Registration" appears if registered_as is not set
```

## Database Flow

```
User Action                Database Operation              Result
───────────────────────────────────────────────────────────────────────
1. Click Language button → get_settings(user_id)        → Show current: "en"
   
2. Select "Русский"      → set_language(user_id, "ru")  → Update DB
                            COMMIT                          Language = "ru"

3. Click Notifications   → toggle_notifications(user_id) → Toggle value
                            SELECT current value            1 → 0 or 0 → 1
                            UPDATE with new value           COMMIT
                            RETURN new value
```

## Callback Data Flow

```
Button Text              Callback Data           Handler Function
──────────────────────────────────────────────────────────────────
"Settings"            → "callsettings"       → setting()
"Language: en"        → "changelanguage"     → change_language()
"🇬🇧 English"          → "lang:en"            → set_language()
"🇷🇺 Русский"          → "lang:ru"            → set_language()
"Weekday notif.: ON"  → "togglenotifications"→ toggle_notifications()
"Back"                → "callsettings"       → setting()
```

## State Management

```
Conversation State: MAIN_MENU
│
├─ Pattern: ^callsettings$       → setting()
├─ Pattern: ^changelanguage$     → change_language()
├─ Pattern: ^lang:               → set_language()
├─ Pattern: ^togglenotifications$→ toggle_notifications()
└─ Pattern: ^start$              → hello()
```

All handlers return to `MAIN_MENU` state to maintain conversation flow.
