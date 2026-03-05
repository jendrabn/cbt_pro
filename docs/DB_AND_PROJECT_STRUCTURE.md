# Database DDL & Django Project Structure - Advanced CBT Application

## 📋 Table of Contents

1. [Database Design Overview](#database-design-overview)
2. [PostgreSQL DDL](#postgresql-ddl)
3. [Django Project Structure](#django-project-structure)
4. [Database Relationships Diagram](#database-relationships-diagram)

---

## 🗄️ Database Design Overview

### Design Principles

- **Normalization**: All tables follow 3NF (Third Normal Form)
- **Timestamps**: Every table has `created_at` and `updated_at`
- **Foreign Keys**: Defined after primary key tables
- **Soft Delete**: Important tables have `is_deleted` flag
- **Indexing**: Strategic indexes for performance
- **Constraints**: Proper constraints for data integrity

### Table Categories

1. **Core Tables**: Users, Roles
2. **Question Management**: Questions, Options, Categories
3. **Exam Management**: Exams, Exam Questions, Assignments
4. **Exam Execution**: Exam Attempts, Answers, Violations
5. **Results & Analytics**: Results, Statistics
6. **System**: Settings, Logs, Notifications

---

## 📊 PostgreSQL DDL

```sql
-- ============================================================================
-- ADVANCED CBT APPLICATION - DATABASE SCHEMA
-- PostgreSQL 14+
-- Normalized to 3NF
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. CORE TABLES (Users & Authentication)
-- ============================================================================

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username) WHERE is_deleted = FALSE;
CREATE INDEX idx_users_email ON users(email) WHERE is_deleted = FALSE;
CREATE INDEX idx_users_role ON users(role) WHERE is_deleted = FALSE;

-- User Profiles Table (Role-specific information)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,
    teacher_id VARCHAR(50), -- NIP for teachers
    student_id VARCHAR(50), -- NIS for students
    phone_number VARCHAR(20),
    subject_specialization VARCHAR(100), -- For teachers
    class_grade VARCHAR(50), -- For students
    profile_picture_url VARCHAR(500),
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_student_id ON user_profiles(student_id);
CREATE INDEX idx_user_profiles_teacher_id ON user_profiles(teacher_id);

-- User Activity Logs
CREATE TABLE user_activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX idx_activity_logs_created_at ON user_activity_logs(created_at);

-- User Import Logs Table (v1.3.0 - Import Users from Excel)
CREATE TABLE user_import_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    imported_by UUID NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size_kb INTEGER NOT NULL,
    total_rows INTEGER DEFAULT 0,
    total_created INTEGER DEFAULT 0,
    total_skipped INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_details JSONB DEFAULT '[]'::jsonb,
    skip_details JSONB DEFAULT '[]'::jsonb,
    send_credentials_email BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (imported_by) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_user_import_logs_imported_by ON user_import_logs(imported_by);
CREATE INDEX idx_user_import_logs_status ON user_import_logs(status);
CREATE INDEX idx_user_import_logs_created_at ON user_import_logs(created_at DESC);

COMMENT ON TABLE user_import_logs IS
    'Log for bulk user import from Excel. Records are append-only (no updated_at column). '
    'finished_at is set once when processing completes. '
    'error_details and skip_details stored as JSONB for flexibility.';

-- ============================================================================
-- 2. QUESTION MANAGEMENT TABLES
-- ============================================================================

-- Subjects Table
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(20) UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subjects_name ON subjects(name) WHERE is_active = TRUE;

-- Question Categories Table
CREATE TABLE question_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id UUID, -- For hierarchical categories
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES question_categories(id) ON DELETE SET NULL
);

CREATE INDEX idx_question_categories_name ON question_categories(name);
CREATE INDEX idx_question_categories_parent_id ON question_categories(parent_id);

-- Questions Table
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_by UUID NOT NULL,
    subject_id UUID NOT NULL,
    category_id UUID,
    question_type VARCHAR(20) NOT NULL CHECK (question_type IN ('multiple_choice', 'essay', 'short_answer')),
    question_text TEXT NOT NULL,
    question_image_url VARCHAR(500),
    points DECIMAL(5,2) NOT NULL DEFAULT 1.00,
    difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('easy', 'medium', 'hard')),
    explanation TEXT,
    
    -- Navigation Settings
    allow_previous BOOLEAN DEFAULT TRUE,
    allow_next BOOLEAN DEFAULT TRUE,
    force_sequential BOOLEAN DEFAULT FALSE,
    time_limit_seconds INTEGER, -- Optional time limit per question
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES question_categories(id) ON DELETE SET NULL
);

CREATE INDEX idx_questions_created_by ON questions(created_by);
CREATE INDEX idx_questions_subject_id ON questions(subject_id);
CREATE INDEX idx_questions_category_id ON questions(category_id);
CREATE INDEX idx_questions_type ON questions(question_type) WHERE is_deleted = FALSE;
CREATE INDEX idx_questions_difficulty ON questions(difficulty_level) WHERE is_deleted = FALSE;

-- Question Options Table (for multiple choice)
CREATE TABLE question_options (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL,
    option_letter VARCHAR(1) NOT NULL CHECK (option_letter IN ('A', 'B', 'C', 'D', 'E')),
    option_text TEXT NOT NULL,
    option_image_url VARCHAR(500),
    is_correct BOOLEAN DEFAULT FALSE,
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE (question_id, option_letter)
);

CREATE INDEX idx_question_options_question_id ON question_options(question_id);

-- Question Correct Answers Table (for essay and short answer)
CREATE TABLE question_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL,
    answer_text TEXT NOT NULL,
    keywords TEXT[], -- Array of keywords for auto-grading
    is_case_sensitive BOOLEAN DEFAULT FALSE,
    max_word_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE INDEX idx_question_answers_question_id ON question_answers(question_id);

-- Question Tags Table (for better organization)
CREATE TABLE question_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE question_tag_relations (
    question_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (question_id, tag_id),
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES question_tags(id) ON DELETE CASCADE
);

-- ============================================================================
-- 3. EXAM MANAGEMENT TABLES
-- ============================================================================

-- Exams Table
CREATE TABLE exams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_by UUID NOT NULL,
    subject_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT,
    
    -- Time Settings
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER NOT NULL,
    
    -- Exam Settings
    passing_score DECIMAL(5,2) NOT NULL,
    total_points DECIMAL(7,2) DEFAULT 0,
    randomize_questions BOOLEAN DEFAULT FALSE,
    randomize_options BOOLEAN DEFAULT FALSE,
    show_results_immediately BOOLEAN DEFAULT FALSE,
    allow_review BOOLEAN DEFAULT TRUE,

    -- Retake Settings
    allow_retake BOOLEAN DEFAULT FALSE,
    max_retake_attempts INTEGER DEFAULT 1
        CHECK (max_retake_attempts BETWEEN 1 AND 10),
    -- Semantik: total attempt termasuk ujian pertama (3 = 1 asli + 2 retake)
    retake_score_policy VARCHAR(20) DEFAULT 'highest'
        CHECK (retake_score_policy IN ('highest', 'latest', 'average')),
    retake_cooldown_minutes INTEGER DEFAULT 0
        CHECK (retake_cooldown_minutes >= 0),
    retake_show_review BOOLEAN DEFAULT FALSE,
    
    -- Navigation Override Settings
    override_question_navigation BOOLEAN DEFAULT FALSE,
    global_allow_previous BOOLEAN DEFAULT TRUE,
    global_allow_next BOOLEAN DEFAULT TRUE,
    global_force_sequential BOOLEAN DEFAULT FALSE,
    
    -- Anti-cheat Settings
    require_fullscreen BOOLEAN DEFAULT TRUE,
    detect_tab_switch BOOLEAN DEFAULT TRUE,
    enable_screenshot_proctoring BOOLEAN DEFAULT FALSE,
    screenshot_interval_seconds INTEGER DEFAULT 300,
    max_violations_allowed INTEGER DEFAULT 3,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'ongoing', 'completed', 'cancelled')),
    is_deleted BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE RESTRICT
);

CREATE INDEX idx_exams_created_by ON exams(created_by);
CREATE INDEX idx_exams_subject_id ON exams(subject_id);
CREATE INDEX idx_exams_status ON exams(status) WHERE is_deleted = FALSE;
CREATE INDEX idx_exams_start_time ON exams(start_time);
CREATE INDEX idx_exams_end_time ON exams(end_time);

-- Exam Questions Table (Junction table with ordering)
CREATE TABLE exam_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id UUID NOT NULL,
    question_id UUID NOT NULL,
    display_order INTEGER NOT NULL,
    points_override DECIMAL(5,2), -- Override question's default points
    
    -- Navigation override per question in this exam
    override_navigation BOOLEAN DEFAULT FALSE,
    allow_previous_override BOOLEAN,
    allow_next_override BOOLEAN,
    force_sequential_override BOOLEAN,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE RESTRICT,
    UNIQUE (exam_id, question_id),
    UNIQUE (exam_id, display_order)
);

CREATE INDEX idx_exam_questions_exam_id ON exam_questions(exam_id);
CREATE INDEX idx_exam_questions_question_id ON exam_questions(question_id);
CREATE INDEX idx_exam_questions_order ON exam_questions(exam_id, display_order);

-- Classes Table (for student grouping)
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    grade_level VARCHAR(50),
    academic_year VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_classes_name ON classes(name) WHERE is_active = TRUE;

-- Class Students Table (Many-to-Many)
CREATE TABLE class_students (
    class_id UUID NOT NULL,
    student_id UUID NOT NULL,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (class_id, student_id),
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_class_students_student_id ON class_students(student_id);

-- Exam Assignments Table
CREATE TABLE exam_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id UUID NOT NULL,
    assigned_to_type VARCHAR(20) NOT NULL CHECK (assigned_to_type IN ('class', 'student')),
    class_id UUID,
    student_id UUID,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    
    CHECK (
        (assigned_to_type = 'class' AND class_id IS NOT NULL AND student_id IS NULL) OR
        (assigned_to_type = 'student' AND student_id IS NOT NULL AND class_id IS NULL)
    )
);

CREATE INDEX idx_exam_assignments_exam_id ON exam_assignments(exam_id);
CREATE INDEX idx_exam_assignments_class_id ON exam_assignments(class_id);
CREATE INDEX idx_exam_assignments_student_id ON exam_assignments(student_id);

-- ============================================================================
-- 4. EXAM EXECUTION TABLES
-- ============================================================================

-- Exam Attempts Table
CREATE TABLE exam_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id UUID NOT NULL,
    student_id UUID NOT NULL,
    
    -- Attempt Info
    attempt_number INTEGER DEFAULT 1,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    submit_time TIMESTAMP WITH TIME ZONE,
    retake_available_from TIMESTAMP WITH TIME ZONE,
    -- NULL = retake tidak aktif / sudah attempt terakhir / belum submit
    -- Diisi saat submit: submit_time + retake_cooldown_minutes
    
    -- Status
    status VARCHAR(20) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'submitted', 'auto_submitted', 'grading', 'completed')),
    
    -- Results
    total_score DECIMAL(7,2) DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    passed BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    browser_fingerprint VARCHAR(255),
    time_spent_seconds INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE RESTRICT,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE RESTRICT,
    UNIQUE (exam_id, student_id, attempt_number)
);

-- Index lama (tetap)
CREATE INDEX idx_exam_attempts_exam_id ON exam_attempts(exam_id);
CREATE INDEX idx_exam_attempts_student_id ON exam_attempts(student_id);
CREATE INDEX idx_exam_attempts_status ON exam_attempts(status);
-- Index baru
CREATE INDEX idx_exam_attempts_retake
    ON exam_attempts(exam_id, student_id, attempt_number);

-- Student Answers Table
CREATE TABLE student_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attempt_id UUID NOT NULL,
    question_id UUID NOT NULL,
    
    -- Answer Data
    answer_type VARCHAR(20) NOT NULL CHECK (answer_type IN ('multiple_choice', 'essay', 'short_answer')),
    selected_option_id UUID, -- For multiple choice
    answer_text TEXT, -- For essay and short answer
    
    -- Scoring
    is_correct BOOLEAN,
    points_earned DECIMAL(5,2) DEFAULT 0,
    points_possible DECIMAL(5,2) NOT NULL,
    
    -- Metadata
    is_marked_for_review BOOLEAN DEFAULT FALSE,
    time_spent_seconds INTEGER DEFAULT 0,
    answer_order INTEGER, -- Order in which question was answered
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE RESTRICT,
    FOREIGN KEY (selected_option_id) REFERENCES question_options(id) ON DELETE SET NULL,
    UNIQUE (attempt_id, question_id)
);

CREATE INDEX idx_student_answers_attempt_id ON student_answers(attempt_id);
CREATE INDEX idx_student_answers_question_id ON student_answers(question_id);

-- Essay Grading (Manual grading for essay questions)
CREATE TABLE essay_gradings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    answer_id UUID NOT NULL UNIQUE,
    graded_by UUID NOT NULL,
    points_awarded DECIMAL(5,2) NOT NULL,
    feedback TEXT,
    graded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (answer_id) REFERENCES student_answers(id) ON DELETE CASCADE,
    FOREIGN KEY (graded_by) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_essay_gradings_answer_id ON essay_gradings(answer_id);
CREATE INDEX idx_essay_gradings_graded_by ON essay_gradings(graded_by);

-- Exam Violations Table
CREATE TABLE exam_violations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attempt_id UUID NOT NULL,
    violation_type VARCHAR(50) NOT NULL CHECK (violation_type IN ('tab_switch', 'fullscreen_exit', 'copy_attempt', 'paste_attempt', 'right_click', 'suspicious_activity')),
    description TEXT,
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE
);

CREATE INDEX idx_exam_violations_attempt_id ON exam_violations(attempt_id);
CREATE INDEX idx_exam_violations_detected_at ON exam_violations(detected_at);
CREATE INDEX idx_exam_violations_type ON exam_violations(violation_type);

-- Screenshot Proctoring Table
CREATE TABLE proctoring_screenshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attempt_id UUID NOT NULL,
    screenshot_url VARCHAR(500) NOT NULL,
    capture_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    file_size_kb INTEGER,
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE
);

CREATE INDEX idx_proctoring_screenshots_attempt_id ON proctoring_screenshots(attempt_id);
CREATE INDEX idx_proctoring_screenshots_capture_time ON proctoring_screenshots(capture_time);
CREATE INDEX idx_proctoring_screenshots_flagged ON proctoring_screenshots(is_flagged) WHERE is_flagged = TRUE;

-- ============================================================================
-- 5. RESULTS & ANALYTICS TABLES
-- ============================================================================

-- Exam Results Summary (Denormalized for quick access)
CREATE TABLE exam_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attempt_id UUID NOT NULL UNIQUE,
    exam_id UUID NOT NULL,
    student_id UUID NOT NULL,
    
    -- Scores
    total_score DECIMAL(7,2) NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,
    grade VARCHAR(5),
    passed BOOLEAN NOT NULL,
    
    -- Statistics
    total_questions INTEGER NOT NULL,
    correct_answers INTEGER DEFAULT 0,
    wrong_answers INTEGER DEFAULT 0,
    unanswered INTEGER DEFAULT 0,
    
    -- Rankings (updated periodically)
    rank_in_exam INTEGER,
    percentile DECIMAL(5,2),
    
    -- Time
    time_taken_seconds INTEGER NOT NULL,
    time_efficiency DECIMAL(5,2), -- Percentage of time used
    
    -- Violations
    total_violations INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE RESTRICT,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_exam_results_exam_id ON exam_results(exam_id);
CREATE INDEX idx_exam_results_student_id ON exam_results(student_id);
CREATE INDEX idx_exam_results_percentage ON exam_results(percentage);
CREATE INDEX idx_exam_results_student_exam
    ON exam_results(exam_id, student_id, total_score DESC);
-- Digunakan calculate_final_score() untuk policy 'highest' dan 'latest'

-- Question Statistics (for item analysis)
CREATE TABLE question_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL UNIQUE,
    
    -- Usage Stats
    times_used INTEGER DEFAULT 0,
    times_answered INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    times_wrong INTEGER DEFAULT 0,
    times_skipped INTEGER DEFAULT 0,
    
    -- Analysis Metrics
    difficulty_index DECIMAL(5,4), -- P-value
    discrimination_index DECIMAL(5,4), -- Point-biserial correlation
    average_time_seconds DECIMAL(8,2),
    
    -- Last updated
    last_calculated_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE INDEX idx_question_statistics_question_id ON question_statistics(question_id);

-- Option Statistics (for distractor analysis)
CREATE TABLE option_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    option_id UUID NOT NULL UNIQUE,
    
    -- Selection Stats
    times_selected INTEGER DEFAULT 0,
    selection_percentage DECIMAL(5,2),
    
    -- By Performance Group
    high_performers_selected INTEGER DEFAULT 0,
    low_performers_selected INTEGER DEFAULT 0,
    
    last_calculated_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (option_id) REFERENCES question_options(id) ON DELETE CASCADE
);

CREATE INDEX idx_option_statistics_option_id ON option_statistics(option_id);

-- Exam Statistics (Aggregated)
CREATE TABLE exam_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id UUID NOT NULL UNIQUE,
    
    -- Participation
    total_assigned INTEGER DEFAULT 0,
    total_started INTEGER DEFAULT 0,
    total_completed INTEGER DEFAULT 0,
    -- total_completed = jumlah siswa UNIK yang submit (bukan jumlah attempt)
    completion_rate DECIMAL(5,2),

    -- Retake Statistics
    total_retake_attempts INTEGER DEFAULT 0,
    -- total attempt ke-2, ke-3, dst. di seluruh ujian ini
    total_unique_students INTEGER DEFAULT 0,
    -- siswa unik yang pernah mengikuti ujian ini (termasuk yang retake)
    avg_attempts_per_student DECIMAL(4,2) DEFAULT 1.00,
    
    -- Score Statistics
    -- SEMUA metrik score dihitung dari nilai FINAL per siswa (sesuai retake_score_policy)
    average_score DECIMAL(7,2),
    median_score DECIMAL(7,2),
    highest_score DECIMAL(7,2),
    lowest_score DECIMAL(7,2),
    standard_deviation DECIMAL(7,4),
    
    -- Pass Rate
    -- berdasarkan nilai final per siswa
    total_passed INTEGER DEFAULT 0,
    pass_rate DECIMAL(5,2),
    
    -- Time Statistics
    average_time_seconds INTEGER,
    median_time_seconds INTEGER,
    
    last_calculated_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

CREATE INDEX idx_exam_statistics_exam_id ON exam_statistics(exam_id);

-- ============================================================================
-- 6. SYSTEM TABLES
-- ============================================================================

-- System Settings Table
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(20) NOT NULL CHECK (setting_type IN ('string', 'number', 'boolean', 'json')),
    category VARCHAR(50) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    updated_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_category ON system_settings(category);

-- Consolidation Note:
-- Site Name dan Site Logo lama di Tab General dipindah ke category `branding`
-- dengan key `institution_name` dan `institution_logo_url`.
-- Tab General menyisakan konfigurasi perilaku aplikasi (timezone, language, dst).

-- Notifications Table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('info', 'success', 'warning', 'error', 'announcement')),
    related_entity_type VARCHAR(50), -- 'exam', 'result', 'user', etc.
    related_entity_id UUID,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- System Logs Table
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    log_level VARCHAR(20) NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    logger_name VARCHAR(100),
    message TEXT NOT NULL,
    module VARCHAR(100),
    function_name VARCHAR(100),
    line_number INTEGER,
    exception_info TEXT,
    user_id UUID,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_system_logs_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX idx_system_logs_user_id ON system_logs(user_id);

-- Certificates Table
CREATE TABLE certificates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    result_id UUID NOT NULL UNIQUE,
    certificate_number VARCHAR(100) UNIQUE NOT NULL,
    certificate_url VARCHAR(500),
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason TEXT,
    
    FOREIGN KEY (result_id) REFERENCES exam_results(id) ON DELETE RESTRICT
);

CREATE INDEX idx_certificates_result_id ON certificates(result_id);
CREATE INDEX idx_certificates_number ON certificates(certificate_number);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMP
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subjects_updated_at BEFORE UPDATE ON subjects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_question_categories_updated_at BEFORE UPDATE ON question_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_question_options_updated_at BEFORE UPDATE ON question_options
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_question_answers_updated_at BEFORE UPDATE ON question_answers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exams_updated_at BEFORE UPDATE ON exams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exam_questions_updated_at BEFORE UPDATE ON exam_questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_classes_updated_at BEFORE UPDATE ON classes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exam_attempts_updated_at BEFORE UPDATE ON exam_attempts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_answers_updated_at BEFORE UPDATE ON student_answers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exam_results_updated_at BEFORE UPDATE ON exam_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_question_statistics_updated_at BEFORE UPDATE ON question_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_option_statistics_updated_at BEFORE UPDATE ON option_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exam_statistics_updated_at BEFORE UPDATE ON exam_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Active Exams with Creator Info
CREATE VIEW v_active_exams AS
SELECT 
    e.*,
    u.first_name || ' ' || u.last_name AS creator_name,
    s.name AS subject_name,
    COUNT(DISTINCT eq.question_id) AS question_count
FROM exams e
JOIN users u ON e.created_by = u.id
JOIN subjects s ON e.subject_id = s.id
LEFT JOIN exam_questions eq ON e.id = eq.exam_id
WHERE e.is_deleted = FALSE 
    AND e.status IN ('published', 'ongoing')
GROUP BY e.id, u.first_name, u.last_name, s.name;

-- View: Student Exam Results with Details
CREATE VIEW v_student_exam_results AS
SELECT 
    er.*,
    e.title AS exam_title,
    e.subject_id,
    s.name AS subject_name,
    u.first_name || ' ' || u.last_name AS student_name,
    u.email AS student_email,
    ea.start_time,
    ea.submit_time
FROM exam_results er
JOIN exam_attempts ea ON er.attempt_id = ea.id
JOIN exams e ON er.exam_id = e.id
JOIN subjects s ON e.subject_id = s.id
JOIN users u ON er.student_id = u.id;

-- View: Nilai Final per Siswa per Ujian (retake-aware)
-- Menampilkan satu baris per (exam_id, student_id) berisi nilai final
-- sesuai retake_score_policy ('highest' dan 'latest' ditangani di sini;
-- 'average' tetap dihitung di service layer karena butuh AVG).
CREATE VIEW v_student_final_results AS
SELECT DISTINCT ON (er.exam_id, er.student_id)
    er.id,
    er.attempt_id,
    er.exam_id,
    er.student_id,
    er.total_score,
    er.percentage,
    er.grade,
    er.passed,
    er.total_questions,
    er.correct_answers,
    er.wrong_answers,
    er.unanswered,
    er.rank_in_exam,
    er.percentile,
    er.time_taken_seconds,
    er.total_violations,
    ea.attempt_number,
    ea.start_time,
    ea.submit_time,
    e.title AS exam_title,
    e.subject_id,
    e.retake_score_policy,
    e.allow_retake,
    e.max_retake_attempts,
    s.name AS subject_name,
    u.first_name || ' ' || u.last_name AS student_name,
    u.email AS student_email
FROM exam_results er
JOIN exam_attempts ea ON er.attempt_id = ea.id
JOIN exams e ON er.exam_id = e.id
JOIN subjects s ON e.subject_id = s.id
JOIN users u ON er.student_id = u.id
WHERE ea.status IN ('submitted', 'auto_submitted', 'completed')
ORDER BY
    er.exam_id,
    er.student_id,
    CASE e.retake_score_policy
        WHEN 'highest' THEN er.total_score
        WHEN 'latest' THEN ea.attempt_number::DECIMAL
        ELSE er.total_score -- fallback; 'average' dihitung terpisah
    END DESC NULLS LAST;

COMMENT ON VIEW v_student_final_results IS
    'Satu baris per (exam_id, student_id) — nilai final berdasarkan retake_score_policy. '
    'Policy average tidak akurat via view ini, gunakan calculate_final_score() di service layer.';

-- View: Question Performance Summary
CREATE VIEW v_question_performance AS
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
        THEN ROUND((qs.times_correct::DECIMAL / qs.times_answered * 100), 2)
        ELSE 0 
    END AS success_rate
FROM questions q
JOIN subjects s ON q.subject_id = s.id
LEFT JOIN question_statistics qs ON q.id = qs.question_id
WHERE q.is_deleted = FALSE;

-- ============================================================================
-- INITIAL DATA (Optional - for development)
-- ============================================================================

-- Insert default admin user (password: admin123 - CHANGE IN PRODUCTION!)
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active)
VALUES (
    'admin',
    'admin@cbt.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6O5uGi', -- bcrypt hash of 'admin123'
    'System',
    'Administrator',
    'admin',
    TRUE
);

-- Insert sample subjects
INSERT INTO subjects (name, code, description) VALUES
    ('Mathematics', 'MATH', 'Mathematics and Calculus'),
    ('Physics', 'PHY', 'Physics and Natural Sciences'),
    ('Chemistry', 'CHEM', 'Chemistry and Lab Sciences'),
    ('Biology', 'BIO', 'Biology and Life Sciences'),
    ('English', 'ENG', 'English Language and Literature'),
    ('Computer Science', 'CS', 'Programming and Computer Science');

-- Insert default system settings
-- NOTE:
-- Kolom setting_value bertipe TEXT NOT NULL.
-- Untuk setting string yang belum dikonfigurasi gunakan '' (string kosong), bukan NULL.
INSERT INTO system_settings (setting_key, setting_value, setting_type, category, description, is_public) VALUES
    ('institution_name', '', 'string', 'branding', 'Nama sekolah/lembaga', TRUE),
    ('institution_type', '', 'string', 'branding', 'Jenis lembaga (SMA, SMK, MA, Universitas, dst.)', TRUE),
    ('institution_address', '', 'string', 'branding', 'Alamat lengkap lembaga', FALSE),
    ('institution_phone', '', 'string', 'branding', 'Nomor telepon/WA lembaga', FALSE),
    ('institution_email', '', 'string', 'branding', 'Email resmi lembaga', FALSE),
    ('institution_website', '', 'string', 'branding', 'Website resmi lembaga', TRUE),
    ('institution_logo_url', '', 'string', 'branding', 'Path logo utama (navbar, login, PDF header)', TRUE),
    ('institution_logo_dark_url', '', 'string', 'branding', 'Path logo versi putih/dark (opsional)', TRUE),
    ('institution_favicon_url', '', 'string', 'branding', 'Path favicon browser', TRUE),
    ('login_page_headline', '', 'string', 'branding', 'Heading halaman login', TRUE),
    ('login_page_subheadline', '', 'string', 'branding', 'Tagline/sub-heading halaman login', TRUE),
    ('login_page_background_url', '', 'string', 'branding', 'Path background image halaman login', TRUE),
    ('primary_color', '#0d6efd', 'string', 'branding', 'Warna utama UI (HEX)', TRUE),
    ('landing_page_enabled', 'true', 'boolean', 'general', 'Jika false URL / redirect ke /login/', FALSE),
    ('default_exam_duration', '120', 'number', 'exam_defaults', 'Default exam duration in minutes', FALSE),
    ('default_passing_score', '60', 'number', 'exam_defaults', 'Default passing score percentage', FALSE),
    ('max_login_attempts', '5', 'number', 'security', 'Maximum login attempts before lockout', FALSE),
    ('session_timeout_minutes', '120', 'number', 'security', 'User session timeout in minutes', FALSE);

-- ============================================================================
-- COMMENTS ON TABLES (Documentation)
-- ============================================================================

COMMENT ON TABLE users IS 'Core users table for authentication and authorization';
COMMENT ON TABLE user_profiles IS 'Extended user profile information specific to roles';
COMMENT ON TABLE questions IS 'Question bank with support for multiple question types';
COMMENT ON TABLE exam_questions IS 'Junction table linking exams to questions with custom settings';
COMMENT ON TABLE exams IS
    'Exam definitions. Kolom allow_retake, max_retake_attempts, retake_score_policy, '
    'retake_cooldown_minutes, retake_show_review mengontrol fitur ujian ulang.';
COMMENT ON TABLE exam_attempts IS
    'Student exam attempts. Satu siswa bisa punya beberapa record per exam jika retake aktif. '
    'retake_available_from menyimpan waktu paling awal attempt berikutnya boleh dimulai.';
COMMENT ON TABLE student_answers IS 'Individual answers submitted by students';
COMMENT ON TABLE exam_violations IS 'Anti-cheat violation tracking';
COMMENT ON TABLE proctoring_screenshots IS 'Screenshot proctoring data storage';
COMMENT ON TABLE exam_results IS 'Denormalized exam results for quick access';
COMMENT ON TABLE exam_statistics IS
    'Statistik ujian teragregasi. Score metrics (avg, pass_rate, dll.) dihitung dari '
    'nilai FINAL per siswa sesuai retake_score_policy, bukan dari jumlah raw attempt.';
COMMENT ON TABLE system_settings IS
    'Key-value store untuk konfigurasi sistem. '
    'Category "general": perilaku aplikasi (timezone, language, landing_page_enabled). '
    'Category "branding": identitas dan visual lembaga (logo, warna, teks login). '
    'Category "email": konfigurasi SMTP. '
    'Category "security": kebijakan password dan session. '
    'Nilai string kosong ("") berarti belum dikonfigurasi, gunakan fallback dari settings.py.';
COMMENT ON TABLE question_statistics IS 'Question performance analytics and item analysis';

-- ============================================================================
-- END OF DDL
-- ============================================================================
```

---

## 📁 Django Project Structure

```
cbt_project/
│
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── pytest.ini
├── setup.py
│
├── config/                          # Project configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                  # Base settings
│   │   ├── development.py           # Development settings
│   │   ├── production.py            # Production settings
│   │   └── testing.py               # Test settings
│   ├── urls.py                      # Root URL configuration
│   ├── asgi.py                      # ASGI config for async/websockets
│   └── wsgi.py                      # WSGI config
│
├── apps/                            # Django applications
│   │
│   ├── core/                        # Core functionality
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # Base models, mixins
│   │   ├── managers.py              # Custom model managers
│   │   ├── utils.py                 # Utility functions
│   │   ├── constants.py             # Constants and choices
│   │   ├── exceptions.py            # Custom exceptions
│   │   ├── validators.py            # Custom validators
│   │   └── mixins.py                # Model/View mixins
│   │
│   ├── accounts/                    # User management
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # User, UserProfile
│   │   ├── managers.py              # User managers
│   │   ├── forms.py                 # User forms
│   │   ├── views.py                 # Auth views (login, logout)
│   │   ├── urls.py
│   │   ├── serializers.py           # API serializers
│   │   ├── permissions.py           # Custom permissions
│   │   ├── signals.py               # User signals
│   │   ├── backends.py              # Custom auth backends
│   │   ├── templates/
│   │   │   └── accounts/
│   │   │       ├── login.html
│   │   │       └── profile.html
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── test_authentication.py
│   │   └── migrations/
│   │
│   ├── users/                       # User CRUD (Admin)
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # UserActivityLog
│   │   ├── views.py                 # User CRUD views
│   │   ├── urls.py
│   │   ├── forms.py                 # User create/edit forms
│   │   ├── serializers.py
│   │   ├── services.py              # User business logic
│   │   ├── templates/
│   │   │   └── users/
│   │   │       ├── user_list.html
│   │   │       ├── user_form.html
│   │   │       └── user_detail.html
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── questions/                   # Question Bank
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # Question, QuestionOption, QuestionAnswer
│   │   ├── views.py                 # Question CRUD, import/export
│   │   ├── urls.py
│   │   ├── forms.py                 # Question forms
│   │   ├── serializers.py
│   │   ├── services.py              # Question services
│   │   ├── importers.py             # Excel/JSON importers
│   │   ├── exporters.py             # Excel/JSON exporters
│   │   ├── validators.py            # Question validators
│   │   ├── templates/
│   │   │   └── questions/
│   │   │       ├── question_list.html
│   │   │       ├── question_form.html
│   │   │       ├── question_preview.html
│   │   │       └── question_import.html
│   │   ├── static/
│   │   │   └── questions/
│   │   │       ├── js/
│   │   │       │   ├── question_form.js
│   │   │       │   └── question_preview.js
│   │   │       └── css/
│   │   │           └── questions.css
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── exams/                       # Exam Management
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # Exam, ExamQuestion, ExamAssignment
│   │   ├── views.py                 # Exam CRUD, publish, duplicate
│   │   ├── urls.py
│   │   ├── forms.py                 # Exam wizard forms
│   │   ├── serializers.py
│   │   ├── services.py              # Exam business logic
│   │   ├── tasks.py                 # Celery tasks
│   │   ├── validators.py
│   │   ├── templates/
│   │   │   └── exams/
│   │   │       ├── exam_list.html
│   │   │       ├── exam_form.html
│   │   │       ├── exam_wizard.html
│   │   │       ├── exam_preview.html
│   │   │       └── exam_detail.html
│   │   ├── static/
│   │   │   └── exams/
│   │   │       ├── js/
│   │   │       │   ├── exam_wizard.js
│   │   │       │   └── exam_settings.js
│   │   │       └── css/
│   │   │           └── exams.css
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── attempts/                    # Exam Taking (Student)
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # ExamAttempt, StudentAnswer, ExamViolation
│   │   ├── views.py                 # Exam room, submit
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── services.py              # Attempt logic, auto-submit
│   │   ├── consumers.py             # WebSocket consumers
│   │   ├── middleware.py            # Anti-cheat middleware
│   │   ├── validators.py
│   │   ├── templates/
│   │   │   └── attempts/
│   │   │       ├── exam_start.html
│   │   │       ├── exam_room.html
│   │   │       └── exam_submit_confirmation.html
│   │   ├── static/
│   │   │   └── attempts/
│   │   │       ├── js/
│   │   │       │   ├── exam_room.js
│   │   │       │   ├── anti_cheat.js
│   │   │       │   ├── timer.js
│   │   │       │   └── auto_save.js
│   │   │       └── css/
│   │   │           └── exam_room.css
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── monitoring/                  # Live Monitoring (Teacher)
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── views.py                 # Monitoring dashboard
│   │   ├── urls.py
│   │   ├── consumers.py             # WebSocket for real-time updates
│   │   ├── serializers.py
│   │   ├── services.py              # Monitoring services
│   │   ├── templates/
│   │   │   └── monitoring/
│   │   │       ├── monitoring_dashboard.html
│   │   │       └── student_detail_modal.html
│   │   ├── static/
│   │   │   └── monitoring/
│   │   │       ├── js/
│   │   │       │   ├── monitoring.js
│   │   │       │   └── websocket_handler.js
│   │   │       └── css/
│   │   │           └── monitoring.css
│   │   └── tests/
│   │
│   ├── results/                     # Results & Analytics
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py                # ExamResult, Statistics
│   │   ├── views.py                 # Results views, analytics
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── services.py              # Grading, statistics calculation
│   │   ├── tasks.py                 # Celery tasks for analytics
│   │   ├── calculators.py           # Statistics calculators
│   │   ├── exporters.py             # PDF/Excel export
│   │   ├── templates/
│   │   │   └── results/
│   │   │       ├── results_list.html
│   │   │       ├── result_detail.html
│   │   │       ├── analytics_dashboard.html
│   │   │       └── answer_review.html
│   │   ├── static/
│   │   │   └── results/
│   │   │       ├── js/
│   │   │       │   ├── charts.js
│   │   │       │   └── analytics.js
│   │   │       └── css/
│   │   │           └── results.css
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── proctoring/                  # Screenshot Proctoring
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # ProctoringScreenshot
│   │   ├── views.py                 # Screenshot upload
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── services.py              # Screenshot processing
│   │   ├── tasks.py                 # Celery tasks
│   │   ├── storage.py               # Custom storage backend
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── notifications/               # Notifications
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                # Notification
│   │   ├── views.py                 # Notification views
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── services.py              # Notification service
│   │   ├── tasks.py                 # Email tasks
│   │   ├── consumers.py             # WebSocket for notifications
│   │   ├── templates/
│   │   │   └── notifications/
│   │   │       └── notification_list.html
│   │   ├── tests/
│   │   └── migrations/
│   │
│   ├── analytics/                   # System Analytics (Admin)
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── views.py                 # Analytics dashboards
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── services.py              # Analytics services
│   │   ├── tasks.py                 # Periodic analytics tasks
│   │   ├── templates/
│   │   │   └── analytics/
│   │   │       ├── admin_analytics.html
│   │   │       └── reports.html
│   │   └── tests/
│   │
│   └── dashboard/                   # Dashboards
│       ├── __init__.py
│       ├── apps.py
│       ├── views.py                 # Dashboard views for each role
│       ├── urls.py
│       ├── templates/
│       │   └── dashboard/
│       │       ├── admin_dashboard.html
│       │       ├── teacher_dashboard.html
│       │       └── student_dashboard.html
│       ├── static/
│       │   └── dashboard/
│       │       ├── js/
│       │       │   └── dashboard.js
│       │       └── css/
│       │           └── dashboard.css
│       └── tests/
│
├── templates/                       # Global templates
│   ├── base.html                    # Base template
│   ├── base_admin.html              # Admin base
│   ├── base_teacher.html            # Teacher base
│   ├── base_student.html            # Student base
│   ├── components/                  # Reusable components
│   │   ├── navbar.html
│   │   ├── sidebar.html
│   │   ├── footer.html
│   │   ├── alerts.html
│   │   ├── modals.html
│   │   └── pagination.html
│   ├── errors/
│   │   ├── 400.html
│   │   ├── 403.html
│   │   ├── 404.html
│   │   └── 500.html
│   └── landing.html                 # Landing page
│
├── static/                          # Global static files
│   ├── css/
│   │   ├── main.css                 # Main stylesheet
│   │   ├── components.css           # Component styles
│   │   ├── utilities.css            # Utility classes
│   │   └── themes/
│   │       ├── light.css
│   │       └── dark.css
│   ├── js/
│   │   ├── main.js                  # Main JavaScript
│   │   ├── alpine-init.js           # Alpine.js initialization
│   │   ├── htmx-config.js           # HTMX configuration
│   │   ├── utils.js                 # Utility functions
│   │   └── components/
│   │       ├── modal.js
│   │       ├── toast.js
│   │       └── charts.js
│   ├── images/
│   │   ├── logo.png
│   │   ├── favicon.ico
│   │   └── placeholder.png
│   └── vendor/                      # Third-party libraries
│       ├── alpinejs/
│       ├── htmx/
│       ├── chartjs/
│       └── tinymce/
│
├── media/                           # User uploaded files
│   ├── questions/                   # Question images
│   ├── branding/
│   │   ├── logo/                    # institution_logo_url
│   │   ├── logo_dark/               # institution_logo_dark_url
│   │   ├── favicon/                 # institution_favicon_url
│   │   └── login_bg/                # login_page_background_url
│   ├── screenshots/                 # Proctoring screenshots
│   ├── certificates/                # Generated certificates
│   └── exports/                     # Exported files
│
├── api/                             # REST API (Optional)
│   ├── __init__.py
│   ├── urls.py                      # API URLs
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── permissions.py
│   └── tests/
│
├── websockets/                      # WebSocket routing
│   ├── __init__.py
│   ├── routing.py                   # WebSocket URL routing
│   └── middleware.py                # WebSocket middleware
│
├── celery_app/                      # Celery configuration
│   ├── __init__.py
│   ├── celery.py                    # Celery app
│   └── tasks.py                     # Shared tasks
│
├── utils/                           # Global utilities
│   ├── __init__.py
│   ├── helpers.py                   # Helper functions
│   ├── decorators.py                # Custom decorators
│   ├── email.py                     # Email utilities
│   ├── pdf.py                       # PDF generation
│   ├── excel.py                     # Excel utilities
│   └── encryption.py                # Encryption utilities
│
├── tests/                           # Global tests
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── factories.py                 # Model factories
│   └── integration/
│       ├── test_exam_flow.py
│       └── test_grading.py
│
├── docs/                            # Documentation
│   ├── api/
│   ├── architecture/
│   ├── deployment/
│   └── user_guide/
│
├── scripts/                         # Utility scripts
│   ├── setup_dev.sh                 # Dev environment setup
│   ├── backup_db.sh                 # Database backup
│   ├── restore_db.sh                # Database restore
│   ├── generate_test_data.py        # Test data generator
│   └── calculate_statistics.py     # Statistics calculator
│
└── deployment/                      # Deployment configs
    ├── docker/
    │   ├── Dockerfile
    │   ├── docker-compose.yml
    │   └── nginx.conf
    ├── kubernetes/
    │   ├── deployment.yaml
    │   └── service.yaml
    └── terraform/
        └── main.tf
```

---

### Media Branding Paths

```text
media/
└── branding/
    ├── logo/          # institution_logo_url
    ├── logo_dark/     # institution_logo_dark_url
    ├── favicon/       # institution_favicon_url
    └── login_bg/      # login_page_background_url
```

---

## 📦 requirements.txt

```txt
alabaster==1.0.0
amqp==5.3.1
asgiref==3.11.1
astroid==4.0.4
attrs==25.4.0
autobahn==25.12.2
Automat==25.4.16
babel==2.18.0
bcrypt==5.0.0
billiard==4.2.4
black==26.1.0
brotli==1.2.0
cbor2==5.8.0
celery==5.6.2
certifi==2026.1.4
cffi==2.0.0
channels==4.3.2
channels_redis==4.3.0
charset-normalizer==3.4.4
click==8.3.1
click-didyoumean==0.3.1
click-plugins==1.1.1.2
click-repl==0.3.0
colorama==0.4.6
constantly==23.10.4
coverage==7.13.4
crispy-bootstrap5==2025.6
cron_descriptor==2.0.6
cryptography==46.0.5
cssselect2==0.9.0
daphne==4.2.1
diff-match-patch==20241021
dill==0.4.1
Django==5.2.11
django-allauth==65.14.3
django-celery-beat==2.8.1
django-cors-headers==4.9.0
django-crispy-forms==2.5
django-debug-toolbar==6.2.0
django-environ==0.12.1
django-extensions==4.1
django-import-export==4.4.0
django-model-utils==5.0.0
django-timezone-field==7.2.1
django-tinymce==5.0.0
django_celery_results==2.6.0
djangorestframework==3.16.1
docutils==0.22.4
drf-spectacular==0.29.0
et_xmlfile==2.0.0
factory_boy==3.3.3
Faker==40.4.0
flake8==7.3.0
fonttools==4.61.1
hyperlink==21.0.0
idna==3.11
imagesize==1.4.1
Incremental==24.11.0
inflection==0.5.1
iniconfig==2.3.0
isort==7.0.0
Jinja2==3.1.6
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
kombu==5.6.2
MarkupSafe==3.0.3
mccabe==0.7.0
msgpack==1.1.2
mypy_extensions==1.1.0
numpy==2.4.2
openpyxl==3.1.5
packaging==26.0
pandas==3.0.0
pathspec==1.0.4
pillow==12.1.1
platformdirs==4.8.0
pluggy==1.6.0
prompt_toolkit==3.0.52
psycopg2-binary==2.9.11
py-ubjson==0.16.1
pyasn1==0.6.2
pyasn1_modules==0.4.2
pycodestyle==2.14.0
pycparser==3.0
pydyf==0.12.1
pyflakes==3.4.0
Pygments==2.19.2
PyJWT==2.11.0
pylint==4.0.4
pyOpenSSL==25.3.0
PyPDF2==3.0.1
pyphen==0.17.2
pytest==9.0.2
pytest-cov==7.0.0
pytest-django==4.11.1
python-crontab==3.3.0
python-dateutil==2.9.0.post0
python-magic==0.4.27
pytokens==0.4.1
pytz==2025.2
PyYAML==6.0.3
redis==7.1.1
referencing==0.37.0
reportlab==4.4.10
requests==2.32.5
roman-numerals==4.1.0
rpds-py==0.30.0
scipy==1.17.0
sentry-sdk==2.52.0
service-identity==24.2.0
six==1.17.0
snowballstemmer==3.0.1
Sphinx==9.1.0
sphinx_rtd_theme==3.1.0
sphinxcontrib-applehelp==2.0.0
sphinxcontrib-devhelp==2.0.0
sphinxcontrib-htmlhelp==2.1.0
sphinxcontrib-jquery==4.1
sphinxcontrib-jsmath==1.0.1
sphinxcontrib-qthelp==2.0.0
sphinxcontrib-serializinghtml==2.0.0
sqlparse==0.5.5
tablib==3.9.0
tinycss2==1.5.1
tinyhtml5==2.0.0
tomlkit==0.14.0
Twisted==25.5.0
txaio==25.12.2
typing_extensions==4.15.0
tzdata==2025.3
tzlocal==5.3.1
ujson==5.11.0
uritemplate==4.2.0
urllib3==2.6.3
vine==5.1.0
wcwidth==0.6.0
weasyprint==68.1
webencodings==0.5.1
xlsxwriter==3.2.9
zope.interface==8.2
zopfli==0.4.1

```

---

## 🔧 Django Settings Structure

### config/settings/base.py

```python
# Base settings shared across all environments
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'channels',
    'celery',
    'django_celery_beat',
    'crispy_forms',
    'crispy_bootstrap5',
    'tinymce',
    'import_export',
    
    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.users',
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}

AUTH_USER_MODEL = 'accounts.User'
```

---

## 📝 Database Migration Commands

```bash
# Create initial migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data
python manage.py loaddata initial_data.json

# Backup database
pg_dump -U postgres cbt_db > backup.sql

# Restore database
psql -U postgres cbt_db < backup.sql
```

---

## 🎯 Key Implementation Notes

### 1. **Foreign Key Order**

All foreign key tables are defined after their referenced tables, ensuring proper migration order.

### 2. **3NF Compliance**

- No transitive dependencies
- All non-key attributes depend only on primary key
- Separate junction tables for many-to-many relationships
- Proper normalization of user profiles, questions, and results

### 3. **Timestamps**

- Every table has `created_at` and `updated_at`
- Automatic update triggers for `updated_at`
- Timezone-aware timestamps (`TIMESTAMP WITH TIME ZONE`)

### 4. **Indexing Strategy**

- Foreign keys are indexed
- Frequently queried columns have indexes
- Composite indexes for common query patterns
- Conditional indexes for soft-deleted records

### 5. **Soft Delete**

- Important tables use `is_deleted` flag
- Allows data recovery and audit trails
- Indexes exclude deleted records for performance

### 6. **UUID Primary Keys**

- Better for distributed systems
- No sequential ID exposure
- Easier data migration between databases

---

**This document provides the complete database schema and project structure for the Advanced CBT Application. Ready for implementation!**
