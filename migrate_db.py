import sqlite3
import os

def migrate_db():
    # Try instance folder first, then root
    paths = ["instance/wikibook.db", "wikibook.db"]
    db_path = None
    for p in paths:
        if os.path.exists(p):
            # Check if it has tables
            try:
                conn = sqlite3.connect(p)
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='wiki_page'")
                if cursor.fetchone()[0] > 0:
                    db_path = p
                    conn.close()
                    break
                conn.close()
            except:
                pass
    
    if not db_path:
        print("Valid Database not found.")
        return

    print(f"Migrating database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define new tables
    new_tables = {
        "user_active_status": """
            CREATE TABLE IF NOT EXISTS user_active_status (
                user_id INTEGER PRIMARY KEY,
                last_active_at DATETIME,
                current_path VARCHAR(500),
                current_action VARCHAR(200),
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
        """,
        "study_session": """
            CREATE TABLE IF NOT EXISTS study_session (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                start_time DATETIME,
                end_time DATETIME,
                FOREIGN KEY(user_id) REFERENCES user(id)
            )
        """
    }

    # Create new tables
    for table_name, create_sql in new_tables.items():
        try:
            print(f"Creating table {table_name}...")
            cursor.execute(create_sql)
            print(f"Successfully created {table_name}.")
        except Exception as e:
            print(f"Error creating {table_name}: {e}")

    tables = ["wiki_page", "note"]
    column = "comment_enabled"
    column_type = "BOOLEAN DEFAULT 1"

    for table in tables:
        try:
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in cursor.fetchall()]
            
            if column not in columns:
                print(f"Adding {column} to {table}...")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                conn.commit()
                print(f"Successfully added {column} to {table}.")
            else:
                print(f"Column {column} already exists in {table}.")
                
        except Exception as e:
            print(f"Error migrating {table}: {e}")

    conn.close()

if __name__ == "__main__":
    migrate_db()
