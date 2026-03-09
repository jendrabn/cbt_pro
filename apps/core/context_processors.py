from __future__ import annotations

from pathlib import Path

from django.conf import settings

from apps.accounts.demo import is_demo_restricted_user
from apps.core.services import get_auth_feature_settings, get_branding_settings


def branding_context(request):
    return {"branding": get_branding_settings()}


def asset_version_context(request):
    css_path = Path(settings.BASE_DIR) / "static" / "css" / "main.css"
    try:
        version = str(int(css_path.stat().st_mtime))
    except OSError:
        version = "1"
    return {"asset_version": version}


def auth_feature_context(request):
    return {"auth_features": get_auth_feature_settings()}


def demo_context(request):
    return {
        "demo_mode": settings.DEMO_MODE,
        "is_demo_restricted_user": is_demo_restricted_user(getattr(request, "user", None)),
    }
