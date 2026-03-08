import uuid
from django.db import models
from apps.core.models import BaseModel, BaseModelSoftDelete
from apps.accounts.models import User
from apps.questions.models import Question
from apps.subjects.models import Subject


class Exam(BaseModelSoftDelete):
    """Exam/ujian"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    RETAKE_SCORE_POLICY_CHOICES = [
        ("highest", "Highest"),
        ("latest", "Latest"),
        ("average", "Average"),
    ]
    
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='exams')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)
    
    # Time Settings
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField()
    
    # Exam Settings
    passing_score = models.DecimalField(max_digits=5, decimal_places=2)
    total_points = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    randomize_questions = models.BooleanField(default=False)
    randomize_options = models.BooleanField(default=False)
    show_results_immediately = models.BooleanField(default=False)
    allow_review = models.BooleanField(default=True)

    # Retake Settings
    allow_retake = models.BooleanField(default=False)
    max_retake_attempts = models.IntegerField(default=1)
    retake_score_policy = models.CharField(
        max_length=20,
        choices=RETAKE_SCORE_POLICY_CHOICES,
        default="highest",
    )
    retake_cooldown_minutes = models.IntegerField(default=0)
    retake_show_review = models.BooleanField(default=False)
    
    # Navigation Override Settings
    override_question_navigation = models.BooleanField(default=False)
    global_allow_previous = models.BooleanField(default=True)
    global_allow_next = models.BooleanField(default=True)
    global_force_sequential = models.BooleanField(default=False)
    
    # Anti-cheat Settings
    require_fullscreen = models.BooleanField(default=True)
    detect_tab_switch = models.BooleanField(default=True)
    enable_screenshot_proctoring = models.BooleanField(default=False)
    screenshot_interval_seconds = models.IntegerField(default=300)
    max_violations_allowed = models.IntegerField(default=3)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    class Meta:
        db_table = 'exams'
        indexes = [
            models.Index(fields=['created_by'], name='idx_exams_created_by'),
            models.Index(fields=['subject'], name='idx_exams_subject_id'),
            models.Index(fields=['status'], condition=models.Q(is_deleted=False), name='idx_exams_status'),
            models.Index(fields=['start_time'], name='idx_exams_start_time'),
            models.Index(fields=['end_time'], name='idx_exams_end_time'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_retake_attempts__gte=1, max_retake_attempts__lte=10),
                name="exam_max_retake_attempts_range",
            ),
            models.CheckConstraint(
                condition=models.Q(retake_cooldown_minutes__gte=0),
                name="exam_retake_cooldown_non_negative",
            ),
        ]
    
    def __str__(self):
        return self.title


class ExamQuestion(BaseModel):
    """Junction table linking exams to questions with custom settings"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='exam_questions')
    display_order = models.IntegerField()
    points_override = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Navigation override per question in this exam
    override_navigation = models.BooleanField(default=False)
    allow_previous_override = models.BooleanField(null=True, blank=True)
    allow_next_override = models.BooleanField(null=True, blank=True)
    force_sequential_override = models.BooleanField(null=True, blank=True)
    
    class Meta:
        db_table = 'exam_questions'
        unique_together = [
            ('exam', 'question'),
            ('exam', 'display_order'),
        ]
        indexes = [
            models.Index(fields=['exam'], name='idx_exam_questions_exam_id'),
            models.Index(fields=['question'], name='idx_exam_questions_question_id'),
            models.Index(fields=['exam', 'display_order'], name='idx_exam_questions_order'),
        ]
    
    def __str__(self):
        return f"{self.exam.title} - Q{self.display_order}"


class Class(BaseModel):
    """Classes for student grouping"""
    name = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=50, null=True, blank=True)
    academic_year = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'classes'
        verbose_name_plural = 'classes'
        indexes = [
            models.Index(fields=['name'], condition=models.Q(is_active=True), name='idx_classes_name'),
        ]
    
    def __str__(self):
        return self.name


class ClassStudent(models.Model):
    """Many-to-many relation between classes and students"""
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='students')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classes')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'class_students'
        unique_together = [('class_obj', 'student')]
        indexes = [
            models.Index(fields=['student'], name='idx_class_students_student_id'),
        ]
    
    def __str__(self):
        return f"{self.class_obj.name} - {self.student.username}"


class ExamAssignment(BaseModel):
    """Exam assignments to classes or students"""
    
    ASSIGNMENT_TYPE_CHOICES = [
        ('class', 'Class'),
        ('student', 'Student'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='assignments')
    assigned_to_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True, related_name='exam_assignments')
    student = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='exam_assignments')
    
    class Meta:
        db_table = 'exam_assignments'
        indexes = [
            models.Index(fields=['exam'], name='idx_exam_assignments_exam_id'),
            models.Index(fields=['class_obj'], name='idx_exam_assignments_class_id'),
            models.Index(fields=['student'], name='idx_exam_assign_stud_id'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(assigned_to_type='class', class_obj__isnull=False, student__isnull=True) |
                    models.Q(assigned_to_type='student', student__isnull=False, class_obj__isnull=True)
                ),
                name='valid_assignment_type'
            ),
        ]
    
    def __str__(self):
        if self.assigned_to_type == 'class':
            return f"{self.exam.title} - {self.class_obj.name}"
        return f"{self.exam.title} - {self.student.username}"
