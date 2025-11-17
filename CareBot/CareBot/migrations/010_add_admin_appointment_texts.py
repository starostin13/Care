"""
Add admin appointment localization texts
"""

from yoyo import step

__depends__ = {'009_add_winner_bonus_to_mission_stack'}

steps = [
    step("""
        INSERT OR REPLACE INTO texts (key, language, value) VALUES 
        ('button_appoint_admin', 'ru', '👑 Назначить администратора'),
        ('button_appoint_admin', 'en', '👑 Appoint Administrator'),
        ('admin_appoint_title', 'ru', 'Выберите пользователя для назначения администратором:'),
        ('admin_appoint_title', 'en', 'Select a user to appoint as administrator:'),
        ('admin_appointed_success', 'ru', 'Пользователь {user_name} назначен администратором!'),
        ('admin_appointed_success', 'en', 'User {user_name} has been appointed as administrator!')
    """)
]
