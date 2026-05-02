# Custom Admin Notifications Feature - Implementation Summary

## Overview
This implementation adds a feature for administrators to send custom notifications to bot users on behalf of the bot. This fulfills the requirement from the issue "Отправка настраиваемых уведомлений".

## Features Implemented

### 1. Admin Menu Integration
- Added a new "📢 Отправить уведомление" (Send notification) button in the admin menu
- Only visible to users with admin privileges

### 2. Recipient Selection
Administrators can send notifications to:
- **Individual Warmaster**: Select from a list of all registered players with nicknames
- **Alliance**: Select an alliance, and the notification will be sent to all members

### 3. Message Types Supported
- **Text messages**: Plain text notifications
- **Photos with captions**: Images with optional text captions

### 4. User Flow
1. Admin clicks "📢 Отправить уведомление" in admin menu
2. Admin selects recipient type (Warmaster or Alliance)
3. Admin selects specific recipient from a list
4. Admin sends the message (text or photo)
5. Bot sends the message to recipient(s)
6. Admin receives confirmation with success/failure count

## Technical Implementation

### Files Modified

#### 1. `/CareBot/CareBot/handlers.py`
- Added new conversation state: `CUSTOM_NOTIFICATION`
- Implemented handlers:
  - `admin_custom_notification()`: Entry point, shows recipient type selection
  - `admin_select_notification_warmaster()`: Shows list of warmasters
  - `admin_select_notification_alliance()`: Shows list of alliances
  - `admin_request_notification_message()`: Prompts admin to send message
  - `handle_notification_message()`: Processes and sends message to recipients
- Added handlers to conversation state machine

#### 2. `/CareBot/CareBot/keyboard_constructor.py`
- Added custom notification button to `get_admin_menu()`

#### 3. `/CareBot/CareBot/mock_sqlite_helper.py`
- Added `get_players_by_alliance()` mock function for test mode support

#### 4. `/CareBot/CareBot/migrations/022_add_custom_notification_texts.py`
- Created migration to add localization texts for:
  - Menu buttons and labels
  - Instructions and prompts
  - Error messages
  - Confirmation messages
- Supports both Russian (ru) and English (en) languages

### New Files Created

#### 1. `/test_custom_notifications.py`
- Test script to validate:
  - Localization texts are properly loaded
  - Database queries work correctly
  - Mock functions are implemented

## Localization Keys Added

### Buttons
- `button_admin_custom_notification`: Admin menu button
- `button_notify_warmaster`: Select warmaster option
- `button_notify_alliance`: Select alliance option
- `button_back`: Back button
- `button_cancel`: Cancel button

### Messages
- `custom_notification_select_recipient_type`: Prompt for recipient type
- `custom_notification_select_warmaster`: Prompt to select warmaster
- `custom_notification_select_alliance`: Prompt to select alliance
- `custom_notification_send_message`: Instructions for sending message
- `custom_notification_sent`: Confirmation message

### Errors
- `no_warmasters_found`: No players with nicknames
- `no_alliances_found`: No alliances exist
- `error_notification_session_expired`: Session expired
- `error_no_recipients`: No recipients found

## Security Considerations

1. **Admin-only access**: All notification handlers check admin status
2. **No SQL injection**: Uses parameterized queries
3. **XSS prevention**: Uses Telegram's built-in message sanitization
4. **Session management**: Uses Telegram's context.user_data for temporary state

## Testing

### Manual Testing Steps
1. Deploy bot with changes
2. Log in as admin user
3. Navigate to admin menu
4. Click "📢 Отправить уведомление"
5. Test sending to individual warmaster
6. Test sending to alliance
7. Test with text message
8. Test with photo message
9. Verify recipients receive messages

### Automated Testing
Run: `python3 test_custom_notifications.py`
- Validates database queries
- Checks localization texts
- Confirms mock functions work

## Dependencies
No new dependencies added. Uses existing:
- `python-telegram-bot` for Telegram API
- `aiosqlite` for database access
- `localization` module for translations

## Future Enhancements (Out of Scope)
- Schedule notifications for future delivery
- Template messages for common notifications
- Notification history/log
- Bulk send to multiple alliances
- Rich formatting (markdown/HTML)

## Code Review Status
✅ Code review completed - 1 issue addressed (redundant database call)

## Security Scan Status
✅ CodeQL security scan passed - No vulnerabilities found

## Deployment Notes
1. Run database migrations to add localization texts
2. Restart bot to load new handlers
3. Verify admin users can access the new menu option

## Translation Examples

### Russian (ru)
- "📢 Отправить уведомление" - Send notification button
- "👤 Отправить одному игроку" - Send to one player
- "⚔️ Отправить альянсу" - Send to alliance

### English (en)
- "📢 Send notification" - Send notification button
- "👤 Send to one player" - Send to one player
- "⚔️ Send to alliance" - Send to alliance
