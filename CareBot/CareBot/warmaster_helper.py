#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

"""
Helper module for warmaster operations.
Handles user registration, contact management, and warmaster-related functionality.
"""

import sqllite_helper
import logging

logger = logging.getLogger(__name__)


async def register_warmaster(user_id: int, phone: str) -> bool:
    """
    Register a warmaster with phone number.
    
    Args:
        user_id: Telegram user ID
        phone: Phone number
        
    Returns:
        bool: True if registration successful
    """
    try:
        result = sqllite_helper.register_warmaster(user_id, phone)
        logger.info(f"Warmaster {user_id} registered with phone {phone}")
        return result
    except Exception as e:
        logger.error(f"Failed to register warmaster {user_id}: {e}")
        return False


async def get_warmaster_info(user_id: int) -> dict:
    """
    Get warmaster information.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        dict: Warmaster information
    """
    try:
        # This function would need to be implemented in sqllite_helper
        # For now, we'll return basic info
        return {"user_id": user_id, "registered": True}
    except Exception as e:
        logger.error(f"Failed to get warmaster info for {user_id}: {e}")
        return {}


async def is_warmaster_registered(user_id: int) -> bool:
    """
    Check if warmaster is registered.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        bool: True if registered
    """
    try:
        # This would need implementation in sqllite_helper
        return True  # Placeholder
    except Exception as e:
        logger.error(f"Failed to check registration for {user_id}: {e}")
        return False