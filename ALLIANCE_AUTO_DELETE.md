# Alliance Auto-Delete Feature

## Overview

This feature automatically deletes alliances that have 0 members and redistributes their territories to remaining alliances.

## What It Does

### 1. Territory Redistribution
When an alliance is deleted (manually or automatically), its territories are redistributed evenly to remaining alliances:
- Territories are assigned to alliances with the fewest territories first
- If there's a tie, a random alliance among the tied alliances is chosen
- This ensures balanced territory distribution

### 2. Player Redistribution
Players are also redistributed when an alliance is deleted:
- Players are assigned to alliances with the fewest members first
- Uses the same balanced distribution algorithm as territories

### 3. Automatic Cleanup
The system automatically checks for and deletes empty alliances:
- Triggered when an admin assigns a player to an alliance
- Finds all alliances with 0 members
- Deletes them and redistributes their territories
- Prevents accumulation of empty alliances

## Implementation Details

### Functions Added

#### `redistribute_territories_from_alliance(alliance_id)`
- Redistributes all territories from the specified alliance
- Distributes evenly to remaining alliances
- Returns the number of territories redistributed

#### `check_and_clean_empty_alliances()`
- Finds all alliances with 0 members
- Deletes each empty alliance
- Redistributes territories for each deleted alliance
- Returns a list of deletion results

#### Updated: `delete_alliance(alliance_id)`
- Now redistributes territories before deletion (previously set to NULL)
- Returns both players and territories redistributed count
- Territory redistribution happens before player redistribution

### Integration Points

The auto-cleanup is triggered at:
- **After alliance assignment**: When an admin assigns a player to an alliance via `admin_alliance_selected` handler

### Database Changes

No schema changes required. Uses existing tables:
- `alliances` - Alliance information
- `warmasters` - Player alliance membership
- `map` - Territory patron (alliance ownership)

### UI Updates

The alliance deletion success message now shows:
- Number of players redistributed
- Number of territories redistributed

Available in both Russian and English (localization keys updated).

## Testing

### Test Files

1. **`test_alliance_logic.py`** - Unit tests using mock data
   - Tests territory redistribution function
   - Tests alliance deletion with territory info
   - Tests automatic cleanup of empty alliances
   - Runs without requiring a database

2. **`test_alliance_auto_delete.py`** - Integration tests with database
   - Tests territory redistribution with real database
   - Tests automatic cleanup with real data
   - Requires DATABASE_PATH to be set

### Running Tests

```bash
# Unit tests (no database required)
python3 test_alliance_logic.py

# Integration tests (requires database)
export DATABASE_PATH=/path/to/database
python3 test_alliance_auto_delete.py
```

## Configuration

No configuration changes required. The feature is enabled by default.

## Limitations

- Cannot delete the last remaining alliance
- Empty alliances are only cleaned up when triggered (on player assignment)
- If you want periodic cleanup, you would need to add a scheduled job

## Future Enhancements

Possible improvements:
1. Add periodic scheduled cleanup (e.g., daily)
2. Add admin notification when empty alliances are auto-deleted
3. Add configuration option to disable auto-deletion
4. Add logging for auto-deletion events
