from __future__ import annotations

import base64
import bisect
import binascii
import hashlib
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import urljoin

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import OperationalError, transaction
from django.db.models import Prefetch, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.core.enums import choice_label
from apps.exams.models import ClassStudent, Exam
from apps.exams.services import resolve_effective_navigation
from apps.questions.models import (
    Question,
    QuestionBlankAnswer,
    QuestionMatchingPair,
    QuestionOption,
    QuestionOrderingItem,
)
from apps.questions.richtext import sanitize_richtext_html
from apps.results.models import ExamResult

from .models import ExamAttempt, ExamViolation, ProctoringScreenshot, StudentAnswer


FINISHED_ATTEMPT_STATUSES = (
    ExamAttempt.Status.SUBMITTED,
    ExamAttempt.Status.AUTO_SUBMITTED,
    ExamAttempt.Status.COMPLETED,
    ExamAttempt.Status.GRADING,
)
LIST_TABS = ("upcoming", "ongoing", "completed", "missed")
EXAM_ROOM_COMPLETED_STATUSES = {
    ExamAttempt.Status.SUBMITTED,
    ExamAttempt.Status.AUTO_SUBMITTED,
    ExamAttempt.Status.COMPLETED,
    ExamAttempt.Status.GRADING,
}


class RetakeNotAllowed(Exception):
    """Retake is not enabled for this exam or the student has not finished the previous attempt."""


class MaxAttemptsReached(Exception):
    """Maximum attempts reached for this exam."""


class CooldownActive(Exception):
    """Retake cooldown has not elapsed yet."""

    def __init__(self, message, cooldown_remaining_seconds=0, next_available_at=None):
        super().__init__(message)
        self.cooldown_remaining_seconds = int(cooldown_remaining_seconds or 0)
        self.next_available_at = next_available_at

STATUS_META = {
    "upcoming": {"label": "Akan Datang", "tone": "primary"},
    "ongoing": {"label": "Sedang Berlangsung", "tone": "success"},
    "completed": {"label": "Selesai", "tone": "secondary"},
    "missed": {"label": "Terlewat", "tone": "danger"},
}

VIOLATION_SEVERITY_MAP = {
    ExamViolation.ViolationType.TAB_SWITCH: ExamViolation.Severity.MEDIUM,
    ExamViolation.ViolationType.FULLSCREEN_EXIT: ExamViolation.Severity.HIGH,
    ExamViolation.ViolationType.COPY_ATTEMPT: ExamViolation.Severity.MEDIUM,
    ExamViolation.ViolationType.PASTE_ATTEMPT: ExamViolation.Severity.MEDIUM,
    ExamViolation.ViolationType.RIGHT_CLICK: ExamViolation.Severity.LOW,
    ExamViolation.ViolationType.SUSPICIOUS_ACTIVITY: ExamViolation.Severity.HIGH,
}

MYSQL_LOCK_TIMEOUT_CODES = {1205, 1213}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StudentExamListFilters:
    tab: str
    keyword: str
    subject_id: str
    selected_date: date | None
    selected_date_raw: str


def parse_exam_list_filters(request):
    tab = (request.GET.get("tab") or "upcoming").strip().lower()
    if tab not in LIST_TABS:
        tab = "upcoming"

    keyword = (request.GET.get("q") or "").strip()
    subject_id = (request.GET.get("subject") or "").strip()
    selected_date_raw = (request.GET.get("date") or "").strip()
    selected_date = parse_date(selected_date_raw) if selected_date_raw else None

    return StudentExamListFilters(
        tab=tab,
        keyword=keyword,
        subject_id=subject_id,
        selected_date=selected_date,
        selected_date_raw=selected_date_raw,
    )


def get_student_assigned_exam_queryset(student):
    class_ids = ClassStudent.objects.filter(student=student).values_list("class_obj_id", flat=True)
    return (
        Exam.objects.filter(
            (
                Q(assignments__assigned_to_type="student", assignments__student=student)
                | Q(assignments__assigned_to_type="class", assignments__class_obj_id__in=class_ids)
            ),
            is_deleted=False,
        )
        .exclude(status__in=[Exam.Status.DRAFT, Exam.Status.CANCELLED])
        .select_related("subject")
        .prefetch_related("assignments__class_obj", "exam_questions")
        .distinct()
        .order_by("start_time")
    )


def get_latest_attempt_for_exam(exam, student):
    return (
        ExamAttempt.objects.filter(exam=exam, student=student)
        .order_by("-attempt_number", "-created_at")
        .first()
    )


def _retake_policy_label(policy):
    mapping = {
        "highest": "Nilai Tertinggi",
        "latest": "Nilai Terbaru",
        "average": "Nilai Rata-rata",
    }
    return mapping.get((policy or "").strip().lower(), "Nilai Tertinggi")


def _result_key_for_policy(policy, result):
    normalized = (policy or "").strip().lower()
    if normalized == "latest":
        return (
            int(result.attempt.attempt_number or 0),
            float(result.total_score or 0),
        )
    return (
        float(result.total_score or 0),
        int(result.attempt.attempt_number or 0),
    )


def _build_final_result_summary(exam, exam_results):
    if not exam_results:
        return {
            "has_result": False,
            "score": 0.0,
            "percentage": 0.0,
            "status": "Belum Ada Hasil",
            "correct": 0,
            "wrong": 0,
            "unanswered": 0,
            "time_spent_seconds": 0,
            "detail_url": "",
            "attempts_used": 0,
            "policy_label": _retake_policy_label(exam.retake_score_policy),
        }

    policy = (exam.retake_score_policy or "highest").strip().lower()
    selected = max(exam_results, key=lambda item: _result_key_for_policy(policy, item))

    if policy == "average":
        score_value = sum(float(item.total_score or 0) for item in exam_results) / len(exam_results)
        percentage_value = sum(float(item.percentage or 0) for item in exam_results) / len(exam_results)
        passed_value = percentage_value >= float(exam.passing_score or 0)
        latest = max(exam_results, key=lambda item: int(item.attempt.attempt_number or 0))
        return {
            "has_result": True,
            "score": round(score_value, 2),
            "percentage": round(percentage_value, 2),
            "status": "Lulus" if passed_value else "Belum Lulus",
            "correct": int(latest.correct_answers or 0),
            "wrong": int(latest.wrong_answers or 0),
            "unanswered": int(latest.unanswered or 0),
            "time_spent_seconds": int(latest.time_taken_seconds or 0),
            "detail_url": reverse("student_result_detail", kwargs={"result_id": latest.id}),
            "attempts_used": len(exam_results),
            "policy_label": _retake_policy_label(policy),
        }

    return {
        "has_result": True,
        "score": round(float(selected.total_score or 0), 2),
        "percentage": round(float(selected.percentage or 0), 2),
        "status": "Lulus" if selected.passed else "Belum Lulus",
        "correct": int(selected.correct_answers or 0),
        "wrong": int(selected.wrong_answers or 0),
        "unanswered": int(selected.unanswered or 0),
        "time_spent_seconds": int(selected.time_taken_seconds or 0),
        "detail_url": reverse("student_result_detail", kwargs={"result_id": selected.id}),
        "attempts_used": len(exam_results),
        "policy_label": _retake_policy_label(policy),
    }


def check_retake_eligibility(exam_id, student_id):
    exam = Exam.objects.only(
        "id",
        "allow_retake",
        "max_retake_attempts",
        "retake_cooldown_minutes",
        "start_time",
        "end_time",
        "status",
    ).get(id=exam_id)
    latest_attempt = (
        ExamAttempt.objects.filter(exam_id=exam_id, student_id=student_id)
        .order_by("-attempt_number", "-created_at")
        .first()
    )
    now = timezone.now()

    attempts_used = int(latest_attempt.attempt_number) if latest_attempt else 0
    max_attempts = int(exam.max_retake_attempts or 1)
    remaining_attempts = max(max_attempts - attempts_used, 0)
    next_available_at = None
    cooldown_remaining_seconds = 0
    eligible = False
    reason = ""

    if not exam.allow_retake:
        reason = "Fitur retake tidak diaktifkan pada ujian ini."
    elif not latest_attempt:
        reason = "Belum ada attempt sebelumnya untuk diulang."
    elif latest_attempt.status not in EXAM_ROOM_COMPLETED_STATUSES:
        reason = "Attempt sebelumnya belum disubmit."
    elif attempts_used >= max_attempts:
        reason = "Batas maksimum attempt sudah tercapai."
    elif now > exam.end_time:
        reason = "Jadwal ujian sudah berakhir."
    else:
        if latest_attempt.retake_available_from:
            next_available_at = latest_attempt.retake_available_from
        elif latest_attempt.submit_time:
            next_available_at = latest_attempt.submit_time + timedelta(minutes=int(exam.retake_cooldown_minutes or 0))
        else:
            next_available_at = now

        cooldown_remaining_seconds = max(int((next_available_at - now).total_seconds()), 0)
        eligible = cooldown_remaining_seconds <= 0
        if not eligible:
            reason = "Cooldown retake masih aktif."

    return {
        "eligible": bool(eligible),
        "attempts_used": attempts_used,
        "max_attempts": max_attempts,
        "remaining_attempts": int(remaining_attempts),
        "cooldown_remaining_seconds": int(cooldown_remaining_seconds),
        "next_available_at": next_available_at,
        "reason": reason,
    }


