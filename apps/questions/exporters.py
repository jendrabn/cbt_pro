from __future__ import annotations

from datetime import datetime
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from apps.subjects.models import Subject

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


def export_questions_to_excel(queryset):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Bank Soal"

    headers = export_template_headers() + ["created_at", "updated_at"]
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
            "",
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
            True,
        ]
    )

    guide = workbook.create_sheet("Panduan")
    guide.append(["Kolom", "Wajib", "Aturan Nilai"])
    subject_names = list(Subject.objects.filter(is_active=True).order_by("name").values_list("name", flat=True))
    subject_text = ", ".join(subject_names) if subject_names else "-"
    guide_rows = [
        ("subject", "YA", f"Nama/kode subject aktif. Daftar subject: {subject_text}"),
        ("question_type", "YA", "multiple_choice, essay, short_answer"),
        ("question_text", "YA", "Teks soal"),
        ("difficulty_level", "TIDAK", "easy, medium, hard"),
        ("question_image_url", "TIDAK", "URL gambar soal jika ada"),
        ("allow_previous", "TIDAK", "TRUE atau FALSE"),
        ("allow_next", "TIDAK", "TRUE atau FALSE"),
        ("force_sequential", "TIDAK", "TRUE atau FALSE"),
        ("is_case_sensitive", "TIDAK", "TRUE atau FALSE (khusus short_answer)"),
        ("correct_option", "KONDISIONAL", "A/B/C/D/E untuk multiple_choice"),
        ("answer_text", "KONDISIONAL", "Wajib untuk essay/short_answer"),
        ("is_active", "TIDAK", "TRUE atau FALSE"),
    ]
    for row in guide_rows:
        guide.append(list(row))
    for col_idx in range(1, 4):
        guide.column_dimensions[guide.cell(row=1, column=col_idx).column_letter].width = 48 if col_idx == 3 else 24

    buffer = BytesIO()
    workbook.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="template_import_bank_soal.xlsx"'
    return response


def export_import_report_excel(import_log) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Laporan Import"

    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    success_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    skip_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    error_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    headers = ["No", "Baris Excel", "Status", "Keterangan"]
    for col_idx, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    widths = [10, 14, 14, 60]
    for col_idx, width in enumerate(widths, start=1):
        worksheet.column_dimensions[worksheet.cell(row=1, column=col_idx).column_letter].width = width

    rows_data = []
    for error in import_log.error_details or []:
        rows_data.append(
            {
                "row": error.get("row", "-"),
                "status": "error",
                "message": error.get("error", ""),
            }
        )
    for skip in import_log.skip_details or []:
        rows_data.append(
            {
                "row": skip.get("row", "-"),
                "status": "skip",
                "message": skip.get("reason", ""),
            }
        )

    if not rows_data:
        rows_data.append(
            {
                "row": "-",
                "status": "success",
                "message": "Tidak ada baris yang gagal atau dilewati pada import ini.",
            }
        )

    status_labels = {
        "success": "Berhasil",
        "skip": "Dilewati",
        "error": "Gagal",
    }
    status_fills = {
        "success": success_fill,
        "skip": skip_fill,
        "error": error_fill,
    }

    for row_idx, row_data in enumerate(rows_data, start=2):
        fill = status_fills.get(row_data["status"], success_fill)
        worksheet.cell(row=row_idx, column=1, value=row_idx - 1)
        worksheet.cell(row=row_idx, column=2, value=row_data.get("row", "-"))
        worksheet.cell(row=row_idx, column=3, value=status_labels.get(row_data["status"], row_data["status"]))
        worksheet.cell(row=row_idx, column=4, value=row_data.get("message", ""))

        for col_idx in range(1, len(headers) + 1):
            worksheet.cell(row=row_idx, column=col_idx).fill = fill

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
