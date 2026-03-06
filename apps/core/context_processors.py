from __future__ import annotations

from pathlib import Path

from django.conf import settings

from apps.core.services import get_branding_settings


def branding_context(request):
    return {"branding": get_branding_settings()}


def asset_version_context(request):
    css_path = Path(settings.BASE_DIR) / "static" / "css" / "main.css"
    try:
        version = str(int(css_path.stat().st_mtime))
    except OSError:
        version = "1"
    return {"asset_version": version}
