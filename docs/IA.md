# Information Architecture - Advanced CBT Application

## 🔄 Key Adjustments from Requirements

### 1. Authentication System

- **No public registration** - Only Admin can create users via User Management
- **No forgot password** - Admin handles password resets
- **Login only** - Simple email/username + password login
- Users get credentials from Admin (can be sent via email)

### 2. All URLs in English

- `/teacher/` instead of `/guru/`
- `/student/` instead of `/siswa/`
- `/exams/` instead of `/ujian/`
- `/question-bank/` instead of `/bank-soal/`
- `/results/` instead of `/hasil/`

### 3. Question Navigation Feature

- **Question-level settings:**
  - Allow Previous (can student go back to this question?)
  - Allow Next (can student skip/proceed from this question?)
  - Force Sequential (must answer in order?)
- **Exam-level override:**
  - Global navigation rules that can override individual questions
  - Useful for specific exam types (e.g., no review allowed)
- **Dynamic UI:**
  - Prev/Next buttons appear/hide based on settings
  - Navigation panel shows locked questions in sequential mode
  - Clear messaging when navigation is restricted

---

## 📐 Application Structure

### Role-Based Access

- **Admin**: Full access to all modules
- **Teacher**: Question management, exam management, and student monitoring
- **Student**: Exam access and results

---

## 🗺️ Site Map & Page Structure

```
├── Public Pages
│   ├── Landing Page
│   └── Login Page
│
├── Admin Dashboard
│   ├── Dashboard Overview
│   ├── User Management (CRUD Users)
│   ├── Subject Management (CRUD Subjects)
│   ├── System Settings
│   └── Analytics & Reports
│
├── Teacher Dashboard
│   ├── Dashboard Overview
│   ├── Question Bank Management
│   ├── Exam Management
│   ├── Student Monitoring
│   └── Results & Analysis
│
└── Student Dashboard
    ├── Dashboard Overview
    ├── Exam List
    ├── Exam Room
    └── Results & Review
```

---

## 📄 Page Details & Components

### 1. PUBLIC PAGES

#### 1.1 Landing Page

**URL:** `/`  
**Access:** Public

**Features:**

- Hero section with application description
- Featured highlights (features showcase)
- Platform statistics (number of users, exams, etc.)
- Call-to-action for login

**Components:**

- `NavigationBar`
  - Logo
  - Menu: Home, Features, About, Login
- `HeroSection`
  - Main heading
  - Tagline
  - CTA Button (Login)
- `FeaturesSection`
  - Feature Cards (4-6 cards)
  - Icons + Description
- `StatsSection`
  - Counter Animations
  - Metrics Display
- `Footer`
  - Links
  - Copyright
  - Social Media

**Notes:**

- Landing page bersifat opsional (halaman marketing publik)
- Jika `landing_page_enabled = false`:
  - URL `/` melakukan redirect `302` ke `/login/` (tidak ada halaman yang dirender)
- Jika `landing_page_enabled = true` (default):
  - Semua teks/gambar branding dibaca dari category `branding`
  - `institution_name` + `institution_logo_url` dipakai di `NavigationBar`
  - `login_page_headline` dipakai sebagai heading `HeroSection`
  - `institution_type` + `institution_name` dipakai di `Footer`

---

#### 1.2 Login Page

**URL:** `/login/`  
**Access:** Public

**Features:**

- Login form with validation
- Remember me checkbox
- Role-based redirect after login
- Error handling for invalid credentials

**Components:**

- `LoginForm`
  - Branding block (menggunakan data category `branding`):
    - Logo lembaga (`institution_logo_url`, fallback: logo default)
    - Nama lembaga (`institution_name`, fallback: "Sistem CBT")
    - Heading (`login_page_headline`, fallback: "Selamat Datang")
    - Sub-heading (`login_page_subheadline`, fallback: kosong)
    - Background page (`login_page_background_url`, fallback: CSS default)
  - Email/Username field
  - Password field (with show/hide toggle)
  - Remember me checkbox
  - Submit button
- `AlertMessage`
  - Success message
  - Error message
  - Info message (e.g., "Contact admin to reset password")

**Notes:**

- No register or forgot password feature
- New users must be registered by Admin through User Management
- Password reset can only be done by Admin

---

### 2. ADMIN DASHBOARD

#### 2.1 Admin Dashboard Overview

**URL:** `/admin/dashboard/`  
**Access:** Admin only

**Features:**

- Real-time statistics overview
- Quick actions panel
- Recent activities log
- System health monitor
- Charts & visualizations

**Components:**

- `StatisticsCards`
  - Total Users (Teachers, Students)
  - Total Subjects
  - Total Questions
  - Total Active Exams
  - Total Completed Exams
- `QuickActionsPanel`
  - Add User
  - View Reports
  - System Settings
- `RecentActivitiesTable`
  - Timestamp
  - User
  - Action
  - Status
- `ChartsSection`
  - User Growth Chart (Line chart)
  - Exam Statistics (Bar chart)
  - Activity Heatmap
- `SystemHealthWidget`
  - Server Status
  - Database Status
  - Storage Usage

---

#### 2.2 User Management

**URL:** `/admin/users/`  
**Access:** Admin only

**Features:**

- **CRUD operations for all users** (Create, Read, Update, Delete)
- **Create User** - Admin can register new users (Teacher/Student)
- **Edit User** - Update profile, email, role, status
- **Reset Password** - Admin can reset user passwords
- **Activate/Deactivate User** - Toggle user status
- Bulk actions (activate, deactivate, delete)
- User filtering & search
- Export user data
- User role management
- Activity logs per user
- Send notification/email to users
- **Import Users from Excel** (v1.3.0) - Bulk import Teacher/Student via .xlsx file

**Components:**

