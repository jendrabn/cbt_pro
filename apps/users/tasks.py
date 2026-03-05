from __future__ import annotations

import logging
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

User = get_user_model()

try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    def shared_task(func):
        def delay(*args, **kwargs):
            return func(*args, **kwargs)
        func.delay = delay
        return func


@shared_task
def send_import_credentials_email(user_ids: List[str], admin_username: str = "admin"):
    """
    Send credential emails to newly imported users.
    
    Args:
        user_ids: List of user UUIDs (as strings)
        admin_username: Username of the admin who performed the import
    """
    if not user_ids:
        logger.info("No users to send credentials email to")
        return
    
    users = User.objects.filter(id__in=user_ids)
    sent_count = 0
    failed_count = 0
    
    for user in users:
        try:
            temp_password = getattr(user, '_import_temp_password', None)
            if not temp_password:
                logger.warning(f"No temp password found for user {user.username}, skipping email")
                continue
            
            subject = "Informasi Akun CBT - Kredensial Login"
            message = (
                f"Halo {user.get_full_name()},\n\n"
                f"Akun CBT Anda telah dibuat oleh {admin_username}.\n\n"
                f"Detail Login:\n"
                f"Username: {user.username}\n"
                f"Email: {user.email}\n"
                f"Password: {temp_password}\n\n"
                f"Silakan login ke sistem CBT dan segera ubah password Anda untuk keamanan.\n\n"
                f"Terima kasih."
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
                fail_silently=False,
            )
            sent_count += 1
            logger.info(f"Credentials email sent to {user.email}")
        except Exception as exc:
            failed_count += 1
            logger.error(f"Failed to send credentials email to {user.email}: {exc}")
    
    logger.info(f"Credentials email task completed: {sent_count} sent, {failed_count} failed")
    return {"sent": sent_count, "failed": failed_count}


def queue_credentials_email(user_ids: List[str], admin_username: str = "admin"):
    """
    Queue the credentials email task.
    Uses Celery if available, otherwise runs synchronously.
    """
    if CELERY_AVAILABLE:
        send_import_credentials_email.delay(user_ids, admin_username)
    else:
        send_import_credentials_email(user_ids, admin_username)
