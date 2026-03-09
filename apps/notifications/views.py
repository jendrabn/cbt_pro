from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from .models import Notification


def _safe_next_url(request, fallback):
    candidate = (
        request.POST.get("next")
        or request.GET.get("next")
        or ""
    ).strip()
    if candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return fallback


def _role_layout_meta(user):
    role = str(getattr(user, "role", "") or "").strip().lower()
    if role == "admin":
        return {
            "base_layout": "layouts/base_admin.html",
            "topbar_partial": "partials/topbar_admin.html",
            "eyebrow": "Panel Admin",
        }
    if role == "teacher":
        return {
            "base_layout": "layouts/base_teacher.html",
            "topbar_partial": "partials/topbar_teacher.html",
            "eyebrow": "Panel Guru",
        }
    return {
        "base_layout": "layouts/base_student.html",
        "topbar_partial": "partials/topbar_student.html",
        "eyebrow": "Panel Siswa",
    }


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            Notification.objects.filter(user=self.request.user)
            .order_by("-created_at")
        )
        status = (self.request.GET.get("status") or "").strip().lower()
        if status == "unread":
            queryset = queryset.filter(is_read=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_qs = Notification.objects.filter(user=self.request.user)
        active_filter = (self.request.GET.get("status") or "all").strip().lower()
        if active_filter not in {"all", "unread"}:
            active_filter = "all"

        context.update(
            {
                "active_filter": active_filter,
                "all_count": all_qs.count(),
                "unread_count": all_qs.filter(is_read=False).count(),
                "role_layout": _role_layout_meta(self.request.user),
            }
        )
        return context


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        now = timezone.now()
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=now,
            updated_at=now,
        )
        return HttpResponseRedirect(
            _safe_next_url(request, reverse("notification_list"))
        )


class NotificationMarkReadView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, notification_id, *args, **kwargs):
        now = timezone.now()
        Notification.objects.filter(
            id=notification_id,
            user=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=now,
            updated_at=now,
        )
        return HttpResponseRedirect(
            _safe_next_url(request, reverse("notification_list"))
        )
