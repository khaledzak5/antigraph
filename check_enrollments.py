from app.database import get_db, is_sqlite
from sqlalchemy import text

db = next(get_db())

try:
    # Check course_enrollments table
    print("✓ Checking course_enrollments table...")
    query = """
    SELECT trainee_no, COUNT(*) as courses_count 
    FROM course_enrollments 
    GROUP BY trainee_no 
    LIMIT 5
    """
    
    result = db.execute(text(query)).fetchall()
    
    if result:
        print("✓ Found trainees with courses:")
        for row in result:
            trainee_no, count = row
            print(f"  - Trainee {trainee_no}: {count} course(s)")
            
            # Get course details for this trainee
            course_query = """
            SELECT ce.trainee_no, c.course_name_ar, c.course_hours 
            FROM course_enrollments ce
            JOIN courses c ON c.course_id = ce.course_id
            WHERE ce.trainee_no = :trainee_no
            """
            courses = db.execute(text(course_query), {"trainee_no": trainee_no}).fetchall()
            for course in courses:
                t_no, c_name, hours = course
                print(f"      - {c_name} ({hours} hours)")
    else:
        print("⚠ No course enrollments found in database")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
