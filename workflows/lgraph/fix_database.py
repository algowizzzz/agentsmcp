"""
Quick Database Fix - Add Missing Columns to Plans Table
Run this script once to update your database schema
"""

import sqlite3
import os


def find_database():
    """Find the database file"""
    possible_paths = [
        'abhikarta.db',
        'db/abhikarta.db',
        './abhikarta.db',
        '../abhikarta.db',
        'data/abhikarta.db',
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # Ask user for path
    print("Could not find database automatically.")
    db_path = input("Enter the full path to your database file: ")
    return db_path


def migrate_database(db_path):
    """Add missing columns to the plans table"""
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(plans)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    print(f"\nExisting columns: {', '.join(existing_columns)}")

    # Define columns to add
    columns_to_add = [
        ('session_id', 'TEXT'),
        ('options_json', 'TEXT'),
        ('autonomous', 'INTEGER DEFAULT 0')
    ]

    print("\nAdding missing columns:")
    for column_name, column_type in columns_to_add:
        if column_name not in existing_columns:
            try:
                sql = f"ALTER TABLE plans ADD COLUMN {column_name} {column_type}"
                print(f"  Adding {column_name}...", end=' ')
                cursor.execute(sql)
                conn.commit()
                print("✓ Success")
            except Exception as e:
                print(f"✗ Error: {e}")
        else:
            print(f"  {column_name} - Already exists ✓")

    # Verify final structure
    cursor.execute("PRAGMA table_info(plans)")
    final_columns = cursor.fetchall()

    print("\nFinal table structure:")
    for col in final_columns:
        print(f"  {col[1]:20s} {col[2]:20s}")

    conn.close()
    print("\n✓ Migration completed successfully!")


if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration Tool")
    print("=" * 60)

    try:
        db_path = find_database()
        if not os.path.exists(db_path):
            print(f"Error: Database file not found at {db_path}")
            print("\nPlease ensure the database file exists and try again.")
            exit(1)

        migrate_database(db_path)

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nIf the error persists, please run these SQL commands manually:")
        print("  ALTER TABLE plans ADD COLUMN session_id TEXT;")
        print("  ALTER TABLE plans ADD COLUMN options_json TEXT;")
        print("  ALTER TABLE plans ADD COLUMN autonomous INTEGER DEFAULT 0;")
        exit(1)