@transaction.atomic
def create_retake_attempt(*, exam_id, student_id, ip_address="", user_agent=""):
    exam = Exam.objects.select_for_update().get(id=exam_id)
    latest_attempt = (
        ExamAttempt.objects.select_for_update()
        .filter(exam_id=exam_id, student_id=student_id)
        .order_by("-attempt_number", "-created_at")
        .first()
    )
    now = timezone.now()

    if not exam.allow_retake:
        raise RetakeNotAllowed("Retake tidak diaktifkan untuk ujian ini.")
    if not latest_attempt:
        raise RetakeNotAllowed("Retake belum tersedia karena belum ada attempt sebelumnya.")
    if latest_attempt.status not in EXAM_ROOM_COMPLETED_STATUSES:
        raise RetakeNotAllowed("Attempt sebelumnya belum disubmit.")
    if latest_attempt.attempt_number >= int(exam.max_retake_attempts or 1):
        raise MaxAttemptsReached("Maksimal jumlah attempt sudah tercapai.")

    next_available_at = latest_attempt.retake_available_from
    if not next_available_at and latest_attempt.submit_time:
        next_available_at = latest_attempt.submit_time + timedelta(minutes=int(exam.retake_cooldown_minutes or 0))
        latest_attempt.retake_available_from = next_available_at
        latest_attempt.save(update_fields=["retake_available_from", "updated_at"])

    cooldown_remaining_seconds = 0
    if next_available_at:
        cooldown_remaining_seconds = max(int((next_available_at - now).total_seconds()), 0)
    if cooldown_remaining_seconds > 0:
        raise CooldownActive(
            "Retake belum tersedia karena cooldown masih aktif.",
            cooldown_remaining_seconds=cooldown_remaining_seconds,
            next_available_at=next_available_at,
        )

    if now > exam.end_time:
        raise RetakeNotAllowed("Jadwal ujian sudah berakhir.")

    attempt = ExamAttempt.objects.create(
        exam_id=exam_id,
        student_id=student_id,
        attempt_number=int(latest_attempt.attempt_number) + 1,
        status=ExamAttempt.Status.NOT_STARTED,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:1000],
    )
    return attempt


def get_exam_subject_options(exams_qs):
    rows = exams_qs.values("subject_id", "subject__name").distinct().order_by("subject__name")
    return [
        {"id": str(item["subject_id"]), "name": item["subject__name"]}
        for item in rows
        if item["subject_id"]
    ]


def apply_exam_list_filters(exams_qs, filters: StudentExamListFilters):
    queryset = exams_qs
    if filters.keyword:
        queryset = queryset.filter(
            Q(title__icontains=filters.keyword)
            | Q(description__icontains=filters.keyword)
            | Q(subject__name__icontains=filters.keyword)
        )
    if filters.subject_id:
        queryset = queryset.filter(subject_id=filters.subject_id)
    if filters.selected_date:
        queryset = queryset.filter(start_time__date=filters.selected_date)
    return queryset


def _attempt_map(student, exam_ids):
    attempts = (
        ExamAttempt.objects.filter(student=student, exam_id__in=exam_ids)
        .order_by("exam_id", "-attempt_number", "-created_at")
        .select_related("exam")
    )
    latest = {}
    for attempt in attempts:
        if attempt.exam_id not in latest:
            latest[attempt.exam_id] = attempt
    return latest


def _result_map(student, exam_ids):
    results = (
        ExamResult.objects.filter(student=student, exam_id__in=exam_ids)
        .select_related("exam", "attempt")
        .order_by("exam_id", "-attempt__attempt_number", "-created_at")
    )
    grouped = {}
    for result in results:
        grouped.setdefault(result.exam_id, []).append(result)
    return grouped


def classify_exam_status(exam, latest_attempt, now):
    if latest_attempt and latest_attempt.status in FINISHED_ATTEMPT_STATUSES:
        return "completed"
    if exam.end_time < now or exam.status == Exam.Status.COMPLETED:
        return "missed"
    if exam.start_time > now:
        return "upcoming"
    if exam.start_time <= now <= exam.end_time and exam.status in {Exam.Status.PUBLISHED, Exam.Status.ONGOING}:
        return "ongoing"
    return "upcoming"


def can_start_exam(exam, latest_attempt, status_key):
    if status_key != "ongoing":
        return False
    if latest_attempt and latest_attempt.status in FINISHED_ATTEMPT_STATUSES:
        return False
    return True


def _navigation_rules(exam):
    if not exam.override_question_navigation:
        return "Mengikuti aturan navigasi default tiap soal."
    labels = []
    labels.append("Dapat kembali ke soal sebelumnya" if exam.global_allow_previous else "Tidak dapat kembali ke soal sebelumnya")
    labels.append("Dapat lanjut ke soal berikutnya" if exam.global_allow_next else "Tidak dapat lompat ke soal berikutnya")
    labels.append("Wajib urut per nomor soal" if exam.global_force_sequential else "Tidak wajib urut per nomor soal")
    return ". ".join(labels)


def _anti_cheat_rules(exam):
    labels = []
    labels.append("Wajib mode fullscreen" if exam.require_fullscreen else "Fullscreen tidak wajib")
    labels.append("Izin kamera wajib" if exam.require_camera else "Kamera tidak wajib")
    labels.append("Izin mikrofon wajib" if exam.require_microphone else "Mikrofon tidak wajib")
    labels.append("Perpindahan tab dipantau" if exam.detect_tab_switch else "Perpindahan tab tidak dipantau")
    if exam.enable_screenshot_proctoring:
        labels.append(f"Screenshot berkala setiap {exam.screenshot_interval_seconds} detik")
    else:
        labels.append("Screenshot berkala tidak aktif")
    labels.append(f"Batas pelanggaran: {exam.max_violations_allowed}")
    return ". ".join(labels)


def _action_meta(exam, status_key, can_start, result_summary):
    if can_start:
        return {
            "type": "start",
            "label": "Mulai Ujian",
            "url": reverse("exam_start", kwargs={"exam_id": exam.id}),
            "class_name": "btn-success",
            "icon": "ri-play-circle-line",
        }
    if status_key == "completed" and result_summary.get("has_result"):
        return {
            "type": "result",
            "label": "Lihat Hasil",
            "url": result_summary.get("detail_url") or "",
            "class_name": "btn-outline-primary",
            "icon": "ri-bar-chart-line",
        }
    if status_key == "completed":
        return {
            "type": "disabled",
            "label": "Menunggu Hasil",
            "url": "",
            "class_name": "btn-outline-secondary",
            "icon": "ri-time-line",
        }
    if status_key == "upcoming":
        return {
            "type": "disabled",
            "label": "Belum Dimulai",
            "url": "",
            "class_name": "btn-outline-secondary",
            "icon": "ri-time-line",
        }
    return {
        "type": "disabled",
        "label": "Terlewat",
        "url": "",
        "class_name": "btn-outline-danger",
        "icon": "ri-close-circle-line",
    }


def _build_retake_meta(exam, latest_attempt, now):
    max_attempts = int(exam.max_retake_attempts or 1)
    attempts_used = int(latest_attempt.attempt_number) if latest_attempt else 0
    remaining_attempts = max(max_attempts - attempts_used, 0)
    enabled = bool(exam.allow_retake)

    cooldown_remaining_seconds = 0
    next_available_at = None
    eligible = False
    if enabled and latest_attempt and latest_attempt.status in EXAM_ROOM_COMPLETED_STATUSES and attempts_used < max_attempts:
        if latest_attempt.retake_available_from:
            next_available_at = latest_attempt.retake_available_from
        elif latest_attempt.submit_time:
            next_available_at = latest_attempt.submit_time + timedelta(minutes=int(exam.retake_cooldown_minutes or 0))
        else:
            next_available_at = now
        cooldown_remaining_seconds = max(int((next_available_at - now).total_seconds()), 0)
        eligible = cooldown_remaining_seconds <= 0 and now <= exam.end_time

    return {
        "enabled": enabled,
        "attempts_used": attempts_used,
        "max_attempts": max_attempts,
        "remaining_attempts": remaining_attempts,
        "eligible": bool(eligible),
        "cooldown_remaining_seconds": int(cooldown_remaining_seconds),
        "next_available_at": next_available_at,
        "next_available_at_iso": next_available_at.isoformat() if next_available_at else "",
        "policy_label": _retake_policy_label(exam.retake_score_policy),
        "show_review": bool(exam.retake_show_review),
    }


