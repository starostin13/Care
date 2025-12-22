#!/usr/bin/env python3
"""
Тест функции get_alliance_of_warmaster на production
"""

import asyncio
import aiosqlite

DATABASE_PATH = "/app/data/game_database.db"

async def test_get_alliance_of_warmaster(telegram_user_id):
    print(f"Testing telegram_id: {telegram_user_id} (type: {type(telegram_user_id).__name__})")
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Сначала проверим что есть в таблице 
        async with db.execute('''
            SELECT telegram_id, alliance FROM warmasters WHERE telegram_id LIKE ?
        ''', (f"%{telegram_user_id}%",)) as cursor:
            rows = await cursor.fetchall()
            print(f"  Found rows with LIKE: {rows}")
        
        # Теперь точный поиск
        async with db.execute('''
            SELECT alliance FROM warmasters WHERE telegram_id=?
        ''', (telegram_user_id,)) as cursor:
            result = await cursor.fetchone()
            print(f"  Exact match result: {result}")
            return result

async def main():
    print("🔍 Testing get_alliance_of_warmaster on production...")
    
    # Тестируем с разными типами
    test_ids = ["325313837", 325313837, "1049378497", 1049378497]
    
    for telegram_id in test_ids:
        print(f"\n{'='*50}")
        try:
            result = await test_get_alliance_of_warmaster(telegram_id)
            if result:
                print(f"✅ Alliance found: {result[0]}")
            else:
                print("❌ No alliance found!")
        except Exception as e:
            print(f"💥 Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())