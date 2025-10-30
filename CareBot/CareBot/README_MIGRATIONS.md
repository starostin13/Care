# CareBot Database Migration System

This project now uses **yoyo-migrations** for database schema management. This ensures that database changes are applied consistently across different environments.

## Files

### Migration System
- `migrate_db.py` - Main migration runner script
- `migrations/` - Directory containing migration files
- `yoyo.ini` - yoyo-migrations configuration file

### Migration Files
- `migrations/001_add_language_and_notifications.py` - Adds language and notifications_enabled columns to warmasters table

## Usage

### Check Migration Status
```bash
python migrate_db.py --status
```

### Apply Pending Migrations
```bash
python migrate_db.py
```

### Automatic Migration on Bot Start
The bot automatically checks for and applies pending migrations when it starts up.

## Creating New Migrations

1. Create a new file in the `migrations/` directory with a descriptive name:
   ```
   migrations/002_add_new_feature.py
   ```

2. Use the following template:
   ```python
   """
   Migration 002: Description of what this migration does
   """
   
   from yoyo import step
   
   def upgrade_function(conn):
       """Apply the migration."""
       cursor = conn.cursor()
       cursor.execute("ALTER TABLE table_name ADD COLUMN new_column TEXT")
   
   def downgrade_function(conn):
       """Rollback the migration (optional)."""
       # SQLite doesn't support DROP COLUMN in older versions
       pass
   
   steps = [
       step(upgrade_function, downgrade_function)
   ]
   ```

3. Test the migration:
   ```bash
   python migrate_db.py --status  # Check that it's detected
   python migrate_db.py           # Apply it
   ```

## Benefits

✅ **Version Control**: Database schema changes are tracked in code
✅ **Consistent Deployments**: Same schema across all environments  
✅ **Automatic**: Migrations run automatically when the bot starts
✅ **Safe**: Checks for existing columns before adding them
✅ **Rollback Support**: Can rollback migrations if needed (where supported)

## Migration History

| Migration | Description | Applied |
|-----------|-------------|---------|
| 001 | Add language and notifications_enabled columns | ✅ |

## Troubleshooting

### Migration Failed
If a migration fails:
1. Check the error message in the console
2. Verify the migration syntax
3. Check database permissions
4. Use `python migrate_db.py --status` to see current state

### Reset Migrations (Development Only)
⚠️ **WARNING**: This will lose migration history
```bash
# Delete migration tracking table (use with caution)
sqlite3 db/database "DROP TABLE IF EXISTS _yoyo_migration"
```

### Manual Migration Fix
If you need to manually fix a migration state:
```python
# Connect to database and check yoyo tables
import sqlite3
conn = sqlite3.connect('db/database')
cursor = conn.cursor()
cursor.execute("SELECT * FROM _yoyo_migration")
print(cursor.fetchall())
```