def build_exam_card_rows(student, exams_qs, selected_tab):
    exams = list(exams_qs)
    if not exams:
        return [], {tab: 0 for tab in LIST_TABS}

    now = timezone.now()
    exam_ids = [exam.id for exam in exams]
    attempt_map = _attempt_map(student, exam_ids)
    result_map = _result_map(student, exam_ids)

    all_rows = []
    tab_counts = {tab: 0 for tab in LIST_TABS}

    for exam in exams:
        latest_attempt = attempt_map.get(exam.id)
        exam_results = result_map.get(exam.id, [])
        status_key = classify_exam_status(exam, latest_attempt, now)
        tab_counts[status_key] += 1

        start_allowed = can_start_exam(exam, latest_attempt, status_key)
        result_summary = _build_final_result_summary(exam, exam_results)
        retake_meta = _build_retake_meta(exam, latest_attempt, now)
        action = _action_meta(exam, status_key, start_allowed, result_summary)
        status_meta = STATUS_META[status_key]

        row = {
            "exam": exam,
            "status_key": status_key,
            "status_label": status_meta["label"],
            "status_tone": status_meta["tone"],
            "question_count": exam.exam_questions.count(),
            "countdown_target": exam.start_time.isoformat() if status_key == "upcoming" else "",
            "start_allowed": start_allowed,
            "start_url": reverse("exam_start", kwargs={"exam_id": exam.id}),
            "action": action,
            "retake": {
                **retake_meta,
                "check_url": reverse("retake_check", kwargs={"exam_id": exam.id}),
                "review_url": reverse("pre_retake_review", kwargs={"exam_id": exam.id}),
                "start_url": reverse("retake_start", kwargs={"exam_id": exam.id}),
                "history_url": reverse("attempt_history", kwargs={"exam_id": exam.id}),
            },
            "detail": {
                "title": exam.title,
                "subject": exam.subject.name if exam.subject_id else "-",
                "description": exam.description or "-",
                "instructions": exam.instructions or "-",
                "schedule": (
                    f"{timezone.localtime(exam.start_time).strftime('%d %b %Y %H:%M')} "
                    f"sampai {timezone.localtime(exam.end_time).strftime('%d %b %Y %H:%M')}"
                ),
                "duration": f"{exam.duration_minutes} menit",
                "question_count": exam.exam_questions.count(),
                "navigation_rules": _navigation_rules(exam),
                "anti_cheat_rules": _anti_cheat_rules(exam),
                "start_url": reverse("exam_start", kwargs={"exam_id": exam.id}) if start_allowed else "",
                "retake_enabled": bool(exam.allow_retake),
                "retake_max_attempts": int(exam.max_retake_attempts or 1),
                "retake_attempts_used": retake_meta["attempts_used"],
                "retake_remaining_attempts": retake_meta["remaining_attempts"],
                "retake_policy_label": _retake_policy_label(exam.retake_score_policy),
                "retake_cooldown_minutes": int(exam.retake_cooldown_minutes or 0),
            },
            "result_summary": result_summary,
        }
        all_rows.append(row)

    filtered_rows = [row for row in all_rows if row["status_key"] == selected_tab]
    return filtered_rows, tab_counts


def _deterministic_rank(seed_value: str):
    return hashlib.sha256(seed_value.encode("utf-8")).hexdigest()


def _coerce_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False
    return bool(value)


def _coerce_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_option_id_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, (list, tuple, set)):
        raw_values = value
    else:
        raw_values = [value]

    normalized = []
    seen = set()
    for item in raw_values:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _normalize_matching_answer_map(value):
    if not isinstance(value, dict):
        return {}

    normalized = {}
    for key, item_value in value.items():
        prompt_id = str(key or "").strip()
        answer_id = str(item_value or "").strip()
        if not prompt_id or not answer_id:
            continue
        normalized[prompt_id] = answer_id
    return normalized


def _normalize_blank_answer_map(value):
    if not isinstance(value, dict):
        return {}

    normalized = {}
    for key, item_value in value.items():
        blank_key = str(key or "").strip()
        if not blank_key:
            continue
        normalized[blank_key] = str(item_value or "")
    return normalized


def _blank_answer_map_has_values(value):
    return any(str(item or "").strip() for item in _normalize_blank_answer_map(value).values())


def _answer_is_filled(answer):
    if not answer:
        return False
    if answer.answer_type == StudentAnswer.AnswerType.MULTIPLE_CHOICE:
        return bool(answer.selected_option_id)
    if answer.answer_type == StudentAnswer.AnswerType.CHECKBOX:
        return bool(answer.selected_option_ids or [])
    if answer.answer_type == StudentAnswer.AnswerType.ORDERING:
        return bool(answer.answer_order_json or [])
    if answer.answer_type == StudentAnswer.AnswerType.MATCHING:
        return bool(_normalize_matching_answer_map(answer.answer_matching_json))
    if answer.answer_type == StudentAnswer.AnswerType.FILL_IN_BLANK:
        return _blank_answer_map_has_values(answer.answer_blanks_json)
    return bool((answer.answer_text or "").strip())


def _resolve_points_possible(question_row):
    points = question_row["points_possible"]
    if isinstance(points, Decimal):
        return points
    return Decimal(str(points))


def resolve_attempt_deadline(exam, attempt):
    if attempt.end_time:
        return min(attempt.end_time, exam.end_time)
    if attempt.start_time:
        attempt_deadline = attempt.start_time + timedelta(minutes=exam.duration_minutes)
        return min(attempt_deadline, exam.end_time)
    return exam.end_time


def get_attempt_remaining_seconds(exam, attempt, now=None):
    current_time = now or timezone.now()
    if attempt.status in EXAM_ROOM_COMPLETED_STATUSES:
        return 0
    deadline = resolve_attempt_deadline(exam, attempt)
    return max(int((deadline - current_time).total_seconds()), 0)


def _duration_label(total_seconds):
    seconds = max(int(total_seconds or 0), 0)
    hours, rem = divmod(seconds, 3600)
    minutes, sec = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"


def _datetime_label(value):
    if not value:
        return "-"
    return timezone.localtime(value).strftime("%d %b %Y %H:%M:%S")


def _build_exam_question_sequence(exam, attempt):
    exam_question_rows = list(
        exam.exam_questions.select_related("question")
        .prefetch_related(
            Prefetch(
                "question__options",
                queryset=QuestionOption.objects.order_by("display_order", "option_letter"),
            ),
            Prefetch(
                "question__ordering_items",
                queryset=QuestionOrderingItem.objects.order_by("correct_order"),
            ),
            Prefetch(
                "question__matching_pairs",
                queryset=QuestionMatchingPair.objects.order_by("pair_order"),
            ),
            Prefetch(
                "question__blank_answers",
                queryset=QuestionBlankAnswer.objects.order_by("blank_number"),
            )
        )
        .order_by("display_order")
    )

    rows = []
    for exam_question in exam_question_rows:
        question = exam_question.question
        options = list(question.options.all())
        ordering_items = list(question.ordering_items.all())
        ordering_items_shuffled = list(ordering_items)
        matching_pairs = list(question.matching_pairs.all())
        matching_answer_choices = list(matching_pairs)
        blank_answers = list(question.blank_answers.all())
        if exam.randomize_options:
            options.sort(key=lambda item: _deterministic_rank(f"{attempt.id}:{question.id}:{item.id}:option"))
        if question.question_type == Question.QuestionType.ORDERING:
            ordering_items_shuffled.sort(
                key=lambda item: _deterministic_rank(f"{attempt.id}:{question.id}:{item.id}:ordering")
            )
        if question.question_type == Question.QuestionType.MATCHING:
            matching_answer_choices.sort(
                key=lambda item: _deterministic_rank(f"{attempt.id}:{question.id}:{item.id}:matching-answer")
            )

        points_possible = exam_question.points_override if exam_question.points_override is not None else question.points
        rows.append(
            {
                "exam_question": exam_question,
                "question": question,
                "options": options,
                "ordering_items": ordering_items,
                "ordering_items_shuffled": ordering_items_shuffled,
                "matching_pairs": matching_pairs,
                "matching_answer_choices": matching_answer_choices,
                "blank_answers": blank_answers,
                "rules": resolve_effective_navigation(exam, exam_question),
                "points_possible": points_possible,
            }
        )

    if exam.randomize_questions:
        rows.sort(key=lambda item: _deterministic_rank(f"{attempt.id}:{item['question'].id}:question"))

    for idx, row in enumerate(rows, start=1):
        row["number"] = idx

    return rows


def _build_answer_map(attempt):
    answers = StudentAnswer.objects.filter(attempt=attempt).select_related("selected_option")
    return {answer.question_id: answer for answer in answers}


def _build_latest_answer_timestamp(answer_map, attempt):
    latest_dt = attempt.updated_at
    for answer in answer_map.values():
        if latest_dt is None or answer.updated_at > latest_dt:
            latest_dt = answer.updated_at
    return latest_dt


def _get_row_by_number(question_rows, number):
    if not question_rows:
        return None
    if number < 1 or number > len(question_rows):
        return None
    return question_rows[number - 1]


def _first_unanswered_number(question_rows, answer_map):
    for row in question_rows:
        if not _answer_is_filled(answer_map.get(row["question"].id)):
            return row["number"]
    return 1 if question_rows else 0


def _sequential_lock_from(question_rows, answer_map):
    for row in question_rows:
        if row["rules"].get("force_sequential") and not _answer_is_filled(answer_map.get(row["question"].id)):
            return row["number"] + 1
    return None


