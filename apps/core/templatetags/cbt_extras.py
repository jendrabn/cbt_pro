from __future__ import annotations

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from urllib.parse import quote_plus

from apps.core.enums import get_enum_badge
from apps.questions.richtext import sanitize_richtext_html

register = template.Library()


@register.filter(name="bootstrap_alert_tone")
def bootstrap_alert_tone(value: str) -> str:
    """Map Django message tags and aliases to Bootstrap alert tones."""
    raw_tags = str(value or "").strip().lower().split()
    tags = set(raw_tags)

    if "error" in tags or "danger" in tags:
        return "danger"
    if "success" in tags:
        return "success"
    if "warning" in tags:
        return "warning"
    if "info" in tags:
        return "info"
    if "primary" in tags:
        return "primary"
    if "secondary" in tags:
        return "secondary"
    if "light" in tags:
        return "light"
    if "dark" in tags:
        return "dark"

    return "info"


@register.filter(name="initials")
def initials(value: str) -> str:
    parts = [part for part in str(value or "").strip().split() if part]
    if not parts:
        return "U"
    if len(parts) == 1:
        return parts[0][:1].upper()
    return f"{parts[0][:1]}{parts[-1][:1]}".upper()


@register.filter(name="avatar_url")
def avatar_url(name: str) -> str:
    name_str = str(name or "").strip() or "User"
    encoded_name = quote_plus(name_str)
    return f"https://ui-avatars.com/api/?name={encoded_name}&background=random&color=fff&bold=true"


@register.filter(name="max_words")
def max_words(value: str, limit: int = 2) -> str:
    try:
        max_limit = max(int(limit), 1)
    except (TypeError, ValueError):
        max_limit = 2

    parts = [part for part in str(value or "").strip().split() if part]
    if not parts:
        return "User"
    return " ".join(parts[:max_limit])


@register.filter(name="sanitize_richtext")
def sanitize_richtext(value: str) -> str:
    return mark_safe(sanitize_richtext_html(value))


@register.simple_tag(name="user_avatar_url")
def user_avatar_url(user) -> str:
    if user is None:
        return avatar_url("")

    display_name = user.get_full_name() or getattr(user, "username", "")

    try:
        profile = user.profile
    except ObjectDoesNotExist:
        profile = None

    if profile is not None:
        profile_picture = getattr(profile, "profile_picture", None)
        if profile_picture:
            try:
                return profile_picture.url
            except (OSError, ValueError):
                pass

        profile_picture_url = str(getattr(profile, "profile_picture_url", "") or "").strip()
        if profile_picture_url:
            return profile_picture_url

    return avatar_url(display_name)


@register.simple_tag(takes_context=True)
def cbt_active(context, *url_names: str) -> str:
    request = context.get("request")
    resolver_match = getattr(request, "resolver_match", None)
    current_name = getattr(resolver_match, "url_name", "")
    return "active" if current_name in set(url_names) else ""


def _render_badge(label: str, tone: str, extra_classes: str = "") -> str:
    classes = f"cbt-status-badge is-{tone}"
    if extra_classes:
        classes = f"{classes} {extra_classes}".strip()
    return format_html('<span class="{}">{}</span>', classes, label)


@register.simple_tag
def soft_badge(label: str, tone: str = "secondary", extra_classes: str = "") -> str:
    return _render_badge(str(label), str(tone or "secondary"), extra_classes=extra_classes)


@register.simple_tag
def enum_badge(kind: str, value, label: str | None = None, extra_classes: str = "") -> str:
    badge = get_enum_badge(kind, value, label=label)
    return _render_badge(badge["label"], badge["tone"], extra_classes=extra_classes)
