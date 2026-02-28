from __future__ import annotations

import sqlite3
from pathlib import Path

from app.esams import ESAMSDatabase


def seeded_db(tmp_path: Path) -> ESAMSDatabase:
    db_path = tmp_path / "esams.db"
    db = ESAMSDatabase(db_path)
    db.initialize()
    db.seed_from_templates("templates")
    return db


def test_monthly_percentage_and_irregular(tmp_path: Path) -> None:
    db = seeded_db(tmp_path)

    assert db.monthly_attendance_percentage("STU001", "2026-01") == 100.0
    assert db.monthly_attendance_percentage("STU002", "2026-01") == 0.0

    irregular = db.irregular_students("2026-01")
    ids = {x["student_id"] for x in irregular}
    assert "STU002" in ids


def test_prevent_duplicate_attendance_per_day_batch_student(tmp_path: Path) -> None:
    db = seeded_db(tmp_path)

    try:
        db.mark_attendance(
            attendance_id="ATT999",
            attendance_date="2026-01-20",
            batch_id="BAT001",
            student_id="STU001",
            status="Absent",
            marked_by_user_id="USR002",
        )
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("Expected duplicate attendance insert to fail")


def test_admin_teacher_student_dashboards(tmp_path: Path) -> None:
    db = seeded_db(tmp_path)

    admin = db.admin_dashboard(today="2026-01-21")
    assert admin["summary"]["total_students"] == 3
    assert admin["summary"]["today_attendance_count"] == 3
    assert len(admin["batch_attendance_chart"]) == 2

    teacher = db.teacher_dashboard("USR002", today="2026-01-21")
    assert len(teacher["assigned_batches"]) == 1
    assert teacher["assigned_batches"][0]["batch_id"] == "BAT001"
    assert len(teacher["today_pending_attendance"]) == 0

    student = db.student_detail("STU001", "2026-01")
    assert student["profile"]["student_id"] == "STU001"
    assert student["monthly_attendance_percent"] == 100.0
    assert len(student["attendance_history"]) == 2
