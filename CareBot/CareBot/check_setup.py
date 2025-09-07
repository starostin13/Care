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
    dependencies = ['telegram', 'flask', 'aiosqlite', 'numpy']
    missing = []
    
    for dep in dependencies:
        spec = importlib.util.find_spec(dep)
        if spec is None:
            missing.append(dep)
            print(f"❌ Missing: {dep}")
        else:
            print(f"✅ Found: {dep}")
    
    if missing:
        print(f"\n📦 Install missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def check_docker():
    """Проверка Docker установки"""
    try:
        # Проверяем Docker
        result = os.system("docker --version >nul 2>&1" if os.name == 'nt' else "docker --version >/dev/null 2>&1")
        if result != 0:
            print("❌ Docker не установлен")
            return False
        print("✅ Docker установлен")
        
        # Проверяем Docker Compose
        result = os.system("docker-compose --version >nul 2>&1" if os.name == 'nt' else "docker-compose --version >/dev/null 2>&1")
        if result != 0:
            print("❌ Docker Compose не установлен")
            return False
        print("✅ Docker Compose установлен")
        
        # Проверяем запущен ли Docker
        result = os.system("docker info >nul 2>&1" if os.name == 'nt' else "docker info >/dev/null 2>&1")
        if result != 0:
            print("⚠️  Docker не запущен (запустите Docker Desktop)")
            return False
        print("✅ Docker запущен")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки Docker: {e}")
        return False

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
        'Dockerfile',
        'docker-compose.yml',
        '.env.example',
        'requirements.txt'
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

def main():
    """Главная функция проверки"""
    print("🔍 Checking CareBot setup...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Docker Environment", check_docker),
        ("Project Files", check_files),
        ("Configuration", check_config),
        ("Database", check_database)
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
        print("🎉 All checks passed! Ready to deploy!")
        print("\n🚀 Deployment options:")
        print("   LOCAL DEVELOPMENT:")
        print("   1. Press Ctrl+Shift+D in VS Code")
        print("   2. Select '🤖 Debug Telegram Bot'")
        print("   3. Press F5")
        print("")
        print("   DOCKER DEPLOYMENT:")
        print("   1. Copy .env.example to .env and edit it")
        print("   2. Run: deploy.bat (Windows) or ./deploy.sh (Linux)")
        print("   3. Access: http://localhost/miniapp")
    else:
        print("🔧 Some issues found. Please fix them before deployment.")
        
        # Дополнительные советы
        if not any(name == "Docker Environment" and result for name, result in results):
            print("\n💡 Docker tips:")
            print("   - Install Docker Desktop from docker.com")
            print("   - Make sure Docker is running")
            print("   - You can still use local development without Docker")
    
    return all_passed

if __name__ == '__main__':
    main()
