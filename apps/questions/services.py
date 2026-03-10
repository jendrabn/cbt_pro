from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

import puremagic
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage
from django.db import OperationalError, ProgrammingError, transaction
from django.db.models import Q

from .forms import OPTION_LETTERS
from .models import (
    Question,
    QuestionAnswer,
    QuestionImportLog,
    QuestionBlankAnswer,
    QuestionMatchingPair,
    QuestionOption,
    QuestionOrderingItem,
    QuestionTag,
    QuestionTagRelation,
)
from .richtext import optimize_uploaded_image, sanitize_optional_richtext_html, sanitize_richtext_html


QUESTION_TYPE_LABELS = dict(Question.QuestionType.choices)
DIFFICULTY_LABELS = dict(Question.Difficulty.choices)
RICHTEXT_UPLOAD_DIRECTORY = "questions/richtext"
RICHTEXT_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
RICHTEXT_VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg"}
RICHTEXT_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac"}
RICHTEXT_IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
RICHTEXT_VIDEO_MIME_TYPES = {"video/mp4", "video/webm", "video/ogg"}
RICHTEXT_AUDIO_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wave",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/mp4",
    "audio/x-m4a",
    "audio/aac",
    "audio/aacp",
}
RICHTEXT_MAX_IMAGE_SIZE = 5 * 1024 * 1024
RICHTEXT_MAX_MEDIA_SIZE = 25 * 1024 * 1024


@dataclass
class FilterState:
    q: str = ""
    question_type: str = ""
    subject: str = ""
    difficulty: str = ""
    category: str = ""


def get_teacher_question_queryset(teacher):
    return (
        Question.objects.filter(created_by=teacher, is_deleted=False)
        .select_related("subject", "category")
        .prefetch_related(
            "options",
            "ordering_items",
            "matching_pairs",
            "blank_answers",
            "correct_answer",
            "questiontagrelation_set__tag",
        )
        .order_by("-updated_at")
    )


def filter_teacher_questions(queryset, params):
    filters = FilterState(
        q=(params.get("q") or "").strip(),
        question_type=(params.get("question_type") or "").strip(),
        subject=(params.get("subject") or "").strip(),
        difficulty=(params.get("difficulty") or "").strip(),
        category=(params.get("category") or "").strip(),
    )

    if filters.q:
        queryset = queryset.filter(
            Q(question_text__icontains=filters.q)
            | Q(explanation__icontains=filters.q)
            | Q(subject__name__icontains=filters.q)
            | Q(category__name__icontains=filters.q)
        )
    if filters.question_type in QUESTION_TYPE_LABELS:
        queryset = queryset.filter(question_type=filters.question_type)
    if filters.subject:
        queryset = queryset.filter(subject_id=filters.subject)
    if filters.difficulty in DIFFICULTY_LABELS:
        queryset = queryset.filter(difficulty_level=filters.difficulty)
    if filters.category:
        queryset = queryset.filter(category_id=filters.category)

    return queryset, filters


def parse_tags(tags_value):
    raw_items = [item.strip() for item in (tags_value or "").split(",")]
    unique = []
    seen = set()
    for item in raw_items:
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _delete_local_image_if_exists(image_url):
    if not image_url:
        return
    if not image_url.startswith(settings.MEDIA_URL):
        return
    relative_path = image_url[len(settings.MEDIA_URL):].lstrip("/")
    target_file = Path(settings.MEDIA_ROOT) / relative_path
    if target_file.exists() and target_file.is_file():
        target_file.unlink()


def _detect_richtext_media_kind(uploaded_file):
    extension = Path(getattr(uploaded_file, "name", "")).suffix.lower()
    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    raw_bytes = b""
    try:
        raw_bytes = uploaded_file.read(8192)
    finally:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass

    if not raw_bytes:
        raise ValidationError("File media kosong atau tidak dapat dibaca.")

    try:
        mime_type = puremagic.from_string(raw_bytes, mime=True)
    except (puremagic.PureError, ValueError) as exc:
        raise ValidationError("Tipe file media tidak dapat dikenali.") from exc

    if mime_type in RICHTEXT_IMAGE_MIME_TYPES or mime_type.startswith("image/"):
        if extension in RICHTEXT_IMAGE_EXTENSIONS:
            return "image", extension
        raise ValidationError("Ekstensi file gambar tidak didukung.")

    if mime_type in RICHTEXT_VIDEO_MIME_TYPES or (mime_type == "application/ogg" and extension in RICHTEXT_VIDEO_EXTENSIONS):
        if extension in RICHTEXT_VIDEO_EXTENSIONS:
            return "video", extension
        raise ValidationError("Ekstensi file video tidak didukung.")

    if mime_type in RICHTEXT_AUDIO_MIME_TYPES or (mime_type == "application/ogg" and extension in RICHTEXT_AUDIO_EXTENSIONS):
        if extension in RICHTEXT_AUDIO_EXTENSIONS:
            return "audio", extension
        raise ValidationError("Ekstensi file audio tidak didukung.")

    raise ValidationError("Format file tidak didukung. Gunakan gambar, audio, atau video yang valid.")


