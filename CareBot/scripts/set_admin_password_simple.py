#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple utility to set admin web password
Does NOT import full CareBot package to avoid server_app dependencies
"""

import asyncio
import hashlib
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Direct imports avoiding __init__.py
import CareBot.sqllite_helper as sqllite_helper


async def set_password_for_admin(warmaster_id: int, password: str):
    """Set web password for admin user"""
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(str(warmaster_id))
    if not is_admin:
        print(f"❌ Error: warmaster_id {warmaster_id} is not an admin (is_admin=0)")
        print("   Use Telegram bot command /make_admin first")
        return False
    
    # Hash password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Set password
    success = await sqllite_helper.set_admin_web_password(warmaster_id, password_hash)
    
    if success:
        print(f"✅ Web password set for warmaster_id: {warmaster_id}")
        print(f"   You can now login at: http://[server-ip]:5555/login")
        return True
    else:
        print(f"❌ Failed to set password")
        return False


async def show_admins():
    """Show all admins and their web access status"""
    print("\n═══════════════════════════════════════════════")
    print("  CURRENT ADMINISTRATORS")
    print("═══════════════════════════════════════════════\n")
    
    admins = await sqllite_helper.get_all_admins_with_web_access()
    
    if not admins:
        print("❌ No administrators found with is_admin=1")
        print("   Use Telegram bot to assign admin rights first")
        return []
    
    print(f"{'ID':<6} {'Nickname':<20} {'Alliance':<15} {'Web Password':<15}")
    print("─" * 60)
    
    for admin in admins:
        warmaster_id, nickname, alliance, is_admin, has_password = admin
        password_status = "✅ Set" if has_password else "⚠️  Not set"
        alliance_name = alliance or "-"
        nickname_display = nickname or f"User {warmaster_id}"
        
        print(f"{warmaster_id:<6} {nickname_display:<20} {alliance_name:<15} {password_status:<15}")
    
    print()
    return admins


async def main():
    """Main entry point"""
    if len(sys.argv) == 3:
        # Direct mode: set_admin_password_simple.py <warmaster_id> <password>
        warmaster_id = int(sys.argv[1])
        password = sys.argv[2]
        await set_password_for_admin(warmaster_id, password)
    elif len(sys.argv) == 2 and sys.argv[1] == "list":
        # List mode: show all admins
        await show_admins()
    else:
        # Interactive mode
        print("\n╔════════════════════════════════════════════════╗")
        print("║  ADMIN WEB PASSWORD MANAGEMENT                ║")
        print("╚════════════════════════════════════════════════╝")
        
        admins = await show_admins()
        
        if not admins:
            return
        
        print("\n📝 SET WEB PASSWORD")
        print("─" * 60)
        
        try:
            warmaster_id = input("\nEnter admin ID: ").strip()
            if not warmaster_id:
                print("Cancelled")
                return
            
            warmaster_id = int(warmaster_id)
            
            # Check if this ID is in admin list
            admin_ids = [a[0] for a in admins]
            if warmaster_id not in admin_ids:
                print(f"❌ ID {warmaster_id} not found among administrators")
                return
            
            password = input("Enter new password: ").strip()
            if not password:
                print("Cancelled")
                return
            
            password_confirm = input("Confirm password: ").strip()
            if password != password_confirm:
                print("❌ Passwords do not match")
                return
            
            if len(password) < 4:
                print("❌ Password must be at least 4 characters")
                return
            
            # Set password
            await set_password_for_admin(warmaster_id, password)
                
        except ValueError:
            print("❌ Invalid ID format")
        except KeyboardInterrupt:
            print("\n\nCancelled")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
