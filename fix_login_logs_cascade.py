"""
Fix the NOT NULL constraint error on login_logs.user_id
This script recreates the login_logs table with proper CASCADE constraint
"""
import sqlite3
from pathlib import Path

def fix_login_logs_cascade():
    db_path = Path(__file__).parent / "app.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")  # Enable foreign keys
    cursor = conn.cursor()
    
    print("Checking current foreign key constraints...")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA foreign_key_list(login_logs)")
    constraints = cursor.fetchall()
    print(f"Current constraints: {constraints}")
    
    if constraints:
        fk = constraints[0]
        if "DELETE CASCADE" in str(fk) or fk[5] == 0:  # 0 = SET NULL, 1 = CASCADE, 2 = RESTRICT
            print("✓ CASCADE constraint already set correctly")
            conn.close()
            return True
    
    print("\n⚠️ Foreign key constraint needs to be fixed")
    print("Recreating login_logs table with CASCADE constraint...")
    
    try:
        # Step 1: Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys=OFF")
        
        # Step 2: Backup existing data
        cursor.execute("""
            CREATE TABLE login_logs_backup AS 
            SELECT * FROM login_logs
        """)
        print("✓ Backed up existing data")
        
        # Step 3: Drop the old table
        cursor.execute("DROP TABLE login_logs")
        print("✓ Dropped old login_logs table")
        
        # Step 4: Create new table with CASCADE constraint
        cursor.execute("""
            CREATE TABLE login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username VARCHAR(100) NOT NULL,
                login_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                ip_address VARCHAR(50),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        print("✓ Created new login_logs table with CASCADE constraint")
        
        # Step 5: Create indexes
        cursor.execute("""
            CREATE INDEX idx_login_logs_user_id ON login_logs(user_id)
        """)
        cursor.execute("""
            CREATE INDEX idx_login_logs_login_at ON login_logs(login_at)
        """)
        print("✓ Created indexes")
        
        # Step 6: Restore data
        cursor.execute("""
            INSERT INTO login_logs (id, user_id, username, login_at, ip_address)
            SELECT id, user_id, username, login_at, ip_address FROM login_logs_backup
        """)
        cursor.execute("DROP TABLE login_logs_backup")
        print("✓ Restored data from backup")
        
        # Step 7: Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        
        print("\n✓ Successfully fixed login_logs table with CASCADE constraint!")
        print("\nNow when you delete a user, all their login_logs will be automatically deleted.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_login_logs_cascade()
    exit(0 if success else 1)
