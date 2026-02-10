"""
Migration 022: Add localization texts for custom admin notifications feature
"""

import sys
import os

# Add parent directory to path to import sqllite_helper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import sqllite_helper


async def migrate():
    """Add localization texts for custom notification feature."""
    
    texts = [
        # Admin menu button
        ("button_admin_custom_notification", "ru", "📢 Отправить уведомление"),
        ("button_admin_custom_notification", "en", "📢 Send notification"),
        
        # Select recipient type
        ("custom_notification_select_recipient_type", "ru", "📢 Выберите тип получателя уведомления:"),
        ("custom_notification_select_recipient_type", "en", "📢 Select notification recipient type:"),
        
        # Recipient type buttons
        ("button_notify_warmaster", "ru", "👤 Отправить одному игроку"),
        ("button_notify_warmaster", "en", "👤 Send to one player"),
        
        ("button_notify_alliance", "ru", "⚔️ Отправить альянсу"),
        ("button_notify_alliance", "en", "⚔️ Send to alliance"),
        
        # Select warmaster
        ("custom_notification_select_warmaster", "ru", "👤 Выберите игрока для отправки уведомления:"),
        ("custom_notification_select_warmaster", "en", "👤 Select player to send notification:"),
        
        # Select alliance
        ("custom_notification_select_alliance", "ru", "⚔️ Выберите альянс для отправки уведомления:"),
        ("custom_notification_select_alliance", "en", "⚔️ Select alliance to send notification:"),
        
        # Request message
        ("custom_notification_send_message", "ru", "📝 Отправьте сообщение, которое будет отправлено игроку/альянсу: {recipient_name}\n\nСообщение может содержать текст или изображение с подписью."),
        ("custom_notification_send_message", "en", "📝 Send the message to be delivered to: {recipient_name}\n\nThe message can contain text or an image with caption."),
        
        # Confirmation message
        ("custom_notification_sent", "ru", "✅ Уведомление отправлено!\n\nПолучатель: {recipient_name}\nУспешно: {success_count}\nОшибок: {failure_count}"),
        ("custom_notification_sent", "en", "✅ Notification sent!\n\nRecipient: {recipient_name}\nSuccess: {success_count}\nFailed: {failure_count}"),
        
        # Error messages
        ("no_warmasters_found", "ru", "⚠️ Не найдено игроков с никнеймами."),
        ("no_warmasters_found", "en", "⚠️ No players with nicknames found."),
        
        ("no_alliances_found", "ru", "⚠️ Не найдено альянсов."),
        ("no_alliances_found", "en", "⚠️ No alliances found."),
        
        ("error_notification_session_expired", "ru", "⚠️ Сессия отправки уведомления истекла. Начните заново."),
        ("error_notification_session_expired", "en", "⚠️ Notification session expired. Please start over."),
        
        ("error_no_recipients", "ru", "⚠️ Не найдено получателей для отправки уведомления."),
        ("error_no_recipients", "en", "⚠️ No recipients found for notification."),
        
        # Back and cancel buttons
        ("button_back", "ru", "⬅️ Назад"),
        ("button_back", "en", "⬅️ Back"),
        
        ("button_cancel", "ru", "❌ Отмена"),
        ("button_cancel", "en", "❌ Cancel"),
    ]
    
    print("Migration 022: Adding custom notification texts...")
    
    for key, language, value in texts:
        await sqllite_helper.add_or_update_text(key, language, value)
        print(f"  ✓ Added text: {key} ({language})")
    
    print("Migration 022 completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
