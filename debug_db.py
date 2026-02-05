
import sqlite3
import os

try:
    conn = sqlite3.connect('wikibook.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, icon FROM badge")
    badges = cursor.fetchall()
    print("Badges:")
    for b in badges:
        print(b)
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")

print("\nFiles in static/uploads:")
try:
    files = os.listdir('static/uploads')
    for f in files:
        print(f)
except Exception as e:
    print(f"File Error: {e}")
