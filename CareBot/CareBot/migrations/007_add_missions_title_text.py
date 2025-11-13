"""
Add missions_title text for localization
"""

from yoyo import step

__depends__ = {'006_add_game_notification_text'}

steps = [
    step("""
        INSERT OR REPLACE INTO texts (key, language, value) VALUES 
        ('missions_title', 'ru', 'Выберите оппонента для игры:'),
        ('missions_title', 'en', 'Select opponent for the game:')
    """)
]
