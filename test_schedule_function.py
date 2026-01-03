#!/usr/bin/env python3
"""Test the get_daily_rule_participant_count function"""

import asyncio
import sys
import os

# Add CareBot to path
sys.path.insert(0, r'C:\Users\staro\Projects\Care\CareBot')

# Test directly with mock first
os.environ['CAREBOT_TEST_MODE'] = 'true'

from CareBot import sqllite_helper

async def test():
    """Test the function"""
    # Test with mock data
    count = await sqllite_helper.get_daily_rule_participant_count('killteam', '2026-01-04')
    print(f'Mock test - Participants for killteam on 2026-01-04: {count}')
    
    # Test with different dates
    count2 = await sqllite_helper.get_daily_rule_participant_count('wh40k', '2026-01-03')
    print(f'Mock test - Participants for wh40k on 2026-01-03: {count2}')

if __name__ == '__main__':
    asyncio.run(test())
