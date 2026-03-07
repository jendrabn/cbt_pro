from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserActivityLog, UserImportLog, UserProfile

from .importers import ExcelUserImporter, ImportPreviewResult

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
    activity = _build_user_activity_log(user, action, description=description, request=request)
    activity.save()
    return activity


def _build_user_activity_log(user, action, description="", request=None):
    ip_address, user_agent = _request_meta(request)
    return UserActivityLog(
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
    default_password: str = ""
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
    importer = ExcelUserImporter(role)
    return importer.parse_file(uploaded_file)


def save_import_preview(preview_key: str, preview_data: dict, ttl: int = IMPORT_PREVIEW_CACHE_TTL):
    cache.set(f"{IMPORT_PREVIEW_CACHE_PREFIX}{preview_key}", preview_data, ttl)


def get_import_preview(preview_key: str) -> dict | None:
    return cache.get(f"{IMPORT_PREVIEW_CACHE_PREFIX}{preview_key}")


def delete_import_preview(preview_key: str):
    cache.delete(f"{IMPORT_PREVIEW_CACHE_PREFIX}{preview_key}")


def _current_import_password() -> str:
    return timezone.localtime().strftime("%Y%m%d")


def _chunked(rows: list[dict[str, Any]], chunk_size: int):
    chunk_size = max(1, chunk_size)
    for start in range(0, len(rows), chunk_size):
        yield rows[start:start + chunk_size]


def _profile_payload_from_row(role: str, row_data: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "phone_number": row_data.get("phone_number") or None,
        "teacher_id": None,
        "subject_specialization": None,
        "student_id": None,
        "class_grade": None,
    }
    if role == "teacher":
        payload["teacher_id"] = row_data.get("teacher_id") or None
        payload["subject_specialization"] = row_data.get("subject_specialization") or None
    elif role == "student":
        payload["student_id"] = row_data.get("student_id") or None
        payload["class_grade"] = row_data.get("class_grade") or None
    return payload


def _append_import_error(result: ImportResult, row_data: dict[str, Any], error: str):
    result.total_failed += 1
    result.error_details.append(
        {
            "row": row_data.get("row_number", 0),
            "username": row_data.get("username", ""),
            "email": row_data.get("email", ""),
            "error": error,
        }
    )


def _append_import_skip(result: ImportResult, row_data: dict[str, Any], reason: str):
    result.total_skipped += 1
    result.skip_details.append(
        {
            "row": row_data.get("row_number", 0),
            "username": row_data.get("username", ""),
            "email": row_data.get("email", ""),
            "reason": reason,
        }
    )


def _create_user_row(row_data: dict[str, Any], role: str, actor, plain_password: str, encoded_password: str, request=None):
    user = User(
        username=row_data["username"],
        email=row_data["email"],
        first_name=row_data["first_name"],
        last_name=row_data["last_name"],
        role=role,
        is_active=row_data.get("is_active", True),
        is_staff=(role == "admin"),
        password=encoded_password,
    )
    user.save()
    UserProfile.objects.create(user=user, **_profile_payload_from_row(role, row_data))
    log_user_activity(
        user,
        "akun_dibuat",
        f"Akun dibuat via import oleh {actor.username}.",
        request=request,
    )
    return user, plain_password


def _process_single_user_row(
    row_data: dict[str, Any],
    role: str,
    actor,
    result: ImportResult,
    plain_password: str,
    encoded_password: str,
    request=None,
):
    username = row_data.get("username", "")
    email = row_data.get("email", "")
    with transaction.atomic():
        if User.objects.filter(email=email).exists():
            _append_import_skip(result, row_data, "Email sudah terdaftar saat proses import.")
            return None
        if User.objects.filter(username=username).exists():
            _append_import_skip(result, row_data, "Username sudah terdaftar saat proses import.")
            return None
        user, password = _create_user_row(
            row_data,
            role,
            actor=actor,
            plain_password=plain_password,
            encoded_password=encoded_password,
            request=request,
        )

    result.total_created += 1
    result.created_user_ids.append(str(user.id))
    return {
        "user_id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.get_full_name().strip() or user.username,
        "temp_password": password,
    }


def _process_user_chunk(
    rows: list[dict[str, Any]],
    role: str,
    actor,
    result: ImportResult,
    plain_password: str,
    encoded_password: str,
    request=None,
):
    pending_rows = []
    user_objects = []

    usernames = [row.get("username", "") for row in rows if row.get("username")]
    emails = [row.get("email", "") for row in rows if row.get("email")]
    existing_usernames = set(User.objects.filter(username__in=usernames).values_list("username", flat=True))
    existing_emails = set(User.objects.filter(email__in=emails).values_list("email", flat=True))

    for row_data in rows:
        username = row_data.get("username", "")
        email = row_data.get("email", "")
        if email in existing_emails:
            _append_import_skip(result, row_data, "Email sudah terdaftar saat proses import.")
            continue
        if username in existing_usernames:
            _append_import_skip(result, row_data, "Username sudah terdaftar saat proses import.")
            continue

        pending_rows.append(row_data)
        user_objects.append(
            User(
                username=username,
                email=email,
                first_name=row_data["first_name"],
                last_name=row_data["last_name"],
                role=role,
                is_active=row_data.get("is_active", True),
                is_staff=(role == "admin"),
                password=encoded_password,
            )
        )

    if not pending_rows:
        return []

    try:
        with transaction.atomic():
            User.objects.bulk_create(user_objects, batch_size=getattr(settings, "USER_IMPORT_CHUNK_SIZE", 250))
            created_users = list(User.objects.filter(username__in=[row["username"] for row in pending_rows]))
            users_by_username = {user.username: user for user in created_users}

            missing = [row["username"] for row in pending_rows if row["username"] not in users_by_username]
            if missing:
                raise ValueError(f"Gagal mengambil user hasil bulk insert: {', '.join(missing)}")

            profiles = []
            activity_logs = []
            credential_rows = []
            for row_data in pending_rows:
                user = users_by_username[row_data["username"]]
                profiles.append(UserProfile(user=user, **_profile_payload_from_row(role, row_data)))
                activity_logs.append(
                    _build_user_activity_log(
                        user,
                        "akun_dibuat",
                        f"Akun dibuat via import oleh {actor.username}.",
                        request=request,
                    )
                )
                result.total_created += 1
                result.created_user_ids.append(str(user.id))
                credential_rows.append(
                    {
                        "user_id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.get_full_name().strip() or user.username,
                        "temp_password": plain_password,
                    }
                )

            UserProfile.objects.bulk_create(profiles, batch_size=getattr(settings, "USER_IMPORT_CHUNK_SIZE", 250))
            UserActivityLog.objects.bulk_create(
                activity_logs,
                batch_size=getattr(settings, "USER_IMPORT_CHUNK_SIZE", 250),
            )
            return credential_rows
    except Exception:
        credential_rows = []
        for row_data in pending_rows:
            try:
                credential = _process_single_user_row(
                    row_data,
                    role,
                    actor=actor,
                    result=result,
                    plain_password=plain_password,
                    encoded_password=encoded_password,
                    request=request,
                )
                if credential:
                    credential_rows.append(credential)
            except Exception as exc:
                _append_import_error(result, row_data, str(exc))
        return credential_rows


def execute_import(preview_key: str, actor, request=None) -> ImportResult:
    preview_data = get_import_preview(preview_key)
    if not preview_data:
        raise ValidationError("Data preview tidak ditemukan atau sudah kedaluwarsa. Silakan upload ulang file.")

    result = ImportResult()
    result.default_password = _current_import_password()
    valid_rows = preview_data.get("valid_rows", [])
    role = preview_data.get("role", "student")
    send_credentials_email = preview_data.get("send_credentials_email", False)
    encoded_password = make_password(result.default_password)

    import_log = UserImportLog.objects.create(
        imported_by=actor,
        original_filename=preview_data.get("filename", "unknown.xlsx"),
        file_size_kb=preview_data.get("file_size_kb", 0),
        total_rows=len(valid_rows) + len(preview_data.get("skip_rows", [])) + len(preview_data.get("error_rows", [])),
        status="processing",
        send_credentials_email=send_credentials_email,
        started_at=timezone.now(),
    )

    credential_rows = []
    try:
        for chunk in _chunked(valid_rows, getattr(settings, "USER_IMPORT_CHUNK_SIZE", 250)):
            credential_rows.extend(
                _process_user_chunk(
                    chunk,
                    role=role,
                    actor=actor,
                    result=result,
                    plain_password=result.default_password,
                    encoded_password=encoded_password,
                    request=request,
                )
            )

        for skip_row in preview_data.get("skip_rows", []):
            _append_import_skip(result, skip_row, skip_row.get("error", "Baris dilewati."))

        for error_row in preview_data.get("error_rows", []):
            if error_row.get("row_number", 0) > 0:
                _append_import_error(result, error_row, error_row.get("error", "Baris gagal diproses."))

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

        if send_credentials_email and credential_rows:
            from .tasks import queue_credentials_email

            queue_credentials_email(credential_rows, actor.username)

        return result
    except Exception as exc:
        import_log.total_created = result.total_created
        import_log.total_skipped = result.total_skipped
        import_log.total_failed = result.total_failed + 1
        import_log.error_details = result.error_details + [
            {
                "row": 0,
                "username": "",
                "email": "",
                "error": str(exc),
            }
        ]
        import_log.skip_details = result.skip_details
        import_log.status = "failed"
        import_log.finished_at = timezone.now()
        import_log.save()
        raise
    finally:
        delete_import_preview(preview_key)


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
