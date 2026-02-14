import sqlite3

# Connect to the database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Check table structure
cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()

print('Users table columns:')
for col in columns:
    print(f'Column: {col[1]}, Type: {col[2]}')

print('\nAvailable users:')
cursor.execute('SELECT * FROM users LIMIT 5;')
users = cursor.fetchall()

for user in users:
    print(f'User data: {user}')

conn.close()