from __future__ import annotations

from .models import Notification


def topbar_notifications(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {
            "topbar_notifications": [],
            "topbar_notification_unread_count": 0,
        }

    queryset = Notification.objects.filter(user=user).order_by("-created_at")
    return {
        "topbar_notifications": list(queryset[:6]),
        "topbar_notification_unread_count": queryset.filter(is_read=False).count(),
    }
