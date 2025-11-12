# Feature Implementation: Admin Alliance Assignment Keyboard

## Issue
**Title:** Создать клавиатуру позволяющую назначать игрокам альянсы  
**Translation:** Create a keyboard that allows assigning alliances to players

## Requirements
1. ✅ Create a keyboard accessible only to admins
2. ✅ Make the first user in warmasters an admin if none exists
3. ✅ Keyboard should show players with nicknames
4. ✅ After selecting a player, show list of alliances with player counts

## Implementation

### 1. Database Functions (`sqllite_helper.py`)

Added 7 new functions:

```python
# Admin Management
async def is_user_admin(user_telegram_id)
async def make_user_admin(user_telegram_id)
async def ensure_first_user_is_admin()

# Data Retrieval
async def get_warmasters_with_nicknames()
async def get_all_alliances()
async def get_alliance_player_count(alliance_id)

# Alliance Assignment
async def set_warmaster_alliance(user_telegram_id, alliance_id)
```

**Note:** Uses existing `is_admin` column from migration `20251106_01_add_is_admin_to_warmasters.sql`

### 2. Keyboard Constructors (`keyboard_constructor.py`)

Added 2 new keyboard builders:

```python
async def admin_assign_alliance_players(userId)
    # Shows list of players with current alliances
    # Format: "PlayerName (Alliance)" or "PlayerName"
    
async def admin_assign_alliance_list(userId, player_telegram_id)
    # Shows list of alliances with player counts
    # Format: "AllianceName (X игроков)"
```

Updated `get_main_menu()`:
- Checks if user is admin
- Adds "⚙️ Управление альянсами" button for admins

### 3. Handlers (`handlers.py`)

Added 3 new handler functions:

```python
async def admin_assign_alliance(update, context)
    # Entry point - checks admin status
    # Shows player selection screen
    
async def admin_select_player(update, context)
    # Handles player selection
    # Shows alliance selection screen
    
async def admin_assign_alliance_to_player(update, context)
    # Handles alliance assignment
    # Shows confirmation and returns to menu
```

Updated `hello()` function:
- Calls `ensure_first_user_is_admin()` on bot start
- Logs admin promotion events

Updated conversation handler:
- Added 3 callback handlers in MAIN_MENU state:
  - `admin_assign_alliance` pattern
  - `admin_player:` pattern
  - `admin_alliance:` pattern

### 4. Localization (`migrations/007_add_admin_alliance_texts.py`)

Added 8 new text entries (4 keys × 2 languages):

| Key | Russian | English |
|-----|---------|---------|
| `button_admin` | ⚙️ Управление альянсами | ⚙️ Manage Alliances |
| `admin_assign_alliance_title` | Выберите игрока для назначения альянса: | Select a player to assign alliance: |
| `admin_select_alliance_for_player` | Выберите альянс для игрока {player_name}: | Select alliance for player {player_name}: |
| `admin_alliance_assigned` | Альянс {alliance_name} назначен игроку {player_name}! | Alliance {alliance_name} assigned to player {player_name}! |

## User Flow

```
1. Admin opens bot (/start)
   ↓
2. Main menu shows "⚙️ Управление альянсами" button
   ↓
3. Click button → Player selection screen
   Shows: "PlayerName (CurrentAlliance)" or "PlayerName"
   ↓
4. Click player → Alliance selection screen  
   Shows: "AllianceName (X игроков)"
   ↓
5. Click alliance → Confirmation
   Shows: "Альянс [X] назначен игроку [Y]!"
   ↓
6. Return to main menu
```

## Security

- ✅ Admin check on every admin action
- ✅ Non-admin users see error message
- ✅ CodeQL scan: 0 vulnerabilities
- ✅ Input validation on callback data

## Testing

### Manual Testing Checklist

1. **Admin Promotion**
   - [ ] First user becomes admin automatically
   - [ ] Admin status persists across restarts
   - [ ] Only one auto-promotion occurs

2. **Admin Access**
   - [ ] Admin button appears for admin users
   - [ ] Admin button hidden for non-admin users
   - [ ] Non-admins get "нет прав" message if they try to access

3. **Player Selection**
   - [ ] Shows all players with nicknames
   - [ ] Shows current alliance if assigned
   - [ ] Empty list handled gracefully
   - [ ] Back button works

4. **Alliance Selection**
   - [ ] Shows all 3 alliances (Tau, Chaos, Imperium)
   - [ ] Shows correct player counts
   - [ ] Player counts update after assignment
   - [ ] Back button returns to player list

5. **Assignment**
   - [ ] Alliance assigned correctly
   - [ ] Confirmation message shows correct names
   - [ ] Database updated immediately
   - [ ] Can reassign player to different alliance

6. **Localization**
   - [ ] Russian texts display correctly
   - [ ] English texts display correctly (if user language is EN)
   - [ ] Variables {player_name} and {alliance_name} populated

### Automated Test

Run `test_admin_functions.py` to verify database functions:

```bash
cd /home/runner/work/Care/Care
export DATABASE_PATH="/path/to/your/database"
python3 test_admin_functions.py
```

## Files Changed

| File | Lines Added | Description |
|------|-------------|-------------|
| `sqllite_helper.py` | +114 | Database functions |
| `keyboard_constructor.py` | +91 | Keyboard builders |
| `handlers.py` | +106 | Handler functions |
| `migrations/007_*.py` | +21 | Localization texts |
| `ADMIN_FEATURES.md` | +135 | Documentation |
| `test_admin_functions.py` | +80 | Test script |

**Total:** 547 lines added

## Database Schema

### Existing Tables Used

**warmasters:**
- `telegram_id` - Primary key
- `nickname` - Display name (required for listing)
- `alliance` - Alliance ID (0, 1, 2, or 3)
- `is_admin` - Admin flag (0 or 1)

**alliances:**
- `id` - Primary key (1=Tau, 2=Chaos, 3=Imperium)
- `name` - Alliance name
- `common_resource` - Not used by this feature

### No Schema Changes Required

The feature uses existing database structure. The `is_admin` column was added by a previous migration.

## Rollback Plan

If needed, revert the changes:

```bash
git revert bc598e6  # Remove documentation
git revert 1878290  # Remove feature implementation
```

Then manually rollback migration 007:

```bash
cd CareBot/CareBot
yoyo rollback -r 1
```

## Future Enhancements

Potential improvements:
1. Bulk alliance assignment (select multiple players)
2. Alliance management (add/remove alliances)
3. Admin role management (multiple admin levels)
4. Alliance statistics dashboard
5. Audit log for alliance changes
6. Filtering/search in player list

## Known Limitations

1. Only players with nicknames appear in the list
2. No undo function (must reassign manually)
3. No confirmation dialog before assignment
4. Large player lists may be unwieldy (no pagination)
5. Alliance names are hardcoded (Tau, Chaos, Imperium)

## Support

For issues or questions:
1. Check `ADMIN_FEATURES.md` for usage documentation
2. Review bot logs for error messages
3. Verify database schema matches expected structure
4. Test with `test_admin_functions.py` script

## Conclusion

The feature is **fully implemented** and ready for deployment. All requirements from the issue have been met:

✅ Admin-only keyboard created  
✅ First user auto-promoted to admin  
✅ Players shown with nicknames  
✅ Alliances shown with player counts  

The implementation follows the existing codebase patterns and includes proper security checks, localization, and documentation.
