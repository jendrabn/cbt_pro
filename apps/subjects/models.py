from django.db import models

from apps.core.models import BaseModel


class Subject(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "subjects"
        indexes = [
            models.Index(fields=["name"], name="idx_subjects_name"),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name
