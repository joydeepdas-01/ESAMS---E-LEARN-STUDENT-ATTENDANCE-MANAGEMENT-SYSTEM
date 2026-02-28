# ESAMS

**E-Learn Student Attendance Management System**

---

## REPOSITORY STARTER KIT

This repository now includes an initial implementation package to help you start ESAMS configuration immediately:

- `schema/esams_schema.sql`: relational reference schema for normalized table design.
- `templates/*.csv`: ready-to-import starter CSV files for all core tables.
- `scripts/validate_data.py`: integrity checker for CSV exports/imports (duplicate detection, FK checks, role validation, status validation).

### Quick Start

1. Review `schema/esams_schema.sql` and align your Google Sheets/AppSheet columns.
2. Use files under `templates/` as initial seed format for each sheet.
3. Run validation locally before importing data:

```bash
python scripts/validate_data.py --data-dir templates
```

---

## LOCAL WORKING IMPLEMENTATION

A runnable local implementation is included using SQLite so ESAMS can be executed end-to-end in development:

- `app/esams.py`: core data/service layer (schema init, seeding, attendance marking, analytics).
- `scripts/run_esams.py`: CLI for operational flows.
- `tests/test_esams.py`: integration-style tests for core behavior.

### Run Locally

```bash
python scripts/run_esams.py --db esams.db init-db
python scripts/run_esams.py --db esams.db seed --templates templates
python scripts/run_esams.py --db esams.db dashboard --today 2026-01-20
python scripts/run_esams.py --db esams.db admin-dashboard --today 2026-01-21
python scripts/run_esams.py --db esams.db teacher-dashboard --teacher-user-id USR002 --today 2026-01-21
python scripts/run_esams.py --db esams.db student-detail --student-id STU001 --month 2026-01
python scripts/run_esams.py --db esams.db monthly-percent --student-id STU001 --month 2026-01
```

Dashboard payloads now include:
- Admin: summary cards, below-75 list, and batch-wise attendance chart data.
- Teacher: assigned batches, today pending attendance, my students, irregular students.
- Student detail: profile, enrolled batches, month-wise percentage, attendance history.

---

## ABOUT ESAMS

ESAMS is a structured, role-based academic management application built using Google Sheets as database and AppSheet as application layer.

It is designed for:

- Coaching centres
- Private tuition institutes
- Schools
- Training academies
- Skill development centres

The system manages:

- Students
- Courses
- Batches
- Teachers
- Attendance
- Performance tracking

It supports many-to-many relationships:

- One student can join multiple batches
- One teacher can teach multiple batches
- One course can have multiple batches

The system is scalable, secure, and mobile-friendly.

---

## CORE OBJECTIVES

1. Digitize attendance completely
2. Remove manual registers
3. Provide real-time attendance monitoring
4. Enable role-based control
5. Automate reporting and analytics
6. Prevent duplicate and incorrect records

---

## SYSTEM ARCHITECTURE

- **Backend:** Google Sheets
- **Frontend & Logic:** AppSheet
- **Authentication:** Google Sign-in
- **Data Structure:** Normalized relational structure

### Main Tables

- Students
- Courses
- Batches
- StudentBatchMap
- TeacherBatchMap
- Attendance
- Users

---

## FULL FEATURE LIST

### 1. STUDENT MANAGEMENT

- Add new student from app
- Upload student photo
- Store student phone and guardian phone
- Email storage (optional)
- Date of admission tracking
- Date of joining tracking
- Active / inactive status control
- Multiple batch enrollment
- Batch transfer facility
- Soft delete via deactivate option

---

### 2. COURSE MANAGEMENT

- Create unlimited courses
- Enable / disable course
- View related batches
- Central course structure

---

### 3. BATCH MANAGEMENT

- Multiple batches per course
- Batch timing management
- Assign multiple teachers to batch
- Activate / deactivate batch
- View enrolled students
- View attendance history

---

### 4. TEACHER MANAGEMENT

- Teacher role login
- Assign multiple batches
- Remove batch assignment
- Track teacher activity
- Attendance marked-by tracking

---

### 5. ATTENDANCE SYSTEM

- Batch-wise attendance
- Auto date capture
- Auto time capture
- One-click Present / Absent
- Prevent duplicate marking
- Attendance editing window
- Admin override facility
- Real-time attendance logging
- Monthly cycle separation
- Audit trail tracking

---

### 6. SMART RULE ENGINE

- Monthly attendance percentage calculation
- Overall attendance percentage
- Below 75 percent detection
- Automatic highlight of irregular students
- Consecutive absence detection
- Warning level classification
- Alert system

---

### 7. DASHBOARD FEATURES

#### Admin Dashboard

- Total students
- Total courses
- Total batches
- Active batches
- Today attendance count
- Absent count
- Below 75 percent list
- Batch-wise attendance chart

#### Teacher Dashboard

- Assigned batches
- Today pending attendance
- My students
- Irregular students

---

### 8. STUDENT DETAIL VIEW

- Profile page with photo
- Enrolled batches list
- Attendance history
- Calendar style view
- Monthly percentage display

---

### 9. ROLE-BASED SECURITY

#### Roles

- SuperAdmin
- Admin
- Teacher

#### Capabilities

- **SuperAdmin** → Full system control
- **Admin** → Data management control
- **Teacher** → Limited batch-based access

Security filters ensure:

- Teacher sees only assigned batch students
- Teacher cannot access other batch data
- Only admin can delete master records

---

### 10. DATA INTEGRITY FEATURES

- Unique ID enforcement
- Ref-based relational linking
- Duplicate attendance prevention
- Soft delete strategy
- ActiveStatus filtering
- Controlled edit permissions

---

### 11. EXPORT & REPORTING

- Monthly attendance PDF export
- Batch-wise attendance sheet
- Excel data export
- Printable reports
- Parent communication ready format

---

### 12. SCALABILITY

Supports:

- 100+ students easily
- 500+ students with optimized structure
- 1000+ students with performance tuning

Many-to-many architecture prevents duplication and ensures clean expansion.

---

## WORKFLOW SUMMARY

1. Admin creates course
2. Admin creates batches under course
3. Admin assigns teachers to batches
4. Admin adds students
5. Admin enrolls students to batches
6. Teacher logs in
7. Teacher selects batch
8. Teacher marks attendance
9. System calculates percentages
10. Dashboard updates automatically

---

## ADVANTAGES OF ESAMS

- Paperless system
- Real-time monitoring
- Reduced manual errors
- Structured academic data
- Mobile-ready interface
- Scalable architecture
- Audit-based control
- Centralized management

---

## LIMITATIONS

- Dependent on Google ecosystem
- Requires internet connection
- Performance depends on sheet size
- Advanced automation requires proper configuration

---

## FUTURE EXPANSION POSSIBILITY

- Fee management module
- Exam marks module
- Performance analytics
- SMS integration
- Parent login system
- Biometric integration
- QR attendance
- AI-based irregular detection

---

## SHORT APP DESCRIPTION (FOR DOCUMENTATION)

ESAMS is a role-based, scalable student attendance and batch management system designed for academic institutions. It provides structured student enrollment, multi-batch handling, teacher assignment, automated attendance calculation, irregularity detection, and real-time dashboards using a relational architecture built on Google Sheets and AppSheet.
