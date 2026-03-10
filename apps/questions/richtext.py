from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import bleach
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


RICH_TEXT_ALLOWED_TAGS = [
    "a",
    "audio",
    "blockquote",
    "br",
    "caption",
    "code",
    "col",
    "colgroup",
    "div",
    "em",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "iframe",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "s",
    "source",
    "span",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
    "video",
]

RICH_TEXT_ALLOWED_ATTRIBUTES = {
    "*": ["class", "title", "lang", "dir"],
    "a": ["href", "target", "rel"],
    "audio": ["controls", "preload", "src"],
    "col": ["span", "width"],
    "iframe": [
        "allow",
        "allowfullscreen",
        "frameborder",
        "height",
        "loading",
        "referrerpolicy",
        "src",
        "title",
        "width",
    ],
    "img": ["alt", "height", "loading", "src", "width"],
    "source": ["src", "type"],
    "table": ["border", "cellpadding", "cellspacing"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan", "scope"],
    "video": ["controls", "height", "playsinline", "poster", "preload", "src", "width"],
}

RICH_TEXT_ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]
MAX_IMAGE_WIDTH = 1920
OPTIMIZED_IMAGE_QUALITY = 85
OPTIMIZABLE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VALIDATABLE_IMAGE_EXTENSIONS = OPTIMIZABLE_IMAGE_EXTENSIONS | {".gif"}
UNSAFE_BLOCK_RE = re.compile(r"<\s*(script|style)\b[^>]*>.*?<\s*/\s*\1\s*>", re.IGNORECASE | re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def sanitize_richtext_html(value: str | None) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""

    raw_value = UNSAFE_BLOCK_RE.sub("", raw_value)
    raw_value = HTML_COMMENT_RE.sub("", raw_value)

    cleaned = bleach.clean(
        raw_value,
        tags=RICH_TEXT_ALLOWED_TAGS,
        attributes=RICH_TEXT_ALLOWED_ATTRIBUTES,
        protocols=RICH_TEXT_ALLOWED_PROTOCOLS,
        strip=True,
    )
    return cleaned.strip()


def sanitize_optional_richtext_html(value: str | None) -> str | None:
    cleaned = sanitize_richtext_html(value)
    return cleaned or None


def optimize_uploaded_image(uploaded_file):
    extension = Path(getattr(uploaded_file, "name", "")).suffix.lower()
    if extension not in VALIDATABLE_IMAGE_EXTENSIONS:
        return uploaded_file

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        image.load()
    except (AttributeError, OSError, UnidentifiedImageError) as exc:
        raise ValidationError("File gambar tidak valid.") from exc
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass

    if extension == ".gif":
        return uploaded_file

    image = ImageOps.exif_transpose(image)
    if image.width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / float(image.width)
        resized_height = max(1, int(image.height * ratio))
        image = image.resize((MAX_IMAGE_WIDTH, resized_height), Image.Resampling.LANCZOS)

    target_format = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".png": "PNG",
        ".webp": "WEBP",
    }.get(extension, "PNG")

    if target_format == "JPEG" and image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")

    buffer = BytesIO()
    save_kwargs = {}
    if target_format == "JPEG":
        save_kwargs = {"quality": OPTIMIZED_IMAGE_QUALITY, "optimize": True}
    elif target_format == "PNG":
        save_kwargs = {"optimize": True}
    elif target_format == "WEBP":
        save_kwargs = {"quality": OPTIMIZED_IMAGE_QUALITY, "method": 6}

    image.save(buffer, format=target_format, **save_kwargs)
    buffer.seek(0)
    optimized_name = Path(getattr(uploaded_file, "name", "image")).name
    return ContentFile(buffer.getvalue(), name=optimized_name)
