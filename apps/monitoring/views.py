from __future__ import annotations

import json

from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.attempts.models import ExamViolation
from apps.core.mixins import RoleRequiredMixin

from .services import (
    build_monitoring_snapshot,
    build_student_detail_payload,
    extend_attempt_time,
    force_submit_attempt,
    get_teacher_exam_or_404,
    send_monitoring_announcement,
)


def _parse_payload(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            raw_body = request.body.decode("utf-8") if request.body else "{}"
            parsed = json.loads(raw_body)
            return parsed if isinstance(parsed, dict) else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
    return request.POST.dict()


def _json_error(message, status=400):
    return JsonResponse({"success": False, "message": message}, status=status)


class TeacherMonitoringBaseView(RoleRequiredMixin):
    required_role = "teacher"
    permission_denied_message = "Hanya guru yang dapat mengakses halaman monitoring siswa."


class MonitoringDashboardView(TeacherMonitoringBaseView, TemplateView):
    template_name = "monitoring/monitoring_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if getattr(request.user, "role", None) != "teacher":
            return super().dispatch(request, *args, **kwargs)
        self.exam = get_teacher_exam_or_404(kwargs["exam_id"], request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        snapshot = build_monitoring_snapshot(self.exam)
        student_placeholder = 1
        attempt_placeholder = "00000000-0000-0000-0000-000000000000"
        student_detail_url_template = reverse(
            "student_detail",
            kwargs={
                "exam_id": self.exam.id,
                "student_id": student_placeholder,
            },
        ).replace("/1/", "/__student_id__/")
        force_submit_url_template = reverse(
            "force_submit",
            kwargs={"attempt_id": attempt_placeholder},
        ).replace(attempt_placeholder, "__attempt_id__")
        context.update(
            {
                "exam": self.exam,
                "initial_snapshot": snapshot,
                "monitoring_config": {
                    "examId": str(self.exam.id),
                    "snapshotUrl": self.request.build_absolute_uri(
                        reverse("monitoring_snapshot", kwargs={"exam_id": self.exam.id})
                    ),
                    "studentDetailUrlTemplate": self.request.build_absolute_uri(
                        student_detail_url_template
                    ),
                    "extendTimeUrl": self.request.build_absolute_uri(
                        reverse("extend_time", kwargs={"exam_id": self.exam.id})
                    ),
                    "forceSubmitUrlTemplate": self.request.build_absolute_uri(
                        force_submit_url_template
                    ),
                    "announcementUrl": self.request.build_absolute_uri(
                        reverse("monitoring_announcement", kwargs={"exam_id": self.exam.id})
                    ),
                },
                "violation_types": ExamViolation.VIOLATION_TYPE_CHOICES,
            }
        )
        return context


class MonitoringSnapshotAPIView(TeacherMonitoringBaseView, View):
    def get(self, request, exam_id):
        exam = get_teacher_exam_or_404(exam_id, request.user)
        violation_type = (request.GET.get("violation_type") or "").strip()
        snapshot = build_monitoring_snapshot(exam, violation_type=violation_type)
        return JsonResponse(snapshot)


class StudentDetailView(TeacherMonitoringBaseView, View):
    def get(self, request, exam_id, student_id):
        exam = get_teacher_exam_or_404(exam_id, request.user)
        payload = build_student_detail_payload(exam, student_id)
        return JsonResponse(payload)


class ExtendTimeAPIView(TeacherMonitoringBaseView, View):
    def post(self, request, exam_id):
        exam = get_teacher_exam_or_404(exam_id, request.user)
        payload = _parse_payload(request)

        student_id = (payload.get("student_id") or "").strip()
        if not student_id:
            return _json_error("Parameter student_id wajib diisi.")

        raw_minutes = payload.get("minutes", 0)
        try:
            minutes = int(raw_minutes)
        except (TypeError, ValueError):
            return _json_error("Parameter minutes harus berupa angka bulat.")

        try:
            result = extend_attempt_time(exam, student_id=student_id, minutes=minutes)
        except ValueError as exc:
            return _json_error(str(exc))

        return JsonResponse({"success": True, "message": "Waktu berhasil ditambah.", "data": result})


class ForceSubmitAPIView(TeacherMonitoringBaseView, View):
    def post(self, request, attempt_id):
        try:
            result = force_submit_attempt(attempt_id=attempt_id, teacher=request.user)
        except ValueError as exc:
            return _json_error(str(exc))

        return JsonResponse({"success": True, "message": "Attempt berhasil dipaksa submit.", "data": result})


class MonitoringAnnouncementAPIView(TeacherMonitoringBaseView, View):
    def post(self, request, exam_id):
        exam = get_teacher_exam_or_404(exam_id, request.user)
        payload = _parse_payload(request)

        target = (payload.get("target") or "all").strip().lower()
        if target not in {"all", "student"}:
            return _json_error("Target pengumuman tidak valid.")

        title = payload.get("title") or ""
        message = payload.get("message") or ""
        student_id = (payload.get("student_id") or "").strip() or None

        try:
            result = send_monitoring_announcement(
                exam,
                title=title,
                message=message,
                target=target,
                student_id=student_id,
            )
        except ValueError as exc:
            return _json_error(str(exc))

        return JsonResponse(
            {
                "success": True,
                "message": f"Pengumuman berhasil dikirim ke {result['sent_count']} penerima.",
                "data": result,
            }
        )
