from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.html import strip_tags

from apps.accounts.models import User, UserProfile
from apps.attempts.models import ExamAttempt, ExamViolation, ProctoringScreenshot, StudentAnswer
from apps.core.enums import choice_label, get_enum_badge_tone
from apps.exams.models import ClassStudent, Exam
from apps.notifications.models import Notification
from apps.results.models import ExamResult


COMPLETED_ATTEMPT_STATUSES = {
    ExamAttempt.Status.SUBMITTED,
    ExamAttempt.Status.AUTO_SUBMITTED,
    ExamAttempt.Status.COMPLETED,
}
STATUS_PRIORITY = {
    "active": 0,
    "idle": 1,
    "submitted": 2,
    "grading": 3,
    "not_started": 4,
    "unknown": 5,
}
SEVERITY_LABELS = {
    value: choice_label(ExamViolation.Severity, value)
    for value in (
        ExamViolation.Severity.LOW,
        ExamViolation.Severity.MEDIUM,
        ExamViolation.Severity.HIGH,
        ExamViolation.Severity.CRITICAL,
    )
}


def _display_name(user: User) -> str:
    full_name = (user.get_full_name() or "").strip()
    return full_name or user.username


def _profile_for_user(user_id, profile_map):
    return profile_map.get(user_id)


def _duration_label(total_seconds: int) -> str:
    total = max(int(total_seconds or 0), 0)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _attempt_deadline(exam: Exam, attempt: ExamAttempt):
    if attempt.end_time:
        return attempt.end_time
    if attempt.start_time:
        return attempt.start_time + timedelta(minutes=exam.duration_minutes)
    return None


def _remaining_seconds(exam: Exam, attempt: ExamAttempt, now):
    if attempt.status in COMPLETED_ATTEMPT_STATUSES:
        return 0
    deadline = _attempt_deadline(exam, attempt)
    if deadline:
        return max(int((deadline - now).total_seconds()), 0)
    return max(int(exam.duration_minutes * 60), 0)


def _attempt_status(attempt: ExamAttempt, now):
    if attempt.status in COMPLETED_ATTEMPT_STATUSES:
        return "submitted", "Sudah Submit"
    if attempt.status == ExamAttempt.Status.IN_PROGRESS:
        last_seen = attempt.updated_at or attempt.start_time or attempt.created_at
        if last_seen and (now - last_seen) >= timedelta(minutes=5):
            return "idle", "Idle"
        return "active", "Aktif"
    if attempt.status == ExamAttempt.Status.NOT_STARTED:
        return "not_started", "Belum Mulai"
    if attempt.status == ExamAttempt.Status.GRADING:
        return "grading", "Penilaian"
    return "unknown", "Tidak Diketahui"


def _status_indicator(status_key: str, violations_count: int, max_violations_allowed: int):
    if status_key == "submitted":
        return "primary", "Sudah submit"
    if max_violations_allowed > 0 and violations_count >= max_violations_allowed:
        return "danger", "Pelanggaran tinggi"
    if status_key == "idle" or violations_count > 0:
        return "warning", "Perlu perhatian"
    if status_key == "active":
        return "success", "Normal"
    if status_key == "not_started":
        return "secondary", "Belum mulai"
    return "secondary", "Status tidak dikenal"


def _serialize_violation(violation: ExamViolation):
    severity = (violation.severity or ExamViolation.Severity.MEDIUM).lower()
    if severity not in SEVERITY_LABELS:
        severity = ExamViolation.Severity.MEDIUM
    return {
        "id": str(violation.id),
        "student_id": str(violation.attempt.student_id),
        "student_name": _display_name(violation.attempt.student),
        "violation_type": violation.violation_type,
        "violation_label": violation.get_violation_type_display(),
        "description": violation.description or "-",
        "severity": severity,
        "severity_label": choice_label(ExamViolation.Severity, severity, default=SEVERITY_LABELS[ExamViolation.Severity.MEDIUM]),
        "severity_badge": get_enum_badge_tone("violation_severity", severity),
        "detected_at": timezone.localtime(violation.detected_at).isoformat(),
        "detected_at_label": timezone.localtime(violation.detected_at).strftime("%d %b %Y %H:%M:%S"),
    }