- `UserListTable`
  - Columns: ID, Name, Email, Role, Status, Join Date, Last Login, Actions
  - Sortable headers
  - Pagination
- `SearchBar`
  - Text search (name, email, username)
  - Advanced filters (Role, Status, Date range)
- `BulkActionToolbar`
  - Select all checkbox
  - Action dropdown (Activate, Deactivate, Delete, Export Selected)
  - Apply button
- `AddUserButton`
  - Prominent button for create user
- `UserFormModal` (Create/Edit)
  - **Basic Information:**
    - Full Name (required)
    - Email (required, unique)
    - Username (required, unique)
    - Role Selector (Admin/Teacher/Student)
    - Status Toggle (Active/Inactive)
  - **For Teacher:**
    - Teacher ID/NIP
    - Subject Specialization
    - Phone Number
  - **For Student:**
    - Student ID/NIS
    - Class/Grade
    - Phone Number
  - **Password (Create Only):**
    - Auto-generate password option
    - Manual password input
    - Show generated password
    - Send password via email (checkbox)
  - Save/Cancel buttons
- `ResetPasswordModal`
  - Username/Email display
  - New password options:
    - Auto-generate
    - Manual input
  - Show password toggle
  - Send via email checkbox
  - Confirm button
- `ExportButton`
  - Export to Excel
  - Export to CSV
  - Export selected only
- `DeleteConfirmationModal`
  - Warning message
  - Confirm/Cancel
- `UserDetailPanel` (Slide-in panel or modal)
  - Full user information
  - Activity logs
  - Login history
  - Exams taken/created
  - Quick actions (Edit, Reset Password, Toggle Status)
- `SendNotificationModal`
  - Select users
  - Message subject
  - Message body
  - Send button
- `ImportUsersModal` (v1.3.0 - 3-step wizard)
  - **Tahap 1 — Upload File:**
    - Download Template buttons (Teacher/Student)
    - Upload Area: drag & drop or browse (.xlsx/.xls, max 5 MB, max 500 rows)
    - Role Selection dropdown (Teacher/Student)
    - Email Option checkbox: "Kirim kredensial ke email user setelah import"
    - Navigation: [Lanjut ke Preview] [Batal]
  - **Tahap 2 — Preview & Validasi:**
    - Status Bar: ✅ Valid / ⚠ Skip (duplikat) / ❌ Error counts
    - Preview Table: max 20 rows; columns: No, Nama, Email, Username, Role, NIP/NIS, Kelas/Mapel, Status
    - Status Badges: ✅ Valid · ⚠ Skip (email/username exists) · ❌ Error (tooltip)
    - Error Panel (collapsible): Row No, Field, Value, Error Message
    - Rules: Skip rows don't stop import · If all errors, Confirm disabled
    - Navigation: [← Ganti File] [Konfirmasi Import] [Batal]
  - **Tahap 3 — Hasil Import:**
    - Summary: ✅ N berhasil · ⚠ Y dilewati · ❌ Z gagal
    - Error Table (collapsible): Row No, Nama, Email, Error Message
    - Download Report button (.xlsx with Status column + audit trail)
    - Password Info (if send_credentials_email=false): instruct admin to copy from detail page
    - Navigation: [Tutup & Refresh Daftar User]
- `ImportHistoryPanel` (v1.3.0 - optional)
  - Position: Tab "Riwayat Import" below user table
  - Table: Tanggal, Nama File, Diimport Oleh, Berhasil, Dilewati, Gagal, Status, Aksi
  - Actions: [⬇ Download Laporan] [👁 Lihat Detail]
  - Filters: Date range, Status, Admin performer
  - Limit: 50 most recent records with pagination

**Notes:**

- This is the only way to add new users to the system
- Admin can reset passwords at any time
- Generated passwords must be displayed to admin (copy button)
- Option to auto-send password to user's email

**Import Notes (v1.3.0):**

- Teacher and Student templates differ (NIP vs NIS fields are not the same)
- Duplicate email/username → skipped (Skip), not fatal Error
- Imported user passwords: auto-generated, must be sent via email or noted by admin
- Import process is synchronous — under 500 rows is responsive enough
- .xlsx report available for audit purposes
- All import history stored in user_import_logs

**Excel Template Columns:**

| Template | Required Fields (*) | Optional Fields |
|----------|---------------------|-----------------|
| import_template_teacher.xlsx | first_name*, last_name*, email*, username* | teacher_id (NIP), subject_specialization, phone_number, is_active |
| import_template_student.xlsx | first_name*, last_name*, email*, username*, student_id* (NIS), class_grade* | phone_number, is_active |

**Import Validation Rules:**

| Rule | Result |
|------|--------|
| Invalid format (not .xlsx/.xls) | Reject at upload |
| File size > 5 MB | Reject at upload |
| Rows > 500 | Reject at server |
| Header mismatch | Format error |
| Email duplicate in file | Row 2+ = Skip |
| Email exists in DB | Skip (not Error) |
| Required field empty | Error |
| Invalid email format | Error |
| All rows Error | Confirm button disabled |
| Import fails mid-process | Full rollback (atomic) |
| Cache expired (>10 min) | Back to Tahap 1 |
| Direct /confirm/ without preview | Reject |

---

#### 2.3 Subject Management

**URL:** `/admin/subjects/`  
**Access:** Admin only

**Features:**

- CRUD operations for subjects
- Subject code and name management
- Active/Inactive status toggle
- Bulk operations (activate, deactivate, delete)
- Search and filter functionality
- Export to Excel/CSV
- Dependency checking before deletion

**Components:**

- `SubjectListTable`
  - Columns: Checkbox, Code, Name, Description, Status, Question Count, Exam Count, Created Date, Actions
  - Sortable headers (Code, Name, Created Date)
  - Pagination
