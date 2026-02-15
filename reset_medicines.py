from app.database import SessionLocal, engine
from sqlalchemy import text, event

db = SessionLocal()

# Disable foreign keys
db.execute(text("PRAGMA foreign_keys=OFF"))

# Delete all medicines to start fresh - delete in correct order
print("=== DELETING ALL MEDICINES ===")
db.execute(text("DELETE FROM drug_stock_movements"))
db.execute(text("DELETE FROM drug_balance"))
db.execute(text("DELETE FROM drug_transactions"))
db.execute(text("DELETE FROM pharmacy_stock"))
db.execute(text("DELETE FROM warehouse_stock"))
db.execute(text("DELETE FROM drugs"))
db.commit()

# Re-enable foreign keys
db.execute(text("PRAGMA foreign_keys=ON"))

print("✅ All medicines deleted")

# Verify
result = db.execute(text("SELECT COUNT(*) as cnt FROM drugs")).mappings().first()
print(f"Total medicines after delete: {result['cnt']}")

db.close()
