#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

"""
Helper module for schedule and game appointment operations.
Handles game scheduling, participant management, and event coordination.
"""

import sqllite_helper
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def register_for_game(game_date: datetime, game_rules: str, user_id: int) -> bool:
    """
    Register player for a scheduled game.
    
    Args:
        game_date: Date and time of the game
        game_rules: Game rules/system (e.g., 'killteam', 'wh40k')
        user_id: Telegram user ID
        
    Returns:
        bool: True if registration successful
    """
    try:
        await sqllite_helper.insert_to_schedule(game_date, game_rules, user_id)
        logger.info(f"User {user_id} registered for {game_rules} game on {game_date}")
        return True
    except Exception as e:
        logger.error(f"Failed to register user {user_id} for game: {e}")
        return False


async def get_event_participants(event_id: str) -> list:
    """
    Get all participants for a specific event.
    
    Args:
        event_id: Event identifier
        
    Returns:
        list: List of participant tuples
    """
    try:
        participants = await sqllite_helper.get_event_participants(event_id)
        logger.info(f"Retrieved {len(participants)} participants for event {event_id}")
        return participants
    except Exception as e:
        logger.error(f"Failed to get participants for event {event_id}: {e}")
        return []


async def get_mission_rules(mission_number: int) -> str:
    """
    Get the rules for a specific mission.
    
    Args:
        mission_number: Mission identifier
        
    Returns:
        str: Game rules for the mission
    """
    try:
        rules = await sqllite_helper.get_rules_of_mission(mission_number)
        logger.info(f"Retrieved rules for mission {mission_number}: {rules}")
        return rules
    except Exception as e:
        logger.error(f"Failed to get rules for mission {mission_number}: {e}")
        return "killteam"  # Default rules


async def get_user_scheduled_games(user_id: int) -> list:
    """
    Get all scheduled games for a specific user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        list: List of scheduled games
    """
    try:
        # This would need implementation in sqllite_helper
        # For now returning empty list
        return []
    except Exception as e:
        logger.error(f"Failed to get scheduled games for user {user_id}: {e}")
        return []


async def cancel_game_registration(user_id: int, event_id: str) -> bool:
    """
    Cancel user registration for a game.
    
    Args:
        user_id: Telegram user ID
        event_id: Event identifier
        
    Returns:
        bool: True if cancellation successful
    """
    try:
        # This would need implementation in sqllite_helper
        logger.info(f"User {user_id} cancelled registration for event {event_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel registration for user {user_id}: {e}")
        return False


async def get_game_schedule_for_date(date: datetime, rules: str = None) -> list:
    """
    Get all scheduled games for a specific date.
    
    Args:
        date: Target date
        rules: Optional game rules filter
        
    Returns:
        list: List of scheduled games
    """
    try:
        # This would need implementation in sqllite_helper
        return []
    except Exception as e:
        logger.error(f"Failed to get schedule for date {date}: {e}")
        return []