- `SearchBar`
  - Text search (name or code)
  - Real-time search with debounce (300ms)
  - Placeholder: "Search by subject name or code..."
- `FilterBar`
  - Status filter (All/Active/Inactive)
  - Reset filters button
- `AddSubjectButton`
  - Opens SubjectFormModal
- `SubjectFormModal` (Create/Edit)
  - Subject Code (required, unique, max 20 chars, auto-uppercase, read-only in edit mode)
  - Subject Name (required, unique, max 100 chars)
  - Description (optional, textarea, max 500 chars)
  - Status Toggle (Active/Inactive, default: Active)
  - Save/Cancel buttons
- `BulkActionToolbar`
  - Select all checkbox
  - Selected count badge
  - Action dropdown (Activate, Deactivate, Export Excel, Export CSV, Delete)
  - Apply button
- `DeleteConfirmationModal`
  - Warning message
  - If has dependencies: show question count and exam count
  - Option to mark as inactive instead of delete
- `ExportButton`
  - Export to Excel
  - Export to CSV
  - File naming: "subjects_YYYYMMDD_HHMMSS.xlsx"

**Notes:**

- Cannot delete subject with associated questions or exams
- Subject code cannot be changed after creation
- Code is auto-converted to uppercase
- Inactive subjects don't appear in dropdown selections (Question Bank, Exam Management)

---

#### 2.4 System Settings

**URL:** `/admin/settings/`  
**Access:** Admin only

**Features:**

- General settings (tanpa Site Name/Site Logo)
- Branding settings (identitas lembaga + visual)
- Email configuration
- Security settings
- Exam default settings
- Notification preferences
- Backup & restore

**Components:**

- `SettingsTabs`
  - Tab: General (diperbarui: hapus Site Name & Site Logo)
  - Tab: Branding (baru, posisi setelah General)
  - Tab: Email
  - Tab: Security
  - Tab: Exam Defaults
  - Tab: Notifications
  - Tab: Backup
- `GeneralSettingsForm`
  - Timezone
  - Language
- `BrandingSettingsForm` (Admin only)
  - Seksi Identitas Lembaga:
    - `institution_name`
    - `institution_type`
    - `institution_address`
    - `institution_phone`
    - `institution_email`
    - `institution_website`
  - Seksi Visual & Logo:
    - `institution_logo_url` (upload + preview, PNG/JPG/SVG, max 2MB; dipakai di navbar/login/PDF/sertifikat)
    - `institution_logo_dark_url` (upload + preview, opsional)
    - `institution_favicon_url` (upload + preview, opsional; ICO/PNG, rekomendasi 32x32)
    - `primary_color` (color picker HEX + reset default `#0d6efd`)
  - Seksi Halaman Login:
    - `login_page_headline`
    - `login_page_subheadline`
    - `login_page_background_url` (upload + preview, opsional, JPG/PNG max 5MB; jika kosong pakai CSS default)
  - Seksi Landing Page:
    - `landing_page_enabled` (toggle ON/OFF)
    - Jika OFF: URL `/` redirect ke `/login/`
    - Muncul konfirmasi:
      - "Menonaktifkan Landing Page akan membuat URL root (/) langsung ke Login."
      - Tombol: `[Ya, Nonaktifkan] [Batal]`
  - Mekanisme upload:
    - `enctype="multipart/form-data"`
    - submit form POST biasa (bukan AJAX upload terpisah)
    - validasi server-side untuk tipe file dan ukuran
    - setelah simpan: reload + flash message
- `EmailSettingsForm`
  - SMTP Configuration
  - Test Email Button
- `SecuritySettingsForm`
  - Password Policy
  - Session Timeout
  - IP Whitelist
- `ExamDefaultsForm`
  - Default Duration
  - Default Passing Score
  - Anti-cheat Settings
- `BackupSection`
  - Create Backup Button
  - Restore Backup Upload
  - Backup History Table

**Notes:**

- Tab Branding hanya untuk Admin
- Konsolidasi: Site Name/Site Logo lama dari Tab General dipindah ke Tab Branding
- Perubahan branding dibaca via cache (bukan hardcoded `settings.py`)
- Cache branding di-invalidate otomatis saat save Tab Branding
- `institution_logo_url` dipakai di navbar, login, header PDF laporan, dan sertifikat
- Jika `institution_name` kosong, gunakan fallback dari `settings.CBT_SITE_NAME`
- Jika `primary_color` kosong, fallback ke `#0d6efd`
- `landing_page_enabled` tetap disimpan di category `general` karena memengaruhi routing

---

#### 2.5 Analytics & Reports

**URL:** `/admin/analytics/`  
**Access:** Admin only

**Features:**

- Real-time analytics dashboard
- Custom date range reports
- Export reports
- Visualization charts
- Comparative analysis

**Components:**

- `DateRangePicker`
- `MetricsSummary`
  - Total Exams Conducted
  - Total Participants
  - Average Score
  - Completion Rate
- `InteractiveCharts`
  - Exam Performance Trends (Line)
  - Subject-wise Analysis (Pie)
  - User Activity (Bar)
  - Score Distribution (Histogram)
- `ReportsTable`
  - Configurable columns
  - Export options
- `FilterPanel`
  - Subject filter
  - Class filter
  - Exam type filter

---

### 3. TEACHER DASHBOARD

#### 3.1 Teacher Dashboard Overview

**URL:** `/teacher/dashboard/`  
**Access:** Teacher only

**Features:**

- Personal statistics
- Upcoming exams
- Recent exam results
- Quick access to common tasks
- Student performance summary

**Components:**

- `WelcomeHeader`
  - Greeting message
  - Profile picture
- `StatsCards`
  - Total Questions Created
  - Active Exams
  - Total Students
  - Average Class Score
