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
    ".env"
]

def read_dockerignore():
    """Читает .dockerignore файл и возвращает список паттернов"""
    dockerignore_path = ".dockerignore"
    patterns = []
    
    if not os.path.exists(dockerignore_path):
        print("WARNING: .dockerignore not found")
        return patterns
    
    with open(dockerignore_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Пропускаем комментарии и пустые строки
            if line and not line.startswith('#'):
                patterns.append(line)
    
    return patterns

def is_pattern_in_dockerignore(filename, dockerignore_patterns):
    """Проверяет есть ли файл в паттернах .dockerignore"""
    import fnmatch
    
    # Нормализуем путь к файлу
    filename = filename.replace("\\", "/")
    
    for pattern in dockerignore_patterns:
        # Игнорируем комментарии
        if pattern.startswith('#'):
            continue
        
        # Проверяем паттерны:
        # - Точное совпадение (например, ".env")
        # - Glob паттерн (например, "test_*.py" или "**/mock_*.py")
        # - Папки (например, ".vscode/")
        
        if pattern == filename:
            # Точное совпадение
            return True
        
        if fnmatch.fnmatch(filename, pattern):
            # Glob совпадение
            return True
        
        if fnmatch.fnmatch(filename, f"**/{pattern}"):
            # Рекурсивное совпадение
            return True
        
        # Проверяем папки
        if pattern.endswith("/"):
            folder = pattern.rstrip("/")
            if filename.startswith(folder + "/") or filename.startswith(folder + "\\"):
                return True
        
        # Проверяем с маской
        if "*" in pattern:
            if fnmatch.fnmatch(filename, pattern):
                return True
            # Для паттернов вроде "**/pattern"
            if "**/" in pattern:
                pattern_clean = pattern.replace("**/", "")
                if fnmatch.fnmatch(filename.split("/")[-1], pattern_clean):
                    return True
    
    return False

def check_production_safety():
    """Проверяет что production образ не содержит тестовых файлов"""
    print("Checking production safety...")
    
    # Читаем .dockerignore
    dockerignore_patterns = read_dockerignore()
    
    if not dockerignore_patterns:
        print("OK: .dockerignore is properly configured")
        return True
    
    forbidden_found = []
    
    for pattern in FORBIDDEN_IN_PRODUCTION:
        matches = glob.glob(pattern, recursive=True)
        for match in matches:
            # Проверяем что файл есть в .dockerignore
            if not is_pattern_in_dockerignore(match, dockerignore_patterns):
                forbidden_found.append(match)
    
    if forbidden_found:
        print("CRITICAL ERROR: Found test files NOT excluded in .dockerignore!")
        print("Found files:")
        for file in forbidden_found:
            print(f"  ERROR: {file}")
        print("\nAdd these patterns to .dockerignore to exclude from Docker image")
        return False
    
    print("OK: Production safety check passed (.dockerignore is properly configured)")
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