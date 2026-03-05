from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from django.db import transaction
from openpyxl import load_workbook

from apps.subjects.models import Subject

from .models import Question, QuestionCategory
from .services import sync_question_answer, sync_question_options, sync_question_tags


@dataclass
class ImportResult:
    total_rows: int = 0
    success_count: int = 0
    errors: list[str] = field(default_factory=list)


def _normalize_question_type(value):
    raw = (value or "").strip().lower()
    mapping = {
        "multiple_choice": "multiple_choice",
        "pilihan_ganda": "multiple_choice",
        "pilihan ganda": "multiple_choice",
        "essay": "essay",
        "esai": "essay",
        "short_answer": "short_answer",
        "jawaban_singkat": "short_answer",
        "jawaban singkat": "short_answer",
    }
    if raw not in mapping:
        raise ValueError("Tipe soal tidak valid.")
    return mapping[raw]


def _normalize_difficulty(value):
    raw = (value or "").strip().lower()
    if not raw:
        return None
    mapping = {
        "easy": "easy",
        "mudah": "easy",
        "medium": "medium",
        "sedang": "medium",
        "hard": "hard",
        "sulit": "hard",
    }
    if raw not in mapping:
        raise ValueError("Tingkat kesulitan tidak valid.")
    return mapping[raw]


def _parse_bool(value, default=False):
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    raw = str(value).strip().lower()
    return raw in {"1", "true", "ya", "yes", "y"}


def _parse_decimal(value, default=Decimal("1.00")):
    if value in (None, ""):
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError("Nilai poin tidak valid.")


def _parse_int(value, field_label):
    if value in (None, ""):
        return None
    try:
        output = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_label} harus berupa angka.")
    if output <= 0:
        raise ValueError(f"{field_label} harus lebih dari 0.")
    return output


def _resolve_subject(subject_value):
    target = (subject_value or "").strip()
    if not target:
        raise ValueError("Mata pelajaran wajib diisi.")
    subject = Subject.objects.filter(code__iexact=target, is_active=True).first()
    if subject:
        return subject
    subject = Subject.objects.filter(name__iexact=target, is_active=True).first()
    if subject:
        return subject
    raise ValueError(f"Mata pelajaran '{target}' tidak ditemukan.")


def _resolve_category(category_value):
    target = (category_value or "").strip()
    if not target:
        return None
    category, _ = QuestionCategory.objects.get_or_create(
        name=target,
        defaults={"is_active": True},
    )
    return category


def _extract_cleaned_payload(payload, question_type):
    option_values = {
        "A": (payload.get("option_a") or "").strip(),
        "B": (payload.get("option_b") or "").strip(),
        "C": (payload.get("option_c") or "").strip(),
        "D": (payload.get("option_d") or "").strip(),
        "E": (payload.get("option_e") or "").strip(),
    }
    active_options = {letter: text for letter, text in option_values.items() if text}
    correct_option = (payload.get("correct_option") or "").strip().upper()

    if question_type == "multiple_choice":
        if len(active_options) < 2:
            raise ValueError("Soal pilihan ganda wajib memiliki minimal 2 opsi.")
        if correct_option not in active_options:
            raise ValueError("Jawaban benar harus salah satu dari opsi yang terisi.")
    else:
        if not (payload.get("answer_text") or "").strip():
            raise ValueError("Kunci jawaban/rubrik wajib diisi untuk tipe soal non-PG.")
        correct_option = ""

    output = {
        "question_type": question_type,
        "option_a": option_values["A"],
        "option_b": option_values["B"],
        "option_c": option_values["C"],
        "option_d": option_values["D"],
        "option_e": option_values["E"],
        "correct_option": correct_option,
        "answer_text": (payload.get("answer_text") or "").strip(),
        "keywords": (payload.get("keywords") or "").strip(),
        "is_case_sensitive": _parse_bool(payload.get("is_case_sensitive"), default=False),
        "max_word_count": _parse_int(payload.get("max_word_count"), "Batas kata"),
        "tags": (payload.get("tags") or "").strip(),
    }
    return output


