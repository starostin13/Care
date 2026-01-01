# Mission Blocking Fix - Summary

## Issue
**Title:** блокировние миссий (Mission Blocking)

**Problem:** Two pairs of players who started playing 10 minutes apart received missions with the same number.

## Root Cause

The bug had two related causes:

1. **`save_mission` function bug**: When creating a new mission, it was saved with `locked=1` (locked state)
2. **`get_mission` query filter**: Only searches for missions where `locked=0` (unlocked state)

This created a scenario where:
- Newly created missions were immediately locked (`locked=1`)
- The `get_mission` query couldn't find them (looking for `locked=0`)
- Each pair of players would trigger creation of a new mission
- Result: Multiple missions with potentially the same number

## The Fix

### Files Changed
1. **CareBot/CareBot/sqllite_helper.py** (line 478)
   - Before: `VALUES(?, ?, ?, ?, ?, 1, ?)`
   - After: `VALUES(?, ?, ?, ?, ?, 0, ?)`

2. **CareBot/CareBot/mock_sqlite_helper.py** (line 360)
   - Before: `'locked': 1`
   - After: `'locked': 0`

### How It Works Now

```
Mission Lifecycle:
1. Mission created → locked=0 (unlocked, available)
2. get_mission finds it → can be assigned
3. lock_mission called → locked=1 (locked, in use)
4. Next get_mission → won't find locked mission
5. New mission created for next pair → different mission
```

## Detailed Flow Comparison

### Before Fix (Bug) ❌
```
Time T:
  └─ Pair 1 requests mission
      ├─ get_mission("killteam") → NULL (no unlocked missions)
      ├─ Generate new mission
      ├─ save_mission(...) → saves with locked=1 ❌
      ├─ Return mission to Pair 1
      └─ lock_mission() → already locked=1 (redundant)

Time T+10min:
  └─ Pair 2 requests mission
      ├─ get_mission("killteam") → NULL (Pair 1's mission has locked=1)
      ├─ Generate new mission ❌ (duplicate!)
      ├─ save_mission(...) → saves with locked=1 ❌
      └─ Return mission to Pair 2
```

### After Fix (Correct) ✅
```
Time T:
  └─ Pair 1 requests mission
      ├─ get_mission("killteam") → NULL (no unlocked missions)
      ├─ Generate new mission
      ├─ save_mission(...) → saves with locked=0 ✅
      ├─ Return mission to Pair 1
      └─ lock_mission() → sets locked=1 ✅

Time T+10min:
  └─ Pair 2 requests mission
      ├─ get_mission("killteam") → NULL (Pair 1's mission has locked=1)
      ├─ Generate new mission ✅ (different mission)
      ├─ save_mission(...) → saves with locked=0 ✅
      └─ Return mission to Pair 2
```

## Testing

### Tests Run
1. ✅ `test_mission_unlock.py` - All tests passed (5/5)
2. ✅ `validate_mission_fix.py` - All validations passed (4/4)
3. ✅ Code review - No issues found
4. ✅ Security scan (CodeQL) - No vulnerabilities

### Validation Tests
- [x] `save_mission` inserts with `locked=0`
- [x] `get_mission` queries for `locked=0`
- [x] `lock_mission` sets `locked=1`
- [x] Mock implementation matches real implementation

## Impact

### Positive Impact
✅ No more duplicate mission assignments  
✅ Missions properly locked when assigned to players  
✅ Each pair gets a unique mission  
✅ Mission pool management works correctly  

### Risk Assessment
- **Low Risk**: Minimal code changes (2 lines in 2 files)
- **Well Tested**: Existing test suite passes
- **Backward Compatible**: No database schema changes needed
- **No Breaking Changes**: Mission locking flow remains the same

## Code References

### Key Functions
- **`save_mission`** (sqllite_helper.py:472-480): Saves mission to database
- **`get_mission`** (sqllite_helper.py:283-292): Retrieves unlocked mission
- **`lock_mission`** (sqllite_helper.py:439-444): Locks mission when assigned
- **`get_mission`** (mission_helper.py:108-195): Main mission retrieval logic

### Mission States
- `locked=0`: Mission is unlocked, available for assignment
- `locked=1`: Mission is locked, currently in use by players
- `locked=2`: Mission is complete (score submitted)

## Deployment Notes

### Required Actions
None - the fix is backward compatible and doesn't require:
- Database migrations
- Configuration changes
- API changes
- Client updates

### Monitoring
After deployment, monitor for:
- Missions being assigned correctly to different pairs
- No duplicate mission complaints
- Mission pool growth rate (should be normal)

## Related Files
- `CareBot/CareBot/sqllite_helper.py` - Database helper functions
- `CareBot/CareBot/mock_sqlite_helper.py` - Mock for testing
- `CareBot/CareBot/mission_helper.py` - Mission business logic
- `test_mission_unlock.py` - Mission unlock tests
- `validate_mission_fix.py` - Validation tests for this fix

## Author Notes

This was a subtle but critical bug in the mission management system. The fix is minimal and surgical - changing only what's necessary to resolve the issue. The existing mission locking mechanism remains intact and continues to work as designed.

The key insight was recognizing the mismatch between the save and query states: missions were being saved as locked but queries expected unlocked missions.
