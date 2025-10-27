# CareBot Database Deployment

This directory contains the database dump and deployment tools for the CareBot project.

## Files

- `database_dump_YYYYMMDD_HHMMSS.sql` - Complete SQL dump of the database
- `deploy_database.py` - Python script to restore the database on another device
- `database` - Original SQLite database file (for reference)

## How to Deploy on Another Device

### Method 1: Using the Deployment Script (Recommended)

1. Copy both files to your target device:
   - `database_dump_YYYYMMDD_HHMMSS.sql`
   - `deploy_database.py`

2. Place them in your project's root directory (same level as the main bot files)

3. Run the deployment script:
   ```bash
   python deploy_database.py
   ```

4. The script will:
   - Create the `db/` directory if it doesn't exist
   - Backup any existing database
   - Restore the database from the dump file

### Method 2: Manual SQLite Restoration

If you prefer to restore manually:

1. Install SQLite3 command line tool
2. Create the database directory: `mkdir db`
3. Restore the database:
   ```bash
   sqlite3 db/database < database_dump_YYYYMMDD_HHMMSS.sql
   ```

### Method 3: Using Python sqlite3

```python
import sqlite3

# Create connection to new database
conn = sqlite3.connect('db/database')

# Read and execute the dump file
with open('database_dump_YYYYMMDD_HHMMSS.sql', 'r') as f:
    sql_script = f.read()

conn.executescript(sql_script)
conn.close()
```

## Database Structure

The database contains the following tables:
- `alliances` - Alliance information and resources
- `battle_attenders` - Battle participants
- `battles` - Battle records
- `edges` - Map connections between hexes
- `map` - Hex map data
- `map_story` - Hex history
- `mission_stack` - Mission queue
- `schedule` - Event scheduling
- `warmasters` - Player information

## Notes

- Make sure the target device has Python and SQLite support
- The dump includes both schema and data
- The deployment script will backup existing databases automatically
- Update the `DATABASE_PATH` in your `sqllite_helper.py` if your directory structure differs

## Troubleshooting

If you encounter issues:

1. Check that the target directory exists and is writable
2. Ensure SQLite3 is properly installed
3. Verify the dump file is complete and not corrupted
4. Check file permissions on the target system