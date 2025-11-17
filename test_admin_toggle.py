#!/usr/bin/env python3
"""
Test script to verify admin toggle functionality.
This tests the new toggle_user_admin function.
"""

import asyncio
import sys
import os

# Set test mode before any imports
os.environ['CAREBOT_TEST_MODE'] = 'true'

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Import config to initialize TEST_MODE, then import the appropriate helper
import config
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Test using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Test using REAL SQLite helper")


async def test_admin_toggle():
    """Test admin toggle functionality."""
    print("=" * 60)
    print("Testing Admin Toggle Functionality")
    print("=" * 60)
    
    # Test 1: Find users to test with
    print("\n1. Finding test users...")
    try:
        warmasters = await sqllite_helper.get_warmasters_with_nicknames()
        if len(warmasters) < 2:
            print("   ✗ Need at least 2 users to test properly")
            return
        
        # Find an admin and a non-admin
        admin_user = None
        non_admin_user = None
        
        for wm in warmasters:
            telegram_id, nickname, alliance = wm
            is_admin = await sqllite_helper.is_user_admin(telegram_id)
            if is_admin and not admin_user:
                admin_user = (telegram_id, nickname)
            elif not is_admin and not non_admin_user:
                non_admin_user = (telegram_id, nickname)
        
        if admin_user:
            print(f"   ✓ Found admin user: {admin_user[1]} (ID: {admin_user[0]})")
        if non_admin_user:
            print(f"   ✓ Found non-admin user: {non_admin_user[1]} (ID: {non_admin_user[0]})")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Test toggle_user_admin on non-admin (should promote to admin)
    if non_admin_user:
        print(f"\n2. Testing toggle_user_admin on non-admin user {non_admin_user[1]}...")
        try:
            # Check initial status
            initial_status = await sqllite_helper.is_user_admin(non_admin_user[0])
            print(f"   - Initial admin status: {initial_status}")
            
            # Toggle (should make admin)
            success, new_status, message = await sqllite_helper.toggle_user_admin(non_admin_user[0])
            print(f"   - Toggle result: success={success}, new_status={new_status}, message='{message}'")
            
            # Verify
            current_status = await sqllite_helper.is_user_admin(non_admin_user[0])
            print(f"   - Current admin status: {current_status}")
            
            if success and new_status and current_status:
                print(f"   ✓ Successfully promoted {non_admin_user[1]} to admin!")
            else:
                print(f"   ✗ Failed to promote user")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Test 3: Test toggle_user_admin on admin (should revoke admin)
    if non_admin_user:  # Using the same user we just promoted
        print(f"\n3. Testing toggle_user_admin on admin user {non_admin_user[1]}...")
        try:
            # Check initial status (should be admin now)
            initial_status = await sqllite_helper.is_user_admin(non_admin_user[0])
            print(f"   - Initial admin status: {initial_status}")
            
            # Toggle (should revoke admin)
            success, new_status, message = await sqllite_helper.toggle_user_admin(non_admin_user[0])
            print(f"   - Toggle result: success={success}, new_status={new_status}, message='{message}'")
            
            # Verify
            current_status = await sqllite_helper.is_user_admin(non_admin_user[0])
            print(f"   - Current admin status: {current_status}")
            
            if success and not new_status and not current_status:
                print(f"   ✓ Successfully revoked admin from {non_admin_user[1]}!")
            else:
                print(f"   ✗ Failed to revoke admin")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Test 4: Test protection for user with id=0 (using mock user with id=0)
    print("\n4. Testing id=0 protection...")
    try:
        if config.TEST_MODE:
            # In mock mode, we have a user with id=0: SuperAdmin
            user_id_0_telegram = '999999999'  # SuperAdmin from MOCK_WARMASTERS with id=0
            print(f"   - Testing with mock user (telegram_id={user_id_0_telegram})")
            
            # Make sure they're admin first
            await sqllite_helper.make_user_admin(user_id_0_telegram)
            is_admin = await sqllite_helper.is_user_admin(user_id_0_telegram)
            print(f"   - User is admin: {is_admin}")
            
            # Try to toggle (should be blocked for user with id=0)
            success, new_status, message = await sqllite_helper.toggle_user_admin(user_id_0_telegram)
            print(f"   - Toggle result: success={success}, new_status={new_status}, message='{message}'")
            
            if not success and "id=0" in message:
                print(f"   ✓ Protection working: Cannot remove admin from id=0")
            else:
                print(f"   ✗ Protection failed: {message}")
        else:
            # In real DB mode, try to find actual user with id=0
            import aiosqlite
            DATABASE_PATH = os.environ.get('DATABASE_PATH', 
                r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database")
            
            async with aiosqlite.connect(DATABASE_PATH) as db:
                async with db.execute('SELECT telegram_id FROM warmasters WHERE id = 0') as cursor:
                    result = await cursor.fetchone()
                    
                    if result:
                        user_id_0_telegram = result[0]
                        print(f"   - Found user with id=0: telegram_id={user_id_0_telegram}")
                        
                        # Make sure they're admin first
                        await sqllite_helper.make_user_admin(user_id_0_telegram)
                        
                        # Try to toggle (should be blocked)
                        success, new_status, message = await sqllite_helper.toggle_user_admin(user_id_0_telegram)
                        print(f"   - Toggle result: success={success}, new_status={new_status}, message='{message}'")
                        
                        if not success and "id=0" in message:
                            print(f"   ✓ Protection working: Cannot remove admin from id=0")
                        else:
                            print(f"   ✗ Protection failed or user is not admin")
                    else:
                        print("   - No user with id=0 exists (this is OK)")
                    
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nNote: Make sure DATABASE_PATH environment variable is set correctly")
    print("or the default path points to your database.\n")
    
    asyncio.run(test_admin_toggle())
