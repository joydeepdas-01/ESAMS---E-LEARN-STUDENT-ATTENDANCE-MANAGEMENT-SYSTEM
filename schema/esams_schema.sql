-- ESAMS relational reference schema
-- This schema is provided as a blueprint for data normalization and validation.

CREATE TABLE users (
  user_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  role TEXT NOT NULL CHECK (role IN ('SuperAdmin', 'Admin', 'Teacher')),
  active_status INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE courses (
  course_id TEXT PRIMARY KEY,
  course_name TEXT NOT NULL,
  description TEXT,
  active_status INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE batches (
  batch_id TEXT PRIMARY KEY,
  course_id TEXT NOT NULL,
  batch_name TEXT NOT NULL,
  start_time TEXT,
  end_time TEXT,
  active_status INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE students (
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

CREATE TABLE student_batch_map (
  student_batch_id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  batch_id TEXT NOT NULL,
  enrolled_at TEXT NOT NULL,
  active_status INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (student_id) REFERENCES students(student_id),
  FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
  UNIQUE (student_id, batch_id)
);

CREATE TABLE teacher_batch_map (
  teacher_batch_id TEXT PRIMARY KEY,
  teacher_user_id TEXT NOT NULL,
  batch_id TEXT NOT NULL,
  assigned_at TEXT NOT NULL,
  active_status INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (teacher_user_id) REFERENCES users(user_id),
  FOREIGN KEY (batch_id) REFERENCES batches(batch_id),
  UNIQUE (teacher_user_id, batch_id)
);

CREATE TABLE attendance (
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

CREATE INDEX idx_attendance_batch_date ON attendance(batch_id, attendance_date);
CREATE INDEX idx_attendance_student_month ON attendance(student_id, month_key);
