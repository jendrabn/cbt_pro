from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from apps.accounts.models import UserActivityLog, UserImportLog, UserProfile

from .importers import ExcelUserImporter, ImportPreviewResult, JsonUserImporter

User = get_user_model()


IMPORT_PREVIEW_CACHE_PREFIX = "user_import_preview_"
IMPORT_PREVIEW_CACHE_TTL = 600  # 10 minutes


def _request_meta(request):
    if request is None:
        return None, None
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip_address = (xff.split(",")[0].strip() if xff else "") or request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT")
    return ip_address, user_agent


def log_user_activity(user, action, description="", request=None):
    ip_address, user_agent = _request_meta(request)
    return UserActivityLog.objects.create(
        user=user,
        action=action,
        description=description or "",
        ip_address=ip_address,
        user_agent=user_agent,
    )


def _upsert_profile(user, cleaned_data):
    role = cleaned_data.get("role")
    defaults = {
        "phone_number": cleaned_data.get("phone_number") or None,
        "teacher_id": None,
        "subject_specialization": None,
        "student_id": None,
        "class_grade": None,
    }
    if role == "teacher":
        defaults["teacher_id"] = cleaned_data.get("teacher_id") or None
        defaults["subject_specialization"] = cleaned_data.get("subject_specialization") or None
    elif role == "student":
        defaults["student_id"] = cleaned_data.get("student_id") or None
        defaults["class_grade"] = cleaned_data.get("class_grade") or None

    UserProfile.objects.update_or_create(user=user, defaults=defaults)


def _send_password_email(user, plain_password, changed_by=None):
    actor_name = getattr(changed_by, "username", "admin")
    subject = "Informasi Akun CBT"
    message = (
        "Halo,\n\n"
        f"Akun CBT Anda telah diperbarui oleh {actor_name}.\n"
        f"Username: {user.username}\n"
        f"Password: {plain_password}\n\n"
        "Silakan login dan segera ubah password Anda.\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[user.email],
        fail_silently=False,
    )


@dataclass
class ServiceResult:
    success_count: int = 0
    skipped_count: int = 0


@transaction.atomic
def create_user_with_profile(form, actor=None, request=None):
    cleaned = form.cleaned_data
    password = cleaned["password"]

    user = User(
        username=cleaned["username"],
        email=cleaned["email"],
        first_name=cleaned["first_name"],
        last_name=cleaned["last_name"],
        role=cleaned["role"],
        is_active=cleaned["is_active"],
        is_staff=cleaned["role"] == "admin",
    )
    user.set_password(password)
    user.save()

    _upsert_profile(user, cleaned)

    actor_name = getattr(actor, "username", "sistem")
    log_user_activity(user, "akun_dibuat", f"Akun dibuat oleh {actor_name}.", request=request)
    if actor and actor.pk != user.pk:
        log_user_activity(
            actor,
            "buat_pengguna",
            f"Membuat pengguna {user.username} ({user.role}).",
            request=request,
        )

    if cleaned.get("send_password_email"):
        _send_password_email(user, password, changed_by=actor)

    return user, password


@transaction.atomic
def update_user_with_profile(user, form, actor=None, request=None):
    cleaned = form.cleaned_data
    previous_role = user.role
    previous_status = user.is_active
    password = cleaned.get("password")

    user.first_name = cleaned["first_name"]
    user.last_name = cleaned["last_name"]
    user.email = cleaned["email"]
    user.username = cleaned["username"]
    user.role = cleaned["role"]
    user.is_active = cleaned["is_active"]
    if not user.is_superuser:
        user.is_staff = cleaned["role"] == "admin"
    if password:
        user.set_password(password)
    user.save()

    _upsert_profile(user, cleaned)

    log_user_activity(
        user,
        "akun_diperbarui",
        f"Profil akun diperbarui oleh {getattr(actor, 'username', 'sistem')}.",
        request=request,
    )
    if actor and actor.pk != user.pk:
        log_user_activity(
            actor,
            "ubah_pengguna",
            (
                f"Mengubah pengguna {user.username}. "
                f"Role: {previous_role} -> {user.role}. "
                f"Status: {'aktif' if previous_status else 'nonaktif'} -> "
                f"{'aktif' if user.is_active else 'nonaktif'}."
            ),
            request=request,
        )
    return user


