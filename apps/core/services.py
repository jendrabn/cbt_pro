from __future__ import annotations

import re
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage

from apps.notifications.models import SystemSetting


BRANDING_CACHE_KEY = "cbt_branding_settings"
BRANDING_CACHE_TTL_SECONDS = 300

HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

BRANDING_DEFAULTS: dict[str, Any] = {
    "institution_name": getattr(settings, "CBT_SITE_NAME", "Sistem CBT"),
    "institution_type": "",
    "institution_address": "",
    "institution_phone": "",
    "institution_email": "",
    "institution_website": "",
    "institution_logo_url": "",
    "institution_logo_dark_url": "",
    "institution_favicon_url": "",
    "login_page_headline": "Selamat Datang",
    "login_page_subheadline": "",
    "login_page_background_url": "",
    "primary_color": "#0d6efd",
    "landing_page_enabled": True,
}


def invalidate_branding_cache():
    cache.delete(BRANDING_CACHE_KEY)


def _as_storage_url(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if text.startswith(("http://", "https://", "/", "data:")):
        return text
    try:
        return default_storage.url(text)
    except Exception:
        media_url = getattr(settings, "MEDIA_URL", "/media/")
        return f"{media_url.rstrip('/')}/{text.lstrip('/')}"


def _normalize_primary_color(value: Any) -> str:
    text = str(value or "").strip()
    if HEX_COLOR_PATTERN.match(text):
        return text
    return BRANDING_DEFAULTS["primary_color"]


def _normalize_boolean(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    if value is None:
        return default
    return bool(value)


def get_branding_settings() -> dict[str, Any]:
    cached = cache.get(BRANDING_CACHE_KEY)
    if isinstance(cached, dict):
        return cached

    keys = list(BRANDING_DEFAULTS.keys())
    legacy_keys = ["site_name", "site_logo"]
    rows = {
        row.setting_key: row
        for row in SystemSetting.objects.filter(setting_key__in=(keys + legacy_keys)).only(
            "setting_key",
            "setting_value",
            "setting_type",
        )
    }

    branding: dict[str, Any] = {}
    for key, default in BRANDING_DEFAULTS.items():
        row = rows.get(key)
        value = row.get_value() if row else default
        if value in {"", None}:
            value = default
        branding[key] = value

    # Legacy fallback from old keys if new keys are not configured.
    if not str(branding["institution_name"]).strip():
        legacy_name_row = rows.get("site_name")
        if legacy_name_row and str(legacy_name_row.get_value() or "").strip():
            branding["institution_name"] = legacy_name_row.get_value()
    if not str(branding["institution_logo_url"]).strip():
        legacy_logo_row = rows.get("site_logo")
        if legacy_logo_row and str(legacy_logo_row.get_value() or "").strip():
            branding["institution_logo_url"] = legacy_logo_row.get_value()

    branding["primary_color"] = _normalize_primary_color(branding.get("primary_color"))
    branding["landing_page_enabled"] = _normalize_boolean(
        branding.get("landing_page_enabled"),
        bool(BRANDING_DEFAULTS["landing_page_enabled"]),
    )

    for media_key in (
        "institution_logo_url",
        "institution_logo_dark_url",
        "institution_favicon_url",
        "login_page_background_url",
    ):
        branding[media_key] = _as_storage_url(str(branding.get(media_key, "")))

    cache.set(BRANDING_CACHE_KEY, branding, BRANDING_CACHE_TTL_SECONDS)
    return branding


AUTH_FEATURE_CACHE_KEY = "cbt_auth_features"
AUTH_FEATURE_CACHE_TTL_SECONDS = 300

AUTH_FEATURE_DEFAULTS = {
    "auth_enable_forgot_password": True,
    "auth_enable_password_reset": True,
    "auth_enable_teacher_registration": False,
    "auth_enable_student_registration": False,
}


def get_auth_feature_settings() -> dict[str, bool]:
    cached = cache.get(AUTH_FEATURE_CACHE_KEY)
    if isinstance(cached, dict):
        return cached

    rows = {
        row.setting_key: row
        for row in SystemSetting.objects.filter(setting_key__in=AUTH_FEATURE_DEFAULTS.keys()).only(
            "setting_key",
            "setting_value",
            "setting_type",
        )
    }

    features: dict[str, bool] = {}
    for key, default in AUTH_FEATURE_DEFAULTS.items():
        row = rows.get(key)
        raw_value = row.get_value() if row else default
        if isinstance(default, bool):
            features[key] = _normalize_boolean(raw_value, default)
        else:
            features[key] = bool(raw_value)

    cache.set(AUTH_FEATURE_CACHE_KEY, features, AUTH_FEATURE_CACHE_TTL_SECONDS)
    return features


def invalidate_auth_feature_cache():
    cache.delete(AUTH_FEATURE_CACHE_KEY)


CERTIFICATE_FEATURE_CACHE_KEY = "cbt_certificate_features"
CERTIFICATE_FEATURE_CACHE_TTL_SECONDS = 300

CERTIFICATE_FEATURE_DEFAULTS = {
    "certificate_number_prefix": "CERT",
    "certificate_pdf_dpi": 150,
    "certificate_storage_path": "certificates/",
    "certificate_email_enabled": False,
    "certificate_verify_public": True,
}


def get_certificate_feature_settings() -> dict[str, Any]:
    cached = cache.get(CERTIFICATE_FEATURE_CACHE_KEY)
    if isinstance(cached, dict):
        return cached

    rows = {
        row.setting_key: row
        for row in SystemSetting.objects.filter(setting_key__in=CERTIFICATE_FEATURE_DEFAULTS.keys()).only(
            "setting_key",
            "setting_value",
            "setting_type",
        )
    }

    features: dict[str, Any] = {}
    for key, default in CERTIFICATE_FEATURE_DEFAULTS.items():
        row = rows.get(key)
        raw_value = row.get_value() if row else default
        if isinstance(default, bool):
            features[key] = _normalize_boolean(raw_value, default)
        elif isinstance(default, int):
            try:
                features[key] = int(raw_value)
            except (TypeError, ValueError):
                features[key] = int(default)
        else:
            features[key] = str(raw_value or default)

    storage_path = str(features.get("certificate_storage_path") or "certificates/").replace("\\", "/")
    if storage_path and not storage_path.endswith("/"):
        storage_path += "/"
    features["certificate_storage_path"] = storage_path or "certificates/"

    cache.set(CERTIFICATE_FEATURE_CACHE_KEY, features, CERTIFICATE_FEATURE_CACHE_TTL_SECONDS)
    return features


def invalidate_certificate_feature_cache():
    cache.delete(CERTIFICATE_FEATURE_CACHE_KEY)
