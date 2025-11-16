#!/usr/bin/env python3
"""Test script to verify localized keyboard functionality"""

import asyncio
import sys
sys.path.append('.')

from keyboard_constructor import get_main_menu, setting, language_selection
from sqllite_helper import get_settings, set_language
from localization import get_text_for_user

async def test_keyboard_localization():
    """Test keyboard localization with different languages"""
    
    # Test user IDs for different languages
    test_users = {
        "test_user_en": "en",
        "test_user_ru": "ru"
    }
    
    print("=== Testing Keyboard Localization ===\n")
    
    for user_id, language in test_users.items():
        print(f"Testing user: {user_id} (language: {language})")
        
        # Set user language
        await set_language(user_id, language)
        
        # Test main menu
        print(f"\n--- Main Menu for {language} ---")
        main_menu = await get_main_menu(user_id)
        for row in main_menu:
            for button in row:
                print(f"Button: {button.text} (callback: {button.callback_data})")
        
        # Test settings menu
        print(f"\n--- Settings Menu for {language} ---")
        settings_menu = await setting(user_id)
        for row in settings_menu:
            for button in row:
                print(f"Button: {button.text} (callback: {button.callback_data})")
        
        # Test language selection
        print(f"\n--- Language Selection for {language} ---")
        lang_menu = await language_selection(user_id)
        for row in lang_menu:
            for button in row:
                print(f"Button: {button.text} (callback: {button.callback_data})")
        
        print(f"\n{'='*50}\n")

if __name__ == "__main__":
    asyncio.run(test_keyboard_localization())