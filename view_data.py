import sqlite3

DB_NAME = "jobs.db"

def display_applications():
    """Display all job applications in a formatted table."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, company, role, status, applied_date
            FROM applications
            ORDER BY applied_date DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("No applications found.")
            return

        print("\n" + "="*80)
        print("JOB APPLICATIONS")
        print("="*80)
        print(f"{'ID':<5} {'Company':<20} {'Role':<25} {'Status':<15} {'Applied Date':<15}")
        print("-"*80)
        
        for row in rows:
            app_id, company, role, status, applied_date = row
            print(f"{app_id:<5} {company:<20} {role:<25} {status:<15} {applied_date:<15}")
        
        print("="*80)
        print(f"Total applications: {len(rows)}\n")
    except sqlite3.Error as e:
        print(f"Error retrieving applications: {e}")

if __name__ == "__main__":
    display_applications()