def _can_navigate_to(question_rows, answer_map, current_number, target_number):
    if target_number == current_number:
        return True, ""
    if target_number < 1 or target_number > len(question_rows):
        return False, "Nomor soal tidak valid."

    current_row = _get_row_by_number(question_rows, current_number)
    if current_row is None:
        return False, "Soal saat ini tidak ditemukan."

    current_rules = current_row["rules"]
    current_answer = answer_map.get(current_row["question"].id)
    current_answered = _answer_is_filled(current_answer)

    if target_number < current_number and not current_rules.get("allow_previous"):
        return False, "Soal ini tidak mengizinkan kembali ke soal sebelumnya."

    if target_number > current_number:
        if not current_rules.get("allow_next"):
            return False, "Soal ini tidak mengizinkan lanjut ke soal berikutnya."
        if current_rules.get("force_sequential") and not current_answered:
            return False, "Mode berurutan aktif: jawab soal ini terlebih dahulu."

        lock_from = _sequential_lock_from(question_rows, answer_map)
        if lock_from and target_number >= lock_from:
            return False, "Mode berurutan aktif: soal berikutnya masih terkunci."

    return True, ""


def _build_question_map(question_rows, answer_map, current_number):
    lock_from = _sequential_lock_from(question_rows, answer_map)
    rows = []
    answered_count = 0
    marked_count = 0

    for row in question_rows:
        answer = answer_map.get(row["question"].id)
        is_answered = _answer_is_filled(answer)
        is_marked = bool(answer and answer.is_marked_for_review)
        is_current = row["number"] == current_number
        is_locked = bool(lock_from and row["number"] >= lock_from and not is_current)

        if is_answered:
            answered_count += 1
        if is_marked:
            marked_count += 1

        rows.append(
            {
                "number": row["number"],
                "answered": is_answered,
                "marked": is_marked,
                "current": is_current,
                "locked": is_locked,
            }
        )

    total = len(question_rows)
    return {
        "rows": rows,
        "answered_count": answered_count,
        "marked_count": marked_count,
        "unanswered_count": max(total - answered_count, 0),
        "total_questions": total,
    }


def _build_navigation_meta(question_rows, answer_map, current_number):
    row = _get_row_by_number(question_rows, current_number)
    if not row:
        return {
            "can_previous": False,
            "can_next": False,
            "is_first": True,
            "is_last": True,
            "restriction_message": "Soal tidak tersedia.",
        }

    rules = row["rules"]
    total = len(question_rows)
    answer = answer_map.get(row["question"].id)
    answered = _answer_is_filled(answer)

    can_previous = current_number > 1 and bool(rules.get("allow_previous"))
    can_next = current_number < total and bool(rules.get("allow_next"))
    restriction_message = ""

    if current_number < total and not rules.get("allow_next"):
        can_next = False
        restriction_message = "Soal ini mengunci navigasi ke soal berikutnya."
    elif current_number < total and rules.get("force_sequential") and not answered:
        can_next = False
        restriction_message = "Mode berurutan aktif: jawab soal ini untuk lanjut."
    elif current_number < total:
        lock_from = _sequential_lock_from(question_rows, answer_map)
        if lock_from and (current_number + 1) >= lock_from and not answered:
            can_next = False
            restriction_message = "Mode berurutan aktif: soal berikutnya masih terkunci."

    if current_number > 1 and not rules.get("allow_previous"):
        can_previous = False
        if not restriction_message:
            restriction_message = "Navigasi ke soal sebelumnya dinonaktifkan."

    return {
        "can_previous": can_previous,
        "can_next": can_next,
        "is_first": current_number <= 1,
        "is_last": current_number >= total,
        "restriction_message": restriction_message,
    }


def _serialize_question_payload(row, answer):
    question = row["question"]
    selected_option_id = str(answer.selected_option_id) if answer and answer.selected_option_id else ""
    selected_option_ids = _normalize_option_id_list(answer.selected_option_ids if answer else [])
    answer_order_json = _normalize_option_id_list(answer.answer_order_json if answer else [])
    answer_matching_json = _normalize_matching_answer_map(answer.answer_matching_json if answer else {})
    answer_blanks_json = _normalize_blank_answer_map(answer.answer_blanks_json if answer else {})
    answer_text = ""
    if answer and answer.answer_text:
        answer_text = answer.answer_text

    options = []
    for option in row["options"]:
        options.append(
            {
                "id": str(option.id),
                "letter": option.option_letter,
                "text": sanitize_richtext_html(option.option_text),
                "image_url": option.option_image_url or "",
            }
        )

    ordering_item_map = {str(item.id): item for item in row.get("ordering_items", [])}
    ordering_items = []
    if question.question_type == Question.QuestionType.ORDERING:
        if answer_order_json:
            seen_item_ids = set()
            for item_id in answer_order_json:
                item = ordering_item_map.get(item_id)
                if not item:
                    continue
                seen_item_ids.add(item_id)
                ordering_items.append(
                    {
                        "id": str(item.id),
                        "text": sanitize_richtext_html(item.item_text),
                    }
                )
            for item in row.get("ordering_items_shuffled", []):
                item_id = str(item.id)
                if item_id in seen_item_ids:
                    continue
                ordering_items.append(
                    {
                        "id": item_id,
                        "text": sanitize_richtext_html(item.item_text),
                    }
                )
        else:
            for item in row.get("ordering_items_shuffled", []):
                ordering_items.append(
                    {
                        "id": str(item.id),
                        "text": sanitize_richtext_html(item.item_text),
                    }
                )

    matching_pairs = []
    matching_answer_choices = []
    if question.question_type == Question.QuestionType.MATCHING:
        for pair in row.get("matching_pairs", []):
            matching_pairs.append(
                {
                    "id": str(pair.id),
                    "prompt_text": sanitize_richtext_html(pair.prompt_text),
                }
            )
        for pair in row.get("matching_answer_choices", []):
            matching_answer_choices.append(
                {
                    "id": str(pair.id),
                    "answer_text": sanitize_richtext_html(pair.answer_text),
                }
            )

    blank_numbers = []
    if question.question_type == Question.QuestionType.FILL_IN_BLANK:
        blank_numbers = [int(item.blank_number) for item in row.get("blank_answers", [])]

    return {
        "number": row["number"],
        "question_id": str(question.id),
        "question_type": question.question_type,
        "question_text": sanitize_richtext_html(question.question_text),
        "question_image_url": question.question_image_url or "",
        "audio_play_limit": int(question.audio_play_limit or 0),
        "video_play_limit": int(question.video_play_limit or 0),
        "points": float(_resolve_points_possible(row)),
        "options": options,
        "ordering_items": ordering_items,
        "matching_pairs": matching_pairs,
        "matching_answer_choices": matching_answer_choices,
        "blank_numbers": blank_numbers,
        "answer": {
            "selected_option_id": selected_option_id,
            "selected_option_ids": selected_option_ids,
            "answer_order_json": answer_order_json,
            "answer_matching_json": answer_matching_json,
            "answer_blanks_json": answer_blanks_json,
            "answer_text": answer_text,
            "marked_for_review": bool(answer and answer.is_marked_for_review),
            "is_answered": _answer_is_filled(answer),
        },
    }


def build_exam_room_payload(
    *,
    exam,
    attempt,
    current_number=1,
    requested_number=None,
    enforce_navigation=False,
):
    question_rows = _build_exam_question_sequence(exam, attempt)
    answer_map = _build_answer_map(attempt)
    total_questions = len(question_rows)

    if total_questions <= 0:
        return {
            "attempt_id": str(attempt.id),
            "exam_id": str(exam.id),
            "exam_title": exam.title,
            "attempt_number": int(attempt.attempt_number or 1),
            "max_attempts": int(exam.max_retake_attempts or 1),
            "allow_retake": bool(exam.allow_retake),
            "attempt_status": attempt.status,
            "attempt_status_label": choice_label(ExamAttempt.Status, attempt.status, default=attempt.status),
            "current_number": 0,
            "total_questions": 0,
            "question": None,
            "question_map": [],
            "summary": {
                "answered_count": 0,
                "marked_count": 0,
                "unanswered_count": 0,
                "total_questions": 0,
            },
            "navigation": {
                "can_previous": False,
                "can_next": False,
                "is_first": True,
                "is_last": True,
                "restriction_message": "Belum ada soal pada ujian ini.",
            },
            "timer": {
                "remaining_seconds": max(int(exam.duration_minutes * 60), 0),
                "remaining_label": _duration_label(max(int(exam.duration_minutes * 60), 0)),
                "deadline_label": _datetime_label(resolve_attempt_deadline(exam, attempt)),
            },
            "anti_cheat": {
                "require_fullscreen": bool(exam.require_fullscreen),
                "require_camera": bool(exam.require_camera),
                "require_microphone": bool(exam.require_microphone),
                "detect_tab_switch": bool(exam.detect_tab_switch),
                "enable_screenshot_proctoring": bool(exam.enable_screenshot_proctoring),
                "screenshot_interval_seconds": int(exam.screenshot_interval_seconds or 300),
                "max_violations_allowed": int(exam.max_violations_allowed or 0),
                "current_violations": 0,
            },
            "last_saved_label": _datetime_label(attempt.updated_at),
            "notice": "Belum ada soal yang dapat dikerjakan.",
            "is_submitted": attempt.status in EXAM_ROOM_COMPLETED_STATUSES,
        }

    requested = None if requested_number is None else _coerce_int(requested_number, default=1)
    if current_number < 1 or current_number > total_questions:
        current_number = _first_unanswered_number(question_rows, answer_map)

    if requested is None:
        requested = current_number

    if requested < 1 or requested > total_questions:
        requested = current_number

    notice = ""
    if enforce_navigation:
        allowed, reason = _can_navigate_to(question_rows, answer_map, current_number, requested)
        if not allowed:
            notice = reason
        else:
            current_number = requested
    else:
        current_number = requested

    map_data = _build_question_map(question_rows, answer_map, current_number)
    nav_meta = _build_navigation_meta(question_rows, answer_map, current_number)
    if not notice:
        notice = nav_meta["restriction_message"] if not nav_meta["can_next"] and not nav_meta["is_last"] else ""

    current_row = _get_row_by_number(question_rows, current_number)
    current_answer = answer_map.get(current_row["question"].id) if current_row else None
    question_payload = _serialize_question_payload(current_row, current_answer) if current_row else None

    now = timezone.now()
    remaining_seconds = get_attempt_remaining_seconds(exam, attempt, now=now)
    violations_count = _safe_violation_count(attempt.id)
    latest_saved_at = _build_latest_answer_timestamp(answer_map, attempt)

    return {
        "attempt_id": str(attempt.id),
        "exam_id": str(exam.id),
        "exam_title": exam.title,
        "attempt_number": int(attempt.attempt_number or 1),
        "max_attempts": int(exam.max_retake_attempts or 1),
        "allow_retake": bool(exam.allow_retake),
        "attempt_status": attempt.status,
        "attempt_status_label": choice_label(ExamAttempt.Status, attempt.status, default=attempt.status),
        "current_number": current_number,
        "total_questions": total_questions,
        "question": question_payload,
        "question_map": map_data["rows"],
        "summary": {
            "answered_count": map_data["answered_count"],
            "marked_count": map_data["marked_count"],
            "unanswered_count": map_data["unanswered_count"],
            "total_questions": map_data["total_questions"],
        },
        "navigation": nav_meta,
        "timer": {
            "remaining_seconds": remaining_seconds,
            "remaining_label": _duration_label(remaining_seconds),
            "deadline_label": _datetime_label(resolve_attempt_deadline(exam, attempt)),
        },
        "anti_cheat": {
            "require_fullscreen": bool(exam.require_fullscreen),
            "require_camera": bool(exam.require_camera),
            "require_microphone": bool(exam.require_microphone),
            "detect_tab_switch": bool(exam.detect_tab_switch),
            "enable_screenshot_proctoring": bool(exam.enable_screenshot_proctoring),
            "screenshot_interval_seconds": int(exam.screenshot_interval_seconds or 300),
            "max_violations_allowed": int(exam.max_violations_allowed or 0),
            "current_violations": violations_count,
        },
        "last_saved_label": _datetime_label(latest_saved_at),
        "notice": notice,
        "is_submitted": attempt.status in EXAM_ROOM_COMPLETED_STATUSES,
    }


