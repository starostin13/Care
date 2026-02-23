# Feature Flags Implementation

## Overview

This implementation adds a toggleable features mechanism that allows administrators to enable/disable game features without code changes. The first toggleable feature is `common_resource`, which controls alliance resource mechanics.

## Database Schema

The `feature_flags` table stores feature flag configuration:

```sql
CREATE TABLE feature_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flag_name TEXT NOT NULL UNIQUE,
    enabled INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    updated_at TEXT
)
```

## Admin Interface

Administrators can access feature flag management through:

1. Main Menu → Admin Menu → ⚙️ Управление фичами (Feature Flags)
2. View list of all features with their current status
3. Click on any feature to toggle it on/off
4. Changes take effect immediately

## Current Features

### common_resource (Alliance Resource Mechanics)

When enabled (default):
- Alliances earn resources for participation in battles
- Different mission types award/deduct resources based on outcomes
- Mission bonuses apply resource rewards to winners

When disabled:
- All resource mechanics are bypassed
- No resources are awarded or deducted
- Battles proceed normally without resource changes

## Implementation Details

### Feature Flag Helper (`feature_flags_helper.py`)

```python
# Check if a feature is enabled
enabled = await feature_flags_helper.is_feature_enabled('common_resource')

# Toggle a feature
new_state = await feature_flags_helper.toggle_feature_flag('common_resource')

# Get all features
flags = await feature_flags_helper.get_all_feature_flags()
```

### Integration Pattern

All resource-related code in `mission_helper.py` checks the flag:

```python
if await feature_flags_helper.is_feature_enabled('common_resource'):
    await sqllite_helper.increase_common_resource(alliance_id, amount)
```

## Adding New Features

To add a new toggleable feature:

1. **Add to database migration:**
   ```python
   cursor.execute("""
       INSERT INTO feature_flags (flag_name, enabled, description, updated_at)
       VALUES (?, ?, ?, datetime('now'))
   """, ('new_feature', 1, 'Description'))
   ```

2. **Add localization texts:**
   ```python
   ('feature_new_feature_name', 'ru', 'Название фичи'),
   ('feature_new_feature_name', 'en', 'Feature Name'),
   ('feature_new_feature_desc', 'ru', 'Описание'),
   ('feature_new_feature_desc', 'en', 'Description'),
   ```

3. **Check flag in code:**
   ```python
   if await feature_flags_helper.is_feature_enabled('new_feature'):
       # Feature-specific code
   ```

## Testing

Tests are located in `CareBot/tests/`:
- `test_feature_flags.py` - Basic flag operations
- `test_common_resource_feature_flag.py` - Integration with common_resource

Run tests:
```bash
cd CareBot/tests
python3 test_feature_flags.py
python3 test_common_resource_feature_flag.py
```

## Migration

The migration `025_add_feature_flags.py` will run automatically when the bot starts. It:
- Creates the `feature_flags` table if it doesn't exist
- Adds the `common_resource` flag (enabled by default)
- Adds all necessary localization texts

## Fail-Safe Design

- Unknown flags default to enabled (fail-safe)
- If the feature_flags table doesn't exist, features are enabled by default
- No breaking changes to existing functionality
