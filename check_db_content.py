import sqlite3
import os

db_path = 'instance/wikibook.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Tables in database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

print("\nContent of 'class' table:")
try:
    cursor.execute("SELECT * FROM class")
    rows = cursor.fetchall()
    if not rows:
        print("Table 'class' is empty.")
    for row in rows:
        print(row)
except Exception as e:
    print(f"Error querying class table: {e}")

print("\nContent of 'group' table:")
try:
    cursor.execute("SELECT * FROM 'group'") # Group is reserved keyword often
    rows = cursor.fetchall()
    if not rows:
        print("Table 'group' is empty.")
    for row in rows:
        print(row)
except Exception as e:
    print(f"Error querying group table: {e}")
    
conn.close()
