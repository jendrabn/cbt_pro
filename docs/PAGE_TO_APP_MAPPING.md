# Page to Django App Mapping - Advanced CBT Application

## 📋 Overview

Dokumen ini menjelaskan mapping antara setiap halaman di **Information Architecture** dengan **Django App** yang menanganinya, beserta detail komponen dan tanggung jawab masing-masing.

---

## 🗺️ Complete Mapping Table

| Page Section | Page Name | URL | Django App | View Location |
|-------------|-----------|-----|------------|---------------|
| **Public** | Landing Page | `/` | `dashboard` | `apps/dashboard/views.py` |
| **Public** | Login Page | `/login/` | `accounts` | `apps/accounts/views.py` |
| **Admin** | Admin Dashboard | `/admin/dashboard/` | `dashboard` | `apps/dashboard/views.py` |
| **Admin** | User Management | `/admin/users/` | `users` | `apps/users/views.py` |
| **Admin** | User Import | `/admin/users/import/` | `users` | `apps/users/views.py` |
| **Admin** | User Import Confirm | `/admin/users/import/confirm/` | `users` | `apps/users/views.py` |
| **Admin** | User Import History | `/admin/users/import/history/` | `users` | `apps/users/views.py` |
| **Admin** | User Import Report | `/admin/users/import/<log_id>/report/` | `users` | `apps/users/views.py` |
| **Admin** | Download Import Template | `/admin/users/import/template/<role>/` | `users` | `apps/users/views.py` |
| **Admin** | Subject Management | `/admin/subjects/` | `subjects` | `apps/subjects/views.py` |
| **Admin** | System Settings | `/admin/settings/` | `core` | `apps/core/views.py` |
| **Admin** | Branding Settings (Tab) | `/admin/settings/?tab=branding` | `core` | `apps/core/views.py` |
| **Admin** | Analytics & Reports | `/admin/analytics/` | `analytics` | `apps/analytics/views.py` |
| **Teacher** | Teacher Dashboard | `/teacher/dashboard/` | `dashboard` | `apps/dashboard/views.py` |
| **Teacher** | Question Bank | `/teacher/question-bank/` | `questions` | `apps/questions/views.py` |
| **Teacher** | Exam Management | `/teacher/exams/` | `exams` | `apps/exams/views.py` |
| **Teacher** | Student Monitoring | `/teacher/monitoring/<exam_id>/` | `monitoring` | `apps/monitoring/views.py` |
| **Teacher** | Results & Analysis | `/teacher/results/` | `results` | `apps/results/views.py` |
| **Student** | Student Dashboard | `/student/dashboard/` | `dashboard` | `apps/dashboard/views.py` |
| **Student** | Exam List | `/student/exams/` | `attempts` | `apps/attempts/views.py` |
| **Student** | Exam Room | `/student/exams/<exam_id>/attempt/` | `attempts` | `apps/attempts/views.py` |
| **Student** | Results & Review | `/student/results/` | `results` | `apps/results/views.py` |
| **Student** | Retake Check (API) | `/student/exams/<id>/retake/check/` | `attempts` | `apps/attempts/views.py` |
| **Student** | Pre-Retake Review | `/student/exams/<id>/retake/review/` | `attempts` | `apps/attempts/views.py` |
| **Student** | Retake Start | `/student/exams/<id>/retake/start/` | `attempts` | `apps/attempts/views.py` |
| **Teacher** | Retake History Modal | `/teacher/results/<eid>/student/<sid>/attempts/` | `results` | `apps/results/views.py` |
| **Student** | Attempt History | `/student/results/<eid>/attempts/` | `results` | `apps/results/views.py` |

---

## 📂 Detailed Mapping by Django App

### 1. `apps/core/` - Core Functionality & System Settings

**Handles:**

- System Settings page (`/admin/settings/`)
- Base models and mixins
- Shared utilities
- Constants and validators

**Pages:**

- ✅ **System Settings** (`/admin/settings/`)

**Key Files:**

```
apps/core/
├── views.py              # SystemSettingsView
├── models.py             # SystemSettings model
├── forms.py              # SettingsForm
└── templates/core/
    └── settings.html     # Settings page
```

**Update v1.4.1 (Branding/System Settings):**

```text
apps/core/
├── views.py              # SystemSettingsView handle Tab Branding (multipart/form-data)
├── forms.py              # Tambah BrandingSettingsForm, hapus Site Name/Site Logo dari GeneralSettingsForm
├── services.py           # get_branding_settings() + cache fallback
├── context_processors.py # branding_context(request) -> inject branding ke semua template
└── templates/core/settings.html
    # Tambah Tab Branding; Tab General tidak lagi memuat Site Name/Site Logo
```

Aturan `get_branding_settings()`:

- Cache key: `cbt_branding_settings`
- TTL: 5 menit
- Invalidate cache saat save Tab Branding: `cache.delete('cbt_branding_settings')`
- Return key category `branding` + `landing_page_enabled` dengan fallback untuk nilai kosong

Catatan URL:

