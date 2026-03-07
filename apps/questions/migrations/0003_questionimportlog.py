# Generated manually

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_userprofile_profile_picture"),
        ("questions", "0002_subject_to_subjects_app"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuestionImportLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("original_filename", models.CharField(max_length=255)),
                ("file_size_kb", models.IntegerField()),
                ("total_rows", models.IntegerField(default=0)),
                ("total_created", models.IntegerField(default=0)),
                ("total_skipped", models.IntegerField(default=0)),
                ("total_failed", models.IntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("error_details", models.JSONField(blank=True, default=list, null=True)),
                ("skip_details", models.JSONField(blank=True, default=list, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "imported_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="question_import_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "question_import_logs",
            },
        ),
        migrations.AddIndex(
            model_name="questionimportlog",
            index=models.Index(fields=["imported_by"], name="idx_qil_imported_by"),
        ),
        migrations.AddIndex(
            model_name="questionimportlog",
            index=models.Index(fields=["status"], name="idx_qil_status"),
        ),
        migrations.AddIndex(
            model_name="questionimportlog",
            index=models.Index(fields=["-created_at"], name="idx_qil_created_at"),
        ),
    ]
