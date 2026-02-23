"""
Migration 013: Update alliance deletion success message to include territories
This migration updates the text for alliance deletion to include both players and territories redistributed.
"""

import sys
import os

# Add parent directory to path to import sqllite_helper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import sqllite_helper


async def migrate():
    """Update alliance deletion success text."""
    
    # Updated texts for alliance deletion including territories
    texts_to_add = [
        # Russian
        ("admin_alliance_deleted_success", "ru", 
         "✅ Альянс удален.\nПерераспределено игроков: {players_redistributed}\nПерераспределено территорий: {territories_redistributed}"),
        
        # English
        ("admin_alliance_deleted_success", "en", 
         "✅ Alliance deleted.\nPlayers redistributed: {players_redistributed}\nTerritories redistributed: {territories_redistributed}"),
    ]
    
    print("Migration 013: Updating alliance deletion texts...")
    
    for key, language, value in texts_to_add:
        await sqllite_helper.add_or_update_text(key, language, value)
        print(f"  ✓ Updated text: {key} ({language})")
    
    print("Migration 013 completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
