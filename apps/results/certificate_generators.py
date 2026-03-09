from __future__ import annotations

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.core.services import get_branding_settings, get_certificate_feature_settings

from .certificate_utils import render_template_text


DEFAULT_HEADER_TEXT = "SERTIFIKAT KELULUSAN"
DEFAULT_BODY_TEMPLATE = """
Diberikan kepada:

{{ student_full_name }}
{{ class_grade }}

Telah berhasil menyelesaikan:
"{{ exam_title }}"
Mata Pelajaran: {{ subject_name }}

Nilai Akhir: {{ final_score }} ({{ percentage }}%)
Grade: {{ grade }}

No. Sertifikat: {{ certificate_number }}
"""


def _resolve_layout_preset(template_data: dict) -> str:
    preset = str(template_data.get("layout_preset") or "").strip()
    valid = {"classic_formal", "modern_minimal", "portrait_achievement"}
    if preset in valid:
        return preset
    if str(template_data.get("layout_type") or "").strip() == "portrait":
        return "portrait_achievement"
    return "classic_formal"


def _grade_from_percentage(percentage_value: float) -> str:
    value = float(percentage_value or 0)
    if value >= 90:
        return "A"
    if value >= 80:
        return "B"
    if value >= 70:
        return "C"
    if value >= 60:
        return "D"
    return "E"


def build_certificate_context(certificate):
    exam = certificate.exam or (certificate.attempt.exam if certificate.attempt_id else None)
    student = certificate.student or (certificate.attempt.student if certificate.attempt_id else None)
    subject_name = exam.subject.name if exam and exam.subject_id else "-"
    profile = getattr(student, "profile", None) if student else None

    branding = get_branding_settings()
    snapshot = dict(certificate.template_snapshot or {})
    template_data = dict(snapshot.get("template") or {})
    branding_data = dict(snapshot.get("branding") or {})
    merged_branding = {**branding, **branding_data}
    layout_preset = _resolve_layout_preset(template_data)
    layout_type = template_data.get("layout_type", "landscape")
    if layout_preset == "portrait_achievement":
        layout_type = "portrait"

    issued_local = timezone.localtime(certificate.issued_at)
    grade_value = ""
    if certificate.result_id and certificate.result and certificate.result.grade:
        grade_value = certificate.result.grade
    if not grade_value:
        grade_value = _grade_from_percentage(float(certificate.final_percentage or 0))

    placeholders = {
        "student_full_name": student.get_full_name() if student else "-",
        "student_id": getattr(profile, "student_id", "") if profile else "",
        "class_grade": getattr(profile, "class_grade", "") if profile else "",
        "exam_title": exam.title if exam else "-",
        "subject_name": subject_name,
        "final_score": f"{float(certificate.final_score or 0):.2f}",
        "percentage": f"{float(certificate.final_percentage or 0):.2f}",
        "grade": grade_value,
        "issued_date": issued_local.strftime("%d %B %Y"),
        "certificate_number": certificate.certificate_number,
        "institution_name": merged_branding.get("institution_name") or "",
        "institution_type": merged_branding.get("institution_type") or "",
        "signatory_name": template_data.get("signatory_name") or "",
        "signatory_title": template_data.get("signatory_title") or "",
        "exam_date": timezone.localtime(exam.end_time).strftime("%d %B %Y") if exam and exam.end_time else "",
        "verification_url": reverse("certificate_verify_token", kwargs={"token": certificate.verification_token}),
    }

    body_template = template_data.get("body_text_template") or DEFAULT_BODY_TEMPLATE
    body_text = render_template_text(body_template, placeholders)

    return {
        "certificate": certificate,
        "exam": exam,
        "student": student,
        "branding": merged_branding,
        "template": {
            "layout_preset": layout_preset,
            "layout_type": layout_type,
            "paper_size": template_data.get("paper_size", "A4"),
            "primary_color": template_data.get("primary_color", "#1A56DB"),
            "secondary_color": template_data.get("secondary_color", "#0E9F6E"),
            "show_logo": template_data.get("show_logo", True),
            "show_score": template_data.get("show_score", True),
            "show_grade": template_data.get("show_grade", True),
            "show_rank": template_data.get("show_rank", False),
            "show_qr_code": template_data.get("show_qr_code", True),
            "qr_code_size": template_data.get("qr_code_size", "M"),
            "header_text": template_data.get("header_text") or DEFAULT_HEADER_TEXT,
            "footer_text": template_data.get("footer_text") or "",
            "background_image_url": template_data.get("background_image_url") or "",
            "signatory_name": template_data.get("signatory_name") or "",
            "signatory_title": template_data.get("signatory_title") or "",
            "signatory_signature_url": template_data.get("signatory_signature_url") or "",
        },
        "placeholders": placeholders,
        "body_text": body_text,
        "verification_url": placeholders["verification_url"],
    }


def render_certificate_html(certificate) -> str:
    context = build_certificate_context(certificate)
    return render_to_string("certificates/certificate_pdf.html", context=context)


def generate_certificate_pdf(certificate, overwrite=False) -> str:
    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover - depends on system libs
        raise RuntimeError(
            "WeasyPrint tidak siap. Pastikan dependensi sistem untuk render PDF terpasang."
        ) from exc

    html = render_certificate_html(certificate)
    pdf_bytes = HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()

    feature_settings = get_certificate_feature_settings()
    base_path = str(feature_settings.get("certificate_storage_path") or "certificates/").strip()
    if not base_path.endswith("/"):
        base_path += "/"
    relative_path = f"{base_path}{certificate.student_id}/{certificate.certificate_number}.pdf"
    if overwrite and default_storage.exists(relative_path):
        default_storage.delete(relative_path)
    return default_storage.save(relative_path, ContentFile(pdf_bytes))
