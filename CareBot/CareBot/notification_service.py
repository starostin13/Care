"""
Notification service for sending game notifications to players
"""
import logging
from telegram.ext import ContextTypes
import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Notification Service using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Notification Service using REAL SQLite helper")
import localization

logger = logging.getLogger(__name__)


async def notify_players_about_game(context: ContextTypes.DEFAULT_TYPE, 
                                    organizer_id: int, 
                                    game_date: str, 
                                    game_rules: str):
    """
    Notify all players who signed up for the same game about a new participant
    
    Args:
        context: Telegram bot context
        organizer_id: ID of the player who just signed up
        game_date: Date of the game
        game_rules: Game rules/type
    """
    try:
        # Get all players signed up for the same game (including organizer)
        players = await sqllite_helper.get_players_for_game(game_rules, game_date)
        
        if not players:
            logger.info(f"No players found for game on {game_date} with rules {game_rules}")
            return
            
        # Get organizer info
        organizer_settings = await sqllite_helper.get_settings(organizer_id)
        organizer_name = organizer_settings[0] if organizer_settings and organizer_settings[0] else "Unknown Player"
        
        # Filter out the organizer from notification list and check notifications
        opponents_to_notify = []
        for player in players:
            player_id = player[0]
            player_name = player[1] 
            notifications_enabled = player[2] if len(player) > 2 else 1
            
            # Skip the organizer themselves
            if player_id == organizer_id:
                continue
                
            # Check if notifications are enabled
            if notifications_enabled != 1:
                logger.info(f"Notifications disabled for player {player_id}, skipping")
                continue
                
            opponents_to_notify.append(player_id)
        
        logger.info(f"Notifying {len(opponents_to_notify)} players about new participant {organizer_name}")
        
        for opponent_id in opponents_to_notify:
            try:
                # Get localized notification message
                notification_text = await localization.get_text_for_user(
                    opponent_id, 
                    "game_notification",
                    player_name=organizer_name,
                    game_date=game_date,
                    game_rules=game_rules
                )
                
                # Send notification
                await context.bot.send_message(
                    chat_id=opponent_id,
                    text=notification_text
                )
                
                logger.info(f"Notification sent to player {opponent_id}")
                
            except Exception as e:
                logger.error(f"Failed to send notification to player {opponent_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in notify_players_about_game: {e}")


async def notify_game_cancellation(context: ContextTypes.DEFAULT_TYPE,
                                 organizer_id: int,
                                 game_date: str,
                                 game_rules: str):
    """
    Notify players about game cancellation
    
    Args:
        context: Telegram bot context
        organizer_id: ID of the player who cancelled
        game_date: Date of the game
        game_rules: Game rules/type
    """
    try:
        # Get all players signed up for the same game
        opponents = await sqllite_helper.get_opponents(organizer_id, f"{game_date},{game_rules}")
        
        if not opponents:
            return
            
        # Get organizer info
        organizer_settings = await sqllite_helper.get_settings(organizer_id)
        organizer_name = organizer_settings[0] if organizer_settings and organizer_settings[0] else "Unknown Player"
        
        logger.info(f"Notifying {len(opponents)} players about game cancellation by {organizer_name}")
        
        for opponent in opponents:
            opponent_id = opponent[0]
            
            # Check if opponent has notifications enabled
            opponent_settings = await sqllite_helper.get_settings(opponent_id)
            if not opponent_settings or len(opponent_settings) < 4:
                continue
                
            notifications_enabled = opponent_settings[3] if len(opponent_settings) > 3 else 1
            if notifications_enabled != 1:
                continue
            
            # Get localized cancellation message
            try:
                cancellation_text = await localization.get_text_for_user(
                    opponent_id,
                    "game_cancellation",
                    player_name=organizer_name,
                    game_date=game_date,
                    game_rules=game_rules
                )
                
                await context.bot.send_message(
                    chat_id=opponent_id,
                    text=cancellation_text
                )
                
                logger.info(f"Cancellation notification sent to player {opponent_id}")
                
            except Exception as e:
                logger.error(f"Failed to send cancellation notification to player {opponent_id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in notify_game_cancellation: {e}")


async def notify_alliance_elimination(context: ContextTypes.DEFAULT_TYPE,
                                      eliminated_alliance_id: int):
    """
    Notify all players about alliance elimination and resource missions
    
    Args:
        context: Telegram bot context
        eliminated_alliance_id: ID of the eliminated alliance
    """
    try:
        # Get all players from eliminated alliance
        eliminated_players = await sqllite_helper.get_players_by_alliance(
            eliminated_alliance_id)
        
        # Get alliance name
        alliance_info = await sqllite_helper.get_alliance_by_id(
            eliminated_alliance_id)
        alliance_name = (alliance_info[1] if alliance_info
                         else "Unknown Alliance")
        
        # Notify eliminated alliance players
        for player in eliminated_players:
            player_id = player[0]
            try:
                elimination_text = await localization.get_text_for_user(
                    player_id, "alliance_eliminated_player")
                elimination_text = elimination_text.format(
                    alliance_name=alliance_name)
                
                await context.bot.send_message(
                    chat_id=player_id,
                    text=elimination_text
                )
                
                logger.info(
                    "Elimination notification sent to player %s", player_id)
                
            except Exception as e:
                logger.error(
                    "Failed to send elimination notification to "
                    "player %s: %s", player_id, e)
        
        # Notify all other players about resource missions
        all_players = await sqllite_helper.get_all_players()
        for player in all_players:
            player_id = player[0]
            player_alliance = player[2] if len(player) > 2 else 0
            
            # Skip players from eliminated alliance (already notified)
            if player_alliance == eliminated_alliance_id:
                continue
                
            try:
                missions_text = await localization.get_text_for_user(
                    player_id, "resource_missions_created")
                missions_text = missions_text.format(
                    alliance_name=alliance_name)
                
                await context.bot.send_message(
                    chat_id=player_id,
                    text=missions_text
                )
                
                logger.info(
                    "Resource missions notification sent to player %s",
                    player_id)
                
            except Exception as e:
                logger.error(
                    "Failed to send missions notification to "
                    "player %s: %s", player_id, e)
                
    except Exception as e:
        logger.error("Error in notify_alliance_elimination: %s", e)
