# Testing Checklist for Warmaster Settings

## Pre-Implementation State
- [ ] Database has warmasters table with existing columns
- [ ] Bot responds to /start command
- [ ] Settings menu is accessible

## Database Schema Tests

### Test 1: Database Schema Migration
```sql
-- Verify new columns exist
SELECT language, notifications_enabled FROM warmasters LIMIT 1;
```
**Expected Result:** Columns exist with default values ('en' and 1)

## Functional Tests

### Test 2: Language Selection Flow
1. [ ] Start bot with `/start`
2. [ ] Click "Settings" button
3. [ ] Verify "Language: en" button appears
4. [ ] Click "Language: en" button
5. [ ] Verify language selection menu appears with:
   - [ ] 🇬🇧 English button
   - [ ] 🇷🇺 Русский button
   - [ ] Back button
6. [ ] Click "🇷🇺 Русский"
7. [ ] Verify return to settings with "Language: ru" displayed
8. [ ] Verify database updated: `SELECT language FROM warmasters WHERE telegram_id=?`

### Test 3: Notification Toggle Flow
1. [ ] Start bot with `/start`
2. [ ] Click "Settings" button
3. [ ] Verify "Weekday notifications: ON" button appears
4. [ ] Click notification button
5. [ ] Verify status changes to "Weekday notifications: OFF"
6. [ ] Verify success message appears
7. [ ] Verify database updated: `SELECT notifications_enabled FROM warmasters WHERE telegram_id=?`
8. [ ] Click notification button again
9. [ ] Verify status changes back to "Weekday notifications: ON"

### Test 4: Set Name Integration
1. [ ] Start bot with `/start` as new user (no nickname set)
2. [ ] Click "Settings" button
3. [ ] Verify "Set the name" button appears
4. [ ] Click "Set the name" button
5. [ ] Follow instructions to set name
6. [ ] Verify nickname is saved
7. [ ] Return to settings
8. [ ] Verify "Set the name" button no longer appears (unless nickname is null)

### Test 5: Registration Integration
1. [ ] Start bot with `/start` as new user (not registered)
2. [ ] Click "Settings" button
3. [ ] Verify "Registration" button appears
4. [ ] After registration
5. [ ] Verify "Registration" button no longer appears

### Test 6: Settings Persistence
1. [ ] Change language to Russian
2. [ ] Toggle notifications OFF
3. [ ] Close bot/restart conversation with /start
4. [ ] Open settings again
5. [ ] Verify language still shows "ru"
6. [ ] Verify notifications still show "OFF"

### Test 7: Edge Cases

#### Test 7a: New User (No DB Record)
1. [ ] Start bot as completely new user
2. [ ] Verify settings menu handles null values gracefully
3. [ ] Verify default language is "en"
4. [ ] Verify default notifications are "ON"

#### Test 7b: Back Button Navigation
1. [ ] From settings, click language button
2. [ ] Click "Back" button
3. [ ] Verify return to settings menu
4. [ ] Settings are unchanged

#### Test 7c: Rapid Toggling
1. [ ] Click notification toggle 5 times rapidly
2. [ ] Verify each toggle is processed
3. [ ] Verify final state in database matches displayed state

## Integration Tests

### Test 8: Other Menu Functions Still Work
1. [ ] Verify "Missions" button still works
2. [ ] Verify "Games" button still works (if registered)
3. [ ] Verify navigation between menus works
4. [ ] Verify /start command works at any point

## Code Quality Tests

### Test 9: Syntax and Imports
```bash
# Run from CareBot/CareBot directory
python3 -m py_compile handlers.py
python3 -m py_compile keyboard_constructor.py
python3 -m py_compile sqllite_helper.py
```
**Expected Result:** All files compile without errors

### Test 10: Database Function Tests
```python
# Test get_settings
settings = await sqllite_helper.get_settings(user_id)
assert len(settings) == 4  # nickname, registered_as, language, notifications_enabled

# Test set_language
await sqllite_helper.set_language(user_id, "ru")
settings = await sqllite_helper.get_settings(user_id)
assert settings[2] == "ru"

# Test toggle_notifications
result1 = await sqllite_helper.toggle_notifications(user_id)
result2 = await sqllite_helper.toggle_notifications(user_id)
assert result1 != result2  # Should toggle
assert result1 in [0, 1] and result2 in [0, 1]
```

## Performance Tests

### Test 11: Response Time
1. [ ] Click any settings button
2. [ ] Verify response time is < 2 seconds
3. [ ] Verify database queries are efficient

## Documentation Tests

### Test 12: Documentation Completeness
1. [ ] Verify WARMASTER_SETTINGS.md covers all features
2. [ ] Verify FLOW_DIAGRAM.md shows correct flow
3. [ ] Verify code comments are clear
4. [ ] Verify no sensitive information in docs

## Rollback Test

### Test 13: Backward Compatibility
1. [ ] Old database records (without new columns) should work
2. [ ] Default values should be applied automatically
3. [ ] No breaking changes to existing functionality

## Final Checklist

- [ ] All database functions work correctly
- [ ] All UI buttons appear correctly
- [ ] All callback handlers are registered
- [ ] Navigation flows work as expected
- [ ] Data persists correctly
- [ ] No syntax errors
- [ ] Documentation is complete
- [ ] Code follows existing patterns
- [ ] Changes are minimal and focused

## Known Limitations

1. Language selection only shows two languages (English, Russian)
2. Notification toggle is binary (ON/OFF) - no granular control
3. No timezone settings for notifications
4. No way to delete/reset settings to defaults

## Future Enhancements

1. Add more language options
2. Add granular notification controls (by event type, time of day)
3. Add timezone settings
4. Add notification history
5. Add settings export/import
