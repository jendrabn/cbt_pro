# CBT Pro - Complete Documentation

## 📋 Table of Contents

### [Part I: Project Overview & Architecture](#part-i-project-overview--architecture)

1. [Introduction](#1-introduction)
2. [Application Structure](#2-application-structure)
3. [Role-Based Access Control](#3-role-based-access-control)
4. [Site Map & Page Structure](#4-site-map--page-structure)

---

### [Part II: Database Design](#part-ii-database-design)

1. [Database Design Overview](#5-database-design-overview)
   - [Design Principles](#51-design-principles)
   - [Table Categories](#52-table-categories)
2. [MySQL DDL Schema](#6-mysql-ddl-schema)
   - [Core Tables](#61-core-tables)
   - [Question Management Tables](#62-question-management-tables)
   - [Exam Management Tables](#63-exam-management-tables)
   - [Exam Execution Tables](#64-exam-execution-tables)
   - [Results & Analytics Tables](#65-results--analytics-tables)
   - [System Tables](#66-system-tables)
3. [Database Relationships](#7-database-relationships)

---

### [Part III: Django Project Structure](#part-iii-django-project-structure)

1. [Project Directory Layout](#8-project-directory-layout)
2. [Django Apps Architecture](#9-django-apps-architecture)
3. [Settings — config/settings.py](#10-settings-structure)
4. [Environment Configuration — .env.example](#11-environment-configuration)
5. [Installation & Setup](#12-installation--setup)
    - [Install Packages](#121-install-packages)
    - [Database Migration Commands](#122-database-migration-commands)
    - [config/asgi.py](#123-configasgipy)
    - [config/celery.py](#124-configcelerypy)
    - [Dockerfile](#125-dockerfile)
    - [.gitignore](#126-gitignore)
6. [Key Implementation Notes](#13-key-implementation-notes)
    - [context_processors.py](#441-context_processorspy)
    - [decorators.py & mixins.py](#442-decoratorspy)
    - [EmailOrUsernameBackend](#443-emailorusernamebackend)

---

### [Part IV: Frontend Stack & Design System](#part-iv-frontend-stack--design-system)

1. [Technology Stack Overview](#14-technology-stack-overview)
2. [Technology Details](#16-technology-details)
    - [Bootstrap 5](#161-bootstrap-5)
    - [Remix Icon](#162-remix-icon)
    - [Alpine.js](#163-alpinejs)
    - [Axios](#164-axios)
    - [Chart.js](#165-chartjs)
    - [TinyMCE](#166-tinymce)
    - [SortableJS](#167-sortablejs)
3. [SCSS Architecture & Design System](#17-scss-architecture--design-system)
    - [theme.scss — Bootstrap Variable Overrides](#161-themescss--bootstrap-variable-overrides)
    - [Prinsip Styling — Bootstrap-First](#162-prinsip-styling--bootstrap-first)
4. [Base Templates & Layouts](#18-base-templates--layouts)
    - [base.html](#181-basehtml)
    - [layouts/base_dashboard.html](#182-layoutsbase_dashboardhtml)
    - [layouts/base_exam.html](#183-layoutsbase_examhtml)
5. [Partials / Reusable Components](#19-partials--reusable-components)
    - [partials/topbar.html](#191-partialstopbarhtml)
    - [partials/sidebar.html](#192-partialssidebarhtml)
    - [partials/user_menu.html](#193-partialsuser_menuhtml)
    - [partials/breadcrumb.html](#194-partialsbreadcrumbhtml)
    - [partials/alerts.html](#195-partialsalertshtml)
    - [partials/footer.html](#196-partialsfooterhtml)
    - [partials/toast.html](#197-partialstoasthtml)
    - [partials/confirm_modal.html](#198-partialsconfirm_modalhtml)
    - [partials/page_header.html](#199-partialspage_headerhtml)
6. [File Organization](#20-file-organization)
7. [Page Examples](#21-page-examples)
    - [Login Page](#211-login-page)
    - [Exam Room](#212-exam-room)
8. [JavaScript — exam-room.js](#22-javascript--exam-roomjs)
9. [Best Practices](#23-best-practices)
10. [CDN Quick Reference](#24-cdn-quick-reference)

---

### [Part V: Information Architecture](#part-v-information-architecture)

1. [Key Adjustments from Requirements](#25-key-adjustments-from-requirements)
    - [Authentication System](#251-authentication-system)
    - [URL Convention](#252-url-convention)
    - [Question Navigation Feature](#253-question-navigation-feature)
2. [Page Details & Components](#26-page-details--components)
    - [Public Pages](#261-public-pages)
    - [Shared Auth Pages](#262-shared-auth-pages)
    - [Admin Dashboard Pages](#263-admin-dashboard-pages)
    - [Teacher Dashboard Pages](#264-teacher-dashboard-pages)
    - [Student Dashboard Pages](#265-student-dashboard-pages)
3. [Global Components](#27-global-components)
4. [Real-time Features](#28-real-time-features)
5. [Data Flow Examples](#29-data-flow-examples)
6. [Key User Interactions](#30-key-user-interactions)
7. [Responsive Considerations](#31-responsive-considerations)
8. [Security Considerations](#32-security-considerations)
9. [Development Priorities](#33-development-priorities)
10. [Component Checklist](#34-component-checklist)

---

### [Part VI: Page to Django App Mapping](#part-vi-page-to-django-app-mapping)

1. [Complete Mapping Table](#35-complete-mapping-table)
2. [Detailed Mapping by Django App](#36-detailed-mapping-by-django-app)
3. [URL Routing Flow](#37-url-routing-flow)
4. [Summary Matrix](#38-summary-matrix)
5. [Development Workflow](#39-development-workflow)

---

### [Part VII: Appendices](#part-vii-appendices)

1. [Database Views](#40-database-views)
2. [Initial Data](#41-initial-data)
3. [Deployment Configuration](#42-deployment-configuration)
4. [Testing Strategy](#43-testing-strategy)
5. [Key Implementation Notes & Code Examples](#44-key-implementation-notes)
    - [context_processors.py](#441-context_processorspy)
    - [decorators.py & mixins.py](#442-decoratorspy)
    - [EmailOrUsernameBackend](#443-emailorusernamebackend)
6. [Database Migration Commands](#45-database-migration-commands)

---

## Part I: Project Overview & Architecture

### 1. Introduction

This document provides comprehensive documentation for the Advanced CBT (Computer-Based Testing) Application. It covers database design, Django project structure, frontend stack, information architecture, and page-to-app mapping.

**Key Features:**

- Multi-role authentication (Admin, Teacher, Student)
- Question bank management with multiple question types
- Exam creation with advanced settings
- Live exam monitoring
- Anti-cheat mechanisms
- Real-time analytics
- Screenshot proctoring
- Profile management & password change for all users

---

### 2. Application Structure

#### Role-Based Access

- **Admin**: Full access to all modules
- **Teacher**: Question management, exam management, and student monitoring
- **Student**: Exam access and results

---

### 3. Role-Based Access Control

| Role    | Access Level       | Key Modules                                                    |
|---------|--------------------|----------------------------------------------------------------|
| Admin   | Full System Access | User Management, Subject Management, System Settings, Analytics |
| Teacher | Content & Monitoring | Question Bank, Exam Management, Student Monitoring, Results  |
| Student | Exam Participation | Exam List, Exam Room, Results & Review                         |

---

### 4. Site Map & Page Structure

```
├── Public Pages
│   ├── Landing Page (/)
│   └── Login Page (/login/)
│
├── Shared (All Authenticated Users)
│   ├── Profile (/profile/)
│   └── Change Password (/change-password/)
│
├── Admin Dashboard
│   ├── Dashboard Overview (/admin/dashboard/)
│   ├── User Management (/admin/users/)
│   ├── Subject Management (/admin/subjects/)
│   ├── System Settings (/admin/settings/)
│   └── Analytics & Reports (/admin/analytics/)
│
├── Teacher Dashboard
│   ├── Dashboard Overview (/teacher/dashboard/)
│   ├── Question Bank Management (/teacher/question-bank/)
│   ├── Exam Management (/teacher/exams/)
│   ├── Student Monitoring (/teacher/monitoring/<exam_id>/)
│   └── Results & Analysis (/teacher/results/)
│
└── Student Dashboard
    ├── Dashboard Overview (/student/dashboard/)
    ├── Exam List (/student/exams/)
    ├── Exam Room (/student/exams/<exam_id>/attempt/)
    └── Results & Review (/student/results/)
```

---

## Part II: Database Design

### 5. Database Design Overview

#### 5.1 Design Principles

- **Normalization**: All tables follow 3NF (Third Normal Form)
- **Timestamps**: Every table has `created_at` and `updated_at`
- **Foreign Keys**: Defined after primary key tables
- **Indexing**: Strategic indexes for performance
- **Constraints**: Proper constraints for data integrity
- **Django Integration**: Core user tables leverage Django's `auth_user` via `AbstractUser`

#### 5.2 Table Categories

1. **Core Tables**: Django `auth_user` (extended via `AbstractUser`), `user_profiles`
2. **Question Management**: Questions, Options, Categories
3. **Exam Management**: Exams, Exam Questions, Assignments
4. **Exam Execution**: Exam Attempts, Answers, Violations
5. **Results & Analytics**: Results, Statistics
6. **System**: Settings, Logs, Notifications

---

### 6. MySQL DDL Schema

> **Note**: Django's `AbstractUser` already creates the `auth_user` table with fields: `id`, `username`, `email`, `password`, `first_name`, `last_name`, `is_staff`, `is_active`, `is_superuser`, `last_login`, `date_joined`. We extend it by adding `role` field in the custom `User` model. The raw DDL below shows the effective schema after Django migrations.

#### 6.1 Core Tables

```sql
-- ============================================================
-- auth_user (Django default, extended via AbstractUser)
-- Custom fields added: role
-- ============================================================
CREATE TABLE auth_user (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(150) NOT NULL UNIQUE,
    email       VARCHAR(254) NOT NULL UNIQUE,
    password    VARCHAR(128) NOT NULL,          -- Django hashed password
    first_name  VARCHAR(150) NOT NULL DEFAULT '',
    last_name   VARCHAR(150) NOT NULL DEFAULT '',
    role        VARCHAR(20)  NOT NULL DEFAULT 'student'
                    COMMENT 'admin | teacher | student',
    is_staff    TINYINT(1)   NOT NULL DEFAULT 0,
    is_active   TINYINT(1)   NOT NULL DEFAULT 1,
    is_superuser TINYINT(1)  NOT NULL DEFAULT 0,
    last_login  DATETIME(6),
    date_joined DATETIME(6)  NOT NULL,
    INDEX idx_user_role (role),
    INDEX idx_user_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- user_profiles  (1:1 extension of auth_user)
-- ============================================================
CREATE TABLE user_profiles (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id                 INT UNSIGNED NOT NULL UNIQUE,
    teacher_id              VARCHAR(50),
    student_id              VARCHAR(50),
    phone_number            VARCHAR(20),
    subject_specialization  VARCHAR(100),   -- for teacher
    class_grade             VARCHAR(50),    -- for student
    profile_picture         VARCHAR(500),   -- relative path under MEDIA_ROOT
    bio                     TEXT,
    created_at              DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at              DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_profile_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- user_activity_logs
-- ============================================================
CREATE TABLE user_activity_logs (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED NOT NULL,
    action      VARCHAR(100) NOT NULL,
    description TEXT,
    ip_address  VARCHAR(45),
    user_agent  TEXT,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_ual_user (user_id),
    INDEX idx_ual_action (action),
    CONSTRAINT fk_ual_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Django Model Design — `apps/accounts/models.py`:**

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Adds 'role' field; all other default fields are inherited.
    """
    ROLE_ADMIN   = 'admin'
    ROLE_TEACHER = 'teacher'
    ROLE_STUDENT = 'student'
    ROLE_CHOICES = [
        (ROLE_ADMIN,   'Admin'),
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_STUDENT, 'Student'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
    )
    email = models.EmailField(unique=True)

    # Use email or username for login (backend handles this)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'role']

    class Meta:
        db_table = 'auth_user'  # reuse Django's default table name
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT

    def get_profile_picture_url(self):
        if self.profile.profile_picture:
            return self.profile.profile_picture.url
        return '/static/images/default-avatar.png'


class UserProfile(models.Model):
    """
    1:1 extension of the User model.
    Auto-created via post_save signal when a User is created.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    teacher_id             = models.CharField(max_length=50, blank=True)
    student_id             = models.CharField(max_length=50, blank=True)
    phone_number           = models.CharField(max_length=20, blank=True)
    subject_specialization = models.CharField(max_length=100, blank=True)  # teacher
    class_grade            = models.CharField(max_length=50, blank=True)   # student
    profile_picture        = models.ImageField(
                                upload_to='profiles/%Y/%m/',
                                null=True, blank=True,
                             )
    bio                    = models.TextField(blank=True)
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'

    def __str__(self):
        return f"Profile of {self.user.username}"
```

**Signal — `apps/accounts/signals.py`:**

```python
# apps/accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile whenever a new User is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
```

**App config — `apps/accounts/apps.py`:**

```python
# apps/accounts/apps.py
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = 'apps.accounts'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import apps.accounts.signals  # noqa: F401 — connects signal handlers
```

#### 6.2 Question Management Tables

```sql
-- subjects
CREATE TABLE subjects (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    code        VARCHAR(20) UNIQUE,
    description TEXT,
    is_active   TINYINT(1)  NOT NULL DEFAULT 1,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                    ON UPDATE CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- question_categories
CREATE TABLE question_categories (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id   INT UNSIGNED,
    is_active   TINYINT(1)  NOT NULL DEFAULT 1,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                    ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_qcat_parent
        FOREIGN KEY (parent_id) REFERENCES question_categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- questions
CREATE TABLE questions (
    id                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    created_by            INT UNSIGNED NOT NULL,
    subject_id            INT UNSIGNED NOT NULL,
    category_id           INT UNSIGNED,
    question_type         VARCHAR(20) NOT NULL
                              COMMENT 'multiple_choice | essay | short_answer',
    question_text         TEXT NOT NULL,
    question_image        VARCHAR(500),
    points                DECIMAL(5,2) NOT NULL DEFAULT 1.00,
    difficulty_level      VARCHAR(20) COMMENT 'easy | medium | hard',
    explanation           TEXT,
    allow_previous        TINYINT(1) DEFAULT 1,
    allow_next            TINYINT(1) DEFAULT 1,
    force_sequential      TINYINT(1) DEFAULT 0,
    time_limit_seconds    INT,
    is_active             TINYINT(1) NOT NULL DEFAULT 1,
    usage_count           INT NOT NULL DEFAULT 0,
    created_at            DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at            DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                              ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_q_subject (subject_id),
    INDEX idx_q_creator (created_by),
    INDEX idx_q_type (question_type),
    CONSTRAINT fk_q_creator  FOREIGN KEY (created_by)   REFERENCES auth_user(id) ON DELETE RESTRICT,
    CONSTRAINT fk_q_subject  FOREIGN KEY (subject_id)   REFERENCES subjects(id) ON DELETE RESTRICT,
    CONSTRAINT fk_q_category FOREIGN KEY (category_id)  REFERENCES question_categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- question_options
CREATE TABLE question_options (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    question_id    INT UNSIGNED NOT NULL,
    option_letter  CHAR(1) NOT NULL COMMENT 'A|B|C|D|E',
    option_text    TEXT NOT NULL,
    option_image   VARCHAR(500),
    is_correct     TINYINT(1) NOT NULL DEFAULT 0,
    display_order  INT NOT NULL,
    created_at     DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at     DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                       ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_option_letter (question_id, option_letter),
    CONSTRAINT fk_opt_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- question_answers (for essay/short_answer)
CREATE TABLE question_answers (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    question_id      INT UNSIGNED NOT NULL,
    answer_text      TEXT NOT NULL,
    keywords         JSON,
    is_case_sensitive TINYINT(1) DEFAULT 0,
    max_word_count   INT,
    created_at       DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at       DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                         ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_ans_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- question_tags
CREATE TABLE question_tags (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(50) NOT NULL UNIQUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE question_tag_relations (
    question_id INT UNSIGNED NOT NULL,
    tag_id      INT UNSIGNED NOT NULL,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (question_id, tag_id),
    CONSTRAINT fk_qtr_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    CONSTRAINT fk_qtr_tag      FOREIGN KEY (tag_id)      REFERENCES question_tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 6.3 Exam Management Tables

```sql
-- exams
CREATE TABLE exams (
    id                           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    created_by                   INT UNSIGNED NOT NULL,
    subject_id                   INT UNSIGNED NOT NULL,
    title                        VARCHAR(255) NOT NULL,
    description                  TEXT,
    instructions                 TEXT,
    start_time                   DATETIME(6) NOT NULL,
    end_time                     DATETIME(6) NOT NULL,
    duration_minutes             INT NOT NULL,
    passing_score                DECIMAL(5,2) NOT NULL,
    total_points                 DECIMAL(7,2) DEFAULT 0,
    randomize_questions          TINYINT(1) DEFAULT 0,
    randomize_options            TINYINT(1) DEFAULT 0,
    show_results_immediately     TINYINT(1) DEFAULT 0,
    allow_review                 TINYINT(1) DEFAULT 1,
    override_question_navigation TINYINT(1) DEFAULT 0,
    global_allow_previous        TINYINT(1) DEFAULT 1,
    global_allow_next            TINYINT(1) DEFAULT 1,
    global_force_sequential      TINYINT(1) DEFAULT 0,
    require_fullscreen           TINYINT(1) DEFAULT 1,
    detect_tab_switch            TINYINT(1) DEFAULT 1,
    enable_screenshot_proctoring TINYINT(1) DEFAULT 0,
    screenshot_interval_seconds  INT DEFAULT 300,
    max_violations_allowed       INT DEFAULT 3,
    max_attempts                 INT NOT NULL DEFAULT 1
                                     COMMENT 'Max attempts per student; 0 = unlimited',
    allow_reattempt              TINYINT(1) NOT NULL DEFAULT 0
                                     COMMENT '1 = students may retake if attempts_used < max_attempts',
    scoring_method               VARCHAR(20) NOT NULL DEFAULT 'highest'
                                     COMMENT 'highest|last — which attempt score is used as final',
    status                       VARCHAR(20) NOT NULL DEFAULT 'draft'
                                     COMMENT 'draft|published|ongoing|completed|cancelled',
    created_at                   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at                   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                     ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_exam_status (status),
    INDEX idx_exam_creator (created_by),
    CONSTRAINT fk_exam_creator  FOREIGN KEY (created_by)  REFERENCES auth_user(id) ON DELETE RESTRICT,
    CONSTRAINT fk_exam_subject  FOREIGN KEY (subject_id)  REFERENCES subjects(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- exam_questions
CREATE TABLE exam_questions (
    id                       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    exam_id                  INT UNSIGNED NOT NULL,
    question_id              INT UNSIGNED NOT NULL,
    display_order            INT NOT NULL,
    points_override          DECIMAL(5,2),
    override_navigation      TINYINT(1) DEFAULT 0,
    allow_previous_override  TINYINT(1),
    allow_next_override      TINYINT(1),
    force_sequential_override TINYINT(1),
    created_at               DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at               DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                 ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_eq_question (exam_id, question_id),
    UNIQUE KEY uq_eq_order    (exam_id, display_order),
    CONSTRAINT fk_eq_exam     FOREIGN KEY (exam_id)     REFERENCES exams(id) ON DELETE CASCADE,
    CONSTRAINT fk_eq_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- classes
CREATE TABLE classes (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    grade_level   VARCHAR(50),
    academic_year VARCHAR(20),
    is_active     TINYINT(1)  NOT NULL DEFAULT 1,
    created_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                      ON UPDATE CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- class_students
CREATE TABLE class_students (
    class_id    INT UNSIGNED NOT NULL,
    student_id  INT UNSIGNED NOT NULL,
    enrolled_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (class_id, student_id),
    CONSTRAINT fk_cs_class   FOREIGN KEY (class_id)   REFERENCES classes(id) ON DELETE CASCADE,
    CONSTRAINT fk_cs_student FOREIGN KEY (student_id) REFERENCES auth_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- exam_assignments
CREATE TABLE exam_assignments (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    exam_id          INT UNSIGNED NOT NULL,
    assigned_to_type VARCHAR(20) NOT NULL COMMENT 'class | student',
    class_id         INT UNSIGNED,
    student_id       INT UNSIGNED,
    assigned_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_ea_exam    FOREIGN KEY (exam_id)    REFERENCES exams(id) ON DELETE CASCADE,
    CONSTRAINT fk_ea_class   FOREIGN KEY (class_id)   REFERENCES classes(id) ON DELETE CASCADE,
    CONSTRAINT fk_ea_student FOREIGN KEY (student_id) REFERENCES auth_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 6.4 Exam Execution Tables

```sql
-- exam_attempts
CREATE TABLE exam_attempts (
    id                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    exam_id               INT UNSIGNED NOT NULL,
    student_id            INT UNSIGNED NOT NULL,
    attempt_number        INT NOT NULL DEFAULT 1,
    start_time            DATETIME(6),
    end_time              DATETIME(6),
    submit_time           DATETIME(6),
    status                VARCHAR(20) NOT NULL DEFAULT 'not_started'
                              COMMENT 'not_started|in_progress|submitted|auto_submitted|grading|completed',
    total_score           DECIMAL(7,2) NOT NULL DEFAULT 0,
    percentage            DECIMAL(5,2) NOT NULL DEFAULT 0,
    passed                TINYINT(1)   NOT NULL DEFAULT 0,
    ip_address            VARCHAR(45),
    user_agent            TEXT,
    browser_fingerprint   VARCHAR(255),
    time_spent_seconds    INT NOT NULL DEFAULT 0,
    created_at            DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at            DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                              ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_ea_attempt (exam_id, student_id, attempt_number),
    INDEX idx_ea_status (status),
    CONSTRAINT fk_ea2_exam    FOREIGN KEY (exam_id)    REFERENCES exams(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ea2_student FOREIGN KEY (student_id) REFERENCES auth_user(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- student_answers
CREATE TABLE student_answers (
    id                   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    attempt_id           INT UNSIGNED NOT NULL,
    question_id          INT UNSIGNED NOT NULL,
    answer_type          VARCHAR(20) NOT NULL COMMENT 'multiple_choice|essay|short_answer',
    selected_option_id   INT UNSIGNED,
    answer_text          TEXT,
    is_correct           TINYINT(1),
    points_earned        DECIMAL(5,2) NOT NULL DEFAULT 0,
    points_possible      DECIMAL(5,2) NOT NULL,
    is_marked_for_review TINYINT(1)  NOT NULL DEFAULT 0,
    time_spent_seconds   INT NOT NULL DEFAULT 0,
    answer_order         INT,
    created_at           DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at           DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                             ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_sa_attempt  (attempt_id),
    INDEX idx_sa_question (question_id),
    CONSTRAINT fk_sa_attempt  FOREIGN KEY (attempt_id)         REFERENCES exam_attempts(id) ON DELETE CASCADE,
    CONSTRAINT fk_sa_question FOREIGN KEY (question_id)        REFERENCES questions(id) ON DELETE RESTRICT,
    CONSTRAINT fk_sa_option   FOREIGN KEY (selected_option_id) REFERENCES question_options(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- exam_violations
CREATE TABLE exam_violations (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    attempt_id     INT UNSIGNED NOT NULL,
    violation_type VARCHAR(50) NOT NULL COMMENT 'tab_switch|fullscreen_exit|copy_paste|right_click',
    description    TEXT,
    occurred_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_ev_attempt (attempt_id),
    CONSTRAINT fk_ev_attempt FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- proctoring_screenshots
CREATE TABLE proctoring_screenshots (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    attempt_id   INT UNSIGNED NOT NULL,
    exam_id      INT UNSIGNED NOT NULL,
    student_id   INT UNSIGNED NOT NULL,
    file_path    VARCHAR(500) NOT NULL,
    file_size    INT,
    captured_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    is_flagged   TINYINT(1) NOT NULL DEFAULT 0,
    flag_reason  TEXT,
    INDEX idx_ps_attempt (attempt_id),
    CONSTRAINT fk_ps_attempt  FOREIGN KEY (attempt_id)  REFERENCES exam_attempts(id) ON DELETE CASCADE,
    CONSTRAINT fk_ps_exam     FOREIGN KEY (exam_id)     REFERENCES exams(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ps_student  FOREIGN KEY (student_id)  REFERENCES auth_user(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 6.5 Results & Analytics Tables

```sql
-- exam_results
CREATE TABLE exam_results (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    attempt_id   INT UNSIGNED NOT NULL UNIQUE,
    exam_id      INT UNSIGNED NOT NULL,
    student_id   INT UNSIGNED NOT NULL,
    total_score  DECIMAL(7,2) NOT NULL DEFAULT 0,
    percentage   DECIMAL(5,2) NOT NULL DEFAULT 0,
    passed       TINYINT(1)   NOT NULL DEFAULT 0,
    rank         INT,
    grade        VARCHAR(5),
    feedback     TEXT,
    graded_by    INT UNSIGNED,
    graded_at    DATETIME(6),
    created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                     ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_er_exam    (exam_id),
    INDEX idx_er_student (student_id),
    CONSTRAINT fk_er_attempt  FOREIGN KEY (attempt_id)  REFERENCES exam_attempts(id) ON DELETE RESTRICT,
    CONSTRAINT fk_er_exam     FOREIGN KEY (exam_id)     REFERENCES exams(id) ON DELETE RESTRICT,
    CONSTRAINT fk_er_student  FOREIGN KEY (student_id)  REFERENCES auth_user(id) ON DELETE RESTRICT,
    CONSTRAINT fk_er_grader   FOREIGN KEY (graded_by)   REFERENCES auth_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- question_statistics
CREATE TABLE question_statistics (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    question_id         INT UNSIGNED NOT NULL UNIQUE,
    times_used          INT NOT NULL DEFAULT 0,
    times_answered      INT NOT NULL DEFAULT 0,
    times_correct       INT NOT NULL DEFAULT 0,
    times_wrong         INT NOT NULL DEFAULT 0,
    times_skipped       INT NOT NULL DEFAULT 0,
    difficulty_index    DECIMAL(5,4),
    discrimination_index DECIMAL(5,4),
    average_time_seconds DECIMAL(8,2),
    last_calculated_at  DATETIME(6),
    updated_at          DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                            ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_qs_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- option_statistics
CREATE TABLE option_statistics (
    id                       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    option_id                INT UNSIGNED NOT NULL UNIQUE,
    times_selected           INT NOT NULL DEFAULT 0,
    selection_percentage     DECIMAL(5,2),
    high_performers_selected INT NOT NULL DEFAULT 0,
    low_performers_selected  INT NOT NULL DEFAULT 0,
    last_calculated_at       DATETIME(6),
    updated_at               DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                 ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_ostat_option FOREIGN KEY (option_id) REFERENCES question_options(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- exam_statistics
CREATE TABLE exam_statistics (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    exam_id           INT UNSIGNED NOT NULL UNIQUE,
    total_assigned    INT NOT NULL DEFAULT 0,
    total_started     INT NOT NULL DEFAULT 0,
    total_completed   INT NOT NULL DEFAULT 0,
    completion_rate   DECIMAL(5,2),
    average_score     DECIMAL(7,2),
    median_score      DECIMAL(7,2),
    highest_score     DECIMAL(7,2),
    lowest_score      DECIMAL(7,2),
    standard_deviation DECIMAL(7,4),
    total_passed      INT NOT NULL DEFAULT 0,
    pass_rate         DECIMAL(5,2),
    average_time_seconds INT,
    last_calculated_at DATETIME(6),
    updated_at        DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                          ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_exs_exam FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 6.6 System Tables

```sql
-- system_settings
CREATE TABLE system_settings (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    setting_key   VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type  VARCHAR(20) NOT NULL COMMENT 'string|number|boolean|json',
    category      VARCHAR(50) NOT NULL,
    description   TEXT,
    is_public     TINYINT(1) NOT NULL DEFAULT 0,
    updated_by    INT UNSIGNED,
    created_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                      ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_ss_user FOREIGN KEY (updated_by) REFERENCES auth_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- notifications
CREATE TABLE notifications (
    id                    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id               INT UNSIGNED NOT NULL,
    title                 VARCHAR(255) NOT NULL,
    message               TEXT NOT NULL,
    notification_type     VARCHAR(50) NOT NULL COMMENT 'info|success|warning|error|announcement',
    related_entity_type   VARCHAR(50),
    related_entity_id     INT UNSIGNED,
    is_read               TINYINT(1) NOT NULL DEFAULT 0,
    read_at               DATETIME(6),
    created_at            DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_notif_user  (user_id),
    INDEX idx_notif_read  (is_read),
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- system_logs
CREATE TABLE system_logs (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    log_level       VARCHAR(20) NOT NULL COMMENT 'DEBUG|INFO|WARNING|ERROR|CRITICAL',
    logger_name     VARCHAR(100),
    message         TEXT NOT NULL,
    module          VARCHAR(100),
    function_name   VARCHAR(100),
    line_number     INT,
    exception_info  TEXT,
    user_id         INT UNSIGNED,
    ip_address      VARCHAR(45),
    created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_sl_level (log_level),
    INDEX idx_sl_user  (user_id),
    CONSTRAINT fk_sl_user FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- certificates
CREATE TABLE certificates (
    id                 INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    result_id          INT UNSIGNED NOT NULL UNIQUE,
    certificate_number VARCHAR(100) NOT NULL UNIQUE,
    certificate_url    VARCHAR(500),
    issued_at          DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    is_valid           TINYINT(1) NOT NULL DEFAULT 1,
    revoked_at         DATETIME(6),
    revoked_reason     TEXT,
    CONSTRAINT fk_cert_result FOREIGN KEY (result_id) REFERENCES exam_results(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 7. Database Relationships

- **auth_user** → **user_profiles** (1:1, via `UserProfile.user` OneToOneField)
- **auth_user** → **questions** (1:N, as `created_by`)
- **subjects** → **questions** (1:N)
- **questions** → **question_options** (1:N)
- **exams** → **exam_questions** (1:N)
- **exams** → **exam_attempts** (1:N)
- **exam_attempts** → **student_answers** (1:N)
- **exam_attempts** → **exam_violations** (1:N)
- **exam_attempts** → **proctoring_screenshots** (1:N)
- **exam_attempts** → **exam_results** (1:1)

---

## Part III: Django Project Structure

### 8. Project Directory Layout

```
cbt_pro/
│
├── manage.py
├── .env                             # Environment variables (never commit)
├── .env.example                     # Template for .env
├── .gitignore
├── README.md
├── package.json                     # npm: bootstrap + sass, scripts build/watch CSS
├── node_modules/                    # Bootstrap SCSS source (gitignore)
├── pytest.ini
│
├── config/                          # Project configuration
│   ├── __init__.py
│   ├── celery.py                    # Celery application instance
│   ├── settings.py              # Single settings file (DEBUG/security via .env)
│   ├── urls.py
│   ├── asgi.py                      # ASGI entrypoint (Django Channels / WebSocket)
│   └── wsgi.py
│
├── apps/                            # Django applications
│   ├── core/                        # Base models, utilities, system settings
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # SystemSettings, SystemLog
│   │   ├── views.py                 # Settings page (admin)
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── context_processors.py   # Global template context (site name, etc.)
│   │   ├── decorators.py            # role_required, admin_required, etc.
│   │   ├── mixins.py                # RoleRequiredMixin, etc.
│   │   └── templates/
│   │       └── core/
│   │           └── settings.html
│   │
│   ├── accounts/                    # Authentication + Profile + Change Password
│   │   ├── __init__.py
│   │   ├── apps.py                  # AccountsConfig — imports signals in ready()
│   │   ├── models.py                # User (AbstractUser), UserProfile, UserActivityLog
│   │   ├── views.py                 # login, logout, profile, change_password
│   │   ├── forms.py                 # LoginForm, ProfileForm, ChangePasswordForm
│   │   ├── backends.py              # Custom auth backend (email or username)
│   │   ├── signals.py               # Auto-create UserProfile on User creation
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── templates/
│   │       └── accounts/
│   │           ├── login.html
│   │           ├── profile.html
│   │           └── change_password.html
│   │
│   ├── users/                       # Admin-only: User CRUD & Management
│   │   ├── __init__.py
│   │   ├── views.py                 # UserListView, UserCreateView, UserUpdateView, etc.
│   │   ├── forms.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── templates/
│   │       └── users/
│   │           ├── list.html
│   │           ├── create.html
│   │           ├── detail.html
│   │           └── edit.html
│   │
│   ├── subjects/                    # Admin-only: Subject CRUD
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── templates/
│   │       └── subjects/
│   │           ├── list.html
│   │           ├── create.html
│   │           └── edit.html
│   │
│   ├── questions/                   # Teacher: Question Bank
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── services.py
│   │   ├── importers.py
│   │   ├── exporters.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── templates/
│   │       └── questions/
│   │           ├── list.html
│   │           ├── create.html
│   │           ├── edit.html
│   │           └── detail.html
│   │
│   ├── exams/                       # Teacher: Exam Management
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── templates/
│   │       └── exams/
│   │           ├── list.html
│   │           ├── create.html
│   │           ├── edit.html
│   │           ├── detail.html
│   │           └── wizard/
│   │               ├── step_info.html
│   │               ├── step_questions.html
│   │               ├── step_settings.html
│   │               └── step_assign.html
│   │
│   ├── attempts/                    # Student: Exam Taking
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── consumers.py
│   │   ├── middleware.py
│   │   ├── urls.py
│   │   └── templates/
│   │       └── attempts/
│   │           ├── exam_list.html
│   │           ├── exam_detail.html
│   │           └── exam_room.html
│   │
│   ├── monitoring/                  # Teacher: Live Monitoring
│   │   ├── __init__.py
│   │   ├── views.py
│   │   ├── consumers.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   └── templates/
│   │       └── monitoring/
│   │           └── live.html
│   │
│   ├── results/                     # Teacher + Student: Results & Analytics
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── calculators.py
│   │   ├── exporters.py
│   │   ├── urls.py
│   │   └── templates/
│   │       └── results/
│   │           ├── teacher_list.html
│   │           ├── teacher_detail.html
│   │           ├── student_list.html
│   │           ├── student_detail.html
│   │           └── essay_grading.html
│   │
│   ├── proctoring/                  # Screenshot Proctoring
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── storage.py
│   │   └── urls.py
│   │
│   ├── notifications/               # Notification System
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── consumers.py
│   │   ├── urls.py
│   │   └── templates/
│   │       └── notifications/
│   │           └── list.html
│   │
│   ├── analytics/                   # Admin: System Analytics
│   │   ├── __init__.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── urls.py
│   │   └── templates/
│   │       └── analytics/
│   │           └── dashboard.html
│   │
│   └── dashboard/                   # All Roles: Dashboards + Landing
│       ├── __init__.py
│       ├── views.py
│       ├── urls.py
│       └── templates/
│           └── dashboard/
│               ├── landing.html
│               ├── admin.html
│               ├── teacher.html
│               └── student.html
│
├── templates/                       # Global templates
│   ├── base.html                    # Root base (CDN, meta, global blocks)
│   ├── layouts/
│   │   ├── base_dashboard.html      # Dashboard layout (extends base.html)
│   │   └── base_exam.html           # Exam room layout (full screen, no sidebar)
│   ├── partials/
│   │   ├── topbar.html              # Dashboard topbar (toggle, breadcrumb, user menu)
│   │   ├── sidebar.html             # Collapsible sidebar (role-aware nav)
│   │   ├── user_menu.html           # Avatar + name + role dropdown (profile/pw/logout)
│   │   ├── breadcrumb.html          # Breadcrumb partial (used inside topbar)
│   │   ├── alerts.html              # Django messages alerts
│   │   ├── footer.html              # Landing page footer
│   │   ├── toast.html               # Alpine.js toast notifications
│   │   ├── confirm_modal.html       # Reusable delete confirmation modal
│   │   └── page_header.html             # Page header: title, subtitle, breadcrumb, action buttons
│   └── errors/
│       ├── 403.html
│       ├── 404.html
│       └── 500.html
│
├── static/                          # Global static files
│   ├── scss/
│   │   ├── theme.scss               # Bootstrap variable overrides (primary color, etc.)
│   │   └── custom.scss              # Custom classes: badge-soft-*, sidebar, stat-card, etc.
│   ├── css/
│   │   ├── theme.css                # Compiled from theme.scss
│   │   └── custom.css               # Compiled from custom.scss
│   ├── js/
│   │   ├── main.js                  # Global JS (CSRF, Axios setup, showToast helper)
│   │   └── pages/
│   │       ├── exam-room.js         # Exam room logic (timer, save, anti-cheat)
│   │       ├── question-form.js     # Question create/edit form logic
│   │       ├── exam-builder.js      # Exam wizard + question selection
│   │       └── monitoring.js        # Live monitoring WebSocket client
│   └── images/
│       ├── logo-B-dark.png   # Logo untuk background terang (landing navbar)
│       └── logo-B-light.png  # Logo untuk background gelap (sidebar, login)
│       └── default-avatar.png
│
├── media/                           # User-uploaded files (gitignored)
│   ├── profiles/                    # Profile pictures
│   ├── questions/                   # Question images
│   ├── screenshots/                 # Proctoring screenshots
│   ├── certificates/                # Generated certificates
│   └── exports/                     # Export downloads
│
├── tests/                           # Global tests
│   ├── conftest.py
│   ├── factories.py
│   └── integration/
│
├── scripts/                         # Utility scripts
│   ├── seed_data.py
│   └── create_admin.py
│
└── deployment/                      # Deployment configs
    └── docker/
        ├── Dockerfile
        ├── docker-compose.yml
        └── nginx.conf
```

---

### 9. Django Apps Architecture

| App             | Responsibility                               | Key Models                                       |
|-----------------|----------------------------------------------|--------------------------------------------------|
| `core`          | Base utilities, system settings, decorators  | SystemSettings, SystemLog                        |
| `accounts`      | Auth, Profile, Change Password               | User (AbstractUser), UserProfile, UserActivityLog |
| `users`         | Admin: User CRUD                             | (uses accounts.User)                             |
| `subjects`      | Admin: Subject CRUD                          | Subject                                          |
| `questions`     | Teacher: Question Bank                       | Question, QuestionOption, QuestionAnswer         |
| `exams`         | Teacher: Exam Management                     | Exam, ExamQuestion, Class, ExamAssignment        |
| `attempts`      | Student: Exam List & Exam Room               | ExamAttempt, StudentAnswer, ExamViolation        |
| `monitoring`    | Teacher: Live Monitoring (WebSocket)         | —                                                |
| `results`       | Teacher + Student: Results & Analytics       | ExamResult, ExamStatistics, QuestionStatistics   |
| `proctoring`    | Screenshot Proctoring                        | ProctoringScreenshot                             |
| `notifications` | Notification System                          | Notification                                     |
| `analytics`     | Admin: System Analytics                      | —                                                |
| `dashboard`     | All Roles: Dashboards + Landing Page         | —                                                |

---

### 10. Settings Structure

```python
# config/settings.py

from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)
environ.Env.read_env(BASE_DIR / '.env')

# ─── Core ─────────────────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY')
DEBUG       = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS = [
    'daphne',                        # Must be FIRST for Channels ASGI support
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'channels',
    'django_celery_beat',
    'django_celery_results',
    'crispy_forms',
    'crispy_bootstrap5',
    'tinymce',
    'import_export',
    'django_extensions',

    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.users',
    'apps.subjects',
    'apps.questions',
    'apps.exams',
    'apps.attempts',
    'apps.monitoring',
    'apps.results',
    'apps.proctoring',
    'apps.notifications',
    'apps.analytics',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files (dev + production)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.ContentSecurityPolicyMiddleware',  # Django 6.0 built-in CSP
]

ROOT_URLCONF = 'config.urls'

# ─── Content Security Policy (Django 6.0) ─────────────────────────
from django.utils.csp import CSP
SECURE_CSP = {
    'default-src': [CSP.SELF],
    'script-src':  [CSP.SELF, 'https://cdn.jsdelivr.net', CSP.NONCE],
    'style-src':   [CSP.SELF, 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com'],
    'font-src':    [CSP.SELF, 'https://fonts.gstatic.com', 'https://cdn.jsdelivr.net'],
    'img-src':     [CSP.SELF, 'data:', 'blob:'],
    'connect-src': [CSP.SELF, "ws:", "wss:"],  # WebSocket
    'frame-ancestors': [CSP.NONE],
}
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION  = 'config.asgi.application'

# ─── Auth ──────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/login/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Database (MySQL) ──────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':     env('DB_NAME'),
        'USER':     env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST':     env('DB_HOST', default='localhost'),
        'PORT':     env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ─── Channels / WebSocket ─────────────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(env('REDIS_HOST', default='127.0.0.1'),
                       env.int('REDIS_PORT', default=6379))],
        },
    },
}

# ─── Celery ───────────────────────────────────────────────────────
CELERY_BROKER_URL       = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND   = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')
CELERY_BEAT_SCHEDULER   = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TIMEZONE         = 'Asia/Jakarta'
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)  # True saat testing

# ─── TinyMCE ──────────────────────────────────────────────────────
TINYMCE_DEFAULT_CONFIG = {
    'height': 400,
    'plugins': 'lists link image code table',
    'toolbar': 'undo redo | blocks | bold italic | bullist numlist | link image | code',
    'license_key': env('TINYMCE_API_KEY', default='gpl'),
}

# ─── Static & Media ──────────────────────────────────────────────
STATIC_URL  = env('STATIC_URL', default='/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL  = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Templates ────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_settings',  # site_name, notifications
            ],
        },
    },
]

# ─── Crispy Forms ─────────────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK          = 'bootstrap5'

# ─── Session ──────────────────────────────────────────────────────
SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', default=7200)

# ─── Internationalisation ─────────────────────────────────────────
LANGUAGE_CODE = 'id'
TIME_ZONE     = 'Asia/Jakarta'
USE_I18N      = True
USE_TZ        = True

# ─── Logging ─────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': env('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ─── Message Tags (align Django messages with Bootstrap classes) ──
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG:   'secondary',
    messages.INFO:    'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR:   'danger',
}

# ─── Debug Toolbar (dev only) ─────────────────────────────────
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1']

# ─── Security Headers (non-debug / production) ────────────────
if not DEBUG:
    CSRF_COOKIE_SECURE            = True
    SESSION_COOKIE_SECURE         = True
    SECURE_SSL_REDIRECT           = env.bool('SECURE_SSL_REDIRECT', default=True)
    SECURE_HSTS_SECONDS           = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD           = True
    SECURE_CONTENT_TYPE_NOSNIFF   = True
    # Django 6.x: use STORAGES dict (STATICFILES_STORAGE is deprecated)
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }

# ─── Email ────────────────────────────────────────────────────
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST          = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT          = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS       = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER     = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = env('DEFAULT_FROM_EMAIL', default='CBT Pro <noreply@cbtpro.com>')

# ─── Sentry (production error tracking) ──────────────────────
_sentry_dsn = env('SENTRY_DSN', default='')
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.2,
        )
    except ImportError:
        pass  # sentry-sdk not installed
```

---

### 11. Environment Configuration

```dotenv
# ================================================================
# .env.example — copy to .env and fill in your values
# ================================================================

# ── Application ─────────────────────────────────────────────────
DEBUG=True
SECRET_KEY=your-very-long-random-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# ── Database (MySQL) ─────────────────────────────────────────────
DB_NAME=cbt_pro
DB_USER=cbt_user
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=3306

# ── Redis ────────────────────────────────────────────────────────
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://127.0.0.1:6379/0

# ── Celery ───────────────────────────────────────────────────────
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2

# ── TinyMCE ──────────────────────────────────────────────────────
TINYMCE_API_KEY=your-tinymce-cloud-api-key

# ── Static & Media ───────────────────────────────────────────────
STATIC_URL=/static/
MEDIA_URL=/media/

# ── Session & Security ───────────────────────────────────────────
SESSION_COOKIE_AGE=7200
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False

# ── Email (optional — for future features) ───────────────────────
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=CBT Pro <noreply@cbtpro.com>

# ── Logging ──────────────────────────────────────────────────────
LOG_LEVEL=DEBUG

# ── Sentry (production error tracking) ──────────────────────────
SENTRY_DSN=

# ── Site Info ────────────────────────────────────────────────────
SITE_NAME=CBT Pro
SITE_URL=http://localhost:8000
```

> **Important:** Add `.env` to `.gitignore`. Always use `.env.example` as the committed reference.

---

### 12. Installation & Setup

#### 12.1 Install Packages

```bash
# 1. Frontend build (wajib sebelum compile SCSS)
npm install bootstrap@5.3.8 sass
```

`package.json` wajib memiliki scripts:

```json
{
  "scripts": {
    "build:css": "sass static/scss/theme.scss static/css/theme.css && sass static/scss/custom.scss static/css/custom.css",
    "watch:css": "sass --watch static/scss/theme.scss static/css/theme.css & sass --watch static/scss/custom.scss static/css/custom.css"
  },
  "dependencies": {
    "bootstrap": "^5.3.8",
    "sass": "latest"
  }
}
```

Compile: `npm run build:css` — Watch: `npm run watch:css`

```bash
# 2. Python packages
# Core
pip install "django>=6.0.3,<6.1" django-environ django-extensions

# Database — MySQL
pip install mysqlclient django-model-utils

# Authentication
pip install bcrypt cryptography

# WebSocket
pip install channels channels-redis daphne

# Celery
pip install celery redis django-celery-beat django-celery-results

# File Processing
pip install Pillow python-magic openpyxl pandas xlsxwriter

# PDF Generation
pip install reportlab weasyprint

# Rich Text Editor
pip install django-tinymce

# Forms
pip install django-crispy-forms crispy-bootstrap5

# Import/Export
pip install django-import-export

# Analytics
pip install numpy scipy

# Static Files
pip install whitenoise

# Monitoring & Logging
pip install sentry-sdk django-debug-toolbar

# Testing
pip install pytest pytest-django pytest-cov factory-boy faker

# Code Quality
pip install black flake8 isort
```

#### 12.2 Database Migration Commands

```bash
# Create initial migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser (admin role auto-set if using createsuperuser)
python manage.py createsuperuser

# Load initial data
python manage.py loaddata initial_data.json

# Backup MySQL database
mysqldump -u root -p cbt_pro > backup.sql

# Restore MySQL database
mysql -u root -p cbt_pro < backup.sql

# Create migration for specific app
python manage.py makemigrations accounts

# Show SQL for a migration
python manage.py sqlmigrate accounts 0001
```


---

### 12.3 config/asgi.py

```python
# config/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

# Import consumers after Django setup
from apps.monitoring.consumers import MonitoringConsumer       # noqa
from apps.notifications.consumers import NotificationConsumer  # noqa
from apps.attempts.consumers import AttemptConsumer            # noqa

websocket_urlpatterns = [
    path('ws/monitoring/<int:exam_id>/',   MonitoringConsumer.as_asgi()),
    path('ws/notifications/',              NotificationConsumer.as_asgi()),
    path('ws/attempt/<int:attempt_id>/',   AttemptConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    ),
})
```

---

### 12.4 config/celery.py

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('cbt_pro')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

```python
# config/__init__.py  — auto-load Celery when Django starts
from .celery import app as celery_app  # noqa
__all__ = ('celery_app',)
```

---

### 12.5 Dockerfile

```dockerfile
# deployment/docker/Dockerfile
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# System deps for mysqlclient, Pillow, WeasyPrint + Node.js for SCSS compile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libmagic1 \
    gettext \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    django python-dotenv \
    djangorestframework django-cors-headers django-environ django-extensions \
    django-crispy-forms crispy-bootstrap5 django-allauth django-import-export \
    django-model-utils django-timezone-field django-tinymce \
    celery django-celery-beat django_celery_results channels channels_redis \
    mysqlclient redis \
    pillow openpyxl python-magic reportlab weasyprint \
    pytest pytest-django pytest-cov factory_boy faker \
    black flake8 isort mypy pylint

COPY . .

# Install npm deps + compile SCSS (Bootstrap harus ada di node_modules)
RUN npm install && \
    npm run build:css

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
```

---

### 12.6 .gitignore

```gitignore
# .gitignore
.env
*.pyc
__pycache__/
*.pyo
.DS_Store
db.sqlite3
test_db.sqlite3
staticfiles/
media/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.pytest_cache/
.mypy_cache/
node_modules/
```

---

### 13. Key Implementation Notes

1. **Django AbstractUser**: Custom `User` model in `apps/accounts` extends `AbstractUser`. Set `AUTH_USER_MODEL = 'accounts.User'` **before** first migration. Never change this after data exists.
2. **db_table Override**: Use `Meta.db_table = 'auth_user'` in the custom User model to keep the standard table name. Django's `accounts` app migration creates this table; the default `django.contrib.auth` migration for `auth_user` is replaced automatically.
3. **UserProfile Signal**: Auto-create `UserProfile` via `post_save` signal in `apps/accounts/signals.py` — import in `apps/accounts/apps.py` `ready()` method.
4. **MySQL charset**: Always use `utf8mb4` for full Unicode support (emoji, Arabic, etc.).
5. **Integer PKs**: Switched from UUID to auto-increment `BigAutoField` (via `DEFAULT_AUTO_FIELD`) for MySQL InnoDB performance.
6. **Indexing**: Foreign keys and frequently filtered columns (status, role, is_active) have indexes.
7. **Single settings.py**: Semua konfigurasi ada di `config/settings.py`. Perilaku dev vs production dikontrol sepenuhnya melalui `.env` (DEBUG=True/False, SECURE_SSL_REDIRECT, EMAIL_BACKEND, dll). Tidak ada settings split.
8. **Django 6.0**: Project ini menggunakan Django 6.0.3 (latest stable). Fitur baru yang dimanfaatkan: (a) `ContentSecurityPolicyMiddleware` + `SECURE_CSP` untuk CSP header bawaan tanpa library tambahan, (b) Template partials (`{% partialdef %}`) untuk reusable template fragments. Python minimum 3.12.

---

## Part IV: Frontend Stack & Design System

### 14. Technology Stack Overview

| #   | Technology      | Version  | Purpose                              |
|-----|-----------------|----------|--------------------------------------|
| 1   | Django Templates | Django 6.x | Server-side HTML rendering          |
| 2   | Bootstrap 5     | v5.3.8   | CSS framework & UI components        |
| 3   | Remix Icon      | v4.9.0   | Icon library (2,800+ icons)          |
| 4   | Alpine.js       | v3.15.8  | Lightweight JS & reactivity          |
| 5   | Axios           | v1.13.6   | HTTP/AJAX calls                      |
| 6   | Chart.js        | v4.5.1   | Data visualization                   |
| 7   | TinyMCE         | v6+      | Rich text editor                     |
| 8   | SortableJS      | v1.15.2  | Drag & drop ordering                 |
| 9   | Sass (SCSS)     | —        | CSS preprocessing (theme + custom)   |

**Principles:**

- Native Bootstrap components — no custom component frameworks
- Bootstrap di-install via npm; SCSS dikompilasi dengan `npm run build:css` (Bootstrap + override = satu `theme.css`)
- All AJAX via Axios + Alpine.js
- Django server-side rendering first, JS enhances progressively
- Buttons use standard size by default; only `btn-sm` for table row actions

---

### 15. UI Design System

> Panduan ini **wajib dibaca oleh AI agent** sebelum membangun template apapun. Semua keputusan visual harus mengikuti panduan ini.

#### 15.1 Filosofi UI

CBT Pro adalah aplikasi **profesional untuk institusi pendidikan** — bukan aplikasi konsumen. UI harus terasa:
- **Bersih & fokus** — tidak ada elemen dekoratif berlebihan
- **Terpercaya** — warna konsisten, tipografi rapi, spacing proporsional
- **Efisien** — pengguna bisa menyelesaikan tugasnya dengan klik minimal

#### 15.2 Color Usage

Warna didefinisikan di `theme.scss`. Selalu gunakan CSS variable Bootstrap, bukan hex langsung.

| Konteks | Warna |
|---------|-------|
| Aksi utama (submit, tambah, konfirmasi) | `btn-primary` / `bg-primary` |
| Aksi destruktif (hapus, nonaktifkan) | `btn-danger` / `text-danger` |
| Informasi / netral | `btn-secondary` / `text-secondary` |
| Sukses / aktif | `text-success` / `badge-soft-success` |
| Peringatan | `text-warning` / `badge-soft-warning` |
| Section terang | `bg-white` atau `bg-light` |
| Section gelap (CTA, statistik) | `bg-dark` atau primary dark dari theme |

#### 15.3 Status Badge — Wajib Soft Color

**Semua badge status di seluruh aplikasi wajib menggunakan soft color** — bukan warna solid Bootstrap default.

Definisikan di `custom.scss`:

```scss
// Soft badge variants — digunakan di seluruh aplikasi
@each $color in (primary, secondary, success, danger, warning, info) {
  .badge-soft-#{$color} {
    color: var(--bs-#{$color});
    background-color: rgba(var(--bs-#{$color}-rgb), 0.15);
    font-weight: 500;
  }
}
```

**Mapping status → badge class:**

| Status | Class |
|--------|-------|
| Aktif / Lulus / Selesai / Benar | `badge badge-soft-success` |
| Nonaktif / Gagal / Salah | `badge badge-soft-danger` |
| Menunggu / Draft / Belum Mulai | `badge badge-soft-warning` |
| Sedang Berjalan / Live | `badge badge-soft-primary` |
| Dijadwalkan / Pending Review | `badge badge-soft-info` |
| Diarsipkan / Tidak Relevan | `badge badge-soft-secondary` |
| Role: Admin | `badge badge-soft-danger` |
| Role: Guru | `badge badge-soft-primary` |
| Role: Siswa | `badge badge-soft-success` |

#### 15.4 Typography Hierarchy

| Elemen | Class Bootstrap |
|--------|----------------|
| Judul halaman (hero/landing) | `display-4` atau `h1 fw-bold` |
| Judul section landing | `h2 fw-bold text-center` |
| Judul halaman dashboard | `h4 fw-semibold` |
| Judul card / widget | `h6 fw-semibold` atau `fw-medium` |
| Label form | `form-label fw-semibold` |
| Teks deskripsi / subteks | `text-muted` |
| Teks kecil pendukung | `small text-muted` |

#### 15.5 Spacing Rhythm

- Section vertikal (landing page): `py-5` minimum, `py-6` ideal (tambah via custom.scss jika perlu)
- Card body: `p-4` standar, `p-3` untuk card kompak
- Antar elemen dalam card: `mb-3` atau `gap-3`
- Grid gap: `g-4` standar untuk card grid

#### 15.6 Component Conventions

| Komponen | Konvensi |
|----------|----------|
| Tombol aksi utama halaman | `btn btn-primary` (standar size) |
| Tombol di kolom aksi tabel | `btn btn-sm btn-outline-primary` / `btn-sm btn-outline-danger` |
| Tombol batal/kembali | `btn btn-outline-secondary` |
| Input form | `form-control`, selalu dalam `mb-3`. Wajib `is-invalid` + `.invalid-feedback` jika ada error (lihat section 15.8) |
| Icon dalam tombol | Remix Icon `me-1` atau `me-2` sebelum teks |
| Tabel data | `table table-hover align-middle`, dibungkus `table-responsive` |
| Kartu dashboard | `card border-0 shadow-sm` |
| Modal konfirmasi hapus | Gunakan `partials/confirm_modal.html` |
| Toast notifikasi | Gunakan `showToast()` via Alpine.js event |

#### 15.7 Layout Patterns

**Dashboard pages** (semua halaman setelah login):
- Extend `layouts/base_dashboard.html`
- Sidebar fixed kiri + topbar sticky + konten kanan
- Konten dimulai dengan `PageHeader` (judul + subtitle + breadcrumb + tombol aksi)
- Lalu konten utama (card, tabel, form)

**Landing & Login**:
- Extend `base.html` langsung
- Full-width, tidak ada sidebar

**Exam Room**:
- Extend `layouts/base_exam.html`
- Full-screen, tidak ada sidebar/topbar

#### 15.8 Form Validation — Wajib di Semua Form

**Aturan wajib:** Setiap form di seluruh aplikasi HARUS menampilkan error menggunakan mekanisme berikut.

##### A. Field-level validation — Bootstrap `is-invalid` + `.invalid-feedback`

Setiap `<input>`, `<select>`, `<textarea>` yang memiliki error Django wajib diberi class `is-invalid`, diikuti elemen `.invalid-feedback` langsung di bawahnya.

**Pattern wajib untuk setiap field:**

```html
<div class="mb-3">
    <label for="{{ form.field_name.id_for_label }}" class="form-label fw-semibold">
        Label Field
    </label>
    <input type="text"
           id="{{ form.field_name.id_for_label }}"
           name="{{ form.field_name.html_name }}"
           class="form-control {% if form.field_name.errors %}is-invalid{% endif %}"
           value="{{ form.field_name.value|default:'' }}">
    {% if form.field_name.errors %}
    <div class="invalid-feedback">
        {% for error in form.field_name.errors %}{{ error }}{% if not forloop.last %} {% endif %}{% endfor %}
    </div>
    {% endif %}
</div>
```

**Untuk `input-group` (input dengan ikon/tombol):**

```html
<div class="mb-3">
    <label for="{{ form.username.id_for_label }}" class="form-label fw-semibold">
        Username atau Email
    </label>
    <div class="input-group {% if form.username.errors %}has-validation{% endif %}">
        <span class="input-group-text"><i class="ri-user-line"></i></span>
        <input type="text"
               id="{{ form.username.id_for_label }}"
               name="{{ form.username.html_name }}"
               class="form-control {% if form.username.errors %}is-invalid{% endif %}"
               value="{{ form.username.value|default:'' }}"
               required autofocus autocomplete="username">
        {% if form.username.errors %}
        <div class="invalid-feedback">
            {% for error in form.username.errors %}{{ error }}{% endfor %}
        </div>
        {% endif %}
    </div>
</div>
```

**Untuk `select` / `dropdown`:**

```html
<div class="mb-3">
    <label for="{{ form.role.id_for_label }}" class="form-label fw-semibold">Role</label>
    <select id="{{ form.role.id_for_label }}"
            name="{{ form.role.html_name }}"
            class="form-select {% if form.role.errors %}is-invalid{% endif %}">
        {% for value, label in form.role.field.choices %}
        <option value="{{ value }}" {% if form.role.value == value|stringformat:"s" %}selected{% endif %}>
            {{ label }}
        </option>
        {% endfor %}
    </select>
    {% if form.role.errors %}
    <div class="invalid-feedback">
        {% for error in form.role.errors %}{{ error }}{% endfor %}
    </div>
    {% endif %}
</div>
```

##### B. Form-level (non-field) errors — `.alert.alert-danger`

Error yang tidak terikat ke field spesifik (misal: "Username atau kata sandi salah") ditampilkan sebagai alert di atas form:

```html
{% if form.non_field_errors %}
<div class="alert alert-danger d-flex align-items-center gap-2" role="alert">
    <i class="ri-error-warning-fill fs-5 flex-shrink-0"></i>
    <div>
        {% for error in form.non_field_errors %}
        <div>{{ error }}</div>
        {% endfor %}
    </div>
</div>
{% endif %}
```

##### C. Django messages alerts — `partials/alerts.html`

Setiap halaman yang memiliki `{% include 'partials/alerts.html' %}` otomatis menampilkan feedback dari `messages.success(...)`, `messages.error(...)`, dll. — selalu letakkan include ini di awal konten halaman, sebelum form.

##### D. Template helpers — Django `{{ form.field.errors }}` shortcut

Untuk form yang dirender via `crispy_forms` atau `{{ form.as_p }}` — tidak digunakan di CBT Pro. Semua form dirender secara **manual** dengan pattern A+B di atas agar styling sepenuhnya terkontrol.

##### E. Mapping pesan error

| Kondisi | Mekanisme | Class |
|---------|-----------|-------|
| Field kosong / tidak valid | `is-invalid` + `.invalid-feedback` | per-field |
| Password tidak cocok | `is-invalid` pada confirm field + `.invalid-feedback` | per-field |
| Username/email tidak ditemukan | `form.non_field_errors` | `.alert.alert-danger` |
| Sukses simpan / aksi berhasil | `messages.success(...)` via `partials/alerts.html` | `.alert.alert-success` |
| Operasi gagal (server error) | `messages.error(...)` via `partials/alerts.html` | `.alert.alert-danger` |
| Peringatan | `messages.warning(...)` via `partials/alerts.html` | `.alert.alert-warning` |


---

### 16. Technology Details

#### 16.1 Bootstrap 5

```html
<!-- Compiled custom theme CSS (compiled from theme.scss → overrides Bootstrap variables) -->
<link href="{% static 'css/theme.css' %}" rel="stylesheet">
<!-- Custom utility classes -->

<!-- JS before </body> -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
```

#### 16.2 Remix Icon

```html
<link href="https://cdn.jsdelivr.net/npm/remixicon@4.9.0/fonts/remixicon.css" rel="stylesheet">
```

**Usage:**

```html
<!-- Navigation -->
<i class="ri-dashboard-line"></i>         <!-- Dashboard -->
<i class="ri-user-line"></i>              <!-- Users -->
<i class="ri-book-open-line"></i>         <!-- Subjects -->
<i class="ri-question-line"></i>          <!-- Questions -->
<i class="ri-file-list-3-line"></i>       <!-- Exams -->
<i class="ri-eye-line"></i>               <!-- Monitoring -->
<i class="ri-bar-chart-line"></i>         <!-- Results / Analytics -->
<i class="ri-notification-line"></i>      <!-- Notifications -->
<i class="ri-settings-3-line"></i>        <!-- Settings -->

<!-- User & Auth -->
<i class="ri-user-circle-line"></i>       <!-- Profile -->
<i class="ri-lock-password-line"></i>     <!-- Change Password -->
<i class="ri-logout-box-line"></i>        <!-- Logout -->

<!-- CRUD -->
<i class="ri-add-line"></i>               <!-- Add -->
<i class="ri-edit-line"></i>              <!-- Edit -->
<i class="ri-delete-bin-line"></i>        <!-- Delete -->
<i class="ri-search-line"></i>            <!-- Search -->
<i class="ri-filter-line"></i>            <!-- Filter -->
<i class="ri-download-line"></i>          <!-- Export -->
<i class="ri-upload-line"></i>            <!-- Import -->
<i class="ri-file-copy-line"></i>         <!-- Duplicate -->

<!-- Status -->
<i class="ri-checkbox-circle-line text-success"></i>  <!-- Passed -->
<i class="ri-close-circle-line text-danger"></i>      <!-- Failed -->
<i class="ri-time-line text-warning"></i>             <!-- In Progress -->
<i class="ri-draft-line"></i>                         <!-- Draft -->
```

#### 16.3 Alpine.js

```html
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.15.8/dist/cdn.min.js"></script>
```

**Key Patterns:**

```html
<!-- 1. Sidebar collapse toggle (stored in localStorage for persistence) -->
<div x-data="sidebarState()" :class="{ 'sidebar-collapsed': collapsed }">
    <button @click="toggle()" class="btn btn-link">
        <i :class="collapsed ? 'ri-menu-unfold-line' : 'ri-menu-fold-line'"></i>
    </button>
</div>

<script>
function sidebarState() {
    return {
        collapsed: localStorage.getItem('sidebarCollapsed') === 'true',
        toggle() {
            this.collapsed = !this.collapsed;
            localStorage.setItem('sidebarCollapsed', this.collapsed);
        }
    }
}
</script>

<!-- 2. Password show/hide -->
<div class="input-group" x-data="{ show: false }">
    <input :type="show ? 'text' : 'password'" class="form-control"
           name="password" placeholder="Password" required>
    <button class="btn btn-outline-secondary" type="button" @click="show = !show">
        <i :class="show ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
    </button>
</div>

<!-- 3. Loading button state -->
<div x-data="{ loading: false }">
    <button class="btn btn-primary px-4"
            :disabled="loading"
            @click="loading = true; $el.closest('form').submit()">
        <span class="spinner-border spinner-border-sm me-2" x-show="loading"></span>
        <span x-text="loading ? 'Menyimpan...' : 'Simpan'"></span>
    </button>
</div>

<!-- 4. Dynamic option list (Question form) -->
<div x-data="{ options: ['', '', '', ''] }">
    <template x-for="(opt, i) in options" :key="i">
        <div class="input-group mb-2">
            <span class="input-group-text fw-bold" x-text="['A','B','C','D','E'][i]"></span>
            <input type="text" class="form-control"
                   x-model="options[i]"
                   :name="`option_${['A','B','C','D','E'][i]}`"
                   :placeholder="`Pilihan ${['A','B','C','D','E'][i]}`" required>
            <button class="btn btn-outline-danger btn-sm" type="button"
                    x-show="options.length > 2"
                    @click="options.splice(i, 1)">
                <i class="ri-delete-bin-line"></i>
            </button>
        </div>
    </template>
    <button class="btn btn-outline-secondary" type="button"
            x-show="options.length < 5"
            @click="options.push('')">
        <i class="ri-add-line me-1"></i> Tambah Pilihan
    </button>
</div>
```

#### 16.4 Axios

```html
<script src="https://cdn.jsdelivr.net/npm/axios@1.13.6/dist/axios.min.js"></script>
```

**Global Setup in `static/js/main.js`:**

```javascript
// ── CSRF Token ────────────────────────────────────────────────
function getCookie(name) {
    let val = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(c => {
            const [k, v] = c.trim().split('=');
            if (k === name) val = decodeURIComponent(v);
        });
    }
    return val;
}
axios.defaults.headers.common['X-CSRFToken'] = getCookie('csrftoken');

// ── Global Response Interceptor ───────────────────────────────
axios.interceptors.response.use(
    response => response,
    error => {
        const status = error.response?.status;
        if (status === 403) { window.location.href = '/login/'; }
        else if (status === 500) { showToast('Server error. Coba lagi.', 'danger'); }
        return Promise.reject(error);
    }
);

// ── Global Toast Helper ───────────────────────────────────────
function showToast(message, type = 'success') {
    window.dispatchEvent(new CustomEvent('show-toast', { detail: { message, type } }));
}
```

#### 16.5 Chart.js

```html
<!-- Page-specific: analytics & results pages only -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"></script>
```

#### 16.6 TinyMCE

```bash
pip install django-tinymce
```

```javascript
// Question form — initialize TinyMCE for question text
// Pass TINYMCE_API_KEY via view context: context['tinymce_key'] = settings.TINYMCE_DEFAULT_CONFIG.get('license_key','')
tinymce.init({
    selector: '#id_question_text',
    plugins: 'lists link image table code',
    toolbar: 'undo redo | blocks | bold italic | bullist numlist | link image | code',
    height: 350,
    license_key: '{{ tinymce_key }}',  // set in view context or use 'gpl' for open-source
});
```

#### 16.7 SortableJS

```html
<!-- Page-specific: exam builder only -->
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"></script>
```

---

### 17. SCSS Architecture & Design System

#### 17.1 theme.scss — Bootstrap Variable Overrides

```scss
// static/scss/theme.scss
// ─────────────────────────────────────────────────────────────────
// CUSTOM THEME COLORS
// Primary: Deep Navy Blue  #1B3A6B
// Scheme:  Professional blue-slate palette
// ─────────────────────────────────────────────────────────────────

// ── Core Brand Colors ─────────────────────────────────────────
$primary:        #1B3A6B;   // Deep Navy Blue — main brand
$secondary:      #4A6FA5;   // Cornflower Blue — supporting
$success:        #1E8449;   // Emerald Green
$info:           #1A7DAF;   // Cerulean Blue
$warning:        #E67E22;   // Burnt Orange
$danger:         #C0392B;   // Crimson Red
$light:          #F0F4F8;   // Cool Light Gray
$dark:           #1A2332;   // Near Black Navy

// ── Extended Palette (CSS custom properties via Bootstrap) ────
$blue:           #1B3A6B;
$indigo:         #3D52A0;
$purple:         #7B2D8B;
$pink:           #D63384;
$red:            #C0392B;
$orange:         #E67E22;
$yellow:         #F4D03F;
$green:          #1E8449;
$teal:           #148F77;
$cyan:           #1A7DAF;

// ── Typography ────────────────────────────────────────────────
$font-family-sans-serif: 'Inter', system-ui, -apple-system, sans-serif;
$font-size-base:         0.9375rem;  // 15px
$line-height-base:       1.6;

$headings-font-weight:   600;
$headings-color:         $dark;

// ── Border Radius ─────────────────────────────────────────────
$border-radius:          0.5rem;
$border-radius-sm:       0.375rem;
$border-radius-lg:       0.75rem;
$border-radius-xl:       1rem;

// ── Shadows ───────────────────────────────────────────────────
$box-shadow-sm: 0 1px 3px rgba(27, 58, 107, 0.08),
                0 1px 2px rgba(27, 58, 107, 0.06);
$box-shadow:    0 4px 6px rgba(27, 58, 107, 0.07),
                0 2px 4px rgba(27, 58, 107, 0.06);
$box-shadow-lg: 0 10px 15px rgba(27, 58, 107, 0.1),
                0 4px 6px rgba(27, 58, 107, 0.05);

// ── Cards ─────────────────────────────────────────────────────
$card-border-color:   rgba(27, 58, 107, 0.1);
$card-border-radius:  $border-radius-lg;
$card-box-shadow:     $box-shadow-sm;

// ── Navbar ────────────────────────────────────────────────────
$navbar-light-color:         rgba($dark, 0.7);
$navbar-light-active-color:  $primary;

// ── Table ─────────────────────────────────────────────────────
$table-striped-bg:           rgba(27, 58, 107, 0.03);
$table-hover-bg:             rgba(27, 58, 107, 0.05);

// ── Inputs ────────────────────────────────────────────────────
$input-focus-border-color:   rgba($primary, 0.6);
$input-focus-box-shadow:     0 0 0 0.25rem rgba($primary, 0.12);

// ── Buttons ───────────────────────────────────────────────────
$btn-border-radius:          $border-radius;
$btn-font-weight:            500;
$btn-padding-y:              0.5rem;
$btn-padding-x:              1.25rem;

// ── Import Bootstrap AFTER variables ─────────────────────────
// WAJIB: npm install bootstrap@5.3.8 sass terlebih dahulu
// Gunakan @import (bukan @use) agar $variable overrides di atas
// terbaca oleh Bootstrap. @use tidak bisa membaca variabel yang
// didefinisikan sebelumnya (scoping rule dart sass).
@import "bootstrap/scss/bootstrap";

// ── CSS Custom Properties (generated by Bootstrap from $vars above) ────
:root {
    --bs-primary:          #1B3A6B;
    --bs-primary-rgb:      27, 58, 107;
    --bs-secondary:        #4A6FA5;
    --bs-secondary-rgb:    74, 111, 165;
    --bs-success:          #1E8449;
    --bs-success-rgb:      30, 132, 73;
    --bs-info:             #1A7DAF;
    --bs-info-rgb:         26, 125, 175;
    --bs-warning:          #E67E22;
    --bs-warning-rgb:      230, 126, 34;
    --bs-danger:           #C0392B;
    --bs-danger-rgb:       192, 57, 43;
    --bs-light:            #F0F4F8;
    --bs-light-rgb:        240, 244, 248;
    --bs-dark:             #1A2332;
    --bs-dark-rgb:         26, 35, 50;

    // Link color
    --bs-link-color:       #1B3A6B;
    --bs-link-hover-color: #4A6FA5;

    // Button primary
    --bs-btn-bg:           #1B3A6B;
    --bs-btn-border-color: #1B3A6B;
    --bs-btn-hover-bg:     #152E58;
    --bs-btn-active-bg:    #102347;
}
```

#### 17.2 Design & Styling Principles

**Aturan file SCSS:**

- `static/scss/theme.scss` → Bootstrap variable overrides + `@import bootstrap` → compile ke `static/css/theme.css`
- `static/scss/custom.scss` → Custom classes yang **tidak tersedia** di Bootstrap → compile ke `static/css/custom.css`
- **Bootstrap-first:** Selalu coba selesaikan dengan utility Bootstrap (`m-*`, `p-*`, `d-flex`, `gap-*`, `rounded-*`, `shadow-*`, `text-*`, `bg-*`) sebelum menulis custom class
- Tulis custom class di `custom.scss` **hanya** jika komponen yang diinginkan benar-benar tidak ada di Bootstrap (contoh: sidebar layout, stat-card, exam timer, avatar inisial, soft badge variants)
- Tidak boleh `style=""` inline kecuali nilai dinamis dari Python/Django (mis. progress bar width `style="width:{{ pct }}%"`)
- Tidak boleh hardcode warna hex — gunakan CSS variable Bootstrap: `var(--bs-primary)`, `var(--bs-danger)`, dll.

**Prinsip UI — Modern, Clean, Nyaman di Mata:**

1. **Whitespace** — Section padding vertikal besar (py-5 atau lebih). Card body cukup (p-4). Jangan padat/sempit.
2. **Tipografi** — Hierarki jelas: H1 besar & bold untuk hero, H2 untuk section title, H5/H6 untuk card title, body text `text-muted` untuk deskripsi pendukung. Gunakan `fw-semibold` atau `fw-bold` untuk emphasis.
3. **Warna** — Gunakan warna dari `theme.scss` variable. Section gelap (`bg-dark` atau primary dark) untuk kontras. Section terang (`bg-white`, `bg-light`) untuk konten utama. Variasikan antar section agar tidak monoton.
4. **Komponen Bootstrap default** — `card`, `navbar`, `badge`, `btn`, `table`, `modal`, `alert`, `form-control`, `progress`, `spinner` — gunakan apa adanya, hanya override via `theme.scss` variable.
5. **Status badge** — **Semua badge status wajib soft color**, bukan warna Bootstrap solid default. Buat di `custom.scss`:
   - `.badge-soft-success` (teks success, background success transparan)
   - `.badge-soft-danger`, `.badge-soft-warning`, `.badge-soft-info`, `.badge-soft-primary`, `.badge-soft-secondary`
   - Pola: `color: var(--bs-X); background-color: rgba(var(--bs-X-rgb), 0.15);`
6. **Responsive wajib** — grid Bootstrap: `col-12 col-md-6 col-lg-4`, breakpoints sm/md/lg/xl. Semua tabel pakai `table-responsive`. Sidebar collapse di mobile.
7. **Konsistensi** — Satu pola dipakai di semua halaman. Jangan campur style antar halaman.
8. **Interaksi** — Hover state pada card (`shadow` lebih besar), tombol loading state (spinner), link aktif di navigasi.
9. **Icon** — Selalu gunakan Remix Icon (`ri-*`). Letakkan di sebelah kiri teks, `me-1` atau `me-2` spasi.
10. **Tombol** — Standar size (`btn btn-primary`) di semua tempat. Hanya `btn-sm` di kolom aksi tabel.

---

### 18. Base Templates & Layouts

#### 18.1 base.html

```html
{# templates/base.html — Root base template #}
{% load static %}
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token }}">
    <title>{% block title %}{{ site_name }}{% endblock %}</title>
    <meta name="description" content="{% block meta_description %}CBT Pro — Advanced Computer-Based Testing{% endblock %}">

    <!-- Google Fonts — Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

    <!-- Remix Icon -->
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.9.0/fonts/remixicon.css" rel="stylesheet">

    <!-- CBT Pro Theme = Bootstrap 5 + override dikompilasi (npm sass). TIDAK pakai Bootstrap CDN CSS -->
    <link href="{% static 'css/theme.css' %}" rel="stylesheet">
    <link href="{% static 'css/custom.css' %}" rel="stylesheet">

    {% block extra_css %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">

    {% block body %}{% endblock %}

    <!-- Toast Notifications -->
    {% include 'partials/toast.html' %}

    <!-- Bootstrap 5 JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>

    <!-- Alpine.js (defer — non-blocking) -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.15.8/dist/cdn.min.js"></script>

    <!-- Axios -->
    <script src="https://cdn.jsdelivr.net/npm/axios@1.13.6/dist/axios.min.js"></script>

    <!-- App globals (CSRF, Axios setup, showToast) -->
    <script src="{% static 'js/main.js' %}"></script>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### 18.2 layouts/base_dashboard.html

```html
{# templates/layouts/base_dashboard.html — Dashboard layout for all roles #}
{% extends 'base.html' %}
{% load static %}

{% block body_class %}dashboard-layout{% endblock %}

{% block body %}
<div x-data="sidebarState()" :class="{ 'sidebar-collapsed': collapsed }">

    <!-- Mobile sidebar overlay -->
    <div class="sidebar-overlay" :class="{ 'active': mobileOpen }" @click="mobileOpen = false"></div>

    <!-- ── Sidebar ─────────────────────────────────────────── -->
    <aside class="sidebar" :class="{ 'sidebar-open': mobileOpen }">
        {% include 'partials/sidebar.html' %}
    </aside>

    <!-- ── Main Content ───────────────────────────────────── -->
    <div class="main-content">

        <!-- Topbar -->
        {% include 'partials/topbar.html' %}

        <!-- Page Content -->
        <main class="page-content">
            <!-- Django Messages Alerts -->
            {% include 'partials/alerts.html' %}

            <!-- Breadcrumb (mobile) -->
            <div class="d-lg-none mb-3">
                {% include 'partials/breadcrumb.html' %}
            </div>

            {% block page_content %}{% endblock %}
        </main>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
function sidebarState() {
    return {
        collapsed:  localStorage.getItem('sidebarCollapsed') === 'true',
        mobileOpen: false,
        toggle()       { this.collapsed = !this.collapsed; localStorage.setItem('sidebarCollapsed', this.collapsed); },
        openMobile()   { this.mobileOpen = true; },
        closeMobile()  { this.mobileOpen = false; },
    }
}
</script>
{% block dashboard_js %}{% endblock %}
{% endblock %}
```

#### 18.3 layouts/base_exam.html

```html
{# templates/layouts/base_exam.html — Full-screen exam layout (no sidebar/topbar) #}
{% extends 'base.html' %}
{% load static %}

{% block body_class %}exam-layout bg-light{% endblock %}

{% block body %}
<div id="exam-wrapper" x-data="examRoom({{ exam_data_json }})">
    <!-- Exam Header (fixed) -->
    <header class="exam-header">
        <div class="d-flex align-items-center gap-3">
            <span class="fw-semibold">{{ exam.title }}</span>
            <span class="badge badge-soft-info">{{ exam.subject_name }}</span>
        </div>
        <div class="d-flex align-items-center gap-3">
            <div class="timer-display" :class="{ 'timer-warning': timeLeft < 300, 'timer-danger': timeLeft < 60 }"
                 x-text="formatTime(timeLeft)"></div>
        </div>
        <div class="d-flex align-items-center gap-2">
            <span class="badge badge-soft-primary">
                <i class="ri-user-line me-1"></i>{{ request.user.full_name }}
            </span>
        </div>
    </header>

    <!-- Exam Content -->
    {% block exam_content %}{% endblock %}
</div>
{% endblock %}
```

---

### 19. Partials / Reusable Components

#### 19.1 partials/topbar.html

```html
{# templates/partials/topbar.html #}
{% load static %}
<header class="topbar">
    <!-- Sidebar Toggle Button -->
    <button class="topbar-toggle" @click="toggle()" title="Toggle Sidebar">
        <i class="ri-menu-fold-line" x-show="!collapsed"></i>
        <i class="ri-menu-unfold-line" x-show="collapsed"></i>
    </button>

    <!-- Mobile: hamburger -->
    <button class="topbar-toggle d-lg-none" @click="openMobile()">
        <i class="ri-menu-line"></i>
    </button>

    <!-- Breadcrumb (desktop) -->
    <div class="topbar-breadcrumb d-none d-lg-block">
        {% include 'partials/breadcrumb.html' %}
    </div>

    <!-- Actions -->
    <div class="topbar-actions ms-auto">
        <!-- Notification Bell -->
        <div class="dropdown">
            <button class="btn btn-link text-secondary position-relative p-1" data-bs-toggle="dropdown">
                <i class="ri-notification-3-line fs-5"></i>
                {% if unread_notifications_count > 0 %}
                <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
                      >
                    {{ unread_notifications_count }}
                </span>
                {% endif %}
            </button>
            <ul class="dropdown-menu dropdown-menu-end shadow" >
                <li><h6 class="dropdown-header">Notifikasi</h6></li>
                {% for notif in recent_notifications %}
                <li>
                    <a class="dropdown-item py-2 {% if not notif.is_read %}bg-primary-soft{% endif %}"
                       href="{% url 'notifications:list' %}">
                        <div class="fw-medium" >{{ notif.title }}</div>
                        <div class="text-muted" >{{ notif.created_at|timesince }} ago</div>
                    </a>
                </li>
                {% empty %}
                <li><span class="dropdown-item text-muted text-center py-3">Tidak ada notifikasi</span></li>
                {% endfor %}
                <li><hr class="dropdown-divider m-0"></li>
                <li><a class="dropdown-item text-center text-primary small py-2" href="{% url 'notifications:list' %}">Lihat Semua</a></li>
            </ul>
        </div>

        <!-- User Menu -->
        {% include 'partials/user_menu.html' %}
    </div>
</header>
```

#### 19.2 partials/sidebar.html

```html
{# templates/partials/sidebar.html — Role-aware collapsible sidebar #}
{% load static %}

<!-- Brand -->
<div class="sidebar-brand">
    <a href="{% url 'dashboard:home' %}">
        <img src="{% static 'images/logo-B-light.png' %}" height="36" alt="CBT Pro">
    </a>
</div>

<!-- Navigation -->
<nav class="sidebar-nav">

    {% if request.user.is_admin %}
    {# ─── Admin Navigation ─── #}
    <div class="sidebar-section-title">Utama</div>
    <a href="{% url 'dashboard:admin' %}"
       class="nav-link {% if request.resolver_match.url_name == 'admin' %}active{% endif %}">
        <i class="ri-dashboard-line"></i>
        <span class="nav-label">Dashboard</span>
    </a>

    <div class="sidebar-section-title">Manajemen</div>
    <a href="{% url 'users:list' %}"
       class="nav-link {% if 'users' in request.resolver_match.app_name %}active{% endif %}">
        <i class="ri-user-settings-line"></i>
        <span class="nav-label">Manajemen Pengguna</span>
    </a>
    <a href="{% url 'subjects:list' %}"
       class="nav-link {% if 'subjects' in request.resolver_match.app_name %}active{% endif %}">
        <i class="ri-book-open-line"></i>
        <span class="nav-label">Mata Pelajaran</span>
    </a>

    <div class="sidebar-section-title">Sistem</div>
    <a href="{% url 'core:settings' %}"
       class="nav-link {% if 'settings' in request.resolver_match.url_name %}active{% endif %}">
        <i class="ri-settings-3-line"></i>
        <span class="nav-label">Pengaturan Sistem</span>
    </a>
    <a href="{% url 'analytics:dashboard' %}"
       class="nav-link {% if 'analytics' in request.resolver_match.app_name %}active{% endif %}">
        <i class="ri-bar-chart-grouped-line"></i>
        <span class="nav-label">Analitik</span>
    </a>

    {% elif request.user.is_teacher %}
    {# ─── Teacher Navigation ─── #}
    <div class="sidebar-section-title">Utama</div>
    <a href="{% url 'dashboard:teacher' %}"
       class="nav-link {% if request.resolver_match.url_name == 'teacher' %}active{% endif %}">
        <i class="ri-dashboard-line"></i>
        <span class="nav-label">Dashboard</span>
    </a>

    <div class="sidebar-section-title">Konten</div>
    <a href="{% url 'questions:list' %}"
       class="nav-link {% if 'questions' in request.resolver_match.app_name %}active{% endif %}">
        <i class="ri-question-line"></i>
        <span class="nav-label">Bank Soal</span>
    </a>
    <a href="{% url 'exams:list' %}"
       class="nav-link {% if 'exams' in request.resolver_match.app_name %}active{% endif %}">
        <i class="ri-file-list-3-line"></i>
        <span class="nav-label">Manajemen Ujian</span>
    </a>

    <div class="sidebar-section-title">Monitoring</div>
    <a href="{% url 'monitoring:index' %}"
       class="nav-link {% if 'monitoring' in request.resolver_match.app_name %}active{% endif %}">
        <i class="ri-eye-line"></i>
        <span class="nav-label">Pemantauan Langsung</span>
    </a>
    <a href="{% url 'results:teacher_list' %}"
       class="nav-link {% if 'results' in request.resolver_match.app_name %}active{% endif %}">
        <i class="ri-bar-chart-line"></i>
        <span class="nav-label">Hasil & Analisis</span>
    </a>

    {% else %}
    {# ─── Student Navigation ─── #}
    <div class="sidebar-section-title">Utama</div>
    <a href="{% url 'dashboard:student' %}"
       class="nav-link {% if request.resolver_match.url_name == 'student' %}active{% endif %}">
        <i class="ri-dashboard-line"></i>
        <span class="nav-label">Dashboard</span>
    </a>

    <div class="sidebar-section-title">Ujian</div>
    <a href="{% url 'attempts:exam_list' %}"
       class="nav-link {% if 'attempts' in request.resolver_match.app_name %}active{% endif %}">
        <i class="ri-file-list-3-line"></i>
        <span class="nav-label">Daftar Ujian</span>
    </a>
    <a href="{% url 'results:student_list' %}"
       class="nav-link {% if 'results' in request.resolver_match.app_name %}active{% endif %}">
        <i class="ri-award-line"></i>
        <span class="nav-label">Hasil Saya</span>
    </a>
    {% endif %}

</nav>
```

#### 19.3 partials/user_menu.html

```html
{# templates/partials/user_menu.html
   Used in: topbar.html (dashboard) and landing page navbar (if logged in) #}
{% if user.is_authenticated %}
<div class="dropdown">
    <button class="user-menu-toggle btn border-0 p-0" data-bs-toggle="dropdown" aria-expanded="false">
        {% if user.profile.profile_picture %}
            <img src="{{ user.profile.profile_picture.url }}" class="user-avatar" alt="{{ user.full_name }}">
        {% else %}
            <div class="user-avatar-placeholder">
                {{ user.first_name|first|upper }}{{ user.last_name|first|upper }}
            </div>
        {% endif %}
        <div class="user-info d-none d-md-block text-start">
            <div class="user-name">{{ user.full_name }}</div>
            <div class="user-role">{{ user.get_role_display }}</div>
        </div>
        <i class="ri-arrow-down-s-line text-muted ms-1 d-none d-md-inline"></i>
    </button>
    <ul class="dropdown-menu dropdown-menu-end shadow mt-1" >
        <li>
            <div class="dropdown-header py-2">
                <div class="fw-semibold">{{ user.full_name }}</div>
                <div class="text-muted small">{{ user.email }}</div>
            </div>
        </li>
        <li><hr class="dropdown-divider m-0"></li>
        <li>
            <a class="dropdown-item py-2" href="{% url 'accounts:profile' %}">
                <i class="ri-user-line me-2 text-primary"></i> Profil Saya
            </a>
        </li>
        <li>
            <a class="dropdown-item py-2" href="{% url 'accounts:change_password' %}">
                <i class="ri-lock-password-line me-2 text-warning"></i> Ubah Kata Sandi
            </a>
        </li>
        <li><hr class="dropdown-divider m-0"></li>
        <li>
            <form method="post" action="{% url 'accounts:logout' %}">
                {% csrf_token %}
                <button type="submit" class="dropdown-item py-2 text-danger">
                    <i class="ri-logout-box-line me-2"></i> Keluar
                </button>
            </form>
        </li>
    </ul>
</div>
{% endif %}
```

#### 19.4 partials/breadcrumb.html

```html
{# templates/partials/breadcrumb.html #}
{# Usage: set breadcrumbs in view context as a list of {'label': '...', 'url': '...'} #}
{% if breadcrumbs %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb mb-0">
        <li class="breadcrumb-item">
            <a href="{% url 'dashboard:home' %}"><i class="ri-home-3-line"></i></a>
        </li>
        {% for crumb in breadcrumbs %}
        {% if forloop.last %}
            <li class="breadcrumb-item active">{{ crumb.label }}</li>
        {% else %}
            <li class="breadcrumb-item"><a href="{{ crumb.url }}">{{ crumb.label }}</a></li>
        {% endif %}
        {% endfor %}
    </ol>
</nav>
{% endif %}
```

#### 19.5 partials/alerts.html

```html
{# templates/partials/alerts.html — Django messages #}
{% if messages %}
<div class="mb-4" id="django-messages">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show d-flex align-items-center"
         role="alert">
        {% if message.tags == 'success' %}<i class="ri-checkbox-circle-fill me-2 fs-5"></i>
        {% elif message.tags == 'error' or message.tags == 'danger' %}<i class="ri-error-warning-fill me-2 fs-5"></i>
        {% elif message.tags == 'warning' %}<i class="ri-alert-fill me-2 fs-5"></i>
        {% else %}<i class="ri-information-fill me-2 fs-5"></i>
        {% endif %}
        <div>{{ message }}</div>
        <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

#### 19.6 partials/footer.html

```html
{# templates/partials/footer.html — Used on landing page #}
<footer class="py-4 bg-dark text-light">
    <div class="container text-center">
        <p class="mb-0 text-light opacity-50 small">&copy; {% now "Y" %} CBT Pro. Hak cipta dilindungi.</p>
    </div>
</footer>
```

#### 19.7 partials/toast.html

```html
{# templates/partials/toast.html — Alpine.js toast system #}
<div x-data="toastManager()" @show-toast.window="add($event.detail)"
     class="toast-container position-fixed bottom-0 end-0 p-3">
    <template x-for="toast in toasts" :key="toast.id">
        <div class="toast show align-items-center border-0 mb-2"
             :class="{
                'text-bg-success': toast.type === 'success',
                'text-bg-danger':  toast.type === 'danger' || toast.type === 'error',
                'text-bg-warning': toast.type === 'warning',
                'text-bg-info':    toast.type === 'info'
             }"
             x-show="toast.visible"
             x-transition:enter="transition ease-out duration-200"
             x-transition:enter-start="opacity-0 translate-y-2"
             x-transition:enter-end="opacity-100 translate-y-0"
             x-transition:leave="transition ease-in duration-150"
             x-transition:leave-end="opacity-0"
             role="alert">
            <div class="d-flex">
                <div class="toast-body fw-medium" x-text="toast.message"></div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto"
                        @click="remove(toast.id)"></button>
            </div>
        </div>
    </template>
</div>

<script>
function toastManager() {
    return {
        toasts: [],
        add({ message, type = 'success' }) {
            const id = Date.now();
            this.toasts.push({ id, message, type, visible: true });
            setTimeout(() => this.remove(id), 4000);
        },
        remove(id) {
            const t = this.toasts.find(t => t.id === id);
            if (t) {
                t.visible = false;
                setTimeout(() => { this.toasts = this.toasts.filter(t => t.id !== id); }, 200);
            }
        }
    }
}
</script>
```

#### 19.8 partials/confirm_modal.html

```html
{# templates/partials/confirm_modal.html — Reusable delete confirmation modal #}
<div class="modal fade" id="confirmModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg">
            <div class="modal-header border-0 pb-0">
                <h5 class="modal-title fw-semibold" id="confirmModalTitle">Konfirmasi Hapus</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body py-2">
                <div class="d-flex gap-3 align-items-start">
                    <div class="flex-shrink-0 text-center">
                        <i class="ri-delete-bin-line text-danger fs-2"></i>
                    </div>
                    <div>
                        <p class="mb-0" id="confirmModalBody">Apakah Anda yakin ingin menghapus item ini?</p>
                        <p class="text-muted small mb-0 mt-1">Tindakan ini tidak dapat dibatalkan.</p>
                    </div>
                </div>
            </div>
            <div class="modal-footer border-0 pt-0">
                <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Batal</button>
                <form id="confirmForm" method="post" class="d-inline">
                    {% csrf_token %}
                    {# Django views handle deletion via POST — the view checks request.POST or a dedicated delete URL #}
                    <button type="submit" class="btn btn-danger">
                        <i class="ri-delete-bin-line me-1"></i> Hapus
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>

<script>
// Helper function to set confirm modal content and form action
function confirmDelete(title, body, formAction) {
    document.getElementById('confirmModalTitle').textContent = title || 'Konfirmasi Hapus';
    document.getElementById('confirmModalBody').textContent  = body  || 'Apakah Anda yakin?';
    document.getElementById('confirmForm').action = formAction;
    new bootstrap.Modal(document.getElementById('confirmModal')).show();
}
</script>
```

---

#### 19.9 partials/page_header.html

```html
{# templates/partials/page_header.html
   Usage: {% include 'partials/page_header.html' with title="..." subtitle="..." %}
   Optional context vars: title, subtitle, breadcrumbs, action_buttons (block) #}
<div class="page-header mb-4">
    {% if breadcrumbs %}
        {% include 'partials/breadcrumb.html' %}
    {% endif %}
    <div class="d-flex align-items-start justify-content-between gap-3 mt-2">
        <div>
            <h4 class="page-title mb-1">{{ title }}</h4>
            {% if subtitle %}
                <p class="page-subtitle text-muted mb-0">{{ subtitle }}</p>
            {% endif %}
        </div>
        {% if action_buttons %}
            <div class="page-header-actions flex-shrink-0">
                {{ action_buttons }}
            </div>
        {% endif %}
    </div>
</div>
```

> **Usage rule:** Every dashboard page must include `{% include 'partials/page_header.html' with title="..." subtitle="..." %}` at the top of its main content block. Action buttons (e.g., "Tambah", "Import") are passed via the `action_buttons` block variable or directly in the page template above the include.

---

### 20. File Organization

```
static/
├── scss/
│   ├── theme.scss           # Bootstrap variable overrides
│   └── custom.scss          # Custom classes (sidebar, stat-card, soft-badge, exam-timer, dll.)
├── css/
│   ├── theme.css            # Compiled from theme.scss
│   └── custom.css           # Compiled from custom.scss
├── js/
│   ├── main.js              # Global: CSRF, Axios, showToast, sidebarState
│   └── pages/
│       ├── exam-room.js     # Exam room (timer, save, anti-cheat, fullscreen)
│       ├── question-form.js # Question create/edit (TinyMCE, dynamic options)
│       ├── exam-builder.js  # Exam wizard + question selector (SortableJS)
│       └── monitoring.js    # Live monitoring WebSocket client
└── images/
    ├── logo-B-dark.png   # Logo untuk background terang (landing navbar)
    ├── logo-B-light.png  # Logo untuk background gelap (sidebar, login)
    └── default-avatar.png

templates/
├── base.html                        # Root base (CDN links, global blocks)
├── layouts/
│   ├── base_dashboard.html          # Dashboard layout (sidebar + topbar)
│   └── base_exam.html               # Exam room layout (full-screen)
├── partials/
│   ├── topbar.html                  # Topbar (toggle, breadcrumb, user menu)
│   ├── sidebar.html                 # Collapsible sidebar (role-aware)
│   ├── user_menu.html               # Avatar + name + role dropdown
│   ├── breadcrumb.html              # Breadcrumb partial
│   ├── alerts.html                  # Django messages
│   ├── footer.html                  # Landing page footer
│   ├── toast.html                   # Alpine.js toast container
│   ├── confirm_modal.html           # Delete confirmation modal
│   └── page_header.html             # Page header with title, subtitle, action buttons
├── errors/
│   ├── 403.html
│   ├── 404.html
│   └── 500.html
│
└── [app templates — in each app's templates/ folder]
    accounts/login.html
    accounts/profile.html
    accounts/change_password.html
    dashboard/landing.html
    dashboard/admin.html
    dashboard/teacher.html
    dashboard/student.html
    users/list.html, create.html, edit.html, detail.html
    subjects/list.html, create.html, edit.html
    questions/list.html, create.html, edit.html, detail.html
    exams/list.html, create.html, edit.html, detail.html
    exams/wizard/step_*.html
    attempts/exam_list.html, exam_detail.html, exam_room.html
    monitoring/live.html
    results/teacher_*.html, student_*.html, essay_grading.html
    analytics/dashboard.html
    notifications/list.html
    core/settings.html
```

---

### 21. Page Examples

#### 21.1 Login Page

Clean centered card, username/password fields, password show/hide, remember me toggle.

```html
{# apps/accounts/templates/accounts/login.html #}
{% extends 'base.html' %}
{% load static %}

{% block title %}Masuk — {{ site_name }}{% endblock %}

{% block body %}
<div class="min-vh-100 d-flex align-items-center justify-content-center">
    <div class="col-12 col-sm-10 col-md-7 col-lg-5 col-xl-4">

        <!-- Logo -->
        <div class="text-center mb-4">
            <img src="{% static 'images/logo-B-light.png' %}" height="48" alt="CBT Pro">
        </div>

        <!-- Card -->
        <div class="card shadow">
            <div class="card-body p-4">

                {% include 'partials/alerts.html' %}

                <form method="post" novalidate x-data="{ loading: false }" @submit.prevent="loading = true; $el.submit()">
                    {% csrf_token %}

                    <!-- Non-field errors (e.g. wrong credentials) -->
                    {% if form.non_field_errors %}
                    <div class="alert alert-danger d-flex align-items-center gap-2" role="alert">
                        <i class="ri-error-warning-fill fs-5 flex-shrink-0"></i>
                        <div>{% for error in form.non_field_errors %}{{ error }}{% endfor %}</div>
                    </div>
                    {% endif %}

                    <!-- Username / Email -->
                    <div class="mb-3">
                        <label for="{{ form.username.id_for_label }}" class="form-label fw-semibold">Username atau Email</label>
                        <div class="input-group {% if form.username.errors %}has-validation{% endif %}">
                            <span class="input-group-text"><i class="ri-user-line"></i></span>
                            <input type="text"
                                   id="{{ form.username.id_for_label }}"
                                   name="{{ form.username.html_name }}"
                                   class="form-control {% if form.username.errors %}is-invalid{% endif %}"
                                   value="{{ form.username.value|default:'' }}"
                                   placeholder="Masukkan username atau email"
                                   required autofocus autocomplete="username">
                            {% if form.username.errors %}
                            <div class="invalid-feedback">
                                {% for error in form.username.errors %}{{ error }}{% endfor %}
                            </div>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Password -->
                    <div class="mb-3" x-data="{ show: false }">
                        <label for="{{ form.password.id_for_label }}" class="form-label fw-semibold">Kata Sandi</label>
                        <div class="input-group {% if form.password.errors %}has-validation{% endif %}">
                            <span class="input-group-text"><i class="ri-lock-line"></i></span>
                            <input :type="show ? 'text' : 'password'"
                                   id="{{ form.password.id_for_label }}"
                                   name="{{ form.password.html_name }}"
                                   class="form-control {% if form.password.errors %}is-invalid{% endif %}"
                                   placeholder="Masukkan kata sandi"
                                   required autocomplete="current-password">
                            <button class="btn btn-outline-secondary" type="button"
                                    @click="show = !show" tabindex="-1">
                                <i :class="show ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
                            </button>
                            {% if form.password.errors %}
                            <div class="invalid-feedback">
                                {% for error in form.password.errors %}{{ error }}{% endfor %}
                            </div>
                            {% endif %}
                        </div>
                    </div>

                    <!-- Remember Me -->
                    <div class="mb-4">
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input" name="remember_me" id="rememberMe">
                            <label class="form-check-label" for="rememberMe">Ingat saya selama 30 hari</label>
                        </div>
                    </div>

                    <!-- Submit -->
                    <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                        <span x-show="loading" class="spinner-border spinner-border-sm me-2"></span>
                        <i x-show="!loading" class="ri-login-box-line me-2"></i>
                        <span x-text="loading ? 'Sedang Masuk...' : 'Masuk'">Masuk</span>
                    </button>
                </form>
            </div>
        </div>

        <p class="text-center text-muted small mt-3">
            <i class="ri-information-line me-1"></i>Hubungi administrator jika lupa kata sandi
        </p>

    </div>
</div>
{% endblock %}
```

#### 21.2 Exam Room

Full-screen exam interface — no sidebar, no topbar. Custom layout via `base_exam.html`.

---

#### 21.3 Stat Card Component

Reusable stat card HTML pattern for Admin/Teacher/Student dashboards.

```html
{# Stat Card — Basic (white bg) #}
<div class="col-lg-3 col-md-6">
    <div class="stat-card card-hover">
        <div class="d-flex align-items-start justify-content-between mb-3">
            <div class="stat-icon bg-primary-soft">
                <i class="ri-users-line text-primary"></i>
            </div>
            <span class="badge bg-success-soft small">+12%</span>
        </div>
        <div class="stat-value">{{ total_users }}</div>
        <div class="stat-label mt-1">Total Pengguna</div>
    </div>
</div>

{# Stat Card — Gradient (dark) #}
<div class="col-lg-3 col-md-6">
    <div class="stat-card stat-card-primary card-hover">
        <div class="d-flex align-items-start justify-content-between mb-3">
            <div class="stat-icon">
                <i class="ri-file-list-3-line"></i>
            </div>
        </div>
        <div class="stat-value">{{ total_exams }}</div>
        <div class="stat-label mt-1">Total Ujian</div>
    </div>
</div>
```

---

#### 20.4 Empty State Component

```html
{# Empty state — used in tables, lists, and dashboards when no data #}
<div class="empty-state">
    <div class="empty-state-icon">
        <i class="ri-file-list-3-line"></i>
    </div>
    <div class="empty-state-title">Belum ada ujian</div>
    <div class="empty-state-desc">
        Buat ujian pertama Anda untuk mulai mengelola dan memantau siswa.
    </div>
    <a href="{% url 'exams:create' %}" class="btn btn-primary">
        <i class="ri-add-line me-1"></i> Buat Ujian Baru
    </a>
</div>
```

---

#### 20.5 Wizard Steps Component

```html
{# Wizard progress bar — 4 steps #}
<div class="wizard-steps mb-4">
    {# Step 1: Active #}
    <div class="wizard-step active">
        <div class="d-flex flex-column align-items-center">
            <div class="step-circle">1</div>
            <div class="step-label">Informasi</div>
        </div>
    </div>
    <div class="step-connector"></div>

    {# Step 2: Completed #}
    <div class="wizard-step completed">
        <div class="d-flex flex-column align-items-center">
            <div class="step-circle"><i class="ri-check-line"></i></div>
            <div class="step-label">Soal</div>
        </div>
    </div>
    <div class="step-connector completed"></div>

    {# Step 3: Incomplete #}
    <div class="wizard-step">
        <div class="d-flex flex-column align-items-center">
            <div class="step-circle">3</div>
            <div class="step-label">Pengaturan</div>
        </div>
    </div>
    <div class="step-connector"></div>

    {# Step 4: Incomplete #}
    <div class="wizard-step">
        <div class="d-flex flex-column align-items-center">
            <div class="step-circle">4</div>
            <div class="step-label">Penugasan</div>
        </div>
    </div>
</div>
```

---

#### 20.6 Table with Modern Styling

```html
<div class="card border-0 shadow-sm">
    <div class="card-header bg-white d-flex align-items-center justify-content-between py-3 px-4">
        <h6 class="mb-0 fw-semibold">Daftar Pengguna</h6>
        <a href="{% url 'users:create' %}" class="btn btn-primary btn-sm">
            <i class="ri-add-line me-1"></i> Tambah
        </a>
    </div>
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-modern mb-0">
                <thead>
                    <tr>
                        <th>Pengguna</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Bergabung</th>
                        <th class="text-end">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>
                            <div class="d-flex align-items-center gap-2">
                                {% if user.profile.profile_picture %}
                                    <img src="{{ user.profile.profile_picture.url }}"
                                         class="avatar-initials rounded-circle" alt="">
                                {% else %}
                                    <div class="avatar-initials">
                                        {{ user.first_name|first|upper }}{{ user.last_name|first|upper }}
                                    </div>
                                {% endif %}
                                <div>
                                    <div class="fw-medium" >{{ user.full_name }}</div>
                                    <div class="text-muted" >@{{ user.username }}</div>
                                </div>
                            </div>
                        </td>
                        <td>{{ user.email }}</td>
                        <td>
                            <span class="badge
                                {% if user.role == 'admin' %}badge-soft-danger
                                {% elif user.role == 'teacher' %}badge-soft-primary
                                {% else %}badge-soft-success{% endif %}">
                                {{ user.get_role_display }}
                            </span>
                        </td>
                        <td>
                            <span class="badge {% if user.is_active %}badge-soft-success{% else %}badge-soft-danger{% endif %}">
                                {% if user.is_active %}Aktif{% else %}Nonaktif{% endif %}
                            </span>
                        </td>
                        <td class="text-muted" >
                            {{ user.date_joined|date:"d M Y" }}
                        </td>
                        <td class="text-end table-actions">
                            <a href="{% url 'users:detail' user.pk %}" class="btn btn-outline-secondary btn-sm" title="Detail">
                                <i class="ri-eye-line"></i>
                            </a>
                            <a href="{% url 'users:edit' user.pk %}" class="btn btn-outline-primary btn-sm" title="Edit">
                                <i class="ri-edit-line"></i>
                            </a>
                            <button class="btn btn-outline-danger btn-sm" title="Hapus"
                                    onclick="confirmDelete('Hapus Pengguna', 'Hapus {{ user.full_name }}?', '{% url "users:delete" user.pk %}')">
                                <i class="ri-delete-bin-line"></i>
                            </button>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="6">
                            <div class="empty-state py-5">
                                <div class="empty-state-icon">
                                    <i class="ri-user-search-line"></i>
                                </div>
                                <div class="empty-state-title">Tidak ada pengguna</div>
                                <div class="empty-state-desc">Coba ubah filter atau tambah pengguna baru.</div>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
```

---

#### 20.7 Filter Bar Component

```html
<div class="filter-bar">
    <div class="filter-group">
        <label>Cari</label>
        <input type="text" name="q" class="form-control form-control-sm"
               placeholder="Cari nama atau email..." value="{{ request.GET.q }}">
    </div>
    <div class="filter-group">
        <label>Role</label>
        <select name="role" class="form-select form-select-sm">
            <option value="">Semua Role</option>
            <option value="admin" {% if request.GET.role == "admin" %}selected{% endif %}>Admin</option>
            <option value="teacher" {% if request.GET.role == "teacher" %}selected{% endif %}>Guru</option>
            <option value="student" {% if request.GET.role == "student" %}selected{% endif %}>Siswa</option>
        </select>
    </div>
    <div class="filter-group">
        <label>Status</label>
        <select name="status" class="form-select form-select-sm">
            <option value="">Semua Status</option>
            <option value="active">Aktif</option>
            <option value="inactive">Nonaktif</option>
        </select>
    </div>
    <div class="filter-group ms-auto">
        <label>&nbsp;</label>
        <div class="d-flex gap-2">
            <button type="submit" class="btn btn-primary btn-sm">
                <i class="ri-search-line me-1"></i> Filter
            </button>
            {% if request.GET.q or request.GET.role or request.GET.status %}
            <a href="?" class="btn btn-outline-secondary btn-sm">Reset</a>
            {% endif %}
        </div>
    </div>
</div>
```

---

### 22. JavaScript — exam-room.js

```javascript
// static/js/pages/exam-room.js

function examRoom(config) {
    return {
        // ── State ──────────────────────────────────────────────
        timeLeft:        config.timeLimit,
        questions:       config.questions || [],   // full question list from server
        currentQuestion: 0,
        answers:         config.savedAnswers || {},
        markedForReview: config.markedForReview || [],
        autoSaveTimer:   null,
        countdownTimer:  null,
        violations:      0,
        maxViolations:   config.maxViolations || 3,
        attemptId:       config.attemptId,

        // ── Init ───────────────────────────────────────────────
        init() {
            this.startCountdown();
            this.startAutoSave();
            if (config.requireFullscreen) this.enforceFullscreen();
            if (config.detectTabSwitch)   this.watchTabSwitch();
        },

        // ── Timer ──────────────────────────────────────────────
        startCountdown() {
            this.countdownTimer = setInterval(() => {
                if (this.timeLeft > 0) {
                    this.timeLeft--;
                } else {
                    clearInterval(this.countdownTimer);
                    this.autoSubmit('time_expired');
                }
            }, 1000);
        },

        formatTime(seconds) {
            const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
            const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
            const s = (seconds % 60).toString().padStart(2, '0');
            return h > 0 ? `${h}:${m}:${s}` : `${m}:${s}`;
        },

        // ── Auto Save ─────────────────────────────────────────
        startAutoSave() {
            this.autoSaveTimer = setInterval(() => this.saveCurrentAnswer(), 15000);
        },

        async saveCurrentAnswer() {
            const q = this.questions[this.currentQuestion];
            if (!q || !this.answers[q.id]) return;
            try {
                await axios.post(`/student/exams/${this.attemptId}/save-answer/`, {
                    question_id: q.id,
                    answer: this.answers[q.id],
                });
            } catch (e) { console.warn('Auto-save failed:', e); }
        },

        // ── Navigation ────────────────────────────────────────
        goTo(index) {
            if (index >= 0 && index < this.questions.length) {
                this.saveCurrentAnswer();
                this.currentQuestion = index;
            }
        },

        // ── Violations ────────────────────────────────────────
        watchTabSwitch() {
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) this.recordViolation('tab_switch');
            });
        },

        enforceFullscreen() {
            if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
            document.addEventListener('fullscreenchange', () => {
                if (!document.fullscreenElement) this.recordViolation('fullscreen_exit');
            });
        },

        async recordViolation(type) {
            this.violations++;
            try {
                await axios.post(`/student/exams/${this.attemptId}/violation/`, { type });
            } catch (e) { /* silent */ }
            if (this.violations >= this.maxViolations) this.autoSubmit('max_violations');
        },

        // ── Submit ────────────────────────────────────────────
        async autoSubmit(reason) {
            clearInterval(this.autoSaveTimer);
            clearInterval(this.countdownTimer);
            await axios.post(`/student/exams/${this.attemptId}/submit/`, { reason });
            window.location.href = `/student/results/`;
        },
    }
}
```

---

### 23. Best Practices

**Bootstrap:**

- Use Bootstrap utilities first before custom CSS
- Leverage native Bootstrap components (`.card`, `.table`, `.badge`, `.alert`)
- Use spacing utilities (`m-*`, `p-*`, `gap-*`) consistently
- **Buttons**: Standard size everywhere; ONLY in table action columns

**SCSS / CSS:**

- Compile SCSS → CSS; load `theme.css` before Bootstrap so CSS variable overrides take effect
- Override Bootstrap with CSS custom properties in `:root` (works with CDN Bootstrap)
- Use Bootstrap utility classes first; only add page-specific `<style>` blocks when absolutely needed

**Alpine.js:**

- Keep components small and focused; extract reusable logic to `main.js`
- Use `x-cloak` to prevent FOUC
- Store sidebar state in `localStorage` for persistence between page loads

**Axios:**

- Set CSRF token globally in `main.js`
- Always wrap `await` in `try/catch`
- Give user feedback via `showToast()` on success and failure

**Forms:**

- Render semua form secara **manual** — JANGAN gunakan `{{ form.as_p }}` atau crispy_forms
- Setiap field yang error wajib mendapat class `is-invalid` pada `<input>`/`<select>`/`<textarea>`
- Error message ditampilkan via `<div class="invalid-feedback">{{ form.field.errors }}</div>` langsung di bawah input
- Untuk `input-group`, tambahkan class `has-validation` pada `<div class="input-group">`
- `form.non_field_errors` wajib ditampilkan sebagai `.alert.alert-danger` di atas form
- Django messages (success/error/warning) ditampilkan via `{% include 'partials/alerts.html' %}` — letakkan di awal konten, sebelum form
- Selalu tambahkan `novalidate` pada `<form>` agar validasi browser tidak override Bootstrap styling
- Lihat section 15.8 untuk pattern lengkap + contoh kode

**Templates:**

- Every page template **must** extend a layout: `layouts/base_dashboard.html` or `layouts/base_exam.html`
- Landing and Login pages extend `base.html` directly
- All partials live in `templates/partials/`
- Use `{% include 'partials/...' %}` for DRY components
- Keep business logic in views/services, not templates

---

### 24. CDN Quick Reference

```html
<!-- ─── In base.html <head> ──────────────────── -->

<!-- Remix Icon -->
<link href="https://cdn.jsdelivr.net/npm/remixicon@4.9.0/fonts/remixicon.css" rel="stylesheet">

<!-- CBT Pro Theme = Bootstrap + override dikompilasi npm sass. TIDAK pakai Bootstrap CDN CSS -->
<link href="{% static 'css/theme.css' %}" rel="stylesheet">


<!-- ─── Before </body> ───────────────────────── -->

<!-- Bootstrap 5 JS Bundle (Popper included) -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>

<!-- Alpine.js (defer) -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.15.8/dist/cdn.min.js"></script>

<!-- Axios -->
<script src="https://cdn.jsdelivr.net/npm/axios@1.13.6/dist/axios.min.js"></script>

<!-- App globals -->
<script src="{% static 'js/main.js' %}"></script>


<!-- ─── Page-specific (in {% block extra_js %}) ─ -->

<!-- Chart.js — analytics & results pages only -->
<!-- <script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"></script> -->

<!-- SortableJS — exam builder page only -->
<!-- <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"></script> -->
```

---

## Part V: Information Architecture
### 25. Key Adjustments from Requirements
#### 25.1 Authentication System
- **No public registration** — Only Admin can create users via `/admin/users/`
- **No forgot password** — Admin handles password resets from User Management
- **Login only** — Username or email + password
- **Auth backend**: Custom backend supports login with email **or** username
- **Profile & Password**: All authenticated users can access `/profile/` and `/change-password/`
#### 25.2 URL Convention
All URLs in English:
- `/teacher/` instead of `/guru/`
- `/student/` instead of `/siswa/`
- `/exams/` instead of `/ujian/`
- `/question-bank/` instead of `/bank-soal/`
#### 25.3 Question Navigation Feature
**Question-level settings:**
- Allow Previous
- Allow Next
- Force Sequential
**Exam-level override:**
- Override question navigation globally per exam
### 26. Detail Halaman & Komponen
> Semua label antarmuka menggunakan **Bahasa Indonesia**. Setiap halaman dijabarkan secara lengkap: seksi, komponen, field form, kolom tabel, tombol, status badge, pesan kosong, dan catatan teknis.
### 26.1 HALAMAN PUBLIK
#### 26.1.1 Halaman Beranda
**URL:** `/`
**Akses:** Publik (redirect ke dashboard sesuai role jika sudah login)
**Template:** `templates/dashboard/landing.html` — extends `base.html` (BUKAN base_dashboard)
##### Komponen 1 — PublicNavbar
**Layout 3-zona horizontal:**
| Zona | Konten |
| Kiri | Logo: `<img>` logo-B-dark.png terbungkus `<a href="/">`. **Tanpa teks di sebelah logo.** |
| Tengah | Menu navigasi: **Beranda** (link ke `#`), **Fitur** (scroll ke `#fitur`), **Tentang** (scroll ke `#tentang`). Collapse ke hamburger di mobile. |
| Kanan | Jika belum login: tombol utama → "⊕ Masuk" → `/login/`. Jika sudah login: `partials/user_menu.html` (avatar + nama + dropdown). |
##### Komponen 2 — HeroSection
**Kolom Kiri (konten):**
1. Badge pill kecil di atas judul — ikon `ri-shield-check-line` + teks: *"Lebih tenang saat ujian berlangsung"*
2. Heading H1: **"Platform Ujian Berbasis Komputer yang Modern"**
3. Paragraf deskripsi: *"CBT Pro membantu sekolah dan institusi menyelenggarakan ujian digital yang cepat, aman, dan rapi. Guru fokus pada kualitas soal, siswa fokus pada jawaban, sistem mengurus sisanya."*
4. 2 tombol CTA berdampingan:
 - Tombol utama (primary) — ikon `ri-login-box-line` + "Mulai Sekarang" → `/login/`
 - Tombol sekunder (outline) — ikon `ri-arrow-down-line` + "Lihat Fitur" → scroll ke `#fitur`
**Kolom Kanan (mockup dashboard):**
Card UI mockup (dekoratif, bukan fungsional) yang mensimulasikan tampilan dashboard guru:
- Header kecil: label "DASHBOARD GURU", judul "Sesi Ujian Aktif", badge `Live`
- Info ujian: "Matematika XII – Sesi A", "45/50 peserta sedang online"
- Progress bar Bootstrap dengan label "Progress penyelesaian" + "78%"
- Grid 2×2 stat mini:
 - Bank Soal: ikon + "10.284 item"
 - Pemantauan: ikon + "Realtime"
 - Anti-Kecurangan: ikon + "2 alert aktif"
 - Analitik & Laporan: ikon + "Ekspor 1 klik"
- Teks kecil di bawah: *"Semua fitur inti ujian online terkendali dari satu panel."*
Di mobile: kolom kanan disembunyikan.
##### Komponen 3 — FeaturesSection
**Header section (terpusat):**
- H2: **"Fitur yang Dibutuhkan Tim Akademik"**
- Paragraf subtitle: *"Dirancang untuk sekolah yang ingin proses ujian lebih profesional, dengan antarmuka bersih dan alur kerja yang ringkas."*
**Grid 3 kolom × 2 baris** — setiap item berupa teks + ikon, **tanpa card border/box**:
| No | Ikon | Judul | Deskripsi |
| 1 | `ri-layout-grid-line` | Bank Soal Terstruktur | Kelola ribuan soal per mapel, tingkat kesulitan, dan tag kompetensi dalam satu panel yang mudah ditelusuri. |
| 2 | `ri-shuffle-line` | Randomisasi Cerdas | Acak soal dan opsi jawaban otomatis untuk tiap peserta, menjaga keadilan ujian tanpa konfigurasi rumit. |
| 3 | `ri-shield-check-line` | Pengawasan Terintegrasi | Dukungan monitoring aktivitas dan sinyal pelanggaran agar pengawas bisa bertindak cepat saat ujian berlangsung. |
| 4 | `ri-medal-line` | Penilaian Otomatis | Skor objektif dihitung instan, sehingga guru dapat langsung menganalisis hasil tanpa menunggu proses manual. |
| 5 | `ri-line-chart-line` | Analitik Berbasis Data | Lihat performa siswa, tingkat keberhasilan per soal, dan tren kelas untuk perbaikan pembelajaran berikutnya. |
| 6 | `ri-team-line` | Multi-Role Workflow | Admin, guru, dan siswa mendapat dashboard sesuai kebutuhan masing-masing agar alur kerja tetap fokus dan efisien. |
##### Komponen 4 — StatisticsSection
- H2: **"Teruji untuk Skala Besar"**
- Paragraf subtitle: *"Stabil saat puncak pelaksanaan ujian, tetap nyaman digunakan tim akademik."*
| Angka | Label |
| **99,9%** | Ketersediaan Platform |
| **10.000+** | Soal Tersimpan |
| **500+** | Ujian Terselenggara |
##### Komponen 5 — AboutSection
**Header section (terpusat):**
- H2: **"Tentang CBT Pro"**
- Paragraf subtitle: *"Kami percaya kualitas evaluasi pembelajaran meningkat saat teknologi bekerja di belakang layar, bukan menambah beban tim pengajar."*
**Grid 3 kolom** — setiap item berupa ikon berwarna + judul + deskripsi, **tanpa card border**:
| Ikon | Judul | Deskripsi |
| `ri-layout-line` | Antarmuka Bersih | Tampilan dibuat fokus pada tugas utama, jadi pengguna baru pun bisa langsung produktif. |
| `ri-time-line` | Operasional Ringkas | Mulai dari setup ujian sampai rekap hasil dipersingkat agar tim punya lebih banyak waktu untuk evaluasi. |
| `ri-lock-line` | Keamanan Terjaga | Setiap sesi dirancang dengan kontrol akses dan jejak aktivitas agar proses ujian lebih terpercaya. |
##### Komponen 6 — CTASection
**Layout 2-zona horizontal** (bukan terpusat):
| Kiri | Kanan |
| H3: **"Siap Memulai?"** + paragraf: *"Masuk ke CBT Pro dan kelola ujian digital dari satu dashboard terpadu."* | Tombol utama → ikon + "Masuk Sekarang" → `/login/` |
##### Komponen 7 — Footer
**Layout 2-zona horizontal:**
| Kiri | Kanan |
| Teks: *"© [tahun] CBT Pro. Hak cipta dilindungi."* | Ikon sosial media: `ri-instagram-line`, `ri-facebook-line`, `ri-youtube-line`, `ri-whatsapp-line` — masing-masing link `#` |
#### 26.1.2 Halaman Masuk
**URL:** `/login/`
**Akses:** Publik (redirect ke dashboard jika sudah login)
**Fitur:**
- Form masuk dengan validasi
- Dukungan login via username atau email
- Pilihan ingat saya
- Redirect berdasarkan role setelah berhasil
- Penanganan error kredensial tidak valid
**Layout halaman:**
**`LoginCard`**
- Logo image saja: `<img src="logo-B-dark.png">` terpusat, tanpa teks di bawahnya 
- Title: "CBT Pro"
- Subtitle: "Masuk ke akun Anda"
**`LoginForm`** (`method="post"`, `novalidate`)
| Label | Tipe Input | Nama Field | Keterangan |
| Username atau Email | text | `username` | Input group dengan ikon, `autofocus`, wajib |
| Kata Sandi | password | `password` | Input group dengan ikon, wajib |
| — | toggle button | — | Tampilkan/sembunyikan kata sandi (ikon mata) |
| Ingat saya | checkbox | `remember_me` | Opsional — sesi 30 hari jika dicentang, session browser jika tidak |
**`LoginButton`**
- "Masuk" → submit form; loading state: spinner + teks "Memproses..."
**`ErrorMessages`** (dari Django messages / form errors)
| Kondisi | Pesan |
| Username/email tidak ditemukan | "Username atau email tidak terdaftar." |
| Kata sandi salah | "Kata sandi yang Anda masukkan salah." |
| Akun nonaktif | "Akun Anda telah dinonaktifkan. Hubungi administrator." |
**Redirect setelah berhasil:**
- Role `admin` → `/admin/dashboard/`
- Role `teacher` → `/teacher/dashboard/`
- Role `student` → `/student/dashboard/`
**Footer kartu:** © [tahun] CBT Pro
**Catatan:** Tidak ada tautan daftar mandiri. Tidak ada tautan lupa kata sandi.
### 26.2 HALAMAN BERSAMA (Semua Role)
#### 26.2.1 Profil Saya
**URL:** `/profile/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Profil Saya
**Akses:** Semua pengguna yang sudah login
**Fitur:**
- Unggah & pratinjau foto profil sebelum disimpan
- Edit informasi dasar (nama, email, telepon)
- Field khusus per role (guru/siswa)
- Tombol simpan standar
**`PageHeader`**
- Title: "Profil Saya"
- Subtitle: "Kelola informasi akun Anda"
**Layout 2 kolom:**
**`AccountInfoCard`**
| Elemen | Detail |
| Foto profil | Bulat — atau placeholder inisial (warna aksen, inisial 2 huruf) |
| Tombol ganti foto | Ikon kamera overlay di atas avatar, klik membuka file picker |
| Pratinjau langsung | JavaScript FileReader — gambar tampil sebelum form disubmit |
| Nama lengkap | `user.full_name` |
| Badge role | "Admin" / "Guru" / "Siswa" |
| Email | `user.email` |
**`ProfileFormCard`**
- Header kartu: "Informasi Profil"
- Form multipart POST (untuk upload foto)
| Label | Tipe | Nama Field | Validasi / Keterangan |
| Nama Depan | text | `first_name` | Wajib, maks. 150 karakter |
| Nama Belakang | text | `last_name` | Opsional, maks. 150 karakter |
| Alamat Email | email | `email` | Wajib, harus unik |
| No. Telepon | text | `phone_number` | Opsional, maks. 20 karakter |
| *(Khusus Guru)* ID Guru | text | `teacher_id` | Opsional, tampil jika `user.is_teacher` |
| *(Khusus Guru)* Spesialisasi Mata Pelajaran | text | `subject_specialization` | Opsional |
| *(Khusus Siswa)* NIS / ID Siswa | text | `student_id` | Opsional, tampil jika `user.is_student` |
| *(Khusus Siswa)* Kelas | text | `class_grade` | Opsional |
| Bio | textarea | `bio` | Opsional, 3 baris, placeholder "Ceritakan sedikit tentang diri Anda..." |
| Foto Profil | file | `profile_picture` | Tersembunyi, `accept="image/*"`, diakses via tombol kamera |
**Tombol:**
- "Simpan Perubahan"
- "Batal" → link ke `dashboard:home`
**Notifikasi:** Toast hijau "Profil berhasil diperbarui."
#### 26.2.2 Ubah Kata Sandi
**URL:** `/change-password/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Ubah Kata Sandi
**Akses:** Semua pengguna yang sudah login
**Fitur:**
- Validasi kata sandi saat ini
- Indikator kekuatan kata sandi baru
- Sesi tetap aktif setelah berhasil (update_session_auth_hash)
**`PageHeader`**
- Title: "Ubah Kata Sandi"
- Subtitle: "Pastikan akun Anda tetap aman"
**`ChangePasswordCard`** (centered, max 540px)
- `method="post"`
| Label | Tipe | Nama Field | Keterangan |
| Kata Sandi Saat Ini | password | `current_password` | Input group + toggle tampilkan/sembunyikan |
| Kata Sandi Baru | password | `new_password` | Input group + toggle, min. 8 karakter |
| Konfirmasi Kata Sandi Baru | password | `confirm_password` | Input group + toggle, harus cocok |
**`StrengthIndicator`** (Alpine.js, muncul setelah mengetik di `new_password`):
| Level | Warna Bar | Kondisi |
| Lemah | `danger` (merah) | Panjang < 8 karakter |
| Sedang | `warning` (kuning) | ≥ 8 karakter, hanya huruf atau hanya angka |
| Kuat | `success` (hijau) | ≥ 8 karakter + huruf besar + angka |
**`RulesList`** (checklist visual):
- ✓ Minimal 8 karakter
- ✓ Mengandung huruf besar
- ✓ Mengandung angka
**Pesan Validasi:**
| Kondisi | Pesan |
| Kata sandi saat ini salah | "Kata sandi saat ini tidak sesuai." |
| Konfirmasi tidak cocok | "Konfirmasi kata sandi tidak sesuai." |
| Kata sandi terlalu lemah | "Kata sandi minimal 8 karakter." |
**Tombol:**
- "Simpan Kata Sandi"
- "Batal" → link ke `dashboard:home`
**Notifikasi:** Toast hijau "Kata sandi berhasil diubah."
### 26.3 ADMIN DASHBOARD
#### 26.3.1 Dasbor Admin
**URL:** `/admin/dashboard/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda
**Akses:** Role `admin`
**Fitur:**
- Statistik platform secara keseluruhan
- Panel aksi cepat
- Log aktivitas terbaru
- Ringkasan kesehatan sistem
**`PageHeader`**
- Title: "Dasbor"
- Subtitle: "Selamat datang, {{ request.user.full_name }}"
**`StatCards`** (baris 4 kartu, masing-masing):
| Kartu | Ikon | Nilai | Label |
| Total Pengguna | ikon pengguna | `{{ total_users }}` | "Total Pengguna" |
| Total Ujian | ikon ujian | `{{ total_exams }}` | "Total Ujian Dibuat" |
| Ujian Hari Ini | ikon kalender | `{{ exams_today }}` | "Ujian Berlangsung Hari Ini" |
| Tingkat Kelulusan | ikon grafik | `{{ pass_rate }}%` | "Rata-rata Kelulusan" |
**Two-column layout:**
**`RecentActivityCard`**
- Header: "Aktivitas Terbaru"
- Tabel:
| Kolom | Isi |
| Pengguna | Avatar + nama |
| Aksi | Deskripsi singkat aksi |
| Keterangan | Detail aksi |
| Waktu | `created_at\|timesince` + " yang lalu" |
- Maks. 10 baris terbaru
- Jika kosong: "Belum ada aktivitas tercatat."
- Link footer: "Lihat semua aktivitas"
**`QuickActionsCard`**
- Header: "Aksi Cepat"
- Daftar tombol (penuh lebar):
 - "Tambah Pengguna" → `users:create`
 - "Tambah Mata Pelajaran" → `subjects:create`
 - "Pengaturan Sistem" → `core:settings`
 - "Lihat Analitik" → `analytics:dashboard`
#### 26.3.2 Manajemen Pengguna — Daftar
**URL:** `/admin/users/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Manajemen Pengguna
**Akses:** Role `admin`
**Fitur:**
- Daftar semua pengguna dengan pencarian & filter
- Tambah, edit, reset sandi, aktifkan/nonaktifkan pengguna
- Paginasi 20 data per halaman
**`PageHeader`**
- Title: "Manajemen Pengguna"
- Subtitle: "Kelola semua akun pengguna sistem"
- Action buttons (right):
 - "Import Excel" (ikon) → membuka `ImportUsersModal`
 - "Tambah Pengguna" (ikon, primary) → `users:create`
**`ImportUsersModal`** (modal besar):
Dipicu oleh tombol "Import Excel" di PageHeader. Tidak ada halaman terpisah untuk fitur ini.
| Elemen | Detail |
| Modal title | "Import Pengguna via Excel" |
| Download template | Link "Unduh Template Excel" → `users:import_template` (file `.xlsx` berisi contoh format) |
| Upload field | `<input type="file" accept=".xlsx,.xls">` — drag & drop area atau klik untuk browse |
| Preview tabel | Setelah file dipilih: tampilkan preview 5 baris pertama + total baris terdeteksi |
| Kolom yang dikenali | `username`, `email`, `first_name`, `last_name`, `role` (`admin`/`teacher`/`student`), `password` (opsional — jika kosong, sistem generate otomatis) |
| Validasi sisi klien | Cek kolom wajib ada sebelum submit |
| Tombol modal | "Batal" (dismiss) \| "Import Sekarang" (POST `users:import_excel`, disabled hingga file valid dipilih) |
| Progress & hasil | Setelah submit: tampilkan ringkasan — berhasil X, gagal Y (dengan detail baris error jika ada) |
> **Backend:** View `users:import_excel` memproses file dengan `openpyxl`, validasi per baris, buat User + UserProfile, kembalikan JSON hasil. Gunakan AJAX (Axios) agar modal tidak reload halaman. Tampilkan hasil di dalam modal itu sendiri.
**`SearchForm`** (GET, inline 4 elemen):
| Elemen | Tipe | Keterangan |
| Cari | text input | Placeholder: "Cari nama, username, atau email..." |
| Filter Role | select | Semua Role / Admin / Guru / Siswa |
| Filter Status | select | Semua Status / Aktif / Nonaktif |
| Tombol | submit | "Cari" |
| Reset | link | "Reset Filter" (muncul jika ada filter aktif) |
**`UserTable`**:
| Kolom | Isi | Keterangan |
| Pengguna | Foto/inisial 36px + nama lengkap + username | Avatar bulat |
| Email | `user.email` | — |
| Role | Badge | "Admin" / "Guru" / "Siswa" |
| Status | Badge | "Aktif" / "Nonaktif" |
| Bergabung | `created_at\|date:"d M Y"` | — |
| Terakhir Login | `last_login\|date:"d M Y"` atau "Belum pernah" | — |
| Aksi | Tombol | Lihat detail di bawah |
**Kolom Aksi**:
- "Detail" → `users:detail pk`
- "Edit" → `users:edit pk`
- "Reset Sandi" → `users:reset_password pk`
- "Nonaktifkan" / "Aktifkan" → POST `users:toggle_active pk`
**Paginasi:** "Menampilkan X–Y dari Z pengguna" | Tombol halaman Bootstrap
**Empty state:** Ikon besar + "Tidak ada pengguna ditemukan." + tombol "Reset Filter"
#### 26.3.3 Tambah Pengguna
**URL:** `/admin/users/create/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Manajemen Pengguna › Tambah Pengguna
**Fitur:**
- Form lengkap pembuatan akun pengguna baru
- Satu-satunya cara menambah pengguna ke sistem
**`PageHeader`**
- Title: "Tambah Pengguna Baru"
**`UserFormCard`**:
| Label | Tipe | Nama Field | Validasi |
| Username | text | `username` | Wajib, unik, maks. 150 karakter, hanya huruf/angka/underscore |
| Alamat Email | email | `email` | Wajib, harus unik |
| Nama Depan | text | `first_name` | Wajib, maks. 150 karakter |
| Nama Belakang | text | `last_name` | Opsional, maks. 150 karakter |
| Role | select | `role` | Wajib — Admin / Guru / Siswa |
| Kata Sandi | password | `password1` | Wajib, min. 8 karakter, show/hide toggle |
| Konfirmasi Kata Sandi | password | `password2` | Wajib, harus cocok, show/hide toggle |
| Status Akun | checkbox | `is_active` | Default: dicentang (Aktif) |
**Tombol:**
- "Simpan Pengguna"
- "Batal" → `users:list`
**Notifikasi:** Toast hijau "Pengguna berhasil ditambahkan."
#### 26.3.4 Edit Pengguna
**URL:** `/admin/users/<pk>/edit/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Manajemen Pengguna › Edit Pengguna
**`PageHeader`**
- Title: "Edit Pengguna: {{ user.full_name }}"
**`EditFormCard`**:
| Label | Tipe | Nama Field | Keterangan |
| Nama Depan | text | `first_name` | Pre-fill dari data existing |
| Nama Belakang | text | `last_name` | Pre-fill |
| Alamat Email | email | `email` | Pre-fill |
| Role | select | `role` | Pre-fill |
| Status Akun | checkbox | `is_active` | Pre-fill |
> Kata sandi tidak dapat diubah di sini. Gunakan halaman Reset Kata Sandi.
**Tombol:**
- "Simpan Perubahan"
- "Batal" → `users:detail pk`
**Notifikasi:** Toast hijau "Data pengguna berhasil diperbarui."
#### 26.3.5 Detail Pengguna
**URL:** `/admin/users/<pk>/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Manajemen Pengguna › Detail Pengguna
**`PageHeader`**
- Title: `{{ user.full_name }}`
- Tombol kanan: "Edit", "Reset Sandi", "Nonaktifkan/Aktifkan"
**Two-column layout:**
**`IdentityCard`**
| Elemen | Isi |
| Foto profil | 120px bulat atau placeholder inisial |
| Nama lengkap | `user.full_name` — teks besar, tebal |
| Username | `@username` (ditampilkan lebih kecil) |
| Email | `user.email` |
| Badge role | Sesuai role |
| Badge status | "Aktif" / "Nonaktif" |
| Bergabung | `created_at\|date:"d M Y"` |
| Terakhir login | `last_login\|date:"d M Y H:i"` |
**`ProfileInfoCard`**
| Label | Nilai |
| ID Guru / NIS Siswa | `teacher_id` atau `student_id` atau "-" |
| No. Telepon | `phone_number` atau "-" |
| Spesialisasi / Kelas | `subject_specialization` atau `class_grade` atau "-" |
| Bio | `bio` atau "-" |
**`ActivityLogCard`**
- Header: "Log Aktivitas Terbaru"
- Tabel: Aksi | Keterangan | Alamat IP | Waktu
- 10 entri terbaru
#### 26.3.6 Reset Kata Sandi Pengguna
**URL:** `/admin/users/<pk>/reset-password/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Manajemen Pengguna › Reset Kata Sandi
**`PageHeader`**
- Title: "Reset Kata Sandi"
- Subtitle: "Akun: {{ user.full_name }} ({{ user.username }})"
**`ResetFormCard`** (centered, max 480px):
| Label | Tipe | Nama Field | Keterangan |
| Kata Sandi Baru | password | `new_password` | Min. 8 karakter, show/hide toggle |
| Konfirmasi Kata Sandi Baru | password | `confirm_password` | Harus cocok, show/hide toggle |
**Tombol:**
- "Reset Kata Sandi"
- "Batal" → `users:detail pk`
**Notifikasi:** Toast kuning "Kata sandi pengguna berhasil direset."
#### 26.3.7 Manajemen Mata Pelajaran — Daftar
**URL:** `/admin/subjects/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Mata Pelajaran
**Akses:** Role `admin`
**`PageHeader`**
- Title: "Mata Pelajaran"
- Subtitle: "Kelola daftar mata pelajaran yang tersedia"
- Tombol kanan: "Tambah Mata Pelajaran" → `subjects:create`
**`SearchForm`** (GET):
| Elemen | Keterangan |
| Cari | Placeholder: "Cari nama atau kode mata pelajaran..." |
| Tombol | "Cari" |
**`SubjectTable`**:
| Kolom | Isi | Keterangan |
| Nama | `subject.name` | — |
| Kode | `subject.code` atau "-" | — |
| Deskripsi | Truncated 80 karakter | — |
| Jumlah Soal | Count dari relasi ke `Question` | Annotated |
| Status | Badge | "Aktif" / "Nonaktif" |
| Aksi | Tombol | Lihat detail di bawah |
**Kolom Aksi:**
- "Edit" → `subjects:edit pk`
- "Nonaktifkan/Aktifkan" → POST `subjects:toggle pk`
- "Hapus" → trigger `confirmDelete` (hanya jika jumlah soal = 0)
**Catatan Hapus:** Jika mata pelajaran masih memiliki soal, tombol hapus dinonaktifkan (`disabled`) dengan tooltip "Tidak dapat dihapus karena masih memiliki soal".
**Empty state:** "Belum ada mata pelajaran. Tambahkan mata pelajaran pertama." + tombol "Tambah Mata Pelajaran"
#### 26.3.8 Tambah / Edit Mata Pelajaran
**Tambah URL:** `/admin/subjects/create/`
**Edit URL:** `/admin/subjects/<pk>/edit/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Mata Pelajaran › Tambah / Edit Mata Pelajaran
**`SubjectFormCard`**:
| Label | Tipe | Nama Field | Validasi |
| Nama Mata Pelajaran | text | `name` | Wajib, unik, maks. 100 karakter |
| Kode | text | `code` | Opsional, unik, maks. 20 karakter, placeholder "Contoh: MTK, FIS, ENG" |
| Deskripsi | textarea | `description` | Opsional, 3 baris |
| Status Aktif | checkbox | `is_active` | Default: dicentang |
**Tombol:**
- "Simpan"
- "Batal" → `subjects:list`
#### 26.3.9 Pengaturan Sistem
**URL:** `/admin/settings/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Pengaturan Sistem
**Akses:** Role `admin`
**`PageHeader`**
- Title: "Pengaturan Sistem"
**`TabNavigasi`** (Bootstrap tabs):
**Tab 1 — Umum:**
| Label | Tipe | Kunci Setting | Default |
| Nama Situs | text | `site_name` | "CBT Pro" |
| URL Situs | url | `site_url` | "<http://localhost:8000>" |
| Deskripsi Situs | textarea | `site_description` | — |
| Zona Waktu | select | `timezone` | "Asia/Jakarta" |
| Bahasa | select | `language` | "Bahasa Indonesia" |
**Tab 2 — Keamanan:**
| Label | Tipe | Kunci Setting | Default |
| Durasi Sesi (menit) | number | `session_timeout` | 120 |
| Maks. Percobaan Login | number | `max_login_attempts` | 5 |
| Masa Blokir Login (menit) | number | `login_lockout_duration` | 15 |
| Panjang Kata Sandi Minimum | number | `min_password_length` | 8 |
**Tab 3 — Default Ujian:**
| Label | Tipe | Kunci Setting | Default |
| Durasi Default (menit) | number | `default_exam_duration` | 90 |
| Nilai Kelulusan Default (%) | number | `default_passing_score` | 75 |
| Aktifkan Layar Penuh | checkbox | `default_require_fullscreen` | ✓ |
| Deteksi Perpindahan Tab | checkbox | `default_detect_tab_switch` | ✓ |
| Maks. Pelanggaran | number | `default_max_violations` | 3 |
| Tampilkan Hasil Langsung | checkbox | `default_show_results_immediately` | ✗ |
| Izinkan Review Jawaban | checkbox | `default_allow_review` | ✓ |
**Tab 4 — Email:**
| Label | Tipe | Kunci Setting |
| Host SMTP | text | `email_host` |
| Port SMTP | number | `email_port` |
| Gunakan TLS | checkbox | `email_use_tls` |
| Username Email | text | `email_host_user` |
| Email Pengirim Default | email | `default_from_email` |
| Tombol Test | button | — → kirim email test |
**Tombol (setiap tab):**
- "Simpan Pengaturan"
**Notifikasi:** Toast hijau "Pengaturan berhasil disimpan."
#### 26.3.10 Analitik & Laporan
**URL:** `/admin/analytics/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Analitik
**Akses:** Role `admin`
**Fitur:**
- Ringkasan statistik platform
- Grafik tren aktivitas 6 bulan
- Distribusi role pengguna
- Performa per mata pelajaran
- Ekspor laporan
**`PageHeader`**
- Title: "Analitik Sistem"
- Subtitle: "Gambaran umum performa platform"
**`DateRangeFilter`** (form GET):
- Dari Tanggal: `date_from` (DateInput)
- Sampai Tanggal: `date_to` (DateInput)
- Tombol: "Terapkan"
**`MainStatCards`** (baris 4 kartu):
| Kartu | Ikon | Nilai | Label |
| Total Pengguna | ikon | `total_users` | "Total Pengguna" |
| Total Ujian | ikon | `total_exams` | "Total Ujian" |
| Total Percobaan | ikon | `total_attempts` | "Total Percobaan Ujian" |
| Rata-rata Kelulusan | ikon | `overall_pass_rate`% | "Rata-rata Kelulusan" |
**Baris Grafik 1:**
`ActivityTrendChart` ("Tren Aktivitas 6 Bulan")
- Chart.js line chart
- Sumbu X: Jan / Feb / Mar / Apr / Mei / Jun (atau sesuai pilihan)
- Dataset: Jumlah percobaan ujian per bulan
- Warna garis: primary (biru)
`UserDistributionChart` ("Distribusi Pengguna")
- Chart.js doughnut
- Segmen: Admin (ungu), Guru (biru), Siswa (hijau)
- Legend di bawah
**Baris Grafik 2:**
`SubjectScoreChart` ("Rata-rata Nilai per Mata Pelajaran") → lebar penuh
- Chart.js bar chart horizontal atau vertikal
- Sumbu X: nama mata pelajaran
- Sumbu Y: rata-rata skor (0–100)
- Warna batang: primer per mata pelajaran
**`ExportButton`** (kanan atas):
- "Ekspor Laporan" → download Excel
### 26.4 GURU DASHBOARD
#### 26.4.1 Dasbor Guru
**URL:** `/teacher/dashboard/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda
**Akses:** Role `teacher`
**`PageHeader`**
- Title: "Dasbor Guru"
- Subtitle: "Selamat datang, {{ request.user.full_name }}"
**`StatCards`** (baris 3 kartu):
| Kartu | Ikon | Nilai | Label |
| Ujian Dibuat | ikon | `exams_created` | "Total Ujian Dibuat" |
| Ujian Aktif | ikon | `active_exams` | "Ujian Aktif Saat Ini" |
| Total Soal | ikon | `questions_created` | "Total Soal Dibuat" |
**Two-column layout:**
**`UpcomingExamsCard`**
- Header: "Ujian Mendatang"
- Tabel:
| Kolom | Isi |
| Judul Ujian | `exam.title` (link ke detail) |
| Mata Pelajaran | `exam.subject.name` |
| Mulai | `start_time\|date:"d M Y H:i"` |
| Durasi | `duration_minutes` menit |
| Status | Badge status |
| Aksi | "Edit" / "Monitor" |
- Maks. 5 baris
- Link footer: "Lihat Semua Ujian →"
- Empty state: "Tidak ada ujian mendatang."
**`RecentResultsCard`**
- Header: "Hasil Terbaru"
- List 5 item:
 - Nama ujian + mata pelajaran
 - Rata-rata skor + badge pass rate
 - Tanggal
- Link footer: "Lihat Semua Hasil →"
- Empty state: "Belum ada hasil ujian."
#### 26.4.2 Bank Soal — Daftar
**URL:** `/teacher/question-bank/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Bank Soal
**Akses:** Role `teacher`
**`PageHeader`**
- Title: "Bank Soal"
- Subtitle: "Kelola semua soal ujian Anda"
- Tombol kanan: "Impor Soal" (ikon) → membuka `ImportQuestionsModal` | "Ekspor Soal" (ikon) | "Tambah Soal" → `questions:create`
**`ImportQuestionsModal`** (modal sangat lebar):
Dipicu oleh tombol "Impor Soal". Tidak ada halaman terpisah.
| Elemen | Detail |
| Modal title | "Import Bank Soal via Excel" |
| Download template | Link "Unduh Template Excel" → `questions:import_template` |
| Upload field | Drag & drop area atau klik browse, `accept=".xlsx,.xls"` |
| Preview tabel | Setelah file dipilih: tampilkan 5 baris pertama + total soal terdeteksi |
| Kolom yang dikenali | `question_text`, `question_type` (`multiple_choice`/`essay`/`short_answer`), `subject_code`, `category`, `points`, `difficulty`, `option_a`–`option_e`, `correct_option`, `explanation` |
| Tombol modal | "Batal" \| "Import Sekarang" (POST `questions:import_excel`, AJAX) |
| Hasil | Ringkasan: X soal berhasil diimport, Y gagal (detail per baris error) |
**`FilterForm`** (GET, 4 elemen inline):
| Elemen | Tipe | Keterangan |
| Cari Soal | text | Placeholder: "Cari teks soal..." |
| Mata Pelajaran | select | Semua Mata Pelajaran + daftar aktif |
| Tipe Soal | select | Semua Tipe / Pilihan Ganda / Essay / Isian Singkat |
| Tingkat Kesulitan | select | Semua Tingkat / Mudah / Sedang / Sulit |
| Tombol | submit | "Filter" + "Reset" |
**`QuestionTable`**:
| Kolom | Isi | Keterangan |
| No. | Nomor urut paginasi | — |
| Soal | Teks soal di-strip HTML, truncated 80 karakter | + badge tipe soal |
| Mata Pelajaran | `question.subject.name` | — |
| Kesulitan | Badge | Mudah / Sedang / Sulit / "-" |
| Poin | `question.points` | — |
| Digunakan | `usage_count` kali | — |
| Aksi | 4 tombol | — |
**Kolom Aksi:**
- "Detail" → `questions:detail pk`
- "Edit" → `questions:edit pk`
- "Duplikat" → POST `questions:duplicate pk`
- "Hapus" → trigger `confirmDelete`
**Paginasi:** 25 soal per halaman
**Empty state:** Ikon besar + "Belum ada soal di bank soal Anda." + tombol "Tambah Soal Pertama"
#### 26.4.3 Tambah / Edit Soal
**Tambah URL:** `/teacher/question-bank/create/`
**Edit URL:** `/teacher/question-bank/<pk>/edit/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Bank Soal › Tambah Soal / Edit Soal
**Judul:** "Tambah Soal Baru" / "Edit Soal"
**Layout halaman:** 2 kolom — panel kiri (konten soal) + panel kanan (pengaturan)
**`QuestionContentCard`**:
**Bagian: Informasi Dasar**
| Label | Tipe | Nama Field | Keterangan |
| Tipe Soal | select | `question_type` | **Wajib diisi pertama** — Pilihan Ganda / Essay / Isian Singkat. Mengontrol field yang tampil di bawah (Alpine.js) |
| Mata Pelajaran | select | `subject` | Dropdown semua mata pelajaran aktif, wajib |
| Kategori | select | `category` | Opsional — dropdown kategori soal |
**Bagian: Teks Soal**
| Label | Tipe | Nama Field | Keterangan |
| Teks Soal | TinyMCE | `question_text` | Tinggi 350px. Plugin: lists link image table code. Wajib |
| Gambar Soal | file | `question_image` | Opsional, `accept="image/*"`. Preview langsung via JS |
**Bagian: Pilihan Jawaban** *(tampil hanya jika tipe = "Pilihan Ganda", Alpine.js kondisional)*
| Elemen per baris | Detail |
| Label otomatis | A / B / C / D / E (sesuai index) |
| Input teks | Placeholder "Masukkan teks pilihan..." |
| Radio "Jawaban Benar" | Satu pilihan, nama group `correct_option` |
| Tombol hapus | ikon — muncul jika jumlah opsi > 2 (kondisional) |
- Tombol "+ Tambah Pilihan" — muncul jika opsi < 5 (kondisional)
- Minimal 2 opsi, maksimal 5 opsi
**Bagian: Kunci Jawaban** *(tampil jika tipe = "Essay" atau "Isian Singkat")*
| Label | Tipe | Nama Field | Keterangan |
| Teks Jawaban / Kata Kunci | textarea | `answer_text` | Jawaban ideal atau kata kunci penilaian |
| Batas Kata Maksimum | number | `max_word_count` | Opsional — hanya untuk Essay |
| Peka Huruf Besar-Kecil | checkbox | `is_case_sensitive` | Opsional — hanya untuk Isian Singkat |
**Bagian: Pembahasan (Opsional)**
- TinyMCE kedua, untuk penjelasan/pembahasan soal
**`SettingsPanel`**:
**`QuestionSettingsCard`**:
| Label | Tipe | Nama Field | Default |
| Poin | number (step 0.25) | `points` | 1.00 |
| Tingkat Kesulitan | select | `difficulty_level` | — (kosong) / Mudah / Sedang / Sulit |
| Batas Waktu per Soal (detik) | number | `time_limit_seconds` | Kosong = tidak terbatas |
| Status Aktif | checkbox | `is_active` | ✓ |
**`NavigationSettingsCard`**:
| Label | Tipe | Nama Field | Default | Keterangan |
| Izinkan Kembali | checkbox | `allow_previous` | ✓ | Siswa boleh kembali ke soal ini |
| Izinkan Lanjut | checkbox | `allow_next` | ✓ | Siswa boleh melewati soal ini |
| Paksa Urutan | checkbox | `force_sequential` | ✗ | Harus dijawab sebelum lanjut |
> Catatan: Pengaturan navigasi per soal dapat di-override oleh pengaturan ujian.
**Tombol (di bawah panel):**
- "Simpan Soal"
- "Batal" → `questions:list`
#### 26.4.4 Detail Soal
**URL:** `/teacher/question-bank/<pk>/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Bank Soal › Detail Soal
**`PageHeader`**
- Title: "Detail Soal"
- Badge tipe soal + badge kesulitan
- Tombol kanan: "Edit" | "Duplikat" | "Hapus"
**Two-column layout:**
**`QuestionContent`**:
- Kartu "Teks Soal": render HTML TinyMCE (aman, `|safe`)
- Gambar soal (jika ada)
- Kartu "Pilihan Jawaban" *(jika pilihan ganda)*:
| Huruf | Teks Pilihan | Jawaban Benar |
| A | ... | ✓ (hijau) / — |
| B | ... | — |
| ... | ... | — |
- Kartu "Pembahasan": render HTML TinyMCE (jika ada)
**`MetadataSoal`**:
| Label | Nilai |
| Mata Pelajaran | `subject.name` |
| Kategori | `category.name` atau "-" |
| Tipe | Teks tipe soal |
| Poin | `points` |
| Kesulitan | Badge |
| Batas Waktu | `time_limit_seconds` detik atau "Tidak terbatas" |
| Izinkan Kembali | ✓ / ✗ |
| Izinkan Lanjut | ✓ / ✗ |
| Paksa Urutan | ✓ / ✗ |
| Digunakan | `usage_count` kali |
| Dibuat oleh | `created_by.full_name` |
| Tanggal Dibuat | `created_at\|date:"d M Y H:i"` |
**`QuestionStatsCard`**:
| Metrik | Nilai |
| Total Dijawab | `times_answered` kali |
| Dijawab Benar | `times_correct` kali |
| Dijawab Salah | `times_wrong` kali |
| Tingkat Kesulitan (Empiris) | `difficulty_index`% |
| Indeks Diskriminasi | `discrimination_index` |
| Rata-rata Waktu Pengerjaan | `average_time_seconds` detik |
#### 26.4.5 Manajemen Ujian — Daftar
**URL:** `/teacher/exams/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Manajemen Ujian
**Akses:** Role `teacher`
**`PageHeader`**
- Title: "Manajemen Ujian"
- Subtitle: "Buat dan kelola ujian Anda"
- Tombol kanan: "Buat Ujian Baru" → `exams:create`
**`FilterForm`** (GET):
| Elemen | Keterangan |
| Cari | Placeholder: "Cari judul ujian..." |
| Filter Status | Semua / Draf / Diterbitkan / Berlangsung / Selesai / Dibatalkan |
| Filter Mata Pelajaran | Dropdown semua mata pelajaran |
**`ExamTable`**:
| Kolom | Isi | Keterangan |
| Judul Ujian | `exam.title` | Link ke detail |
| Mata Pelajaran | `exam.subject.name` | — |
| Status | Badge | Lihat tabel status di bawah |
| Mulai | `start_time\|date:"d M Y H:i"` | — |
| Selesai | `end_time\|date:"d M Y H:i"` | — |
| Soal | `question_count` soal | Annotated |
| Peserta | `participant_count` siswa | Annotated |
| Aksi | Kondisional per status | Lihat tabel di bawah |
**Badge Status:**
| Status DB | Label | Warna Badge |
| `draft` | Draf | Badge abu/ungu |
| `published` | Diterbitkan | Badge hijau |
| `ongoing` | Berlangsung | Badge biru |
| `completed` | Selesai | Badge abu |
| `cancelled` | Dibatalkan | Badge merah |
**Kolom Aksi (kondisional):**
| Tombol | Muncul Jika | Aksi |
| "Detail" | Selalu | → `exams:detail pk` |
| "Edit" | Status = Draf | → `exams:edit pk` |
| "Terbitkan" | Status = Draf | → POST `exams:publish pk` |
| "Monitor" | Status = Berlangsung | → `monitoring:live pk` |
| "Hasil" | Status = Selesai | → `results:teacher_exam pk` |
| "Batalkan" | Status = Diterbitkan / Berlangsung | → POST `exams:cancel pk` |
| "Duplikat" | Selalu | → POST `exams:duplicate pk` |
**Empty state:** "Belum ada ujian. Buat ujian pertama Anda." + tombol "Buat Ujian Baru"
#### 26.4.6 Wizard Buat Ujian — Langkah 1: Informasi Dasar
**URL:** `/teacher/exams/create/1/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Manajemen Ujian › Buat Ujian Baru
**`ProgressBar`:** ① **Informasi** → ② Soal → ③ Pengaturan → ④ Penugasan
**`ExamInfoCard`**:
| Label | Tipe | Nama Field | Validasi |
| Judul Ujian | text | `title` | Wajib, maks. 255 karakter |
| Mata Pelajaran | select | `subject` | Wajib — dropdown mata pelajaran aktif |
| Deskripsi | textarea | `description` | Opsional, 3 baris |
| Instruksi untuk Siswa | textarea | `instructions` | Opsional, 4 baris — ditampilkan ke siswa sebelum mulai ujian |
| Tanggal & Waktu Mulai | datetime-local | `start_time` | Wajib |
| Tanggal & Waktu Selesai | datetime-local | `end_time` | Wajib — harus lebih besar dari waktu mulai |
| Durasi Pengerjaan (menit) | number | `duration_minutes` | Wajib, min. 5, maks. 480 |
| Nilai Kelulusan (%) | number | `passing_score` | Wajib, min. 0, maks. 100, default 75 |
**Validasi:**
- `end_time` harus lebih besar dari `start_time`
- `duration_minutes` tidak boleh melebihi selisih `start_time` dan `end_time`
**Tombol:**
- "Lanjut ke Pilih Soal →"
- "Batal" → `exams:list`
#### 26.4.7 Wizard Buat Ujian — Langkah 2: Pilih Soal
**URL:** `/teacher/exams/create/2/`
**Progress Bar:** ① Informasi → ② **Soal** → ③ Pengaturan → ④ Penugasan
**Layout dua panel:**
**`QuestionSearchPanel`**:
- Header: "Cari & Tambah Soal"
- Input cari (AJAX real-time, debounce 300ms)
- Filter mata pelajaran (default: mata pelajaran ujian)
- Filter tipe soal
**`SearchResults`** (AJAX, muncul di bawah input):
Per baris soal:
| Elemen | Detail |
| Teks soal | Truncated 60 karakter, HTML stripped |
| Badge tipe | Pilihan Ganda / Essay / Isian Singkat |
| Badge kesulitan | / |
| Poin | `X poin` |
| Tombol tambah | "+" → klik menambahkan ke panel kanan |
**`SelectedQuestionsPanel`**:
- Header: "Soal Terpilih" + counter "**X soal / Y poin total**"
- Empty state: "Belum ada soal dipilih. Cari dan tambahkan dari panel kiri."
Per baris soal terpilih:
| Elemen | Detail |
| Handle drag | ikon — klik drag untuk ubah urutan |
| Nomor urut | Otomatis terupdate |
| Teks soal | Truncated 60 karakter |
| Badge tipe + kesulitan | — |
| Input poin override | number kecil (opsional, default dari poin soal) |
| Tombol hapus | ikon |
- Counter bawah: "Total: **X soal** \| **Y poin**" — update real-time
**Tombol:**
- "← Kembali"
- "Lanjut ke Pengaturan →" → (disable jika soal = 0)
#### 26.4.8 Wizard Buat Ujian — Langkah 3: Pengaturan
**URL:** `/teacher/exams/create/3/`
**Progress Bar:** ① Informasi → ② Soal → ③ **Pengaturan** → ④ Penugasan
**`ExamResultSettingsCard`**:
| Label | Tipe | Nama Field | Default |
| Acak Urutan Soal | toggle switch | `randomize_questions` | Tidak |
| Acak Urutan Pilihan Jawaban | toggle switch | `randomize_options` | Tidak |
| Tampilkan Hasil Langsung Setelah Submit | toggle switch | `show_results_immediately` | Tidak |
| Izinkan Siswa Review Jawaban | toggle switch | `allow_review` | Ya |
**`GlobalNavSettingsCard`**:
| Label | Tipe | Nama Field | Default | Keterangan |
| Override Navigasi Soal Global | toggle switch | `override_question_navigation` | Tidak | Jika aktif, semua soal menggunakan aturan di bawah |
| Izinkan Kembali (Global) | checkbox | `global_allow_previous` | ✓ | Aktif jika override = Ya |
| Izinkan Lanjut (Global) | checkbox | `global_allow_next` | ✓ | Aktif jika override = Ya |
| Paksa Urutan (Global) | checkbox | `global_force_sequential` | ✗ | Aktif jika override = Ya |
**`AntiCheatSettingsCard`**:
| Label | Tipe | Nama Field | Default |
| Paksa Mode Layar Penuh | toggle switch | `require_fullscreen` | Ya |
| Deteksi Perpindahan Tab | toggle switch | `detect_tab_switch` | Ya |
| Aktifkan Tangkap Layar Otomatis | toggle switch | `enable_screenshot_proctoring` | Tidak |
| Interval Tangkap Layar (detik) | number | `screenshot_interval_seconds` | 300 — tampil jika proctoring aktif |
| Maks. Pelanggaran Sebelum Auto-Submit | number | `max_violations_allowed` | 3 |
**`ReAttemptSettingsCard`**:
| Label | Tipe | Nama Field | Default | Keterangan |
| Izinkan Pengulangan Ujian | toggle switch | `allow_reattempt` | Tidak | Jika aktif, siswa dapat mengerjakan ulang ujian setelah selesai |
| Maks. Jumlah Percobaan | number | `max_attempts` | 1 | Total percobaan yang diizinkan (min. 1); 0 = tidak terbatas. Hanya aktif jika izinkan pengulangan = Ya |
| Metode Penilaian Akhir | select | `scoring_method` | Nilai Tertinggi | **Nilai Tertinggi** = ambil skor terbaik dari semua percobaan; **Percobaan Terakhir** = gunakan skor percobaan paling akhir |
> Jika "Izinkan Pengulangan Ujian" dinonaktifkan, `max_attempts` otomatis = 1 dan field ini tersembunyi.
**Tombol:**
- "← Kembali"
- "Lanjut ke Penugasan →" (primary)
#### 26.4.9 Wizard Buat Ujian — Langkah 4: Penugasan
**URL:** `/teacher/exams/create/4/`
**Progress Bar:** ① Informasi → ② Soal → ③ Pengaturan → ④ **Penugasan**
**`AssignmentCard`**:
**Pilih Jenis Penugasan** (radio):
- ◉ Tugaskan ke Kelas
- ○ Tugaskan ke Siswa Tertentu
**Jika "Tugaskan ke Kelas" dipilih (kondisional):**
| Elemen | Detail |
| Pilih Kelas | Multi-select `ModelMultipleChoiceField` — daftar semua kelas aktif |
| Nama kelas | Tampil dengan jumlah siswa di dalamnya |
**Jika "Tugaskan ke Siswa Tertentu" dipilih (kondisional):**
| Elemen | Detail |
| Cari siswa | Input pencarian AJAX |
| Daftar hasil | Nama + kelas — klik untuk menambahkan |
| Siswa terpilih | Tags/chips yang bisa dihapus |
**`ExamSummaryCard`** (pratinjau di kanan atau bawah):
| Label | Nilai |
| Judul | `title` |
| Mata Pelajaran | `subject.name` |
| Waktu Mulai | `start_time` |
| Waktu Selesai | `end_time` |
| Durasi | `duration_minutes` menit |
| Jumlah Soal | X soal |
| Total Poin | Y poin |
| Nilai Kelulusan | `passing_score`% |
| Acak Soal | Ya / Tidak |
| Anti-Kecurangan | Aktif / Nonaktif |
| Maks. Percobaan | `max_attempts` (atau Tidak Terbatas) |
| Metode Penilaian | Nilai Tertinggi / Percobaan Terakhir |
**Tombol:**
- "← Kembali"
- "Simpan sebagai Draf"
- "Simpan & Terbitkan"
#### 26.4.10 Detail Ujian
**URL:** `/teacher/exams/<pk>/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Manajemen Ujian › Detail Ujian
**`PageHeader`**
- Title: `exam.title`
- Badge status ujian
- Tombol kanan (kondisional per status):
 - "Edit" (hanya Draf)
 - "Terbitkan" (hanya Draf)
 - "Monitor Langsung" (hanya Berlangsung)
 - "Batalkan" (Diterbitkan/Berlangsung)
 - "Duplikat"
**Two-column layout:**
**`ExamInfoCard`**:
| Label | Nilai |
| Mata Pelajaran | `subject.name` |
| Mulai | `start_time\|date:"d M Y H:i"` |
| Selesai | `end_time\|date:"d M Y H:i"` |
| Durasi | `duration_minutes` menit |
| Nilai Kelulusan | `passing_score`% |
| Jumlah Soal | `question_count` |
| Total Poin | `total_points` |
| Peserta | `participant_count` siswa |
| Acak Soal | Ya / Tidak |
| Acak Pilihan | Ya / Tidak |
| Layar Penuh | Ya / Tidak |
| Deteksi Tab | Ya / Tidak |
| Tangkap Layar | Ya / Tidak |
| Maks. Percobaan | `max_attempts` (atau Tidak Terbatas) |
| Metode Penilaian | Nilai Tertinggi / Percobaan Terakhir |
| Dibuat | `created_at\|date:"d M Y"` |
**`DescriptionCard`**:
- Header: "Deskripsi & Instruksi"
- Teks deskripsi
- Teks instruksi untuk siswa
**`QuestionListCard`**:
- Header: "Daftar Soal" + counter
- Tabel:
| No | Teks Soal | Tipe | Mata Pelajaran | Kesulitan | Poin |
**`AssignmentCard`**:
- Header: "Penugasan"
- Tabel: Jenis (Kelas/Siswa) | Nama | Tanggal Ditugaskan
#### 26.4.11 Pemantauan Langsung
**URL:** `/teacher/monitoring/<exam_id>/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Pemantauan › [Judul Ujian]
**Akses:** Role `teacher`
**Fitur:**
- Pemantauan siswa secara real-time via WebSocket
- Statistik live
- Feed pelanggaran
- Detail per siswa
**`PageHeader`**
- Title: `exam.title`
- Badge status ujian
- Sub-info: Tanggal · Durasi · Jumlah soal
- Tombol: "Refresh Data"
**`LiveStats`** (baris 4 mini-kartu):
| Kartu | Ikon | Label |
| Total Terdaftar | ikon | "Total Terdaftar" |
| Sedang Ujian | ikon | "Sedang Ujian" |
| Sudah Selesai | ikon | "Sudah Selesai" |
| Tidak Hadir | ikon | "Tidak Hadir" |
**Two-column layout:**
**`StudentGrid`**:
Per kartu siswa (id="student-{{ student.id }}"):
| Elemen | Detail |
| Avatar / inisial | bulat |
| Nama siswa | Teks utama |
| Nomor soal saat ini | "Soal X / Y" |
| Mini progress bar | `answered / total` × 100% |
| Badge pelanggaran | badge jika violations > 0 |
| Badge status | Berlangsung / Selesai / Belum Mulai |
- Border kartu merah jika `violations >= max_violations_allowed`
- Update real-time via WebSocket
**`ViolationFeed`**:
- Header: "Log Pelanggaran"
- Daftar kronologis (terbaru di atas):
 - Nama siswa + badge jenis pelanggaran + waktu
 - Jenis: Perpindahan Tab / Keluar Layar Penuh / Salin-Tempel / Klik Kanan
- Auto-scroll ke bawah
- Maks. 50 entri terakhir
- Empty state: "Belum ada pelanggaran tercatat."
#### 26.4.12 Hasil Ujian — Daftar (Guru)
**URL:** `/teacher/results/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Hasil Ujian
**Akses:** Role `teacher`
**`PageHeader`**
- Title: "Hasil Ujian"
- Subtitle: "Analisis performa siswa per ujian"
**`FilterForm`** (GET):
| Elemen | Keterangan |
| Filter Mata Pelajaran | Dropdown |
| Rentang Tanggal | `date_from` + `date_to` |
| Tombol | "Filter" + "Reset" |
**`ResultListTable`**:
| Kolom | Isi |
| Ujian | `exam.title` |
| Mata Pelajaran | `exam.subject.name` |
| Tanggal Selesai | `end_time\|date:"d M Y"` |
| Peserta | `participant_count` siswa |
| Rata-rata | `avg_score`% |
| Tertinggi | `highest_score`% |
| Terendah | `lowest_score`% |
| Pass Rate | `pass_rate`% badge |
| Aksi | "Lihat Detail" / "Ekspor" |
**Kolom Aksi:**
- "Lihat Detail" → `results:teacher_exam pk`
- "Ekspor" → `results:export pk`
#### 26.4.13 Detail Hasil Ujian (Guru)
**URL:** `/teacher/results/<exam_id>/exam/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Hasil Ujian › [Judul Ujian]
**`PageHeader`**
- Title: `exam.title`
- Subtitle: `exam.subject.name` · `exam.end_time\|date:"d M Y"`
- Tombol: "Ekspor Excel"
**`ResultStats`** (baris 5 mini-kartu):
| Kartu | Nilai |
| Rata-rata Nilai | `avg_score`% |
| Nilai Tertinggi | `highest_score`% |
| Nilai Terendah | `lowest_score`% |
| Standar Deviasi | `std_deviation` |
| Pass Rate | `pass_rate`% |
**`ScoreDistributionChart`** — Chart.js histogram, lebar penuh
- Sumbu X: rentang nilai (0–10, 10–20, ..., 90–100)
- Sumbu Y: jumlah siswa
**`StudentResultTable`**:
| Kolom | Isi |
| Peringkat | `rank` |
| Nama Siswa | `student.full_name` |
| Total Nilai | `total_score` / `max_score` |
| Persentase | `percentage`% |
| Status | "Lulus" / "Tidak Lulus" |
| Waktu Pengerjaan | `time_spent_seconds` diformat |
| Aksi | "Detail" / "Nilai Essay" |
**Kolom Aksi:**
- "Detail" → `results:teacher_detail pk`
- "Nilai Essay" → (muncul jika ada soal essay belum dinilai)
**`ItemAnalysis`** (di bawah):
- Header: "Analisis Item Soal"
- Tabel per soal:
| Kolom | Isi |
| No | Urutan soal |
| Teks Soal | Truncated |
| Tipe | Badge |
| Dijawab | X kali |
| Benar | X kali |
| Tingkat Kesulitan | `difficulty_index`% |
| Diskriminasi | `discrimination_index` |
#### 26.4.14 Penilaian Essay
**URL:** `/teacher/results/<attempt_id>/grade/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Hasil Ujian › Penilaian Essay
**`PageHeader`**
- Title: "Penilaian Essay"
- Subtitle: `student.full_name` — `exam.title`
Per soal essay, kartu terpisah:
- Teks soal (render HTML)
- Jawaban siswa (dalam kotak abu)
- Pembahasan/kunci (jika ada, dalam `<details>` collapse)
- Input: "Nilai" number (0 – `points_possible`) + "Komentar" textarea
- Tombol: "Simpan Nilai" (AJAX POST)
**Tombol bawah halaman:**
- "Selesai Penilaian" → redirect ke detail hasil
### 26.5 SISWA DASHBOARD
#### 26.5.1 Dasbor Siswa
**URL:** `/student/dashboard/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda
**Akses:** Role `student`
**`PageHeader`**
- Title: "Halo, {{ request.user.first_name }}! 👋"
- Subtitle: `date today\|date:"l, d F Y"`
**`StudentStats`** (baris 3 kartu):
| Kartu | Ikon | Nilai | Label |
| Ujian Selesai | ikon | `total_completed` | "Ujian Diselesaikan" |
| Rata-rata Nilai | ikon | `avg_score`% | "Rata-rata Nilai" |
| Pass Rate | ikon | `pass_rate`% | "Tingkat Kelulusan" |
**Two-column layout:**
**`AvailableExamsCard`**:
- Header: "Ujian Tersedia"
- Kartu per ujian (maks. 3):
| Elemen | Detail |
| Judul ujian | Bold |
| Mata pelajaran | Badge |
| Durasi | `duration_minutes` menit |
| Tanggal mulai | `start_time\|date:"d M Y H:i"` |
| Countdown | Alpine.js countdown timer jika belum mulai |
| Tombol | "Mulai Ujian" / "Lanjutkan" |
- Link: "Lihat Semua Ujian →"
- Empty state: "Tidak ada ujian tersedia saat ini."
**`RecentResultsCard`**:
- Header: "Hasil Terbaru"
- List 5 item:
 - Nama ujian + mata pelajaran
 - Nilai besar + badge Lulus/Tidak Lulus
 - Tanggal
#### 26.5.2 Daftar Ujian
**URL:** `/student/exams/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Daftar Ujian
**Akses:** Role `student`
**`PageHeader`**
- Title: "Daftar Ujian"
- Subtitle: "Semua ujian yang ditugaskan kepada Anda"
**`StatusTabs`** (Bootstrap tabs):
| Tab | Label | Konten |
| `akan-datang` | Akan Datang | Ujian belum mulai |
| `tersedia` | Tersedia | Ujian sedang bisa dikerjakan |
| `selesai` | Selesai | Ujian sudah dikerjakan |
| `terlewat` | Terlewat | Ujian sudah lewat, belum dikerjakan |
**`FilterForm`** (GET, di atas tabs):
| Elemen | Keterangan |
| Cari | Placeholder: "Cari judul ujian..." |
| Filter Mata Pelajaran | Dropdown |
**`ExamCard`** (grid, per kartu):
| Elemen | Detail |
| Header kartu | Judul ujian (tebal) + badge mata pelajaran |
| Deskripsi singkat | Truncated 100 karakter |
| Ikon durasi | ikon + `duration_minutes` menit |
| Ikon soal | ikon + `question_count` soal |
| Jadwal | `start_time` – `end_time\|date:"d M Y H:i"` |
| Badge status | Sesuai kondisi |
| Countdown | Alpine.js (hanya tab "Akan Datang") |
| Tombol aksi | Kondisional per status |
**Tombol Aksi Kondisional:**
| Kondisi | Tombol |
| Belum mulai (waktu belum tiba) | "Belum Tersedia" (disabled) |
| Tersedia, belum dikerjakan | "Mulai Ujian" → `attempts:exam_detail exam_id` |
| In progress (ada attempt aktif) | "Lanjutkan Ujian" → `attempts:exam_room exam_id` |
| Sudah selesai, re-attempt tersedia (`attempts_used < max_attempts`) | "Lihat Hasil" + "Coba Lagi (X / Y)" — "Coba Lagi" membuka modal konfirmasi re-attempt |
| Sudah selesai, maks. percobaan tercapai | "Lihat Hasil" (tombol "Coba Lagi" nonaktif/tidak tampil) |
| Terlewat | "Terlewat" (disabled) |
**Info Percobaan:** Di bawah tombol aksi, tampilkan teks kecil: "Percobaan X dari Y" jika `max_attempts > 1`. Jika scoring method = "Nilai Tertinggi", tampilkan juga "Nilai terbaik: Z%".
#### 26.5.3 Detail Ujian (Sebelum Mulai)
**URL:** `/student/exams/<exam_id>/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Daftar Ujian › [Judul Ujian]
**`PageHeader`**
- Title: `exam.title`
- Badge mata pelajaran + badge status
**Two-column layout:**
**`ExamInfoCard`**:
| Label | Nilai |
| Mata Pelajaran | `subject.name` |
| Tanggal Mulai | `start_time\|date:"d M Y H:i"` |
| Tanggal Selesai | `end_time\|date:"d M Y H:i"` |
| Durasi Pengerjaan | `duration_minutes` menit |
| Jumlah Soal | `question_count` soal |
| Nilai Kelulusan | `passing_score`% |
| Layar Penuh | Ya / Tidak |
**`InstructionsCard`**:
- Header: "Instruksi Ujian"
- Teks instruksi dari guru (render HTML)
**`RulesCard`**:
- Header: "Peraturan & Ketentuan"
- List peraturan umum:
 - Ujian berlangsung selama `duration_minutes` menit
 - Jika meninggalkan ujian, waktu tetap berjalan
 - Pelanggaran akan dicatat dan dilaporkan ke guru
 - Jika `require_fullscreen`: "Ujian harus dilakukan dalam mode layar penuh"
 - Jika `detect_tab_switch`: "Perpindahan tab akan terdeteksi dan dicatat sebagai pelanggaran"
 - Jika `enable_screenshot_proctoring`: "Layar Anda akan ditangkap secara berkala"
 - Maks. `max_violations_allowed` pelanggaran — ujian akan dikumpulkan otomatis
**Tombol:**
- "Mulai Ujian Sekarang" → trigger modal konfirmasi
- "Kembali" → `attempts:exam_list`
**`StartConfirmModal`**:
- Title: "Konfirmasi Mulai Ujian"
- Teks: "Setelah ujian dimulai, timer tidak dapat dihentikan. Pastikan Anda siap."
- Tombol: "Ya, Mulai Sekarang" → POST `attempts:exam_room exam_id` | "Batal"
#### 26.5.4 Ruang Ujian
**URL:** `/student/exams/<exam_id>/attempt/`
**Layout:** `layouts/base_exam.html` (full screen, tanpa sidebar/topbar)
**Akses:** Role `student` saat ujian berlangsung
**Fitur:**
- Mode layar penuh (dipaksakan)
- Timer hitung mundur
- Auto-save setiap 15 detik
- Navigasi soal berdasarkan pengaturan
- Tandai untuk review
- Kirim jawaban dengan konfirmasi
- Deteksi perpindahan tab & keluar layar penuh
- Tangkap layar berkala (jika aktif)
- Auto-submit saat waktu habis atau pelanggaran maks.
**`ExamHeader`** (fixed, `exam-header`):
- Kiri: Judul ujian + badge mata pelajaran
- Tengah: Timer countdown
- Kanan: Badge nama siswa
**Layout konten:** Layout dua panel (area soal + sidebar navigator)
**`QuestionArea`**:
**`QuestionHeader`**:
- "Soal {{ currentQuestion + 1 }} dari {{ questions.length }}"
- Badge tipe soal
**`QuestionContent`**:
- Teks soal: (render TinyMCE HTML)
- Gambar soal (jika ada): `<img>` responsive
**`AnswerOptions`** *(jika tipe = Pilihan Ganda)*:
Setiap opsi:
| Elemen | Detail |
| Huruf | A / B / C / D / E (badge kecil) |
| Teks pilihan | Full width |
| Interaksi | Klik untuk memilih jawaban |
| State | Normal / Terpilih (biru) |
**`EssayArea`** *(jika tipe = Essay)*:
- Textarea besar untuk jawaban isian panjang
- Counter kata real-time (Alpine.js)
**`ShortAnswerInput`** *(jika tipe = Isian Singkat)*:
- Input teks untuk jawaban isian singkat
**`NavigationButtons`** (bawah area soal):
- "← Sebelumnya" (sembunyikan jika tidak boleh)
- "Tandai Review" — toggle `markedForReview`
- "Lanjut →" (sembunyikan jika tidak boleh)
**`RestrictedNavigationInfo`** (toast/banner, muncul jika navigasi dikunci):
- Contoh: "Mode berurutan: Jawab soal ini untuk melanjutkan"
**`AutoSaveIndicator`**:
- "Terakhir disimpan: X menit yang lalu" (update setelah save berhasil)
**`QuestionNavigator`**:
**`QuestionProgress`**:
- Teks: "{{ answeredCount }} / {{ questions.length }} soal terjawab"
- Bootstrap progress bar: `(answeredCount / questions.length) * 100`%
**`QuestionNavGrid`** :
- Loop semua soal - Classes kondisional:
 - — sudah dijawab (biru)
 - — ditandai review (kuning)
 - — soal aktif (outline biru)
 - Normal — belum dijawab
 - — terkunci (jika sequential mode, abu)
- Klik navigasi (jika diizinkan):
**`StatusLegend`**:
| Warna | Label |
| Biru (filled) | Sudah dijawab |
| Kuning (filled) | Ditandai review |
| Putih | Belum dijawab |
| Abu (disabled) | Terkunci |
**`SubmitButton`**:
- "Selesai & Kumpulkan"
**`SubmitModal`** (Bootstrap modal):
- Title: "Konfirmasi Pengumpulan"
- Tabel ringkasan:
| Label | Nilai |
| Total Soal | `questions.length` |
| Sudah Dijawab | `answeredCount` |
| Belum Dijawab | `unansweredCount` |
| Ditandai Review | `markedCount` |
- Tombol: "Kembali ke Ujian" | "Ya, Kumpulkan Sekarang" → POST submit
**`ViolationWarningModal`** (muncul otomatis saat pelanggaran terdeteksi):
- Title: "Peringatan!"
- Teks: "Perpindahan tab terdeteksi. Pelanggaran ke-X dari maks. Y. Harap kembali ke ujian."
- Counter pelanggaran: merah
- Tombol: "Kembali ke Ujian"
**Pemantauan Latar Belakang (tidak terlihat):**
- `document.addEventListener('visibilitychange')` → catat perpindahan tab
- `document.addEventListener('fullscreenchange')` → catat keluar layar penuh
- `setInterval(saveCurrentAnswer, 15000)` → auto-save
- `setInterval(captureScreenshot, screenshot_interval_seconds * 1000)` → tangkap layar (jika aktif)
#### 26.5.5 Hasil Ujian — Daftar (Siswa)
**URL:** `/student/results/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Hasil Ujian
**Akses:** Role `student`
**`PageHeader`**
- Title: "Hasil Ujian Saya"
- Subtitle: "Riwayat lengkap ujian yang telah dikerjakan"
**`FilterForm`** (GET):
| Elemen | Keterangan |
| Filter Mata Pelajaran | Dropdown |
| Filter Status | Semua / Lulus / Tidak Lulus |
| Rentang Tanggal | `date_from` + `date_to` |
**`StudentResultTable`**:
| Kolom | Isi |
| Ujian | `exam.title` |
| Mata Pelajaran | `exam.subject.name` |
| Tanggal Dikerjakan | `attempt.submit_time\|date:"d M Y"` |
| Nilai (Final) | `final_percentage`% — sesuai `scoring_method` ujian |
| Percobaan | `attempts_used` / `max_attempts` (tampil hanya jika `max_attempts > 1`) |
| Status | "Lulus" / "Tidak Lulus" |
| Peringkat | `rank` atau "-" |
| Aksi | "Lihat Detail" |
**Paginasi:** 20 per halaman
**Empty state:** Ikon + "Belum ada ujian yang diselesaikan." + tombol "Lihat Daftar Ujian"
#### 26.5.6 Detail Hasil Ujian (Siswa)
**URL:** `/student/results/<result_id>/`
**Layout:** `layouts/base_dashboard.html`
**Breadcrumb:** Beranda › Hasil Ujian › [Judul Ujian]
**`PageHeader`**
- Title: `exam.title`
- Subtitle: `exam.subject.name` · `attempt.submit_time\|date:"d M Y H:i"`
**`MainScoreCard`** (centered):
- Nilai persentase kelulusan (angka besar prominan)
- Badge besar: "LULUS" / "TIDAK LULUS"
- Sub-info: Total Poin: `total_score` / `max_score` | Peringkat: `rank` | Waktu: `time_spent` menit
**`AnswerStats`** (baris 3 mini-kartu):
| Kartu | Ikon | Nilai | Label |
| Benar | ikon | `correct_count` soal | "Jawaban Benar" |
| Salah | ikon | `wrong_count` soal | "Jawaban Salah" |
| Tidak Dijawab | ikon | `unanswered_count` soal | "Tidak Dijawab" |
**`AnswerReview`** *(hanya jika `exam.allow_review = True`)*:
Header: "Review Jawaban"
Per soal, satu kartu:
- Header kartu: "Soal {{ no }}" + badge tipe + badge poin diperoleh
- Teks soal (render HTML)
- Gambar soal (jika ada)
**Untuk Pilihan Ganda:**
- List semua opsi dengan highlight:
 - Pilihan siswa + salah → border `danger`, ikon ✗
 - Pilihan benar → border `success`, ikon ✓
 - Pilihan siswa + benar → border `success`, ikon ✓
**Untuk Essay:**
- Jawaban siswa (dalam kotak abu)
- Nilai yang diberikan guru + komentar guru
**Untuk Isian Singkat:**
- Jawaban siswa + jawaban benar (jika salah)
**Pembahasan:** `<details>` Bootstrap collapse — "Lihat Pembahasan" → isi teks pembahasan
**Jika `allow_review = False`:**
- Info box: "Guru tidak mengizinkan review jawaban untuk ujian ini."
**`AttemptHistoryCard`** *(hanya tampil jika `exam.max_attempts > 1`)*:
- Header: "Riwayat Percobaan"
- Tabel semua attempt milik siswa untuk ujian ini:
| Percobaan Ke- | Tanggal | Nilai | Status Lulus | Waktu Pengerjaan | Aksi |
| 1 | `submit_time` | `percentage`% | Lulus / Tidak | `time_spent` mnt | "Lihat Detail" |
| 2 | ... | ... | ... | ... | "Lihat Detail" |
- Baris aktif (attempt yang sedang dilihat) di-highlight
- Info footer: "Nilai final Anda: **Z%** (berdasarkan metode: Nilai Tertinggi / Percobaan Terakhir)"
**Tombol bawah halaman:**
- "Kembali ke Daftar Hasil"
- "Coba Lagi" (primary, muncul jika `attempts_used < max_attempts` dan waktu ujian masih berlaku)
### 27. Komponen Global (Bersama)
**`Topbar`** (`partials/topbar.html`)
- Tombol toggle sidebar (desktop: lipat/buka, mobile: hamburger)
- Breadcrumb (desktop saja)
- Notifikasi dropdown (lonceng, badge unread, 5 notif terbaru, link "Lihat Semua")
- Menu pengguna → `partials/user_menu.html`
**`Sidebar`** (`partials/sidebar.html`)
- Logo image saja (logo-B-light.png), tanpa teks di sampingnya
- Navigasi berdasarkan role (Admin / Guru / Siswa)
- Indikator aktif per halaman
- Section label (Utama / Manajemen / Konten / Monitoring / Ujian / Sistem)
- Collapse ke ikon saja jika `sidebar-collapsed`
- Mobile: slide-in overlay dari kiri
**`UserMenu`** (`partials/user_menu.html`)
- Avatar bulat + nama + role (dalam `user-menu-toggle`)
- Dropdown: Profil Saya / Ubah Kata Sandi / --- / Keluar (form POST)
**`Breadcrumb`** (`partials/breadcrumb.html`)
- Ikon rumah (link ke `dashboard:home`)
- Loop `breadcrumbs` context variable
**`AlertMessages`** (`partials/alerts.html`)
- Django messages → Bootstrap alert dismissible
- Ikon per jenis: sukses (✓), bahaya (⚠), peringatan (🔔), info (ℹ)
**`ToastNotification`** (`partials/toast.html`)
- Alpine.js `toastManager`
- Auto-dismiss 4 detik
- Support tipe: success, danger, warning, info
- Posisi: pojok kanan bawah
**`DeleteConfirmModal`** (`partials/confirm_modal.html`)
- Title: "Konfirmasi Hapus"
- Ikon peringatan merah di tengah
- Teks: "Apakah Anda yakin ingin menghapus **[nama item]**? Tindakan ini tidak dapat dibatalkan."
- Tombol: "Batal" | "Hapus"
- JS helper: `confirmDelete(title, body, formAction)`
**`Footer`** (`partials/footer.html`)
- Digunakan di halaman landing (publik)
- Satu baris teks hak cipta: © [tahun] CBT Pro. Hak cipta dilindungi.
### 28. Fitur Real-time (WebSocket)
**Channel / Event:**
1. **`exam_monitoring_{exam_id}`** — Student → Teacher
 - Bergabung, progress soal, status, pelanggaran, submit
2. **`notifications_{user_id}`** — Push notifikasi ke semua role
 - Ujian baru, hasil tersedia, pengumuman
3. **`live_stats_{exam_id}`** — Update statistik langsung
 - Jumlah aktif, selesai, persentase progress rata-rata
### 29. Alur Data
**Alur Ujian (Siswa):**
```
Daftar Ujian → Detail Ujian → Konfirmasi Mulai Ruang Ujian (layar penuh) → Jawab Soal (auto-save 15d) → Kumpulkan Hasil Ujian (jika show_results_immediately)
```
**Alur Pemantauan (Guru):**
```
Manajemen Ujian → Terbitkan Ujian Pemantauan Langsung (WebSocket) → Hasil & Analisis
```
**Alur Pembuatan Soal (Guru):**
```
Bank Soal → Tambah Soal Form (tipe + navigasi + pembahasan) → Simpan Detail Soal → Gunakan di Ujian
```
**Alur Manajemen Pengguna (Admin):**
```
Manajemen Pengguna → Tambah Pengguna Isi Form → Set Kata Sandi → Simpan Pengguna dapat login dengan kredensial tersebut
```
### 30. Interaksi Pengguna Utama
**Alur Registrasi Pengguna (Admin Only):**
1. Admin buka Manajemen Pengguna
2. Klik "Tambah Pengguna"
3. Isi informasi lengkap (nama, email, username, role)
4. Set kata sandi manual
5. Simpan → pengguna dapat login
**Alur Kontrol Navigasi (Saat Ujian):**
1. Siswa mulai ujian
2. Sistem periksa pengaturan navigasi per soal
3. Sistem periksa override level ujian
4. Terapkan aturan:
 - Izinkan Kembali = Tidak → tombol "Sebelumnya" disembunyikan
 - Izinkan Lanjut = Tidak → tombol "Lanjut" disembunyikan
 - Paksa Urutan = Ya → soal belum dijawab dikunci
5. Tampilkan pesan informatif jika navigasi dibatasi
6. Update state tombol saat siswa berpindah soal
**Alur Anti-Kecurangan:**
1. Siswa masuk Ruang Ujian
2. Sistem minta mode layar penuh (jika aktif)
3. Pemantauan dimulai: perpindahan tab, keluar layar penuh
4. Tangkap layar berkala (jika aktif)
5. Pelanggaran terdeteksi → modal peringatan + catat ke log
6. Pelanggaran melebihi batas → auto-submit + tandai sebagai curang
**Alur Impor Soal:**
1. Guru klik "Impor Soal" di Bank Soal
2. Unduh template Excel (jika perlu)
3. Unggah file Excel/JSON
4. Sistem validasi format
5. Pratinjau soal yang akan diimpor
6. Konfirmasi impor
7. Toast sukses + redirect ke Bank Soal
### 31. Pertimbangan Responsif
| Breakpoint | Layout |
| Desktop (≥992px) | Sidebar penuh 260px, layout multi-kolom, tabel lengkap |
| Tablet (768–991px) | Sidebar tersembunyi (overlay saat toggle), beberapa kolom distacked |
| Mobile (<768px) | Hamburger buka sidebar overlay, semua single column, tabel horizontal scroll |
### 32. Pertimbangan Keamanan per Halaman
**Ruang Ujian:**
- Proteksi CSRF pada semua POST
- Validasi sesi di setiap navigasi soal
- Token akses ujian berbasis attempt ID
- Browser fingerprinting
- Nonaktifkan klik kanan dan seleksi teks
**Halaman Admin:**
- Dekorator `@admin_required` di semua view
- Pencatatan aksi ke `user_activity_logs`
**Kata Sandi:**
- Hashing PBKDF2 Django (AbstractUser default)
- Panjang minimum 8 karakter
- Kata sandi saat ini wajib sebelum ubah
**Ekspor Data:**
- Rate limiting
- Log akses ekspor
### 33. Prioritas Pengembangan
1. **Fase 1** — Autentikasi (login, logout, model User, profil, ubah kata sandi)
2. **Fase 2** — Template dasar (base.html, layouts, partials)
3. **Fase 3** — Bank Soal CRUD
4. **Fase 4** — Manajemen Ujian (wizard)
5. **Fase 5** — Ruang Ujian & Anti-kecurangan
6. **Fase 6** — Pemantauan & Hasil Analitik
7. **Fase 7** — Real-time (WebSocket, Celery)
8. **Fase 8** — Impor/Ekspor, Proctoring
### 34. Daftar Komponen yang Harus Dibuat
**Autentikasi & Pengguna:**
- [ ] Form Masuk (username/email + kata sandi)
- [ ] Manajemen Sesi & Redirect Berdasarkan Role
- [ ] Halaman Profil (unggah foto, field per role)
- [ ] Halaman Ubah Kata Sandi
**Layout:**
- [ ] `base.html`
- [ ] `layouts/base_dashboard.html` (sidebar + topbar)
- [ ] `layouts/base_exam.html` (layar penuh)
- [ ] `partials/topbar.html` (toggle, breadcrumb, menu pengguna)
- [ ] `partials/sidebar.html` (collapsible, role-aware)
- [ ] `partials/user_menu.html` (avatar, nama, role, dropdown)
- [ ] `partials/alerts.html`
- [ ] `partials/toast.html`
- [ ] `partials/confirm_modal.html`
- [ ] `partials/page_header.html`
- [ ] `partials/footer.html`
- [ ] `partials/breadcrumb.html`
**Dasbor:**
- [ ] `.stat-card` (4 varian warna)
- [ ] Grafik Chart.js (garis, batang, donat)
- [ ] Tabel Aktivitas / Hasil
**Bank Soal:**
- [ ] Tabel daftar soal (dengan filter 4 kolom)
- [ ] Form soal (TinyMCE + opsi dinamis Alpine.js)
- [ ] Komponen Pengaturan Navigasi (3 checkbox)
- [ ] Modal Impor (unggah + pratinjau + konfirmasi)
- [ ] Modal Pratinjau Soal
**Manajemen Ujian:**
- [ ] Wizard 4 langkah (progress bar)
- [ ] Panel cari & pilih soal (AJAX + SortableJS)
- [ ] Panel pengaturan (toggle switch)
- [ ] Panel penugasan (kelas / siswa tertentu)
- [ ] Komponen Override Navigasi Global
**Ruang Ujian:**
- [ ] (4 state: normal, selected, correct, incorrect)
- [ ] dan (4 state)
- [ ] (+ warning + danger + pulse animation)
- [ ] Modal Kumpulkan (ringkasan jawaban)
- [ ] Modal Peringatan Pelanggaran
- [ ] Indikator Auto-save
**Pemantauan:**
- [ ] Panel Statistik Live (4 angka, update WS)
- [ ] Grid Kartu Siswa (update real-time)
- [ ] Feed Pelanggaran (auto-scroll)
**Hasil:**
- [ ] Tabel Hasil Guru (sortable, ekspor)
- [ ] Grafik Distribusi Nilai (histogram)
- [ ] Analisis Item Soal (tabel per soal)
- [ ] Halaman Review Jawaban Siswa (highlight benar/salah)
- [ ] Form Penilaian Essay (AJAX save per soal)## Part VI: Page to Django App Mapping

### 35. Complete Mapping Table

| Page                | URL                                       | Django App    | View Location                  |
|---------------------|-------------------------------------------|---------------|--------------------------------|
| Landing             | `/`                                       | `dashboard`   | `apps/dashboard/views.py`      |
| Login               | `/login/`                                 | `accounts`    | `apps/accounts/views.py`       |
| Logout              | `/logout/`                                | `accounts`    | `apps/accounts/views.py`       |
| Profile             | `/profile/`                               | `accounts`    | `apps/accounts/views.py`       |
| Change Password     | `/change-password/`                       | `accounts`    | `apps/accounts/views.py`       |
| Admin Dashboard     | `/admin/dashboard/`                       | `dashboard`   | `apps/dashboard/views.py`      |
| User Management     | `/admin/users/`                           | `users`       | `apps/users/views.py`          |
| User Create         | `/admin/users/create/`                    | `users`       | `apps/users/views.py`          |
| User Edit           | `/admin/users/<pk>/edit/`                 | `users`       | `apps/users/views.py`          |
| Subject Management  | `/admin/subjects/`                        | `subjects`    | `apps/subjects/views.py`       |
| System Settings     | `/admin/settings/`                        | `core`        | `apps/core/views.py`           |
| Analytics           | `/admin/analytics/`                       | `analytics`   | `apps/analytics/views.py`      |
| Teacher Dashboard   | `/teacher/dashboard/`                     | `dashboard`   | `apps/dashboard/views.py`      |
| Question Bank       | `/teacher/question-bank/`                 | `questions`   | `apps/questions/views.py`      |
| Exam Management     | `/teacher/exams/`                         | `exams`       | `apps/exams/views.py`          |
| Exam Wizard         | `/teacher/exams/create/`                  | `exams`       | `apps/exams/views.py`          |
| Monitoring          | `/teacher/monitoring/<exam_id>/`          | `monitoring`  | `apps/monitoring/views.py`     |
| Results (Teacher)   | `/teacher/results/`                       | `results`     | `apps/results/views.py`        |
| Student Dashboard   | `/student/dashboard/`                     | `dashboard`   | `apps/dashboard/views.py`      |
| Exam List           | `/student/exams/`                         | `attempts`    | `apps/attempts/views.py`       |
| Exam Room           | `/student/exams/<exam_id>/attempt/`       | `attempts`    | `apps/attempts/views.py`       |
| Results (Student)   | `/student/results/`                       | `results`     | `apps/results/views.py`        |

---

### 36. Detailed Mapping by Django App

#### 36.1 apps/core/ — Core Functionality

**Handles:** System Settings, Base utilities, Decorators, Context processors

```
apps/core/
├── __init__.py
├── models.py                # SystemSettings, SystemLog
├── views.py                 # SystemSettingsView (admin only)
├── forms.py                 # SystemSettingsForm
├── urls.py                  # path('admin/settings/', ...)
├── admin.py
├── context_processors.py    # site_settings → available in all templates
├── decorators.py            # @role_required, @admin_required, @teacher_required
├── mixins.py                # AdminRequiredMixin, TeacherRequiredMixin, etc.
└── templates/
    └── core/
        └── settings.html
```

#### 36.2 apps/accounts/ — Authentication + Profile + Change Password

**Handles:** Login, Logout, User model (AbstractUser), UserProfile, Profile page, Change password

```
apps/accounts/
├── __init__.py
├── models.py                # User (AbstractUser + role), UserProfile, UserActivityLog
├── views.py                 # LoginView, LogoutView, ProfileView, ChangePasswordView
├── forms.py                 # LoginForm, ProfileForm, ChangePasswordForm
├── backends.py              # EmailOrUsernameBackend
├── signals.py               # auto-create UserProfile on User creation
├── apps.py                  # imports signals in ready()
├── urls.py                  # login, logout, profile, change-password
├── admin.py
└── templates/
    └── accounts/
        ├── login.html
        ├── profile.html
        └── change_password.html
```

**Key Views:**

```python
# apps/accounts/views.py

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

def login_view(request):
    """Handles email/username + password login with role-based redirect."""

def logout_view(request):
    """Logout and redirect to login."""

@login_required
def profile_view(request):
    """
    GET  → Show profile form pre-filled with User + UserProfile data.
    POST → Update User (first/last name, email) + UserProfile (phone, bio, picture, etc.)
    Template: accounts/profile.html (extends layouts/base_dashboard.html)
    """

@login_required
def change_password_view(request):
    """
    GET  → Show change password form.
    POST → Validate current password, set new password, call update_session_auth_hash()
           so the user stays logged in after password change.
    Template: accounts/change_password.html (extends layouts/base_dashboard.html)
    """
```

#### 36.3 apps/users/ — User Management (Admin only)

**Handles:** User CRUD for Admin — create, edit, list, deactivate, reset password

```
apps/users/
├── __init__.py
├── views.py                 # UserListView, UserCreateView, UserUpdateView, UserDetailView
├── forms.py                 # AdminUserCreateForm, AdminUserUpdateForm, ResetPasswordForm
├── services.py              # create_user_with_profile(), reset_user_password()
├── urls.py                  # admin/users/...
├── admin.py
└── templates/
    └── users/
        ├── list.html
        ├── create.html
        ├── detail.html
        └── edit.html
```

#### 36.4 apps/subjects/ — Subject Management (Admin only)

```
apps/subjects/
├── __init__.py
├── models.py                # Subject
├── views.py
├── forms.py
├── services.py
├── urls.py                  # admin/subjects/...
├── admin.py
└── templates/
    └── subjects/
        ├── list.html
        ├── create.html
        └── edit.html
```

#### 36.5 apps/questions/ — Question Bank (Teacher)

```
apps/questions/
├── __init__.py
├── models.py                # Question, QuestionOption, QuestionAnswer, QuestionTag
├── views.py
├── forms.py
├── services.py
├── importers.py
├── exporters.py
├── urls.py                  # teacher/question-bank/...
├── admin.py
└── templates/
    └── questions/
        ├── list.html
        ├── create.html
        ├── edit.html
        └── detail.html
```

#### 36.6 apps/exams/ — Exam Management (Teacher)

```
apps/exams/
├── __init__.py
├── models.py                # Exam, ExamQuestion, Class, ClassStudent, ExamAssignment
├── views.py
├── forms.py
├── services.py
├── tasks.py                 # auto-publish, auto-complete Celery tasks
├── urls.py                  # teacher/exams/...
├── admin.py
└── templates/
    └── exams/
        ├── list.html
        ├── detail.html
        └── wizard/
            ├── step_info.html
            ├── step_questions.html
            ├── step_settings.html
            └── step_assign.html
```

#### 36.7 apps/attempts/ — Exam Taking (Student)

```
apps/attempts/
├── __init__.py
├── models.py                # ExamAttempt, StudentAnswer, ExamViolation
├── views.py
├── services.py
├── consumers.py             # WebSocket — sends attempt updates to teacher
├── middleware.py            # exam session middleware
├── urls.py                  # student/exams/...
└── templates/
    └── attempts/
        ├── exam_list.html
        ├── exam_detail.html
        └── exam_room.html
```

#### 36.8 apps/monitoring/ — Live Monitoring (Teacher)

```
apps/monitoring/
├── __init__.py
├── views.py
├── consumers.py             # WebSocket consumer — receives attempt updates
├── services.py
├── urls.py                  # teacher/monitoring/...
└── templates/
    └── monitoring/
        └── live.html
```

#### 36.9 apps/results/ — Results & Analytics

```
apps/results/
├── __init__.py
├── models.py                # ExamResult, QuestionStatistics, ExamStatistics
├── views.py
├── services.py
├── tasks.py                 # async result calculation
├── calculators.py
├── exporters.py
├── urls.py                  # teacher/results/ + student/results/
└── templates/
    └── results/
        ├── teacher_list.html
        ├── teacher_detail.html
        ├── student_list.html
        ├── student_detail.html
        └── essay_grading.html
```

#### 36.10 apps/proctoring/ — Screenshot Proctoring

```
apps/proctoring/
├── __init__.py
├── models.py                # ProctoringScreenshot
├── views.py                 # Screenshot upload endpoint (AJAX)
├── services.py
├── tasks.py                 # async screenshot analysis
├── storage.py
└── urls.py
```

#### 36.11 apps/notifications/ — Notifications

```
apps/notifications/
├── __init__.py
├── models.py                # Notification
├── views.py
├── services.py
├── tasks.py
├── consumers.py             # WebSocket — push notifications
├── urls.py
└── templates/
    └── notifications/
        └── list.html
```

#### 36.12 apps/analytics/ — System Analytics (Admin)

```
apps/analytics/
├── __init__.py
├── views.py
├── services.py
├── tasks.py
├── urls.py                  # admin/analytics/
└── templates/
    └── analytics/
        └── dashboard.html
```

#### 36.13 apps/dashboard/ — Dashboards + Landing

```
apps/dashboard/
├── __init__.py
├── views.py                 # LandingView, AdminDashboardView, TeacherDashboardView, StudentDashboardView
├── urls.py                  # / + /admin/dashboard/ + /teacher/dashboard/ + /student/dashboard/
└── templates/
    └── dashboard/
        ├── landing.html
        ├── admin.html
        ├── teacher.html
        └── student.html
```

**Dashboard URL names (used across templates):**

```python
# apps/dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',                      views.landing_view,          name='home'),        # {% url 'dashboard:home' %}
    path('admin/dashboard/',      views.admin_dashboard_view,  name='admin'),
    path('teacher/dashboard/',    views.teacher_dashboard_view, name='teacher'),
    path('student/dashboard/',    views.student_dashboard_view, name='student'),
]
```

---

### 37. URL Routing Flow

```python
# config/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Public & Auth
    path('', include('apps.dashboard.urls')),        # / landing + role dashboards
    path('', include('apps.accounts.urls')),          # /login/ /logout/ /profile/ /change-password/

    # Admin section
    path('', include('apps.users.urls')),             # /admin/users/
    path('', include('apps.subjects.urls')),           # /admin/subjects/
    path('', include('apps.core.urls')),               # /admin/settings/
    path('', include('apps.analytics.urls')),          # /admin/analytics/

    # Teacher section
    path('', include('apps.questions.urls')),          # /teacher/question-bank/
    path('', include('apps.exams.urls')),              # /teacher/exams/
    path('', include('apps.monitoring.urls')),         # /teacher/monitoring/
    path('', include('apps.results.urls')),            # /teacher/results/ + /student/results/

    # Student section
    path('', include('apps.attempts.urls')),           # /student/exams/

    # Shared
    path('', include('apps.notifications.urls')),      # /notifications/
    path('', include('apps.proctoring.urls')),         # /proctoring/ (AJAX endpoint)

    # Django Admin (for superuser only)
    path('django-admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Each app's `urls.py` example:**

```python
# apps/accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',           views.login_view,           name='login'),
    path('logout/',          views.logout_view,           name='logout'),
    path('profile/',         views.profile_view,          name='profile'),
    path('change-password/', views.change_password_view,  name='change_password'),
]
```

---

### 38. Summary Matrix

#### Public (2 pages)

| Page    | App         |
|---------|-------------|
| Landing | `dashboard` |
| Login   | `accounts`  |

#### Shared Auth (2 pages)

| Page            | App        |
|-----------------|------------|
| Profile         | `accounts` |
| Change Password | `accounts` |

#### Admin (5 pages)

| Page             | App         |
|------------------|-------------|
| Dashboard        | `dashboard` |
| User Management  | `users`     |
| Subject Mgmt     | `subjects`  |
| Settings         | `core`      |
| Analytics        | `analytics` |

#### Teacher (5 pages)

| Page             | App          |
|------------------|--------------|
| Dashboard        | `dashboard`  |
| Question Bank    | `questions`  |
| Exam Management  | `exams`      |
| Monitoring       | `monitoring` |
| Results          | `results`    |

#### Student (4 pages)

| Page         | App        |
|--------------|------------|
| Dashboard    | `dashboard`|
| Exam List    | `attempts` |
| Exam Room    | `attempts` |
| Results      | `results`  |

---

### 39. Development Workflow

**Creating a New Page:**

1. Identify the responsible app
2. Create view in `apps/<app>/views.py`
3. Create template extending the correct layout:
   - Dashboard pages → `{% extends 'layouts/base_dashboard.html' %}`
   - Exam room → `{% extends 'layouts/base_exam.html' %}`
4. Add URL in `apps/<app>/urls.py`
5. Include URL in `config/urls.py`
6. Create form (if needed) in `apps/<app>/forms.py`
7. Add business logic in `apps/<app>/services.py`
8. Set `breadcrumbs` context variable in view for topbar breadcrumb partial

**Example: Profile Page**

```python
# apps/accounts/views.py

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import ProfileForm

@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES,
                           instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil berhasil diperbarui.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'breadcrumbs': [{'label': 'Profil'}],
    })
```

```html
{# apps/accounts/templates/accounts/profile.html #}
{% extends 'layouts/base_dashboard.html' %}
{% load static %}

{% block title %}Profil Saya — {{ site_name }}{% endblock %}

{% block page_content %}
<div class="page-header d-flex justify-content-between align-items-center">
    <div>
        <h1 class="page-title">Profil Saya</h1>
        <p class="page-subtitle">Kelola informasi profil Anda</p>
    </div>
</div>

<div class="row g-4">
    <!-- Avatar Card -->
    <div class="col-lg-4">
        <div class="card border-0 shadow-sm h-100">
            <div class="card-body text-center py-4">
                <form method="post" enctype="multipart/form-data" id="avatarForm">
                    {% csrf_token %}
                    <div class="profile-avatar-wrapper mx-auto mb-3">
                        {% if user.profile.profile_picture %}
                            <img id="avatarPreview" src="{{ user.profile.profile_picture.url }}"
                                 class="profile-avatar" alt="Avatar">
                        {% else %}
                            <div id="avatarPreview" class="profile-avatar bg-primary-soft d-flex align-items-center justify-content-center rounded-circle display-6 fw-bold text-primary mx-auto">
                                {{ user.first_name|first|upper }}{{ user.last_name|first|upper }}
                            </div>
                        {% endif %}
                        <label for="id_profile_picture" class="avatar-upload-btn" title="Ganti foto">
                            <i class="ri-camera-line"></i>
                        </label>
                        <input type="file" id="id_profile_picture" name="profile_picture"
                               class="d-none" accept="image/*">
                    </div>
                </form>
                <h5 class="fw-semibold mb-0">{{ user.full_name }}</h5>
                <span class="badge bg-{{ user.role }}-soft mt-1">{{ user.get_role_display }}</span>
                <div class="text-muted small mt-2">{{ user.email }}</div>
            </div>
        </div>
    </div>

    <!-- Profile Form -->
    <div class="col-lg-8">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-transparent border-bottom py-3">
                <h5 class="mb-0 fw-semibold">Informasi Profil</h5>
            </div>
            <div class="card-body p-4">
                <form method="post" enctype="multipart/form-data">
                    {% csrf_token %}
                    <!-- Personal Info -->
                    {% if form.non_field_errors %}
                    <div class="alert alert-danger d-flex align-items-center gap-2" role="alert">
                        <i class="ri-error-warning-fill fs-5 flex-shrink-0"></i>
                        <div>{% for error in form.non_field_errors %}{{ error }}{% endfor %}</div>
                    </div>
                    {% endif %}
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label for="{{ form.first_name.id_for_label }}" class="form-label fw-medium">Nama Depan</label>
                            <input type="text"
                                   id="{{ form.first_name.id_for_label }}"
                                   name="{{ form.first_name.html_name }}"
                                   class="form-control {% if form.first_name.errors %}is-invalid{% endif %}"
                                   value="{{ form.first_name.value|default:'' }}">
                            {% if form.first_name.errors %}
                            <div class="invalid-feedback">{% for e in form.first_name.errors %}{{ e }}{% endfor %}</div>
                            {% endif %}
                        </div>
                        <div class="col-md-6">
                            <label for="{{ form.last_name.id_for_label }}" class="form-label fw-medium">Nama Belakang</label>
                            <input type="text"
                                   id="{{ form.last_name.id_for_label }}"
                                   name="{{ form.last_name.html_name }}"
                                   class="form-control {% if form.last_name.errors %}is-invalid{% endif %}"
                                   value="{{ form.last_name.value|default:'' }}">
                            {% if form.last_name.errors %}
                            <div class="invalid-feedback">{% for e in form.last_name.errors %}{{ e }}{% endfor %}</div>
                            {% endif %}
                        </div>
                        <div class="col-md-6">
                            <label for="{{ form.email.id_for_label }}" class="form-label fw-medium">Email</label>
                            <input type="email"
                                   id="{{ form.email.id_for_label }}"
                                   name="{{ form.email.html_name }}"
                                   class="form-control {% if form.email.errors %}is-invalid{% endif %}"
                                   value="{{ form.email.value|default:'' }}">
                            {% if form.email.errors %}
                            <div class="invalid-feedback">{% for e in form.email.errors %}{{ e }}{% endfor %}</div>
                            {% endif %}
                        </div>
                        <div class="col-md-6">
                            <label for="{{ form.phone_number.id_for_label }}" class="form-label fw-medium">No. Telepon</label>
                            <input type="text"
                                   id="{{ form.phone_number.id_for_label }}"
                                   name="{{ form.phone_number.html_name }}"
                                   class="form-control {% if form.phone_number.errors %}is-invalid{% endif %}"
                                   value="{{ form.phone_number.value|default:'' }}">
                            {% if form.phone_number.errors %}
                            <div class="invalid-feedback">{% for e in form.phone_number.errors %}{{ e }}{% endfor %}</div>
                            {% endif %}
                        </div>
                        {% if user.is_teacher %}
                        <div class="col-md-6">
                            <label class="form-label fw-medium">ID Guru</label>
                            <input type="text" name="teacher_id" class="form-control"
                                   value="{{ user.profile.teacher_id }}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-medium">Spesialisasi Mata Pelajaran</label>
                            <input type="text" name="subject_specialization" class="form-control"
                                   value="{{ user.profile.subject_specialization }}">
                        </div>
                        {% elif user.is_student %}
                        <div class="col-md-6">
                            <label class="form-label fw-medium">NIS / ID Siswa</label>
                            <input type="text" name="student_id" class="form-control"
                                   value="{{ user.profile.student_id }}">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-medium">Kelas</label>
                            <input type="text" name="class_grade" class="form-control"
                                   value="{{ user.profile.class_grade }}">
                        </div>
                        {% endif %}
                        <div class="col-12">
                            <label class="form-label fw-medium">Bio</label>
                            <textarea name="bio" class="form-control" rows="3"
                                      placeholder="Ceritakan sedikit tentang diri Anda...">{{ user.profile.bio }}</textarea>
                        </div>
                    </div>

                    <div class="d-flex gap-2 mt-4">
                        <button type="submit" class="btn btn-primary px-4">
                            <i class="ri-save-line me-1"></i> Simpan Perubahan
                        </button>
                        <a href="{% url 'dashboard:home' %}" class="btn btn-outline-secondary">Batal</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Part VII: Appendices

### 40. Database Views

> Note: These are optional MySQL views for reporting purposes. Django ORM is preferred for application queries.

```sql
-- v_active_exams
CREATE OR REPLACE VIEW v_active_exams AS
SELECT
    e.*,
    CONCAT(u.first_name, ' ', u.last_name) AS creator_name,
    s.name AS subject_name,
    COUNT(DISTINCT eq.question_id) AS question_count
FROM exams e
JOIN auth_user u  ON e.created_by = u.id
JOIN subjects s   ON e.subject_id = s.id
LEFT JOIN exam_questions eq ON e.id = eq.exam_id
WHERE e.status IN ('published', 'ongoing')
GROUP BY e.id, u.first_name, u.last_name, s.name;

-- v_student_exam_results
CREATE OR REPLACE VIEW v_student_exam_results AS
SELECT
    er.*,
    e.title AS exam_title,
    s.name  AS subject_name,
    CONCAT(u.first_name, ' ', u.last_name) AS student_name,
    u.email AS student_email,
    ea.start_time,
    ea.submit_time
FROM exam_results er
JOIN exam_attempts ea ON er.attempt_id = ea.id
JOIN exams e          ON er.exam_id    = e.id
JOIN subjects s       ON e.subject_id  = s.id
JOIN auth_user u      ON er.student_id = u.id;

-- v_question_performance
CREATE OR REPLACE VIEW v_question_performance AS
SELECT
    q.id,
    q.question_text,
    q.question_type,
    q.difficulty_level,
    s.name AS subject_name,
    qs.times_used,
    qs.times_answered,
    qs.times_correct,
    qs.difficulty_index,
    qs.discrimination_index,
    CASE
        WHEN qs.times_answered > 0
        THEN ROUND((qs.times_correct / qs.times_answered * 100), 2)
        ELSE 0
    END AS success_rate
FROM questions q
JOIN subjects s ON q.subject_id = s.id
LEFT JOIN question_statistics qs ON q.id = qs.question_id;
```

---

### 41. Initial Data

**Create default admin via Django management command:**

```bash
python manage.py createsuperuser
# Then set role='admin' via shell or management command:
python manage.py shell
>>> from apps.accounts.models import User
>>> u = User.objects.get(username='admin')
>>> u.role = 'admin'
>>> u.is_staff = True
>>> u.save()
```

**Or use a custom management command `scripts/create_admin.py`:**

```python
# scripts/create_admin.py
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@cbtpro.com',
        password='Admin@123',    # CHANGE IN PRODUCTION
        first_name='System',
        last_name='Administrator',
        role='admin',
    )
    print('Admin user created.')
```

**Sample Subjects fixture (`scripts/initial_data.json`):**

```json
[
  {"model": "subjects.subject", "pk": 1, "fields": {"name": "Matematika",    "code": "MTK", "is_active": true}},
  {"model": "subjects.subject", "pk": 2, "fields": {"name": "Fisika",        "code": "FIS", "is_active": true}},
  {"model": "subjects.subject", "pk": 3, "fields": {"name": "Kimia",         "code": "KIM", "is_active": true}},
  {"model": "subjects.subject", "pk": 4, "fields": {"name": "Biologi",       "code": "BIO", "is_active": true}},
  {"model": "subjects.subject", "pk": 5, "fields": {"name": "Bahasa Inggris","code": "ENG", "is_active": true}},
  {"model": "subjects.subject", "pk": 6, "fields": {"name": "Informatika",   "code": "INF", "is_active": true}}
]
```

---

### 42. Deployment Configuration

**Docker Compose:**

```yaml
# deployment/docker/docker-compose.yml
version: '3.9'
services:
  web:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file: .env
    depends_on:
      - db
      - redis

  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER:     ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: rootpassword
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A config worker --loglevel=info
    env_file: .env
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file: .env
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./deployment/docker/nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/static
      - media_volume:/media
    depends_on:
      - web

volumes:
  mysql_data:
  static_volume:
  media_volume:
```

**Nginx Configuration:**

```nginx
# deployment/docker/nginx.conf
server {
    listen 80;
    server_name _;
    client_max_body_size 50M;

    location /static/ { alias /static/; }
    location /media/  { alias /media/;  }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://web:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

### 43. Testing Strategy

**Pytest Configuration:**

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = --cov=apps --cov-report=html --cov-report=term
# Pastikan .env memiliki: CELERY_TASK_ALWAYS_EAGER=True saat testing
```

**Test Fixtures:**

```python
# tests/conftest.py
import pytest
from apps.accounts.models import User

@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin', email='admin@cbt.com',
        password='admin123', role='admin',
        first_name='System', last_name='Admin',
    )

@pytest.fixture
def teacher_user():
    return User.objects.create_user(
        username='teacher', email='teacher@cbt.com',
        password='teacher123', role='teacher',
        first_name='Budi', last_name='Santoso',
    )

@pytest.fixture
def student_user():
    return User.objects.create_user(
        username='student', email='student@cbt.com',
        password='student123', role='student',
        first_name='Andi', last_name='Wijaya',
    )
```

**Test Categories:**

- **Unit tests**: Models, forms, services, utilities
- **Integration tests**: Exam flow, grading, notifications
- **E2E tests**: Full user journeys (login → profile → exam → results)

---

### 44. Key Implementation Notes

1. **AbstractUser Migration**: Set `AUTH_USER_MODEL = 'accounts.User'` before first `migrate`. If changing later on an existing project, use `django-migrate-user` or recreate migrations carefully.

2. **db_table = 'auth_user'**: Keeps the table name consistent with Django default, avoiding confusion.

3. **Signal Import**: In `apps/accounts/apps.py`:

   ```python
   class AccountsConfig(AppConfig):
       name = 'apps.accounts'
       def ready(self):
           import apps.accounts.signals  # noqa
   ```

4. **MySQL**: Install `mysqlclient` (not `pymysql`) for best Django compatibility. Ensure MySQL server charset is `utf8mb4`.

5. **SCSS Compilation**: Run `npm run build:css` (requires `npm install bootstrap@5.3.8 sass` first). `theme.scss` untuk Bootstrap variable overrides → `theme.css`. `custom.scss` untuk custom classes → `custom.css`. Watch mode: `npm run watch:css`.

6. **Context Processor**: `apps/core/context_processors.py` injects `site_name`, `unread_notifications_count`, and `recent_notifications` into every template context — used by `partials/topbar.html`.

7. **Breadcrumbs**: Pass `breadcrumbs` as a list of `{'label': str, 'url': str}` in every view context. Last item has no `url` (active state).

8. **Button Rule**: Enforce code review policy: only in HTML within `<td class="table-actions">`. All other buttons use default size.

---

### 44.1 context_processors.py

```python
# apps/core/context_processors.py
from .models import SystemSettings

def site_settings(request):
    """
    Inject global variables into every template context.
    Referenced in settings: 'apps.core.context_processors.site_settings'
    """
    ctx = {
        'site_name': 'CBT Pro',
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }

    # Site name from DB settings (cached via Django's cache framework in production)
    try:
        setting = SystemSettings.objects.get(setting_key='site_name')
        ctx['site_name'] = setting.setting_value
    except SystemSettings.DoesNotExist:
        pass

    # Notification count for authenticated users
    if request.user.is_authenticated:
        from apps.notifications.models import Notification
        ctx['unread_notifications_count'] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        ctx['recent_notifications'] = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]

    return ctx
```

---

### 44.2 decorators.py

```python
# apps/core/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*roles):
    """
    Decorator to restrict views to specific user roles.
    Usage: @role_required('admin') or @role_required('teacher', 'admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in roles:
                messages.error(request, 'Anda tidak memiliki izin untuk mengakses halaman ini.')
                return redirect('dashboard:home')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

# Shorthand decorators
def admin_required(view_func):
    return role_required('admin')(view_func)

def teacher_required(view_func):
    return role_required('teacher', 'admin')(view_func)

def student_required(view_func):
    return role_required('student')(view_func)
```

```python
# apps/core/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages

class RoleRequiredMixin(LoginRequiredMixin):
    """CBV mixin to restrict access by role. Set allowed_roles on the view."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in self.allowed_roles:
            messages.error(request, 'Anda tidak memiliki izin untuk mengakses halaman ini.')
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']

class TeacherRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['teacher', 'admin']

class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['student']
```

---

### 44.3 EmailOrUsernameBackend

```python
# apps/accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Allow login with either username or email address.
    Listed first in AUTHENTICATION_BACKENDS so it is tried before the default.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Try username first, then email
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
```

---

### 45. Database Migration Commands

```bash
# Create migrations for all apps
python manage.py makemigrations

# Create migrations for a specific app
python manage.py makemigrations accounts

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial fixture data
python manage.py loaddata initial_data.json

# Backup MySQL database
mysqldump -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} > backup_$(date +%Y%m%d).sql

# Restore MySQL database
mysql -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} < backup.sql

# Show SQL for a migration
python manage.py sqlmigrate accounts 0001

# Check for migration issues
python manage.py migrate --check

# Collect static files (production)
python manage.py collectstatic --noinput

# Compile SCSS
npm run build:css
```