def get_teacher_exam_or_404(exam_id, teacher: User):
    return get_object_or_404(
        Exam.objects.filter(
            id=exam_id,
            created_by=teacher,
            is_deleted=False,
        ).select_related("subject"),
        id=exam_id,
    )


def _resolve_assigned_student_ids(exam: Exam):
    assignments = exam.assignments.all()
    direct_student_ids = {
        assignment.student_id
        for assignment in assignments
        if assignment.assigned_to_type == "student" and assignment.student_id
    }
    class_ids = [
        assignment.class_obj_id
        for assignment in assignments
        if assignment.assigned_to_type == "class" and assignment.class_obj_id
    ]
    class_student_ids = set(
        ClassStudent.objects.filter(class_obj_id__in=class_ids).values_list("student_id", flat=True)
    )
    return set(direct_student_ids) | class_student_ids


def _resolve_monitoring_target_users(exam: Exam):
    assigned_ids = _resolve_assigned_student_ids(exam)
    attempted_ids = set(ExamAttempt.objects.filter(exam=exam).values_list("student_id", flat=True))
    target_ids = assigned_ids | attempted_ids
    if not target_ids:
        return User.objects.none()
    return (
        User.objects.filter(
            id__in=target_ids,
            role="student",
            is_deleted=False,
            is_active=True,
        )
        .order_by("first_name", "last_name", "username")
    )


def _latest_attempt_map(exam: Exam):
    attempt_qs = (
        ExamAttempt.objects.filter(exam=exam)
        .select_related("student")
        .prefetch_related(
            Prefetch(
                "answers",
                queryset=StudentAnswer.objects.only(
                    "id",
                    "attempt_id",
                    "question_id",
                    "answer_order",
                    "time_spent_seconds",
                    "created_at",
                    "updated_at",
                ).order_by("answer_order", "created_at"),
            ),
            Prefetch(
                "violations",
                queryset=ExamViolation.objects.only(
                    "id",
                    "attempt_id",
                    "violation_type",
                    "severity",
                    "detected_at",
                    "description",
                ).order_by("-detected_at"),
            ),
            Prefetch(
                "screenshots",
                queryset=ProctoringScreenshot.objects.only(
                    "id",
                    "attempt_id",
                    "capture_time",
                    "is_flagged",
                ).order_by("-capture_time"),
            ),
        )
        .order_by("student_id", "-attempt_number", "-created_at")
    )
    latest_by_student = {}
    for attempt in attempt_qs:
        if attempt.student_id not in latest_by_student:
            latest_by_student[attempt.student_id] = attempt
    return latest_by_student


