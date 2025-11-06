# Database Migrations

This directory contains Yoyo database migration scripts for the Care bot.

## Prerequisites

Install yoyo-migrations:
```bash
pip install yoyo-migrations
```

## Usage

### Apply all pending migrations
```bash
cd CareBot/CareBot
yoyo apply
```

### Rollback the last migration
```bash
cd CareBot/CareBot
yoyo rollback
```

### Create a new migration
```bash
cd CareBot/CareBot
yoyo new -m "description of migration"
```

## Migration Files

Migrations are SQL files with a timestamp prefix and follow the format:
- `YYYYMMDD_NN_description.sql`

Each migration should:
1. Start with a comment describing what it does
2. Include a `-- depends:` line listing any migration dependencies
3. Contain SQL statements to apply the migration

## Configuration

The database connection and migration settings are configured in `yoyo.ini`.
Make sure to update the database path if your database is in a different location.
