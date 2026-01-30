import sqlite3
import os

db_path = "instance/wikibook.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {os.path.abspath(db_path)}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:", tables)

    # Define new columns
    new_columns = [
        ("real_name", "VARCHAR(80)"),
        ("student_id", "VARCHAR(20)"),
        ("department", "VARCHAR(100)"),
        ("class_name", "VARCHAR(100)")
    ]

    # Get existing columns
    # Try 'user' first, then 'User'
    table_name = "user"
    if ('user',) not in tables and ('User',) in tables:
        table_name = "User"
    
    print(f"Using table name: {table_name}")

    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print("Existing columns:", existing_columns)

        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                print(f"Adding column {col_name}...")
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                    if col_name == "student_id":
                        cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_user_student_id ON {table_name}(student_id)")
                except Exception as e:
                    print(f"Error adding {col_name}: {e}")
            else:
                print(f"Column {col_name} already exists.")
    except Exception as e:
        print(f"Error accessing table {table_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