def _serialize_student_card(exam: Exam, student: User, profile: UserProfile | None, attempt: ExamAttempt | None, now, total_questions: int):
    if not attempt:
        return {
            "student_id": str(student.id),
            "attempt_id": "",
            "student_name": _display_name(student),
            "username": student.username,
            "photo_url": (profile.profile_picture_url if profile and profile.profile_picture_url else ""),
            "status_key": "not_started",
            "status_label": "Belum Mulai",
            "indicator": "secondary",
            "indicator_label": "Belum mulai",
            "progress_percent": 0,
            "answered_count": 0,
            "total_questions": total_questions,
            "current_question": 0,
            "time_remaining_seconds": int(exam.duration_minutes * 60),
            "time_remaining_label": _duration_label(int(exam.duration_minutes * 60)),
            "violations_count": 0,
            "last_seen_label": "-",
            "screenshot_count": 0,
            "can_intervene": False,
            "attempt_number": 0,
            "max_attempts": int(exam.max_retake_attempts or 1),
            "show_attempt_badge": bool(exam.allow_retake),
        }

    status_key, status_label = _attempt_status(attempt, now)
    violations_count = len(attempt.violations.all())
    indicator, indicator_label = _status_indicator(status_key, violations_count, exam.max_violations_allowed)

    answered_ids = {answer.question_id for answer in attempt.answers.all() if answer.question_id}
    answered_count = len(answered_ids)
    progress_percent = round((answered_count / total_questions) * 100, 1) if total_questions else 0.0

    current_question = 0
    max_order = 0
    for answer in attempt.answers.all():
        max_order = max(max_order, int(answer.answer_order or 0))
    if status_key == "submitted":
        current_question = total_questions
    elif max_order > 0:
        current_question = min(max_order, total_questions)
    elif status_key in {"active", "idle"} and total_questions > 0:
        current_question = 1

    remaining_seconds = _remaining_seconds(exam, attempt, now)
    last_seen = attempt.updated_at or attempt.start_time or attempt.created_at
    can_intervene = status_key in {"active", "idle"} and attempt.status not in COMPLETED_ATTEMPT_STATUSES

    return {
        "student_id": str(student.id),
        "attempt_id": str(attempt.id),
        "student_name": _display_name(student),
        "username": student.username,
        "photo_url": (profile.profile_picture_url if profile and profile.profile_picture_url else ""),
        "status_key": status_key,
        "status_label": status_label,
        "indicator": indicator,
        "indicator_label": indicator_label,
        "progress_percent": progress_percent,
        "answered_count": answered_count,
        "total_questions": total_questions,
        "current_question": current_question,
        "time_remaining_seconds": remaining_seconds,
        "time_remaining_label": _duration_label(remaining_seconds),
        "violations_count": violations_count,
        "last_seen_label": timezone.localtime(last_seen).strftime("%d %b %Y %H:%M:%S") if last_seen else "-",
        "screenshot_count": len(attempt.screenshots.all()),
        "can_intervene": can_intervene,
        "attempt_number": int(attempt.attempt_number or 1),
        "max_attempts": int(exam.max_retake_attempts or 1),
        "show_attempt_badge": bool(exam.allow_retake),
    }


def _build_violation_feed(exam: Exam, violation_type: str = "", limit: int = 50):
    valid_types = {choice[0] for choice in ExamViolation.VIOLATION_TYPE_CHOICES}
    query = ExamViolation.objects.filter(attempt__exam=exam).select_related("attempt__student").order_by("-detected_at")
    if violation_type in valid_types:
        query = query.filter(violation_type=violation_type)
    items = [_serialize_violation(violation) for violation in query[:limit]]
    return items


def build_monitoring_snapshot(exam: Exam, violation_type: str = ""):
    now = timezone.now()
    total_questions = exam.exam_questions.count()
    target_students = list(_resolve_monitoring_target_users(exam))

    attempt_map = _latest_attempt_map(exam)
    student_ids = [student.id for student in target_students]
    profile_map = UserProfile.objects.filter(user_id__in=student_ids).in_bulk(field_name="user_id")

    cards = []
    for student in target_students:
        cards.append(
            _serialize_student_card(
                exam=exam,
                student=student,
                profile=_profile_for_user(student.id, profile_map),
                attempt=attempt_map.get(student.id),
                now=now,
                total_questions=total_questions,
            )
        )

    cards.sort(
        key=lambda item: (
            STATUS_PRIORITY.get(item["status_key"], STATUS_PRIORITY["unknown"]),
            -float(item["progress_percent"]),
            item["student_name"].lower(),
        )
    )

    active_count = sum(1 for item in cards if item["status_key"] == "active")
    completed_count = sum(1 for item in cards if item["status_key"] == "submitted")
    idle_count = sum(1 for item in cards if item["status_key"] == "idle")
    average_progress = round(sum(float(item["progress_percent"]) for item in cards) / len(cards), 1) if cards else 0.0

    violations_feed = _build_violation_feed(exam, violation_type=violation_type, limit=50)
    announcement_targets = [
        {
            "id": str(student.id),
            "name": _display_name(student),
            "username": student.username,
        }
        for student in target_students
    ]

    return {
        "exam": {
            "id": str(exam.id),
            "title": exam.title,
            "subject": exam.subject.name if exam.subject_id else "-",
            "status": exam.status,
            "status_label": exam.get_status_display(),
            "total_questions": total_questions,
            "max_violations_allowed": exam.max_violations_allowed,
            "enable_screenshot_proctoring": exam.enable_screenshot_proctoring,
        },
        "stats": {
            "total_participants": len(cards),
            "currently_active": active_count,
            "completed": completed_count,
            "idle": idle_count,
            "average_progress_percent": average_progress,
            "violations_count": len(violations_feed),
        },
        "students": cards,
        "violations": violations_feed,
        "announcement_targets": announcement_targets,
        "generated_at": timezone.localtime(now).isoformat(),
        "generated_at_label": timezone.localtime(now).strftime("%d %b %Y %H:%M:%S"),
    }


