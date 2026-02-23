#!/usr/bin/env python3
"""
Тест функции get_opponent_telegram_id на production
"""

import asyncio
import aiosqlite

DATABASE_PATH = "/app/data/game_database.db"

async def test_get_opponent_telegram_id(battle_id, user_telegram_id):
    print(f"Testing battle_id: {battle_id}, user_telegram_id: {user_telegram_id}")
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Проверим что есть в battle_attenders для этого батла
        async with db.execute('''
            SELECT battle_id, attender_id FROM battle_attenders WHERE battle_id=?
        ''', (battle_id,)) as cursor:
            rows = await cursor.fetchall()
            print(f"  Battle attenders: {rows}")
        
        # Эмулируем логику get_opponent_telegram_id
        async with db.execute('''
            SELECT attender_id FROM battle_attenders 
            WHERE battle_id=? AND attender_id!=?
        ''', (battle_id, user_telegram_id)) as cursor:
            result = await cursor.fetchone()
            print(f"  Opponent result: {result}")
            return result

async def main():
    print("🔍 Testing get_opponent_telegram_id on production...")
    
    # Тестируем батл 71
    battle_id = 71
    user_ids = [325313837, "325313837", 1049378497, "1049378497"]
    
    for user_id in user_ids:
        print(f"\n{'='*60}")
        try:
            result = await test_get_opponent_telegram_id(battle_id, user_id)
            if result:
                print(f"✅ Opponent found: {result[0]} (type: {type(result[0])})")
            else:
                print("❌ No opponent found!")
        except Exception as e:
            print(f"💥 Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())