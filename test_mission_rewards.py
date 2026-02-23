#!/usr/bin/env python3
"""
Тест apply_mission_rewards с исправлениями
"""

import asyncio
import aiosqlite
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_PATH = "/app/data/game_database.db"

async def test_apply_mission_rewards():
    """Эмулируем apply_mission_rewards с исправлениями"""
    
    # Тестовые данные
    battle_id = 71
    user_reply = "15 10"
    user_telegram_id = 325313837
    
    print(f"Testing apply_mission_rewards:")
    print(f"  battle_id: {battle_id}")
    print(f"  user_reply: {user_reply}")
    print(f"  user_telegram_id: {user_telegram_id}")
    
    counts = user_reply.split(' ')
    user_score = int(counts[0])
    opponent_score = int(counts[1])
    
    # Получаем opponent telegram ID
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT attender_id FROM battle_attenders 
            WHERE battle_id=? AND attender_id!=?
        ''', (battle_id, user_telegram_id)) as cursor:
            result = await cursor.fetchone()
            if result:
                opponent_telegram_id = result[0]
            else:
                print("❌ Opponent not found!")
                return
                
    print(f"  opponent_telegram_id: {opponent_telegram_id} (type: {type(opponent_telegram_id)})")
    
    # Принудительно конвертируем в string
    user_telegram_id = str(user_telegram_id)
    opponent_telegram_id = str(opponent_telegram_id)
    
    print(f"  After conversion:")
    print(f"    user_telegram_id: {user_telegram_id} (type: {type(user_telegram_id)})")
    print(f"    opponent_telegram_id: {opponent_telegram_id} (type: {type(opponent_telegram_id)})")
    
    # Тестируем получение альянсов
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # User alliance
        async with db.execute('''
            SELECT alliance FROM warmasters WHERE telegram_id=?
        ''', (user_telegram_id,)) as cursor:
            user_alliance_id = await cursor.fetchone()
            
        # Opponent alliance  
        async with db.execute('''
            SELECT alliance FROM warmasters WHERE telegram_id=?
        ''', (opponent_telegram_id,)) as cursor:
            opponent_alliance_id = await cursor.fetchone()
    
    print(f"  Alliance results:")
    print(f"    user_alliance_id: {user_alliance_id}")
    print(f"    opponent_alliance_id: {opponent_alliance_id}")
    
    if user_alliance_id is None or opponent_alliance_id is None:
        print("❌ One or both alliances not found!")
        return None
        
    # Определяем победителя
    if user_score > opponent_score:
        winner_alliance_id = user_alliance_id[0]
        loser_alliance_id = opponent_alliance_id[0]
        print(f"✅ Winner: user (alliance {winner_alliance_id})")
        print(f"✅ Loser: opponent (alliance {loser_alliance_id})")
    else:
        winner_alliance_id = opponent_alliance_id[0]
        loser_alliance_id = user_alliance_id[0]
        print(f"✅ Winner: opponent (alliance {winner_alliance_id})")
        print(f"✅ Loser: user (alliance {loser_alliance_id})")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_apply_mission_rewards())