from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.core.cache import cache
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone

from apps.notifications.models import SystemSetting

from .models import StudentActiveSession, UserActivityLog

DEFAULT_STUDENT_SESSION_TIMEOUT_MINUTES = 120
SESSION_TIMEOUT_CACHE_KEY = "cbt_student_session_timeout_minutes"
SESSION_TIMEOUT_CACHE_TTL_SECONDS = 60
SESSION_TOUCH_INTERVAL_SECONDS = 60


class ActiveStudentSessionExists(Exception):
    pass


@dataclass
class StudentSessionValidationResult:
    valid: bool
    reason: str = ""
    message: str = ""
    created: bool = False


def _request_meta(request):
    if request is None:
        return None, None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip_address = (forwarded.split(",")[0].strip() if forwarded else "") or request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT")
    return ip_address or None, user_agent or None


def _is_student_user(user) -> bool:
    return bool(getattr(user, "is_authenticated", False) and getattr(user, "role", "") == "student")


def get_student_session_timeout_minutes() -> int:
    cached = cache.get(SESSION_TIMEOUT_CACHE_KEY)
    if isinstance(cached, int):
        return cached

    row = (
        SystemSetting.objects.filter(setting_key="session_timeout_minutes")
        .only("setting_key", "setting_value", "setting_type")
        .first()
    )
    raw_value = row.get_value() if row else DEFAULT_STUDENT_SESSION_TIMEOUT_MINUTES
    try:
        minutes = int(raw_value)
    except (TypeError, ValueError):
        minutes = DEFAULT_STUDENT_SESSION_TIMEOUT_MINUTES
    minutes = max(5, min(minutes, 1440))
    cache.set(SESSION_TIMEOUT_CACHE_KEY, minutes, SESSION_TIMEOUT_CACHE_TTL_SECONDS)
    return minutes


def invalidate_student_session_timeout_cache():
    cache.delete(SESSION_TIMEOUT_CACHE_KEY)


def _session_exists(session_key: str, now=None) -> bool:
    key = (session_key or "").strip()
    if not key:
        return False
    now = now or timezone.now()
    return Session.objects.filter(session_key=key, expire_date__gte=now).exists()


def _delete_django_session(session_key: str):
    key = (session_key or "").strip()
    if key:
        Session.objects.filter(session_key=key).delete()


def _is_lock_expired(lock: StudentActiveSession, now=None) -> bool:
    now = now or timezone.now()
    reference_time = lock.last_seen_at or lock.login_at or lock.updated_at or lock.created_at
    if reference_time is None:
        return False
    timeout_delta = timedelta(minutes=get_student_session_timeout_minutes())
    return reference_time < (now - timeout_delta)


def _lock_has_active_session(lock: StudentActiveSession, now=None) -> tuple[bool, str]:
    now = now or timezone.now()
    if not (lock.session_key or "").strip():
        return False, "empty"
    if not _session_exists(lock.session_key, now=now):
        return False, "missing"
    if _is_lock_expired(lock, now=now):
        return False, "timeout"
    return True, ""


def _clear_lock(lock: StudentActiveSession, *, delete_session: bool = False, clear_reset_meta: bool = False):
    current_session_key = lock.session_key
    lock.session_key = ""
    lock.login_at = None
    lock.last_seen_at = None
    lock.ip_address = None
    lock.user_agent = ""

    update_fields = [
        "session_key",
        "login_at",
        "last_seen_at",
        "ip_address",
        "user_agent",
        "updated_at",
    ]
    if clear_reset_meta:
        lock.reset_at = None
        lock.reset_by = None
        lock.reset_reason = ""
        update_fields.extend(["reset_at", "reset_by", "reset_reason"])

    lock.save(update_fields=update_fields)
    if delete_session:
        _delete_django_session(current_session_key)


def _bind_lock(lock: StudentActiveSession, *, request, session_key: str):
    now = timezone.now()
    ip_address, user_agent = _request_meta(request)
    lock.session_key = session_key
    lock.login_at = now
    lock.last_seen_at = now
    lock.ip_address = ip_address
    lock.user_agent = user_agent or ""
    lock.reset_at = None
    lock.reset_by = None
    lock.reset_reason = ""
    lock.save(
        update_fields=[
            "session_key",
            "login_at",
            "last_seen_at",
            "ip_address",
            "user_agent",
            "reset_at",
            "reset_by",
            "reset_reason",
            "updated_at",
        ]
    )


def _touch_lock(lock: StudentActiveSession):
    now = timezone.now()
    if lock.last_seen_at and (now - lock.last_seen_at).total_seconds() < SESSION_TOUCH_INTERVAL_SECONDS:
        return
    lock.last_seen_at = now
    lock.save(update_fields=["last_seen_at", "updated_at"])


def _log_activity(user, action: str, description: str, request=None):
    if user is None:
        return
    ip_address, user_agent = _request_meta(request)
    UserActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def ensure_student_login_available(user) -> None:
    if not _is_student_user(user):
        return

    with transaction.atomic():
        lock, _ = StudentActiveSession.objects.select_for_update().get_or_create(user=user)
        is_active, reason = _lock_has_active_session(lock)
        if is_active:
            raise ActiveStudentSessionExists(
                "Akun siswa ini sedang aktif di perangkat lain. Minta guru atau admin untuk mereset sesi login terlebih dahulu."
            )
        if reason in {"missing", "timeout"}:
            _clear_lock(lock, delete_session=True)