def save_question_richtext_media(uploaded_file):
    if not uploaded_file:
        raise ValidationError("File media tidak ditemukan.")

    media_kind, extension = _detect_richtext_media_kind(uploaded_file)
    max_size = RICHTEXT_MAX_IMAGE_SIZE if media_kind == "image" else RICHTEXT_MAX_MEDIA_SIZE

    if uploaded_file.size > max_size:
        if media_kind == "image":
            raise ValidationError("Ukuran gambar maksimal 5MB.")
        raise ValidationError("Ukuran file audio/video maksimal 25MB.")

    folder = Path(settings.MEDIA_ROOT) / RICHTEXT_UPLOAD_DIRECTORY
    folder.mkdir(parents=True, exist_ok=True)
    storage = FileSystemStorage(
        location=str(folder),
        base_url=f"{settings.MEDIA_URL.rstrip('/')}/{RICHTEXT_UPLOAD_DIRECTORY}/",
    )
    filename = f"{uuid.uuid4().hex}{extension}"
    stored_file = optimize_uploaded_image(uploaded_file) if media_kind == "image" else uploaded_file
    if isinstance(stored_file, File):
        stored_file.name = filename
    stored_name = storage.save(filename, stored_file)
    file_url = storage.url(stored_name)
    return {
        "url": file_url,
        "location": file_url,
        "kind": media_kind,
        "name": Path(uploaded_file.name).name,
    }


def _resolve_richtext_media_kind(path_obj: Path):
    extension = path_obj.suffix.lower()
    if extension in RICHTEXT_IMAGE_EXTENSIONS:
        return "image"
    if extension in RICHTEXT_VIDEO_EXTENSIONS:
        return "video"
    if extension in RICHTEXT_AUDIO_EXTENSIONS:
        return "audio"
    return ""


def list_question_richtext_media(media_kind="all", limit=120):
    folder = Path(settings.MEDIA_ROOT) / RICHTEXT_UPLOAD_DIRECTORY
    if not folder.exists():
        return []

    normalized_kind = (media_kind or "all").strip().lower()
    allowed_kinds = {
        "all": {"image", "audio", "video"},
        "image": {"image"},
        "media": {"audio", "video"},
        "audio": {"audio"},
        "video": {"video"},
    }.get(normalized_kind, {"image", "audio", "video"})

    rows = []
    media_root = Path(settings.MEDIA_ROOT)
    for file_path in folder.iterdir():
        if not file_path.is_file():
            continue
        resolved_kind = _resolve_richtext_media_kind(file_path)
        if not resolved_kind or resolved_kind not in allowed_kinds:
            continue

        stat_result = file_path.stat()
        relative_path = file_path.relative_to(media_root).as_posix()
        rows.append(
            {
                "name": file_path.name,
                "url": f"{settings.MEDIA_URL.rstrip('/')}/{relative_path}",
                "kind": resolved_kind,
                "size_kb": round(stat_result.st_size / 1024, 1),
                "modified_at": int(stat_result.st_mtime),
            }
        )

    rows.sort(key=lambda item: item["modified_at"], reverse=True)
    return rows[: max(int(limit or 0), 1)]


def save_question_image(question, uploaded_file):
    if not uploaded_file:
        return question.question_image_url

    folder = Path(settings.MEDIA_ROOT) / "questions"
    folder.mkdir(parents=True, exist_ok=True)
    storage = FileSystemStorage(
        location=str(folder),
        base_url=f"{settings.MEDIA_URL.rstrip('/')}/questions/",
    )
    extension = Path(uploaded_file.name).suffix.lower() or ".bin"
    filename = f"{uuid.uuid4().hex}{extension}"
    stored_file = optimize_uploaded_image(uploaded_file)
    if isinstance(stored_file, File):
        stored_file.name = filename
    stored_name = storage.save(filename, stored_file)
    new_url = storage.url(stored_name)

    old_url = question.question_image_url
    question.question_image_url = new_url
    question.save(update_fields=["question_image_url"])
    if old_url and old_url != new_url:
        _delete_local_image_if_exists(old_url)
    return new_url


