import uuid
from django.db import models
from apps.core.models import BaseModel
from apps.accounts.models import User
from apps.exams.models import Exam
from apps.questions.models import Question, QuestionOption


class ExamAttempt(BaseModel):
    """Student exam attempts"""
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('auto_submitted', 'Auto Submitted'),
        ('grading', 'Grading'),
        ('completed', 'Completed'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='exam_attempts')
    
    # Attempt Info
    attempt_number = models.IntegerField(default=1)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    submit_time = models.DateTimeField(null=True, blank=True)
    retake_available_from = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Results
    total_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    browser_fingerprint = models.CharField(max_length=255, null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'exam_attempts'
        unique_together = [('exam', 'student', 'attempt_number')]
        indexes = [
            models.Index(fields=['exam'], name='idx_exam_attempts_exam_id'),
            models.Index(fields=['student'], name='idx_exam_attempts_student_id'),
            models.Index(fields=['status'], name='idx_exam_attempts_status'),
            models.Index(fields=["exam", "student", "attempt_number"], name="idx_exam_attempts_retake"),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.title} (Attempt {self.attempt_number})"


class StudentAnswer(BaseModel):
    """Individual answers submitted by students"""
    
    ANSWER_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('essay', 'Essay'),
        ('short_answer', 'Short Answer'),
    ]
    
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    
    # Answer Data
    answer_type = models.CharField(max_length=20, choices=ANSWER_TYPE_CHOICES)
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_answers')
    answer_text = models.TextField(null=True, blank=True)
    
    # Scoring
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    points_possible = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Metadata
    is_marked_for_review = models.BooleanField(default=False)
    time_spent_seconds = models.IntegerField(default=0)
    answer_order = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'student_answers'
        unique_together = [('attempt', 'question')]
        indexes = [
            models.Index(fields=['attempt'], name='idx_stud_ans_attempt_id'),
            models.Index(fields=['question'], name='idx_stud_ans_question_id'),
        ]
    
    def __str__(self):
        return f"{self.attempt.student.username} - Q{self.question.id}"


class EssayGrading(BaseModel):
    """Manual grading for essay questions"""
    answer = models.OneToOneField(StudentAnswer, on_delete=models.CASCADE, related_name='grading')
    graded_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='essay_gradings')
    points_awarded = models.DecimalField(max_digits=5, decimal_places=2)
    feedback = models.TextField(null=True, blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'essay_gradings'
        indexes = [
            models.Index(fields=['answer'], name='idx_essay_gradings_answer_id'),
            models.Index(fields=['graded_by'], name='idx_essay_gradings_graded_by'),
        ]
    
    def __str__(self):
        return f"Grading for {self.answer.id}"


class ExamViolation(BaseModel):
    """Anti-cheat violation tracking"""
    
    VIOLATION_TYPE_CHOICES = [
        ('tab_switch', 'Tab Switch'),
        ('fullscreen_exit', 'Fullscreen Exit'),
        ('copy_attempt', 'Copy Attempt'),
        ('paste_attempt', 'Paste Attempt'),
        ('right_click', 'Right Click'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='violations')
    violation_type = models.CharField(max_length=50, choices=VIOLATION_TYPE_CHOICES)
    description = models.TextField(null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, null=True, blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exam_violations'
        indexes = [
            models.Index(fields=['attempt'], name='idx_viol_attempt_id'),
            models.Index(fields=['detected_at'], name='idx_viol_detected_at'),
            models.Index(fields=['violation_type'], name='idx_viol_type'),
        ]
    
    def __str__(self):
        return f"{self.attempt.student.username} - {self.violation_type}"


class ProctoringScreenshot(BaseModel):
    """Screenshot proctoring data storage"""
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='screenshots')
    screenshot_url = models.URLField(max_length=500)
    capture_time = models.DateTimeField(auto_now_add=True)
    file_size_kb = models.IntegerField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'proctoring_screenshots'
        indexes = [
            models.Index(fields=['attempt'], name='idx_ss_attempt_id'),
            models.Index(fields=['capture_time'], name='idx_ss_capture_time'),
            models.Index(fields=['is_flagged'], condition=models.Q(is_flagged=True), name='idx_ss_flagged'),
        ]
    
    def __str__(self):
        return f"Screenshot for {self.attempt.student.username} at {self.capture_time}"
