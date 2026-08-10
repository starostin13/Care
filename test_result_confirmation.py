"""
Test script to verify that the result confirmation feature is working correctly.
This tests the pending results flow and confirmation handlers.
"""

import sys
import os
import asyncio

# Add the project directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CareBot', 'CareBot'))

# Set test mode
os.environ['CAREBOT_TEST_MODE'] = 'true'

async def test_pending_result_functions_exist():
    """Test that pending result functions exist in sqllite_helper."""
    try:
        import sqllite_helper
        
        required_functions = [
            'create_pending_result',
            'get_pending_result_by_battle_id',
            'delete_pending_result',
            'get_all_pending_missions',
            'update_mission_status',
            'get_battle_participants',
            'get_pending_missions_count',
            'get_battle_id_by_mission_id'
        ]
        
        all_exist = True
        for func_name in required_functions:
            if hasattr(sqllite_helper, func_name):
                print(f"✅ {func_name} exists in sqllite_helper")
            else:
                print(f"❌ {func_name} NOT found in sqllite_helper")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ Error checking pending result functions: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_pending_result_model_exists():
    """Test that PendingResult model exists."""
    try:
        from models import PendingResult
        
        # Check that it has the expected fields
        expected_fields = ['id', 'battle_id', 'submitter_id', 'fstplayer_score', 'sndplayer_score', 'created_at']
        actual_fields = list(PendingResult.__dataclass_fields__.keys())
        
        if set(expected_fields) == set(actual_fields):
            print(f"✅ PendingResult model has all expected fields: {actual_fields}")
            return True
        else:
            missing = set(expected_fields) - set(actual_fields)
            extra = set(actual_fields) - set(expected_fields)
            if missing:
                print(f"❌ PendingResult missing fields: {missing}")
            if extra:
                print(f"⚠️  PendingResult has extra fields: {extra}")
            return False
    except Exception as e:
        print(f"❌ Error checking PendingResult model: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mission_model_has_status():
    """Test that Mission model has status field."""
    try:
        from models import Mission
        
        if 'status' in Mission.__dataclass_fields__:
            print("✅ Mission model has status field")
            return True
        else:
            print("❌ Mission model does NOT have status field")
            return False
    except Exception as e:
        print(f"❌ Error checking Mission model: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_confirmation_handlers_exist():
    """Test that confirmation handlers exist in handlers module."""
    try:
        import handlers
        
        required_handlers = [
            'confirm_result',
            'cancel_result',
            'admin_pending_confirmations',
            'admin_confirm_mission',
            'admin_do_confirm_mission',
            'admin_do_reject_mission'
        ]
        
        all_exist = True
        for handler_name in required_handlers:
            if hasattr(handlers, handler_name):
                print(f"✅ {handler_name} handler exists")
            else:
                print(f"❌ {handler_name} handler NOT found")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ Error checking confirmation handlers: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_migration_file_exists():
    """Test that the migration file exists."""
    try:
        migration_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'CareBot', 'CareBot', 'migrations', '020_add_status_and_pending_results.py'
        )

        if os.path.exists(migration_path):
            print(f"✅ Migration file exists: {migration_path}")

            # Check migration content
            with open(migration_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'ALTER TABLE mission_stack ADD COLUMN status' in content:
                    print("✅ Migration includes status column addition")
                else:
                    print("❌ Migration missing status column addition")
                    return False

                if 'CREATE TABLE pending_results' in content:
                    print("✅ Migration includes pending_results table creation")
                else:
                    print("❌ Migration missing pending_results table creation")
                    return False

            return True
        else:
            print(f"❌ Migration file does NOT exist: {migration_path}")
            return False
    except Exception as e:
        print(f"❌ Error checking migration file: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_unified_flow_behavior():
    """Behavior test for shared pending/confirm/reject mission flow in test mode."""
    try:
        import mission_helper
        import mock_sqlite_helper as sqllite_helper
        import mock_sqlite_helper

        player_1 = '325313837'
        player_2 = '123456789'

        # --- Branch 1: submit -> confirm ---
        mission_id_confirm = await sqllite_helper.save_mission({
            'deploy': 'Behavior Deploy Confirm',
            'rules': 'killteam',
            'cell': 3,
            'mission_description': 'Behavior test: confirm branch',
            'status': 0,
        })

        battle_id_confirm = int((await mission_helper.start_battle(
            mission_id_confirm,
            player_1,
            player_2,
            forced_battle_id=910001,
        )))

        await sqllite_helper.update_mission_status(mission_id_confirm, 1)

        submit_result = await mission_helper.submit_pending_battle_result(
            battle_id=battle_id_confirm,
            submitter_id=player_1,
            fstplayer_score=17,
            sndplayer_score=10,
        )

        if submit_result['mission_id'] != mission_id_confirm:
            print("❌ submit_pending_battle_result returned unexpected mission_id")
            return False

        mission_after_submit = await sqllite_helper.get_mission_details(mission_id_confirm)
        if int(mission_after_submit.status) != 2:
            print("❌ Mission status did not transition to pending (2) after submit")
            return False

        # Submitter must not be allowed to confirm own result.
        try:
            await mission_helper.confirm_pending_battle_result(
                battle_id=battle_id_confirm,
                confirmer_id=player_1,
                require_participant=True,
                allow_submitter_confirm=False,
            )
            print("❌ Submitter unexpectedly confirmed own result")
            return False
        except PermissionError:
            print("✅ Submitter cannot confirm own result")

        confirm_result = await mission_helper.confirm_pending_battle_result(
            battle_id=battle_id_confirm,
            confirmer_id=player_2,
            require_participant=True,
            allow_submitter_confirm=False,
        )

        if confirm_result['mission_id'] != mission_id_confirm:
            print("❌ confirm_pending_battle_result returned unexpected mission_id")
            return False

        mission_after_confirm = await sqllite_helper.get_mission_details(mission_id_confirm)
        pending_after_confirm = await sqllite_helper.get_pending_result_by_battle_id(battle_id_confirm)
        battle_after_confirm = mock_sqlite_helper.MOCK_BATTLES.get(battle_id_confirm, {})

        if int(mission_after_confirm.status) != 3:
            print("❌ Mission status did not transition to confirmed (3) after confirm")
            return False
        if pending_after_confirm is not None:
            print("❌ Pending result was not deleted after confirm")
            return False
        if int(battle_after_confirm.get('fstplayer', -1)) != 17 or int(battle_after_confirm.get('sndplayer', -1)) != 10:
            print("❌ Final battle scores were not persisted on confirm")
            return False

        # --- Branch 2: submit -> reject ---
        mission_id_reject = await sqllite_helper.save_mission({
            'deploy': 'Behavior Deploy Reject',
            'rules': 'killteam',
            'cell': 4,
            'mission_description': 'Behavior test: reject branch',
            'status': 0,
        })

        battle_id_reject = int((await mission_helper.start_battle(
            mission_id_reject,
            player_1,
            player_2,
            forced_battle_id=910002,
        )))

        await sqllite_helper.update_mission_status(mission_id_reject, 1)

        await mission_helper.submit_pending_battle_result(
            battle_id=battle_id_reject,
            submitter_id=player_1,
            fstplayer_score=12,
            sndplayer_score=14,
        )

        mission_after_submit_reject = await sqllite_helper.get_mission_details(mission_id_reject)
        if int(mission_after_submit_reject.status) != 2:
            print("❌ Mission status did not transition to pending (2) in reject branch")
            return False

        # Submitter must not be allowed to reject own result.
        try:
            await mission_helper.reject_pending_battle_result(
                battle_id=battle_id_reject,
                rejector_id=player_1,
                require_participant=True,
                allow_submitter_reject=False,
            )
            print("❌ Submitter unexpectedly rejected own result")
            return False
        except PermissionError:
            print("✅ Submitter cannot reject own result")

        reject_result = await mission_helper.reject_pending_battle_result(
            battle_id=battle_id_reject,
            rejector_id=player_2,
            require_participant=True,
            allow_submitter_reject=False,
        )

        if reject_result['mission_id'] != mission_id_reject:
            print("❌ reject_pending_battle_result returned unexpected mission_id")
            return False

        mission_after_reject = await sqllite_helper.get_mission_details(mission_id_reject)
        pending_after_reject = await sqllite_helper.get_pending_result_by_battle_id(battle_id_reject)

        if int(mission_after_reject.status) != 1:
            print("❌ Mission status did not roll back to active (1) after reject")
            return False
        if pending_after_reject is not None:
            print("❌ Pending result was not deleted after reject")
            return False

        print("✅ Unified flow behavior validated (submit/confirm/reject)")
        return True
    except Exception as e:
        print(f"❌ Error in unified flow behavior test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("TESTING RESULT CONFIRMATION FEATURE")
    print("=" * 60)
    print()
    
    tests = [
        ("Migration file exists", test_migration_file_exists),
        ("Mission model has status field", test_mission_model_has_status),
        ("PendingResult model exists", test_pending_result_model_exists),
        ("Pending result functions exist", test_pending_result_functions_exist),
        ("Confirmation handlers exist", test_confirmation_handlers_exist),
        ("Unified flow behavior", test_unified_flow_behavior),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
