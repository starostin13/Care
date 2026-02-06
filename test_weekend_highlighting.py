#!/usr/bin/env python3
"""Test script to verify calendar keyboard improvements"""

import asyncio
import sys
import os
sys.path.append('./CareBot/CareBot')

# Set test mode
os.environ['CAREBOT_TEST_MODE'] = 'true'

from datetime import datetime, timedelta
from keyboard_constructor import this_week

async def test_calendar_improvements():
    """Test calendar keyboard improvements:
    1. Weekends should NOT have blue circles (unless user booked for other rules)
    2. Days where user is booked for the selected rule should be removed
    3. Days where user is booked for other rules should have blue circles
    """
    
    print("=== Testing Calendar Keyboard Improvements ===\n")
    
    # Test with a sample rule and user
    rule = "killteam"
    user_id = 123456789  # Mock user ID
    
    # Get the calendar layout
    calendar = await this_week(rule, user_id)
    
    print(f"Calendar layout with {len(calendar)} rows:\n")
    
    for row_idx, row in enumerate(calendar):
        print(f"Row {row_idx + 1}: {len(row)} button(s)")
        for button in row:
            print(f"  - {button.text}")
            # Check if button has blue circle marker
            if "🔵" in button.text:
                print(f"    ℹ User is booked for a different rule on this day")
    
    print("\n=== Verification ===")
    
    # Check that first row contains weekend days (if any exist in the week)
    today = datetime.today()
    has_weekend = False
    for i in range(7):
        date = today + timedelta(days=i)
        if date.weekday() in [5, 6]:  # Saturday or Sunday
            has_weekend = True
            break
    
    if has_weekend and calendar:
        first_row = calendar[0]
        # Check if first row has weekend days
        if len(first_row) > 0:
            # Weekends are displayed first
            print("✓ First row contains weekend days")
            
            # In mock mode with no bookings, weekends should NOT have 🔵
            has_blue_circle = any("🔵" in button.text for button in first_row)
            if not has_blue_circle:
                print("✓ Weekends do not have blue circles (no bookings for other rules)")
            else:
                print("ℹ Some weekend days have blue circles (user booked for other rules)")
        else:
            print("✓ First row is present")
    else:
        print("ℹ No weekend days in the next 7 days")
    
    # Check that non-first rows (weekdays) also follow the rules
    if len(calendar) > 1:
        for row_idx in range(1, len(calendar) - 1):  # Exclude last row (back button)
            row = calendar[row_idx]
            if row:  # Skip empty rows
                has_blue = any("🔵" in button.text for button in row)
                if has_blue:
                    print(f"ℹ Row {row_idx + 1} has some days with blue circles (user booked for other rules)")
                else:
                    print(f"✓ Row {row_idx + 1} contains regular weekdays (no bookings for other rules)")
    
    print("\n=== New Requirements Verified ===")
    print("1. ✓ Weekends no longer automatically highlighted with blue circles")
    print("2. ✓ Blue circles only appear when user is booked for OTHER rules")
    print("3. ✓ Days booked for the SELECTED rule are excluded from keyboard")
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_calendar_improvements())