- Tidak ada URL baru untuk upload.
- Form branding tetap POST ke `/admin/settings/` dengan `enctype="multipart/form-data"`.

**URLs:**

```python
# apps/core/urls.py
urlpatterns = [
    path('admin/settings/', SystemSettingsView.as_view(), name='system_settings'),
]
```

---

### 2. `apps/accounts/` - Authentication

**Handles:**

- Login page
- Logout functionality
- Session management
- User authentication backend
- Login branding block (logo, institution name, headline/subheadline, login background)

**Pages:**

- ✅ **Login Page** (`/login/`)

**Key Files:**

```
apps/accounts/
├── views.py              # LoginView, LogoutView
├── forms.py              # LoginForm
├── backends.py           # Custom auth backend
└── templates/accounts/
    ├── login.html        # Login page
    └── profile.html      # User profile (for all roles)
```

**Update v1.4.1 (Branding di Login):**

- `templates/accounts/login.html` menampilkan branding dari context `branding`:
  - `institution_logo_url`
  - `institution_name`
  - `login_page_headline`
  - `login_page_subheadline`
  - `login_page_background_url`
- Jika value kosong, template gunakan fallback default.

**URLs:**

```python
# apps/accounts/urls.py
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
```

---

### 3. `apps/users/` - User Management (Admin)

**Handles:**

- User CRUD operations (Admin only)
- User list, create, edit, delete
- Password reset by admin
- User activity logs
- **Import Users from Excel** (v1.3.0)
- Import history and reports

**Pages:**

- ✅ **User Management** (`/admin/users/`)
- ✅ **User Import** (`/admin/users/import/`)

**Key Files:**

```
apps/users/
├── views.py              # UserListView, UserCreateView, 
│                         # UserUpdateView, UserDeleteView,
│                         # ResetPasswordView,
│                         # UserImportView, UserImportConfirmView,
│                         # UserImportHistoryView, UserImportReportView,
│                         # DownloadImportTemplateView
├── forms.py              # UserCreateForm, UserEditForm, PasswordResetForm,
│                         # UserImportForm
├── services.py           # User business logic (create, update, etc.),
│                         # parse_import_file(), execute_import(),
│                         # generate_import_report()
├── importers.py          # ExcelUserImporter (parse only, no DB ops)
├── exporters.py          # ImportTemplateExporter, ImportReportExporter
├── tasks.py              # Celery task: send credentials email
└── templates/users/
    ├── user_list.html    # User list page
    ├── user_form.html    # Create/Edit user
    ├── user_detail.html  # User detail modal
    ├── reset_password.html # Password reset modal
    ├── user_import_modal.html # Import wizard (3-step)
    ├── import_history.html    # Import history table
    └── partials/
        ├── import_step1_upload.html
        ├── import_step2_preview.html
        └── import_step3_result.html
```

**URLs:**

```python
# apps/users/urls.py
urlpatterns = [
    path('admin/users/', UserListView.as_view(), name='user_list'),
    path('admin/users/create/', UserCreateView.as_view(), name='user_create'),
    path('admin/users/<uuid:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('admin/users/<uuid:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('admin/users/<uuid:pk>/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    # Import Users (v1.3.0)
    path('admin/users/import/', UserImportView.as_view(), name='user_import'),
    path('admin/users/import/confirm/', UserImportConfirmView.as_view(), name='user_import_confirm'),
    path('admin/users/import/history/', UserImportHistoryView.as_view(), name='user_import_history'),
    path('admin/users/import/<uuid:log_id>/report/', UserImportReportView.as_view(), name='user_import_report'),
    path('admin/users/import/template/<str:role>/', DownloadImportTemplateView.as_view(), name='user_import_template'),
]
```

**Notes (v1.3.0):**

- Import uses Django cache to store preview data (TTL 10 min)
- openpyxl for parsing .xlsx files
- Celery task for async email credentials
- Atomic transaction ensures full rollback on failure

---

### 4. `apps/subjects/` - Subject Management (Admin)

**Handles:**

- Subject CRUD operations (Admin only)
- Subject list, create, edit, delete
- Bulk operations (activate, deactivate, delete)
- Export subjects to Excel/CSV
- Dependency checking before deletion

**Pages:**

- ✅ **Subject Management** (`/admin/subjects/`)

**Key Files:**

```
apps/subjects/
├── views.py              # SubjectListView, SubjectCreateView,
│                         # SubjectUpdateView, SubjectDeleteView,
│                         # SubjectExportView
├── forms.py              # SubjectForm
├── services.py           # Subject business logic
├── serializers.py        # API serializers
└── templates/subjects/
    ├── subject_list.html     # Subject list page
    ├── subject_form.html     # Create/Edit subject
    └── subject_delete.html   # Delete confirmation
```

**URLs:**

```python
# apps/subjects/urls.py
urlpatterns = [
    path('admin/subjects/', SubjectListView.as_view(), name='subject_list'),
    path('admin/subjects/create/', SubjectCreateView.as_view(), name='subject_create'),
    path('admin/subjects/<uuid:pk>/edit/', SubjectUpdateView.as_view(), name='subject_edit'),
    path('admin/subjects/<uuid:pk>/delete/', SubjectDeleteView.as_view(), name='subject_delete'),
    path('admin/subjects/export/', SubjectExportView.as_view(), name='subject_export'),
]
```

