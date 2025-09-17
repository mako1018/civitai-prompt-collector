import sqlite3

def add_missing_columns(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check and add the `model_id` column if it doesn't exist
    cursor.execute("PRAGMA table_info(prompts)")
    columns = [row[1] for row in cursor.fetchall()]
    if "model_id" not in columns:
        cursor.execute("ALTER TABLE prompts ADD COLUMN model_id TEXT")
        print("Added `model_id` column to `prompts` table.")

    # Check and add the `categories` column if it doesn't exist
    if "categories" not in columns:
        cursor.execute("ALTER TABLE prompts ADD COLUMN categories TEXT")
        print("Added `categories` column to `prompts` table.")

    # Check and add the `created_at` column if it doesn't exist
    if "created_at" not in columns:
        cursor.execute("ALTER TABLE prompts ADD COLUMN created_at TEXT")
        print("Added `created_at` column to `prompts` table.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_missing_columns("test_large_dataset.db")
