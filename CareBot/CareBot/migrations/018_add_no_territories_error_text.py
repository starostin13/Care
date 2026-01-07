"""
Migration 018: Add error messages for alliance territory validation
"""

import sys
import os

# Add parent directory to path to import sqllite_helper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import sqllite_helper


async def migrate():
    """Add error messages for when alliance has no territories."""
    
    texts = [
        # Error message when alliance has no territories
        ("error_no_territories", "ru", "⚠️ Ваш альянс не контролирует территории на карте.\nДля участия в играх альянс должен владеть хотя бы одной территорией."),
        ("error_no_territories", "en", "⚠️ Your alliance does not control any territories on the map.\nTo participate in games, the alliance must control at least one territory."),
        
        # Error message when user has no alliance
        ("error_no_alliance", "ru", "⚠️ Вы не состоите в альянсе.\nДля участия в играх необходимо быть участником альянса."),
        ("error_no_alliance", "en", "⚠️ You are not a member of any alliance.\nYou must be a member of an alliance to participate in games."),
    ]
    
    print("Migration 018: Adding alliance territory validation texts...")
    
    for key, language, value in texts:
        await sqllite_helper.add_or_update_text(key, language, value)
        print(f"  ✓ Added text: {key} ({language})")
    
    print("Migration 018 completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