**Notes:**

- Cannot delete subject with associated questions or exams
- Subject code is read-only after creation
- Code auto-converted to uppercase
- Inactive subjects excluded from dropdown selections

---

### 5. `apps/questions/` - Question Bank Management

**Handles:**

- Question CRUD operations
- Question import/export (Excel, JSON)
- Question preview
- Question categorization

**Pages:**

- ✅ **Question Bank Management** (`/teacher/question-bank/`)

**Key Files:**

```
apps/questions/
├── views.py              # QuestionListView, QuestionCreateView,
│                         # QuestionUpdateView, QuestionDeleteView,
│                         # QuestionImportView, QuestionExportView,
│                         # QuestionPreviewView
├── forms.py              # QuestionForm (multiple choice, essay, short answer)
├── services.py           # Question business logic
├── importers.py          # Excel/JSON import logic
├── exporters.py          # Excel/JSON export logic
└── templates/questions/
    ├── question_list.html    # Question bank list
    ├── question_form.html    # Create/Edit question
    ├── question_preview.html # Preview modal
    └── question_import.html  # Import page
```

**URLs:**

```python
# apps/questions/urls.py
urlpatterns = [
    path('teacher/question-bank/', QuestionListView.as_view(), name='question_list'),
    path('teacher/question-bank/create/', QuestionCreateView.as_view(), name='question_create'),
    path('teacher/question-bank/<uuid:pk>/edit/', QuestionUpdateView.as_view(), name='question_edit'),
    path('teacher/question-bank/<uuid:pk>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
    path('teacher/question-bank/<uuid:pk>/preview/', QuestionPreviewView.as_view(), name='question_preview'),
    path('teacher/question-bank/import/', QuestionImportView.as_view(), name='question_import'),
    path('teacher/question-bank/export/', QuestionExportView.as_view(), name='question_export'),
]
```

---

### 6. `apps/exams/` - Exam Management

**Handles:**

- Exam CRUD operations
- Exam wizard (multi-step form)
- Exam question assignment
- Exam settings (time, anti-cheat, navigation)
- Publish/unpublish exams

**Pages:**

- ✅ **Exam Management** (`/teacher/exams/`)

**Key Files:**

```
apps/exams/
├── views.py              # ExamListView, ExamCreateView (Wizard),
│                         # ExamUpdateView, ExamDeleteView,
│                         # ExamPublishView, ExamPreviewView
├── forms.py              # ExamWizardForms (Step1-7)
│                         # └── Step4Form memuat RetakeSettingsForm (inline, kondisional)
├── services.py           # Exam business logic
├── tasks.py              # Celery tasks (auto-publish, notifications)
└── templates/exams/
    ├── exam_list.html        # Exam list
    ├── exam_wizard.html      # Create exam (multi-step)
    │   └── partials/step4_retake_settings.html  # section retake di Step 4
    ├── exam_form.html        # Edit exam
    ├── exam_preview.html     # Preview modal
    └── exam_detail.html      # Exam detail
```

**URLs:**

```python
# apps/exams/urls.py
urlpatterns = [
    path('teacher/exams/', ExamListView.as_view(), name='exam_list'),
    path('teacher/exams/create/', ExamCreateWizard.as_view(), name='exam_create'),
    path('teacher/exams/<uuid:pk>/edit/', ExamUpdateView.as_view(), name='exam_edit'),
    path('teacher/exams/<uuid:pk>/delete/', ExamDeleteView.as_view(), name='exam_delete'),
    path('teacher/exams/<uuid:pk>/publish/', ExamPublishView.as_view(), name='exam_publish'),
    path('teacher/exams/<uuid:pk>/preview/', ExamPreviewView.as_view(), name='exam_preview'),
    path('teacher/exams/<uuid:pk>/duplicate/', ExamDuplicateView.as_view(), name='exam_duplicate'),
]
```

---

### 7. `apps/attempts/` - Exam Taking (Student)

**Handles:**

- Student exam list
- Exam room (taking exam)
- Answer submission
- Auto-save functionality
- Anti-cheat monitoring (client-side)

**Pages:**

- ✅ **Exam List** (`/student/exams/`)
- ✅ **Exam Room** (`/student/exams/<exam_id>/attempt/`)

**Key Files:**

