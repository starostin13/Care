"""
Add admin toggle localization texts (revoke and error messages)
"""

from yoyo import step

__depends__ = {'010_add_admin_appointment_texts'}

steps = [
    step("""
        INSERT OR REPLACE INTO texts (key, language, value) VALUES 
        ('admin_revoked_success', 'ru', 'Права администратора сняты с пользователя {user_name}!'),
        ('admin_revoked_success', 'en', 'Administrator rights have been revoked from user {user_name}!'),
        ('admin_operation_failed', 'ru', 'Не удалось изменить права пользователя {user_name}. {reason}'),
        ('admin_operation_failed', 'en', 'Failed to change rights for user {user_name}. {reason}')
    """)
]
