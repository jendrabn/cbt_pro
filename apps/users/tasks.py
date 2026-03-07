from __future__ import annotations

import logging
from typing import Any, List

from django.conf import settings
from django.core.mail import send_mail

from apps.core.tasking import enqueue_task_or_run

logger = logging.getLogger(__name__)

try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        def delay(*args, **kwargs):
            return func(*args, **kwargs)
        func.delay = delay
        return func


@shared_task
def send_import_credentials_email(credentials: List[dict[str, Any]], admin_username: str = "admin"):
    """
    Send credential emails to newly imported users.
    """
    if not credentials:
        logger.info("No users to send credentials email to")
        return

    sent_count = 0
    failed_count = 0

    for item in credentials:
        email = item.get("email", "")
        username = item.get("username", "")
        temp_password = item.get("temp_password", "")
        full_name = item.get("full_name", username).strip() or username
        try:
            if not temp_password:
                logger.warning("No temp password found for user %s, skipping email", username)
                continue

            subject = "Informasi Akun CBT - Kredensial Login"
            message = (
                f"Halo {full_name},\n\n"
                f"Akun CBT Anda telah dibuat oleh {admin_username}.\n\n"
                f"Detail Login:\n"
                f"Username: {username}\n"
                f"Email: {email}\n"
                f"Password: {temp_password}\n\n"
                f"Silakan login ke sistem CBT dan segera ubah password Anda untuk keamanan.\n\n"
                f"Terima kasih."
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[email],
                fail_silently=False,
            )
            sent_count += 1
            logger.info("Credentials email sent to %s", email)
        except Exception as exc:
            failed_count += 1
            logger.error("Failed to send credentials email to %s: %s", email, exc)

    logger.info("Credentials email task completed: %s sent, %s failed", sent_count, failed_count)
    return {"sent": sent_count, "failed": failed_count}


def queue_credentials_email(credentials: List[dict[str, Any]], admin_username: str = "admin"):
    """
    Queue the credentials email task and fall back to synchronous execution
    when the broker is unavailable.
    """
    return enqueue_task_or_run(send_import_credentials_email, credentials, admin_username)
