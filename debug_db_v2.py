
import sqlite3
import os

db_path = os.path.abspath('wikibook.db')
print(f"DB Path: {db_path}")

if not os.path.exists(db_path):
    print("DB file does not exist!")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", [t[0] for t in tables])
        
        if ('badge',) in tables or ('Badge',) in tables:
             cursor.execute("SELECT id, name, icon FROM badge")
             badges = cursor.fetchall()
             print("Badges:")
             for b in badges:
                 print(b)
        else:
             print("Badge table not found. Checking case sensitivity...")
             # Try case insensitive
             for t in tables:
                 if t[0].lower() == 'badge':
                     print(f"Found table {t[0]}")
                     cursor.execute(f"SELECT id, name, icon FROM {t[0]}")
                     print(cursor.fetchall())

        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