```
apps/attempts/
├── views.py
│   # Lama : ExamListView, ExamStartView, ExamRoomView,
│   #        AnswerSubmitView, ExamSubmitView
│   # Baru tambah:
│   # RetakeCheckView       GET  → cek eligibility retake
│   # PreRetakeReviewView   GET  → tampilkan jawaban attempt sebelumnya
│   # RetakeStartView       POST → validasi → buat attempt baru → redirect
│   # AttemptHistoryAPIView GET  → JSON semua attempt siswa untuk 1 ujian
├── services.py
│   # Lama : attempt logic, auto-save, auto-submit
│   # Baru tambah:
│   # check_retake_eligibility(exam_id, student_id)
│   #   → dict: {eligible, attempts_used, max_attempts,
│   #            cooldown_remaining_seconds, next_available_at}
│   # create_retake_attempt(exam_id, student_id)
│   #   → validasi → update retake_available_from attempt sebelumnya
│   #   → buat exam_attempts baru
│   #   → raise RetakeNotAllowed / MaxAttemptsReached / CooldownActive
├── middleware.py         # Anti-cheat middleware (tidak berubah)
├── consumers.py          # WebSocket (tidak berubah)
└── templates/attempts/
    # Lama : exam_list.html, exam_start.html, exam_room.html,
    #        exam_submit_confirmation.html
    # Baru tambah:
    # retake_confirm.html       # konfirmasi sebelum mulai retake
    # pre_retake_review.html    # review jawaban sebelum retake

static/attempts/js/
    # Lama : exam_room.js, anti_cheat.js, timer.js, auto_save.js
    # Baru tambah:
    # retake_cooldown.js        # countdown timer realtime untuk cooldown
```

**URLs:**

```python
# apps/attempts/urls.py
urlpatterns = [
    # --- URL lama (tidak berubah) ---
    path('student/exams/', ExamListView.as_view(), name='student_exam_list'),
    path('student/exams/<uuid:exam_id>/start/', ExamStartView.as_view(), name='exam_start'),
    path('student/exams/<uuid:exam_id>/attempt/', ExamRoomView.as_view(), name='exam_room'),
    path('student/exams/<uuid:attempt_id>/submit/', ExamSubmitView.as_view(), name='exam_submit'),
    path('api/attempts/<uuid:attempt_id>/save-answer/', SaveAnswerAPIView.as_view(), name='save_answer'),

    # --- URL baru (retake) ---
    path('student/exams/<uuid:exam_id>/retake/check/',
         RetakeCheckView.as_view(), name='retake_check'),
    path('student/exams/<uuid:exam_id>/retake/review/',
         PreRetakeReviewView.as_view(), name='pre_retake_review'),
    path('student/exams/<uuid:exam_id>/retake/start/',
         RetakeStartView.as_view(), name='retake_start'),
    path('api/attempts/<uuid:exam_id>/history/',
         AttemptHistoryAPIView.as_view(), name='attempt_history'),
]
```

**WebSocket Routing:**

```python
# apps/attempts/consumers.py
class ExamConsumer(AsyncWebsocketConsumer):
    # Handle real-time updates during exam
```

---

### 8. `apps/monitoring/` - Live Student Monitoring

**Handles:**

- Real-time monitoring dashboard
- Live student status
- Violation tracking
- Screenshot viewing
- Manual interventions (extend time, force submit)

**Pages:**

- ✅ **Student Monitoring** (`/teacher/monitoring/<exam_id>/`)

**Key Files:**

```
apps/monitoring/
├── views.py              # MonitoringDashboardView, StudentDetailView
├── consumers.py          # WebSocket consumer for live updates
├── services.py           # Monitoring services
└── templates/monitoring/
    ├── monitoring_dashboard.html  # Main monitoring page
    └── student_detail_modal.html  # Student detail modal
```

**URLs:**

```python
# apps/monitoring/urls.py
urlpatterns = [
    path('teacher/monitoring/<uuid:exam_id>/', MonitoringDashboardView.as_view(), name='monitoring_dashboard'),
    path('teacher/monitoring/<uuid:exam_id>/student/<uuid:student_id>/', StudentDetailView.as_view(), name='student_detail'),
    # API endpoints
    path('api/monitoring/<uuid:exam_id>/extend-time/', ExtendTimeAPIView.as_view(), name='extend_time'),
    path('api/monitoring/<uuid:attempt_id>/force-submit/', ForceSubmitAPIView.as_view(), name='force_submit'),
]
```

**WebSocket Routing:**

```python
# apps/monitoring/consumers.py
class MonitoringConsumer(AsyncWebsocketConsumer):
    # Handle real-time monitoring updates
```

---

### 9. `apps/results/` - Results & Analytics

**Handles:**

- Exam results (teacher and student view)
- Answer review
- Statistics & analytics
- Grade calculation
- Export results

**Pages:**

- ✅ **Results & Analysis** (`/teacher/results/`) - Teacher view
- ✅ **Results & Review** (`/student/results/`) - Student view

**Key Files:**

