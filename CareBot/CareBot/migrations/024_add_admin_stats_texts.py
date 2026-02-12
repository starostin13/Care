"""
Migration 024: Add localization texts for admin statistics menu.
"""
from yoyo import step


def add_admin_stats_texts(conn):
    cursor = conn.cursor()
    texts = [
        ("button_admin_stats", "ru", "📊 Статистика"),
        ("button_admin_stats", "en", "📊 Statistics"),
        ("button_admin_stats_users", "ru", "👥 Список пользователей"),
        ("button_admin_stats_users", "en", "👥 User list"),
        ("button_admin_stats_alliances", "ru", "🛡️ Список альянсов"),
        ("button_admin_stats_alliances", "en", "🛡️ Alliance list"),
        ("admin_stats_title", "ru", "Что показать?"),
        ("admin_stats_title", "en", "What would you like to view?"),
        ("admin_stats_users_title", "ru", "Игроки (игры за последний месяц)"),
        ("admin_stats_users_title", "en", "Players (games in the last month)"),
        ("admin_stats_alliances_title", "ru", "Альянсы (игры за последний месяц)"),
        ("admin_stats_alliances_title", "en", "Alliances (games in the last month)"),
        ("admin_stats_alliance_users_title", "ru", "Игроки альянса {alliance_name}"),
        ("admin_stats_alliance_users_title", "en", "Players of alliance {alliance_name}"),
        ("admin_stats_no_data", "ru", "Нет завершённых игр за последний месяц."),
        ("admin_stats_no_data", "en", "No completed games in the last month."),
        ("admin_stats_games_label", "ru", "игр"),
        ("admin_stats_games_label", "en", "games"),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO texts (key, language, value) VALUES (?, ?, ?)",
        texts
    )
    print(f"✅ Добавлены {len(texts)} текстов для админской статистики")


steps = [
    step(add_admin_stats_texts)
]
