"""
Medicine/Drug College Isolation Utilities

Functions for filtering medicine queries by college and ensuring college isolation
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

def get_doctor_college(db: Session, user_id: int) -> Optional[str]:
    """Get doctor's college from user_id"""
    try:
        result = db.execute(text("""
            SELECT doctor_college FROM users WHERE id = :user_id
        """), {"user_id": user_id}).scalar()
        return result
    except Exception:
        return None

def ensure_medicine_has_college(db: Session, medicine_id: int, college_id: str) -> bool:
    """
    Ensure a medicine record has a college_id set.
    Used when medicines are created without explicit college_id.
    """
    try:
        # Check if medicine already has a college_id
        current = db.execute(text("""
            SELECT college_id FROM drugs WHERE id = :id
        """), {"id": medicine_id}).scalar()
        
        if not current:
            # Set the college_id if not set
            db.execute(text("""
                UPDATE drugs SET college_id = :college_id WHERE id = :id
            """), {"college_id": college_id, "id": medicine_id})
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"Error setting college_id: {e}")
        return False

def filter_medicines_by_college(db: Session, college_id: str) -> str:
    """
    Returns a WHERE clause filter for filtering medicines by college_id.
    Usage: WHERE is_active=TRUE {filter_medicines_by_college(db, college_id)}
    """
    if college_id:
        return f"AND (college_id = '{college_id}' OR college_id IS NULL)"
    return ""

def verify_medicine_access(db: Session, medicine_id: int, college_id: str) -> bool:
    """
    Verify that a doctor from college_id can access a medicine record.
    Returns True if:
    - Medicine's college_id matches the doctor's college_id
    - Medicine's college_id is NULL (legacy data)
    """
    try:
        medicine_college = db.execute(text("""
            SELECT college_id FROM drugs WHERE id = :id
        """), {"id": medicine_id}).scalar()
        
        if medicine_college is None or medicine_college == college_id:
            return True
        return False
    except Exception:
        return False

def prevent_medicine_cross_access(db: Session, medicine_id: int, college_id: str) -> None:
    """
    Raise HTTPException if doctor cannot access this medicine.
    Security check for edit/delete operations.
    """
    if not verify_medicine_access(db, medicine_id, college_id):
        raise HTTPException(
            status_code=403,
            detail=f"آسف، لا يمكنك الوصول إلى هذا الدواء. قد يكون من كلية أخرى."
        )

def auto_assign_college_to_medicine(db: Session, medicine_id: int, college_id: str) -> bool:
    """
    Auto-assign college_id to a medicine if not already set.
    Returns True if assignment was made, False if already had a college.
    """
    try:
        # Get current college_id
        current_college = db.execute(text("""
            SELECT college_id FROM drugs WHERE id = :id
        """), {"id": medicine_id}).scalar()
        
        if not current_college:
            # Assign college
            db.execute(text("""
                UPDATE drugs SET college_id = :college WHERE id = :id
            """), {"college": college_id, "id": medicine_id})
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"Error auto-assigning college: {e}")
        db.rollback()
        return False

def get_pharmacy_stock_query(college_id: str = None) -> str:
    """
    Get a SQL WHERE clause filter for pharmacy_stock table by college.
    If college_id is None, returns empty string (no filter).
    """
    if college_id:
        return f"AND ps.college_id = '{college_id}'"
    return ""

def get_warehouse_stock_query(college_id: str = None) -> str:
    """
    Get a SQL WHERE clause filter for warehouse_stock table by college.
    """
    if college_id:
        return f"AND ws.college_id = '{college_id}'"
    return ""

def get_drug_transactions_query(college_id: str = None) -> str:
    """
    Get a SQL WHERE clause filter for drug_transactions table by college.
    """
    if college_id:
        return f"AND dt.college_id = '{college_id}'"
    return ""

# Summary of college isolation for medicines:
"""
When a doctor interacts with medicines:

1. READING medicines:
   - Use filter_medicines_by_college() to filter the query
   - Only show medicines from their college or NULL (legacy)

2. CREATING medicines:
   - Call auto_assign_college_to_medicine() after creation
   - OR pass college_id in INSERT statement

3. EDITING medicines:
   - Call prevent_medicine_cross_access() first
   - Only allow if medicine belongs to their college

4. DELETING medicines:
   - Call prevent_medicine_cross_access() first
   - Only allow if medicine belongs to their college

5. STATISTICS:
   - Always filter by college_id
   - Each doctor sees only their college's stats
"""