def _get_latest_attempt_for_student(exam: Exam, student_id):
    return (
        ExamAttempt.objects.filter(exam=exam, student_id=student_id)
        .select_related("student", "student__profile")
        .prefetch_related(
            Prefetch(
                "answers",
                queryset=StudentAnswer.objects.select_related("question", "selected_option").order_by("answer_order", "created_at"),
            ),
            Prefetch("violations", queryset=ExamViolation.objects.order_by("-detected_at")),
            Prefetch("screenshots", queryset=ProctoringScreenshot.objects.order_by("-capture_time")),
        )
        .order_by("-attempt_number", "-created_at")
        .first()
    )


def build_student_detail_payload(exam: Exam, student_id):
    student = get_object_or_404(
        User.objects.filter(id=student_id, role="student", is_deleted=False),
        id=student_id,
    )
    profile = UserProfile.objects.filter(user=student).first()
    now = timezone.now()
    total_questions = exam.exam_questions.count()

    attempt = _get_latest_attempt_for_student(exam, student.id)
    if not attempt:
        return {
            "student": {
                "id": str(student.id),
                "name": _display_name(student),
                "username": student.username,
                "photo_url": profile.profile_picture_url if profile and profile.profile_picture_url else "",
            },
            "attempt": None,
            "summary": {
                "progress_percent": 0,
                "answered_count": 0,
                "total_questions": total_questions,
                "time_remaining_label": _duration_label(int(exam.duration_minutes * 60)),
                "violations_count": 0,
            },
            "answers": [],
            "screenshots": [],
            "violations": [],
            "attempt_history": [],
        }

    status_key, status_label = _attempt_status(attempt, now)
    violations_count = attempt.violations.count()
    answered_count = len({answer.question_id for answer in attempt.answers.all() if answer.question_id})
    progress_percent = round((answered_count / total_questions) * 100, 1) if total_questions else 0.0
    remaining_seconds = _remaining_seconds(exam, attempt, now)
    can_intervene = status_key in {"active", "idle"} and attempt.status not in COMPLETED_ATTEMPT_STATUSES

    answers = []
    for idx, answer in enumerate(attempt.answers.all(), start=1):
        question_text = strip_tags(answer.question.question_text or "")
        if answer.answer_type == "multiple_choice":
            if answer.selected_option_id:
                answer_value = f"Opsi {answer.selected_option.option_letter}"
            else:
                answer_value = "Belum memilih opsi"
        elif answer.answer_type == "checkbox":
            answer_value = f"{len(answer.selected_option_ids or [])} opsi dipilih"
        elif answer.answer_type == "ordering":
            answer_value = f"{len(answer.answer_order_json or [])} item diurutkan"
        elif answer.answer_type == "matching":
            answer_value = f"{len((answer.answer_matching_json or {}).keys())} pasangan diisi"
        elif answer.answer_type == "fill_in_blank":
            answer_value = f"{sum(1 for item in (answer.answer_blanks_json or {}).values() if str(item or '').strip())} blank diisi"
        else:
            answer_value = (answer.answer_text or "").strip() or "Belum diisi"
        answers.append(
            {
                "id": str(answer.id),
                "order": answer.answer_order or idx,
                "question_text": question_text,
                "answer_type": answer.answer_type,
                "answer_type_label": answer.get_answer_type_display(),
                "answer_value": answer_value,
                "time_spent_seconds": int(answer.time_spent_seconds or 0),
                "time_spent_label": _duration_label(int(answer.time_spent_seconds or 0)),
                "is_marked_for_review": bool(answer.is_marked_for_review),
                "is_correct": answer.is_correct,
                "points_earned": float(answer.points_earned or 0),
                "points_possible": float(answer.points_possible or 0),
                "updated_at_label": timezone.localtime(answer.updated_at).strftime("%d %b %Y %H:%M:%S"),
            }
        )

    screenshots = []
    for screenshot in attempt.screenshots.all()[:24]:
        screenshots.append(
            {
                "id": str(screenshot.id),
                "url": screenshot.screenshot_url,
                "capture_time": timezone.localtime(screenshot.capture_time).isoformat(),
                "capture_time_label": timezone.localtime(screenshot.capture_time).strftime("%d %b %Y %H:%M:%S"),
                "is_flagged": screenshot.is_flagged,
                "flag_reason": screenshot.flag_reason or "",
            }
        )

    violations = [_serialize_violation(item) for item in attempt.violations.all()[:40]]
    attempt_history = []
    if exam.allow_retake:
        history_attempts = list(
            ExamAttempt.objects.filter(exam=exam, student=student)
            .order_by("attempt_number", "created_at")
        )
        history_result_map = {
            result.attempt_id: result
            for result in ExamResult.objects.filter(attempt_id__in=[item.id for item in history_attempts])
        }
        for history in history_attempts:
            history_result = history_result_map.get(history.id)
            attempt_history.append(
                {
                    "attempt_number": int(history.attempt_number or 0),
                    "start_time_label": timezone.localtime(history.start_time).strftime("%d %b %Y %H:%M:%S")
                    if history.start_time
                    else "-",
                    "submit_time_label": timezone.localtime(history.submit_time).strftime("%d %b %Y %H:%M:%S")
                    if history.submit_time
                    else "-",
                    "status_label": history.get_status_display(),
                    "total_score": float(history_result.total_score) if history_result else float(history.total_score or 0),
                }
            )

    return {
        "student": {
            "id": str(student.id),
            "name": _display_name(student),
            "username": student.username,
            "photo_url": profile.profile_picture_url if profile and profile.profile_picture_url else "",
        },
        "attempt": {
            "id": str(attempt.id),
            "status_key": status_key,
            "status_label": status_label,
            "can_intervene": can_intervene,
            "start_time_label": timezone.localtime(attempt.start_time).strftime("%d %b %Y %H:%M:%S")
            if attempt.start_time
            else "-",
            "submit_time_label": timezone.localtime(attempt.submit_time).strftime("%d %b %Y %H:%M:%S")
            if attempt.submit_time
            else "-",
            "time_spent_seconds": int(attempt.time_spent_seconds or 0),
            "time_spent_label": _duration_label(int(attempt.time_spent_seconds or 0)),
        },
        "summary": {
            "progress_percent": progress_percent,
            "answered_count": answered_count,
            "total_questions": total_questions,
            "time_remaining_seconds": remaining_seconds,
            "time_remaining_label": _duration_label(remaining_seconds),
            "violations_count": violations_count,
            "screenshot_count": len(screenshots),
        },
        "answers": answers,
        "screenshots": screenshots,
        "violations": violations,
        "attempt_history": attempt_history,
    }


