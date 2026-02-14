from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print("📋 جميع الجداول في الـ Database:")
for table in sorted(tables):
    print(f"  - {table}")

# Check if we can find course-related tables
course_tables = [t for t in tables if 'course' in t.lower()]
print(f"\n🔍 جداول تتعلق بـ Courses:")
for table in course_tables:
    print(f"  - {table}")

# Check trainee tables
trainee_tables = [t for t in tables if 'trainee' in t.lower()]
print(f"\n🔍 جداول تتعلق بـ Trainees:")
for table in trainee_tables:
    print(f"  - {table}")
