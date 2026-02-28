#!/usr/bin/env python3
"""Validate ESAMS CSV exports for common integrity issues.

Usage:
  python scripts/validate_data.py --data-dir templates
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

REQUIRED_FILES = {
    "students.csv": ["student_id"],
    "courses.csv": ["course_id"],
    "batches.csv": ["batch_id", "course_id"],
    "users.csv": ["user_id", "role"],
    "student_batch_map.csv": ["student_batch_id", "student_id", "batch_id"],
    "teacher_batch_map.csv": ["teacher_batch_id", "teacher_user_id", "batch_id"],
    "attendance.csv": [
        "attendance_id",
        "attendance_date",
        "batch_id",
        "student_id",
        "status",
        "marked_by_user_id",
    ],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def check_required_columns(path: Path, expected: list[str]) -> list[str]:
    with path.open(newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        if not reader.fieldnames:
            return [f"{path.name}: missing header row"]
        missing = [c for c in expected if c not in reader.fieldnames]
        return [f"{path.name}: missing columns: {', '.join(missing)}"] if missing else []


def find_duplicates(rows: list[dict[str, str]], key_fields: list[str], name: str) -> list[str]:
    keys = [tuple(row.get(k, "").strip() for k in key_fields) for row in rows]
    duplicates = [k for k, count in Counter(keys).items() if count > 1]
    if not duplicates:
        return []
    return [f"{name}: duplicate key {key_fields}={dup}" for dup in duplicates]


def validate(data_dir: Path) -> list[str]:
    errors: list[str] = []
    datasets: dict[str, list[dict[str, str]]] = {}

    for filename, columns in REQUIRED_FILES.items():
        path = data_dir / filename
        if not path.exists():
            errors.append(f"Missing required file: {filename}")
            continue
        errors.extend(check_required_columns(path, columns))
        datasets[filename] = read_csv(path)

    if errors:
        return errors

    student_ids = {r["student_id"] for r in datasets["students.csv"]}
    course_ids = {r["course_id"] for r in datasets["courses.csv"]}
    batch_ids = {r["batch_id"] for r in datasets["batches.csv"]}
    user_ids = {r["user_id"] for r in datasets["users.csv"]}
    teacher_ids = {
        r["user_id"]
        for r in datasets["users.csv"]
        if r.get("role", "").strip() == "Teacher"
    }

    errors.extend(find_duplicates(datasets["students.csv"], ["student_id"], "students.csv"))
    errors.extend(find_duplicates(datasets["courses.csv"], ["course_id"], "courses.csv"))
    errors.extend(find_duplicates(datasets["batches.csv"], ["batch_id"], "batches.csv"))
    errors.extend(find_duplicates(datasets["users.csv"], ["user_id"], "users.csv"))

    errors.extend(
        find_duplicates(
            datasets["attendance.csv"],
            ["attendance_date", "batch_id", "student_id"],
            "attendance.csv",
        )
    )

    for row in datasets["batches.csv"]:
        if row["course_id"] not in course_ids:
            errors.append(f"batches.csv: unknown course_id {row['course_id']}")

    for row in datasets["student_batch_map.csv"]:
        if row["student_id"] not in student_ids:
            errors.append(
                f"student_batch_map.csv: unknown student_id {row['student_id']}"
            )
        if row["batch_id"] not in batch_ids:
            errors.append(f"student_batch_map.csv: unknown batch_id {row['batch_id']}")

    for row in datasets["teacher_batch_map.csv"]:
        if row["teacher_user_id"] not in teacher_ids:
            errors.append(
                f"teacher_batch_map.csv: teacher_user_id is not a Teacher role: {row['teacher_user_id']}"
            )
        if row["batch_id"] not in batch_ids:
            errors.append(f"teacher_batch_map.csv: unknown batch_id {row['batch_id']}")

    for row in datasets["attendance.csv"]:
        if row["student_id"] not in student_ids:
            errors.append(f"attendance.csv: unknown student_id {row['student_id']}")
        if row["batch_id"] not in batch_ids:
            errors.append(f"attendance.csv: unknown batch_id {row['batch_id']}")
        if row["marked_by_user_id"] not in user_ids:
            errors.append(
                f"attendance.csv: unknown marked_by_user_id {row['marked_by_user_id']}"
            )
        if row["status"] not in {"Present", "Absent"}:
            errors.append(
                f"attendance.csv: invalid status '{row['status']}' (allowed: Present/Absent)"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("templates"),
        help="Directory containing ESAMS CSV files",
    )
    args = parser.parse_args()

    errors = validate(args.data_dir)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation passed for data directory: {args.data_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