def sync_question_options(question, cleaned_data):
    question_type = cleaned_data.get("question_type")
    if question_type not in {Question.QuestionType.MULTIPLE_CHOICE, Question.QuestionType.CHECKBOX}:
        QuestionOption.objects.filter(question=question).delete()
        return

    options = []
    display_order = 1
    correct_option = cleaned_data.get("correct_option")
    correct_options = set(cleaned_data.get("correct_options") or [])
    for letter in OPTION_LETTERS:
        text = sanitize_richtext_html(cleaned_data.get(f"option_{letter.lower()}"))
        if not text:
            continue
        options.append(
            QuestionOption(
                question=question,
                option_letter=letter,
                option_text=text,
                is_correct=(correct_option == letter) if question_type == Question.QuestionType.MULTIPLE_CHOICE else (letter in correct_options),
                display_order=display_order,
            )
        )
        display_order += 1
    QuestionOption.objects.filter(question=question).delete()
    QuestionOption.objects.bulk_create(options)


def sync_question_answer(question, cleaned_data):
    question_type = cleaned_data.get("question_type")
    if question_type in {
        Question.QuestionType.MULTIPLE_CHOICE,
        Question.QuestionType.CHECKBOX,
        Question.QuestionType.ORDERING,
        Question.QuestionType.MATCHING,
        Question.QuestionType.FILL_IN_BLANK,
    }:
        QuestionAnswer.objects.filter(question=question).delete()
        return

    keywords = parse_tags(cleaned_data.get("keywords"))
    defaults = {
        "answer_text": (cleaned_data.get("answer_text") or "").strip(),
        "keywords": keywords,
        "is_case_sensitive": bool(cleaned_data.get("is_case_sensitive")) if question_type == Question.QuestionType.SHORT_ANSWER else False,
        "max_word_count": cleaned_data.get("max_word_count"),
    }
    QuestionAnswer.objects.update_or_create(question=question, defaults=defaults)


def sync_question_ordering_items(question, cleaned_data):
    question_type = cleaned_data.get("question_type")
    if question_type != Question.QuestionType.ORDERING:
        QuestionOrderingItem.objects.filter(question=question).delete()
        return

    ordering_items = []
    for index, item_text in enumerate(cleaned_data.get("ordering_items") or [], start=1):
        sanitized_text = sanitize_richtext_html(item_text)
        if not sanitized_text:
            continue
        ordering_items.append(
            QuestionOrderingItem(
                question=question,
                item_text=sanitized_text,
                correct_order=index,
            )
        )

    QuestionOrderingItem.objects.filter(question=question).delete()
    QuestionOrderingItem.objects.bulk_create(ordering_items)


def sync_question_matching_pairs(question, cleaned_data):
    question_type = cleaned_data.get("question_type")
    if question_type != Question.QuestionType.MATCHING:
        QuestionMatchingPair.objects.filter(question=question).delete()
        return

    matching_pairs = []
    for pair in cleaned_data.get("matching_pairs") or []:
        prompt_text = sanitize_richtext_html(pair.get("prompt_text"))
        answer_text = sanitize_richtext_html(pair.get("answer_text"))
        if not prompt_text or not answer_text:
            continue
        matching_pairs.append(
            QuestionMatchingPair(
                question=question,
                prompt_text=prompt_text,
                answer_text=answer_text,
                pair_order=int(pair.get("pair_order") or (len(matching_pairs) + 1)),
            )
        )

    QuestionMatchingPair.objects.filter(question=question).delete()
    QuestionMatchingPair.objects.bulk_create(matching_pairs)


def sync_question_blank_answers(question, cleaned_data):
    question_type = cleaned_data.get("question_type")
    if question_type != Question.QuestionType.FILL_IN_BLANK:
        QuestionBlankAnswer.objects.filter(question=question).delete()
        return

    blank_answers = []
    for blank in cleaned_data.get("blank_answers") or []:
        accepted_answers = [str(item).strip() for item in (blank.get("accepted_answers") or []) if str(item).strip()]
        if not accepted_answers:
            continue
        blank_answers.append(
            QuestionBlankAnswer(
                question=question,
                blank_number=int(blank.get("blank_number") or (len(blank_answers) + 1)),
                accepted_answers=accepted_answers,
                is_case_sensitive=bool(blank.get("is_case_sensitive")),
                blank_points=blank.get("blank_points"),
            )
        )

    QuestionBlankAnswer.objects.filter(question=question).delete()
    QuestionBlankAnswer.objects.bulk_create(blank_answers)