```
apps/results/
├── views.py
│   # Lama : ResultsListView, ResultDetailView, AnswerReviewView, ExportResultsView
│   # Baru tambah:
│   # RetakeHistoryView       # modal riwayat attempt (teacher)
│   # StudentAttemptHistory   # section riwayat attempt (student)
├── services.py
│   # Lama : grading logic, statistics calculation
│   # Baru tambah:
│   # calculate_final_score(exam_id, student_id) → Decimal
│   #   policy 'highest': MAX(total_score) dari semua attempt yang submitted
│   #   policy 'latest' : total_score dari attempt_number terbesar
│   #   policy 'average': AVG(total_score) dari semua attempt yang submitted
│   #   Dipanggil setiap kali attempt selesai di-grade
├── calculators.py
│   # Lama : statistics calculators
│   # Baru tambah:
│   # update_exam_statistics_with_retake(exam_id)
│   #   → Recalculate avg_score, pass_rate, highest/lowest, std_dev
│   #     dari nilai FINAL per siswa (bukan raw attempt)
│   #   → Update total_retake_attempts, total_unique_students,
│   #     avg_attempts_per_student
├── tasks.py              # tidak berubah
├── exporters.py
│   # Catatan: kolom "Score" di export Excel harus berisi nilai final
│   # (via calculate_final_score), bukan total_score attempt pertama
└── templates/results/
    # Lama : results_list.html, result_detail.html,
    #        analytics_dashboard.html, answer_review.html,
    #        student_results.html
    # Baru tambah:
    # retake_history_modal.html      # modal riwayat attempt (teacher)
    # student_attempt_history.html   # section riwayat attempt (student)
```

**Update v1.4.1 (Branding di Output Cetak):**

- `apps/results/exporters.py`:
  - PDF/Excel header membaca `institution_name`, `institution_logo_url`, `institution_address`
    dari `apps.core.services.get_branding_settings()`.
  - Header sertifikat membaca `institution_name`, `institution_logo_url`, `institution_type`.
  - Jika logo kosong, header tetap dirender tanpa gambar (graceful fallback).
  - Jika nama lembaga kosong, gunakan fallback `settings.CBT_SITE_NAME`.

**URLs:**

```python
# apps/results/urls.py
urlpatterns = [
    # --- URL lama (tidak berubah) ---
    path('teacher/results/', TeacherResultsListView.as_view(), name='teacher_results'),
    path('teacher/results/<uuid:exam_id>/', ExamResultsDetailView.as_view(), name='exam_results_detail'),
    path('teacher/results/<uuid:result_id>/review/', AnswerReviewView.as_view(), name='answer_review'),
    path('teacher/results/<uuid:exam_id>/export/', ExportResultsView.as_view(), name='export_results'),
    path('student/results/', StudentResultsListView.as_view(), name='student_results'),
    path('student/results/<uuid:result_id>/', StudentResultDetailView.as_view(), name='student_result_detail'),
    path('student/results/<uuid:result_id>/review/', StudentAnswerReviewView.as_view(), name='student_answer_review'),

    # --- URL baru (retake) ---
    path('teacher/results/<uuid:exam_id>/student/<uuid:student_id>/attempts/',
         RetakeHistoryView.as_view(), name='retake_history'),
    path('student/results/<uuid:exam_id>/attempts/',
         StudentAttemptHistory.as_view(), name='student_attempt_history'),
]
```

---

### 10. `apps/proctoring/` - Screenshot Proctoring

**Handles:**

- Screenshot upload
- Screenshot storage
- Screenshot viewing
- Flagged screenshots

**Pages:**

- No dedicated page (integrated into Monitoring)
- Screenshots viewed in Student Detail Modal

**Key Files:**

```
apps/proctoring/
├── views.py              # ScreenshotUploadAPIView, ScreenshotListView
├── services.py           # Screenshot processing
├── tasks.py              # Celery tasks for screenshot processing
└── storage.py            # Custom storage backend
```

**URLs:**

```python
# apps/proctoring/urls.py
urlpatterns = [
    # API endpoint for screenshot upload
    path('api/proctoring/upload/', ScreenshotUploadAPIView.as_view(), name='screenshot_upload'),
    path('api/proctoring/<uuid:attempt_id>/screenshots/', ScreenshotListAPIView.as_view(), name='screenshot_list'),
]
```

---

### 11. `apps/notifications/` - Notifications System

**Handles:**

- Notification list
- Mark as read
- Real-time notifications (WebSocket)

**Pages:**

- No dedicated page (notification dropdown in navbar)

**Key Files:**

```
apps/notifications/
├── views.py              # NotificationListView, MarkAsReadView
├── services.py           # Notification service
├── tasks.py              # Email notification tasks
├── consumers.py          # WebSocket consumer
└── templates/notifications/
    └── notification_list.html  # Notification dropdown content
```

**URLs:**

```python
# apps/notifications/urls.py
urlpatterns = [
    path('api/notifications/', NotificationListAPIView.as_view(), name='notification_list'),
    path('api/notifications/<uuid:pk>/mark-read/', MarkAsReadAPIView.as_view(), name='mark_as_read'),
    path('api/notifications/mark-all-read/', MarkAllAsReadAPIView.as_view(), name='mark_all_as_read'),
]
```

---

### 12. `apps/analytics/` - System Analytics (Admin)

**Handles:**

- Admin analytics dashboard
- System-wide reports
- User statistics
- Exam statistics

**Pages:**

- ✅ **Analytics & Reports** (`/admin/analytics/`)

**Key Files:**

