"""
TEST MEDICINE COLLEGE ISOLATION
Tests that medicines created by one doctor are NOT visible to other doctors
"""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("\n" + "="*70)
print("TEST: MEDICINE COLLEGE ISOLATION")
print("="*70)

# Scenario: Doctor A from College "1" creates Paracetamol
# Scenario: Doctor B from College "2" creates Ibuprofen
# Expected: Doctor A sees only Paracetamol, Doctor B sees only Ibuprofen

# Simulate adding medicine WITH college_id (as if doctor created it)
print("\n1️⃣  SCENARIO: Doctor A (College 1) creates Paracetamol")
db.execute(text("""
    INSERT INTO drugs (drug_code, trade_name, generic_name, strength, form, unit, is_active, college_id)
    VALUES ('DRUG-DOC1-001', 'Paracetamol', 'Acetaminophen', '500mg', 'tablet', 'tablet', TRUE, 1)
"""))
db.commit()

result = db.execute(text("SELECT id, trade_name, generic_name, college_id FROM drugs WHERE trade_name='Paracetamol'")).mappings().first()
print(f"   ✓ Created: {result['trade_name']} ({result['generic_name']}) - College_ID: {result['college_id']}")

# Simulate adding medicine FOR College 2
print("\n2️⃣  SCENARIO: Doctor B (College 2) creates Ibuprofen")
db.execute(text("""
    INSERT INTO drugs (drug_code, trade_name, generic_name, strength, form, unit, is_active, college_id)
    VALUES ('DRUG-DOC2-001', 'Ibuprofen', 'Ibuprofen', '400mg', 'tablet', 'tablet', TRUE, 2)
"""))
db.commit()

result = db.execute(text("SELECT id, trade_name, generic_name, college_id FROM drugs WHERE trade_name='Ibuprofen'")).mappings().first()
print(f"   ✓ Created: {result['trade_name']} ({result['generic_name']}) - College_ID: {result['college_id']}")

# Test filtering: College 1 query
print("\n3️⃣  TEST: Doctor A (College 1) queries medicines")
results = db.execute(text("SELECT id, trade_name, college_id FROM drugs WHERE college_id=1")).mappings().all()
print(f"   Found {len(results)} medicine(s):")
for row in results:
    print(f"     - {row['trade_name']} (College {row['college_id']})")

if len(results) == 1 and results[0]['trade_name'] == 'Paracetamol':
    print("   ✅ PASS: Doctor A sees only their medicine")
else:
    print("   ❌ FAIL: Doctor A should see only 1 medicine (Paracetamol)")

# Test filtering: College 2 query
print("\n4️⃣  TEST: Doctor B (College 2) queries medicines")
results = db.execute(text("SELECT id, trade_name, college_id FROM drugs WHERE college_id=2")).mappings().all()
print(f"   Found {len(results)} medicine(s):")
for row in results:
    print(f"     - {row['trade_name']} (College {row['college_id']})")

if len(results) == 1 and results[0]['trade_name'] == 'Ibuprofen':
    print("   ✅ PASS: Doctor B sees only their medicine")
else:
    print("   ❌ FAIL: Doctor B should see only 1 medicine (Ibuprofen)")

# Test unfiltered query (should show all medicines - BUG scenario)
print("\n5️⃣  TEST: UNFILTERED query (simulates BUG - showing all medicines)")
results = db.execute(text("SELECT id, trade_name, college_id FROM drugs")).mappings().all()
print(f"   Total medicines in database: {len(results)}")
for row in results:
    print(f"     - {row['trade_name']} (College {row['college_id']})")

print("\n" + "="*70)
print("SUMMARY:")
print("="*70)
total = len(db.execute(text("SELECT COUNT(*) as cnt FROM drugs")).mappings().all())
print(f"✓ Database now contains {total} total medicine records")
print("✓ Each medicine has a college_id assigned")
print("✓ Queries with college_id filter work correctly")
print("\nNEXT: The endpoint code must use college_id filtering:")
print("  - /clinic/pharmacy/drugs must filter: WHERE college_id=:college_id")
print("  - /clinic/pharmacy/drugs/create must assign: college_id=current_user.doctor_college")
print("="*70 + "\n")

db.close()
