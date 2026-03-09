from __future__ import annotations

from decimal import Decimal

from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from apps.core.services import get_branding_settings, get_certificate_feature_settings
from apps.core.tasking import enqueue_task_or_run
from apps.notifications.models import Notification

from .certificate_utils import generate_certificate_number, generate_verification_token
from .models import Certificate, CertificateTemplate, ExamResult


FINISHED_STATUSES = ("submitted", "auto_submitted", "completed")


def _to_decimal(value, default="0.00"):
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _select_final_result(exam, result_rows):
    rows = list(result_rows or [])
    if not rows:
        return None, Decimal("0.00"), Decimal("0.00"), False

    policy = (exam.retake_score_policy or "highest").strip().lower()
    if policy == "latest":
        selected = max(rows, key=lambda row: int(row.attempt.attempt_number or 0))
        return selected, _to_decimal(selected.total_score), _to_decimal(selected.percentage), bool(selected.passed)

    if policy == "average":
        latest = max(rows, key=lambda row: int(row.attempt.attempt_number or 0))
        score = sum(_to_decimal(item.total_score) for item in rows) / len(rows)
        percentage = sum(_to_decimal(item.percentage) for item in rows) / len(rows)
        passed = percentage >= _to_decimal(exam.passing_score)
        return latest, score.quantize(Decimal("0.01")), percentage.quantize(Decimal("0.01")), bool(passed)

    selected = max(
        rows,
        key=lambda row: (
            float(row.total_score or 0),
            int(row.attempt.attempt_number or 0),
        ),
    )
    return selected, _to_decimal(selected.total_score), _to_decimal(selected.percentage), bool(selected.passed)


def _resolve_template(exam):
    if exam.certificate_template_id:
        return exam.certificate_template
    return CertificateTemplate.objects.filter(is_default=True).order_by("-updated_at").first()


def _serialize_template_payload(template):
    return {
        "layout_preset": template.layout_preset,
        "layout_type": template.layout_type,
        "paper_size": template.paper_size,
        "primary_color": template.primary_color,
        "secondary_color": template.secondary_color,
        "show_logo": template.show_logo,
        "show_score": template.show_score,
        "show_grade": template.show_grade,
        "show_rank": template.show_rank,
        "show_qr_code": template.show_qr_code,
        "qr_code_size": template.qr_code_size,
        "header_text": template.header_text or "",
        "body_text_template": template.body_text_template or "",
        "footer_text": template.footer_text or "",
        "signatory_name": template.signatory_name or "",
        "signatory_title": template.signatory_title or "",
        "signatory_signature_url": template.signatory_signature_url or "",
        "background_image_url": template.background_image_url or "",
    }


def _build_template_snapshot(exam):
    template = _resolve_template(exam)
    branding = get_branding_settings()
    if not template:
        return {
            "template": {
                "layout_preset": "classic_formal",
                "layout_type": "landscape",
                "paper_size": "A4",
                "primary_color": branding.get("primary_color", "#1A56DB"),
                "secondary_color": "#0E9F6E",
                "show_logo": True,
                "show_score": True,
                "show_grade": True,
                "show_rank": False,
                "show_qr_code": True,
                "qr_code_size": "M",
                "header_text": "SERTIFIKAT KELULUSAN",
                "body_text_template": "",
                "footer_text": "",
                "signatory_name": "",
                "signatory_title": "",
                "signatory_signature_url": "",
                "background_image_url": "",
            },
            "branding": branding,
            "source_template_id": None,
        }

    return {
        "template": _serialize_template_payload(template),
        "branding": branding,
        "source_template_id": str(template.id),
    }


def _notify(user, title, message, notification_type, certificate):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_entity_type="certificate",
        related_entity_id=certificate.id,
    )


def _generate_unique_certificate_number(prefix):
    for _ in range(20):
        number = generate_certificate_number(prefix=prefix, now=timezone.localtime())
        if not Certificate.objects.filter(certificate_number=number).exists():
            return number
    raise RuntimeError("Gagal menghasilkan nomor sertifikat unik.")


def _generate_unique_verification_token():
    for _ in range(20):
        token = generate_verification_token()
        if not Certificate.objects.filter(verification_token=token).exists():
            return token
    raise RuntimeError("Gagal menghasilkan token verifikasi unik.")


def check_eligibility_for_attempt(attempt):
    settings_data = get_certificate_feature_settings()
    if not settings_data.get("certificates_enabled", True):
        return {"eligible": False, "reason": "Fitur sertifikat nonaktif."}

    exam = attempt.exam
    if not exam.certificate_enabled:
        return {"eligible": False, "reason": "Sertifikat tidak diaktifkan untuk ujian ini."}

    result_rows = list(
        ExamResult.objects.filter(
            exam=exam,
            student=attempt.student,
            attempt__status__in=FINISHED_STATUSES,
        ).select_related("attempt")
    )
    selected_result, final_score, final_percentage, passed = _select_final_result(exam, result_rows)
    if not selected_result:
        return {"eligible": False, "reason": "Hasil ujian final belum tersedia."}
    if not passed:
        return {"eligible": False, "reason": "Nilai final belum mencapai passing score."}

    active_exists = Certificate.objects.filter(
        exam_id=exam.id,
        student_id=attempt.student_id,
        revoked_at__isnull=True,
        is_valid=True,
    ).exists()
    if active_exists:
        return {"eligible": False, "reason": "Sertifikat aktif sudah tersedia untuk ujian ini."}

    return {
        "eligible": True,
        "reason": "",
        "selected_result": selected_result,
        "final_score": final_score.quantize(Decimal("0.01")),
        "final_percentage": final_percentage.quantize(Decimal("0.01")),
    }


