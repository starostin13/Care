#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility script to manage admin web passwords
Sets web passwords for users who already have is_admin=1 in warmasters table
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from CareBot import sqllite_helper
from CareBot import auth


async def show_admins():
    """Show all admins and their web access status"""
    print("\n═══════════════════════════════════════════════")
    print("  ТЕКУЩИЕ АДМИНИСТРАТОРЫ")
    print("═══════════════════════════════════════════════\n")
    
    admins = await sqllite_helper.get_all_admins_with_web_access()
    
    if not admins:
        print("❌ Нет администраторов с is_admin=1")
        print("   Используйте Telegram бота для назначения админов")
        return []
    
    print(f"{'ID':<6} {'Nickname':<20} {'Alliance':<15} {'Web Password':<15}")
    print("─" * 60)
    
    for admin in admins:
        warmaster_id, nickname, alliance, is_admin, has_password = admin
        password_status = "✅ Установлен" if has_password else "⚠️  Не установлен"
        alliance_name = alliance or "-"
        nickname_display = nickname or f"User {warmaster_id}"
        
        print(f"{warmaster_id:<6} {nickname_display:<20} {alliance_name:<15} {password_status:<15}")
    
    print()
    return admins


async def set_password_interactive():
    """Interactive password setup"""
    admins = await show_admins()
    
    if not admins:
        return
    
    print("\n📝 УСТАНОВКА ВЕБ-ПАРОЛЯ")
    print("─" * 60)
    
    try:
        warmaster_id = input("\nВведите ID администратора: ").strip()
        if not warmaster_id:
            print("Отменено")
            return
        
        warmaster_id = int(warmaster_id)
        
        # Check if this ID is in admin list
        admin_ids = [a[0] for a in admins]
        if warmaster_id not in admin_ids:
            print(f"❌ ID {warmaster_id} не найден среди администраторов")
            return
        
        password = input("Введите новый пароль: ").strip()
        if not password:
            print("Отменено")
            return
        
        password_confirm = input("Подтвердите пароль: ").strip()
        if password != password_confirm:
            print("❌ Пароли не совпадают")
            return
        
        if len(password) < 4:
            print("❌ Пароль должен содержать минимум 4 символа")
            return
        
        # Set password
        success = auth.set_admin_password(warmaster_id, password)
        
        if success:
            print(f"\n✅ Веб-пароль установлен для warmaster_id: {warmaster_id}")
            print(f"   Теперь можно войти через https://[server-ip]:5000/login")
        else:
            print(f"\n❌ Ошибка установки пароля")
            
    except ValueError:
        print("❌ Неверный формат ID")
    except KeyboardInterrupt:
        print("\n\nОтменено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def main():
    """Main entry point"""
    print("\n╔════════════════════════════════════════════════╗")
    print("║  УПРАВЛЕНИЕ ВЕБ-ДОСТУПОМ АДМИНИСТРАТОРОВ     ║")
    print("╚════════════════════════════════════════════════╝")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            await show_admins()
            return
        elif sys.argv[1] == "set" and len(sys.argv) == 4:
            warmaster_id = int(sys.argv[2])
            password = sys.argv[3]
            success = auth.set_admin_password(warmaster_id, password)
            if not success:
                print(f"❌ Не удалось установить пароль. Убедитесь что warmaster_id {warmaster_id} имеет is_admin=1")
                sys.exit(1)
            return
    
    await set_password_interactive()


if __name__ == "__main__":
    asyncio.run(main())