- `UpcomingExamsWidget`
  - List of scheduled exams
  - Start exam button
  - Edit/Delete actions
- `RecentResultsWidget`
  - Latest exam results
  - Quick view statistics
- `QuickActionsPanel`
  - Create New Question
  - Create New Exam
  - Import Questions
  - View Question Bank

---

#### 3.2 Question Bank Management

**URL:** `/teacher/question-bank/`  
**Access:** Teacher only

**Features:**

- CRUD operations for questions
- Categorization (Subject, Difficulty Level, Category)
- Bulk import from Excel/JSON
- Bulk export questions
- Preview questions
- Duplicate questions
- Rich text editor for essay questions
- Media upload (images for questions)
- **Question Navigation Settings** - Settings to configure whether students can navigate prev/next during exams

**Components:**

- `QuestionListView`
  - Table with columns: No, Type, Question Preview, Category, Difficulty, Actions
  - Pagination
- `FilterSidebar`
  - Filter by Question Type
  - Filter by Subject
  - Filter by Difficulty Level
  - Filter by Category
- `SearchBar`
- `ActionButtons`
  - Add New Question
  - Import Questions (Excel/JSON)
  - Export Questions
- `QuestionFormModal` (Add/Edit)
  - Question Type Selector (Multiple Choice/Essay/Short Answer)
  - Rich Text Editor (for question text)
  - Image Upload
  - Dynamic Options Fields (for multiple choice)
  - Correct Answer Selector
  - Points/Weight
  - Difficulty Level
  - Category/Tags
  - **Navigation Settings:**
    - Allow Previous (checkbox) - Can students go back to this question?
    - Allow Next (checkbox) - Can students skip/proceed from this question?
    - Force Sequential (checkbox) - Questions must be answered in order
  - Explanation/Discussion (optional)
- `PreviewModal`
  - Render question as in exam
  - Show navigation settings
- `ImportModal`
  - File upload
  - Template download link
  - Validation feedback
- `DeleteConfirmationModal`

**Sub-Components for Form:**

- `MultipleChoiceFields`
  - Options A, B, C, D, E (dynamic add/remove)
  - Radio button for correct answer
- `EssayFields`
  - Rich text area
  - Keyword rubric (optional)
  - Max word count
- `ShortAnswerFields`
  - Text input for answer
  - Case sensitive toggle

**Notes on Navigation Settings:**

- Each question can be configured whether it can be prev/next or not
- These settings will be applied when the question is used in exams
- Useful for questions that should not be reviewed (prevent cheating)
- Can be combined with timer per question

---

#### 3.3 Exam Management

**URL:** `/teacher/exams/`  
**Access:** Teacher only

**Features:**

- CRUD operations for exams
- Time settings (start, end, duration)
- Question selection from question bank
- Randomize questions & options
- Passing grade settings
- Assignment to classes/specific students
- Anti-cheat settings
- **Question Navigation Rules** - Override navigation settings per exam
- Preview exam
- Publish/unpublish exam
- Duplicate exam

**Components:**

- `ExamListView`
  - Cards/Table view toggle
  - Columns: Title, Subject, Schedule, Duration, Participants, Status, Actions
  - Jika `allow_retake = true`: tampilkan badge `[🔁 Nx]` di samping Title
    (`N = max_retake_attempts`, warna muted/secondary)
- `FilterBar`
  - Status filter (Draft, Published, Ongoing, Completed)
  - Date filter
  - Subject filter
- `CreateExamButton`
- `ExamFormWizard` (Multi-step)
  - **Step 1: Basic Info**
    - Exam Title
    - Subject
    - Description
    - Instructions
  - **Step 2: Time Settings**
    - Start Date & Time (datetime picker)
    - End Date & Time (datetime picker)
    - Exam Duration
    - Time per Question (optional)
  - **Step 3: Question Selection**
    - Question Bank Selector
    - Add questions individually or by category
    - Drag-and-drop for ordering
    - Preview selected questions
    - Total points calculator
    - **Per-Question Navigation Override:**
      - View navigation settings from question
      - Override checkbox per question
      - Custom navigation rules for this exam
  - **Step 4: Exam Settings**
    - Passing Grade
    - Randomize Questions (toggle)
    - Randomize Options (toggle)
    - Show results immediately (toggle)
    - Allow answer review (toggle)
    - **Global Navigation Rules:**
      - Allow previous navigation (global toggle)
      - Allow next navigation (global toggle)
      - Force sequential answering (toggle)
      - Override individual question settings (toggle)
    - **Retake Settings**
      - Allow Retake (toggle, default: OFF)
      - `[Tampil hanya jika Allow Retake = ON]`
      - Max Attempts
        - Input angka, min 2, max 10
        - Helper: "Termasuk ujian pertama - nilai 3 = 1 asli + 2 retake"
      - Kebijakan Nilai (radio, wajib dipilih)
        - Nilai Tertinggi (default & rekomendasi)
        - Nilai Terbaru
        - Nilai Rata-rata
      - Jeda Antar Percobaan
        - Input angka (menit), min 0
        - Helper: "0 = langsung bisa retake setelah submit"
      - Izinkan review jawaban sebelum retake (toggle)
        - ON: siswa dapat melihat soal yang salah sebelum mulai ulang
        - OFF: langsung masuk ke halaman konfirmasi retake
  - **Step 5: Anti-Cheat Settings**
    - Full screen mode (toggle)
    - Detect tab switching (toggle)
    - Screenshot proctoring (toggle)
    - Screenshot interval
    - Max violations before auto-submit
  - **Step 6: Assignment**
    - Select classes/students
    - Multi-select list
  - **Step 7: Review & Publish**
    - Summary of all settings
    - Navigation rules summary
    - Retake summary (jika `allow_retake = true`):
      - "Ujian ulang: Aktif | Maks. N percobaan | Nilai: Tertinggi/Terbaru/Rata-rata
         Jeda: N menit | Review sebelum retake: Ya/Tidak"
    - Save as draft or Publish
