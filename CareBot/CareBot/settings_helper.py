#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

"""
Helper module for user settings operations.
Handles language preferences, notifications, and other user settings.
"""

import sqllite_helper
import logging

logger = logging.getLogger(__name__)


async def get_user_settings(user_id: int) -> tuple:
    """
    Get user settings including nickname, language, notifications.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        tuple: User settings (nickname, language, notifications_enabled)
    """
    try:
        settings = await sqllite_helper.get_settings(user_id)
        logger.info(f"Retrieved settings for user {user_id}")
        return settings
    except Exception as e:
        logger.error(f"Failed to get settings for user {user_id}: {e}")
        return None


async def set_user_language(user_id: int, language: str) -> bool:
    """
    Set user language preference.
    
    Args:
        user_id: Telegram user ID
        language: Language code (e.g., 'en', 'ru')
        
    Returns:
        bool: True if successful
    """
    try:
        await sqllite_helper.set_language(user_id, language)
        logger.info(f"Set language {language} for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to set language for user {user_id}: {e}")
        return False


async def toggle_user_notifications(user_id: int) -> int:
    """
    Toggle user notification preferences.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        int: New notification status (1 for enabled, 0 for disabled)
    """
    try:
        new_value = await sqllite_helper.toggle_notifications(user_id)
        logger.info(f"Toggled notifications for user {user_id} to {new_value}")
        return new_value
    except Exception as e:
        logger.error(f"Failed to toggle notifications for user {user_id}: {e}")
        return 0


async def has_user_nickname(user_id: int) -> bool:
    """
    Check if user has set a nickname.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        bool: True if user has nickname
    """
    try:
        settings = await get_user_settings(user_id)
        return settings and settings[0] is not None
    except Exception as e:
        logger.error(f"Failed to check nickname for user {user_id}: {e}")
        return False


async def get_user_language(user_id: int) -> str:
    """
    Get user language preference.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        str: Language code or 'en' as default
    """
    try:
        settings = await get_user_settings(user_id)
        if settings and len(settings) > 2 and settings[2]:
            return settings[2]
        return 'en'  # Default language
    except Exception as e:
        logger.error(f"Failed to get language for user {user_id}: {e}")
        return 'en'


async def are_notifications_enabled(user_id: int) -> bool:
    """
    Check if notifications are enabled for user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        bool: True if notifications enabled
    """
    try:
        settings = await get_user_settings(user_id)
        if settings and len(settings) > 3 and settings[3] is not None:
            return bool(settings[3])
        return True  # Default to enabled
    except Exception as e:
        logger.error(f"Failed to check notifications for user {user_id}: {e}")
        return True