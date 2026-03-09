import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
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


class CertificateTemplate(BaseModel):
    """Certificate template configuration."""

    class LayoutPreset(models.TextChoices):
        CLASSIC_FORMAL = "classic_formal", "Classic Formal"
        MODERN_MINIMAL = "modern_minimal", "Modern Minimalist"
        PORTRAIT_ACHIEVEMENT = "portrait_achievement", "Portrait Achievement"

    class LayoutType(models.TextChoices):
        LANDSCAPE = "landscape", "Landscape"
        PORTRAIT = "portrait", "Portrait"

    class PaperSize(models.TextChoices):
        A4 = "A4", "A4"
        LETTER = "letter", "Letter"

    class QrCodeSize(models.TextChoices):
        S = "S", "Small"
        M = "M", "Medium"
        L = "L", "Large"

    template_name = models.CharField(max_length=100)
    layout_preset = models.CharField(
        max_length=30,
        choices=LayoutPreset.choices,
        default=LayoutPreset.CLASSIC_FORMAL,
    )
    layout_type = models.CharField(max_length=20, choices=LayoutType.choices, default=LayoutType.LANDSCAPE)
    paper_size = models.CharField(max_length=10, choices=PaperSize.choices, default=PaperSize.A4)

    background_image_url = models.CharField(max_length=500, null=True, blank=True)
    primary_color = models.CharField(max_length=7, default="#1A56DB")
    secondary_color = models.CharField(max_length=7, default="#0E9F6E")

    show_logo = models.BooleanField(default=True)
    show_score = models.BooleanField(default=True)
    show_grade = models.BooleanField(default=True)
    show_rank = models.BooleanField(default=False)
    show_qr_code = models.BooleanField(default=True)
    qr_code_size = models.CharField(max_length=5, choices=QrCodeSize.choices, default=QrCodeSize.M)

    header_text = models.TextField(null=True, blank=True)
    body_text_template = models.TextField(null=True, blank=True)
    footer_text = models.TextField(null=True, blank=True)

    signatory_name = models.CharField(max_length=200, null=True, blank=True)
    signatory_title = models.CharField(max_length=200, null=True, blank=True)
    signatory_signature_url = models.CharField(max_length=500, null=True, blank=True)

    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="certificate_templates")

    class Meta:
        db_table = "certificate_templates"
        indexes = [
            models.Index(fields=["created_by"], name="idx_cert_templates_creator"),
            models.Index(fields=["is_default"], name="idx_cert_templates_default"),
        ]

    def __str__(self):
        return self.template_name

    def save(self, *args, **kwargs):
        # Keep orientation in sync with selected built-in preset.
        if self.layout_preset == self.LayoutPreset.PORTRAIT_ACHIEVEMENT:
            self.layout_type = self.LayoutType.PORTRAIT
        elif self.layout_type == self.LayoutType.PORTRAIT:
            self.layout_preset = self.LayoutPreset.PORTRAIT_ACHIEVEMENT
        super().save(*args, **kwargs)


class Certificate(BaseModel):
    """Certificates issued for final exam result policy output."""

    # Legacy relation is kept for backward compatibility with existing views/tests.
    result = models.OneToOneField(
        ExamResult,
        on_delete=models.CASCADE,
        related_name="certificate",
        null=True,
        blank=True,
    )

    attempt = models.OneToOneField(
        ExamAttempt,
        on_delete=models.RESTRICT,
        related_name="certificate_record",
        null=True,
        blank=True,
    )
    exam = models.ForeignKey(Exam, on_delete=models.RESTRICT, related_name="certificates", null=True, blank=True)
    student = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="certificates", null=True, blank=True)

    certificate_number = models.CharField(max_length=50, unique=True)
    verification_token = models.CharField(max_length=100, unique=True, null=True, blank=True)

    issued_at = models.DateTimeField(default=timezone.now)
    is_valid = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_certificates",
    )
    revoked_reason = models.TextField(null=True, blank=True)

    final_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    final_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    template_snapshot = models.JSONField(default=dict, blank=True)

    pdf_file_path = models.CharField(max_length=500, null=True, blank=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)

    # Legacy field used by old student download flow.
    certificate_url = models.URLField(max_length=500, null=True, blank=True)
    
    class Meta:
        db_table = 'certificates'
        indexes = [
            models.Index(fields=['result'], name='idx_certificates_result_id'),
            models.Index(fields=['attempt'], name='idx_certificates_attempt_id'),
            models.Index(fields=['exam'], name='idx_certificates_exam_id'),
            models.Index(fields=['student'], name='idx_certificates_student_id'),
            models.Index(fields=['certificate_number'], name='idx_certificates_number'),
            models.Index(fields=['verification_token'], name='idx_certificates_token'),
        ]
    
    def __str__(self):
        return f"Certificate {self.certificate_number}"

    @property
    def is_revoked(self):
        return bool(self.revoked_at)

    @property
    def is_active(self):
        return bool(self.is_valid and not self.revoked_at)

    @property
    def is_pdf_ready(self):
        return bool(self.pdf_generated_at and self.pdf_file_path)

    def save(self, *args, **kwargs):
        if self.result_id:
            result_obj = getattr(self, "result", None)
            if result_obj is None:
                result_obj = ExamResult.objects.filter(id=self.result_id).select_related("attempt", "exam", "student").first()
            if result_obj is not None:
                self.attempt_id = self.attempt_id or result_obj.attempt_id
                self.exam_id = self.exam_id or result_obj.exam_id
                self.student_id = self.student_id or result_obj.student_id
        if self.revoked_at and self.is_valid:
            self.is_valid = False
        super().save(*args, **kwargs)
