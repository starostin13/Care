"""
Add game_notification text for localization
"""

from yoyo import step

__depends__ = {'005_add_name_input_translations'}

steps = [
    step("""
        INSERT OR REPLACE INTO texts (key, language, value) VALUES 
        ('game_notification', 'ru', 'Игрок {player_name} записался на игру {game_date} по правилам {game_rules}!'),
        ('game_notification', 'en', 'Player {player_name} signed up for game {game_date} with rules {game_rules}!'),
        ('game_cancellation', 'ru', 'Игрок {player_name} отменил участие в игре {game_date} по правилам {game_rules}'),
        ('game_cancellation', 'en', 'Player {player_name} cancelled participation in game {game_date} with rules {game_rules}')
    """)
]