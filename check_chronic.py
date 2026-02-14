import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Query for visits with chronic disease data
cursor.execute('SELECT id, full_name, chronic_json FROM clinic_patients WHERE record_kind="visit" LIMIT 10;')
rows = cursor.fetchall()

print('Database results:')
for row in rows:
    print(f'ID: {row[0]}, Name: {row[1]}')
    print(f'Raw Chronic JSON: {repr(row[2])}')
    
    # Try to parse JSON if it's a string
    if row[2]:
        try:
            if isinstance(row[2], str):
                parsed = json.loads(row[2])
                print(f'Parsed Chronic Data: {parsed}')
            else:
                print(f'Chronic Data (not string): {row[2]}')
        except json.JSONDecodeError as e:
            print(f'Failed to parse JSON: {e}')
    else:
        print('No chronic disease data')
    print('---')

conn.close()