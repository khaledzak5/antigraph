"""
Force recreation of login_logs table with proper CASCADE foreign key
This version directly uses SQLAlchemy to recreate the table
"""
import os
from pathlib import Path
from sqlalchemy import inspect, text, event, create_engine

def force_recreate_login_logs():
    db_path = Path(__file__).parent / "app.db"
    db_url = f"sqlite:///{db_path}"
    
    print(f"Database path: {db_path}")
    print(f"Database URL: {db_url}")
    
    engine = create_engine(db_url)
    
    # Enable foreign keys for this connection
    @event.listens_for(engine, "connect")
    def set_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    with engine.begin() as conn:
        print("\n✓ Connection established with PRAGMA foreign_keys=ON")
        
        # Check if table exists
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        
        data = []
        if "login_logs" in tables:
            print("⚠️  login_logs table exists, recreating...")
            
            # Get current data
            result = conn.execute(text("""
                SELECT id, user_id, username, login_at, ip_address 
                FROM login_logs
            """))
            data = result.fetchall()
            print(f"✓ Backed up {len(data)} login log entries")
            
            # Get column info from inspector
            cols = inspector.get_columns("login_logs")
            print(f"Current columns: {[c['name'] for c in cols]}")
            
            # Drop old table
            conn.execute(text("DROP TABLE login_logs"))
            print("✓ Dropped old login_logs table")
        
        # Create new table with CASCADE
        print("\nCreating new login_logs table with CASCADE constraint...")
        conn.execute(text("""
            CREATE TABLE login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username VARCHAR(100) NOT NULL,
                login_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                ip_address VARCHAR(50),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        print("✓ Created login_logs table")
        
        # Create indexes
        conn.execute(text("CREATE INDEX idx_login_logs_user_id ON login_logs(user_id)"))
        conn.execute(text("CREATE INDEX idx_login_logs_login_at ON login_logs(login_at)"))
        print("✓ Created indexes")
        
        # Restore data if we had any
        if data:
            print(f"Restoring {len(data)} entries...")
            for row in data:
                conn.execute(text("""
                    INSERT INTO login_logs (id, user_id, username, login_at, ip_address)
                    VALUES (:id, :user_id, :username, :login_at, :ip_address)
                """), {
                    "id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "login_at": row[3],
                    "ip_address": row[4]
                })
            print(f"✓ Restored all {len(data)} entries")
    
    # Verify the new constraint
    with engine.connect() as conn:
        # Need to enable pragma again
        conn.execute(text("PRAGMA foreign_keys=ON"))
        fk_info = conn.execute(text("PRAGMA foreign_key_list(login_logs)")).fetchall()
        print(f"\nForeign key constraints:")
        for fk in fk_info:
            print(f"  {fk}")
    
    print("\n" + "="*60)
    print("✓ LOGIN_LOGS TABLE RECREATED WITH CASCADE")
    print("="*60)
    print("\nForeign Key Details:")
    print("  - ON DELETE CASCADE: When a user is deleted, all their")
    print("    login_logs are automatically deleted")
    print("  - NOT NULL constraint: user_id cannot be null")
    print("  - Result: User deletion will work without errors!")

if __name__ == "__main__":
    force_recreate_login_logs()
