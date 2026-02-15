# User Deletion - NOT NULL Constraint Fix ✅ RESOLVED

## Problem ❌
When deleting a user, you got:
```
IntegrityError: (sqlite3.IntegrityError) NOT NULL constraint failed: login_logs.user_id
[SQL: UPDATE login_logs SET user_id=? WHERE login_logs.id = ?]
[parameters: (None, 54)]
```

## Root Causes
1. **Foreign Key Constraint**: Set to `NO ACTION` instead of `CASCADE`
2. **SQLAlchemy Relationship**: Not configured to let the database handle cascade
3. **SQLite Config**: Foreign keys not enabled globally
4. **ORM Management**: SQLAlchemy tried to manage deletion instead of database

## Solution Implemented ✅

### 1. Database Schema Fix
Recreated `login_logs` table with `ON DELETE CASCADE`:

**Before:**
```sql
FOREIGN KEY (user_id) REFERENCES users(id) ON NO ACTION
```

**After:**
```sql
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
```

### 2. SQLAlchemy Model Configuration
Updated [app/models.py](app/models.py#L151-L165):

**User Model** - Added login_logs relationship:
```python
class User(Base):
    # ... existing fields ...
    
    # Login logs relationship - database handles cascade
    login_logs = relationship(
        "LoginLog",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,  # ← Important!
        lazy="selectin",
    )
```

**LoginLog Model** - Added passive_deletes:
```python
class LoginLog(Base):
    __tablename__ = "login_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(100), nullable=False)
    login_at = Column(DateTime, server_default=func.now(), nullable=False)
    ip_address = Column(String(50), nullable=True)
    
    # passive_deletes=True: Database handles cascade, not ORM
    user = relationship("User", back_populates="login_logs", passive_deletes=True)
```

### 3. Enable Foreign Keys in SQLite
Updated [app/database.py](app/database.py):

```python
# Enable foreign keys for SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```

## Files Modified

| File | Change | Status |
|------|--------|--------|
| [app/models.py](app/models.py#L120-L165) | Added login_logs relationship to User; Updated LoginLog | ✅ |
| [app/database.py](app/database.py) | Enable PRAGMA foreign_keys=ON | ✅ |

## How The Fix Works

### Deletion Flow (After Fix):
```
Step 1: Admin clicks Delete User
  ↓
Step 2: User record marked for deletion
  ↓
Step 3: SQLAlchemy sees passive_deletes=True
  ↓
Step 4: SQLAlchemy deletes user from database
  ↓
Step 5: Database CASCADE triggered automatically
  ↓
Step 6: All login_logs for user deleted by database
  ↓
✅ Success - No errors!
```

### Key Configuration: `passive_deletes=True`
This tells SQLAlchemy:
- ❌ DON'T try to manage related records in Python
- ❌ DON'T try to update foreign keys to NULL
- ✅ DO let the database handle it via CASCADE

Without this, SQLAlchemy would try:
1. Update login_logs.user_id to NULL
2. Fail with NOT NULL constraint error

## Test Results ✅

```
✓ Created test user: 10
✓ Created 3 login logs for test user
✓ Successfully deleted user 10
✓ User 10 is deleted from database
✓ All 3 login logs were automatically deleted (CASCADE)

============================================================
✓ USER DELETION TEST PASSED!
============================================================
```

## How to Use

Just delete users normally from the Admin Panel:
1. Admin Panel → Users
2. Click "Delete" button
3. ✅ User deleted
4. ✅ All login history removed automatically
5. ✅ No errors

## Technical Details

### cascade="all, delete-orphan"
On User side tells SQLAlchemy:
- Delete LoginLog records when User is deleted
- Clean up orphaned records

### passive_deletes=True
Tells SQLAlchemy:
- Database handles the actual cascade
- Don't manage it at ORM level

### PRAGMA foreign_keys=ON
SQLite setting:
- Enforce foreign key constraints
- Enable CASCADE behavior
- Atomic transactions

## Foreign Keys Summary

| Table | FK Column | References | Constraint |
|-------|-----------|-----------|-----------|
| login_logs | user_id | users.id | **CASCADE** ✅ |
| departments | head_user_id | users.id | SET NULL ✅ |
| course_enrollments | course_id | courses.id | CASCADE ✅ |
| course_targets | course_id | courses.id | CASCADE ✅ |
| first_aid_items | box_id | first_aid_boxes.id | CASCADE ✅ |

## Data Integrity

When user is deleted:
```
users table:              login_logs table:
┌─────────────────┐      ┌──────────────────────┐
│ id │ username  │ --->  │ id │ user_id│ login│
├─────────────────┤      ├──────────────────────┤
│ 1  │ john      │       │ 1  │ 1      │ ...  │
│ 2  │ jane      │ --->  │ 2  │ 1      │ ...  │
│ 3  │ bob       │       │ 3  │ 1      │ ...  │
└─────────────────┘      │ 4  │ 2      │ ...  │
                         └──────────────────────┘

Delete User (id=1):
↓
users.id=1 deleted
↓ CASCADE triggered
login_logs with user_id=1 auto-deleted (rows 1,2,3)
↓
Final state - Clean!
```

## Status

✅ **COMPLETE AND TESTED**

- Database schema updated
- SQLAlchemy models configured correctly
- Foreign keys enabled globally
- All tests passing
- Ready for production use

## Next Steps

Nothing needed - user deletion now works perfectly!

If you have other foreign key tables that might have similar issues:
- Check if they have `passive_deletes=True`
- Verify CASCADE constraints are set
- Test deletion flows for those tables
