import uuid
from django.db import models


class BaseModel(models.Model):
    """Base model dengan UUID dan timestamp"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class BaseModelSoftDelete(BaseModel):
    """Base model dengan soft delete"""
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
    
    def delete(self, *args, **kwargs):
        """Soft delete instead of hard delete"""
        self.is_deleted = True
        self.save()
    
    def hard_delete(self, *args, **kwargs):
        """Actual database delete"""
        super().delete(*args, **kwargs)
