from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)

# Get courses table structure
courses_columns = inspector.get_columns('courses')
print("📋 أعمدة جدول courses:")
for col in courses_columns:
    print(f"  - {col['name']}: {col['type']}")

print("\n" + "="*50 + "\n")

# Get course_enrollments table structure
enrollments_columns = inspector.get_columns('course_enrollments')
print("📋 أعمدة جدول course_enrollments:")
for col in enrollments_columns:
    print(f"  - {col['name']}: {col['type']}")

print("\n" + "="*50 + "\n")

# Get users table structure (trainees are users)
users_columns = inspector.get_columns('users')
print("📋 أعمدة جدول users:")
for col in users_columns:
    print(f"  - {col['name']}: {col['type']}")
