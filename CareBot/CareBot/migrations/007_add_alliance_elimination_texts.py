"""
Add alliance elimination texts for localization
"""

from yoyo import step

__depends__ = {'006_add_game_notification_text'}

steps = [
    step("""
        INSERT OR REPLACE INTO texts (key, language, value)
        VALUES ('alliance_eliminated_player', 'ru', '⚠️ Ваш альянс {alliance_name} был исключён из игры! У альянса не осталось территорий.\n\nВы переведены в статус ''без альянса''. Обратитесь к администратору для назначения в новый альянс.');
    """),
    step("""
        INSERT OR REPLACE INTO texts (key, language, value)
        VALUES ('alliance_eliminated_player', 'en', '⚠️ Your alliance {alliance_name} has been eliminated from the game! The alliance has no territories left.\n\nYou have been set to ''no alliance'' status. Contact an administrator to be assigned to a new alliance.');
    """),
    step("""
        INSERT OR REPLACE INTO texts (key, language, value)
        VALUES ('resource_missions_created', 'ru', '📦 Альянс {alliance_name} исключён из игры!\n\nИх ресурсы были преобразованы в миссии ''Сбор ресурсов''. Эти миссии теперь доступны для выполнения всеми оставшимися альянсами.');
    """),
    step("""
        INSERT OR REPLACE INTO texts (key, language, value)
        VALUES ('resource_missions_created', 'en', '📦 Alliance {alliance_name} has been eliminated!\n\nTheir resources have been converted into ''Resource Collection'' missions. These missions are now available for all remaining alliances.');
    """),
]