def register_student_session(user, request, *, log_event: bool = False) -> None:
    if not _is_student_user(user):
        return

    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key or ""

    with transaction.atomic():
        lock, _ = StudentActiveSession.objects.select_for_update().get_or_create(user=user)
        is_active, reason = _lock_has_active_session(lock)
        if is_active and lock.session_key != session_key:
            raise ActiveStudentSessionExists(
                "Akun siswa ini baru saja aktif di perangkat lain. Silakan minta guru atau admin untuk mereset sesi lama."
            )
        if reason in {"missing", "timeout"}:
            _clear_lock(lock, delete_session=True)
        _bind_lock(lock, request=request, session_key=session_key)

    if log_event:
        _log_activity(user, "login_berhasil", "Login siswa berhasil dan sesi aktif dicatat.", request=request)


def release_student_session(user, session_key: str = "", *, request=None, delete_session: bool = False) -> bool:
    if not _is_student_user(user):
        return False

    with transaction.atomic():
        lock = (
            StudentActiveSession.objects.select_for_update()
            .filter(user=user)
            .first()
        )
        if not lock:
            return False
        stored_key = (lock.session_key or "").strip()
        current_key = (session_key or "").strip()
        if stored_key and current_key and stored_key != current_key:
            return False
        _clear_lock(lock, delete_session=delete_session, clear_reset_meta=True)

    _log_activity(user, "logout", "Siswa logout dari sistem.", request=request)
    return True


def reset_student_session(student, *, actor=None, request=None, reason: str = "") -> bool:
    if getattr(student, "role", "") != "student":
        raise ValueError("Reset sesi hanya berlaku untuk akun siswa.")

    with transaction.atomic():
        lock, _ = StudentActiveSession.objects.select_for_update().get_or_create(user=student)
        had_active_session, stale_reason = _lock_has_active_session(lock)
        if stale_reason in {"missing", "timeout"}:
            _clear_lock(lock, delete_session=True)

        session_key = lock.session_key
        lock.session_key = ""
        lock.login_at = None
        lock.last_seen_at = None
        lock.ip_address = None
        lock.user_agent = ""
        lock.reset_at = timezone.now()
        lock.reset_by = actor
        lock.reset_reason = reason or "reset_manual"
        lock.save(
            update_fields=[
                "session_key",
                "login_at",
                "last_seen_at",
                "ip_address",
                "user_agent",
                "reset_at",
                "reset_by",
                "reset_reason",
                "updated_at",
            ]
        )
        _delete_django_session(session_key)

    actor_name = getattr(actor, "username", "sistem")
    _log_activity(
        student,
        "sesi_direset",
        f"Sesi login direset oleh {actor_name}.",
        request=request,
    )
    if actor and actor.pk != student.pk:
        _log_activity(
            actor,
            "reset_sesi_siswa",
            f"Mereset sesi login siswa {student.username}.",
            request=request,
        )
    return had_active_session


def validate_student_request_session(request) -> StudentSessionValidationResult:
    user = getattr(request, "user", None)
    if not _is_student_user(user):
        return StudentSessionValidationResult(valid=True)

    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key or ""

    with transaction.atomic():
        lock, created = StudentActiveSession.objects.select_for_update().get_or_create(user=user)
        if created:
            _bind_lock(lock, request=request, session_key=session_key)
            return StudentSessionValidationResult(valid=True, created=True)

        is_active, reason = _lock_has_active_session(lock)
        if not is_active:
            if reason in {"missing", "timeout"}:
                _clear_lock(lock, delete_session=True)
                return StudentSessionValidationResult(
                    valid=False,
                    reason=reason,
                    message="Sesi login Anda sudah berakhir. Silakan login kembali.",
                )
            return StudentSessionValidationResult(
                valid=False,
                reason="reset",
                message="Sesi login Anda telah direset oleh guru atau admin. Silakan login kembali.",
            )

        if lock.session_key != session_key:
            return StudentSessionValidationResult(
                valid=False,
                reason="session_mismatch",
                message="Sesi login Anda tidak lagi valid. Silakan login kembali.",
            )

        _touch_lock(lock)
        return StudentSessionValidationResult(valid=True)


def get_student_session_status(user) -> dict:
    if getattr(user, "role", "") != "student":
        return {"managed": False, "active": False}

    lock = (
        StudentActiveSession.objects.filter(user=user)
        .select_related("reset_by")
        .first()
    )
    if not lock:
        return {
            "managed": True,
            "active": False,
            "label": "Belum ada sesi aktif",
            "login_at": None,
            "last_seen_at": None,
            "ip_address": None,
            "user_agent": "",
            "reset_at": None,
            "reset_by": None,
            "reset_reason": "",
        }

    is_active, reason = _lock_has_active_session(lock)
    if not is_active and reason in {"missing", "timeout"}:
        _clear_lock(lock, delete_session=True)
        lock.refresh_from_db()

    is_active = bool((lock.session_key or "").strip())
    return {
        "managed": True,
        "active": is_active,
        "label": "Aktif" if is_active else ("Direset" if lock.reset_at else "Tidak ada sesi aktif"),
        "login_at": lock.login_at,
        "last_seen_at": lock.last_seen_at,
        "ip_address": lock.ip_address,
        "user_agent": lock.user_agent or "",
        "reset_at": lock.reset_at,
        "reset_by": lock.reset_by,
        "reset_reason": lock.reset_reason or "",
    }
