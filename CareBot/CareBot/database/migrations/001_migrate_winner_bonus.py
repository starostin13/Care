#!/usr/bin/env python3
"""
Migration script to add winner_bonus column to mission_stack table
and update existing records.
"""

import aiosqlite
import asyncio
import os

# Get the database path relative to this script
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'game_database.db')

async def migrate_database():
    """Add winner_bonus column and migrate existing data."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check if column already exists
        cursor = await db.execute("PRAGMA table_info(mission_stack)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'winner_bonus' not in column_names:
            print("Adding winner_bonus column...")
            await db.execute("ALTER TABLE mission_stack ADD COLUMN winner_bonus TEXT")
            await db.commit()
            print("Column added successfully!")
        else:
            print("winner_bonus column already exists.")
        
        # Update existing wh40k missions to have default winner bonus
        print("Updating existing wh40k missions...")
        default_wh40k_bonus = "Выбрать один юнит участвующий в битве. Этот юнит получает 3xp вместо 1xp за участие в битве."
        await db.execute("""
            UPDATE mission_stack 
            SET winner_bonus = ?
            WHERE rules = 'wh40k' AND winner_bonus IS NULL
        """, (default_wh40k_bonus,))
        
        rows_affected = db.total_changes
        await db.commit()
        print(f"Updated {rows_affected} wh40k missions with default winner bonus.")
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_database())