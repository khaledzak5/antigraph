"""
Identify all medicine-related tables in the database
"""
import sqlite3
from pathlib import Path

def get_all_tables():
    db_path = Path(__file__).parent / "app.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("="*60)
    print("ALL TABLES IN DATABASE")
    print("="*60)
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n" + "="*60)
    print("MEDICINE-RELATED TABLES")
    print("="*60)
    
    medicine_tables = [t[0] for t in tables if any(keyword in t[0].lower() for keyword in ['medicine', 'drug', 'pharmacy', 'inventory', 'supply', 'stock'])]
    
    if medicine_tables:
        for table in medicine_tables:
            print(f"\n📋 Table: {table}")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                col_id, col_name, col_type, notnull, default_val, pk = col
                print(f"   - {col_name} ({col_type})")
    else:
        print("  ❌ No medicine-related tables found")
    
    conn.close()

if __name__ == "__main__":
    get_all_tables()