- `ExamPreviewModal`
  - Student view simulation
  - Test navigation rules
- `DuplicateModal`
- `DeleteConfirmationModal`

**Notes on Navigation Rules:**

- Exam-level settings can override question-level settings
- Preview mode shows how navigation will work
- Useful for adaptive CBT exams or no-review exams

---

#### 3.4 Student Monitoring (Live Exam Monitor)

**URL:** `/teacher/monitoring/<exam_id>/`  
**Access:** Teacher only

**Features:**

- Real-time monitoring of students taking exams
- Live statistics
- View individual student progress
- View screenshots (if enabled)
- View violations log
- Manual intervention (extend time, force submit)
- Live chat/announcement

**Components:**

- `LiveStatsPanel`
  - Total Participants
  - Currently Active
  - Completed
  - Average Progress %
  - Real-time updates via WebSocket
- `StudentsMonitoringGrid`
  - Cards for each student
  - Each card shows:
    - Student name & photo
    - Status (Active/Idle/Submitted)
    - Progress bar
    - Current question number
    - Time remaining
    - Violations count
    - Attempt badge: `Attempt 2/3`
      - Hanya tampil jika `allow_retake = true` pada ujian tersebut
    - View detail button
- `StatusIndicators`
  - Color coding (Green: normal, Yellow: warning, Red: violations)
- `StudentDetailModal`
  - Answer history
  - Time spent per question
  - Screenshots gallery
  - Violations log with timestamp
  - Actions: Extend time, Force submit
  - Riwayat Attempt (hanya jika `allow_retake = true` & `attempt_number > 1`):
    - Tabel: No. Attempt | Waktu Mulai | Waktu Selesai | Nilai | Status
- `ViolationsPanel`
  - Real-time violations feed
  - Filter by violation type
- `AnnouncementWidget`
  - Broadcast message to all students
  - Send message to individual student
- `RefreshToggle`
  - Auto-refresh interval selector

---

#### 3.5 Results & Analysis

**URL:** `/teacher/results/`  
**Access:** Teacher only

**Features:**

- List all exam results
- Detailed analytics per exam
- Individual student performance
- Export results (Excel, PDF)
- Statistical analysis
- Item analysis (most difficult questions, etc.)
- Comparative analysis between classes

**Components:**

- `ExamResultsList`
  - Table: Exam, Date, Participants, Avg Score, Pass Rate, Actions
- `FilterBar`
  - Date range
  - Subject
  - Class
- `ResultDetailView`
  - Exam info summary
  - Overall statistics
  - Score distribution chart
  - Pass/fail ratio (donut chart)
- `StatisticsCards`
  - Highest Score
  - Lowest Score
  - Average Score
  - Median Score
  - Standard Deviation
- `StudentResultsTable`
  - Columns: Rank, Name, Score, Percentage, Status, Time Taken, Attempts, Actions
  - Kolom Score = nilai FINAL sesuai `retake_score_policy`
    - Tooltip: "Nilai final (Tertinggi dari N attempt)"
  - Kolom Attempts = `2/3` (klik membuka `RetakeHistoryModal`)
    - Hanya tampil jika `allow_retake = true`
  - Sortable
  - Export selected
- `RetakeHistoryModal` (komponen baru - teacher view)
  - Header: "[Nama Siswa] - [Nama Ujian]"
  - Subheader: "Kebijakan: Nilai Tertinggi dari N percobaan"
  - Tabel: No. | Tanggal & Jam | Nilai | % | Lulus? | Durasi | Ket.
  - Kolom Ket.: ★ = attempt yang nilai-nya digunakan sebagai nilai final
- `ItemAnalysisPanel`
  - Question-by-question breakdown
  - Difficulty index
  - Discrimination index
  - Distractor analysis (for multiple choice)
- `ExportOptions`
  - Export All (Excel)
  - Export Selected
  - Generate PDF Report
- `StudentDetailModal`
  - Complete answer sheet
  - Question-by-question review
  - Time analysis
  - Violations during exam
- `ComparisonChart`
  - Compare multiple exams
  - Class vs class comparison

---

### 4. STUDENT DASHBOARD

#### 4.1 Student Dashboard Overview

**URL:** `/student/dashboard/`  
**Access:** Student only

**Features:**

- Welcome message
- Upcoming exams
- Recent exam results
- Performance summary
- Notifications

**Components:**

- `WelcomeHeader`
  - Greeting
  - Profile picture
- `UpcomingExamsCards`
  - Exam cards with countdown
  - Start Exam button (if time has arrived)
  - Exam details
- `RecentResultsWidget`
  - Score yang ditampilkan = nilai FINAL (via `calculate_final_score`),
    bukan score attempt terakhir mentah
  - Badge 🔁 kecil di samping nama ujian jika `allow_retake = true`
- `PerformanceSummary`
  - Total Exams Taken -> hitung ujian UNIK, bukan jumlah attempt
  - Average Score -> berbasis nilai final per ujian unik
  - Best Score -> berbasis nilai final
  - Performance trend (mini chart) -> berbasis nilai final per ujian unik
- `NotificationsWidget`
  - Recent notifications
  - Unread count badge

---

#### 4.2 Exam List

**URL:** `/student/exams/`  
**Access:** Student only

**Features:**

- List all assigned exams
- Filter by status (Upcoming, Ongoing, Completed, Missed)
- Exam detail view
- Start exam button
- View results (for completed exams)

**Components:**

- `ExamTabs`
  - Tab: Upcoming
  - Tab: Ongoing
  - Tab: Completed
  - Tab: Missed