def sync_question_tags(question, cleaned_data):
    tag_names = parse_tags(cleaned_data.get("tags"))
    QuestionTagRelation.objects.filter(question=question).delete()
    for name in tag_names:
        tag, _ = QuestionTag.objects.get_or_create(name=name)
        QuestionTagRelation.objects.create(question=question, tag=tag)


@transaction.atomic
def save_question_from_form(form, teacher, question=None):
    is_create = question is None
    target = form.save(commit=False)
    target.question_text = sanitize_richtext_html(target.question_text)
    target.explanation = sanitize_optional_richtext_html(target.explanation)
    if is_create:
        target.created_by = teacher
    target.save()

    cleaned_data = form.cleaned_data
    sync_question_options(target, cleaned_data)
    sync_question_ordering_items(target, cleaned_data)
    sync_question_matching_pairs(target, cleaned_data)
    sync_question_blank_answers(target, cleaned_data)
    sync_question_answer(target, cleaned_data)
    sync_question_tags(target, cleaned_data)
    save_question_image(target, cleaned_data.get("question_image"))
    return target


@transaction.atomic
def duplicate_question(source_question, teacher):
    copy_question = Question.objects.create(
        created_by=teacher,
        subject=source_question.subject,
        category=source_question.category,
        question_type=source_question.question_type,
        question_text=source_question.question_text,
        question_image_url=source_question.question_image_url,
        audio_play_limit=source_question.audio_play_limit,
        video_play_limit=source_question.video_play_limit,
        points=source_question.points,
        difficulty_level=source_question.difficulty_level,
        explanation=source_question.explanation,
        checkbox_scoring=source_question.checkbox_scoring,
        allow_previous=source_question.allow_previous,
        allow_next=source_question.allow_next,
        force_sequential=source_question.force_sequential,
        time_limit_seconds=source_question.time_limit_seconds,
        is_active=source_question.is_active,
    )

    source_options = source_question.options.all().order_by("display_order")
    if source_options.exists():
        QuestionOption.objects.bulk_create(
            [
                QuestionOption(
                    question=copy_question,
                    option_letter=option.option_letter,
                    option_text=option.option_text,
                    option_image_url=option.option_image_url,
                    is_correct=option.is_correct,
                    display_order=option.display_order,
                )
                for option in source_options
            ]
        )

    source_answer = QuestionAnswer.objects.filter(question=source_question).first()
    if source_answer:
        QuestionAnswer.objects.create(
            question=copy_question,
            answer_text=source_answer.answer_text,
            keywords=source_answer.keywords,
            is_case_sensitive=source_answer.is_case_sensitive,
            max_word_count=source_answer.max_word_count,
        )

    source_ordering_items = source_question.ordering_items.all().order_by("correct_order")
    if source_ordering_items.exists():
        QuestionOrderingItem.objects.bulk_create(
            [
                QuestionOrderingItem(
                    question=copy_question,
                    item_text=item.item_text,
                    correct_order=item.correct_order,
                )
                for item in source_ordering_items
            ]
        )

    source_matching_pairs = source_question.matching_pairs.all().order_by("pair_order")
    if source_matching_pairs.exists():
        QuestionMatchingPair.objects.bulk_create(
            [
                QuestionMatchingPair(
                    question=copy_question,
                    prompt_text=pair.prompt_text,
                    answer_text=pair.answer_text,
                    pair_order=pair.pair_order,
                )
                for pair in source_matching_pairs
            ]
        )

    source_blank_answers = source_question.blank_answers.all().order_by("blank_number")
    if source_blank_answers.exists():
        QuestionBlankAnswer.objects.bulk_create(
            [
                QuestionBlankAnswer(
                    question=copy_question,
                    blank_number=blank.blank_number,
                    accepted_answers=blank.accepted_answers,
                    is_case_sensitive=blank.is_case_sensitive,
                    blank_points=blank.blank_points,
                )
                for blank in source_blank_answers
            ]
        )

    source_tags = QuestionTagRelation.objects.filter(question=source_question).select_related("tag")
    for relation in source_tags:
        QuestionTagRelation.objects.create(question=copy_question, tag=relation.tag)

    return copy_question


def get_question_import_history(teacher=None, limit: int = 25):
    try:
        queryset = QuestionImportLog.objects.select_related("imported_by").order_by("-created_at")
        if teacher:
            queryset = queryset.filter(imported_by=teacher)
        return list(queryset[:limit])
    except (ProgrammingError, OperationalError):
        return []


def generate_question_import_report(import_log) -> bytes:
    from .exporters import export_import_report_excel

    return export_import_report_excel(import_log)