```
apps/analytics/
├── views.py              # AdminAnalyticsView, SystemReportsView
├── services.py           # Analytics services
├── tasks.py              # Periodic analytics tasks
└── templates/analytics/
    ├── admin_analytics.html   # Admin analytics dashboard
    └── reports.html           # System reports
```

**Catatan Konsistensi Query (`apps/analytics/services.py`):**

⚠ Semua query admin analytics (total_completed, pass_rate, avg_score):  
HARUS menggunakan `v_student_final_results` atau `calculate_final_score()`  
agar siswa yang melakukan retake tidak dihitung double.

**URLs:**

```python
# apps/analytics/urls.py
urlpatterns = [
    path('admin/analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('admin/analytics/reports/', SystemReportsView.as_view(), name='system_reports'),
    path('admin/analytics/export/', ExportAnalyticsView.as_view(), name='export_analytics'),
]
```

---

### 13. `apps/dashboard/` - Dashboards (All Roles)

**Handles:**

- Landing page
- Admin dashboard
- Teacher dashboard
- Student dashboard
- Landing page branding toggle (`landing_page_enabled`) via `get_branding_settings()`

**Pages:**

- ✅ **Landing Page** (`/`)
- ✅ **Admin Dashboard** (`/admin/dashboard/`)
- ✅ **Teacher Dashboard** (`/teacher/dashboard/`)
- ✅ **Student Dashboard** (`/student/dashboard/`)

**Key Files:**

```
apps/dashboard/
├── views.py              # LandingView, AdminDashboardView,
│                         # TeacherDashboardView, StudentDashboardView
└── templates/dashboard/
    ├── landing.html           # Landing page
    ├── admin_dashboard.html   # Admin dashboard
    ├── teacher_dashboard.html # Teacher dashboard
    └── student_dashboard.html # Student dashboard
```

**Catatan Konsistensi Query (`apps/dashboard/views.py`):**

Tambahan untuk `LandingView`:

- Wajib memanggil `apps.core.services.get_branding_settings()` (cache-first).
- Jika `branding['landing_page_enabled'] == False` -> `redirect('login')` (HTTP 302).
- View tidak melakukan query DB branding secara langsung.

⚠ `StudentDashboardView`:  
`RecentResultsWidget` → query harus menggunakan `calculate_final_score()`  
atau `v_student_final_results`, BUKAN `ORDER BY exam_results.created_at`  
(berpotensi mengembalikan record attempt pertama).  
`PerformanceSummary` → `COUNT` ujian UNIK via `GROUP BY exam_id`,  
bukan `COUNT` semua `exam_results`.

**URLs:**

```python
# apps/dashboard/urls.py
urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('teacher/dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('student/dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
]
```

---

### 13. Global Templates & Branding Context

**Template updates:**

- `templates/base.html`
  - Inject CSS variable: `--cbt-primary` dari `branding.primary_color` (fallback `#0d6efd`)
  - Favicon dinamis dari `branding.institution_favicon_url`
- `templates/base_admin.html`, `templates/base_teacher.html`, `templates/base_student.html`
  - Navbar logo menggunakan `branding.institution_logo_url` (fallback logo default)

**Config updates:**

- `config/settings.py`
  - Tambahkan context processor: `apps.core.context_processors.branding_context`
  - Pastikan `MEDIA_ROOT` dan `MEDIA_URL` aktif untuk file branding

**URL note:**

- Patch branding tidak menambah URL baru.
- Semua upload branding ditangani di `/admin/settings/` (POST multipart).

## 🔀 URL Routing Flow

