#!/usr/bin/env python3
"""ESAMS command-line runner."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.esams import ESAMSDatabase


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ESAMS local workflow")
    parser.add_argument("--db", default="esams.db", help="SQLite database path")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Create ESAMS schema in SQLite")

    seed = sub.add_parser("seed", help="Seed SQLite DB from template CSV directory")
    seed.add_argument("--templates", default="templates", help="CSV template directory")

    mark = sub.add_parser("mark-attendance", help="Insert one attendance record")
    mark.add_argument("--attendance-id", required=True)
    mark.add_argument("--date", required=True, help="YYYY-MM-DD")
    mark.add_argument("--batch-id", required=True)
    mark.add_argument("--student-id", required=True)
    mark.add_argument("--status", required=True, choices=["Present", "Absent"])
    mark.add_argument("--marked-by", required=True)
    mark.add_argument("--notes", default="")

    monthly = sub.add_parser("monthly-percent", help="Compute monthly attendance %")
    monthly.add_argument("--student-id", required=True)
    monthly.add_argument("--month", required=True, help="YYYY-MM")

    irregular = sub.add_parser("irregular", help="List students below threshold")
    irregular.add_argument("--month", required=True, help="YYYY-MM")
    irregular.add_argument("--threshold", type=float, default=75.0)

    dash = sub.add_parser("dashboard", help="Compute basic dashboard summary")
    dash.add_argument("--today", required=True, help="YYYY-MM-DD")

    admin = sub.add_parser("admin-dashboard", help="Get full admin dashboard payload")
    admin.add_argument("--today", required=True, help="YYYY-MM-DD")

    teacher = sub.add_parser("teacher-dashboard", help="Get full teacher dashboard payload")
    teacher.add_argument("--teacher-user-id", required=True)
    teacher.add_argument("--today", required=True, help="YYYY-MM-DD")

    student = sub.add_parser("student-detail", help="Get student profile and attendance detail")
    student.add_argument("--student-id", required=True)
    student.add_argument("--month", required=True, help="YYYY-MM")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    db = ESAMSDatabase(args.db)

    if args.command == "init-db":
        db.initialize()
        print(f"Initialized ESAMS database at {args.db}")
        return 0

    if args.command == "seed":
        db.seed_from_templates(args.templates)
        print(f"Seeded database from {args.templates}")
        return 0

    if args.command == "mark-attendance":
        db.mark_attendance(
            attendance_id=args.attendance_id,
            attendance_date=args.date,
            batch_id=args.batch_id,
            student_id=args.student_id,
            status=args.status,
            marked_by_user_id=args.marked_by,
            notes=args.notes,
        )
        print("Attendance marked successfully")
        return 0

    if args.command == "monthly-percent":
        percent = db.monthly_attendance_percentage(
            student_id=args.student_id,
            month_key=args.month,
        )
        print(f"{args.student_id} monthly attendance ({args.month}): {percent}%")
        return 0

    if args.command == "irregular":
        students = db.irregular_students(month_key=args.month, threshold=args.threshold)
        print(json.dumps(students, indent=2))
        return 0

    if args.command == "dashboard":
        summary = db.dashboard_summary(today=args.today)
        print(json.dumps(asdict(summary), indent=2))
        return 0

    if args.command == "admin-dashboard":
        print(json.dumps(db.admin_dashboard(today=args.today), indent=2))
        return 0

    if args.command == "teacher-dashboard":
        print(
            json.dumps(
                db.teacher_dashboard(teacher_user_id=args.teacher_user_id, today=args.today),
                indent=2,
            )
        )
        return 0

    if args.command == "student-detail":
        print(
            json.dumps(
                db.student_detail(student_id=args.student_id, month_key=args.month),
                indent=2,
            )
        )
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
