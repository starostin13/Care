#!/usr/bin/env python3
"""Test script to verify notification system functionality"""

import asyncio
import sys
sys.path.append('.')

from notification_service import notify_players_about_game
from sqllite_helper import get_players_for_game, add_or_update_text, set_language
from unittest.mock import AsyncMock, MagicMock

async def test_notification_system():
    """Test the notification system"""
    
    print("=== Testing Notification System ===\n")
    
    # Test 1: Check if we can get players for a game
    print("Test 1: Getting players for a game...")
    try:
        # Use a test date and rule
        test_date = "Wed Oct 30 00:00:00 2024"
        test_rule = "killteam"
        
        players = await get_players_for_game(test_rule, test_date)
        print(f"Found {len(players)} players for {test_rule} on {test_date}")
        for player in players:
            print(f"  Player: ID={player[0]}, Name={player[1]}, Notifications={player[2]}")
            
    except Exception as e:
        print(f"Error getting players: {e}")
    
    # Test 2: Test notification text generation
    print("\nTest 2: Testing notification text generation...")
    try:
        # Set up test users
        test_user_en = "test_user_en"
        test_user_ru = "test_user_ru"
        
        await set_language(test_user_en, "en")
        await set_language(test_user_ru, "ru")
        
        # Get notification texts
        from localization import get_text_for_user
        
        en_text = await get_text_for_user(
            test_user_en, 
            "game_notification",
            player_name="TestPlayer",
            game_date="Wed Oct 30 00:00:00 2024",
            game_rules="killteam"
        )
        
        ru_text = await get_text_for_user(
            test_user_ru,
            "game_notification", 
            player_name="TestPlayer",
            game_date="Wed Oct 30 00:00:00 2024",
            game_rules="killteam"
        )
        
        print(f"EN notification: {en_text}")
        print(f"RU notification: {ru_text}")
        
    except Exception as e:
        print(f"Error testing notification text: {e}")
    
    # Test 3: Mock bot context test 
    print("\nTest 3: Testing notification function (mocked)...")
    try:
        # Create a mock context
        mock_context = MagicMock()
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        
        # Test the notification function
        await notify_players_about_game(
            mock_context,
            organizer_id=12345,
            game_date="Wed Oct 30 00:00:00 2024", 
            game_rules="killteam"
        )
        
        print("Notification function completed without errors")
        print(f"Bot send_message was called {mock_bot.send_message.call_count} times")
        
    except Exception as e:
        print(f"Error testing notification function: {e}")

if __name__ == "__main__":
    asyncio.run(test_notification_system())