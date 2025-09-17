import unittest
from src.collector.db import save_prompt
import sqlite3

class TestSavePrompt(unittest.TestCase):

    def setUp(self):
        # Set up an in-memory SQLite database for testing
        self.connection = sqlite3.connect(':memory:')
        self.cursor = self.connection.cursor()
        self.cursor.execute('''CREATE TABLE prompts (
            id TEXT PRIMARY KEY,
            model_id TEXT,
            prompt TEXT,
            categories TEXT,
            created_at TEXT
        )''')
        self.connection.commit()

    def tearDown(self):
        # Close the database connection after each test
        self.connection.close()

    def test_save_new_prompt(self):
        # Test saving a new prompt
        record = {
            "id": "1",
            "model_id": "model_1",
            "prompt": "This is a test prompt.",
            "categories": "test",
            "created_at": "2025-09-17"
        }
        save_prompt(self.connection, record)

        self.cursor.execute("SELECT prompt FROM prompts WHERE id = ?", (record["id"],))
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], record["prompt"])

    def test_save_duplicate_prompt(self):
        # Test saving a duplicate prompt
        record = {
            "id": "1",
            "model_id": "model_1",
            "prompt": "This is a duplicate test prompt.",
            "categories": "test",
            "created_at": "2025-09-17"
        }
        save_prompt(self.connection, record)
        save_prompt(self.connection, record)  # Attempt to save the same prompt again

        self.cursor.execute("SELECT COUNT(*) FROM prompts WHERE id = ?", (record["id"],))
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 1)  # Ensure the prompt is not duplicated

    def test_save_invalid_data(self):
        # Test saving a record with missing required fields
        invalid_record = {
            "id": None,  # Missing ID
            "model_id": "model_1",
            "prompt": "This is a test prompt.",
            "categories": "test",
            "created_at": "2025-09-17"
        }
        with self.assertRaises(ValueError):
            save_prompt(self.connection, invalid_record)

    def test_save_with_database_error(self):
        # Test handling of database connection errors
        self.connection.close()  # Simulate a closed connection
        valid_record = {
            "id": "1",
            "model_id": "model_1",
            "prompt": "This is a test prompt.",
            "categories": "test",
            "created_at": "2025-09-17"
        }
        with self.assertRaises(sqlite3.ProgrammingError):
            save_prompt(self.connection, valid_record)

if __name__ == "__main__":
    unittest.main()