def build_exam_submit_summary(exam, attempt):
    question_rows = _build_exam_question_sequence(exam, attempt)
    answer_map = _build_answer_map(attempt)
    total_questions = len(question_rows)
    answered_count = 0
    marked_count = 0
    for row in question_rows:
        answer = answer_map.get(row["question"].id)
        if _answer_is_filled(answer):
            answered_count += 1
        if answer and answer.is_marked_for_review:
            marked_count += 1

    return {
        "attempt_id": str(attempt.id),
        "exam_id": str(exam.id),
        "exam_title": exam.title,
        "status": attempt.status,
        "status_label": choice_label(ExamAttempt.Status, attempt.status, default=attempt.status),
        "total_questions": total_questions,
        "answered_count": answered_count,
        "unanswered_count": max(total_questions - answered_count, 0),
        "marked_count": marked_count,
        "start_time_label": _datetime_label(attempt.start_time),
        "submit_time_label": _datetime_label(attempt.submit_time),
        "duration_used_label": _duration_label(int(attempt.time_spent_seconds or 0)),
    }


def _decimal_value(value, default=Decimal("0.00")):
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _rounded_decimal(value):
    return _decimal_value(value).quantize(Decimal("0.01"))


def _normalize_text(value, case_sensitive=False):
    text = " ".join(str(value or "").split())
    return text if case_sensitive else text.lower()


def _evaluate_short_answer(question, answer_text):
    if not answer_text:
        return None

    correct_answer = getattr(question, "correct_answer", None)
    if not correct_answer:
        return None

    case_sensitive = bool(correct_answer.is_case_sensitive)
    normalized_student = _normalize_text(answer_text, case_sensitive=case_sensitive)
    normalized_expected = _normalize_text(correct_answer.answer_text, case_sensitive=case_sensitive)

    if normalized_expected and normalized_student == normalized_expected:
        return True

    keywords = correct_answer.keywords or []
    clean_keywords = [str(item).strip() for item in keywords if str(item).strip()]
    if clean_keywords:
        if not case_sensitive:
            clean_keywords = [item.lower() for item in clean_keywords]
        if all(keyword in normalized_student for keyword in clean_keywords):
            return True

    return False


def _evaluate_checkbox_answer(question, answer, points_possible):
    correct_ids = {
        str(option.id)
        for option in question.options.filter(is_correct=True)
    }
    selected_ids = set(_normalize_option_id_list(getattr(answer, "selected_option_ids", [])))

    if not correct_ids:
        return False, Decimal("0.00")

    is_correct = selected_ids == correct_ids
    scoring = (question.checkbox_scoring or Question.CheckboxScoring.ALL_OR_NOTHING).strip().lower()
    total_correct = len(correct_ids)

    if scoring == Question.CheckboxScoring.PARTIAL:
        true_positive = len(selected_ids & correct_ids)
        false_positive = len(selected_ids - correct_ids)
        fraction = Decimal(str((true_positive - false_positive) / total_correct))
        points = max(Decimal("0.00"), _rounded_decimal(fraction * points_possible))
        return is_correct, points

    if scoring == Question.CheckboxScoring.PARTIAL_NO_PENALTY:
        true_positive = len(selected_ids & correct_ids)
        fraction = Decimal(str(true_positive / total_correct))
        points = _rounded_decimal(fraction * points_possible)
        return is_correct, points

    return is_correct, (points_possible if is_correct else Decimal("0.00"))


def _lis_length(student, correct):
    index_map = {value: index for index, value in enumerate(correct)}
    sequence = [index_map[item] for item in student if item in index_map]
    tails = []
    for value in sequence:
        position = bisect.bisect_left(tails, value)
        if position == len(tails):
            tails.append(value)
        else:
            tails[position] = value
    return len(tails)


def _evaluate_ordering_answer(question, answer, points_possible):
    correct = [str(item.id) for item in question.ordering_items.all().order_by("correct_order")]
    student = _normalize_option_id_list(getattr(answer, "answer_order_json", []))

    if not correct:
        return False, Decimal("0.00")

    is_correct = student == correct
    if is_correct:
        return True, points_possible

    lis = _lis_length(student, correct)
    points = _rounded_decimal(Decimal(str(lis / len(correct))) * points_possible)
    return False, points


def _evaluate_matching_answer(question, answer, points_possible):
    student_map = _normalize_matching_answer_map(getattr(answer, "answer_matching_json", {}))
    correct_map = {str(pair.id): str(pair.id) for pair in question.matching_pairs.all()}
    total = len(correct_map)
    if total <= 0:
        return False, Decimal("0.00")

    correct_count = sum(1 for pair_id, answer_id in student_map.items() if correct_map.get(pair_id) == answer_id)
    points = _rounded_decimal(Decimal(str(correct_count / total)) * points_possible)
    return correct_count == total, points


def _evaluate_fill_in_blank_answer(question, answer, points_possible):
    student_blanks = _normalize_blank_answer_map(getattr(answer, "answer_blanks_json", {}))
    blank_defs = list(question.blank_answers.all().order_by("blank_number"))
    if not blank_defs:
        return False, Decimal("0.00")

    auto_points = points_possible / Decimal(str(len(blank_defs)))
    total_points = Decimal("0.00")
    correct_count = 0

    for blank_def in blank_defs:
        raw_value = str(student_blanks.get(str(blank_def.blank_number), "")).strip()
        if not raw_value:
            continue

        accepted_answers = [str(item).strip() for item in (blank_def.accepted_answers or []) if str(item).strip()]
        if not accepted_answers:
            continue

        normalized_value = _normalize_text(raw_value, case_sensitive=blank_def.is_case_sensitive)
        matched = normalized_value in {
            _normalize_text(item, case_sensitive=blank_def.is_case_sensitive)
            for item in accepted_answers
        }

        if not matched:
            continue

        correct_count += 1
        awarded = blank_def.blank_points if blank_def.blank_points is not None else auto_points
        total_points += _decimal_value(awarded, default=Decimal("0.00"))

    points = min(_rounded_decimal(total_points), points_possible)
    return correct_count == len(blank_defs), points


def _grade_letter_from_percentage(percentage_value):
    percentage = _decimal_value(percentage_value)
    if percentage >= Decimal("85"):
        return "A"
    if percentage >= Decimal("75"):
        return "B"
    if percentage >= Decimal("65"):
        return "C"
    if percentage >= Decimal("50"):
        return "D"
    return "E"


def _calculate_time_efficiency(exam, time_taken_seconds):
    planned_seconds = max(int(exam.duration_minutes or 0) * 60, 1)
    used_seconds = max(int(time_taken_seconds or 0), 0)
    if used_seconds <= 0:
        return Decimal("0.00")
    efficiency = min((planned_seconds / used_seconds) * 100, 100.0)
    return _rounded_decimal(efficiency)


