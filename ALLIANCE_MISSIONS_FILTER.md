# Alliance Allies Filter in Missions - Implementation Summary

## Issue
**Title:** В клавиатуре со списком миссий не должно показывать союзников по альянсу  
**Translation:** In the keyboard with the list of missions, it should not show alliance allies

## Problem
Previously, when users clicked on the "Missions" button in the bot, the missions keyboard would show all available opponents including their alliance allies. This was incorrect behavior as players should not be matched against their own alliance members.

## Solution

### Files Modified

1. **CareBot/CareBot/sqllite_helper.py**
   - Modified `get_schedule_with_warmasters()` function
   - Added alliance filtering logic using SQL CTE (Common Table Expression)
   - Improved performance by fetching current user's alliance once instead of multiple times

2. **CareBot/CareBot/mock_sqlite_helper.py**
   - Updated mock implementation to match the real implementation
   - Added alliance filtering logic to exclude allies in test mode

### Implementation Details

#### SQL Query Logic
The new implementation uses a CTE and a NOT condition to efficiently filter out alliance allies:

```sql
WITH current_user_alliance AS (
    SELECT alliance FROM warmasters WHERE telegram_id=?
)
SELECT schedule.id, schedule.rules, warmasters.nickname 
FROM schedule 
JOIN warmasters ON schedule.user_telegram=warmasters.telegram_id 
CROSS JOIN current_user_alliance
WHERE schedule.user_telegram<>? 
AND schedule.date=?
AND (
    -- Exclude allies: both users must have valid alliances AND they must be the same
    NOT (
        warmasters.alliance IS NOT NULL 
        AND warmasters.alliance != 0
        AND current_user_alliance.alliance IS NOT NULL
        AND current_user_alliance.alliance != 0
        AND warmasters.alliance = current_user_alliance.alliance
    )
)
```

#### Logic Explanation
The filter excludes a warmaster ONLY when ALL of the following conditions are true:
1. The opponent has a non-null alliance
2. The opponent's alliance is not 0 (zero means no alliance)
3. The current user has a non-null alliance
4. The current user's alliance is not 0
5. Both alliances are the same

This means:
- ✅ Users without alliance (NULL or 0) can see missions normally
- ✅ Users from different alliances can see each other
- ❌ Users from the same alliance CANNOT see each other in missions

### Testing

Created two comprehensive test files:

1. **test_alliance_missions_filter.py**
   - Tests basic alliance filtering functionality
   - Validates SQL query structure
   - Ensures users without alliance can see missions

2. **test_alliance_missions_integration.py**
   - Tests edge cases (same alliance, alliance = 0, NULL alliance)
   - Validates that alliance = 0 users can see each other (not treated as same alliance)
   - Comprehensive integration testing

All tests pass successfully ✅

### Code Review & Security

- ✅ Code review completed - no issues found
- ✅ CodeQL security scan - no vulnerabilities detected
- ✅ Performance improved by using CTE instead of multiple subqueries
- ✅ Logic corrected based on code review feedback

### Expected Behavior

**Before:** Users saw ALL opponents including alliance allies  
**After:** Users see ONLY opponents from different alliances or without alliance

### Examples

**Scenario 1: User with Alliance**
- User A (Alliance 1) ➡️ Can see users from Alliance 2, 3, etc.
- User A (Alliance 1) ➡️ CANNOT see users from Alliance 1

**Scenario 2: User without Alliance**
- User B (No alliance) ➡️ Can see all users including those with alliances

**Scenario 3: Alliance = 0**
- User C (Alliance = 0) ➡️ Can see all users (0 means no alliance, not Alliance #0)
- User D (Alliance = 0) ➡️ Can see User C (they are not considered same alliance)

## Verification

Run the following tests to verify the implementation:
```bash
python test_alliance_missions_filter.py
python test_alliance_missions_integration.py
python test_alliance_logic.py  # Ensure no regressions
```

All tests should pass ✅

## Notes

- The mock implementation mirrors the real implementation for testing purposes
- The CTE approach is more efficient than multiple subqueries
- The NOT condition makes the logic clearer and easier to understand
- Users with NULL or 0 alliance are not restricted and can see all missions
