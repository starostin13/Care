"""
Migration 030: Add localization texts for admin active missions management menu.

Adds texts for:
- Admin menu button for active missions
- Active missions list title
- Active mission detail view
- Unlock mission action
- Enter score action (for status=1 and status=2 missions)
"""
from yoyo import step


def add_admin_active_missions_texts(conn):
    cursor = conn.cursor()

    texts = [
        # Warning when trying to unlock a mission that has a battle
        ("admin_unlock_mission_battle_warning", "ru", "⚠️ Миссия #{mission_id} привязана к бою #{battle_id}.\n\nПри разблокировке миссия получит статус 0, а бой останется без изменений (будет висеть как сирота).\n\nВы уверены?"),
        ("admin_unlock_mission_battle_warning", "en", "⚠️ Mission #{mission_id} is linked to battle #{battle_id}.\n\nUnlocking will set the mission to status 0, but the battle record will remain (orphaned).\n\nAre you sure?"),

        # Admin menu button for active missions
        ("button_admin_active_missions", "ru", "⚔️ Активные миссии"),
        ("button_admin_active_missions", "en", "⚔️ Active Missions"),

        # Active missions list title
        ("admin_active_missions_title", "ru", "⚔️ Активные миссии (статус 1) — {count}:\n\nВыберите миссию для управления:"),
        ("admin_active_missions_title", "en", "⚔️ Active Missions (status 1) — {count}:\n\nSelect a mission to manage:"),

        # No active missions
        ("admin_no_active_missions", "ru", "✅ Нет активных миссий (статус 1)."),
        ("admin_no_active_missions", "en", "✅ No active missions (status 1)."),

        # Active mission detail
        ("admin_active_mission_detail", "ru", "⚔️ Миссия #{mission_id}\n📅 Создана: {created_date}\n📜 Правила: {rules}\n🗺️ Клетка: {cell}\n\n👥 Участники:\n  • {p1_name}\n  • {p2_name}\n\nВыберите действие:"),
        ("admin_active_mission_detail", "en", "⚔️ Mission #{mission_id}\n📅 Created: {created_date}\n📜 Rules: {rules}\n🗺️ Cell: {cell}\n\n👥 Participants:\n  • {p1_name}\n  • {p2_name}\n\nSelect action:"),

        # Active mission detail when no battle found
        ("admin_active_mission_no_battle", "ru", "⚔️ Миссия #{mission_id}\n📅 Создана: {created_date}\n📜 Правила: {rules}\n\n⚠️ Бой не найден\n\nВыберите действие:"),
        ("admin_active_mission_no_battle", "en", "⚔️ Mission #{mission_id}\n📅 Created: {created_date}\n📜 Rules: {rules}\n\n⚠️ Battle not found\n\nSelect action:"),

        # Unlock button
        ("btn_unlock_mission", "ru", "🔓 Разблокировать (→ статус 0)"),
        ("btn_unlock_mission", "en", "🔓 Unlock (→ status 0)"),

        # Enter score button
        ("btn_enter_score", "ru", "📝 Ввести счёт"),
        ("btn_enter_score", "en", "📝 Enter Score"),

        # Unlock success
        ("admin_mission_unlocked", "ru", "✅ Миссия #{mission_id} разблокирована (статус 0)."),
        ("admin_mission_unlocked", "en", "✅ Mission #{mission_id} unlocked (status 0)."),

        # Prompt for score input
        ("admin_enter_score_prompt", "ru", "📝 Введите счёт для миссии #{mission_id} в формате X:Y\n(например: 3:1)"),
        ("admin_enter_score_prompt", "en", "📝 Enter score for mission #{mission_id} in format X:Y\n(e.g. 3:1)"),

        # Invalid score format
        ("admin_score_invalid_format", "ru", "❌ Неверный формат счёта. Введите X:Y (например: 3:1)"),
        ("admin_score_invalid_format", "en", "❌ Invalid score format. Enter X:Y (e.g. 3:1)"),

        # Score saved success
        ("admin_score_saved", "ru", "✅ Счёт миссии #{mission_id} сохранён: {fst_score}:{snd_score}"),
        ("admin_score_saved", "en", "✅ Mission #{mission_id} score saved: {fst_score}:{snd_score}"),

        # Error when no battle for mission during score entry
        ("admin_score_no_battle", "ru", "❌ Бой не найден для миссии #{mission_id}. Нельзя ввести счёт."),
        ("admin_score_no_battle", "en", "❌ Battle not found for mission #{mission_id}. Cannot enter score."),

        # Error applying score
        ("admin_score_apply_error", "ru", "❌ Ошибка при сохранении счёта: {error}"),
        ("admin_score_apply_error", "en", "❌ Error saving score: {error}"),

        # Override score button (for status=2 missions)
        ("btn_override_score", "ru", "✏️ Изменить счёт"),
        ("btn_override_score", "en", "✏️ Override Score"),

        # Active missions count button label in admin menu
        ("admin_active_count", "ru", "⚔️ Активные миссии ({active_count})"),
        ("admin_active_count", "en", "⚔️ Active Missions ({active_count})"),
    ]

    for key, lang, text in texts:
        cursor.execute(
            "SELECT id FROM texts WHERE key = ? AND language = ?",
            (key, lang)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO texts (key, language, text) VALUES (?, ?, ?)",
                (key, lang, text)
            )

    conn.commit()
    print("✅ Migration 030: admin active missions texts added")


steps = [step(add_admin_active_missions_texts)]