@transaction.atomic
def soft_delete_user(user, actor=None, request=None):
    if actor and actor.pk == user.pk:
        raise ValidationError("Anda tidak dapat menghapus akun sendiri.")
    if user.is_superuser:
        raise ValidationError("Akun superuser tidak dapat dihapus.")

    user.is_active = False
    user.is_deleted = True
    user.save(update_fields=["is_active", "is_deleted"])

    if actor:
        log_user_activity(
            actor,
            "hapus_pengguna",
            f"Menghapus pengguna {user.username}.",
            request=request,
        )


@transaction.atomic
def toggle_user_status(user, is_active, actor=None, request=None):
    if user.is_deleted:
        raise ValidationError("Pengguna sudah dihapus dan tidak bisa diubah statusnya.")

    user.is_active = is_active
    user.save(update_fields=["is_active"])

    status_label = "aktif" if is_active else "nonaktif"
    log_user_activity(
        user,
        "status_diubah",
        f"Status akun diubah menjadi {status_label} oleh {getattr(actor, 'username', 'admin')}.",
        request=request,
    )
    if actor and actor.pk != user.pk:
        log_user_activity(
            actor,
            "ubah_status_pengguna",
            f"Mengubah status pengguna {user.username} menjadi {status_label}.",
            request=request,
        )
    return user


@transaction.atomic
def run_bulk_action(users_qs, action, actor=None, request=None):
    result = ServiceResult()

    if action == "activate":
        for user in users_qs:
            if user.is_deleted:
                result.skipped_count += 1
                continue
            toggle_user_status(user, True, actor=actor, request=request)
            result.success_count += 1
        return result

    if action == "deactivate":
        for user in users_qs:
            if user.is_deleted:
                result.skipped_count += 1
                continue
            toggle_user_status(user, False, actor=actor, request=request)
            result.success_count += 1
        return result

    if action == "delete":
        for user in users_qs:
            try:
                soft_delete_user(user, actor=actor, request=request)
                result.success_count += 1
            except ValidationError:
                result.skipped_count += 1
        return result

    raise ValidationError("Aksi bulk tidak dikenali.")


@dataclass
class ImportResult:
    total_created: int = 0
    total_skipped: int = 0
    total_failed: int = 0
    created_user_ids: list = None
    error_details: list = None
    skip_details: list = None

    def __post_init__(self):
        if self.created_user_ids is None:
            self.created_user_ids = []
        if self.error_details is None:
            self.error_details = []
        if self.skip_details is None:
            self.skip_details = []


def parse_import_file(uploaded_file, role: str) -> ImportPreviewResult:
    filename = (getattr(uploaded_file, "name", "") or "").lower()
    if filename.endswith(".json"):
        importer = JsonUserImporter(role)
    else:
        importer = ExcelUserImporter(role)
    return importer.parse_file(uploaded_file)


def save_import_preview(preview_key: str, preview_data: dict, ttl: int = IMPORT_PREVIEW_CACHE_TTL):
    cache.set(f"{IMPORT_PREVIEW_CACHE_PREFIX}{preview_key}", preview_data, ttl)


def get_import_preview(preview_key: str) -> dict | None:
    return cache.get(f"{IMPORT_PREVIEW_CACHE_PREFIX}{preview_key}")


def delete_import_preview(preview_key: str):
    cache.delete(f"{IMPORT_PREVIEW_CACHE_PREFIX}{preview_key}")


