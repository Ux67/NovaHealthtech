"""
Nova Healthtech - SQLite Database Layer (Production Ready)
Supports custom persistent volume mount paths via DATABASE_PATH environment variable.
Enforces read-only prescribed dosages and zero-PII storage of sensitive government identifiers.
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Supports persistent volume mounts (e.g. /data/nova_health.db in Docker/Render/AWS)
DEFAULT_LOCAL_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "nova_health.db"))
DB_PATH = os.getenv("DATABASE_PATH", DEFAULT_LOCAL_DB)


def get_db_connection() -> sqlite3.Connection:
    """Creates a thread-safe connection to the SQLite database."""
    # Ensure target parent directory exists if using a custom mount directory
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes tables and indexes for Doctor Consultations and Medication Schedules."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Doctor Consultation Requests Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS consultation_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                contact_number TEXT NOT NULL,
                district TEXT NOT NULL,
                preferred_language TEXT NOT NULL DEFAULT 'en',
                symptoms_summary TEXT NOT NULL,
                urgency_level TEXT NOT NULL DEFAULT 'ROUTINE',
                consent_given INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'PENDING_DOCTOR_ASSIGNMENT',
                created_at_utc TEXT NOT NULL
            );
            """
        )

        # 2. Safe Medication Adherence Reminders Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS medication_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_name TEXT NOT NULL,
                prescribed_dosage TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                meal_relation TEXT NOT NULL DEFAULT 'after_food',
                doctor_prescribed_confirmed INTEGER NOT NULL DEFAULT 1,
                notes TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                last_taken_at_utc TEXT,
                created_at_utc TEXT NOT NULL
            );
            """
        )

        # Optimization indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_consult_status ON consultation_requests(status);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_med_active ON medication_reminders(is_active);"
        )

        conn.commit()


# =====================================================================
# DOCTOR CONSULTATION REPOSITORY
# =====================================================================

def create_consultation_request(
    patient_name: str,
    contact_number: str,
    district: str,
    preferred_language: str,
    symptoms_summary: str,
    urgency_level: str = "ROUTINE",
) -> int:
    """Inserts a new doctor consultation request."""
    now_utc = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO consultation_requests (
                patient_name, contact_number, district, preferred_language,
                symptoms_summary, urgency_level, consent_given, status, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, 1, 'PENDING_DOCTOR_ASSIGNMENT', ?)
            """,
            (
                patient_name.strip(),
                contact_number.strip(),
                district.strip(),
                preferred_language.strip(),
                symptoms_summary.strip(),
                urgency_level.strip(),
                now_utc,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_recent_consultations(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves recent consultation requests with masked contact numbers for privacy."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, patient_name, contact_number, district, preferred_language,
                   symptoms_summary, urgency_level, status, created_at_utc
            FROM consultation_requests
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        results = []
        for row in rows:
            raw_contact = row["contact_number"]
            masked_contact = (
                raw_contact[:2] + "******" + raw_contact[-2:]
                if len(raw_contact) >= 8
                else "******"
            )
            results.append(
                {
                    "id": row["id"],
                    "patient_name": row["patient_name"],
                    "contact_masked": masked_contact,
                    "district": row["district"],
                    "preferred_language": row["preferred_language"],
                    "symptoms_summary": row["symptoms_summary"],
                    "urgency_level": row["urgency_level"],
                    "status": row["status"],
                    "created_at_utc": row["created_at_utc"],
                }
            )
        return results


# =====================================================================
# SAFE MEDICATION ADHERENCE REMINDERS REPOSITORY
# =====================================================================

def create_medication_reminder(
    medicine_name: str,
    prescribed_dosage: str,
    scheduled_time: str,
    meal_relation: str,
    doctor_prescribed_confirmed: bool,
    notes: Optional[str] = "",
) -> int:
    """Creates a medication reminder strictly adhering to doctor prescriptions."""
    if not doctor_prescribed_confirmed:
        raise ValueError("Safety Violation: Reminders require verified doctor prescription confirmation.")

    now_utc = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO medication_reminders (
                medicine_name, prescribed_dosage, scheduled_time, meal_relation,
                doctor_prescribed_confirmed, notes, is_active, created_at_utc
            ) VALUES (?, ?, ?, ?, 1, ?, 1, ?)
            """,
            (
                medicine_name.strip(),
                prescribed_dosage.strip(),
                scheduled_time.strip(),
                meal_relation.strip(),
                notes.strip() if notes else "",
                now_utc,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_active_medication_reminders() -> List[Dict[str, Any]]:
    """Retrieves all active prescribed medication reminders."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, medicine_name, prescribed_dosage, scheduled_time,
                   meal_relation, doctor_prescribed_confirmed, notes, is_active,
                   last_taken_at_utc, created_at_utc
            FROM medication_reminders
            WHERE is_active = 1
            ORDER BY scheduled_time ASC
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def log_medication_taken(reminder_id: int) -> bool:
    """Logs the exact timestamp a dose was marked as taken."""
    now_utc = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE medication_reminders
            SET last_taken_at_utc = ?
            WHERE id = ?
            """,
            (now_utc, reminder_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_medication_reminder(reminder_id: int) -> bool:
    """Deletes or archives a medication reminder schedule."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM medication_reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        return cursor.rowcount > 0