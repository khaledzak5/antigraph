from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

# Look for trainee-related tables
trainee_tables = [t for t in tables if 'trainee' in t.lower() or 'student' in t.lower()]
print('Trainee/Student tables:', trainee_tables)

# Check course_enrollments structure
if 'course_enrollments' in tables:
    cols = inspector.get_columns('course_enrollments')
    print('\nCourse Enrollments columns:')
    for col in cols:
        print(f'  - {col["name"]}: {col["type"]}')

# Check what data we have
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text('''
SELECT * FROM course_enrollments WHERE trainee_no = '123456789' LIMIT 1
''')).mappings().first()

if result:
    print('\nCourse Enrollment data for trainee 123456789:')
    for key, value in dict(result).items():
        print(f'  {key}: {value}')

db.close()
