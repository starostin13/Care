"""
Migration 012: Добавление недостающих текстов для управления альянсами
"""
from yoyo import step

def add_missing_alliance_texts(conn):
    cursor = conn.cursor()
    
    # Недостающие тексты для управления альянсами
    texts = [
        # Заголовок админского меню
        ("admin_menu_title", "ru", "🔧 Панель администратора"),
        ("admin_menu_title", "en", "🔧 Administrator Panel"),
        
        # Кнопки
        ("button_admin_alliance_management", "ru", "⚙️ Управление альянсами"),
        ("button_admin_alliance_management", "en", "⚙️ Alliance Management"),
        ("button_admin_assign_alliance", "ru", "👥 Назначить альянс игроку"),
        ("button_admin_assign_alliance", "en", "👥 Assign Alliance to Player"),
        ("button_edit_alliances", "ru", "✏️ Редактировать альянсы"),
        ("button_edit_alliances", "en", "✏️ Edit Alliances"),
        ("button_delete_alliances", "ru", "🗑️ Удалить альянсы"),
        ("button_delete_alliances", "en", "🗑️ Delete Alliances"),
        ("button_rename_alliance", "ru", "✏️ Переименовать"),
        ("button_rename_alliance", "en", "✏️ Rename"),
        
        # Заголовки страниц
        ("admin_create_alliance_prompt", "ru", "📝 Введите название нового альянса:\n\n💡 Максимум 50 символов\n🔤 Разрешены буквы, цифры и основные символы"),
        ("admin_create_alliance_prompt", "en", "📝 Enter new alliance name:\n\n💡 Maximum 50 characters\n🔤 Letters, numbers and basic symbols allowed"),
        ("admin_edit_alliances_title", "ru", "✏️ Выберите альянс для редактирования:"),
        ("admin_edit_alliances_title", "en", "✏️ Choose alliance to edit:"),
        ("admin_delete_alliances_title", "ru", "🗑️ Выберите альянс для удаления:"),
        ("admin_delete_alliances_title", "en", "🗑️ Choose alliance to delete:"),
        ("admin_edit_alliance_title", "ru", "⚙️ Редактирование альянса '{alliance_name}':"),
        ("admin_edit_alliance_title", "en", "⚙️ Editing alliance '{alliance_name}':"),
        ("admin_rename_alliance_prompt", "ru", "✏️ Введите новое название для альянса '{alliance_name}':\n\n💡 Максимум 50 символов"),
        ("admin_rename_alliance_prompt", "en", "✏️ Enter new name for alliance '{alliance_name}':\n\n💡 Maximum 50 characters"),
        ("admin_delete_alliance_confirm", "ru", "⚠️ Вы уверены что хотите удалить альянс '{alliance_name}'?\n\nВ альянсе: {player_count} игроков\nОни будут перераспределены по другим альянсам.\n\n🚨 Это действие необратимо!"),
        ("admin_delete_alliance_confirm", "en", "⚠️ Are you sure you want to delete alliance '{alliance_name}'?\n\nPlayers in alliance: {player_count}\nThey will be redistributed to other alliances.\n\n🚨 This action is irreversible!"),
        
        # Результаты операций
        ("admin_alliance_created_success", "ru", "✅ Альянс '{alliance_name}' успешно создан!"),
        ("admin_alliance_created_success", "en", "✅ Alliance '{alliance_name}' created successfully!"),
        ("admin_alliance_name_exists", "ru", "❌ Альянс с названием '{alliance_name}' уже существует!"),
        ("admin_alliance_name_exists", "en", "❌ Alliance with name '{alliance_name}' already exists!"),
        ("admin_alliance_creation_error", "ru", "❌ Ошибка при создании альянса:"),
        ("admin_alliance_creation_error", "en", "❌ Error creating alliance:"),
        ("admin_alliance_renamed_success", "ru", "✅ Альянс переименован в '{alliance_name}'!"),
        ("admin_alliance_renamed_success", "en", "✅ Alliance renamed to '{alliance_name}'!"),
        ("admin_alliance_rename_error", "ru", "❌ Ошибка при переименовании альянса"),
        ("admin_alliance_rename_error", "en", "❌ Error renaming alliance"),
        ("admin_alliance_not_found", "ru", "❌ Альянс не найден"),
        ("admin_alliance_not_found", "en", "❌ Alliance not found"),
        ("admin_alliance_deleted_success", "ru", "✅ Альянс удален. Перераспределено игроков: {players_redistributed}"),
        ("admin_alliance_deleted_success", "en", "✅ Alliance deleted. Players redistributed: {players_redistributed}"),
        ("admin_alliance_deletion_error", "ru", "❌ Ошибка при удалении альянса:"),
        ("admin_alliance_deletion_error", "en", "❌ Error deleting alliance:"),
    ]
    
    for key, language, text in texts:
        cursor.execute('''
            INSERT OR REPLACE INTO texts (key, language, value) VALUES (?, ?, ?)
        ''', (key, language, text))
        print(f"✅ Added/updated text: {key} ({language})")
    
    print("✅ Missing alliance management texts added successfully")

steps = [step(add_missing_alliance_texts)]