- `ExamCards`
  - Title & Subject
  - Short description
  - Schedule (Date & Time)
  - Duration
  - Total Questions
  - Status badge
  - Action button (Start/View Results)
  - (Tab Completed, jika retake tersedia):
    - Badge: "🔁 N sisa" (jika `attempt_number < max_retake_attempts`)
    - Tombol "Ujian Ulang":
      - Aktif -> sisa attempt > 0 dan cooldown selesai
      - Disabled -> cooldown belum selesai + countdown: "Tersedia dalam Xm Ys"
- `CountdownTimer` (for upcoming exams)
- `ExamDetailModal`
  - Full description
  - Instructions
  - Rules & anti-cheat info
  - Navigation rules info (if applicable)
  - Blok Info Retake (tampil jika `allow_retake = true`):
    - Kesempatan total: N kali
    - Sudah digunakan: M kali -> Sisa: (N-M) kali
    - Kebijakan nilai: Tertinggi / Terbaru / Rata-rata
    - Jeda antar sesi: N menit (jika > 0)
  - Tombol Start / Ujian Ulang
- `FilterBar`
  - Search
  - Subject filter
  - Date filter

---

#### 4.3 Exam Room

**URL:** `/student/exams/<exam_id>/attempt/`  
**Access:** Student only (during exam time)

**Features:**

- Full screen mode (enforced)
- Question navigation (based on question/exam settings)
- Timer countdown
- Auto-save answers
- Mark for review
- Submit confirmation
- Tab switching detection
- Screenshot proctoring (background)
- Warning system for violations
- Auto-submit when time runs out
- **Dynamic Navigation Controls** - Next/Prev buttons appear based on question settings

**Components:**

- `ExamHeader`
  - Exam title
  - Timer (countdown) - prominent display
  - Submit button
  - Attempt badge: "Attempt 2 dari 3"
    - Hanya tampil jika `allow_retake = true` & `max_retake_attempts > 1`
- `QuestionNavigationPanel`
  - Question numbers grid
  - Status indicators:
    - Answered (green)
    - Not answered (gray)
    - Marked for review (yellow)
    - Current (blue border)
    - Locked/Disabled (if sequential mode or navigation restricted)
  - Click navigation (if allowed by settings)
- `QuestionDisplay`
  - Question number indicator
  - Question text (with rich text support)
  - Question image (if any)
  - **For Multiple Choice:**
    - Radio buttons for options A-E
  - **For Essay:**
    - Rich text area
    - Character/word counter
  - **For Short Answer:**
    - Text input field
  - Mark for review checkbox
- `NavigationButtons` (Dynamic based on settings)
  - **Previous button** - Only shown if:
    - Question allows previous navigation, OR
    - Exam allows previous navigation
    - Disabled if on first question
  - **Next button** - Only shown if:
    - Question allows next navigation, OR
    - Exam allows next navigation
    - Changes to "Submit" on last question
  - **Clear answer** button
  - **Navigation locked message** (if applicable)
- `ProgressBar`
  - Answered vs Total questions
- `WarningModal`
  - Tab switching warning
  - Full screen exit warning
  - Violation counter
  - Return to exam button
- `SubmitConfirmationModal`
  - Summary:
    - Total questions
    - Answered
    - Not answered
    - Marked for review
  - Info retake (jika sisa attempt > 0 setelah ini):
    - "Setelah submit, kamu masih punya N kesempatan ujian ulang."
  - Tombol: Submit | Batal
- `AutoSaveIndicator`
  - Last saved timestamp
- `FullScreenEnforcer`
  - Detect exit from fullscreen
  - Overlay blocker
- `NavigationRestrictionInfo` (Toast/Banner)
  - Shown when navigation is restricted
  - Example: "Sequential mode: Answer this question to proceed"

**Monitoring Features (Background):**

- Tab switch detector
- Window focus detector
- Screenshot capture (periodic)
- Violation logger
- Auto-submit trigger

**Navigation Logic:**

- Check question-level navigation settings first
- Apply exam-level override if enabled
- Disable navigation buttons accordingly
- Show helpful messages when navigation is restricted
- In sequential mode: lock unanswered questions ahead

---

#### 4.4 Results & Review

**URL:** `/student/results/`  
**Access:** Student only

**Features:**

- List completed exam results
- Detail score per exam
- Review answers (if allowed by teacher)
- Download certificate (if available)
- Performance analytics
- Question explanations (if available)

**Components:**

- `ResultsList`
  - Cards/Table view
  - Columns: Exam, Date, Score, Percentage, Status, Actions
  - Score = nilai FINAL
  - Badge 🔁 di kolom Exam jika ujian tersebut punya retake aktif
- `FilterBar`
  - Subject filter
  - Date range
  - Status (Passed/Failed)
- `ResultDetailView`
  - Score Card (large display)
  - Percentage
  - Status (Passed/Failed)
  - Rank (if displayed)
  - Time taken
  - Exam info
  - Info nilai: "Nilai ini adalah [Tertinggi/Terbaru/Rata-rata] dari N percobaan"
  - Badge ★ pada attempt yang nilai-nya digunakan sebagai nilai final
- `AnswerReviewSection` (if enabled)
  - Question-by-question review
  - Student's answer
  - Correct answer
  - Explanation/Discussion
  - Points earned
  - Color coding (correct/incorrect)
- `PerformanceChart`
  - Score trends over time
  - Subject-wise performance
- `DownloadCertificateButton` (if applicable)
- `StatisticsCards`
  - Correct Answers
  - Wrong Answers
  - Unanswered
  - Time Efficiency
