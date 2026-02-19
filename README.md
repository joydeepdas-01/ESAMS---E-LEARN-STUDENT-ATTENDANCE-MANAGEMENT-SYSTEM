# ESAMS on Google Sheets + Google Drive + Apps Script

This repository contains a production-ready starter for building **E-Learn Student Attendance Management System (ESAMS)** using:
- **Google Sheets** as the database
- **Google Apps Script** as the backend + web app
- **Google Drive** for report exports and monthly archives

## 1) Data model (Google Sheets tabs)
Create a Google Sheet and add these tabs:

1. `Users`
   - `email`, `name`, `role`, `assignedBatches` (comma-separated)
   - roles: `SUPER_ADMIN`, `ADMIN`, `TEACHER`

2. `Students`
   - `studentId`, `fullName`, `batchId`, `guardianPhone`, `active`

3. `Attendance`
   - `attendanceId`, `date`, `batchId`, `studentId`, `status`, `markedAt`, `markedBy`, `monthKey`, `updatedAt`

4. `Batches`
   - `batchId`, `batchName`, `active`

5. `Settings`
   - `key`, `value`
   - add at least:
     - `EDIT_LOCK_HOURS` = `8`
     - `ALERT_THRESHOLD_PERCENT` = `75`

6. `AuditLog`
   - `timestamp`, `action`, `actorEmail`, `detailsJson`

7. `DailySummary`
   - `date`, `batchId`, `presentCount`, `absentCount`, `updatedAt`

## 2) Deploy
1. Open Apps Script from the target Google Sheet.
2. Add files from this repo:
   - `appsscript.json`
   - `Code.gs`
   - `Dashboard.html`
3. Update `SPREADSHEET_ID` in `Code.gs`.
4. Deploy as **Web app**:
   - Execute as: **User accessing the app**
   - Access: your organization as needed.

## 3) Implemented feature mapping

### Attendance Core
- Batch-wise student loading with role access control.
- One-click Present/Absent toggles in mobile-friendly table.
- Auto date/time + actor email tracking.
- Duplicate prevention (same day + student + batch upsert).

### Smart Rules
- Monthly and overall attendance %.
- Below 75% warning list.
- 2/3 consecutive absence detection.
- Monthly archive to Drive as CSV + optional PDF conversion hook.

### Dashboards
- Admin dashboard: totals, today summary, irregular list, below-threshold list.
- Teacher dashboard: assigned batches, pending mark status, irregular list.

### Security & Control
- Role-based login by Google account email.
- Teacher can see assigned batches only.
- Edit lock by hours with Admin/Super Admin override.

### Export & Reports
- Batch-wise monthly CSV export to Drive.
- Student individual summary object for certificate/report generation.

## 4) Extend next
- SMS/Call integration through Twilio/Banglalink APIs.
- PWA service worker and offline local queue.
- QR attendance scan endpoint.
- Late/Half-day/Leave statuses.

## 5) Notes
- This starter is optimized for quick MVP launch.
- For 10k+ rows, move aggregation to cached summary tables and time-driven jobs.
