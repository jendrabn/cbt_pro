import uuid
from django.db import models
from apps.core.models import BaseModel, BaseModelSoftDelete
from apps.accounts.models import User
from apps.subjects.models import Subject


class QuestionCategory(BaseModel):
    """Question categories with hierarchy support"""
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'question_categories'
        indexes = [
            models.Index(fields=['name'], name='idx_question_categories_name'),
            models.Index(fields=['parent'], name='idx_qcat_parent_id'),
        ]
    
    def __str__(self):
        return self.name


class Question(BaseModelSoftDelete):
    """Question bank"""
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('essay', 'Essay'),
        ('short_answer', 'Short Answer'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='questions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    question_text = models.TextField()
    question_image_url = models.URLField(max_length=500, null=True, blank=True)
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)
    
    # Navigation Settings
    allow_previous = models.BooleanField(default=True)
    allow_next = models.BooleanField(default=True)
    force_sequential = models.BooleanField(default=False)
    time_limit_seconds = models.IntegerField(null=True, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'questions'
        indexes = [
            models.Index(fields=['created_by'], name='idx_questions_created_by'),
            models.Index(fields=['subject'], name='idx_questions_subject_id'),
            models.Index(fields=['category'], name='idx_questions_category_id'),
            models.Index(fields=['question_type'], condition=models.Q(is_deleted=False), name='idx_questions_type'),
            models.Index(fields=['difficulty_level'], condition=models.Q(is_deleted=False), name='idx_questions_difficulty'),
        ]
    
    def __str__(self):
        return f"{self.question_text[:50]}... ({self.question_type})"


class QuestionOption(BaseModel):
    """Options for multiple choice questions"""
    
    OPTION_LETTERS = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
    ]
    
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_letter = models.CharField(max_length=1, choices=OPTION_LETTERS)
    option_text = models.TextField()
    option_image_url = models.URLField(max_length=500, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    display_order = models.IntegerField()
    
    class Meta:
        db_table = 'question_options'
        unique_together = [('question', 'option_letter')]
        indexes = [
            models.Index(fields=['question'], name='idx_qopt_question_id'),
        ]
    
    def __str__(self):
        return f"{self.question.id} - Option {self.option_letter}"


class QuestionAnswer(BaseModel):
    """Correct answers for essay and short answer questions"""
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='correct_answer')
    answer_text = models.TextField()
    # Menggunakan JSONField untuk menyimpan array keywords (agnostic untuk MySQL dan PostgreSQL)
    keywords = models.JSONField(default=list, blank=True, help_text="List of keywords for auto-grading")
    is_case_sensitive = models.BooleanField(default=False)
    max_word_count = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'question_answers'
        indexes = [
            models.Index(fields=['question'], name='idx_qans_question_id'),
        ]
    
    def __str__(self):
        return f"Answer for {self.question.id}"


class QuestionTag(BaseModel):
    """Tags for organizing questions"""
    name = models.CharField(max_length=50, unique=True)
    
    class Meta:
        db_table = 'question_tags'
    
    def __str__(self):
        return self.name


class QuestionTagRelation(models.Model):
    """Many-to-many relation between questions and tags"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    tag = models.ForeignKey(QuestionTag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'question_tag_relations'
        unique_together = [('question', 'tag')]
    
    def __str__(self):
        return f"{self.question.id} - {self.tag.name}"


class QuestionImportLog(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    imported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="question_import_logs")
    original_filename = models.CharField(max_length=255)
    file_size_kb = models.IntegerField()
    total_rows = models.IntegerField(default=0)
    total_created = models.IntegerField(default=0)
    total_skipped = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_details = models.JSONField(null=True, blank=True, default=list)
    skip_details = models.JSONField(null=True, blank=True, default=list)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "question_import_logs"
        indexes = [
            models.Index(fields=["imported_by"], name="idx_qil_imported_by"),
            models.Index(fields=["status"], name="idx_qil_status"),
            models.Index(fields=["-created_at"], name="idx_qil_created_at"),
        ]

    def __str__(self):
        return f"Question import {self.original_filename} by {self.imported_by.username} - {self.status}"
