#!/usr/bin/env python3
"""Core ESAMS service layer using SQLite."""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass
class DashboardSummary:
    total_students: int
    total_courses: int
    total_batches: int
    active_batches: int
    today_attendance_count: int
    today_absent_count: int
    below_75_count: int


class ESAMSDatabase:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                  user_id TEXT PRIMARY KEY,
                  full_name TEXT NOT NULL,
                  email TEXT NOT NULL UNIQUE,
                  role TEXT NOT NULL CHECK (role IN ('SuperAdmin', 'Admin', 'Teacher')),
                  active_status INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS courses (
                  course_id TEXT PRIMARY KEY,
                  course_name TEXT NOT NULL,
                  description TEXT,
                  active_status INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS batches (
                  batch_id TEXT PRIMARY KEY,
                  course_id TEXT NOT NULL,
                  batch_name TEXT NOT NULL,
                  start_time TEXT,
                  end_time TEXT,
                  active_status INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (course_id) REFERENCES courses(course_id)
                );

                CREATE TABLE IF NOT EXISTS students (
                  student_id TEXT PRIMARY KEY,
                  full_name TEXT NOT NULL,
                  phone TEXT,
                  guardian_phone TEXT,
                  email TEXT,
                  admission_date TEXT,
                  joining_date TEXT,
                  active_status INTEGER NOT NULL DEFAULT 1,
                  photo_url TEXT,
                  created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS student_batch_map (
                  student_batch_id TEXT PRIMARY KEY,
                  student_id TEXT NOT NULL,
                  batch_id TEXT NOT NULL,
                  enrolled_at TEXT NOT NULL,
                  active_status INTEGER NOT NULL DEFAULT 1,
                  FOREIGN KEY (student_id) REFERENCES students(student_id),
                  FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
                  UNIQUE (student_id, batch_id)
                );

                CREATE TABLE IF NOT EXISTS teacher_batch_map (
                  teacher_batch_id TEXT PRIMARY KEY,
                  teacher_user_id TEXT NOT NULL,
                  batch_id TEXT NOT NULL,
                  assigned_at TEXT NOT NULL,
                  active_status INTEGER NOT NULL DEFAULT 1,
                  FOREIGN KEY (teacher_user_id) REFERENCES users(user_id),
                  FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
                  UNIQUE (teacher_user_id, batch_id)
                );

                CREATE TABLE IF NOT EXISTS attendance (
                  attendance_id TEXT PRIMARY KEY,
                  attendance_date TEXT NOT NULL,
                  batch_id TEXT NOT NULL,
                  student_id TEXT NOT NULL,
                  status TEXT NOT NULL CHECK (status IN ('Present', 'Absent')),
                  marked_by_user_id TEXT NOT NULL,
                  marked_at TEXT NOT NULL,
                  month_key TEXT NOT NULL,
                  notes TEXT,
                  FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
                  FOREIGN KEY (student_id) REFERENCES students(student_id),
                  FOREIGN KEY (marked_by_user_id) REFERENCES users(user_id),
                  UNIQUE (attendance_date, batch_id, student_id)
                );

                CREATE INDEX IF NOT EXISTS idx_attendance_batch_date
                  ON attendance(batch_id, attendance_date);
                CREATE INDEX IF NOT EXISTS idx_attendance_student_month
                  ON attendance(student_id, month_key);
                """
            )

    def seed_from_templates(self, template_dir: str | Path) -> None:
        template_dir = Path(template_dir)
        order = [
            "users.csv",
            "courses.csv",
            "batches.csv",
            "students.csv",
            "student_batch_map.csv",
            "teacher_batch_map.csv",
            "attendance.csv",
        ]

        with self.connect() as conn:
            for filename in order:
                path = template_dir / filename
                rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
                if not rows:
                    continue
                table = filename.removesuffix(".csv")
                columns = list(rows[0].keys())
                placeholders = ", ".join(["?" for _ in columns])
                col_sql = ", ".join(columns)
                sql = f"INSERT OR REPLACE INTO {table} ({col_sql}) VALUES ({placeholders})"
                values: Iterable[tuple[str, ...]] = [
                    tuple(row[col] for col in columns) for row in rows
                ]
                conn.executemany(sql, values)

    def mark_attendance(
        self,
        attendance_id: str,
        attendance_date: str,
        batch_id: str,
        student_id: str,
        status: str,
        marked_by_user_id: str,
        notes: str = "",
    ) -> None:
        if status not in {"Present", "Absent"}:
            raise ValueError("status must be Present or Absent")

        month_key = attendance_date[:7]
        marked_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO attendance (
                    attendance_id, attendance_date, batch_id, student_id, status,
                    marked_by_user_id, marked_at, month_key, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attendance_id,
                    attendance_date,
                    batch_id,
                    student_id,
                    status,
                    marked_by_user_id,
                    marked_at,
                    month_key,
                    notes,
                ),
            )

    def monthly_attendance_percentage(self, student_id: str, month_key: str) -> float:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present_count,
                    COUNT(*) AS total_count
                FROM attendance
                WHERE student_id = ? AND month_key = ?
                """,
                (student_id, month_key),
            ).fetchone()

        total = row["total_count"] or 0
        present = row["present_count"] or 0
        if total == 0:
            return 0.0
        return round((present / total) * 100, 2)

    def irregular_students(self, month_key: str, threshold: float = 75.0) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    s.student_id,
                    s.full_name,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
                    COUNT(*) AS total_count
                FROM students s
                JOIN attendance a ON a.student_id = s.student_id
                WHERE a.month_key = ?
                GROUP BY s.student_id, s.full_name
                HAVING COUNT(*) > 0
                """,
                (month_key,),
            ).fetchall()

        out = []
        for row in rows:
            percent = round((row["present_count"] / row["total_count"]) * 100, 2)
            if percent < threshold:
                out.append(
                    {
                        "student_id": row["student_id"],
                        "full_name": row["full_name"],
                        "attendance_percent": percent,
                    }
                )
        return out

    def batch_attendance_chart(self, month_key: str) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    b.batch_id,
                    b.batch_name,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
                    SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
                    COUNT(*) AS total_count
                FROM batches b
                LEFT JOIN attendance a ON a.batch_id = b.batch_id AND a.month_key = ?
                GROUP BY b.batch_id, b.batch_name
                ORDER BY b.batch_id
                """,
                (month_key,),
            ).fetchall()

        chart: list[dict] = []
        for row in rows:
            total = row["total_count"] or 0
            present = row["present_count"] or 0
            absent = row["absent_count"] or 0
            percent = round((present / total) * 100, 2) if total else 0.0
            chart.append(
                {
                    "batch_id": row["batch_id"],
                    "batch_name": row["batch_name"],
                    "present_count": present,
                    "absent_count": absent,
                    "attendance_percent": percent,
                }
            )
        return chart

    def dashboard_summary(self, today: str) -> DashboardSummary:
        month_key = today[:7]
        with self.connect() as conn:
            total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            total_courses = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
            total_batches = conn.execute("SELECT COUNT(*) FROM batches").fetchone()[0]
            active_batches = conn.execute(
                "SELECT COUNT(*) FROM batches WHERE active_status = 1"
            ).fetchone()[0]
            today_attendance_count = conn.execute(
                "SELECT COUNT(*) FROM attendance WHERE attendance_date = ?", (today,)
            ).fetchone()[0]
            today_absent_count = conn.execute(
                "SELECT COUNT(*) FROM attendance WHERE attendance_date = ? AND status = 'Absent'",
                (today,),
            ).fetchone()[0]

        below_75_count = len(self.irregular_students(month_key=month_key, threshold=75.0))
        return DashboardSummary(
            total_students=total_students,
            total_courses=total_courses,
            total_batches=total_batches,
            active_batches=active_batches,
            today_attendance_count=today_attendance_count,
            today_absent_count=today_absent_count,
            below_75_count=below_75_count,
        )

    def admin_dashboard(self, today: str) -> dict:
        summary = self.dashboard_summary(today)
        month_key = today[:7]
        return {
            "summary": asdict(summary),
            "below_75_students": self.irregular_students(month_key),
            "batch_attendance_chart": self.batch_attendance_chart(month_key),
        }

    def teacher_dashboard(self, teacher_user_id: str, today: str) -> dict:
        month_key = today[:7]
        with self.connect() as conn:
            assigned_batches = conn.execute(
                """
                SELECT b.batch_id, b.batch_name
                FROM teacher_batch_map tb
                JOIN batches b ON b.batch_id = tb.batch_id
                WHERE tb.teacher_user_id = ? AND tb.active_status = 1
                ORDER BY b.batch_id
                """,
                (teacher_user_id,),
            ).fetchall()

            pending = conn.execute(
                """
                SELECT b.batch_id, b.batch_name
                FROM teacher_batch_map tb
                JOIN batches b ON b.batch_id = tb.batch_id
                WHERE tb.teacher_user_id = ?
                AND NOT EXISTS (
                  SELECT 1 FROM attendance a
                  WHERE a.batch_id = b.batch_id
                  AND a.attendance_date = ?
                )
                ORDER BY b.batch_id
                """,
                (teacher_user_id, today),
            ).fetchall()

            my_students = conn.execute(
                """
                SELECT DISTINCT s.student_id, s.full_name
                FROM teacher_batch_map tb
                JOIN student_batch_map sb ON sb.batch_id = tb.batch_id AND sb.active_status = 1
                JOIN students s ON s.student_id = sb.student_id
                WHERE tb.teacher_user_id = ? AND tb.active_status = 1
                ORDER BY s.student_id
                """,
                (teacher_user_id,),
            ).fetchall()

        irregular = [
            s for s in self.irregular_students(month_key) if s["student_id"] in {x["student_id"] for x in my_students}
        ]

        return {
            "assigned_batches": [dict(row) for row in assigned_batches],
            "today_pending_attendance": [dict(row) for row in pending],
            "my_students": [dict(row) for row in my_students],
            "irregular_students": irregular,
        }

    def student_detail(self, student_id: str, month_key: str) -> dict:
        with self.connect() as conn:
            student = conn.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if student is None:
                raise ValueError(f"Unknown student_id: {student_id}")

            batches = conn.execute(
                """
                SELECT b.batch_id, b.batch_name, c.course_name
                FROM student_batch_map sb
                JOIN batches b ON b.batch_id = sb.batch_id
                JOIN courses c ON c.course_id = b.course_id
                WHERE sb.student_id = ? AND sb.active_status = 1
                ORDER BY b.batch_id
                """,
                (student_id,),
            ).fetchall()

            attendance_rows = conn.execute(
                """
                SELECT attendance_date, batch_id, status, marked_by_user_id, marked_at, notes
                FROM attendance
                WHERE student_id = ? AND month_key = ?
                ORDER BY attendance_date, batch_id
                """,
                (student_id, month_key),
            ).fetchall()

        return {
            "profile": dict(student),
            "enrolled_batches": [dict(row) for row in batches],
            "monthly_attendance_percent": self.monthly_attendance_percentage(student_id, month_key),
            "attendance_history": [dict(row) for row in attendance_rows],
        }