@transaction.atomic
def extend_attempt_time(exam: Exam, student_id, minutes: int):
    attempt = _get_latest_attempt_for_student(exam, student_id)
    if not attempt:
        raise ValueError("Siswa belum memiliki attempt pada ujian ini.")
    if attempt.status in COMPLETED_ATTEMPT_STATUSES:
        raise ValueError("Attempt siswa sudah selesai, waktu tidak bisa ditambah.")
    if minutes <= 0:
        raise ValueError("Durasi penambahan waktu harus lebih dari 0 menit.")
    if minutes > 240:
        raise ValueError("Durasi penambahan maksimal 240 menit per aksi.")

    now = timezone.now()
    deadline = _attempt_deadline(exam, attempt)
    if not deadline:
        if attempt.start_time:
            deadline = attempt.start_time + timedelta(minutes=exam.duration_minutes)
        else:
            deadline = now + timedelta(minutes=exam.duration_minutes)

    attempt.end_time = deadline + timedelta(minutes=minutes)
    if not attempt.start_time:
        attempt.start_time = now
    attempt.save(update_fields=["start_time", "end_time", "updated_at"])

    Notification.objects.create(
        user=attempt.student,
        title=f"Penambahan Waktu Ujian: {exam.title}",
        message=f"Waktu pengerjaan Anda ditambah {minutes} menit oleh guru.",
        notification_type=Notification.Type.ANNOUNCEMENT,
        related_entity_type="exam",
        related_entity_id=exam.id,
    )

    remaining_seconds = _remaining_seconds(exam, attempt, now)
    return {
        "attempt_id": str(attempt.id),
        "student_id": str(attempt.student_id),
        "new_end_time": timezone.localtime(attempt.end_time).isoformat(),
        "new_end_time_label": timezone.localtime(attempt.end_time).strftime("%d %b %Y %H:%M:%S"),
        "time_remaining_seconds": remaining_seconds,
        "time_remaining_label": _duration_label(remaining_seconds),
    }


