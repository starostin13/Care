"""
Migration 023: Add enhanced alliance information localization texts.
Updates the alliance resources display to show comprehensive alliance information
including resources, player count, and territory count.
"""
from yoyo import step


def add_alliance_info_texts(conn):
    cursor = conn.cursor()
    texts = [
        # Enhanced alliance info message with resources, players, and territories
        ("alliance_info_message", "ru", "📊 Информация об альянсе {alliance_name}\n\n💎 Ресурсы: {resources}\n👥 Игроков: {player_count}\n🗺️ Территорий: {territory_count}"),
        ("alliance_info_message", "en", "📊 Alliance {alliance_name} Information\n\n💎 Resources: {resources}\n👥 Players: {player_count}\n🗺️ Territories: {territory_count}"),
        # Update button text to reflect comprehensive info (keep old key for backward compatibility)
        ("button_alliance_resources", "ru", "📊 Информация об альянсе"),
        ("button_alliance_resources", "en", "📊 Alliance Information"),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO texts (key, language, value) VALUES (?, ?, ?)",
        texts
    )
    print(f"✅ Добавлены {len(texts)} текстов для расширенной информации об альянсах")


steps = [
    step(add_alliance_info_texts)
]
