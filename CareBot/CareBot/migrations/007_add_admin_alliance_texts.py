"""
Add admin alliance assignment localization texts
"""

from yoyo import step

__depends__ = {'006_add_game_notification_text'}

steps = [
    step("""
        INSERT OR REPLACE INTO texts (key, language, value) VALUES 
        ('button_admin', 'ru', '⚙️ Управление альянсами'),
        ('button_admin', 'en', '⚙️ Manage Alliances'),
        ('admin_assign_alliance_title', 'ru', 'Выберите игрока для назначения альянса:'),
        ('admin_assign_alliance_title', 'en', 'Select a player to assign alliance:'),
        ('admin_select_alliance_for_player', 'ru', 'Выберите альянс для игрока {player_name}:'),
        ('admin_select_alliance_for_player', 'en', 'Select alliance for player {player_name}:'),
        ('admin_alliance_assigned', 'ru', 'Альянс {alliance_name} назначен игроку {player_name}!'),
        ('admin_alliance_assigned', 'en', 'Alliance {alliance_name} assigned to player {player_name}!')
    """)
]
