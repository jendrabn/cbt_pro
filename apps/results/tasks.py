from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from apps.core.services import get_certificate_feature_settings
from apps.core.tasking import enqueue_task_or_run
from apps.notifications.models import Notification

from .certificate_generators import generate_certificate_pdf
from .models import Certificate


@shared_task(name="results.generate_certificate_pdf")
def generate_certificate_pdf_task(certificate_id: str):
    certificate = (
        Certificate.objects.filter(id=certificate_id)
        .select_related("student")
        .first()
    )
    if not certificate or certificate.is_revoked:
        return {"ok": False, "reason": "certificate_not_found_or_revoked"}

    try:
        pdf_path = generate_certificate_pdf(certificate, overwrite=True)
    except Exception as exc:  # pragma: no cover - external renderer specific
        if certificate.student_id:
            Notification.objects.create(
                user=certificate.student,
                title="Gagal membuat sertifikat",
                message=f"Terjadi kesalahan saat membuat PDF sertifikat: {exc}",
                notification_type=Notification.Type.ERROR,
                related_entity_type="certificate",
                related_entity_id=certificate.id,
            )
        return {"ok": False, "reason": str(exc)}

    certificate.pdf_file_path = pdf_path
    certificate.pdf_generated_at = timezone.now()
    try:
        certificate.certificate_url = default_storage.url(pdf_path)
    except Exception:
        certificate.certificate_url = ""
    certificate.save(update_fields=["pdf_file_path", "pdf_generated_at", "certificate_url", "updated_at"])

    if certificate.student_id:
        Notification.objects.create(
            user=certificate.student,
            title="Sertifikat siap diunduh",
            message=f"Sertifikat {certificate.certificate_number} telah siap diunduh.",
            notification_type=Notification.Type.SUCCESS,
            related_entity_type="certificate",
            related_entity_id=certificate.id,
        )

    feature_settings = get_certificate_feature_settings()
    if feature_settings.get("certificate_email_enabled", False) and certificate.student_id:
        enqueue_task_or_run(send_certificate_email_task, str(certificate.id))

    return {"ok": True, "certificate_id": str(certificate.id), "pdf_file_path": pdf_path}


@shared_task(name="results.send_certificate_email")
def send_certificate_email_task(certificate_id: str):
    certificate = (
        Certificate.objects.filter(id=certificate_id)
        .select_related("student", "exam")
        .first()
    )
    if not certificate:
        return {"ok": False, "reason": "certificate_not_found"}
    if not certificate.student_id or not (certificate.student.email or "").strip():
        return {"ok": False, "reason": "student_email_missing"}

    feature_settings = get_certificate_feature_settings()
    if not feature_settings.get("certificate_email_enabled", False):
        return {"ok": False, "reason": "email_feature_disabled"}

    student_name = certificate.student.get_full_name().strip() or certificate.student.username
    exam_title = certificate.exam.title if certificate.exam_id else "ujian"
    verify_url = reverse("certificate_verify_token", kwargs={"token": certificate.verification_token})
    download_url = (certificate.certificate_url or "").strip()

    subject = "Sertifikat CBT Siap Diunduh"
    lines = [
        f"Halo {student_name},",
        "",
        f"Sertifikat untuk {exam_title} sudah siap diunduh.",
        f"Nomor Sertifikat: {certificate.certificate_number}",
    ]
    if download_url:
        lines.append(f"URL Download: {download_url}")
    lines += [
        f"URL Verifikasi: {verify_url}",
        "",
        "Terima kasih.",
    ]
    message = "\n".join(lines)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[certificate.student.email],
            fail_silently=False,
        )
    except Exception as exc:  # pragma: no cover - backend specific
        if certificate.student_id:
            Notification.objects.create(
                user=certificate.student,
                title="Gagal mengirim email sertifikat",
                message=f"Email sertifikat gagal dikirim: {exc}",
                notification_type=Notification.Type.ERROR,
                related_entity_type="certificate",
                related_entity_id=certificate.id,
            )
        return {"ok": False, "reason": str(exc)}

    return {
        "ok": True,
        "certificate_id": str(certificate.id),
        "recipient": certificate.student.email,
    }
