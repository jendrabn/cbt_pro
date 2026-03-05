import uuid
from django.db import models
from apps.core.models import BaseModel
from apps.accounts.models import User


class Notification(BaseModel):
    """User notifications"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('announcement', 'Announcement'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    related_entity_type = models.CharField(max_length=50, null=True, blank=True, help_text="'exam', 'result', 'user', etc.")
    related_entity_id = models.UUIDField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user'], name='idx_notifications_user_id'),
            models.Index(fields=['user', 'is_read'], name='idx_notifications_is_read'),
            models.Index(fields=['created_at'], name='idx_notifications_created_at'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class SystemSetting(BaseModel):
    """System settings"""
    
    SETTING_TYPE_CHOICES = [
        ('string', 'String'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]
    
    setting_key = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPE_CHOICES)
    category = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'system_settings'
        indexes = [
            models.Index(fields=['setting_key'], name='idx_system_settings_key'),
            models.Index(fields=['category'], name='idx_system_settings_category'),
        ]
    
    def __str__(self):
        return self.setting_key
    
    def get_value(self):
        """Get setting value with proper type conversion"""
        if self.setting_type == 'boolean':
            return self.setting_value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'number':
            try:
                if '.' in self.setting_value:
                    return float(self.setting_value)
                return int(self.setting_value)
            except ValueError:
                return 0
        elif self.setting_type == 'json':
            import json
            try:
                return json.loads(self.setting_value)
            except json.JSONDecodeError:
                return {}
        return self.setting_value


class SystemLog(BaseModel):
    """System logs"""
    
    LOG_LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    log_level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES)
    logger_name = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField()
    module = models.CharField(max_length=100, null=True, blank=True)
    function_name = models.CharField(max_length=100, null=True, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    exception_info = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'system_logs'
        indexes = [
            models.Index(fields=['log_level'], name='idx_system_logs_level'),
            models.Index(fields=['created_at'], name='idx_system_logs_created_at'),
            models.Index(fields=['user'], name='idx_system_logs_user_id'),
        ]
    
    def __str__(self):
        return f"[{self.log_level}] {self.message[:50]}"