@transaction.atomic
def force_submit_attempt(attempt_id, teacher: User):
    attempt = get_object_or_404(
        ExamAttempt.objects.select_related("exam", "student").filter(
            id=attempt_id,
            exam__created_by=teacher,
            exam__is_deleted=False,
        ),
        id=attempt_id,
    )
    if attempt.status in COMPLETED_ATTEMPT_STATUSES:
        raise ValueError("Attempt ini sudah selesai.")

    now = timezone.now()
    if attempt.start_time and (attempt.time_spent_seconds or 0) <= 0:
        attempt.time_spent_seconds = max(int((now - attempt.start_time).total_seconds()), 0)
    attempt.status = ExamAttempt.Status.AUTO_SUBMITTED
    attempt.submit_time = now
    attempt.end_time = now
    attempt.save(
        update_fields=[
            "status",
            "submit_time",
            "end_time",
            "time_spent_seconds",
            "updated_at",
        ]
    )

    Notification.objects.create(
        user=attempt.student,
        title=f"Attempt Ujian Dihentikan: {attempt.exam.title}",
        message="Attempt ujian Anda dihentikan oleh guru dan otomatis disubmit.",
        notification_type=Notification.Type.WARNING,
        related_entity_type="exam",
        related_entity_id=attempt.exam_id,
    )

    return {
        "attempt_id": str(attempt.id),
        "status": attempt.status,
        "submit_time": timezone.localtime(attempt.submit_time).isoformat() if attempt.submit_time else "",
    }


@transaction.atomic
def send_monitoring_announcement(exam: Exam, message: str, title: str = "", target: str = "all", student_id=None):
    clean_message = (message or "").strip()
    if not clean_message:
        raise ValueError("Isi pesan pengumuman wajib diisi.")
    if len(clean_message) > 1000:
        raise ValueError("Pesan pengumuman maksimal 1000 karakter.")

    clean_title = (title or "").strip() or f"Pengumuman Ujian: {exam.title}"
    if len(clean_title) > 255:
        raise ValueError("Judul pengumuman maksimal 255 karakter.")

    recipients_qs = _resolve_monitoring_target_users(exam)
    if target == "student":
        if not student_id:
            raise ValueError("Pilih siswa tujuan pengumuman.")
        recipients_qs = recipients_qs.filter(id=student_id)

    recipients = list(recipients_qs)
    if not recipients:
        raise ValueError("Tidak ada penerima yang sesuai untuk pengumuman ini.")

    Notification.objects.bulk_create(
        [
            Notification(
                user=user,
                title=clean_title,
                message=clean_message,
                notification_type=Notification.Type.ANNOUNCEMENT,
                related_entity_type="exam",
                related_entity_id=exam.id,
            )
            for user in recipients
        ]
    )

    return {
        "sent_count": len(recipients),
        "target": target,
    }