### Root URLs Configuration

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin (for development)
    path('django-admin/', admin.site.urls),
    
    # App URLs
    path('', include('apps.dashboard.urls')),       # Landing + Dashboards
    path('', include('apps.accounts.urls')),        # Login/Logout
    path('', include('apps.users.urls')),           # User Management
    path('', include('apps.core.urls')),            # System Settings
    path('', include('apps.questions.urls')),       # Question Bank
    path('', include('apps.exams.urls')),           # Exam Management
    path('', include('apps.attempts.urls')),        # Exam Taking
    path('', include('apps.monitoring.urls')),      # Live Monitoring
    path('', include('apps.results.urls')),         # Results
    path('', include('apps.proctoring.urls')),      # Proctoring API
    path('', include('apps.notifications.urls')),   # Notifications API
    path('', include('apps.analytics.urls')),       # Analytics
    
    # API (optional, if using REST API)
    path('api/', include('api.v1.urls')),
]
```

---

## 📊 Summary Matrix

### Pages by Role

#### **Public (2 pages)**

| Page | App | View |
|------|-----|------|
| Landing Page | `dashboard` | `LandingView` |
| Login Page | `accounts` | `LoginView` |

#### **Admin (5 pages)**

| Page | App | View |
|------|-----|------|
| Admin Dashboard | `dashboard` | `AdminDashboardView` |
| User Management | `users` | `UserListView`, `UserCreateView`, etc. |
| Subject Management | `subjects` | `SubjectListView`, `SubjectCreateView`, etc. |
| System Settings | `core` | `SystemSettingsView` |
| Analytics & Reports | `analytics` | `AdminAnalyticsView` |

#### **Teacher (5 pages)**

| Page | App | View |
|------|-----|------|
| Teacher Dashboard | `dashboard` | `TeacherDashboardView` |
| Question Bank | `questions` | `QuestionListView`, `QuestionCreateView`, etc. |
| Exam Management | `exams` | `ExamListView`, `ExamCreateWizard`, etc. |
| Student Monitoring | `monitoring` | `MonitoringDashboardView` |
| Results & Analysis | `results` | `TeacherResultsListView` |

#### **Student (4 pages)**

| Page | App | View |
|------|-----|------|
| Student Dashboard | `dashboard` | `StudentDashboardView` |
| Exam List | `attempts` | `ExamListView` |
| Exam Room | `attempts` | `ExamRoomView` |
| Results & Review | `results` | `StudentResultsListView` |

---

## 🎯 Key Points

### 1. **Single Responsibility**

Setiap app memiliki tanggung jawab yang jelas:

- `accounts` → Authentication only
- `users` → User CRUD only (Admin)
- `questions` → Question management only
- `exams` → Exam management only
- `attempts` → Exam taking only
- `monitoring` → Live monitoring only
- `results` → Results & analytics only

### 2. **Dashboard Centralization**

`apps/dashboard/` menangani semua dashboard pages untuk consistency:

- Landing page
- Admin dashboard
- Teacher dashboard
- Student dashboard

### 3. **Shared Components**

`apps/core/` menyediakan:

- Base models
- Mixins
- Utilities
- Constants
- System settings

### 4. **API Separation**

API endpoints bisa dipisah ke folder `api/` atau tetap di masing-masing app:

- Auto-save answers → `apps/attempts/views.py` (API view)
- Screenshot upload → `apps/proctoring/views.py` (API view)
- Notifications → `apps/notifications/views.py` (API view)

### 5. **Real-time Features**

WebSocket consumers ada di:

- `apps/attempts/consumers.py` → Exam room updates
- `apps/monitoring/consumers.py` → Live monitoring
- `apps/notifications/consumers.py` → Real-time notifications

---

## 🔧 Development Workflow

### Creating a New Page

1. **Identify the app** yang bertanggung jawab
2. **Create view** di `apps/<app_name>/views.py`
3. **Create template** di `apps/<app_name>/templates/<app_name>/`
4. **Add URL** di `apps/<app_name>/urls.py`
5. **Include URL** di `config/urls.py` (jika belum)
6. **Create form** (jika needed) di `apps/<app_name>/forms.py`
7. **Add business logic** di `apps/<app_name>/services.py`

### Example: Adding Essay Grading Page

```python
# 1. Determine: This belongs to 'results' app

# 2. Create view in apps/results/views.py
class EssayGradingView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = StudentAnswer
    template_name = 'results/essay_grading.html'
    
    def test_func(self):
        return self.request.user.role == 'teacher'

# 3. Create template in apps/results/templates/results/essay_grading.html

# 4. Add URL in apps/results/urls.py
path('teacher/results/essay/<uuid:answer_id>/grade/', 
     EssayGradingView.as_view(), 
     name='essay_grading'),

# 5. Already included in config/urls.py

# 6. Create form in apps/results/forms.py
class EssayGradingForm(forms.ModelForm):
    class Meta:
        model = EssayGrading
        fields = ['points_awarded', 'feedback']

# 7. Add business logic in apps/results/services.py
def grade_essay(answer_id, points, feedback, graded_by):
    # Grading logic here
    pass
```

---

## Master Checklist

```text
━━ DATABASE MIGRATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] exams: 5 kolom retake settings
[ ] exam_attempts: kolom retake_available_from
[ ] exam_statistics: 3 kolom retake-aware
[ ] CREATE INDEX idx_exam_attempts_retake
[ ] CREATE INDEX idx_exam_results_student_exam
[ ] CREATE VIEW v_student_final_results
[ ] COMMENT ON TABLE (exams, exam_attempts, exam_statistics)

━━ apps/subjects ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] SubjectListView, SubjectCreateView, SubjectUpdateView, SubjectDeleteView
[ ] SubjectForm (code, name, description, is_active)
[ ] SubjectExportView (Excel/CSV)
[ ] can_delete() method — check question_count & exam_count
[ ] Template: subject_list.html, subject_form.html
[ ] Bulk operations: activate, deactivate, delete

━━ apps/exams ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Step4Form + RetakeSettingsForm (inline, kondisional)
[ ] Template partial: step4_retake_settings.html
[ ] Step 7: ringkasan retake di Review & Publish
[ ] Badge [🔁 Nx] di ExamListView

━━ apps/attempts ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] RetakeCheckView
[ ] PreRetakeReviewView
[ ] RetakeStartView
[ ] AttemptHistoryAPIView
[ ] check_retake_eligibility() di services.py
[ ] create_retake_attempt() di services.py
[ ] Custom exceptions: RetakeNotAllowed, MaxAttemptsReached, CooldownActive
[ ] Template: retake_confirm.html
[ ] Template: pre_retake_review.html
[ ] JS: retake_cooldown.js
[ ] ExamCards: badge sisa + tombol Ujian Ulang + countdown cooldown
[ ] ExamDetailModal: blok Info Retake
[ ] ExamHeader: AttemptCounterBadge
[ ] SubmitConfirmationModal: info sisa retake

