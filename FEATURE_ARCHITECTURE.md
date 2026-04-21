# Feature Architecture Documentation

## Overview

The feature system has been refactored to use a proper architecture with feature classes and lifecycle methods, replacing scattered if-checks throughout the codebase.

## Architecture

### Base Components

#### Feature Class (`features.py`)
```python
class Feature:
    """Base class for all toggleable features."""
    
    def __init__(self, flag_name: str, description: str)
    
    async def is_enabled(self) -> bool
    
    # Lifecycle methods (override in subclasses)
    async def on_create_mission(self, mission_data: Dict[str, Any])
    async def on_result_approved(self, battle_data: Dict[str, Any])
    async def on_battle_start(self, battle_data: Dict[str, Any])
    async def on_mission_complete(self, mission_data: Dict[str, Any])
```

#### FeatureRegistry (`features.py`)
```python
class FeatureRegistry:
    """Registry for all game features."""
    
    def register(self, feature: Feature)
    def get_feature(self, flag_name: str) -> Optional[Feature]
    def get_all_features(self) -> Dict[str, Feature]
    
    # Calls lifecycle methods on all enabled features
    async def on_create_mission(self, mission_data: Dict[str, Any])
    async def on_result_approved(self, battle_data: Dict[str, Any])
    async def on_battle_start(self, battle_data: Dict[str, Any])
    async def on_mission_complete(self, mission_data: Dict[str, Any])
```

## Lifecycle Methods

### on_create_mission(mission_data)
Called when a mission is created.

**mission_data:**
- `rules`: Game rules (killteam, wh40k, etc)
- `cell`: Map cell
- `attacker_id`: Telegram ID
- `defender_id`: Telegram ID

**Use case:** Modify mission parameters based on active features

### on_result_approved(battle_data) ✅ Implemented
Called when battle results are approved and confirmed.

**battle_data:**
- `battle_id`: Battle ID
- `mission_id`: Mission ID
- `user_score`: Score
- `opponent_score`: Score
- `user_alliance`: Alliance ID
- `opponent_alliance`: Alliance ID
- `winner_alliance_id`: Winner alliance
- `loser_alliance_id`: Loser alliance
- `mission_type`: Mission type string
- `rules`: Game rules
- `reward_config`: Mission reward configuration

**Use case:** Award/deduct resources, update statistics, trigger events

### on_battle_start(battle_data)
Called when a battle starts.

**Use case:** Apply battle modifiers, log events

### on_mission_complete(mission_data)
Called when a mission is completed.

**Use case:** Clean up, finalize state changes

## Current Features

### CommonResourceFeature (`common_resource_feature.py`)

**Flag name:** `common_resource`
**Default state:** Disabled

**Implemented lifecycle methods:**
- ✅ `on_result_approved()` - Handles all resource gain/loss logic

**Functionality:**
- Awards participation resources to alliances
- Processes mission-type-specific rewards:
  - Loot: Additional resources based on score ratio
  - Transmission: Resource transfer mechanics
  - Secure: Winner gets 2 resources
  - Resource Collection: Winner gets 1 resource
  - Extraction: Winner +1, Loser -1
  - Power Surge: Loser loses resources based on warehouses
  - Coordinates: Loser loses resources and warehouse
- Applies mission-specific reward bonuses from reward_config

## Adding New Features

### Step 1: Create Feature Class

```python
# my_feature.py
from features import Feature
import sqllite_helper

class MyFeature(Feature):
    def __init__(self):
        super().__init__(
            flag_name='my_feature',
            description='My feature description'
        )
    
    async def on_result_approved(self, battle_data):
        # Implement feature logic
        pass

# Create instance
my_feature = MyFeature()
```

### Step 2: Register Feature

```python
# In register_features.py
from my_feature import my_feature

feature_registry.register(my_feature)
```

### Step 3: Add Database Entry

```python
# In migration
cursor.execute("""
    INSERT INTO feature_flags (flag_name, enabled, description, updated_at)
    VALUES (?, ?, ?, datetime('now'))
""", ('my_feature', 0, 'My feature description'))
```

### Step 4: Add Localization

```python
# In migration
('feature_my_feature_name', 'ru', 'Название фичи'),
('feature_my_feature_name', 'en', 'Feature Name'),
```

## Integration Points

### mission_helper.py

```python
# Old approach (removed):
if await feature_flags_helper.is_feature_enabled('common_resource'):
    await sqllite_helper.increase_common_resource(alliance_id, 1)

# New approach:
battle_data = {...}
await feature_registry.on_result_approved(battle_data)
```

### Future Integration Points

```python
# Mission creation
mission_data = {...}
await feature_registry.on_create_mission(mission_data)

# Battle start
battle_data = {...}
await feature_registry.on_battle_start(battle_data)

# Mission completion
mission_data = {...}
await feature_registry.on_mission_complete(mission_data)
```

## Benefits

1. **Centralized Logic:** All feature-specific code in one place
2. **Easy Extension:** Add new features by implementing Feature class
3. **Clean Separation:** Mission logic separated from feature logic
4. **Type Safety:** Clear interfaces and data structures
5. **Error Handling:** Registry catches and logs feature errors
6. **Testability:** Features can be tested independently

## Migration from Old Approach

### Before
- Feature checks scattered throughout mission_helper.py
- 12+ separate if-checks for common_resource
- Hard to track all feature usage

### After
- Single call to feature_registry.on_result_approved()
- All resource logic in CommonResourceFeature class
- Clear lifecycle for feature execution

## Error Handling

The FeatureRegistry wraps each feature call in try-except:

```python
try:
    await feature.on_result_approved(battle_data)
except Exception as e:
    logger.error(f"Error in {feature.flag_name}.on_result_approved: {e}")
```

This ensures one feature's error doesn't break others.

## Performance

- Minimal overhead: Only iterates enabled features
- Database checks cached during feature instance lifetime
- No additional database queries per feature call

## Testing

Features can be tested independently:

```python
feature = CommonResourceFeature()

# Mock the is_enabled check
async def mock_is_enabled():
    return True

feature.is_enabled = mock_is_enabled

# Test the feature
battle_data = {...}
await feature.on_result_approved(battle_data)
```

## Future Enhancements

Potential additional lifecycle methods:
- `on_player_join(player_data)`
- `on_alliance_created(alliance_data)`
- `on_territory_captured(territory_data)`
- `on_daily_reset()`
- `on_weekly_reset()`
