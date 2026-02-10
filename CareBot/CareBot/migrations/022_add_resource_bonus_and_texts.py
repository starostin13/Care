"""
Migration 022: Add reward_config column for missions and localization texts
for alliance resource features.
"""
from yoyo import step


def add_reward_config_column(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(mission_stack)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'reward_config' not in columns:
        cursor.execute(
            "ALTER TABLE mission_stack ADD COLUMN reward_config TEXT"
        )
        print("✅ Добавлена колонка reward_config в таблицу mission_stack")
    else:
        print("✅ Колонка reward_config уже существует в mission_stack")


def add_common_resource_texts(conn):
    cursor = conn.cursor()
    texts = [
        ("button_alliance_resources", "ru", "💎 Ресурсы альянса"),
        ("button_alliance_resources", "en", "💎 Alliance Resources"),
        ("alliance_resources_message", "ru", "Ресурсы альянса {alliance_name}: {resources}"),
        ("alliance_resources_message", "en", "Alliance {alliance_name} resources: {resources}"),
        ("alliance_no_alliance", "ru", "У вас пока не выбран альянс."),
        ("alliance_no_alliance", "en", "You are not assigned to an alliance yet."),
        ("button_admin_adjust_resources", "ru", "⚙️ Ресурсы альянсов"),
        ("button_admin_adjust_resources", "en", "⚙️ Alliance Resources"),
        ("admin_adjust_resources_title", "ru", "Выберите альянс для изменения ресурсов"),
        ("admin_adjust_resources_title", "en", "Select an alliance to adjust resources"),
        ("admin_adjust_resource_prompt", "ru", "Введите изменение ресурсов для {alliance_name} (текущее значение: {current}). Пример: 2 или -1"),
        ("admin_adjust_resource_prompt", "en", "Enter resource change for {alliance_name} (current: {current}). Example: 2 or -1"),
        ("admin_adjust_resource_success", "ru", "Ресурсы альянса {alliance_name} изменены на {delta}. Текущее значение: {new_value}"),
        ("admin_adjust_resource_success", "en", "Alliance {alliance_name} resources changed by {delta}. Current value: {new_value}"),
        ("admin_adjust_resource_invalid", "ru", "Введите целое число (например 2 или -1)."),
        ("admin_adjust_resource_invalid", "en", "Please enter an integer value (e.g. 2 or -1)."),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO texts (key, language, value) VALUES (?, ?, ?)",
        texts
    )
    print(f"✅ Добавлены {len(texts)} текстов для ресурсов альянсов")


steps = [
    step(add_reward_config_column),
    step(add_common_resource_texts)
]
