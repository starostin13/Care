#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт проверки настройки проекта
"""

import sys
import os
import importlib.util
import asyncio

def check_python_version():
    """Проверка версии Python"""
    print(f"🐍 Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print("✅ Python version OK")
    return True

def check_dependencies():
    """Проверка установленных зависимостей"""
    dependencies = ['telegram', 'flask', 'aiosqlite', 'numpy', 'requests']
    optional_dependencies = ['kivy']
    missing = []
    
    print("📦 Required dependencies:")
    for dep in dependencies:
        spec = importlib.util.find_spec(dep)
        if spec is None:
            missing.append(dep)
            print(f"❌ Missing: {dep}")
        else:
            print(f"✅ Found: {dep}")
    
    print("\n📱 Optional dependencies (for mobile app):")
    for dep in optional_dependencies:
        spec = importlib.util.find_spec(dep)
        if spec is None:
            print(f"⚠️ Optional: {dep} (install for mobile app)")
        else:
            print(f"✅ Found: {dep}")
    
    if missing:
        print(f"\n📦 Install missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def check_files():
    """Проверка наличия важных файлов"""
    important_files = [
        'handlers.py',
        'views.py', 
        'config.py',
        'sqllite_helper.py',
        'templates/map.html',
        '.vscode/launch.json',
        '.vscode/tasks.json',
        # Новые файлы
        'mission_engine/__init__.py',
        'mobile_app/crusade_mobile.py',
        'server_app.py',
        'sync_api.py',
        'templates/missions.html',
        'templates/print_station.html'
    ]
    
    missing_files = []
    for file_path in important_files:
        if os.path.exists(file_path):
            print(f"✅ Found: {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
    
    return len(missing_files) == 0

def check_database():
    """Проверка подключения к базе данных"""
    try:
        import sqllite_helper
        
        async def test_db():
            try:
                cells = await sqllite_helper.get_all_map_cells()
                print(f"✅ Database OK, found {len(cells)} map cells")
                return True
            except Exception as e:
                print(f"❌ Database error: {e}")
                return False
        
        return asyncio.run(test_db())
    except ImportError as e:
        print(f"❌ Cannot import sqllite_helper: {e}")
        return False

def check_config():
    """Проверка конфигурации"""
    try:
        import config
        if hasattr(config, 'crusade_care_bot_telegram_token'):
            token = config.crusade_care_bot_telegram_token
            if token and len(token) > 10:
                print("✅ Telegram bot token configured")
                return True
            else:
                print("❌ Telegram bot token not configured properly")
                return False
        else:
            print("❌ Telegram bot token not found in config")
            return False
    except ImportError as e:
        print(f"❌ Cannot import config: {e}")
        return False

def check_mission_engine():
    """Проверка движка миссий"""
    try:
        from mission_engine import MissionGenerator, MissionType, Player, MapHex, Faction
        
        # Тестируем генерацию миссии
        generator = MissionGenerator()
        players = [
            Player("test1", "Test Player 1", Faction.SPACE_MARINES, "alliance_1"),
            Player("test2", "Test Player 2", Faction.CHAOS, "alliance_2")
        ]
        hex = MapHex(1, 1, "contested")
        
        mission = generator.generate_mission(MissionType.KILL_TEAM, players, hex)
        
        print(f"✅ Mission Engine OK - Generated: {mission.title}")
        return True
        
    except ImportError as e:
        print(f"❌ Mission Engine import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Mission Engine error: {e}")
        return False

def main():
    """Главная функция проверки"""
    print("🔍 Checking CareBot setup...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Files", check_files),
        ("Configuration", check_config),
        ("Database", check_database),
        ("Mission Engine", check_mission_engine)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "="*50)
    print("📊 SUMMARY:")
    print("="*50)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if not result:
            all_passed = False
    
    print("="*50)
    if all_passed:
        print("🎉 All checks passed! Ready to run!")
        print("\n🚀 Available options:")
        print("   📱 Mobile App: python mobile_app/crusade_mobile.py")
        print("   🌐 Server App: python server_app.py")
        print("   🤖 Telegram Bot: python handlers.py")
        print("   🖨️ Print Station: http://localhost:5000/print-station")
    else:
        print("🔧 Some issues found. Please fix them before running.")
    
    return all_passed

if __name__ == '__main__':
    main()
