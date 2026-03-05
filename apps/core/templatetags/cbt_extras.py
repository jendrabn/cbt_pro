from __future__ import annotations

from django import template
from urllib.parse import quote_plus

register = template.Library()


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


@register.simple_tag(takes_context=True)
def cbt_active(context, *url_names: str) -> str:
    request = context.get("request")
    resolver_match = getattr(request, "resolver_match", None)
    current_name = getattr(resolver_match, "url_name", "")
    return "active" if current_name in set(url_names) else ""

