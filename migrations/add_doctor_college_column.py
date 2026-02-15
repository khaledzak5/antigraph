"""
Migration: Add doctor_college column to users table

This migration adds the `doctor_college` column to the users table to store
which college a doctor user belongs to. Each doctor can be associated with 
a specific college through this field.
"""

from sqlalchemy import text
from app.database import engine


def upgrade():
    """Add doctor_college column to users table"""
    with engine.connect() as conn:
        # Check if column already exists
        try:
            conn.execute(text('ALTER TABLE users ADD COLUMN doctor_college VARCHAR(255) NULL'))
            conn.commit()
            print("✓ Added doctor_college column to users table")
        except Exception as e:
            if "duplicate column name" in str(e) or "already exists" in str(e):
                print("⚠ doctor_college column already exists, skipping...")
            else:
                raise


def downgrade():
    """Remove doctor_college column from users table (if needed)"""
    with engine.connect() as conn:
        try:
            conn.execute(text('ALTER TABLE users DROP COLUMN doctor_college'))
            conn.commit()
            print("✓ Removed doctor_college column from users table")
        except Exception as e:
            print(f"Could not drop column: {e}")


if __name__ == "__main__":
    print("Running migration: Add doctor_college column...")
    upgrade()