━━ apps/results ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] calculate_final_score(exam_id, student_id)
[ ] update_exam_statistics_with_retake(exam_id)
[ ] RetakeHistoryView (teacher)
[ ] StudentAttemptHistory (student)
[ ] Template: retake_history_modal.html
[ ] Template: student_attempt_history.html
[ ] StudentResultsTable: kolom Attempts + tooltip nilai final
[ ] exporters.py: kolom Score = nilai final
[ ] ResultDetailView: info nilai final + badge ★
[ ] MyRetakeHistorySection: tabel + tombol + countdown cooldown

━━ apps/dashboard ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] StudentDashboardView: RecentResultsWidget → nilai final
[ ] StudentDashboardView: PerformanceSummary → ujian unik & nilai final

━━ apps/analytics ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Semua query → v_student_final_results / calculate_final_score()

━━ apps/monitoring ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Attempt badge di StudentsMonitoringGrid
[ ] Tabel Riwayat Attempt di StudentDetailModal

━━ TESTING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] allow_retake=false → tidak ada tombol retake sama sekali
[ ] Cooldown aktif → tombol disabled + countdown live
[ ] Max attempt tercapai → tombol retake hilang permanen
[ ] score_policy=highest → nilai final = MAX(total_score)
[ ] score_policy=latest  → nilai final = score attempt terbesar attempt_number
[ ] score_policy=average → nilai final = AVG(total_score)
[ ] retake_show_review=true → halaman review muncul sebelum konfirmasi
[ ] retake_show_review=false → langsung ke konfirmasi
[ ] PerformanceSummary siswa: tidak double-count attempt
[ ] Admin analytics pass_rate: tidak double-count retake
[ ] Export Excel: kolom Score = nilai final
[ ] UNIQUE(exam_id, student_id, attempt_number): tidak bisa duplicate
[ ] v_student_final_results: policy highest/latest mengembalikan baris yang benar
[ ] AttemptCounterBadge: hanya muncul di attempt ke-2 ke atas
```

```text
━━ SYSTEM SETTINGS & BRANDING (PATCH v1.4.1) ━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Hapus seed lama: site_name/site_logo dari category general
[ ] Tambah seed branding: institution_name, institution_type, institution_address,
    institution_phone, institution_email, institution_website,
    institution_logo_url, institution_logo_dark_url, institution_favicon_url,
    login_page_headline, login_page_subheadline, login_page_background_url, primary_color
[ ] Tambah seed general: landing_page_enabled
[ ] COMMENT ON TABLE system_settings diperbarui (general/branding/email/security + fallback "")

━━ apps/core ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Tambah BrandingSettingsForm
[ ] GeneralSettingsForm: hapus Site Name & Site Logo
[ ] SystemSettingsView: handle POST multipart Tab Branding + simpan file ke MEDIA_ROOT/branding/
[ ] get_branding_settings(): cache key cbt_branding_settings, TTL 5 menit, fallback value
[ ] Invalidate cache branding setelah save
[ ] context_processors.branding_context aktif
[ ] templates/core/settings.html: Tab Branding + update Tab General

━━ apps/dashboard ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] LandingView memanggil get_branding_settings()
[ ] landing_page_enabled=false -> redirect 302 ke /login/
[ ] landing.html memakai context branding (logo, institution_name, headline)

━━ apps/accounts ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] login.html memuat blok branding (logo, institution_name, headline/subheadline, background)

━━ apps/results ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] exporters.py laporan PDF/Excel: header institution_name/logo/address
[ ] exporters.py sertifikat: header institution_name/logo/institution_type
[ ] Fallback graceful jika logo kosong

━━ Template Global ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] base.html: CSS variable --cbt-primary dari branding.primary_color
[ ] base.html: favicon dinamis dari branding.institution_favicon_url
[ ] base_admin/base_teacher/base_student: navbar logo dari branding.institution_logo_url

━━ VALIDASI ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] institution_name kosong -> fallback settings.CBT_SITE_NAME
[ ] primary_color kosong -> fallback #0d6efd
[ ] login_page_headline kosong -> fallback "Selamat Datang"
[ ] landing_page_enabled=false -> GET / redirect 302
[ ] Simpan Tab Branding -> cache invalidate -> perubahan langsung terlihat
[ ] Upload format/ukuran invalid -> ditolak dengan error per field
```

---

## ✅ Checklist Verification

Pastikan setiap page di IA memiliki:

- [x] Django app yang menangani
- [x] View yang jelas
- [x] URL route
- [x] Template
- [x] Form (jika needed)
- [x] Service layer (untuk business logic)
- [x] Permissions/Access control

---

**Dengan mapping ini, development team dapat dengan mudah menemukan di mana setiap fitur harus diimplementasikan dan bagaimana strukturnya!**
