from __future__ import annotations

import json
from datetime import timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.core.mixins import RoleRequiredMixin
from apps.results.models import ExamResult

from .models import ExamAttempt, StudentAnswer
from .services import (
    CooldownActive,
    LIST_TABS,
    MaxAttemptsReached,
    RetakeNotAllowed,
    apply_exam_list_filters,
    auto_submit_if_time_expired,
    build_exam_card_rows,
    build_exam_room_payload,
    build_exam_submit_summary,
    check_retake_eligibility,
    create_retake_attempt,
    get_exam_subject_options,
    get_attempt_history_for_exam,
    get_latest_attempt_for_exam,
    get_student_assigned_exam_queryset,
    parse_exam_list_filters,
    record_exam_violation,
    record_proctoring_capture,
    save_attempt_answer,
    submit_attempt,
)


def _querystring_without(request, keys):
    querydict = request.GET.copy()
    for key in keys:
        querydict.pop(key, None)
    return querydict.urlencode()


def _resolve_exam_for_student(student, exam_id):
    queryset = get_student_assigned_exam_queryset(student)
    return get_object_or_404(queryset, id=exam_id)


def _resolve_attempt_for_student(student, attempt_id):
    return get_object_or_404(
        ExamAttempt.objects.select_related("exam", "exam__subject"),
        id=attempt_id,
        student=student,
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


def _json_error(message, status=400, **extra):
    payload = {"success": False, "message": message}
    payload.update(extra)
    return JsonResponse(payload, status=status)


class StudentAttemptBaseView(RoleRequiredMixin):
    required_role = "student"
    permission_denied_message = "Hanya siswa yang dapat mengakses halaman ujian."


class StudentAttemptAPIBaseView(StudentAttemptBaseView):
    def get_attempt(self, attempt_id):
        return _resolve_attempt_for_student(self.request.user, attempt_id)


class ExamListView(StudentAttemptBaseView, TemplateView):
    template_name = "attempts/exam_list.html"
    tab_labels = {
        "upcoming": "Akan Datang",
        "ongoing": "Sedang Berlangsung",
        "completed": "Selesai",
        "missed": "Terlewat",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = parse_exam_list_filters(self.request)
        assigned_qs = get_student_assigned_exam_queryset(self.request.user)
        subjects = get_exam_subject_options(assigned_qs)
        filtered_qs = apply_exam_list_filters(assigned_qs, filters)

        rows, tab_counts = build_exam_card_rows(
            student=self.request.user,
            exams_qs=filtered_qs,
            selected_tab=filters.tab,
        )

        query_without_tab = _querystring_without(self.request, ["tab"])
        tab_urls = {}
        for tab in LIST_TABS:
            if query_without_tab:
                tab_urls[tab] = f"?{query_without_tab}&tab={tab}"
            else:
                tab_urls[tab] = f"?tab={tab}"

        context.update(
            {
                "filters": filters,
                "subjects": subjects,
                "exam_rows": rows,
                "tab_counts": tab_counts,
                "tab_urls": tab_urls,
                "active_tab": filters.tab,
                "tab_labels": self.tab_labels,
                "active_tab_label": self.tab_labels.get(filters.tab, "Akan Datang"),
            }
        )
        return context


class ExamStartView(StudentAttemptBaseView, TemplateView):
    template_name = "attempts/exam_start.html"

    def _can_start(self, exam):
        now = timezone.now()
        return exam.start_time <= now <= exam.end_time and exam.status in {"published", "ongoing"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = _resolve_exam_for_student(self.request.user, self.kwargs["exam_id"])
        latest_attempt = get_latest_attempt_for_exam(exam, self.request.user)

        context.update(
            {
                "exam": exam,
                "latest_attempt": latest_attempt,
                "can_start_now": self._can_start(exam),
                "back_url": reverse("student_exam_list"),
            }
        )
        return context

    def post(self, request, exam_id):
        exam = _resolve_exam_for_student(request.user, exam_id)
        now = timezone.now()
        if not self._can_start(exam):
            messages.warning(request, "Ujian belum bisa dimulai atau waktu ujian sudah berakhir.")
            return redirect("student_exam_list")

        latest_attempt = get_latest_attempt_for_exam(exam, request.user)
        if latest_attempt and latest_attempt.status in {"submitted", "auto_submitted", "completed", "grading"}:
            messages.info(request, "Anda sudah menyelesaikan ujian ini.")
            return redirect("exam_submit", attempt_id=latest_attempt.id)

        if latest_attempt:
            attempt = latest_attempt
            attempt.status = "in_progress"
            if not attempt.start_time:
                attempt.start_time = now
            if not attempt.end_time:
                deadline = now + timedelta(minutes=exam.duration_minutes)
                attempt.end_time = min(deadline, exam.end_time)
            attempt.save(update_fields=["status", "start_time", "end_time", "updated_at"])
        else:
            deadline = now + timedelta(minutes=exam.duration_minutes)
            attempt = ExamAttempt.objects.create(
                exam=exam,
                student=request.user,
                attempt_number=1,
                start_time=now,
                end_time=min(deadline, exam.end_time),
                status="in_progress",
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:1000],
            )

        messages.success(request, "Ujian berhasil dimulai.")
        return redirect("exam_room", exam_id=exam.id)


class ExamRoomView(StudentAttemptBaseView, TemplateView):
    template_name = "attempts/exam_room.html"

    def get(self, request, exam_id, *args, **kwargs):
        exam = _resolve_exam_for_student(request.user, exam_id)
        attempt = get_latest_attempt_for_exam(exam, request.user)
        if not attempt:
            messages.warning(request, "Attempt belum tersedia. Silakan mulai ujian dari daftar ujian.")
            return redirect("student_exam_list")

        if attempt.status in {"submitted", "auto_submitted", "completed", "grading"}:
            return redirect("exam_submit", attempt_id=attempt.id)

        if attempt.status == "not_started":
            now = timezone.now()
            attempt.status = "in_progress"
            if not attempt.start_time:
                attempt.start_time = now
            if not attempt.end_time:
                deadline = now + timedelta(minutes=exam.duration_minutes)
                attempt.end_time = min(deadline, exam.end_time)
            attempt.save(update_fields=["status", "start_time", "end_time", "updated_at"])

        attempt, is_auto_submitted, _ = auto_submit_if_time_expired(exam=exam, attempt=attempt)
        if is_auto_submitted:
            messages.warning(request, "Waktu ujian habis dan ujian Anda sudah disubmit otomatis.")
            return redirect("exam_submit", attempt_id=attempt.id)

        initial_payload = build_exam_room_payload(
            exam=exam,
            attempt=attempt,
            current_number=0,
        )

        number_placeholder = 999999
        question_url_template = reverse(
            "attempt_question_api",
            kwargs={"attempt_id": attempt.id, "number": number_placeholder},
        ).replace(str(number_placeholder), "__number__")

        context = self.get_context_data(**kwargs)
        context.update(
            {
                "exam": exam,
                "attempt": attempt,
                "back_url": reverse("student_exam_list"),
                "exam_room_config": {
                    "attemptId": str(attempt.id),
                    "examId": str(exam.id),
                    "questionUrlTemplate": question_url_template,
                    "saveAnswerUrl": reverse("attempt_save_answer_api", kwargs={"attempt_id": attempt.id}),
                    "submitUrl": reverse("attempt_submit_api", kwargs={"attempt_id": attempt.id}),
                    "violationUrl": reverse("attempt_violation_api", kwargs={"attempt_id": attempt.id}),
                    "proctoringUrl": reverse("attempt_proctoring_api", kwargs={"attempt_id": attempt.id}),
                    "submitRedirectUrl": reverse("exam_submit", kwargs={"attempt_id": attempt.id}),
                    "initialPayload": initial_payload,
                },
            }
        )
        return self.render_to_response(context)


class ExamSubmitConfirmationView(StudentAttemptBaseView, TemplateView):
    template_name = "attempts/exam_submit_confirmation.html"

    def get(self, request, attempt_id):
        attempt = _resolve_attempt_for_student(request.user, attempt_id)
        if attempt.status not in {"submitted", "auto_submitted", "completed", "grading"}:
            messages.info(request, "Ujian belum disubmit. Silakan lanjutkan pengerjaan.")
            return redirect("exam_room", exam_id=attempt.exam_id)

        summary = build_exam_submit_summary(attempt.exam, attempt)
        context = self.get_context_data()
        context.update(
            {
                "attempt": attempt,
                "exam": attempt.exam,
                "summary": summary,
                "back_url": reverse("student_exam_list"),
                "retake_eligibility": check_retake_eligibility(attempt.exam_id, request.user.id),
            }
        )
        return self.render_to_response(context)


class AttemptQuestionAPIView(StudentAttemptAPIBaseView, View):
    http_method_names = ["get"]

    def get(self, request, attempt_id, number):
        attempt = self.get_attempt(attempt_id)
        exam = attempt.exam

        attempt, is_auto_submitted, _ = auto_submit_if_time_expired(exam=exam, attempt=attempt)
        if is_auto_submitted:
            return _json_error(
                "Waktu ujian habis. Ujian disubmit otomatis.",
                status=409,
                redirect_url=reverse("exam_submit", kwargs={"attempt_id": attempt.id}),
            )

        current_number = request.GET.get("current_number")
        payload = build_exam_room_payload(
            exam=exam,
            attempt=attempt,
            current_number=int(current_number) if str(current_number).isdigit() else 1,
            requested_number=number,
            enforce_navigation=True,
        )

        message = ""
        if int(payload.get("current_number") or 0) != int(number):
            message = payload.get("notice") or "Navigasi soal tidak diizinkan oleh aturan ujian."

        return JsonResponse({"success": True, "message": message, "payload": payload})


class SaveAnswerAPIView(StudentAttemptAPIBaseView, View):
    http_method_names = ["post"]

    def post(self, request, attempt_id):
        attempt = self.get_attempt(attempt_id)
        payload = _parse_payload(request)
        question_number_raw = payload.get("question_number")
        try:
            question_number = int(question_number_raw)
        except (TypeError, ValueError):
            return _json_error("Parameter question_number wajib berupa angka.")

        try:
            result = save_attempt_answer(
                exam=attempt.exam,
                attempt=attempt,
                question_number=question_number,
                payload=payload,
            )
        except ValueError as exc:
            return _json_error(str(exc))

        if result["auto_submitted"]:
            return JsonResponse(
                {
                    "success": False,
                    "auto_submitted": True,
                    "message": result["message"],
                    "payload": result["payload"],
                    "redirect_url": reverse("exam_submit", kwargs={"attempt_id": attempt.id}),
                },
                status=409,
            )

        return JsonResponse(
            {
                "success": True,
                "message": result["message"],
                "payload": result["payload"],
            }
        )


class SubmitAttemptAPIView(StudentAttemptAPIBaseView, View):
    http_method_names = ["post"]

    def post(self, request, attempt_id):
        attempt = self.get_attempt(attempt_id)
        submission = submit_attempt(
            exam=attempt.exam,
            attempt=attempt,
            auto_submit=False,
        )
        return JsonResponse(
            {
                "success": True,
                "message": "Ujian berhasil dikumpulkan.",
                "summary": submission["summary"],
                "redirect_url": reverse("exam_submit", kwargs={"attempt_id": attempt.id}),
            }
        )


class AttemptViolationAPIView(StudentAttemptAPIBaseView, View):
    http_method_names = ["post"]

    def post(self, request, attempt_id):
        attempt = self.get_attempt(attempt_id)
        payload = _parse_payload(request)
        violation_type = (payload.get("type") or "").strip()
        description = payload.get("description") or ""

        if not violation_type:
            return _json_error("Parameter type pelanggaran wajib diisi.")

        try:
            result = record_exam_violation(
                exam=attempt.exam,
                attempt=attempt,
                violation_type=violation_type,
                description=description,
            )
        except ValueError as exc:
            return _json_error(str(exc))

        response_payload = {
            "success": True,
            "message": result["message"],
            "violations_count": result["violations_count"],
            "max_violations_allowed": result["max_violations_allowed"],
            "auto_submitted": result["auto_submitted"],
        }
        if result["auto_submitted"]:
            response_payload["redirect_url"] = reverse("exam_submit", kwargs={"attempt_id": attempt.id})
        return JsonResponse(response_payload)


class AttemptProctoringAPIView(StudentAttemptAPIBaseView, View):
    http_method_names = ["post"]

    def post(self, request, attempt_id):
        attempt = self.get_attempt(attempt_id)
        payload = _parse_payload(request)
        snapshot_label = payload.get("label") or "capture"
        screenshot_data_url = payload.get("screenshot_data_url") or ""
        result = record_proctoring_capture(
            exam=attempt.exam,
            attempt=attempt,
            snapshot_label=snapshot_label,
            screenshot_data_url=screenshot_data_url,
            request_base_url=request.build_absolute_uri("/"),
        )
        return JsonResponse(
            {
                "success": bool(result.get("captured")),
                "message": result.get("message", ""),
                "data": result,
            }
        )


class RetakeCheckView(StudentAttemptBaseView, View):
    http_method_names = ["get"]

    def get(self, request, exam_id):
        exam = _resolve_exam_for_student(request.user, exam_id)
        data = check_retake_eligibility(exam.id, request.user.id)
        return JsonResponse(
            {
                "success": True,
                "exam_id": str(exam.id),
                "eligible": data["eligible"],
                "attempts_used": data["attempts_used"],
                "max_attempts": data["max_attempts"],
                "remaining_attempts": data["remaining_attempts"],
                "cooldown_remaining_seconds": data["cooldown_remaining_seconds"],
                "next_available_at": data["next_available_at"].isoformat() if data["next_available_at"] else None,
                "reason": data["reason"],
            }
        )


class PreRetakeReviewView(StudentAttemptBaseView, TemplateView):
    template_name = "attempts/pre_retake_review.html"

    def get(self, request, exam_id, *args, **kwargs):
        exam = _resolve_exam_for_student(request.user, exam_id)
        latest_attempt = get_latest_attempt_for_exam(exam, request.user)
        if not exam.allow_retake:
            messages.info(request, "Retake tidak diaktifkan untuk ujian ini.")
            return redirect("student_exam_list")
        if not exam.retake_show_review:
            return redirect("retake_start", exam_id=exam.id)
        if not latest_attempt:
            messages.info(request, "Belum ada attempt sebelumnya.")
            return redirect("student_exam_list")

        wrong_answers = list(
            StudentAnswer.objects.filter(
                attempt=latest_attempt,
                is_correct=False,
            )
            .select_related("question", "selected_option")
            .order_by("answer_order", "created_at")
        )
        result = ExamResult.objects.filter(attempt=latest_attempt).first()
        context = self.get_context_data(**kwargs)
        context.update(
            {
                "exam": exam,
                "attempt": latest_attempt,
                "result": result,
                "wrong_answers": wrong_answers,
                "retake_check": check_retake_eligibility(exam.id, request.user.id),
                "start_retake_url": reverse("retake_start", kwargs={"exam_id": exam.id}),
                "back_url": reverse("student_exam_list"),
            }
        )
        return self.render_to_response(context)


class RetakeStartView(StudentAttemptBaseView, TemplateView):
    template_name = "attempts/retake_confirm.html"

    def get(self, request, exam_id, *args, **kwargs):
        exam = _resolve_exam_for_student(request.user, exam_id)
        if not exam.allow_retake:
            messages.info(request, "Retake tidak diaktifkan untuk ujian ini.")
            return redirect("student_exam_list")
        context = self.get_context_data(**kwargs)
        context.update(
            {
                "exam": exam,
                "retake_check": check_retake_eligibility(exam.id, request.user.id),
                "back_url": reverse("student_exam_list"),
            }
        )
        return self.render_to_response(context)

    def post(self, request, exam_id):
        exam = _resolve_exam_for_student(request.user, exam_id)
        if not exam.allow_retake:
            messages.info(request, "Retake tidak diaktifkan untuk ujian ini.")
            return redirect("student_exam_list")
        try:
            attempt = create_retake_attempt(
                exam_id=exam.id,
                student_id=request.user.id,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT") or "",
            )
        except RetakeNotAllowed as exc:
            messages.warning(request, str(exc))
            if exam.retake_show_review:
                return redirect("pre_retake_review", exam_id=exam.id)
            return redirect("student_exam_list")
        except MaxAttemptsReached as exc:
            messages.warning(request, str(exc))
            return redirect("student_exam_list")
        except CooldownActive as exc:
            messages.warning(request, str(exc))
            if exam.retake_show_review:
                return redirect("pre_retake_review", exam_id=exam.id)
            return redirect("retake_start", exam_id=exam.id)

        messages.success(
            request,
            f"Retake berhasil dibuat. Anda memulai attempt {attempt.attempt_number} dari {exam.max_retake_attempts}.",
        )
        return redirect("exam_room", exam_id=exam.id)


class AttemptHistoryAPIView(StudentAttemptBaseView, View):
    http_method_names = ["get"]

    def get(self, request, exam_id):
        exam = _resolve_exam_for_student(request.user, exam_id)
        rows = get_attempt_history_for_exam(exam=exam, student=request.user)
        payload = [
            {
                **row,
                "start_time": row["start_time"].isoformat() if row["start_time"] else None,
                "submit_time": row["submit_time"].isoformat() if row["submit_time"] else None,
                "retake_available_from": row["retake_available_from"].isoformat() if row["retake_available_from"] else None,
            }
            for row in rows
        ]
        return JsonResponse(
            {
                "success": True,
                "exam_id": str(exam.id),
                "history": payload,
            }
        )
