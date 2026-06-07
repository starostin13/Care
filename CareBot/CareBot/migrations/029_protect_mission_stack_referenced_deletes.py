"""
Migration 029: Protect mission_stack records referenced by battles

Prevents deleting missions that are referenced by historical battles.
This protects battle history from accidental mission cleanup operations.
"""

from yoyo import step


def add_mission_delete_guard(conn):
    cursor = conn.cursor()

    cursor.execute("DROP TRIGGER IF EXISTS prevent_deleting_referenced_mission")

    cursor.execute("""
        CREATE TRIGGER prevent_deleting_referenced_mission
        BEFORE DELETE ON mission_stack
        FOR EACH ROW
        WHEN EXISTS (
            SELECT 1
            FROM battles
            WHERE mission_id = OLD.id
        )
        BEGIN
            SELECT RAISE(
                ABORT,
                'Cannot delete mission referenced by battles; keep history integrity'
            );
        END;
    """)

    conn.commit()


steps = [step(add_mission_delete_guard)]
