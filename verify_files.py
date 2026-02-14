import sys
import py_compile

files = [
    'app/routers/hod.py',
    'app/reports/skills_record_pdf_template.py',
    'app/routers/clinic.py'
]

print("🔍 Compiling Python files...")
all_ok = True

for file in files:
    try:
        py_compile.compile(file, doraise=True)
        print(f"✓ {file}")
    except py_compile.PyCompileError as e:
        print(f"❌ {file}")
        print(f"   Error: {e}")
        all_ok = False

if all_ok:
    print("\n✅ All files compiled successfully!")
else:
    print("\n❌ Some files have errors")
    sys.exit(1)