- `MyRetakeHistorySection` (komponen baru - student view)
  - Tampil di bawah `ResultDetailView`, hanya jika `allow_retake = true`
  - Tabel: No. | Waktu | Nilai | % | Status | Durasi | Ket.
  - Kolom Ket.: ★ = nilai final yang digunakan
  - Tombol "Mulai Ujian Ulang" (jika sisa > 0):
    - Aktif -> cooldown selesai
    - Disabled -> countdown live "Tersedia dalam Xm Ys"

---

## 🎨 Global Components (Shared)

### Navigation Bar

- Logo
- Role-specific menu items
- Notifications dropdown
- User profile dropdown
  - My Profile
  - Settings
  - Logout

### Sidebar Navigation (Dashboard)

- Role-based menu items
- Active state indicator
- Collapsible (mobile)

### Footer

- Copyright
- Links
- Version info

### Alert/Toast Notifications

- Success messages
- Error messages
- Warning messages
- Info messages
- Auto-dismiss timer

### Loading Indicators

- Spinner
- Progress bar
- Skeleton loaders

### Modal Base

- Header
- Body
- Footer (actions)
- Close button
- Backdrop

### Form Components

- Text Input
- Email Input
- Password Input (with show/hide)
- Textarea
- Select/Dropdown
- Multi-select
- Radio buttons
- Checkboxes
- Date picker
- DateTime picker
- Time picker
- File upload
- Rich text editor
- Image upload with preview

### Table Components

- Sortable headers
- Pagination
- Row selection (checkbox)
- Action buttons per row
- Empty state
- Loading state

### Card Components

- Basic card
- Stats card
- Action card
- List card

### Chart Components

- Line chart
- Bar chart
- Pie chart
- Donut chart
- Area chart
- Histogram

---

## 🔄 Real-time Features (WebSocket)

### Channels/Events

1. **exam_monitoring_{exam_id}**
   - Student join/leave
   - Progress updates
   - Violations
   - Submissions

2. **notifications_{user_id}**
   - New notifications
   - Announcements

3. **live_stats_{exam_id}**
   - Real-time statistics updates

---

## 📊 Data Flow Examples

### Exam Flow (Student)

```
Exam List → Exam Detail → Confirm Start →
Exam Room (Full screen) → Answer Questions (with navigation controls) → Submit →
Results (if allowed)
```

### Retake Flow (Student)

```
[Submit Attempt N]
  → Sistem grade → simpan exam_results (1 record, UNIQUE attempt_id)
  → Hitung retake_available_from = submit_time + retake_cooldown_minutes
  → Update exam_attempts.retake_available_from pada attempt N
  → Hitung nilai final via calculate_final_score() berdasarkan score_policy
  → Redirect ke halaman Hasil Attempt N

[Cek kelayakan retake]
  attempt_number < max_retake_attempts?  → YA
  NOW() >= retake_available_from?        → YA
    → Tampilkan tombol "🔁 Ujian Ulang"
    ↓
    [retake_show_review = true?]
      YA  → Halaman Pre-Retake Review (jawaban salah attempt N)
      TIDAK → langsung ke konfirmasi
    ↓
    Retake Confirmation Modal:
      "Kamu akan memulai Attempt ke-(N+1) dari (max) total.
       Nilai yang digunakan: [Policy]."
      [Mulai] [Batal]
    ↓
    → Buat exam_attempts baru (attempt_number = N+1, status = not_started)
    → Exam Room (header: "Attempt N+1 dari Max")
    → Submit → ulangi siklus dari awal

[Max attempts tercapai]
  attempt_number >= max_retake_attempts
    → Tidak ada tombol Ujian Ulang
    → Tampilkan nilai final definitif
```

### Branding Setup Flow (Admin)

```text
[Admin login -> System Settings -> Tab Branding]
  -> Isi identitas lembaga (nama, jenis, alamat, kontak, website)
  -> Upload logo utama, favicon, dan (opsional) background login
  -> Set primary color
  -> Atur headline/subheadline login
  -> Atur toggle landing_page_enabled
  -> Klik [Simpan Pengaturan] -> POST multipart -> validasi file server-side
  -> Cache branding di-invalidate
  -> Redirect kembali ke settings + flash message sukses

[Efek setelah simpan]
  -> Branding navbar/login langsung berubah
  -> Favicon browser berubah
  -> Primary color dipakai sebagai CSS variable global
  -> Header PDF laporan/sertifikat memakai institution_name + logo
  -> Jika landing_page_enabled = false, GET / redirect 302 ke /login/

LandingView logic (apps/dashboard/views.py):
  -> Panggil apps.core.services.get_branding_settings() dari cache
  -> Jika landing_page_enabled = false -> redirect('login')
  -> Jika true -> render landing.html dengan context branding
```

### Monitoring Flow (Teacher)

```
Exam Management → Publish Exam →
Live Monitoring (during exam) →
Results & Analysis
```

### Question Creation Flow (Teacher)

```
Question Bank → Add New Question →
Form (multi-type + navigation settings) → Save →
Preview → Use in Exam
```

### User Management Flow (Admin)

```
User Management → Create User →
Fill Form → Generate/Set Password →
Save → Send credentials (optional)
```

### Import Users Flow (v1.3.0)

```
[Klik "Import Users"]
  → Open ImportUsersModal Tahap 1
  → (Optional) Download Teacher/Student template
  → Upload .xlsx file + check email option
  → Lanjut ke Preview

[Server — Validasi]
  → Parse file with openpyxl
  → Validate per row: required fields, email format,
    uniqueness of email & username in DB, valid role
  → Return JSON: {valid, skip, errors}
  → Display Tahap 2

[Admin Review]
  → Check valid/skip/error rows
  → If not satisfied → Ganti File (back to Tahap 1)
  → If satisfied → Konfirmasi Import

[Server — Eksekusi]
  → Atomic transaction: create users + user_profiles
  → Log to user_activity_logs (action: bulk_import)
  → If send_email=True → trigger Celery task for credentials
  → Save summary to user_import_logs
  → Display Tahap 3

[Admin Review Hasil]
  → View summary & download report if needed
  → Close modal → user list auto-refreshes
```

