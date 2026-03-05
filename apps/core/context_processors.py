from __future__ import annotations

from apps.core.services import get_branding_settings


def branding_context(request):
    return {"branding": get_branding_settings()}
