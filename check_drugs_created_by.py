from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== فحص بيانات الأدوية ===\n")

# فحص الأدوية الموجودة
result = db.execute(text("""
    SELECT id, trade_name, college_id, created_by, is_active 
    FROM drugs 
    LIMIT 20
""")).mappings().all()

print(f"عدد الأدوية الموجودة: {len(result)}\n")

for drug in result:
    print(f"ID: {drug['id']}")
    print(f"  الاسم: {drug['trade_name']}")
    print(f"  الكلية: {drug['college_id']}")
    print(f"  أضافها المستخدم: {drug['created_by']}")
    print(f"  نشطة: {drug['is_active']}")
    print()

db.close()
