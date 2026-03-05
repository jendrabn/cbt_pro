import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('Users must have a username')
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model dengan UUID"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username'], condition=models.Q(is_deleted=False), name='idx_users_username'),
            models.Index(fields=['email'], condition=models.Q(is_deleted=False), name='idx_users_email'),
            models.Index(fields=['role'], condition=models.Q(is_deleted=False), name='idx_users_role'),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


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
