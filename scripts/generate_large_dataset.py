import random
import string
import sqlite3

# Function to generate random strings
def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to generate a large dataset
def generate_large_dataset(num_records=100000):
    dataset = []
    for _ in range(num_records):
        record = {
            "prompt": random_string(50),
            "metadata": random_string(100)
        }
        dataset.append(record)
    return dataset

# Function to insert dataset into the database
def insert_large_dataset(dataset, db_path="test_large_dataset.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            metadata TEXT NOT NULL
        )
        """
    )

    # Insert data
    for record in dataset:
        cursor.execute(
            "INSERT INTO prompts (prompt, metadata) VALUES (?, ?)",
            (record["prompt"], record["metadata"])
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Generating large dataset...")
    data = generate_large_dataset()
    print("Inserting dataset into the database...")
    insert_large_dataset(data)
    print("Done.")
