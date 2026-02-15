"""
Migration Script: Add college_id columns to first_aid tables

This migration adds college_id columns to:
- first_aid_boxes
- first_aid_box_items

Without losing existing data. Existing records get NULL for college_id.
New records from doctors will have college_id auto-populated.
"""

from sqlalchemy import text, inspect
from app.database import engine


def add_column_if_not_exists(table_name: str, column_name: str, column_def: str) -> bool:
    """
    Add a column to a table if it doesn't already exist.
    
    Args:
        table_name: Name of the table
        column_name: Name of the column to add
        column_def: SQL definition for the column
        
    Returns:
        True if column was added or already exists, False if error
    """
    with engine.connect() as conn:
        # Check if column exists
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name in columns:
            print(f"✓ Column {table_name}.{column_name} already exists")
            return True
        
        try:
            # Add the column
            alter_sql = f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}'
            conn.execute(text(alter_sql))
            conn.commit()
            print(f"✓ Added column {table_name}.{column_name}")
            return True
        except Exception as e:
            print(f"✗ Error adding {table_name}.{column_name}: {e}")
            return False


def add_index_if_not_exists(table_name: str, index_name: str, column_name: str) -> bool:
    """
    Add an index to a table if it doesn't already exist.
    
    Args:
        table_name: Name of the table
        index_name: Name of the index
        column_name: Name of the column to index
        
    Returns:
        True if index was added or already exists, False if error
    """
    with engine.connect() as conn:
        try:
            # Try to create the index (SQLite will ignore if it exists)
            create_index_sql = f'CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})'
            conn.execute(text(create_index_sql))
            conn.commit()
            print(f"✓ Index {index_name} created or already exists")
            return True
        except Exception as e:
            print(f"⚠ Index {index_name}: {e}")
            return False


def run_migration():
    """Run the migration"""
    print("\n" + "="*60)
    print("MIGRATION: Add college_id to first_aid tables")
    print("="*60 + "\n")
    
    # Add college_id to first_aid_boxes
    print("1. Adding college_id to first_aid_boxes table...")
    add_column_if_not_exists(
        "first_aid_boxes",
        "college_id",
        "VARCHAR(255) DEFAULT NULL"
    )
    add_index_if_not_exists(
        "first_aid_boxes",
        "idx_first_aid_box_college",
        "college_id"
    )
    
    # Add college_id to first_aid_box_items
    print("\n2. Adding college_id to first_aid_box_items table...")
    add_column_if_not_exists(
        "first_aid_box_items",
        "college_id",
        "VARCHAR(255) DEFAULT NULL"
    )
    add_index_if_not_exists(
        "first_aid_box_items",
        "idx_first_aid_item_college",
        "college_id"
    )
    
    print("\n" + "="*60)
    print("Migration completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_migration()
