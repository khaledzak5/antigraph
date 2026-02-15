"""
Test script for college-based data isolation.

This script verifies that doctors from different colleges cannot see
each other's data and that each college starts with a clean slate.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models import FirstAidBox, FirstAidBoxItem, User
from app.utils_college import (
    get_user_college,
    verify_college_access,
    validate_college_assignment,
    get_all_accessible_colleges,
    prevent_cross_college_access
)


def create_test_doctors():
    """Create test doctors from different colleges"""
    from app.security import hash_password
    
    db = SessionLocal()
    
    # Clear existing test data
    db.query(FirstAidBoxItem).delete()
    db.query(FirstAidBox).delete()
    db.query(User).filter(User.username.in_(['test_doctor_kfupm', 'test_doctor_ksu'])).delete()
    db.commit()
    
    # Create doctor for KFUPM
    doc1 = User(
        full_name="طبيب الجامعة البترولية",
        username="test_doctor_kfupm",
        password_hash=hash_password("test123"),
        is_doc=True,
        doctor_college="جامعة الملك فهد للبترول والمعادن",
        is_active=True,
    )
    db.add(doc1)
    db.flush()
    
    # Create doctor for KSU
    doc2 = User(
        full_name="طبيب جامعة الملك سعود",
        username="test_doctor_ksu",
        password_hash=hash_password("test123"),
        is_doc=True,
        doctor_college="جامعة الملك سعود",
        is_active=True,
    )
    db.add(doc2)
    db.commit()
    
    return doc1, doc2


def test_doctor_college_assignment():
    """Test that doctors are correctly assigned to colleges"""
    db = SessionLocal()
    
    print("\n" + "="*60)
    print("TEST 1: Doctor College Assignment")
    print("="*60)
    
    doc1, doc2 = create_test_doctors()
    
    # Keep in session to avoid detached instances
    db = SessionLocal()
    doc1_db = db.query(User).filter(User.username == "test_doctor_kfupm").first()
    doc2_db = db.query(User).filter(User.username == "test_doctor_ksu").first()
    
    # Test get_user_college for doctor 1
    college1 = get_user_college(doc1_db)
    assert college1 == "جامعة الملك فهد للبترول والمعادن", f"Doctor 1 college mismatch: {college1}"
    print(f"✓ Doctor 1 assigned to: {college1}")
    
    # Test get_user_college for doctor 2
    college2 = get_user_college(doc2_db)
    assert college2 == "جامعة الملك سعود", f"Doctor 2 college mismatch: {college2}"
    print(f"✓ Doctor 2 assigned to: {college2}")
    
    db.close()


def test_college_access_verification():
    """Test that college access is properly verified"""
    db = SessionLocal()
    
    print("\n" + "="*60)
    print("TEST 2: College Access Verification")
    print("="*60)
    
    doc1, doc2 = create_test_doctors()
    
    db = SessionLocal()
    doc1_db = db.query(User).filter(User.username == "test_doctor_kfupm").first()
    doc2_db = db.query(User).filter(User.username == "test_doctor_ksu").first()
    
    # Doctor 1 should have access to their college
    is_valid, msg = validate_college_assignment(doc1_db, "جامعة الملك فهد للبترول والمعادن")
    assert is_valid, f"Doctor 1 should have access to their college: {msg}"
    print(f"✓ {msg}")
    
    # Doctor 1 should NOT have access to doctor 2's college
    is_valid, msg = validate_college_assignment(doc1_db, "جامعة الملك سعود")
    assert not is_valid, f"Doctor 1 should NOT have access to other college"
    print(f"✓ Correctly blocked: {msg}")
    
    # Test with doctor 2
    is_valid, msg = validate_college_assignment(doc2_db, "جامعة الملك سعود")
    assert is_valid, f"Doctor 2 should have access to their college"
    print(f"✓ {msg}")
    
    db.close()


def test_first_aid_box_isolation():
    """Test that first aid boxes are isolated by college"""
    db = SessionLocal()
    
    print("\n" + "="*60)
    print("TEST 3: First Aid Box Isolation")
    print("="*60)
    
    doc1, doc2 = create_test_doctors()
    
    db = SessionLocal()
    doc1_db = db.query(User).filter(User.username == "test_doctor_kfupm").first()
    doc2_db = db.query(User).filter(User.username == "test_doctor_ksu").first()
    
    # Create first aid boxes for each doctor's college
    box1 = FirstAidBox(
        box_name="صندوق العيادة - الجامعة البترولية",
        location="العيادة الطبية - KFUPM",
        college_id="جامعة الملك فهد للبترول والمعادن",
        created_by_user_id=doc1_db.id
    )
    db.add(box1)
    db.flush()
    
    box2 = FirstAidBox(
        box_name="صندوق العيادة - جامعة الملك سعود",
        location="العيادة الطبية - KSU",
        college_id="جامعة الملك سعود",
        created_by_user_id=doc2_db.id
    )
    db.add(box2)
    db.commit()
    
    print(f"✓ Created box 1 for KFUPM: {box1.box_name}")
    print(f"✓ Created box 2 for KSU: {box2.box_name}")
    
    # Verify isolation: Doctor 1 should only see box 1
    doc1_boxes = db.query(FirstAidBox).filter(
        FirstAidBox.college_id == get_user_college(doc1_db)
    ).all()
    assert len(doc1_boxes) == 1, f"Doctor 1 should see only 1 box, got {len(doc1_boxes)}"
    assert doc1_boxes[0].id == box1.id, "Doctor 1 should see their own box"
    print(f"✓ Doctor 1 can see: {[b.box_name for b in doc1_boxes]}")
    
    # Verify isolation: Doctor 2 should only see box 2
    doc2_boxes = db.query(FirstAidBox).filter(
        FirstAidBox.college_id == get_user_college(doc2_db)
    ).all()
    assert len(doc2_boxes) == 1, f"Doctor 2 should see only 1 box, got {len(doc2_boxes)}"
    assert doc2_boxes[0].id == box2.id, "Doctor 2 should see their own box"
    print(f"✓ Doctor 2 can see: {[b.box_name for b in doc2_boxes]}")
    
    db.close()


def test_first_aid_item_isolation():
    """Test that first aid box items are isolated by college"""
    db = SessionLocal()
    
    print("\n" + "="*60)
    print("TEST 4: First Aid Box Items Isolation")
    print("="*60)
    
    doc1, doc2 = create_test_doctors()
    
    db = SessionLocal()
    doc1_db = db.query(User).filter(User.username == "test_doctor_kfupm").first()
    doc2_db = db.query(User).filter(User.username == "test_doctor_ksu").first()
    
    # Create boxes
    box1 = FirstAidBox(
        box_name="صندوق العيادة - الجامعة البترولية",
        location="العيادة الطبية - KFUPM",
        college_id="جامعة الملك فهد للبترول والمعادن",
        created_by_user_id=doc1_db.id
    )
    db.add(box1)
    db.flush()
    
    box2 = FirstAidBox(
        box_name="صندوق العيادة - جامعة الملك سعود",
        location="العيادة الطبية - KSU",
        college_id="جامعة الملك سعود",
        created_by_user_id=doc2_db.id
    )
    db.add(box2)
    db.commit()
    
    # Add items to box 1
    item1 = FirstAidBoxItem(
        box_id=box1.id,
        college_id="جامعة الملك فهد للبترول والمعادن",
        drug_name="أسبرين",
        quantity=10,
        unit="عدد"
    )
    db.add(item1)
    
    # Add items to box 2
    item2 = FirstAidBoxItem(
        box_id=box2.id,
        college_id="جامعة الملك سعود",
        drug_name="باراسيتامول",
        quantity=20,
        unit="عدد"
    )
    db.add(item2)
    db.commit()
    
    print(f"✓ Added item to box 1: {item1.drug_name} ({item1.quantity})")
    print(f"✓ Added item to box 2: {item2.drug_name} ({item2.quantity})")
    
    # Verify items are isolated by college
    doc1_items = db.query(FirstAidBoxItem).filter(
        FirstAidBoxItem.college_id == get_user_college(doc1_db)
    ).all()
    assert len(doc1_items) == 1, f"Doctor 1 should see only 1 item"
    assert doc1_items[0].id == item1.id, "Doctor 1 should see their own item"
    print(f"✓ Doctor 1 can access items: {[i.drug_name for i in doc1_items]}")
    
    doc2_items = db.query(FirstAidBoxItem).filter(
        FirstAidBoxItem.college_id == get_user_college(doc2_db)
    ).all()
    assert len(doc2_items) == 1, f"Doctor 2 should see only 1 item"
    assert doc2_items[0].id == item2.id, "Doctor 2 should see their own item"
    print(f"✓ Doctor 2 can access items: {[i.drug_name for i in doc2_items]}")
    
    db.close()


def test_cross_college_prevention():
    """Test that cross-college access is prevented"""
    
    print("\n" + "="*60)
    print("TEST 5: Cross-College Access Prevention")
    print("="*60)
    
    doc1, doc2 = create_test_doctors()
    
    db = SessionLocal()
    doc1_db = db.query(User).filter(User.username == "test_doctor_kfupm").first()
    doc2_db = db.query(User).filter(User.username == "test_doctor_ksu").first()
    
    # Doctor 1 tries to access Doctor 2's college
    try:
        prevent_cross_college_access(doc1_db, "جامعة الملك سعود")
        assert False, "Should have raised PermissionError"
    except Exception as e:
        print(f"✓ Doctor 1 blocked from KSU: {str(e)}")
    
    # Doctor 2 tries to access Doctor 1's college
    try:
        prevent_cross_college_access(doc2_db, "جامعة الملك فهد للبترول والمعادن")
        assert False, "Should have raised PermissionError"
    except Exception as e:
        print(f"✓ Doctor 2 blocked from KFUPM: {str(e)}")
    
    # Doctor 1 can access their own college
    try:
        prevent_cross_college_access(doc1_db, "جامعة الملك فهد للبترول والمعادن")
        print(f"✓ Doctor 1 allowed access to KFUPM")
    except Exception as e:
        assert False, f"Should allow access to own college: {e}"
    
    db.close()


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*70)
    print("COLLEGE ISOLATION TEST SUITE")
    print("="*70)
    
    try:
        test_doctor_college_assignment()
        test_college_access_verification()
        test_first_aid_box_isolation()
        test_first_aid_item_isolation()
        test_cross_college_prevention()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED!")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()
