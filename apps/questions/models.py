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

    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Pilihan Ganda"
        CHECKBOX = "checkbox", "Checkbox"
        ORDERING = "ordering", "Ordering"
        MATCHING = "matching", "Matching"
        FILL_IN_BLANK = "fill_in_blank", "Fill In Blank"
        ESSAY = "essay", "Esai"
        SHORT_ANSWER = "short_answer", "Jawaban Singkat"

    class CheckboxScoring(models.TextChoices):
        ALL_OR_NOTHING = "all_or_nothing", "Semua atau Nol"
        PARTIAL = "partial", "Parsial dengan Penalti"
        PARTIAL_NO_PENALTY = "partial_no_penalty", "Parsial tanpa Penalti"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Mudah"
        MEDIUM = "medium", "Sedang"
        HARD = "hard", "Sulit"

    QUESTION_TYPE_CHOICES = QuestionType.choices
    DIFFICULTY_CHOICES = Difficulty.choices
    
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='questions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    category = models.ForeignKey(QuestionCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    question_text = models.TextField()
    question_image_url = models.URLField(max_length=500, null=True, blank=True)
    audio_play_limit = models.PositiveIntegerField(null=True, blank=True)
    video_play_limit = models.PositiveIntegerField(null=True, blank=True)
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)
    checkbox_scoring = models.CharField(
        max_length=32,
        choices=CheckboxScoring.choices,
        default=CheckboxScoring.ALL_OR_NOTHING,
    )
    
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

    class OptionLetter(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"
        E = "E", "E"
        F = "F", "F"
        G = "G", "G"
        H = "H", "H"
        I = "I", "I"
        J = "J", "J"

    OPTION_LETTERS = OptionLetter.choices
    
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


class QuestionOrderingItem(BaseModel):
    """Ordered items for ordering questions"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="ordering_items")
    item_text = models.TextField()
    correct_order = models.PositiveIntegerField()

    class Meta:
        db_table = "question_ordering_items"
        unique_together = [("question", "correct_order")]
        indexes = [
            models.Index(fields=["question"], name="idx_qord_question_id"),
            models.Index(fields=["question", "correct_order"], name="idx_qord_order"),
        ]

    def __str__(self):
        return f"{self.question.id} - Ordering item {self.correct_order}"


class QuestionMatchingPair(BaseModel):
    """Prompt/answer pairs for matching questions"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="matching_pairs")
    prompt_text = models.TextField()
    answer_text = models.TextField()
    pair_order = models.PositiveIntegerField()

    class Meta:
        db_table = "question_matching_pairs"
        unique_together = [("question", "pair_order")]
        indexes = [
            models.Index(fields=["question"], name="idx_qmatch_question_id"),
            models.Index(fields=["question", "pair_order"], name="idx_qmatch_order"),
        ]

    def __str__(self):
        return f"{self.question.id} - Matching pair {self.pair_order}"


class QuestionBlankAnswer(BaseModel):
    """Accepted answers for fill in blank questions"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="blank_answers")
    blank_number = models.PositiveIntegerField()
    accepted_answers = models.JSONField(default=list, blank=True)
    is_case_sensitive = models.BooleanField(default=False)
    blank_points = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "question_blank_answers"
        unique_together = [("question", "blank_number")]
        indexes = [
            models.Index(fields=["question"], name="idx_qblank_question_id"),
            models.Index(fields=["question", "blank_number"], name="idx_qblank_number"),
        ]

    def __str__(self):
        return f"{self.question.id} - Blank {self.blank_number}"


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
    class Status(models.TextChoices):
        PENDING = "pending", "Menunggu"
        PROCESSING = "processing", "Diproses"
        COMPLETED = "completed", "Selesai"
        FAILED = "failed", "Gagal"

    STATUS_CHOICES = Status.choices

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    imported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="question_import_logs")
    original_filename = models.CharField(max_length=255)
    file_size_kb = models.IntegerField()
    total_rows = models.IntegerField(default=0)
    total_created = models.IntegerField(default=0)
    total_skipped = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=Status.PENDING)
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
