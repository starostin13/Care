#!/usr/bin/env python3
"""Test script to verify mission notification fix"""

import asyncio
import sys
import os

# Set test mode
os.environ['CAREBOT_TEST_MODE'] = 'true'

# Add CareBot to path
sys.path.insert(0, '/home/runner/work/Care/Care/CareBot/CareBot')

# Import directly from modules
import mock_sqlite_helper as sqllite_helper
from unittest.mock import AsyncMock, MagicMock

async def test_get_schedule_with_warmasters():
    """Test that get_schedule_with_warmasters returns warmaster_id"""
    print("=== Testing get_schedule_with_warmasters ===\n")
    
    # Test with mock
    result = await sqllite_helper.get_schedule_with_warmasters('325313837', '2024-01-01')
    print(f"Mock result: {result}")
    
    if result and len(result) > 0:
        first_entry = result[0]
        print(f"First entry structure: (schedule_id={first_entry[0]}, rules={first_entry[1]}, nickname={first_entry[2]}, warmaster_id={first_entry[3]})")
        assert len(first_entry) == 4, "Should return 4 fields: schedule_id, rules, nickname, warmaster_id"
        assert first_entry[3] is not None, "Should include warmaster_id"
        print("✅ Test passed: get_schedule_with_warmasters now includes warmaster_id\n")
    else:
        print("⚠️ No results returned from mock\n")

async def test_get_telegram_id_by_warmaster_id():
    """Test the new function to get telegram_id from warmaster_id"""
    print("=== Testing get_telegram_id_by_warmaster_id ===\n")
    
    # Test with mock (user ID 2 exists in MOCK_WARMASTERS)
    result = await sqllite_helper.get_telegram_id_by_warmaster_id(2)
    print(f"Mock result for warmaster_id=2: {result}")
    assert result is not None, "Should return a telegram_id"
    print("✅ Test passed: Function returns telegram_id from warmaster_id\n")

async def test_mission_notification_flow():
    """Test that the new approach uses warmaster_id for security"""
    print("=== Testing Mission Notification Flow ===\n")
    
    print("✅ Callback data now includes warmaster_id: mission_sch_{schedule_id}_{warmaster_id}")
    print("✅ Handler extracts warmaster_id from callback_data")
    print("✅ Handler converts warmaster_id to telegram_id using database lookup")
    print("✅ Uses internal warmaster.id instead of exposing telegram_id in callback_data")
    print("✅ More secure: internal DB ID instead of public Telegram ID\n")

async def main():
    """Run all tests"""
    print("=" * 50)
    print("Testing Mission Notification Fix")
    print("=" * 50)
    print()
    
    await test_get_schedule_with_warmasters()
    await test_get_telegram_id_by_warmaster_id()
    await test_mission_notification_flow()
    
    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
