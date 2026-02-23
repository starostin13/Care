"""
Migration 011: Добавление текстов для управления альянсами
"""
from yoyo import step

def add_alliance_management_texts(conn):
    cursor = conn.cursor()
    
    # Тексты для управления альянсами
    texts = [
        # Кнопки
        ("button_alliance_management", "ru", "⚙️ Управление альянсами"),
        ("button_alliance_management", "en", "⚙️ Alliance Management"),
        ("button_create_alliance", "ru", "➕ Создать альянс"),
        ("button_create_alliance", "en", "➕ Create Alliance"),
        ("button_edit_alliance", "ru", "✏️ Редактировать альянс"),
        ("button_edit_alliance", "en", "✏️ Edit Alliance"),
        ("button_delete_alliance", "ru", "🗑️ Удалить альянс"),
        ("button_delete_alliance", "en", "🗑️ Delete Alliance"),
        ("button_assign_alliance", "ru", "👥 Назначить альянс игроку"),
        ("button_assign_alliance", "en", "👥 Assign Alliance to Player"),
        
        # Заголовки и сообщения
        ("admin_alliance_management_title", "ru", "Выберите действие с альянсами:"),
        ("admin_alliance_management_title", "en", "Choose alliance action:"),
        ("admin_create_alliance_title", "ru", "Введите название нового альянса:"),
        ("admin_create_alliance_title", "en", "Enter new alliance name:"),
        ("admin_edit_alliance_title", "ru", "Выберите альянс для редактирования:"),
        ("admin_edit_alliance_title", "en", "Choose alliance to edit:"),
        ("admin_delete_alliance_title", "ru", "Выберите альянс для удаления:"),
        ("admin_delete_alliance_title", "en", "Choose alliance to delete:"),
        ("admin_edit_alliance_name_title", "ru", "Введите новое название для альянса {alliance_name}:"),
        ("admin_edit_alliance_name_title", "en", "Enter new name for alliance {alliance_name}:"),
        
        # Подтверждения
        ("admin_delete_alliance_confirm", "ru", "⚠️ Вы уверены что хотите удалить альянс '{alliance_name}'?\n\n{players_count} игроков будут перераспределены по другим альянсам.\n\nЭто действие необратимо!"),
        ("admin_delete_alliance_confirm", "en", "⚠️ Are you sure you want to delete alliance '{alliance_name}'?\n\n{players_count} players will be redistributed to other alliances.\n\nThis action is irreversible!"),
        ("button_confirm_delete", "ru", "✅ Да, удалить"),
        ("button_confirm_delete", "en", "✅ Yes, delete"),
        ("button_cancel", "ru", "❌ Отмена"),
        ("button_cancel", "en", "❌ Cancel"),
        
        # Результаты
        ("admin_alliance_created", "ru", "✅ Альянс '{alliance_name}' создан!"),
        ("admin_alliance_created", "en", "✅ Alliance '{alliance_name}' created!"),
        ("admin_alliance_name_exists", "ru", "❌ Альянс с таким именем уже существует!"),
        ("admin_alliance_name_exists", "en", "❌ Alliance with this name already exists!"),
        ("admin_alliance_name_invalid", "ru", "❌ Недопустимое название альянса. Используйте только буквы, цифры и базовые символы. Максимум 50 символов."),
        ("admin_alliance_name_invalid", "en", "❌ Invalid alliance name. Use only letters, numbers and basic symbols. Maximum 50 characters."),
        ("admin_alliance_updated", "ru", "✅ Название альянса изменено на '{alliance_name}'!"),
        ("admin_alliance_updated", "en", "✅ Alliance name changed to '{alliance_name}'!"),
        ("admin_alliance_deleted", "ru", "✅ Альянс '{alliance_name}' удален. {players_count} игроков перераспределены."),
        ("admin_alliance_deleted", "en", "✅ Alliance '{alliance_name}' deleted. {players_count} players redistributed."),
        ("admin_cannot_delete_last_alliance", "ru", "❌ Нельзя удалить последний альянс!"),
        ("admin_cannot_delete_last_alliance", "en", "❌ Cannot delete the last alliance!"),
        ("admin_alliance_not_found", "ru", "❌ Альянс не найден!"),
        ("admin_alliance_not_found", "en", "❌ Alliance not found!"),
        ("admin_operation_cancelled", "ru", "❌ Операция отменена."),
        ("admin_operation_cancelled", "en", "❌ Operation cancelled."),
    ]
    
    for key, language, text in texts:
        cursor.execute('''
            INSERT OR REPLACE INTO texts (key, language, value) VALUES (?, ?, ?)
        ''', (key, language, text))
        print(f"✅ Added/updated text: {key} ({language})")
    
    print("✅ Alliance management texts added successfully")

steps = [step(add_alliance_management_texts)]