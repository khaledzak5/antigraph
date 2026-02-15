from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== تحديث الأدوية القديمة ===\n")

# حذف جميع الأدوية القديمة
db.execute(text("PRAGMA foreign_keys=OFF"))
db.execute(text("DELETE FROM drugs"))
db.execute(text("PRAGMA foreign_keys=ON"))
db.commit()

print("✅ تم حذف جميع الأدوية القديمة")
print("✅ الآن عند إضافة أدوية جديدة ستُحفظ مع created_by = user_id\n")

# تحقق
result = db.execute(text("SELECT COUNT(*) as cnt FROM drugs")).mappings().first()
print(f"عدد الأدوية الحالية: {result['cnt']}")

db.close()
