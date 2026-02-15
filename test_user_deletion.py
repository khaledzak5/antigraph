"""
Test user deletion after CASCADE constraint fix
"""
import importlib
import sys
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Remove cached models to force reload
if 'app.models' in sys.modules:
    del sys.modules['app.models']
if 'app.database' in sys.modules:
    del sys.modules['app.database']
if 'app' in sys.modules:
    del sys.modules['app']

from app.models import User, LoginLog

def test_user_deletion():
    # Create a fresh engine with foreign keys enabled
    engine = create_engine("sqlite:///app.db")
    
    @event.listens_for(engine, "connect")
    def set_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Clean up test user if exists
        db.query(LoginLog).filter_by(username="test_delete_user").delete()
        db.query(User).filter_by(username="test_delete_user").delete()
        db.commit()
        
        # Create a test user
        test_user = User(
            full_name="Test User for Deletion",
            username="test_delete_user",
            password_hash="hashed_password",
            is_admin=False,
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        user_id = test_user.id
        print(f"✓ Created test user: {user_id}")
        
        # Add some login logs
        for i in range(3):
            log = LoginLog(
                user_id=user_id,
                username="test_delete_user",
                ip_address=f"192.168.1.{i+1}"
            )
            db.add(log)
        db.commit()
        
        # Verify login logs exist
        logs_before = db.query(LoginLog).filter_by(user_id=user_id).count()
        print(f"✓ Created {logs_before} login logs for test user")
        
        # Delete the user
        user_to_delete = db.query(User).filter_by(id=user_id).first()
        db.delete(user_to_delete)
        db.commit()
        print(f"✓ Successfully deleted user {user_id}")
        
        # Verify user is gone
        user_exists = db.query(User).filter_by(id=user_id).first()
        if not user_exists:
            print(f"✓ User {user_id} is deleted from database")
        
        # Verify login logs are CASCADE deleted
        logs_after = db.query(LoginLog).filter_by(user_id=user_id).count()
        if logs_after == 0:
            print(f"✓ All {logs_before} login logs were automatically deleted (CASCADE)")
        else:
            print(f"❌ ERROR: {logs_after} login logs still exist!")
            return False
        
        print("\n" + "="*60)
        print("✓ USER DELETION TEST PASSED!")
        print("="*60)
        print("\nNow you can safely delete users without errors.")
        print("All their login_logs will be automatically removed.")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_user_deletion()
    exit(0 if success else 1)
