# Custom Notification Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN MENU                              │
│  [📢 Отправить уведомление / Send notification]                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               SELECT RECIPIENT TYPE                             │
│  [👤 Отправить одному игроку / Send to one player]             │
│  [⚔️ Отправить альянсу / Send to alliance]                     │
│  [⬅️ Назад / Back]                                             │
└─────────────────────────────────────────────────────────────────┘
              │                              │
              │ (warmaster)                  │ (alliance)
              ▼                              ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│  SELECT WARMASTER        │    │  SELECT ALLIANCE         │
│  [Player 1]              │    │  [Alliance 1]            │
│  [Player 2]              │    │  [Alliance 2]            │
│  [Player 3]              │    │  [Alliance 3]            │
│  [⬅️ Назад / Back]       │    │  [⬅️ Назад / Back]       │
└──────────────────────────┘    └──────────────────────────┘
              │                              │
              └──────────────┬───────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SEND MESSAGE PROMPT                            │
│  "📝 Отправьте сообщение, которое будет отправлено..."         │
│  "Send the message to be delivered to..."                      │
│  [❌ Отмена / Cancel]                                          │
└─────────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │ Admin sends message         │
              │ (text or photo)             │
              └──────────────┬──────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MESSAGE PROCESSING                             │
│  • Get recipient list (1 warmaster or N alliance members)      │
│  • Send message to each recipient                              │
│  • Count successes and failures                                │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CONFIRMATION MESSAGE                           │
│  "✅ Уведомление отправлено! / Notification sent!"            │
│  "Получатель / Recipient: <name>"                              │
│  "Успешно / Success: N"                                        │
│  "Ошибок / Failed: M"                                          │
│  [Return to main menu]                                         │
└─────────────────────────────────────────────────────────────────┘
```

## Conversation State Flow

```
MAIN_MENU
    │
    ├─> admin_custom_notification() 
    │   └─> Shows recipient type selection
    │       └─> MAIN_MENU (stays in same state)
    │
    ├─> admin_select_notification_warmaster()
    │   └─> Shows warmaster list
    │       └─> MAIN_MENU
    │
    ├─> admin_select_notification_alliance()
    │   └─> Shows alliance list
    │       └─> MAIN_MENU
    │
    ├─> admin_request_notification_message()
    │   └─> Prompts for message
    │       └─> CUSTOM_NOTIFICATION (new state)
    │
    └─> (other handlers)

CUSTOM_NOTIFICATION
    │
    ├─> handle_notification_message()
    │   └─> Sends message to recipients
    │       └─> MAIN_MENU (returns)
    │
    └─> admin_menu (cancel button)
        └─> MAIN_MENU
```

## Database Queries Used

1. **sqllite_helper.is_user_admin(user_id)**
   - Checks if user has admin privileges
   - Used in all admin handlers

2. **sqllite_helper.get_warmasters_with_nicknames()**
   - Returns: [(telegram_id, nickname, alliance), ...]
   - Used to show warmaster selection list

3. **sqllite_helper.get_all_alliances()**
   - Returns: [(id, name), ...]
   - Used to show alliance selection list

4. **sqllite_helper.get_players_by_alliance(alliance_id)**
   - Returns: [(telegram_id, nickname, alliance), ...]
   - Used to get recipient list for alliance notifications

5. **sqllite_helper.get_settings(user_id)**
   - Returns user settings including nickname
   - Used to get warmaster display name

## Telegram API Calls

1. **context.bot.send_message(chat_id, text)**
   - Sends text message to recipient

2. **context.bot.send_photo(chat_id, photo, caption)**
   - Sends photo with optional caption to recipient

## Error Handling

- Admin privileges checked before any operation
- Empty lists handled gracefully with error messages
- Session expiration detected and reported
- Individual send failures logged but don't stop batch send
- Success/failure counts reported to admin
