from __future__ import annotations

import re
import secrets
from datetime import datetime


PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def generate_certificate_number(prefix: str = "CERT", now: datetime | None = None) -> str:
    current = now or datetime.now()
    safe_prefix = (prefix or "CERT").strip().upper() or "CERT"
    token = secrets.token_urlsafe(6).replace("-", "").replace("_", "").upper()
    return f"{safe_prefix}-{current.strftime('%Y%m')}-{token[:6]}"


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32).replace("-", "").replace("_", "")


def render_template_text(template: str, payload: dict[str, object]) -> str:
    text = str(template or "")

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = payload.get(key)
        return "" if value is None else str(value)

    return PLACEHOLDER_PATTERN.sub(_replace, text)
