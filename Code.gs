const SPREADSHEET_ID = 'REPLACE_WITH_YOUR_SPREADSHEET_ID';
const SHEETS = {
  USERS: 'Users',
  STUDENTS: 'Students',
  ATTENDANCE: 'Attendance',
  BATCHES: 'Batches',
  SETTINGS: 'Settings',
  AUDIT: 'AuditLog',
  DAILY_SUMMARY: 'DailySummary'
};

function doGet() {
  return HtmlService.createTemplateFromFile('Dashboard')
    .evaluate()
    .setTitle('ESAMS')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

function getCurrentUserContext() {
  const email = Session.getActiveUser().getEmail();
  const users = getTableObjects_(SHEETS.USERS);
  const user = users.find((u) => normalize_(u.email) === normalize_(email));
  if (!user) throw new Error('User is not configured in Users sheet.');

  return {
    email,
    name: user.name,
    role: user.role,
    assignedBatches: splitCsv_(user.assignedBatches)
  };
}

function getDashboardData() {
  const user = getCurrentUserContext();
  const students = getVisibleStudents_(user);
  const attendance = getTableObjects_(SHEETS.ATTENDANCE);
  const today = dateKey_(new Date());

  const todayRows = attendance.filter((a) => a.date === today && batchAllowed_(user, a.batchId));
  const presentCount = todayRows.filter((r) => r.status === 'P').length;
  const absentCount = todayRows.filter((r) => r.status === 'A').length;

  const stats = computeAttendanceStats_(students, attendance);
  const threshold = Number(getSetting_('ALERT_THRESHOLD_PERCENT', '75'));
  const belowThreshold = stats.filter((s) => s.overallPercent < threshold);
  const irregular = stats.filter((s) => s.consecutiveAbsent >= 2);

  return {
    user,
    totalStudents: students.length,
    todayAttendanceCount: todayRows.length,
    presentCount,
    absentCount,
    belowThreshold,
    irregular,
    batches: getVisibleBatches_(user)
  };
}

function getStudentsByBatch(batchId) {
  const user = getCurrentUserContext();
  if (!batchAllowed_(user, batchId)) throw new Error('Access denied for this batch.');

  const students = getTableObjects_(SHEETS.STUDENTS)
    .filter((s) => s.batchId === batchId && String(s.active).toUpperCase() !== 'FALSE')
    .map((s) => ({
      studentId: s.studentId,
      fullName: s.fullName,
      guardianPhone: s.guardianPhone,
      batchId: s.batchId
    }));

  return students;
}

function markAttendance(payload) {
  const user = getCurrentUserContext();
  const now = new Date();
  const date = payload.date || dateKey_(now);
  const batchId = payload.batchId;

  if (!batchAllowed_(user, batchId)) throw new Error('Access denied for this batch.');
  enforceEditLock_(user, date);

  const sh = sheet_(SHEETS.ATTENDANCE);
  const headers = getHeaders_(sh);
  const rows = getTableObjects_(SHEETS.ATTENDANCE);
  const rowByKey = {};

  rows.forEach((r, i) => {
    rowByKey[`${r.date}|${r.batchId}|${r.studentId}`] = i + 2;
  });

  payload.records.forEach((rec) => {
    const key = `${date}|${batchId}|${rec.studentId}`;
    const attendanceId = Utilities.getUuid();
    const values = {
      attendanceId,
      date,
      batchId,
      studentId: rec.studentId,
      status: rec.status,
      markedAt: now.toISOString(),
      markedBy: user.email,
      monthKey: date.slice(0, 7),
      updatedAt: now.toISOString()
    };

    if (rowByKey[key]) {
      writeRowByHeaders_(sh, headers, rowByKey[key], values, true);
    } else {
      appendByHeaders_(sh, headers, values);
    }
  });

  recalculateDailySummary_(date, batchId);
  audit_('MARK_ATTENDANCE', user.email, { date, batchId, count: payload.records.length });
  return { ok: true };
}

function getStudentReport(studentId) {
  const user = getCurrentUserContext();
  const student = getTableObjects_(SHEETS.STUDENTS).find((s) => s.studentId === studentId);
  if (!student) throw new Error('Student not found');
  if (!batchAllowed_(user, student.batchId)) throw new Error('Access denied');

  const attendance = getTableObjects_(SHEETS.ATTENDANCE).filter((a) => a.studentId === studentId);
  const monthly = {};
  attendance.forEach((a) => {
    const k = a.monthKey || String(a.date).slice(0, 7);
    if (!monthly[k]) monthly[k] = { present: 0, absent: 0, total: 0 };
    monthly[k].total++;
    if (a.status === 'P') monthly[k].present++;
    else monthly[k].absent++;
  });

  return { student, monthly, total: attendance.length };
}

function runMonthlyArchive(monthKey, driveFolderId) {
  const rows = getTableObjects_(SHEETS.ATTENDANCE).filter((r) => r.monthKey === monthKey);
  const csv = toCsv_(rows);
  const folder = DriveApp.getFolderById(driveFolderId);
  folder.createFile(`attendance_${monthKey}.csv`, csv, MimeType.CSV);

  audit_('MONTHLY_ARCHIVE', Session.getActiveUser().getEmail(), { monthKey, rows: rows.length });
  return { ok: true, rows: rows.length };
}

function computeAttendanceStats_(students, attendanceRows) {
  const byStudent = {};
  students.forEach((s) => {
    byStudent[s.studentId] = {
      studentId: s.studentId,
      fullName: s.fullName,
      present: 0,
      absent: 0,
      overallPercent: 0,
      consecutiveAbsent: 0
    };
  });

  const sorted = attendanceRows
    .filter((a) => byStudent[a.studentId])
    .sort((a, b) => String(a.date).localeCompare(String(b.date)));

  const streak = {};
  sorted.forEach((row) => {
    const item = byStudent[row.studentId];
    if (row.status === 'P') {
      item.present++;
      streak[row.studentId] = 0;
    } else {
      item.absent++;
      streak[row.studentId] = (streak[row.studentId] || 0) + 1;
      item.consecutiveAbsent = Math.max(item.consecutiveAbsent, streak[row.studentId]);
    }
  });

  return Object.values(byStudent).map((r) => {
    const total = r.present + r.absent;
    r.overallPercent = total ? Math.round((r.present * 10000) / total) / 100 : 0;
    return r;
  });
}

function recalculateDailySummary_(date, batchId) {
  const rows = getTableObjects_(SHEETS.ATTENDANCE).filter((r) => r.date === date && r.batchId === batchId);
  const presentCount = rows.filter((r) => r.status === 'P').length;
  const absentCount = rows.filter((r) => r.status === 'A').length;

  const sh = sheet_(SHEETS.DAILY_SUMMARY);
  const headers = getHeaders_(sh);
  const data = getTableObjects_(SHEETS.DAILY_SUMMARY);
  const idx = data.findIndex((r) => r.date === date && r.batchId === batchId);
  const values = { date, batchId, presentCount, absentCount, updatedAt: new Date().toISOString() };

  if (idx >= 0) writeRowByHeaders_(sh, headers, idx + 2, values, false);
  else appendByHeaders_(sh, headers, values);
}

function enforceEditLock_(user, dateStr) {
  if (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') return;
  const lockHours = Number(getSetting_('EDIT_LOCK_HOURS', '8'));
  const target = new Date(`${dateStr}T00:00:00`);
  const diffHrs = (Date.now() - target.getTime()) / (1000 * 60 * 60);
  if (diffHrs > lockHours) {
    throw new Error(`Edit locked after ${lockHours} hours. Ask Admin.`);
  }
}

function getVisibleStudents_(user) {
  const all = getTableObjects_(SHEETS.STUDENTS).filter((s) => String(s.active).toUpperCase() !== 'FALSE');
  if (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') return all;
  return all.filter((s) => user.assignedBatches.includes(s.batchId));
}

function getVisibleBatches_(user) {
  const all = getTableObjects_(SHEETS.BATCHES).filter((b) => String(b.active).toUpperCase() !== 'FALSE');
  if (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN') return all;
  return all.filter((b) => user.assignedBatches.includes(b.batchId));
}

function batchAllowed_(user, batchId) {
  return user.role === 'ADMIN' || user.role === 'SUPER_ADMIN' || user.assignedBatches.includes(batchId);
}

function getTableObjects_(sheetName) {
  const sh = sheet_(sheetName);
  const values = sh.getDataRange().getValues();
  if (values.length < 2) return [];
  const headers = values[0].map(String);
  return values.slice(1).filter((r) => r.join('') !== '').map((row) => {
    const obj = {};
    headers.forEach((h, i) => (obj[h] = row[i]));
    return obj;
  });
}

function getHeaders_(sh) {
  return sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(String);
}

function appendByHeaders_(sh, headers, values) {
  const row = headers.map((h) => (values[h] !== undefined ? values[h] : ''));
  sh.appendRow(row);
}

function writeRowByHeaders_(sh, headers, rowNumber, values, preserveId) {
  const current = sh.getRange(rowNumber, 1, 1, headers.length).getValues()[0];
  const row = headers.map((h, i) => {
    if (preserveId && h === 'attendanceId') return current[i] || values[h] || '';
    return values[h] !== undefined ? values[h] : current[i];
  });
  sh.getRange(rowNumber, 1, 1, headers.length).setValues([row]);
}

function getSetting_(key, fallback) {
  const items = getTableObjects_(SHEETS.SETTINGS);
  const found = items.find((x) => x.key === key);
  return found ? String(found.value) : fallback;
}

function audit_(action, actorEmail, details) {
  const sh = sheet_(SHEETS.AUDIT);
  const headers = getHeaders_(sh);
  appendByHeaders_(sh, headers, {
    timestamp: new Date().toISOString(),
    action,
    actorEmail,
    detailsJson: JSON.stringify(details || {})
  });
}

function dateKey_(d) {
  return Utilities.formatDate(new Date(d), Session.getScriptTimeZone(), 'yyyy-MM-dd');
}

function splitCsv_(v) {
  return String(v || '')
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean);
}

function normalize_(v) {
  return String(v || '').trim().toLowerCase();
}

function sheet_(name) {
  return SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(name);
}

function toCsv_(rows) {
  if (!rows.length) return '';
  const headers = Object.keys(rows[0]);
  const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const lines = [headers.map(esc).join(',')];
  rows.forEach((r) => lines.push(headers.map((h) => esc(r[h])).join(',')));
  return lines.join('\n');
}