@transaction.atomic
def _create_question_from_payload(payload, teacher):
    question_type = _normalize_question_type(payload.get("question_type"))
    question_text = (payload.get("question_text") or "").strip()
    if not question_text:
        raise ValueError("Teks soal wajib diisi.")

    subject = _resolve_subject(payload.get("subject"))
    category = _resolve_category(payload.get("category"))
    difficulty_level = _normalize_difficulty(payload.get("difficulty_level"))
    points = _parse_decimal(payload.get("points"))
    allow_previous = _parse_bool(payload.get("allow_previous"), default=True)
    allow_next = _parse_bool(payload.get("allow_next"), default=True)
    force_sequential = _parse_bool(payload.get("force_sequential"), default=False)
    if force_sequential:
        allow_previous = False

    question = Question.objects.create(
        created_by=teacher,
        subject=subject,
        category=category,
        question_type=question_type,
        question_text=question_text,
        question_image_url=(payload.get("question_image_url") or "").strip() or None,
        points=points,
        difficulty_level=difficulty_level,
        explanation=(payload.get("explanation") or "").strip() or None,
        allow_previous=allow_previous,
        allow_next=allow_next,
        force_sequential=force_sequential,
        time_limit_seconds=_parse_int(payload.get("time_limit_seconds"), "Batas waktu soal"),
        is_active=_parse_bool(payload.get("is_active"), default=True),
    )

    cleaned_data = _extract_cleaned_payload(payload, question_type)
    sync_question_options(question, cleaned_data)
    sync_question_answer(question, cleaned_data)
    sync_question_tags(question, cleaned_data)
    return question


def import_questions_from_json(uploaded_file, teacher):
    result = ImportResult()
    try:
        payload = json.loads(uploaded_file.read().decode("utf-8-sig"))
    except Exception as exc:
        result.errors.append(f"Gagal membaca file JSON: {exc}")
        return result

    rows = payload.get("questions", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        result.errors.append("Format JSON tidak valid. Harus berupa list data atau key 'questions'.")
        return result

    for index, row in enumerate(rows, start=1):
        result.total_rows += 1
        try:
            if not isinstance(row, dict):
                raise ValueError("Setiap item JSON harus berupa objek.")
            _create_question_from_payload(row, teacher)
            result.success_count += 1
        except Exception as exc:
            result.errors.append(f"Baris {index}: {exc}")
    return result


def import_questions_from_excel(uploaded_file, teacher):
    result = ImportResult()
    try:
        workbook = load_workbook(uploaded_file, data_only=True)
    except Exception as exc:
        result.errors.append(f"Gagal membaca file Excel: {exc}")
        return result

    sheet = workbook.active
    header_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), None)
    if not header_row:
        result.errors.append("File Excel kosong.")
        return result

    headers = [str(value).strip().lower() if value is not None else "" for value in header_row]
    required_headers = {"subject", "question_type", "question_text"}
    if not required_headers.issubset(set(headers)):
        result.errors.append("Header wajib minimal: subject, question_type, question_text.")
        return result

    for row_index, row_values in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        if not any(value not in (None, "") for value in row_values):
            continue
        row = {headers[idx]: row_values[idx] for idx in range(len(headers))}
        normalized = {key: ("" if value is None else str(value)) for key, value in row.items()}

        # Keep numeric values for exact parsing where available
        for numeric_key in ["points", "time_limit_seconds", "max_word_count"]:
            if numeric_key in row:
                normalized[numeric_key] = row[numeric_key]

        result.total_rows += 1
        try:
            _create_question_from_payload(normalized, teacher)
            result.success_count += 1
        except Exception as exc:
            result.errors.append(f"Baris Excel {row_index}: {exc}")

    return result


def export_template_headers():
    return [
        "subject",
        "category",
        "question_type",
        "question_text",
        "difficulty_level",
        "points",
        "explanation",
        "allow_previous",
        "allow_next",
        "force_sequential",
        "time_limit_seconds",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "option_e",
        "correct_option",
        "answer_text",
        "keywords",
        "is_case_sensitive",
        "max_word_count",
        "tags",
    ]
