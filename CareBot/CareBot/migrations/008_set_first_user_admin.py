"""
Set first user in warmasters as admin if no admin exists
"""

from yoyo import step

__depends__ = {'007_add_admin_alliance_texts'}

steps = [
    step("""
        UPDATE warmasters 
        SET is_admin = 1 
        WHERE id = (SELECT MIN(id) FROM warmasters)
        AND NOT EXISTS (SELECT 1 FROM warmasters WHERE is_admin = 1)
    """)
]
