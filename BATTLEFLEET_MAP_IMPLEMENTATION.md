# Battlefleet Gothica Map Generation - Implementation Summary

## Overview
This implementation adds automatic celestial phenomena map generation for Battlefleet Gothica missions as requested in the issue.

## Changes Made

### 1. Database Schema
- **Migration**: `021_add_map_description_to_mission_stack.py`
- Added `map_description` TEXT column to `mission_stack` table
- Column defaults to NULL for non-battlefleet missions

### 2. Data Models
- Updated `Mission` dataclass to include `map_description` field
- Updated `MissionDetails` dataclass to include `map_description` field
- Fixed `to_tuple()` method to properly include mission ID at position 4

### 3. Map Generation Logic
- **Function**: `generate_battlefleet_map()` in `mission_helper.py`
- Implements "Setting Up Celestial Phenomena: Method 2" rules
- Features:
  - 6 battlezone generators (Asteroid Field, Nebula Zone, Gravity Wells, Solar Phenomena, Debris Field, Planetary Bodies)
  - Each generator has 6 unique phenomena with game effects
  - Divides table into 2x3 grid (6 areas of 60cm each)
  - D6 roll per area - phenomena placed on 4+
  - D6 roll to select battlezone type
  - Returns formatted map description string

### 4. Mission Generation
- Updated `generate_new_one()` to call map generator for battlefleet
- All mission types now return consistent 6-element tuples: `(deploy, rules, cell, description, winner_bonus, map_description)`
- Non-battlefleet missions have `map_description = None`

### 5. Mission Display
- Updated `handlers.py` to extract and display map description for battlefleet missions
- Map appears in mission message using the existing message builder

### 6. Database Helpers
- Updated `save_mission()` to store map_description (7th parameter)
- Updated `get_mission()` to retrieve map_description (9th column)
- Updated `get_mission_details()` to include map_description

### 7. Test Support
- Updated `mock_sqlite_helper.py` to return Mission objects
- Added battlefleet-specific mock map for testing
- Created `test_map_standalone.py` for manual verification

## Example Output

When a player selects a battlefleet mission, they will see:

```
🗺️ BATTLEFLEET MAP - ASTEROID FIELD

Celestial Phenomena (60cm grid areas):
  • Top-Left: Dense Asteroid Cluster - Ships moving through reduce speed by 2"
  • Top-Center: Empty space
  • Top-Right: Asteroid Belt - Provides cover, enemies get -1 to hit
  • Bottom-Left: Empty space
  • Bottom-Center: Ice Field - Sensors reduced, -2" to detection range
  • Bottom-Right: Metallic Asteroids - Interferes with targeting systems

📋 Note: Position phenomena anywhere within each area, but don't overlap them.
```

## Testing

- ✅ Standalone map generation tested successfully
- ✅ Code compiles without errors
- ✅ No security vulnerabilities detected
- ✅ Code review feedback addressed
- ✅ Mock helper updated for test mode compatibility

## Battlezone Generators

### 1. Asteroid Field
- Dense Asteroid Cluster, Asteroid Belt, Scattered Debris, Mining Operation, Ice Field, Metallic Asteroids

### 2. Nebula Zone
- Gas Cloud, Plasma Storm, Dust Cloud, Ion Nebula, Radiation Field, Clear Zone

### 3. Gravity Wells
- Massive Gravity Well, Unstable Gravity, Black Hole Proximity, Tidal Forces, Gravitational Anomaly, Stable Orbit Zone

### 4. Solar Phenomena
- Solar Flare, Radiation Burst, Electromagnetic Pulse, Corona Discharge, Stellar Wind, Magnetic Storm

### 5. Debris Field
- Ship Wreckage, Battle Debris, Ancient Hulk, Orbital Wreckage, Minefield Remnants, Salvage Field

### 6. Planetary Bodies
- Moon, Small Planet, Gas Giant, Planetary Ring, Barren Rock, Space Station

## Migration Instructions

When deploying this change:
1. The migration will automatically add the `map_description` column
2. Existing missions will have `map_description = NULL`
3. New battlefleet missions will automatically include generated maps
4. Other mission types remain unchanged

## Security Summary

No security vulnerabilities were introduced by this change. All changes are purely additive and do not affect existing mission types or functionality.