---
## 🎯 Key User Interactions

### User Registration Flow (Admin Only)

1. Admin goes to User Management
2. Click "Add User" button
3. Fill user information (name, email, role, etc.)
4. Generate or set password
5. Optionally send credentials via email
6. User can now login with provided credentials

### Navigation Control Flow (During Exam)

1. Student starts exam
2. System checks question navigation settings
3. System checks exam-level override settings
4. Apply navigation rules:
   - If "Allow Previous" = false → Hide/disable Previous button
   - If "Allow Next" = false → Hide/disable Next button  
   - If "Force Sequential" = true → Lock unanswered questions
5. Show appropriate messages when navigation blocked
6. Update button states as student progresses

### Anti-Cheat Flow

1. Student enters exam room
2. System request full screen
3. Monitoring starts (tab switch, screenshot)
4. If violation detected → Warning modal
5. If exceed max violations → Auto submit + flag

### Real-time Monitoring

1. Teacher opens monitoring page
2. WebSocket connection established
3. Receive real-time updates from students taking exam
4. Display violations, progress, status

### Import Questions Flow

1. Teacher clicks Import Questions
2. Download template (if needed)
3. Upload file (Excel/JSON)
4. System validates format
5. Preview questions to be imported (including navigation settings)
6. Confirm import
7. Success message + redirect to question bank

---

## 📱 Responsive Considerations

### Desktop (>1024px)

- Full sidebar navigation
- Multi-column layouts
- Large data tables
- Side-by-side panels

### Tablet (768px - 1024px)

- Collapsible sidebar
- Stacked layouts for some sections
- Responsive tables (horizontal scroll)

### Mobile (<768px)

- Hamburger menu
- Single column layouts
- Card-based views instead of tables
- Bottom navigation (optional)
- Simplified monitoring views

---

## 🔐 Security Considerations per Page

### Exam Room

- CSRF protection
- Session validation
- Token-based exam access
- IP restriction (optional)
- Browser fingerprinting

### Admin Pages

- Role-based access control
- Action logging
- Two-factor authentication (optional)

### Data Export

- Rate limiting
- Access logging
- Watermarking (optional)

---

## 📝 Notes for Development

1. **Development Priorities:**
   - Phase 1: Authentication & Role Management
   - Phase 2: Question Bank & CRUD
   - Phase 3: Exam Creation & Management
   - Phase 4: Exam Room & Anti-cheat
   - Phase 5: Monitoring & Analytics
   - Phase 6: Real-time Features & WebSocket
   - Phase 7: Import/Export & Advanced Features

2. **Technology Stack Recommendations:**
   - Frontend: Alpine.js for simple interactivity, HTMX for dynamic updates
   - Charts: Chart.js or ApexCharts
   - Rich Text: TinyMCE or Quill
   - WebSocket: Django Channels with Redis
   - Task Queue: Celery (for screenshot processing, export generation)

3. **Database Optimization:**
   - Index on foreign keys
   - Index on frequently queried fields
   - Denormalization for analytics table

4. **Caching Strategy:**
   - Cache question bank list
   - Cache exam list
   - Cache student results
   - Invalidate on updates

---

## ✅ Component Checklist to Build

### Admin & System Settings

- [ ] BrandingSettingsForm (Tab Branding di System Settings)
- [ ] Identitas lembaga: nama, jenis, alamat, telepon, email, website
- [ ] Upload logo utama (file + preview)
- [ ] Upload logo dark (file + preview, opsional)
- [ ] Upload favicon (file + preview, opsional)
- [ ] Color picker primary color + tombol reset
- [ ] Heading & tagline halaman login
- [ ] Upload background login (file + preview, opsional)
- [ ] Toggle `landing_page_enabled` + dialog konfirmasi
- [ ] GeneralSettingsForm diperbarui (hapus Site Name & Site Logo)

### Subject Management

- [ ] Subject List Table
- [ ] Subject Form (Create/Edit)
- [ ] Subject Search Bar
- [ ] Subject Filter Bar
- [ ] Bulk Action Toolbar
- [ ] Delete Confirmation with Dependency Check
- [ ] Export Functionality

### Exam Management

- [ ] Exam Form Wizard
- [ ] RetakeSettingsForm (embedded di Step 4, kondisional saat allow_retake=ON)
- [ ] Retake badge [🔁 Nx] di ExamListView

### Exam Room

- [ ] Question Display, Timer, Anti-cheat, Submit Modal
- [ ] AttemptCounterBadge di ExamHeader
- [ ] Info sisa retake di SubmitConfirmationModal

### Monitoring

- [ ] Live Stats Panel, Student Cards Grid, Violations Feed
- [ ] Attempt badge di kartu siswa (StudentsMonitoringGrid)
- [ ] Tabel Riwayat Attempt di StudentDetailModal

### Results & Analytics (Teacher)

- [ ] StudentResultsTable - kolom Attempts + nilai final + tooltip
- [ ] RetakeHistoryModal (teacher)

### Results & Analytics (Student)

- [ ] ResultsList - nilai final + badge 🔁
- [ ] ResultDetailView - info nilai final + badge ★
- [ ] MyRetakeHistorySection + tombol retake + cooldown countdown

### Student Dashboard

- [ ] RecentResultsWidget - nilai final, bukan score attempt mentah
- [ ] PerformanceSummary - hitung dari ujian unik & nilai final

---

**This document will serve as a blueprint for development. Each page, feature, and component has been clearly defined to facilitate implementation.**
