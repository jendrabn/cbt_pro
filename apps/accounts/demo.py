from __future__ import annotations

from django.conf import settings


def _normalize(value):
    return str(value or "").strip().casefold()


def get_demo_accounts():
    return {
        "teacher": {
            "label": "Guru",
            "username": getattr(settings, "DEMO_TEACHER_USERNAME", ""),
            "email": getattr(settings, "DEMO_TEACHER_EMAIL", ""),
            "password": getattr(settings, "DEMO_TEACHER_PASSWORD", ""),
        },
        "student": {
            "label": "Siswa",
            "username": getattr(settings, "DEMO_STUDENT_USERNAME", ""),
            "email": getattr(settings, "DEMO_STUDENT_EMAIL", ""),
            "password": getattr(settings, "DEMO_STUDENT_PASSWORD", ""),
        },
    }


def is_demo_restricted_user(user):
    if not getattr(settings, "DEMO_MODE", False):
        return False
    if not getattr(user, "is_authenticated", False):
        return False

    account = get_demo_accounts().get(getattr(user, "role", ""))
    if not account:
        return False

    username = _normalize(getattr(user, "username", ""))
    email = _normalize(getattr(user, "email", ""))
    return (
        bool(account["username"]) and username == _normalize(account["username"])
    ) or (
        bool(account["email"]) and email == _normalize(account["email"])
    )