@transaction.atomic
def execute_import(preview_key: str, actor, request=None) -> ImportResult:
    preview_data = get_import_preview(preview_key)
    if not preview_data:
        raise ValidationError("Data preview tidak ditemukan atau sudah kedaluwarsa. Silakan upload ulang file.")

    result = ImportResult()
    valid_rows = preview_data.get("valid_rows", [])
    role = preview_data.get("role", "student")
    send_credentials_email = preview_data.get("send_credentials_email", False)

    import_log = UserImportLog.objects.create(
        imported_by=actor,
        original_filename=preview_data.get("filename", "unknown.xlsx"),
        file_size_kb=preview_data.get("file_size_kb", 0),
        total_rows=len(valid_rows) + len(preview_data.get("skip_rows", [])) + len(preview_data.get("error_rows", [])),
        status="processing",
        send_credentials_email=send_credentials_email,
        started_at=timezone.now(),
    )

    created_users = []
    passwords_map = {}

    for row_data in valid_rows:
        try:
            password = get_random_string(
                12,
                allowed_chars="abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789",
            )

            user = User(
                username=row_data["username"],
                email=row_data["email"],
                first_name=row_data["first_name"],
                last_name=row_data["last_name"],
                role=role,
                is_active=row_data.get("is_active", True),
                is_staff=(role == "admin"),
            )
            user.set_password(password)
            user.save()

            profile_defaults = {
                "phone_number": row_data.get("phone_number") or None,
            }
            if role == "teacher":
                profile_defaults["teacher_id"] = row_data.get("teacher_id") or None
                profile_defaults["subject_specialization"] = row_data.get("subject_specialization") or None
            elif role == "student":
                profile_defaults["student_id"] = row_data.get("student_id") or None
                profile_defaults["class_grade"] = row_data.get("class_grade") or None

            UserProfile.objects.update_or_create(user=user, defaults=profile_defaults)

            log_user_activity(
                user,
                "akun_dibuat",
                f"Akun dibuat via import oleh {actor.username}.",
                request=request,
            )

            created_users.append(user)
            passwords_map[str(user.id)] = password
            result.total_created += 1

        except Exception as exc:
            result.total_failed += 1
            result.error_details.append({
                "row": row_data.get("row_number", 0),
                "username": row_data.get("username", ""),
                "email": row_data.get("email", ""),
                "error": str(exc),
            })

    for skip_row in preview_data.get("skip_rows", []):
        result.total_skipped += 1
        result.skip_details.append({
            "row": skip_row.get("row_number", 0),
            "username": skip_row.get("username", ""),
            "email": skip_row.get("email", ""),
            "reason": skip_row.get("error", ""),
        })

    for error_row in preview_data.get("error_rows", []):
        if error_row.get("row_number", 0) > 0:
            result.total_failed += 1
            result.error_details.append({
                "row": error_row.get("row_number", 0),
                "username": error_row.get("username", ""),
                "email": error_row.get("email", ""),
                "error": error_row.get("error", ""),
            })

    if actor:
        log_user_activity(
            actor,
            "bulk_import",
            f"Import {result.total_created} user ({role}). File: {preview_data.get('filename', 'unknown')}",
            request=request,
        )

    import_log.total_created = result.total_created
    import_log.total_skipped = result.total_skipped
    import_log.total_failed = result.total_failed
    import_log.error_details = result.error_details
    import_log.skip_details = result.skip_details
    import_log.status = "completed"
    import_log.finished_at = timezone.now()
    import_log.save()

    result.created_user_ids = [str(u.id) for u in created_users]

    if send_credentials_email and created_users:
        from .tasks import queue_credentials_email

        for user in created_users:
            user._import_temp_password = passwords_map.get(str(user.id))
        queue_credentials_email(result.created_user_ids, actor.username)

    delete_import_preview(preview_key)

    return result


def generate_import_report(import_log: UserImportLog) -> bytes:
    from .exporters import ImportReportExporter

    rows_data = []

    if import_log.error_details:
        for error in import_log.error_details:
            rows_data.append({
                **error,
                "status": "error",
            })

    if import_log.skip_details:
        for skip in import_log.skip_details:
            rows_data.append({
                **skip,
                "status": "skip",
            })

    return ImportReportExporter.create_report(import_log, rows_data)


def get_import_history(actor=None, limit: int = 50):
    queryset = UserImportLog.objects.select_related("imported_by").order_by("-created_at")
    if actor:
        queryset = queryset.filter(imported_by=actor)
    return queryset[:limit]
