from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook

from .importers import export_template_headers


def _safe_timestamp():
    return timezone.localtime().strftime("%Y%m%d_%H%M%S")


def _question_to_export_row(question):
    option_map = {option.option_letter: option for option in question.options.all()}
    correct_option = ""
    for letter, option in option_map.items():
        if option.is_correct:
            correct_option = letter
            break

    answer = getattr(question, "correct_answer", None)
    tags = [relation.tag.name for relation in question.questiontagrelation_set.all()]

    return {
        "id": str(question.id),
        "subject": question.subject.name if question.subject_id else "",
        "category": question.category.name if question.category_id else "",
        "question_type": question.question_type,
        "question_text": question.question_text,
        "difficulty_level": question.difficulty_level or "",
        "points": float(question.points),
        "explanation": question.explanation or "",
        "question_image_url": question.question_image_url or "",
        "allow_previous": question.allow_previous,
        "allow_next": question.allow_next,
        "force_sequential": question.force_sequential,
        "time_limit_seconds": question.time_limit_seconds or "",
        "option_a": option_map.get("A").option_text if option_map.get("A") else "",
        "option_b": option_map.get("B").option_text if option_map.get("B") else "",
        "option_c": option_map.get("C").option_text if option_map.get("C") else "",
        "option_d": option_map.get("D").option_text if option_map.get("D") else "",
        "option_e": option_map.get("E").option_text if option_map.get("E") else "",
        "correct_option": correct_option,
        "answer_text": answer.answer_text if answer else "",
        "keywords": ", ".join(answer.keywords or []) if answer else "",
        "is_case_sensitive": bool(answer.is_case_sensitive) if answer else False,
        "max_word_count": answer.max_word_count if answer and answer.max_word_count else "",
        "tags": ", ".join(tags),
        "is_active": question.is_active,
        "created_at": timezone.localtime(question.created_at).isoformat() if isinstance(question.created_at, datetime) else "",
        "updated_at": timezone.localtime(question.updated_at).isoformat() if isinstance(question.updated_at, datetime) else "",
    }


def export_questions_to_json(queryset):
    rows = [_question_to_export_row(question) for question in queryset]
    response = HttpResponse(
        json.dumps({"questions": rows}, ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    response["Content-Disposition"] = f'attachment; filename="bank_soal_{_safe_timestamp()}.json"'
    return response


def export_questions_to_excel(queryset):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Bank Soal"

    headers = export_template_headers() + ["is_active", "question_image_url", "created_at", "updated_at"]
    worksheet.append(headers)

    for question in queryset:
        row = _question_to_export_row(question)
        worksheet.append([row.get(header, "") for header in headers])

    buffer = BytesIO()
    workbook.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="bank_soal_{_safe_timestamp()}.xlsx"'
    return response


def export_import_template_excel():
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Template Import"
    headers = export_template_headers()
    worksheet.append(headers)
    worksheet.append(
        [
            "Matematika",
            "Aljabar",
            "multiple_choice",
            "Hasil dari 2 + 2 adalah ...",
            "easy",
            5,
            "Operasi penjumlahan dasar.",
            True,
            True,
            False,
            "",
            "3",
            "4",
            "5",
            "",
            "",
            "B",
            "",
            "",
            False,
            "",
            "aljabar, dasar",
        ]
    )

    buffer = BytesIO()
    workbook.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="template_import_bank_soal.xlsx"'
    return response
