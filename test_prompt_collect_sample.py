import unittest
from unittest.mock import patch, MagicMock
from src.collector.collector import CivitaiPromptCollector
import sqlite3
import os

class TestCivitaiPromptCollector(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.conn = sqlite3.connect(":memory:")  # Use an in-memory database for testing
        self.conn.execute("CREATE TABLE IF NOT EXISTS civitai_prompts (civitai_id TEXT PRIMARY KEY)")
        self.collector = CivitaiPromptCollector(api_key="test_key", db_path="test_collect.db", conn=self.conn)
        # Ensure the test database is clean
        if os.path.exists("test_collect.db"):
            os.remove("test_collect.db")

    def tearDown(self):
        # Clean up the test database after each test
        if os.path.exists("test_collect.db"):
            os.remove("test_collect.db")

    @patch("requests.Session.get")
    def test_fetch_prompts(self, mock_get):
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {"id": "1", "full_prompt": "Test Prompt 1"},
                {"id": "2", "full_prompt": "Test Prompt 2"}
            ]
        }
        mock_get.return_value = mock_response

        # Call fetch_prompts
        prompts = self.collector.fetch_prompts(endpoint="/api/prompts", max_pages=1)

        # Assertions
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[0]["civitai_id"], "1")
        self.assertEqual(prompts[1]["full_prompt"], "Test Prompt 2")

    @patch("requests.Session.get")
    def test_fetch_prompts_error_handling(self, mock_get):
        # Mock API response with 500 error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Call fetch_prompts and expect empty result
        prompts = self.collector.fetch_prompts(endpoint="/api/prompts", max_pages=1)

        # Assertions
        self.assertEqual(len(prompts), 0)

    def test_save_to_db(self):
        # Sample data
        items = [
            {"civitai_id": "1", "full_prompt": "Test Prompt 1", "negative_prompt": "", "raw_metadata": {}},
            {"civitai_id": "2", "full_prompt": "Test Prompt 2", "negative_prompt": "", "raw_metadata": {}}
        ]

        # Call save_to_db
        self.collector.save_to_db(items)

        # Verify data in the database
        conn = sqlite3.connect("test_collect.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM civitai_prompts")
        rows = cur.fetchall()
        conn.close()

        # Assertions
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], "1")  # civitai_id
        self.assertEqual(rows[1][2], "Test Prompt 2")  # full_prompt

    def test_save_to_db_with_duplicates(self):
        # Ensure the table exists before clearing data
        conn = sqlite3.connect("test_collect.db")
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS civitai_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            civitai_id TEXT,
            full_prompt TEXT,
            negative_prompt TEXT,
            raw_metadata TEXT,
            categories TEXT,
            collected_at TEXT DEFAULT (datetime('now'))
        )
        """)
        cur.execute("DELETE FROM civitai_prompts")
        conn.commit()
        conn.close()

        # Sample data with duplicates
        items = [
            {"civitai_id": "1", "full_prompt": "Test Prompt 1", "negative_prompt": "", "raw_metadata": {}},
            {"civitai_id": "1", "full_prompt": "Test Prompt 1 Duplicate", "negative_prompt": "", "raw_metadata": {}},
            {"civitai_id": "2", "full_prompt": "Test Prompt 2", "negative_prompt": "", "raw_metadata": {}}
        ]

        # Call save_to_db
        self.collector.save_to_db(items)

        # Verify data in the database
        conn = sqlite3.connect("test_collect.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM civitai_prompts")
        rows = cur.fetchall()
        conn.close()

        # Assertions
        self.assertEqual(len(rows), 2)  # Only two unique entries
        self.assertEqual(rows[0][1], "1")  # civitai_id
        self.assertEqual(rows[1][1], "2")  # civitai_id

        # Debug: Inspect database content after the test
        conn = sqlite3.connect("test_collect.db")
        cur = conn.cursor()
        rows = cur.execute("SELECT * FROM civitai_prompts").fetchall()
        # Debug: Print detailed database content after the test
        print("Detailed Database Content:")
        for row in rows:
            print(row)
        conn.close()

        # Manual inspection of database content
        conn = sqlite3.connect("test_collect.db")
        cur = conn.cursor()
        rows = cur.execute("SELECT * FROM civitai_prompts").fetchall()
        print("Manual Database Inspection:")
        for row in rows:
            print(row)
        conn.close()

    def test_initialization_validation(self):
        # Test missing API key
        with self.assertRaises(ValueError) as context:
            CivitaiPromptCollector(api_key=None, db_path="test_collect.db")
        self.assertEqual(str(context.exception), "API key must be provided.")

        # Test invalid database path
        with self.assertRaises(ValueError) as context:
            CivitaiPromptCollector(api_key="test_key", db_path="invalid_path.txt")
        self.assertEqual(str(context.exception), "Database path must end with '.db'.")

    def test_direct_select_query(self):
        # Insert a record
        self.conn.execute("INSERT INTO civitai_prompts (civitai_id) VALUES (?)", ("test_id",))
        self.conn.commit()

        # Directly execute SELECT query
        cur = self.conn.cursor()
        result = cur.execute("SELECT 1 FROM civitai_prompts WHERE civitai_id = ?", ("test_id",)).fetchone()
        print("Direct SELECT query result:", result)
        self.assertIsNotNone(result, "SELECT query should return a result for existing record.")

    # Debugging: Print database content
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM civitai_prompts")
        rows = cur.fetchall()
        print("Database content:", rows)

if __name__ == "__main__":
    unittest.main()