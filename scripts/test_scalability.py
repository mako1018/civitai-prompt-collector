import time
import sqlite3

def test_save_to_db_performance(db_path="test_large_dataset.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Measure the time taken to query the dataset
    start_time = time.time()
    cursor.execute("SELECT COUNT(*) FROM prompts")
    total_records = cursor.fetchone()[0]
    end_time = time.time()

    print(f"Total records: {total_records}")
    print(f"Time taken to count records: {end_time - start_time:.2f} seconds")

    # Measure the time taken to insert a new record
    new_record = ("Test Prompt", "Test Metadata")
    start_time = time.time()
    cursor.execute(
        "INSERT INTO prompts (prompt, metadata) VALUES (?, ?)",
        new_record
    )
    conn.commit()
    end_time = time.time()

    print(f"Time taken to insert a record: {end_time - start_time:.2f} seconds")

    conn.close()

if __name__ == "__main__":
    print("Running scalability test...")
    test_save_to_db_performance()
    print("Scalability test completed.")
