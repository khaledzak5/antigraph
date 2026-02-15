"""
Complete medicine cleanup and college isolation setup
This script:
1. Deletes all existing medicines from all tables
2. Adds college_id column where missing
3. Creates indexes for performance
"""
import sqlite3
from pathlib import Path
from datetime import datetime

def cleanup_and_setup():
    db_path = Path(__file__).parent / "app.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("="*70)
    print("MEDICINE DATA CLEANUP AND COLLEGE ISOLATION SETUP")
    print("="*70)
    
    try:
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        print("\n✓ Foreign keys enabled")
        
        # STEP 1: Delete all existing medicines
        print("\n" + "-"*70)
        print("STEP 1: DELETE ALL EXISTING MEDICINES")
        print("-"*70)
        
        tables_to_clear = [
            ('drug_stock_movements', 'Deleting from drug_stock_movements...'),
            ('drug_transactions', 'Deleting from drug_transactions...'),
            ('pharmacy_stock', 'Deleting from pharmacy_stock...'),
            ('warehouse_stock', 'Deleting from warehouse_stock...'),
            ('drug_balance', 'Deleting from drug_balance...'),
            ('drugs', 'Deleting from drugs...'),
        ]
        
        for table, message in tables_to_clear:
            print(message)
            cursor.execute(f"DELETE FROM {table}")
            count = cursor.rowcount
            print(f"  ✓ Deleted {count} records from {table}")
        
        conn.commit()
        print("\n✓ All medicine records deleted successfully")
        
        # STEP 2: Verify and add college_id columns if missing
        print("\n" + "-"*70)
        print("STEP 2: VERIFY/ADD college_id COLUMNS")
        print("-"*70)
        
        tables_to_check = [
            ('drugs', 'Drug master table'),
            ('pharmacy_stock', 'Pharmacy stock table'),
            ('warehouse_stock', 'Warehouse stock table'),
            ('drug_transactions', 'Drug transactions table'),
            ('drug_stock_movements', 'Stock movements table'),
            ('drug_balance', 'Drug balance table'),
        ]
        
        for table, description in tables_to_check:
            print(f"\nChecking {table} ({description})...")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'college_id' not in columns:
                print(f"  ⚠️  Adding college_id column...")
                try:
                    if table == 'drugs':
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ADD COLUMN college_id VARCHAR(255) DEFAULT NULL
                        """)
                    else:
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ADD COLUMN college_id VARCHAR(255) DEFAULT NULL
                        """)
                    print(f"  ✓ Added college_id column to {table}")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        print(f"  ✓ college_id column already exists")
                    else:
                        raise
            else:
                print(f"  ✓ college_id column already exists")
        
        conn.commit()
        print("\n✓ All college_id columns verified/added")
        
        # STEP 3: Create indexes for college_id
        print("\n" + "-"*70)
        print("STEP 3: CREATE INDEXES FOR PERFORMANCE")
        print("-"*70)
        
        indexes = [
            ('drugs', 'idx_drugs_college_id', 'college_id'),
            ('pharmacy_stock', 'idx_pharmacy_stock_college_id', 'college_id'),
            ('warehouse_stock', 'idx_warehouse_stock_college_id', 'college_id'),
            ('drug_transactions', 'idx_drug_tx_college_id', 'college_id'),
            ('drug_stock_movements', 'idx_drug_mvmt_college_id', 'college_id'),
            ('drug_balance', 'idx_drug_balance_college_id', 'college_id'),
        ]
        
        for table, index_name, column in indexes:
            print(f"\nCreating index on {table}.{column}...")
            try:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {table}({column})
                """)
                print(f"  ✓ Index {index_name} created")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  ✓ Index already exists")
                else:
                    print(f"  ⚠️  Error: {e}")
        
        conn.commit()
        print("\n✓ All indexes created")
        
        # STEP 4: Verify cleanup
        print("\n" + "-"*70)
        print("STEP 4: VERIFICATION")
        print("-"*70)
        
        for table, _ in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} records")
        
        print("\n✓ Verification complete")
        
        print("\n" + "="*70)
        print("✅ CLEANUP AND SETUP COMPLETE")
        print("="*70)
        print("\nDatabase state:")
        print("  ✓ All existing medicines deleted")
        print("  ✓ college_id columns added to all medicine tables")
        print("  ✓ Indexes created for performance")
        print("  ✓ Ready for college-isolated data")
        print("\nNext steps:")
        print("  1. Update all medicine endpoints to filter by college_id")
        print("  2. Auto-assign college_id on medicine creation")
        print("  3. Add access validation for college isolation")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = cleanup_and_setup()
    exit(0 if success else 1)
