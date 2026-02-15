from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check if any medicines exist and what their college_id values are
print('=== CHECKING MEDICINES IN DATABASE ===')
result = db.execute(text('SELECT id, trade_name, generic_name, college_id FROM drugs LIMIT 20')).mappings().all()
print('Total rows in drugs table:', len(result))
for row in result:
    print(f'  ID: {row["id"]}, Name: {row["trade_name"]}, College_ID: {row["college_id"]}')

# Check pharmacy_stock
result = db.execute(text('SELECT id, drug_id, balance_qty, college_id FROM pharmacy_stock LIMIT 10')).mappings().all()
print('\nTotal rows in pharmacy_stock table:', len(result))
for row in result:
    print(f'  ID: {row["id"]}, Drug_ID: {row["drug_id"]}, College_ID: {row["college_id"]}')

db.close()
