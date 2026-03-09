from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import OperationalError, ProgrammingError, transaction
from django.db.models import Q

from .forms import OPTION_LETTERS
from .models import (
    Question,
    QuestionAnswer,
    QuestionImportLog,
    QuestionOption,
    QuestionTag,
    QuestionTagRelation,
)


QUESTION_TYPE_LABELS = dict(Question.QuestionType.choices)
DIFFICULTY_LABELS = dict(Question.Difficulty.choices)
RICHTEXT_UPLOAD_DIRECTORY = "questions/richtext"
RICHTEXT_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
RICHTEXT_VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg"}
RICHTEXT_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".aac"}
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
        .prefetch_related("options", "correct_answer", "questiontagrelation_set__tag")
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


def save_question_richtext_media(uploaded_file):
    if not uploaded_file:
        raise ValidationError("File media tidak ditemukan.")

    extension = Path(uploaded_file.name).suffix.lower()
    if extension in RICHTEXT_IMAGE_EXTENSIONS:
        media_kind = "image"
        max_size = RICHTEXT_MAX_IMAGE_SIZE
    elif extension in RICHTEXT_VIDEO_EXTENSIONS:
        media_kind = "video"
        max_size = RICHTEXT_MAX_MEDIA_SIZE
    elif extension in RICHTEXT_AUDIO_EXTENSIONS:
        media_kind = "audio"
        max_size = RICHTEXT_MAX_MEDIA_SIZE
    else:
        raise ValidationError("Format file tidak didukung. Gunakan gambar, audio, atau video yang valid.")

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
    stored_name = storage.save(filename, uploaded_file)
    file_url = storage.url(stored_name)
    return {
        "url": file_url,
        "location": file_url,
        "kind": media_kind,
        "name": Path(uploaded_file.name).name,
    }


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
    stored_name = storage.save(filename, uploaded_file)
    new_url = storage.url(stored_name)

    old_url = question.question_image_url
    question.question_image_url = new_url
    question.save(update_fields=["question_image_url"])
    if old_url and old_url != new_url:
        _delete_local_image_if_exists(old_url)
    return new_url


def sync_question_options(question, cleaned_data):
    question_type = cleaned_data.get("question_type")
    if question_type != Question.QuestionType.MULTIPLE_CHOICE:
        QuestionOption.objects.filter(question=question).delete()
        return

    options = []
    display_order = 1
    for letter in OPTION_LETTERS:
        text = (cleaned_data.get(f"option_{letter.lower()}") or "").strip()
        if not text:
            continue
        options.append(
            QuestionOption(
                question=question,
                option_letter=letter,
                option_text=text,
                is_correct=(cleaned_data.get("correct_option") == letter),
                display_order=display_order,
            )
        )
        display_order += 1
    QuestionOption.objects.filter(question=question).delete()
    QuestionOption.objects.bulk_create(options)


def sync_question_answer(question, cleaned_data):
    question_type = cleaned_data.get("question_type")
    if question_type == Question.QuestionType.MULTIPLE_CHOICE:
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
    if is_create:
        target.created_by = teacher
    target.save()

    cleaned_data = form.cleaned_data
    sync_question_options(target, cleaned_data)
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
        points=source_question.points,
        difficulty_level=source_question.difficulty_level,
        explanation=source_question.explanation,
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