def _is_lock_wait_error(exc):
    code = None
    if isinstance(getattr(exc, "args", None), (list, tuple)) and exc.args:
        code = exc.args[0]
    try:
        code = int(code)
    except (TypeError, ValueError):
        code = None
    return code in MYSQL_LOCK_TIMEOUT_CODES


def _safe_violation_count(attempt_id, fallback=0):
    try:
        return ExamViolation.objects.filter(attempt_id=attempt_id).count()
    except OperationalError:
        return int(fallback or 0)


def _refresh_exam_rankings(exam_id):
    results = list(
        ExamResult.objects.filter(exam_id=exam_id).order_by(
            "-percentage",
            "-total_score",
            "time_taken_seconds",
            "created_at",
        )
    )
    total = len(results)
    if not total:
        return

    changed = []
    for idx, result in enumerate(results, start=1):
        if total == 1:
            percentile = Decimal("100.00")
        else:
            percentile = _rounded_decimal(((total - idx) / (total - 1)) * 100)

        if result.rank_in_exam != idx or result.percentile != percentile:
            result.rank_in_exam = idx
            result.percentile = percentile
            changed.append(result)

    if changed:
        ExamResult.objects.bulk_update(changed, ["rank_in_exam", "percentile", "updated_at"])


def _refresh_exam_rankings_safe(exam_id):
    try:
        _refresh_exam_rankings(exam_id)
    except Exception:
        logger.exception("Failed to refresh exam rankings for exam_id=%s", exam_id)


def _schedule_exam_rankings_refresh(exam_id):
    safe_exam_id = str(exam_id)
    transaction.on_commit(lambda: _refresh_exam_rankings_safe(safe_exam_id))


def _run_post_submit_housekeeping(attempt_id, exam_id):
    attempt_obj = (
        ExamAttempt.objects.select_related("exam", "student")
        .filter(id=attempt_id)
        .first()
    )
    if attempt_obj is None:
        return

    try:
        from apps.results.certificate_services import issue_certificate_for_attempt

        issue_certificate_for_attempt(attempt_obj)
    except Exception:
        logger.exception("Certificate issuance failed after submit for attempt_id=%s", attempt_id)

    try:
        from apps.results.calculators import update_exam_statistics_with_retake

        update_exam_statistics_with_retake(exam_id)
    except Exception:
        logger.exception("Exam statistics update failed after submit for exam_id=%s", exam_id)


def _schedule_post_submit_housekeeping(attempt_id, exam_id):
    safe_attempt_id = str(attempt_id)
    safe_exam_id = str(exam_id)
    transaction.on_commit(lambda: _run_post_submit_housekeeping(safe_attempt_id, safe_exam_id))


@transaction.atomic
def upsert_exam_result_for_attempt(*, exam, attempt):
    exam_rows = list(
        exam.exam_questions.select_related("question", "question__correct_answer")
        .prefetch_related("question__options", "question__ordering_items", "question__matching_pairs", "question__blank_answers")
        .order_by("display_order")
    )
    answer_map = {
        answer.question_id: answer
        for answer in StudentAnswer.objects.filter(attempt=attempt).select_related(
            "selected_option",
            "question",
            "question__correct_answer",
        )
    }

    total_questions = len(exam_rows)
    correct_answers = 0
    wrong_answers = 0
    unanswered = 0
    total_score = Decimal("0.00")
    total_points = Decimal("0.00")

    for row in exam_rows:
        question = row.question
        points_possible = _rounded_decimal(row.points_override if row.points_override is not None else question.points)
        total_points += points_possible

        answer = answer_map.get(question.id)
        is_answered = bool(answer and (
            answer.selected_option_id
            or (answer.selected_option_ids)
            or (answer.answer_order_json)
            or (answer.answer_matching_json)
            or _blank_answer_map_has_values(answer.answer_blanks_json)
            or (answer.answer_text and answer.answer_text.strip())
        ))
        if not is_answered:
            unanswered += 1
            continue

        evaluated_correct = answer.is_correct
        points_earned = _rounded_decimal(answer.points_earned if answer else Decimal("0.00"))

        if question.question_type == Question.QuestionType.MULTIPLE_CHOICE:
            evaluated_correct = bool(answer.selected_option and answer.selected_option.is_correct)
            points_earned = points_possible if evaluated_correct else Decimal("0.00")
        elif question.question_type == Question.QuestionType.CHECKBOX:
            evaluated_correct, points_earned = _evaluate_checkbox_answer(question, answer, points_possible)
        elif question.question_type == Question.QuestionType.ORDERING:
            evaluated_correct, points_earned = _evaluate_ordering_answer(question, answer, points_possible)
        elif question.question_type == Question.QuestionType.MATCHING:
            evaluated_correct, points_earned = _evaluate_matching_answer(question, answer, points_possible)
        elif question.question_type == Question.QuestionType.FILL_IN_BLANK:
            evaluated_correct, points_earned = _evaluate_fill_in_blank_answer(question, answer, points_possible)
        elif question.question_type == Question.QuestionType.SHORT_ANSWER:
            short_result = _evaluate_short_answer(question, answer.answer_text)
            if short_result is not None:
                evaluated_correct = short_result
                points_earned = points_possible if short_result else Decimal("0.00")
        else:
            if evaluated_correct is None and hasattr(answer, "grading"):
                points_earned = _rounded_decimal(answer.grading.points_awarded)

        answer_updates = []
        if answer.points_possible != points_possible:
            answer.points_possible = points_possible
            answer_updates.append("points_possible")
        if answer.is_correct != evaluated_correct:
            answer.is_correct = evaluated_correct
            answer_updates.append("is_correct")
        if answer.points_earned != points_earned:
            answer.points_earned = points_earned
            answer_updates.append("points_earned")
        if answer_updates:
            answer.save(update_fields=answer_updates + ["updated_at"])

        total_score += points_earned
        if evaluated_correct is True:
            correct_answers += 1
        else:
            wrong_answers += 1

    if total_questions and (correct_answers + wrong_answers + unanswered) < total_questions:
        wrong_answers = max(total_questions - correct_answers - unanswered, wrong_answers)

    if total_points > 0:
        percentage = _rounded_decimal((total_score / total_points) * Decimal("100"))
    else:
        percentage = Decimal("0.00")

    passing_score = _decimal_value(exam.passing_score, default=Decimal("0.00"))
    passed = percentage >= passing_score

    time_taken_seconds = int(attempt.time_spent_seconds or 0)
    if time_taken_seconds <= 0 and attempt.start_time and attempt.submit_time:
        time_taken_seconds = max(int((attempt.submit_time - attempt.start_time).total_seconds()), 0)

    attempt.total_score = _rounded_decimal(total_score)
    attempt.percentage = percentage
    attempt.passed = passed
    attempt.save(update_fields=["total_score", "percentage", "passed", "updated_at"])

    total_violations = _safe_violation_count(attempt.id)
    defaults = {
        "exam": exam,
        "student": attempt.student,
        "total_score": attempt.total_score,
        "percentage": percentage,
        "grade": _grade_letter_from_percentage(percentage),
        "passed": passed,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "unanswered": unanswered,
        "time_taken_seconds": time_taken_seconds,
        "time_efficiency": _calculate_time_efficiency(exam, time_taken_seconds),
        "total_violations": total_violations,
    }
    result, _ = ExamResult.objects.update_or_create(attempt=attempt, defaults=defaults)
    _schedule_exam_rankings_refresh(exam.id)
    return result


@transaction.atomic
def sync_missing_results_for_exam(exam):
    attempts = (
        ExamAttempt.objects.filter(
            exam=exam,
            status__in=EXAM_ROOM_COMPLETED_STATUSES,
        )
        .filter(result__isnull=True)
        .select_related("exam", "student")
    )
    created_count = 0
    for attempt in attempts:
        upsert_exam_result_for_attempt(exam=exam, attempt=attempt)
        created_count += 1
    return created_count


@transaction.atomic
def sync_missing_results_for_student(student):
    attempts = (
        ExamAttempt.objects.filter(
            student=student,
            status__in=EXAM_ROOM_COMPLETED_STATUSES,
        )
        .filter(result__isnull=True)
        .select_related("exam", "student")
    )
    created_count = 0
    for attempt in attempts:
        upsert_exam_result_for_attempt(exam=attempt.exam, attempt=attempt)
        created_count += 1
    return created_count


def _resolve_final_attempt_id(exam, attempts_with_results):
    if not attempts_with_results:
        return None
    policy = (exam.retake_score_policy or "highest").strip().lower()
    if policy == "latest":
        return max(
            attempts_with_results,
            key=lambda row: int(row["attempt"].attempt_number or 0),
        )["attempt"].id
    if policy == "average":
        return max(
            attempts_with_results,
            key=lambda row: int(row["attempt"].attempt_number or 0),
        )["attempt"].id
    return max(
        attempts_with_results,
        key=lambda row: (
            float(row["result"].total_score if row["result"] else 0),
            int(row["attempt"].attempt_number or 0),
        ),
    )["attempt"].id


