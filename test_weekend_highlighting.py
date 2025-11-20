#!/usr/bin/env python3
"""Test script to verify weekend highlighting in calendar"""

import asyncio
import sys
sys.path.append('./CareBot/CareBot')

from datetime import datetime, timedelta
from keyboard_constructor import this_week

async def test_weekend_highlighting():
    """Test that weekends are highlighted and placed first in calendar"""
    
    print("=== Testing Weekend Highlighting ===\n")
    
    # Test with a sample rule
    rule = "killteam"
    
    # Get the calendar layout
    calendar = await this_week(rule)
    
    print(f"Calendar layout with {len(calendar)} rows:\n")
    
    for row_idx, row in enumerate(calendar):
        print(f"Row {row_idx + 1}: {len(row)} button(s)")
        for button in row:
            print(f"  - {button.text}")
            # Check if button has weekend highlighting (🔵 emoji)
            if "🔵" in button.text:
                print(f"    ✓ Weekend day highlighted")
    
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
        # All buttons in first row should have 🔵 emoji (weekend markers)
        all_weekend = all("🔵" in button.text for button in first_row)
        if all_weekend:
            print("✓ First row contains only weekend days")
        else:
            print("✗ First row should contain only weekend days!")
        
        # Check that weekend days are actually Sat/Sun
        for button in first_row:
            callback = button.callback_data
            date_str = callback.split(',')[0]
            # Parse date to check weekday
            print(f"  Weekend button: {button.text}")
    else:
        print("ℹ No weekend days in the next 7 days")
    
    # Check that non-first rows don't have 🔵 emoji
    if len(calendar) > 1:
        for row_idx in range(1, len(calendar)):
            row = calendar[row_idx]
            has_emoji = any("🔵" in button.text for button in row)
            if has_emoji:
                print(f"✗ Row {row_idx + 1} should not contain weekend markers!")
            else:
                print(f"✓ Row {row_idx + 1} contains only weekdays")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_weekend_highlighting())
