import uuid
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from apps.core.models import BaseModel


class UserManager(DjangoUserManager):
    """Custom user manager with role default for superuser."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        return super().create_superuser(username, email=email, password=password, **extra_fields)


class User(AbstractUser):
    """Custom User model using Django auth_user table."""

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("teacher", "Teacher"),
        ("student", "Student"),
    ]

    email = models.EmailField(max_length=254, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    is_deleted = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    objects = UserManager()

    class Meta:
        db_table = "auth_user"
        indexes = [
            models.Index(fields=["role"], name="idx_auth_user_role"),
            models.Index(fields=["is_active"], name="idx_auth_user_active"),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_teacher(self):
        return self.role == "teacher"

    @property
    def is_student(self):
        return self.role == "student"


class UserProfile(BaseModel):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    teacher_id = models.CharField(max_length=50, null=True, blank=True, help_text="NIP for teachers")
    student_id = models.CharField(max_length=50, null=True, blank=True, help_text="NIS for students")
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    subject_specialization = models.CharField(max_length=100, null=True, blank=True, help_text="For teachers")
    class_grade = models.CharField(max_length=50, null=True, blank=True, help_text="For students")
    profile_picture = models.ImageField(upload_to='avatars/', null=True, blank=True)
    profile_picture_url = models.URLField(max_length=500, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['user'], name='idx_user_profiles_user_id'),
            models.Index(fields=['student_id'], name='idx_user_profiles_student_id'),
            models.Index(fields=['teacher_id'], name='idx_user_profiles_teacher_id'),
        ]
    
    def __str__(self):
        return f"Profile for {self.user.username}"


class UserActivityLog(BaseModel):
    """User activity logs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_activity_logs'
        indexes = [
            models.Index(fields=['user'], name='idx_activity_logs_user_id'),
            models.Index(fields=['created_at'], name='idx_activity_logs_created_at'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action}"


class UserImportLog(models.Model):
    """Log for bulk user import from Excel"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    imported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='import_logs')
    original_filename = models.CharField(max_length=255)
    file_size_kb = models.IntegerField()
    total_rows = models.IntegerField(default=0)
    total_created = models.IntegerField(default=0)
    total_skipped = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_details = models.JSONField(null=True, blank=True, default=list)
    skip_details = models.JSONField(null=True, blank=True, default=list)
    send_credentials_email = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_import_logs'
        indexes = [
            models.Index(fields=['imported_by'], name='idx_uil_imported_by'),
            models.Index(fields=['status'], name='idx_user_import_logs_status'),
            models.Index(fields=['-created_at'], name='idx_uil_created_at'),
        ]
    
    def __str__(self):
        return f"Import {self.original_filename} by {self.imported_by.username} - {self.status}"
