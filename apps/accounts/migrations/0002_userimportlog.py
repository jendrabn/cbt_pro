# Generated manually

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserImportLog",
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
                ("send_credentials_email", models.BooleanField(default=False)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "imported_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="import_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "user_import_logs",
            },
        ),
        migrations.AddIndex(
            model_name="userimportlog",
            index=models.Index(
                fields=["imported_by"], name="idx_uil_imported_by"
            ),
        ),
        migrations.AddIndex(
            model_name="userimportlog",
            index=models.Index(fields=["status"], name="idx_user_import_logs_status"),
        ),
        migrations.AddIndex(
            model_name="userimportlog",
            index=models.Index(
                fields=["-created_at"], name="idx_uil_created_at"
            ),
        ),
    ]
