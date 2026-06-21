import sqlite3
from pathlib import Path

DB_NAME = Path(__file__).resolve().parent / "jobs.db"
VALID_STATUSES = ["Applied", "Shortlisted", "Interview", "Offer", "Rejected"]

def get_db_connection():
    """Return a SQLite connection with row access enabled."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Initialize the database schema."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'Applied' CHECK(status IN ('Applied', 'Shortlisted', 'Interview', 'Offer', 'Rejected')),
            applied_date TEXT NOT NULL
        )
        """)

        # Create index on status for faster queries
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status ON applications(status)
        """)

        conn.commit()
        conn.close()
        print(f"Database '{DB_NAME}' initialized successfully!")
        return True
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    initialize_database()