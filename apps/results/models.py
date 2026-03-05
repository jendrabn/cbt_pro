import uuid
from decimal import Decimal
from django.db import models
from apps.core.models import BaseModel
from apps.accounts.models import User
from apps.exams.models import Exam
from apps.questions.models import Question, QuestionOption
from apps.attempts.models import ExamAttempt


class ExamResult(BaseModel):
    """Denormalized exam results for quick access"""
    attempt = models.OneToOneField(ExamAttempt, on_delete=models.CASCADE, related_name='result')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='exam_results')
    
    # Scores
    total_score = models.DecimalField(max_digits=7, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=5, null=True, blank=True)
    passed = models.BooleanField()
    
    # Statistics
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    unanswered = models.IntegerField(default=0)
    
    # Rankings (updated periodically)
    rank_in_exam = models.IntegerField(null=True, blank=True)
    percentile = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Time
    time_taken_seconds = models.IntegerField()
    time_efficiency = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Violations
    total_violations = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'exam_results'
        indexes = [
            models.Index(fields=['exam'], name='idx_exam_results_exam_id'),
            models.Index(fields=['student'], name='idx_exam_results_student_id'),
            models.Index(fields=['percentage'], name='idx_exam_results_percentage'),
            models.Index(fields=['exam', 'student', 'total_score'], name='idx_exam_results_student_exam'),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.title}: {self.percentage}%"


class QuestionStatistics(BaseModel):
    """Question performance analytics and item analysis"""
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='statistics')
    
    # Usage Stats
    times_used = models.IntegerField(default=0)
    times_answered = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    times_wrong = models.IntegerField(default=0)
    times_skipped = models.IntegerField(default=0)
    
    # Analysis Metrics
    difficulty_index = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    discrimination_index = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    average_time_seconds = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Last updated
    last_calculated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'question_statistics'
        verbose_name_plural = 'question statistics'
        indexes = [
            models.Index(fields=['question'], name='idx_qstat_question_id'),
        ]
    
    def __str__(self):
        return f"Statistics for {self.question.id}"
    
    @property
    def success_rate(self):
        """Calculate success rate as percentage"""
        if self.times_answered > 0:
            return round((self.times_correct / self.times_answered) * 100, 2)
        return 0


class OptionStatistics(BaseModel):
    """Option statistics for distractor analysis"""
    option = models.OneToOneField(QuestionOption, on_delete=models.CASCADE, related_name='statistics')
    
    # Selection Stats
    times_selected = models.IntegerField(default=0)
    selection_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # By Performance Group
    high_performers_selected = models.IntegerField(default=0)
    low_performers_selected = models.IntegerField(default=0)
    
    last_calculated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'option_statistics'
        verbose_name_plural = 'option statistics'
        indexes = [
            models.Index(fields=['option'], name='idx_optstat_option_id'),
        ]
    
    def __str__(self):
        return f"Statistics for Option {self.option.option_letter}"


class ExamStatistics(BaseModel):
    """Aggregated exam statistics"""
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='statistics')
    
    # Participation
    total_assigned = models.IntegerField(default=0)
    total_started = models.IntegerField(default=0)
    total_completed = models.IntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Retake Statistics
    total_retake_attempts = models.IntegerField(default=0)
    total_unique_students = models.IntegerField(default=0)
    avg_attempts_per_student = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("1.00"))
    
    # Score Statistics
    average_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    median_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    highest_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    lowest_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    standard_deviation = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    
    # Pass Rate
    total_passed = models.IntegerField(default=0)
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Time Statistics
    average_time_seconds = models.IntegerField(null=True, blank=True)
    median_time_seconds = models.IntegerField(null=True, blank=True)
    
    last_calculated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'exam_statistics'
        verbose_name_plural = 'exam statistics'
        indexes = [
            models.Index(fields=['exam'], name='idx_exam_statistics_exam_id'),
        ]
    
    def __str__(self):
        return f"Statistics for {self.exam.title}"


class Certificate(BaseModel):
    """Certificates for exam results"""
    result = models.OneToOneField(ExamResult, on_delete=models.CASCADE, related_name='certificate')
    certificate_number = models.CharField(max_length=100, unique=True)
    certificate_url = models.URLField(max_length=500, null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'certificates'
        indexes = [
            models.Index(fields=['result'], name='idx_certificates_result_id'),
            models.Index(fields=['certificate_number'], name='idx_certificates_number'),
        ]
    
    def __str__(self):
        return f"Certificate {self.certificate_number}"