@transaction.atomic
def issue_certificate_for_attempt(attempt):
    eligibility = check_eligibility_for_attempt(attempt)
    if not eligibility.get("eligible"):
        return None, eligibility

    selected_result = eligibility["selected_result"]
    settings_data = get_certificate_feature_settings()
    prefix = settings_data.get("certificate_number_prefix", "CERT")
    certificate_number = _generate_unique_certificate_number(prefix=prefix)
    verification_token = _generate_unique_verification_token()
    template_snapshot = _build_template_snapshot(attempt.exam)

    certificate = Certificate.objects.create(
        result=selected_result,
        attempt=selected_result.attempt,
        exam=attempt.exam,
        student=attempt.student,
        certificate_number=certificate_number,
        verification_token=verification_token,
        issued_at=timezone.now(),
        revoked_at=None,
        revoked_reason="",
        final_score=eligibility["final_score"],
        final_percentage=eligibility["final_percentage"],
        template_snapshot=template_snapshot,
        pdf_file_path="",
        pdf_generated_at=None,
        is_valid=True,
        certificate_url="",
    )

    _notify(
        attempt.student,
        "Sertifikat sedang diproses",
        f"Sertifikat untuk ujian '{attempt.exam.title}' sedang dibuat.",
        Notification.Type.INFO,
        certificate,
    )

    from .tasks import generate_certificate_pdf_task

    enqueue_task_or_run(generate_certificate_pdf_task, str(certificate.id))
    return certificate, eligibility


@transaction.atomic
def revoke_certificate(certificate, revoked_by, reason):
    certificate.revoked_at = timezone.now()
    certificate.revoked_by = revoked_by
    certificate.revoked_reason = (reason or "").strip()
    certificate.is_valid = False
    certificate.save(
        update_fields=["revoked_at", "revoked_by", "revoked_reason", "is_valid", "updated_at"]
    )

    if certificate.student_id:
        _notify(
            certificate.student,
            "Sertifikat dicabut",
            f"Sertifikat {certificate.certificate_number} telah dicabut.",
            Notification.Type.WARNING,
            certificate,
        )
    return certificate


def issue_missing_certificates_for_exam(exam):
    issued = 0
    skipped = 0
    for student_id in (
        ExamResult.objects.filter(exam=exam)
        .values_list("student_id", flat=True)
        .distinct()
    ):
        latest_attempt = (
            exam.attempts.filter(student_id=student_id, status__in=FINISHED_STATUSES)
            .order_by("-attempt_number", "-created_at")
            .first()
        )
        if not latest_attempt:
            skipped += 1
            continue
        certificate, meta = issue_certificate_for_attempt(latest_attempt)
        if certificate:
            issued += 1
        else:
            skipped += 1
    return {"issued": issued, "skipped": skipped}


def get_certificate_for_result(result):
    certificate = (
        Certificate.objects.filter(result_id=result.id)
        .order_by("-issued_at", "-created_at")
        .first()
    )
    if certificate:
        return certificate

    certificate = (
        Certificate.objects.filter(attempt_id=result.attempt_id)
        .order_by("-issued_at", "-created_at")
        .first()
    )
    if certificate:
        return certificate
    return (
        Certificate.objects.filter(exam_id=result.exam_id, student_id=result.student_id)
        .order_by("-issued_at", "-created_at")
        .first()
    )


def get_certificate_download_url(certificate):
    if not certificate or not certificate.is_active:
        return ""
    if certificate.pdf_file_path:
        try:
            return default_storage.url(certificate.pdf_file_path)
        except Exception:
            return ""
    return (certificate.certificate_url or "").strip()


def certificate_state_label(certificate):
    if not certificate:
        return "hidden"
    if certificate.revoked_at or not certificate.is_valid:
        return "revoked"
    if certificate.pdf_generated_at and certificate.pdf_file_path:
        return "active"
    if certificate.certificate_url:
        return "active"
    return "loading"


def queue_regenerate_certificates_for_template(template):
    source_id = str(template.id)
    queryset = Certificate.objects.filter(is_valid=True, revoked_at__isnull=True)
    matched = 0
    queued = 0
    skipped = 0

    from .tasks import generate_certificate_pdf_task

    for certificate in queryset:
        snapshot = dict(certificate.template_snapshot or {})
        if str(snapshot.get("source_template_id") or "") != source_id:
            continue

        matched += 1
        snapshot["template"] = _serialize_template_payload(template)
        snapshot["source_template_id"] = source_id
        certificate.template_snapshot = snapshot
        certificate.pdf_file_path = ""
        certificate.certificate_url = ""
        certificate.pdf_generated_at = None
        certificate.save(
            update_fields=[
                "template_snapshot",
                "pdf_file_path",
                "certificate_url",
                "pdf_generated_at",
                "updated_at",
            ]
        )

        try:
            enqueue_task_or_run(generate_certificate_pdf_task, str(certificate.id))
            queued += 1
        except Exception:
            skipped += 1

    return {
        "matched": matched,
        "queued": queued,
        "skipped": skipped,
    }