def get_attempt_history_for_exam(*, exam, student):
    attempts = list(
        ExamAttempt.objects.filter(exam=exam, student=student)
        .select_related("exam", "student")
        .order_by("attempt_number", "created_at")
    )
    if not attempts:
        return []

    result_map = {
        result.attempt_id: result
        for result in ExamResult.objects.filter(attempt_id__in=[item.id for item in attempts])
    }
    attempts_with_results = [
        {"attempt": attempt, "result": result_map.get(attempt.id)}
        for attempt in attempts
        if attempt.status in EXAM_ROOM_COMPLETED_STATUSES
    ]
    final_attempt_id = _resolve_final_attempt_id(exam, attempts_with_results)

    rows = []
    for attempt in attempts:
        result = result_map.get(attempt.id)
        rows.append(
            {
                "attempt_id": str(attempt.id),
                "attempt_number": int(attempt.attempt_number or 0),
                "status": attempt.status,
                "status_label": choice_label(ExamAttempt.Status, attempt.status, default=attempt.status),
                "start_time": attempt.start_time,
                "submit_time": attempt.submit_time,
                "retake_available_from": attempt.retake_available_from,
                "total_score": round(float(result.total_score), 2) if result else round(float(attempt.total_score or 0), 2),
                "percentage": round(float(result.percentage), 2) if result else round(float(attempt.percentage or 0), 2),
                "passed": bool(result.passed if result else attempt.passed),
                "time_spent_seconds": int(attempt.time_spent_seconds or 0),
                "is_final": bool(final_attempt_id and final_attempt_id == attempt.id),
            }
        )
    return rows


@transaction.atomic
def submit_attempt(*, exam, attempt, auto_submit=False, reason=""):
    if attempt.status in EXAM_ROOM_COMPLETED_STATUSES:
        if (
            exam.allow_retake
            and attempt.retake_available_from is None
            and attempt.submit_time
            and int(attempt.attempt_number or 0) < int(exam.max_retake_attempts or 1)
        ):
            attempt.retake_available_from = attempt.submit_time + timedelta(
                minutes=int(exam.retake_cooldown_minutes or 0)
            )
            attempt.save(update_fields=["retake_available_from", "updated_at"])

        if not ExamResult.objects.filter(attempt_id=attempt.id).exists():
            upsert_exam_result_for_attempt(exam=exam, attempt=attempt)
        eligibility = check_retake_eligibility(exam.id, attempt.student_id)
        return {
            "attempt": attempt,
            "summary": build_exam_submit_summary(exam, attempt),
            "auto_submitted": attempt.status == ExamAttempt.Status.AUTO_SUBMITTED,
            "reason": "",
            "already_submitted": True,
            "retake_eligibility": eligibility,
        }

    now = timezone.now()
    if not attempt.start_time:
        attempt.start_time = now

    elapsed = max(int((now - attempt.start_time).total_seconds()), 0)
    attempt.time_spent_seconds = max(int(attempt.time_spent_seconds or 0), elapsed)
    attempt.submit_time = now
    attempt.end_time = now
    attempt.status = ExamAttempt.Status.AUTO_SUBMITTED if auto_submit else ExamAttempt.Status.SUBMITTED
    if exam.allow_retake and int(attempt.attempt_number or 0) < int(exam.max_retake_attempts or 1):
        attempt.retake_available_from = now + timedelta(minutes=int(exam.retake_cooldown_minutes or 0))
    else:
        attempt.retake_available_from = None
    attempt.save(
        update_fields=[
            "start_time",
            "submit_time",
            "end_time",
            "retake_available_from",
            "status",
            "time_spent_seconds",
            "updated_at",
        ]
    )
    upsert_exam_result_for_attempt(exam=exam, attempt=attempt)
    _schedule_post_submit_housekeeping(attempt.id, exam.id)
    eligibility = check_retake_eligibility(exam.id, attempt.student_id)

    return {
        "attempt": attempt,
        "summary": build_exam_submit_summary(exam, attempt),
        "auto_submitted": auto_submit,
        "reason": reason,
        "already_submitted": False,
        "retake_eligibility": eligibility,
    }


def auto_submit_if_time_expired(*, exam, attempt):
    if attempt.status in EXAM_ROOM_COMPLETED_STATUSES:
        return attempt, False, None

    remaining = get_attempt_remaining_seconds(exam, attempt)
    if remaining > 0:
        return attempt, False, None

    submission = submit_attempt(
        exam=exam,
        attempt=attempt,
        auto_submit=True,
        reason="Waktu pengerjaan habis dan ujian dikirim otomatis.",
    )
    return submission["attempt"], True, submission


@transaction.atomic
def save_attempt_answer(*, exam, attempt, question_number, payload):
    attempt, auto_submitted, auto_submission = auto_submit_if_time_expired(exam=exam, attempt=attempt)
    if auto_submitted:
        return {
            "saved": False,
            "auto_submitted": True,
            "submission": auto_submission,
            "payload": build_exam_room_payload(exam=exam, attempt=attempt, current_number=question_number),
            "message": "Waktu ujian sudah habis. Ujian otomatis disubmit.",
        }

    if attempt.status in EXAM_ROOM_COMPLETED_STATUSES:
        raise ValueError("Attempt ujian sudah selesai dan tidak dapat diubah.")

    question_rows = _build_exam_question_sequence(exam, attempt)
    current_row = _get_row_by_number(question_rows, question_number)
    if not current_row:
        raise ValueError("Nomor soal tidak valid.")

    question = current_row["question"]
    answer = StudentAnswer.objects.filter(attempt=attempt, question=question).first()

    clear_answer = _coerce_bool(payload.get("clear_answer"), default=False)
    is_marked_present = "is_marked_for_review" in payload
    if is_marked_present:
        is_marked_for_review = _coerce_bool(payload.get("is_marked_for_review"), default=False)
    else:
        is_marked_for_review = bool(answer and answer.is_marked_for_review)

    selected_option = answer.selected_option if answer else None
    selected_option_ids = _normalize_option_id_list(answer.selected_option_ids if answer else [])
    answer_order_json = _normalize_option_id_list(answer.answer_order_json if answer else [])
    answer_matching_json = _normalize_matching_answer_map(answer.answer_matching_json if answer else {})
    answer_blanks_json = _normalize_blank_answer_map(answer.answer_blanks_json if answer else {})
    answer_text = (answer.answer_text or "") if answer else ""

    if question.question_type == Question.QuestionType.MULTIPLE_CHOICE:
        selected_option_id = ""
        if clear_answer:
            selected_option_id = ""
        elif "selected_option_id" in payload:
            selected_option_id = str(payload.get("selected_option_id") or "").strip()
        elif answer and answer.selected_option_id:
            selected_option_id = str(answer.selected_option_id)

        if selected_option_id:
            option_map = {str(item.id): item for item in current_row["options"]}
            selected_option = option_map.get(selected_option_id)
            if not selected_option:
                raise ValueError("Opsi jawaban tidak valid untuk soal ini.")
        else:
            selected_option = None
        selected_option_ids = []
        answer_text = ""
    elif question.question_type == Question.QuestionType.CHECKBOX:
        if clear_answer:
            selected_option_ids = []
        elif "selected_option_ids" in payload:
            selected_option_ids = _normalize_option_id_list(payload.get("selected_option_ids"))
        elif answer:
            selected_option_ids = _normalize_option_id_list(answer.selected_option_ids)

        option_map = {str(item.id): item for item in current_row["options"]}
        invalid_option_ids = [item for item in selected_option_ids if item not in option_map]
        if invalid_option_ids:
            raise ValueError("Opsi jawaban checkbox tidak valid untuk soal ini.")
        selected_option = None
        answer_order_json = []
        answer_text = ""
    elif question.question_type == Question.QuestionType.ORDERING:
        if clear_answer:
            answer_order_json = []
        elif "answer_order_json" in payload:
            answer_order_json = _normalize_option_id_list(payload.get("answer_order_json"))
        elif answer:
            answer_order_json = _normalize_option_id_list(answer.answer_order_json)

        ordering_item_ids = {str(item.id) for item in current_row["ordering_items"]}
        invalid_order_ids = [item_id for item_id in answer_order_json if item_id not in ordering_item_ids]
        if invalid_order_ids:
            raise ValueError("Item ordering tidak valid untuk soal ini.")
        if answer_order_json and set(answer_order_json) != ordering_item_ids:
            raise ValueError("Urutan jawaban ordering harus memuat seluruh item soal.")
        selected_option = None
        selected_option_ids = []
        answer_matching_json = {}
        answer_blanks_json = {}
        answer_text = ""
    elif question.question_type == Question.QuestionType.MATCHING:
        if clear_answer:
            answer_matching_json = {}
        elif "answer_matching_json" in payload:
            answer_matching_json = _normalize_matching_answer_map(payload.get("answer_matching_json"))
        elif answer:
            answer_matching_json = _normalize_matching_answer_map(answer.answer_matching_json)

        pair_ids = {str(item.id) for item in current_row["matching_pairs"]}
        answer_choice_ids = {str(item.id) for item in current_row["matching_answer_choices"]}
        invalid_prompt_ids = [item_id for item_id in answer_matching_json.keys() if item_id not in pair_ids]
        invalid_answer_ids = [item_id for item_id in answer_matching_json.values() if item_id not in answer_choice_ids]
        if invalid_prompt_ids or invalid_answer_ids:
            raise ValueError("Pasangan jawaban matching tidak valid untuk soal ini.")
        selected_option = None
        selected_option_ids = []
        answer_order_json = []
        answer_blanks_json = {}
        answer_text = ""
    elif question.question_type == Question.QuestionType.FILL_IN_BLANK:
        if clear_answer:
            answer_blanks_json = {}
        elif "answer_blanks_json" in payload:
            answer_blanks_json = _normalize_blank_answer_map(payload.get("answer_blanks_json"))
        elif answer:
            answer_blanks_json = _normalize_blank_answer_map(answer.answer_blanks_json)

        valid_blank_numbers = {str(item.blank_number) for item in current_row["blank_answers"]}
        invalid_blank_numbers = [item_key for item_key in answer_blanks_json.keys() if item_key not in valid_blank_numbers]
        if invalid_blank_numbers:
            raise ValueError("Blank jawaban tidak valid untuk soal ini.")
        selected_option = None
        selected_option_ids = []
        answer_order_json = []
        answer_matching_json = {}
        answer_text = ""
    else:
        if clear_answer:
            answer_text = ""
        elif "answer_text" in payload:
            answer_text = str(payload.get("answer_text") or "")
        elif answer:
            answer_text = answer.answer_text or ""
        selected_option = None
        selected_option_ids = []
        answer_order_json = []
        answer_matching_json = {}
        answer_blanks_json = {}

    if question.question_type == Question.QuestionType.MULTIPLE_CHOICE:
        has_answer = bool(selected_option)
    elif question.question_type == Question.QuestionType.CHECKBOX:
        has_answer = bool(selected_option_ids)
    elif question.question_type == Question.QuestionType.ORDERING:
        has_answer = bool(answer_order_json)
    elif question.question_type == Question.QuestionType.MATCHING:
        has_answer = bool(answer_matching_json)
    elif question.question_type == Question.QuestionType.FILL_IN_BLANK:
        has_answer = _blank_answer_map_has_values(answer_blanks_json)
    else:
        has_answer = bool(answer_text.strip())
    points_possible = _resolve_points_possible(current_row)

    if answer is None and (has_answer or is_marked_for_review):
        answer = StudentAnswer(
            attempt=attempt,
            question=question,
            answer_type=question.question_type,
            points_possible=points_possible,
            answer_order=question_number,
        )

    if answer is not None:
        answer.answer_type = question.question_type
        answer.points_possible = points_possible
        answer.answer_order = question_number
        answer.is_marked_for_review = is_marked_for_review
        if question.question_type == Question.QuestionType.MULTIPLE_CHOICE:
            answer.selected_option = selected_option
            answer.selected_option_ids = []
            answer.answer_order_json = []
            answer.answer_matching_json = {}
            answer.answer_blanks_json = {}
            answer.answer_text = None
        elif question.question_type == Question.QuestionType.CHECKBOX:
            answer.selected_option = None
            answer.selected_option_ids = selected_option_ids
            answer.answer_order_json = []
            answer.answer_matching_json = {}
            answer.answer_blanks_json = {}
            answer.answer_text = None
        elif question.question_type == Question.QuestionType.ORDERING:
            answer.selected_option = None
            answer.selected_option_ids = []
            answer.answer_order_json = answer_order_json
            answer.answer_matching_json = {}
            answer.answer_blanks_json = {}
            answer.answer_text = None
        elif question.question_type == Question.QuestionType.MATCHING:
            answer.selected_option = None
            answer.selected_option_ids = []
            answer.answer_order_json = []
            answer.answer_matching_json = answer_matching_json
            answer.answer_blanks_json = {}
            answer.answer_text = None
        elif question.question_type == Question.QuestionType.FILL_IN_BLANK:
            answer.selected_option = None
            answer.selected_option_ids = []
            answer.answer_order_json = []
            answer.answer_matching_json = {}
            answer.answer_blanks_json = answer_blanks_json
            answer.answer_text = None
        else:
            answer.selected_option = None
            answer.selected_option_ids = []
            answer.answer_order_json = []
            answer.answer_matching_json = {}
            answer.answer_blanks_json = {}
            answer.answer_text = answer_text

        if has_answer or is_marked_for_review:
            answer.save()
        else:
            answer.delete()

    refreshed = build_exam_room_payload(
        exam=exam,
        attempt=attempt,
        current_number=question_number,
        requested_number=question_number,
        enforce_navigation=False,
    )
    return {
        "saved": True,
        "auto_submitted": False,
        "submission": None,
        "payload": refreshed,
        "message": "Jawaban berhasil disimpan otomatis.",
    }


