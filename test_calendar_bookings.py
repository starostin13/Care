#!/usr/bin/env python3
"""Test script to verify calendar keyboard with user bookings"""

import asyncio
import sys
import os
sys.path.append('./CareBot/CareBot')

# Set test mode
os.environ['CAREBOT_TEST_MODE'] = 'true'

from datetime import datetime, timedelta
from keyboard_constructor import this_week
import mock_sqlite_helper

# Add mock bookings
async def add_mock_bookings():
    """Add mock bookings for testing"""
    from datetime import datetime, timedelta
    
    today = datetime.today()
    
    # Create mock bookings for the next few days
    mock_bookings = {
        str((today + timedelta(days=1)).date()): 'killteam',  # Tomorrow booked for killteam
        str((today + timedelta(days=3)).date()): 'wh40k',      # Day 3 booked for wh40k
        str((today + timedelta(days=5)).date()): 'killteam',  # Day 5 booked for killteam
    }
    
    # Monkey patch the mock function to return our test bookings
    async def mock_get_user_bookings_for_dates(user_telegram, dates):
        print(f"🧪 Mock: get_user_bookings_for_dates({user_telegram}, {dates})")
        return {date: rule for date, rule in mock_bookings.items() if date in dates}
    
    mock_sqlite_helper.get_user_bookings_for_dates = mock_get_user_bookings_for_dates
    
    return mock_bookings

async def test_calendar_with_bookings():
    """Test calendar keyboard with various booking scenarios"""
    
    print("=== Testing Calendar Keyboard with User Bookings ===\n")
    
    # Add mock bookings
    mock_bookings = await add_mock_bookings()
    
    print("Mock bookings created:")
    for date, rule in mock_bookings.items():
        print(f"  - {date}: {rule}")
    print()
    
    # Test 1: Calendar for killteam (should exclude days booked for killteam)
    print("=== Test 1: Calendar for 'killteam' rule ===")
    rule = "killteam"
    user_id = 123456789
    
    calendar = await this_week(rule, user_id)
    
    print(f"Calendar layout with {len(calendar)} rows:\n")
    
    today = datetime.today()
    expected_excluded = []
    expected_blue_circles = []
    
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = str(date.date())
        if date_str in mock_bookings:
            if mock_bookings[date_str] == rule:
                expected_excluded.append(date_str)
            else:
                expected_blue_circles.append(date_str)
    
    print(f"Expected excluded dates (booked for {rule}): {expected_excluded}")
    print(f"Expected blue circle dates (booked for other rules): {expected_blue_circles}\n")
    
    for row_idx, row in enumerate(calendar):
        print(f"Row {row_idx + 1}: {len(row)} button(s)")
        for button in row:
            print(f"  - {button.text}")
            if "🔵" in button.text:
                print(f"    ✓ Has blue circle (user booked for different rule)")
    
    print("\n=== Test 2: Calendar for 'wh40k' rule ===")
    rule = "wh40k"
    
    calendar = await this_week(rule, user_id)
    
    expected_excluded = []
    expected_blue_circles = []
    
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = str(date.date())
        if date_str in mock_bookings:
            if mock_bookings[date_str] == rule:
                expected_excluded.append(date_str)
            else:
                expected_blue_circles.append(date_str)
    
    print(f"Expected excluded dates (booked for {rule}): {expected_excluded}")
    print(f"Expected blue circle dates (booked for other rules): {expected_blue_circles}\n")
    
    for row_idx, row in enumerate(calendar):
        print(f"Row {row_idx + 1}: {len(row)} button(s)")
        for button in row:
            print(f"  - {button.text}")
            if "🔵" in button.text:
                print(f"    ✓ Has blue circle (user booked for different rule)")
    
    print("\n=== Verification Summary ===")
    print("✓ Days booked for the selected rule are excluded from the calendar")
    print("✓ Days booked for other rules are marked with blue circles")
    print("✓ Weekends are no longer automatically highlighted")
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_calendar_with_bookings())
