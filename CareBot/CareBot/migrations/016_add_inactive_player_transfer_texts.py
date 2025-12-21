"""
Migration 016: Add localization texts for inactive player transfer notifications
"""
from yoyo import step

def add_inactive_player_transfer_texts(conn):
    cursor = conn.cursor()
    
    # Тексты для уведомлений о переводе неактивного игрока
    texts = [
        # Уведомление админам
        ("inactive_player_transfer_admin_notification", "ru", 
         "⚠️ Игрок {player_name} был переведен из альянса '{from_alliance}' в альянс '{to_alliance}' из-за длительной неактивности.\n\n"
         "Последняя активность: {last_active}\n"
         "Среднее время последней активности в альянсе '{from_alliance}': {alliance_avg_activity}"),
        ("inactive_player_transfer_admin_notification", "en", 
         "⚠️ Player {player_name} was transferred from alliance '{from_alliance}' to alliance '{to_alliance}' due to long inactivity.\n\n"
         "Last activity: {last_active}\n"
         "Average last activity time in alliance '{from_alliance}': {alliance_avg_activity}"),
        
        # Уведомление игроку которого перевели
        ("inactive_player_transfer_player_notification", "ru",
         "⚠️ Вы были переведены в альянс '{to_alliance}' из-за длительной неактивности.\n\n"
         "Ваша последняя активность была: {last_active}\n"
         "Пожалуйста, участвуйте в миссиях, чтобы оставаться активным членом альянса."),
        ("inactive_player_transfer_player_notification", "en",
         "⚠️ You have been transferred to alliance '{to_alliance}' due to long inactivity.\n\n"
         "Your last activity was: {last_active}\n"
         "Please participate in missions to remain an active alliance member."),
        
        # Уведомление участникам старого альянса
        ("inactive_player_transfer_old_alliance_notification", "ru",
         "ℹ️ Игрок {player_name} был переведен в другой альянс из-за длительной неактивности.\n\n"
         "Последняя активность игрока: {last_active}"),
        ("inactive_player_transfer_old_alliance_notification", "en",
         "ℹ️ Player {player_name} has been transferred to another alliance due to long inactivity.\n\n"
         "Player's last activity: {last_active}"),
        
        # Уведомление участникам нового альянса
        ("inactive_player_transfer_new_alliance_notification", "ru",
         "ℹ️ Игрок {player_name} был переведен в ваш альянс из альянса '{from_alliance}'.\n\n"
         "Добро пожаловать в команду!"),
        ("inactive_player_transfer_new_alliance_notification", "en",
         "ℹ️ Player {player_name} has been transferred to your alliance from alliance '{from_alliance}'.\n\n"
         "Welcome to the team!"),
    ]
    
    for key, language, text in texts:
        cursor.execute('''
            INSERT OR REPLACE INTO texts (key, language, value) VALUES (?, ?, ?)
        ''', (key, language, text))
        print(f"✅ Added/updated text: {key} ({language})")
    
    print("✅ Inactive player transfer notification texts added successfully")

steps = [step(add_inactive_player_transfer_texts)]
