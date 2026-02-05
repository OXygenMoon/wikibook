
import sqlite3
import os

db_path = '/root/projects/wikibook/instance/wikibook.db'
print(f"DB Path: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, icon FROM badge")
    badges = cursor.fetchall()
    print("Badges:")
    for b in badges:
        print(b)
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")
