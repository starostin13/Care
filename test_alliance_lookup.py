#!/usr/bin/env python3
"""
Тест для проверки get_alliance_of_warmaster с разными типами данных
"""
import os
import sys
import asyncio

# Добавляем путь к модулям CareBot
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Устанавливаем тестовый режим
os.environ['CAREBOT_TEST_MODE'] = 'true'

import config
import mock_sqlite_helper as sqllite_helper

async def test_alliance_lookup():
    """Тестируем поиск альянса с разными типами telegram_id"""
    
    print("🧪 Testing get_alliance_of_warmaster with different data types...")
    
    # Тестовые ID из mock базы
    test_ids = [
        "325313837",  # string
        325313837,    # int
        "1049378497", # string  
        1049378497    # int
    ]
    
    for telegram_id in test_ids:
        print(f"\n🔍 Testing with telegram_id: {telegram_id} (type: {type(telegram_id).__name__})")
        
        try:
            result = await sqllite_helper.get_alliance_of_warmaster(telegram_id)
            print(f"  📊 Result: {result}")
            print(f"  📊 Type: {type(result)}")
            
            if result:
                print(f"  ✅ Alliance ID: {result[0]}")
            else:
                print(f"  ❌ No alliance found!")
                
        except Exception as e:
            print(f"  💥 Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_alliance_lookup())