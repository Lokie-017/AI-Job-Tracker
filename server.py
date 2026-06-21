import sqlite3
from datetime import date
from typing import Any, Dict, List

from database import get_db_connection, initialize_database, VALID_STATUSES
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Learning MCP")


def _validate_nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def _validate_positive_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _rows_to_dicts(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [dict(row) for row in rows]


@mcp.tool()
def hello(name: str) -> str:
    """Say hello to someone."""
    try:
        name = _validate_nonempty_string(name, "name")
    except ValueError as exc:
        return {"error": str(exc)}
    return f"Hello {name}!"





@mcp.tool()
def add_application(company: str, role: str) -> str:
    """Add a job application."""
    try:
        company = _validate_nonempty_string(company, "company")
        role = _validate_nonempty_string(role, "role")
    except ValueError as exc:
        return {"error": str(exc)}

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            today = date.today().isoformat()
            cursor.execute(
                """
                INSERT INTO applications
                (company, role, status, applied_date)
                VALUES (?, ?, ?, ?)
                """,
                (company, role, "Applied", today),
            )
            conn.commit()
        return f"Added application: {company} - {role}"
    except sqlite3.Error as e:
        return {"error": f"Error adding application: {e}"}

@mcp.tool()
def list_applications() -> list:
    """List all job applications."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, company, role, status, applied_date
                FROM applications
                ORDER BY applied_date DESC
            """)
            rows = cursor.fetchall()
        return _rows_to_dicts(rows)
    except sqlite3.Error as e:
        return {"error": f"Failed to retrieve applications: {e}"}


@mcp.tool()
def update_status(application_id: int, status: str) -> str:
    """Update the status of a job application."""
    try:
        application_id = _validate_positive_int(application_id, "application_id")
    except ValueError as exc:
        return {"error": str(exc)}

    if status not in VALID_STATUSES:
        return {"error": f"Invalid status. Use one of: {', '.join(VALID_STATUSES)}"}

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE applications SET status = ? WHERE id = ?",
                (status, application_id),
            )
            if cursor.rowcount == 0:
                return {"error": f"Application with ID {application_id} not found."}
            conn.commit()
        return f"Application {application_id} updated to {status}"
    except sqlite3.Error as e:
        return {"error": f"Error updating application: {e}"}

@mcp.tool()
def application_summary() -> dict:
    """Get application statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM applications")
            total = cursor.fetchone()[0]
            summary = {"total": total}
            for status in VALID_STATUSES:
                cursor.execute(
                    "SELECT COUNT(*) FROM applications WHERE status = ?",
                    (status,),
                )
                summary[status.lower()] = cursor.fetchone()[0]
        return summary
    except sqlite3.Error as e:
        return {"error": f"Failed to retrieve summary: {e}"}

@mcp.tool()
def pending_followups(days_threshold: int = 7) -> list:
    """Find applications needing follow-up.
    
    Args:
        days_threshold: Number of days after which to flag as needing follow-up (default: 7)
    """
    try:
        days_threshold = _validate_positive_int(days_threshold, "days_threshold")
    except ValueError as exc:
        return {"error": str(exc)}

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, company, role, applied_date
                FROM applications
                WHERE status = 'Applied'
                ORDER BY applied_date ASC
            """)
            rows = cursor.fetchall()

        followups = []
        today = date.today()
        for row in rows:
            app_id, company, role, applied_date = row
            try:
                applied = date.fromisoformat(applied_date)
                days_old = (today - applied).days
                if days_old > days_threshold:
                    followups.append({
                        "id": app_id,
                        "company": company,
                        "role": role,
                        "days_old": days_old,
                    })
            except ValueError:
                continue

        return followups
    except sqlite3.Error as e:
        return {"error": f"Failed to retrieve pending followups: {e}"}


@mcp.tool()
def get_application_by_company(company: str) -> list:
    """Get all applications for a specific company."""
    try:
        company = _validate_nonempty_string(company, "company")
    except ValueError as exc:
        return {"error": str(exc)}

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, company, role, status, applied_date
                FROM applications
                WHERE company LIKE ?
                ORDER BY applied_date DESC
            """, (f"%{company}%",))
            rows = cursor.fetchall()
        return _rows_to_dicts(rows)
    except sqlite3.Error as e:
        return {"error": f"Failed to retrieve applications: {e}"}


@mcp.tool()
def delete_application(id: int) -> str:
    """Delete a job application by ID."""
    try:
        application_id = _validate_positive_int(id, "id")
    except ValueError as exc:
        return {"error": str(exc)}

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM applications WHERE id = ?",
                (application_id,),
            )
            if cursor.rowcount == 0:
                return {"error": f"Application with ID {application_id} not found."}
            conn.commit()
        return f"Application {application_id} deleted successfully."
    except sqlite3.Error as e:
        return {"error": f"Error deleting application: {e}"}


@mcp.tool()
def search_applications(status: str) -> list:
    """Search applications by status."""
    try:
        status = _validate_nonempty_string(status, "status")
    except ValueError as exc:
        return {"error": str(exc)}

    if status not in VALID_STATUSES:
        return {"error": f"Invalid status. Use one of: {', '.join(VALID_STATUSES)}"}

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, company, role, status, applied_date
                FROM applications
                WHERE status = ?
                ORDER BY applied_date DESC
            """, (status,))
            rows = cursor.fetchall()
        return _rows_to_dicts(rows)
    except sqlite3.Error as e:
        return {"error": f"Failed to search applications: {e}"}


if __name__ == "__main__":
    initialize_database()
    mcp.run()