@transaction.atomic
def record_exam_violation(*, exam, attempt, violation_type, description=""):
    normalized_type = (violation_type or "").strip()
    valid_types = {member.value for member in ExamViolation.ViolationType}
    if normalized_type not in valid_types:
        raise ValueError("Jenis pelanggaran tidak valid.")

    if attempt.status in EXAM_ROOM_COMPLETED_STATUSES:
        return {
            "logged": False,
            "already_submitted": True,
            "auto_submitted": False,
            "violations_count": _safe_violation_count(attempt.id),
            "max_violations_allowed": int(exam.max_violations_allowed or 0),
            "message": "Attempt sudah selesai.",
            "submission": None,
        }

    clean_description = (description or "").strip()[:500]
    try:
        ExamViolation.objects.create(
            attempt=attempt,
            violation_type=normalized_type,
            description=clean_description,
            severity=VIOLATION_SEVERITY_MAP.get(normalized_type, ExamViolation.Severity.MEDIUM),
        )
        violations_count = _safe_violation_count(attempt.id)
    except OperationalError as exc:
        if not _is_lock_wait_error(exc):
            raise
        latest_status = (
            ExamAttempt.objects.filter(id=attempt.id).values_list("status", flat=True).first()
            or attempt.status
        )
        return {
            "logged": False,
            "already_submitted": latest_status in EXAM_ROOM_COMPLETED_STATUSES,
            "auto_submitted": False,
            "violations_count": _safe_violation_count(attempt.id),
            "max_violations_allowed": int(exam.max_violations_allowed or 0),
            "message": "Sistem sedang memproses submit ujian. Pelanggaran ini akan dilewati sementara.",
            "submission": None,
        }

    max_violations_allowed = int(exam.max_violations_allowed or 0)
    auto_submitted = False
    submission = None

    if max_violations_allowed > 0 and violations_count >= max_violations_allowed:
        submission = submit_attempt(
            exam=exam,
            attempt=attempt,
            auto_submit=True,
            reason="Batas pelanggaran anti-cheat telah terlampaui.",
        )
        auto_submitted = True

    return {
        "logged": True,
        "already_submitted": False,
        "auto_submitted": auto_submitted,
        "violations_count": violations_count,
        "max_violations_allowed": max_violations_allowed,
        "message": "Pelanggaran berhasil dicatat.",
        "submission": submission,
    }


@transaction.atomic
def record_proctoring_capture(
    *,
    exam,
    attempt,
    snapshot_label="capture",
    screenshot_data_url="",
    request_base_url="",
):
    if attempt.status in EXAM_ROOM_COMPLETED_STATUSES:
        return {"captured": False, "message": "Attempt sudah selesai."}
    if not exam.enable_screenshot_proctoring:
        return {"captured": False, "message": "Fitur screenshot proctoring tidak aktif."}

    label = "".join(ch for ch in str(snapshot_label or "capture") if ch.isalnum() or ch in {"-", "_"})
    label = (label or "capture")[:24]
    stamp = timezone.localtime(timezone.now()).strftime("%Y%m%d%H%M%S")
    image_info = _decode_proctoring_data_url(screenshot_data_url)

    if not image_info:
        return {"captured": False, "message": "Data screenshot tidak valid atau kosong."}

    image_bytes, extension = image_info
    relative_path = f"proctoring/{attempt.id}/{stamp}-{label}.{extension}"
    saved_path = default_storage.save(relative_path, ContentFile(image_bytes))
    public_url = default_storage.url(saved_path)
    screenshot_url = (
        urljoin(request_base_url, public_url)
        if request_base_url and public_url.startswith("/")
        else public_url
    )

    try:
        screenshot = ProctoringScreenshot.objects.create(
            attempt=attempt,
            screenshot_url=screenshot_url,
            file_size_kb=max(1, round(len(image_bytes) / 1024)),
            is_flagged=False,
        )
    except OperationalError as exc:
        if not _is_lock_wait_error(exc):
            raise
        return {
            "captured": False,
            "message": "Sistem sedang memproses submit ujian. Snapshot proctoring dilewati sementara.",
        }

    return {
        "captured": True,
        "message": "Snapshot proctoring berhasil dicatat.",
        "screenshot_id": str(screenshot.id),
        "captured_at": _datetime_label(screenshot.capture_time),
    }


def _decode_proctoring_data_url(raw_value):
    if not raw_value or not isinstance(raw_value, str):
        return None
    value = raw_value.strip()
    if not value.startswith("data:image/"):
        return None

    header, separator, encoded = value.partition(",")
    if not separator:
        return None

    extension = "jpg"
    header_lower = header.lower()
    if "image/png" in header_lower:
        extension = "png"
    elif "image/webp" in header_lower:
        extension = "webp"

    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return None

    if not image_bytes:
        return None
    if len(image_bytes) > 5 * 1024 * 1024:
        return None

    return image_bytes, extension
