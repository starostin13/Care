#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8

"""
Helper module for warmaster operations.
Handles user registration, contact management, and warmaster-related functionality.
"""

import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Warmaster Helper using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Warmaster Helper using REAL SQLite helper")
import logging
import notification_service
from datetime import datetime, timedelta

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


async def check_and_transfer_inactive_players(context, threshold_multiplier=2.0):
    """
    Check all alliances for inactive players and transfer them to other alliances.
    
    A player is considered inactive if their inactivity duration is significantly 
    longer than the average inactivity of their alliance (determined by threshold_multiplier).
    
    Args:
        context: Telegram bot context for sending notifications
        threshold_multiplier: How many times more inactive than average to trigger transfer (default: 2.0)
        
    Returns:
        dict: Summary of transfers performed
    """
    try:
        logger.info("Starting inactive player check and transfer process")
        
        # Get all alliances
        alliances = await sqllite_helper.get_all_alliances()
        transfers_performed = []
        
        for alliance_id, alliance_name in alliances:
            logger.info(f"Checking alliance: {alliance_name} (ID: {alliance_id})")
            
            # Get inactive players in this alliance
            inactive_players = await sqllite_helper.get_inactive_players_in_alliance(
                alliance_id, threshold_multiplier
            )
            
            if not inactive_players:
                logger.info(f"No inactive players found in alliance {alliance_name}")
                continue
            
            logger.info(f"Found {len(inactive_players)} inactive players in alliance {alliance_name}")
            
            # Get average inactivity for notification
            avg_inactivity_days = await sqllite_helper.get_alliance_average_inactivity_days(alliance_id)
            avg_activity_str = f"{avg_inactivity_days:.1f} days ago" if avg_inactivity_days else "N/A"
            
            for player_id, player_nickname, days_inactive in inactive_players:
                logger.info(f"Processing transfer for inactive player: {player_nickname} ({days_inactive:.1f} days inactive)")
                
                # Find target alliance
                target_alliance_id = await sqllite_helper.get_target_alliance_for_inactive_player(alliance_id)
                
                if not target_alliance_id:
                    logger.warning(f"No target alliance found for player {player_nickname}")
                    continue
                
                # Get target alliance name
                target_alliance = await sqllite_helper.get_alliance_by_id(target_alliance_id)
                if not target_alliance:
                    logger.warning(f"Could not get target alliance details for ID {target_alliance_id}")
                    continue
                
                target_alliance_name = target_alliance[1]  # alliance tuple is (id, name, resources)
                
                # Perform the transfer
                transfer_result = await sqllite_helper.transfer_inactive_player(
                    player_id, alliance_id, target_alliance_id
                )
                
                if not transfer_result['success']:
                    logger.error(f"Failed to transfer player {player_nickname}: {transfer_result['message']}")
                    continue
                
                logger.info(f"Successfully transferred {player_nickname} from {alliance_name} to {target_alliance_name}")
                
                # Get last active timestamp for notifications
                last_active = await sqllite_helper.get_player_last_active(player_id)
                last_active_str = f"{days_inactive:.1f} days ago" if last_active else "Unknown"
                
                # Send notifications
                try:
                    await notification_service.notify_inactive_player_transfer(
                        context=context,
                        player_telegram_id=player_id,
                        player_name=player_nickname or "Unknown Player",
                        from_alliance_id=alliance_id,
                        from_alliance_name=alliance_name,
                        to_alliance_id=target_alliance_id,
                        to_alliance_name=target_alliance_name,
                        last_active=last_active_str,
                        alliance_avg_activity=avg_activity_str
                    )
                    logger.info(f"Notifications sent for transfer of {player_nickname}")
                except Exception as e:
                    logger.error(f"Failed to send notifications for {player_nickname}: {e}")
                
                transfers_performed.append({
                    'player_id': player_id,
                    'player_name': player_nickname,
                    'from_alliance': alliance_name,
                    'to_alliance': target_alliance_name,
                    'days_inactive': days_inactive
                })
        
        logger.info(f"Inactive player transfer process completed. Total transfers: {len(transfers_performed)}")
        
        return {
            'success': True,
            'transfers_count': len(transfers_performed),
            'transfers': transfers_performed
        }
        
    except Exception as e:
        logger.error(f"Error in check_and_transfer_inactive_players: {e}")
        return {
            'success': False,
            'error': str(e),
            'transfers_count': 0,
            'transfers': []
        }