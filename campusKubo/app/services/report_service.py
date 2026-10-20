"""
Report Service
Handles admin oversight of submitted reports.
"""

import os
import sys
# Allow importing the top-level `storage` package when running from app/ context
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from storage.db import get_connection


class ReportService:
    @staticmethod
    def get_all_reports():
        """Backward-compatible alias to get_reports with no filters."""
        return ReportService.get_reports()

    @staticmethod
    def get_reports(status: str = None, start_date: str = None, end_date: str = None, reporter_email: str = None):
        """Fetch reports with optional filtering by status, date range, and reporter email.

        Dates should be ISO strings (YYYY-MM-DD) or full timestamps.
        """
        conn = get_connection()
        cursor = conn.cursor()

        sql = [
            "SELECT r.id, r.message, r.status, r.created_at, r.user_id, u.email as reporter_email, l.address as listing_address, r.assigned_admin_id, r.assigned_at, r.assigned_note",
            "FROM reports r",
            "LEFT JOIN users u ON r.user_id = u.id",
            "LEFT JOIN listings l ON r.listing_id = l.id",
        ]

        where_clauses = []
        params = []

        if status:
            where_clauses.append("r.status = ?")
            params.append(status)
        if reporter_email:
            where_clauses.append("u.email LIKE ?")
            params.append(f"%{reporter_email}%")
        if start_date:
            where_clauses.append("r.created_at >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("r.created_at <= ?")
            params.append(end_date)

        if where_clauses:
            sql.append("WHERE " + " AND ".join(where_clauses))

        sql.append("ORDER BY r.created_at DESC")

        try:
            cursor.execute("\n".join(sql), tuple(params))
            rows = cursor.fetchall()
            reports = []
            for row in rows:
                reports.append({
                    "id": row[0],
                    "message": row[1],
                    "status": row[2],
                    "created_at": row[3],
                    "user_id": row[4],
                    "reporter_email": row[5],
                    "listing_address": row[6],
                    "assigned_admin_id": row[7],
                    "assigned_at": row[8],
                    "assigned_note": row[9],
                })
            return reports
        finally:
            conn.close()

    @staticmethod
    def update_report_status(report_id: int, new_status: str):
        """
        Updates the status of a report (e.g., Pending → Reviewed/Resolved)
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE reports
                SET status = ?
                WHERE id = ?
            """, (new_status, report_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def escalate_report(report_id: int, reason: str = None, admin_id: int = None) -> bool:
        """Mark a report as escalated and optionally record reason/admin."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            now = None
            try:
                from datetime import datetime
                now = datetime.utcnow().isoformat()
            except Exception:
                now = ""

            cursor.execute("UPDATE reports SET status = ?, assigned_at = ? WHERE id = ?;", ("escalated", now, report_id))
            conn.commit()
            ok = cursor.rowcount > 0
            # Log activity
            try:
                from services.activity_service import ActivityService
                ActivityService.log_activity(admin_id, "Report Escalated", f"Report {report_id} escalated. Reason: {reason or 'N/A'}")
            except Exception:
                pass
            return ok
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def assign_report(report_id: int, admin_id: int, note: str = None) -> bool:
        """Assign a report to an admin and record assignment note."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            from datetime import datetime
            now = datetime.utcnow().isoformat()
            cursor.execute("UPDATE reports SET assigned_admin_id = ?, assigned_at = ?, assigned_note = ?, status = ? WHERE id = ?;", (admin_id, now, note, 'assigned', report_id))
            conn.commit()
            ok = cursor.rowcount > 0
            try:
                from services.activity_service import ActivityService
                ActivityService.log_activity(admin_id, "Report Assigned", f"Assigned report {report_id}. Note: {note or ''}")
            except Exception:
                pass
            return ok
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()
