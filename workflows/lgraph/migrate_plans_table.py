"""
Database Migration Script for Plans Table
Adds session_id, options_json, and autonomous columns to existing plans table

© 2025-2030 Ashutosh Sinha, ajsinha@gmail.com, https://www.github.com/ajsinha/abhikarta
"""

import sys
from db.database import get_db


def migrate_plans_table():
    """Add missing columns to existing plans table"""
    db = get_db()

    migrations = [
        {
            'column': 'session_id',
            'sql': 'ALTER TABLE plans ADD COLUMN session_id TEXT',
            'description': 'Adding session_id column'
        },
        {
            'column': 'options_json',
            'sql': 'ALTER TABLE plans ADD COLUMN options_json TEXT',
            'description': 'Adding options_json column'
        },
        {
            'column': 'autonomous',
            'sql': 'ALTER TABLE plans ADD COLUMN autonomous INTEGER DEFAULT 0',
            'description': 'Adding autonomous column'
        }
    ]

    print("Starting database migration for plans table...")

    for migration in migrations:
        try:
            print(f"  {migration['description']}...", end=' ')
            db.execute(migration['sql'])
            print("✓ Success")
        except Exception as e:
            if 'duplicate column name' in str(e).lower():
                print("⊘ Already exists")
            else:
                print(f"✗ Error: {e}")

    print("\nMigration complete!")

    # Verify the table structure
    print("\nVerifying table structure...")
    try:
        cursor = db.execute("PRAGMA table_info(plans)")
        columns = cursor.fetchall()
        print("\nCurrent plans table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    except Exception as e:
        print(f"Error verifying table: {e}")


if __name__ == '__main__':
    try:
        migrate_plans_table()
    except Exception as e:
        print(f"\nMigration failed: {e}")
        sys.exit(1)