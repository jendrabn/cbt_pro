import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_alter_user_role_alter_userimportlog_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentActiveSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("session_key", models.CharField(blank=True, default="", max_length=40)),
                ("login_at", models.DateTimeField(blank=True, null=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, null=True)),
                ("reset_at", models.DateTimeField(blank=True, null=True)),
                ("reset_reason", models.CharField(blank=True, default="", max_length=255)),
                (
                    "reset_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reset_student_sessions",
                        to="accounts.user",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        limit_choices_to={"role": "student"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="active_student_session",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "db_table": "student_active_sessions",
            },
        ),
        migrations.AddIndex(
            model_name="studentactivesession",
            index=models.Index(fields=["session_key"], name="idx_stud_active_session_key"),
        ),
        migrations.AddIndex(
            model_name="studentactivesession",
            index=models.Index(fields=["last_seen_at"], name="idx_stud_active_last_seen"),
        ),
        migrations.AddIndex(
            model_name="studentactivesession",
            index=models.Index(fields=["reset_at"], name="idx_stud_active_reset_at"),
        ),
    ]
