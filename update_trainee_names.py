from app.database import SessionLocal, engine
from sqlalchemy import text
import pandas as pd

db = SessionLocal()

# قائمة من الأرقام التدريبية والأسماء المعروفة
trainee_data = {
    '123456789': 'أحمد محمد علي',  # مثال
    '987654321': 'فاطمة خالد محمود',  # مثال
}

# محاولة قراءة من ملف Excel إن وُجد
try:
    # البحث عن ملف Excel في المشروع
    import os
    for file in os.listdir('.'):
        if file.endswith('.xlsx') or file.endswith('.xls'):
            print(f'وجدت ملف: {file}')
            # يمكنك قراءة البيانات من هنا
except:
    pass

# تحديث البيانات في الـ database
print('تحديث أسماء المتدربين...')

# For now, just update with placeholder names
for trainee_no, name in trainee_data.items():
    try:
        db.execute(text(f"""
            UPDATE course_enrollments 
            SET trainee_name = '{name}'
            WHERE trainee_no = '{trainee_no}' AND trainee_name IS NULL
        """))
    except:
        pass

db.commit()
print('تم التحديث!')
db.close()
