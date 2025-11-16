#!/usr/bin/env python3
"""
Скрипт проверки production безопасности
Проверяет что в production Docker образе нет тестовых файлов и mock данных
"""

import os
import sys
import glob

# Файлы и паттерны, которые НЕ должны попадать в production
FORBIDDEN_IN_PRODUCTION = [
    "**/mock_sqlite_helper.py",
    "**/test_*.py", 
    "TEST_MODE_GUIDE.md",
    "VSCODE_QUICKSTART.md",
    "scripts/test-mode.ps1",
    "test_storage/**",
    ".vscode/**",
    ".env",
    ".env.local"
]

def check_production_safety():
    """Проверяет что production образ не содержит тестовых файлов"""
    print("Checking production safety...")
    
    forbidden_found = []
    
    for pattern in FORBIDDEN_IN_PRODUCTION:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            forbidden_found.extend(matches)
    
    if forbidden_found:
        print("CRITICAL ERROR: Found test files in production!")
        print("Found files:")
        for file in forbidden_found:
            print(f"  ERROR: {file}")
        print("\nThese files must be excluded via .dockerignore")
        return False
    
    print("OK: Production safety check passed")
    return True

def check_test_mode_environment():
    """Проверяет что TEST_MODE не установлен в production"""
    test_mode = os.getenv('CAREBOT_TEST_MODE', 'false').lower()
    
    if test_mode == 'true':
        print("WARNING: CAREBOT_TEST_MODE=true in production!")
        print("Make sure this is NOT a production environment")
        return False
    
    print("OK: Environment variables check passed")
    return True

def main():
    """Основная функция проверки"""
    print("CareBot Production Safety Check")
    print("=" * 50)
    
    safety_checks = [
        check_production_safety(),
        check_test_mode_environment()
    ]
    
    if all(safety_checks):
        print("\nSUCCESS: All safety checks passed!")
        print("READY: Production is ready for deployment")
        return 0
    else:
        print("\nFAILED: Safety checks failed!")
        print("BLOCKED: Deployment blocked")
        return 1

if __name__ == "__main__":
    sys.exit(main())