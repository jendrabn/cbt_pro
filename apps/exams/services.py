from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal

from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import ClassStudent, Exam, ExamAssignment, ExamQuestion


STATUS_LABELS = {
    "draft": "Draf",
    "published": "Dipublikasikan",
    "ongoing": "Berlangsung",
    "completed": "Selesai",
    "cancelled": "Dibatalkan",
}


@dataclass
class ExamFilterState:
    q: str = ""
    status: str = ""
    subject: str = ""
    date_from: str = ""
    date_to: str = ""
    view_mode: str = "table"


def get_teacher_exam_queryset(teacher):
    return (
        Exam.objects.filter(created_by=teacher, is_deleted=False)
        .select_related("subject")
        .prefetch_related(
            "assignments__class_obj",
            "assignments__student",
            Prefetch(
                "exam_questions",
                queryset=ExamQuestion.objects.select_related("question").order_by("display_order"),
            ),
        )
        .order_by("-created_at")
    )


def filter_teacher_exams(queryset, params):
    filters = ExamFilterState(
        q=(params.get("q") or "").strip(),
        status=(params.get("status") or "").strip(),
        subject=(params.get("subject") or "").strip(),
        date_from=(params.get("date_from") or "").strip(),
        date_to=(params.get("date_to") or "").strip(),
        view_mode=(params.get("view") or "table").strip(),
    )

    if filters.q:
        queryset = queryset.filter(
            Q(title__icontains=filters.q)
            | Q(description__icontains=filters.q)
            | Q(subject__name__icontains=filters.q)
        )
    if filters.status in STATUS_LABELS:
        queryset = queryset.filter(status=filters.status)
    if filters.subject:
        queryset = queryset.filter(subject_id=filters.subject)
    current_tz = timezone.get_current_timezone()
    date_from = parse_date(filters.date_from) if filters.date_from else None
    date_to = parse_date(filters.date_to) if filters.date_to else None
    if date_from:
        dt_from = timezone.make_aware(datetime.combine(date_from, time.min), current_tz)
        queryset = queryset.filter(start_time__gte=dt_from)
    if date_to:
        dt_to = timezone.make_aware(datetime.combine(date_to, time.max), current_tz)
        queryset = queryset.filter(end_time__lte=dt_to)
    if filters.view_mode not in {"table", "cards"}:
        filters.view_mode = "table"

    return queryset.order_by("-start_time"), filters


def _participant_count_for_exam(exam):
    direct_student_ids = {
        str(assignment.student_id)
        for assignment in exam.assignments.all()
        if assignment.assigned_to_type == "student" and assignment.student_id
    }
    class_ids = [
        assignment.class_obj_id
        for assignment in exam.assignments.all()
        if assignment.assigned_to_type == "class" and assignment.class_obj_id
    ]
    class_student_ids = set(
        str(student_id)
        for student_id in ClassStudent.objects.filter(class_obj_id__in=class_ids).values_list("student_id", flat=True)
    )
    return len(direct_student_ids | class_student_ids)


def build_exam_list_rows(exams_qs):
    rows = []
    for exam in exams_qs:
        rows.append(
            {
                "exam": exam,
                "participant_count": _participant_count_for_exam(exam),
                "question_count": exam.exam_questions.count(),
                "status_label": STATUS_LABELS.get(exam.status, exam.status),
                "retake_badge": f"🔁 {exam.max_retake_attempts}x" if exam.allow_retake else "",
            }
        )
    return rows


@transaction.atomic
def save_exam_from_form(form, teacher, instance=None):
    cleaned = form.cleaned_data
    is_create = instance is None
    exam = form.save(commit=False)
    if is_create:
        exam.created_by = teacher

    exam.status = "published" if cleaned.get("status_action") == "publish" else "draft"
    exam.save()

    question_items = sorted(cleaned.get("parsed_questions", []), key=lambda item: item["display_order"])
    ExamQuestion.objects.filter(exam=exam).delete()

    exam_question_objects = []
    total_points = Decimal("0.00")
    for idx, item in enumerate(question_items, start=1):
        points_value = item["points_override"] if item["points_override"] is not None else item["default_points"]
        total_points += Decimal(points_value)
        exam_question_objects.append(
            ExamQuestion(
                exam=exam,
                question=item["question_obj"],
                display_order=idx,
                points_override=item["points_override"],
                override_navigation=item["override_navigation"],
                allow_previous_override=item["allow_previous_override"],
                allow_next_override=item["allow_next_override"],
                force_sequential_override=item["force_sequential_override"],
            )
        )
    ExamQuestion.objects.bulk_create(exam_question_objects)

    ExamAssignment.objects.filter(exam=exam).delete()
    assignment_objects = []
    for item in cleaned.get("parsed_assignments", []):
        if item["type"] == "class":
            assignment_objects.append(
                ExamAssignment(
                    exam=exam,
                    assigned_to_type="class",
                    class_obj_id=item["id"],
                )
            )
        else:
            assignment_objects.append(
                ExamAssignment(
                    exam=exam,
                    assigned_to_type="student",
                    student_id=item["id"],
                )
            )
    ExamAssignment.objects.bulk_create(assignment_objects)

    exam.total_points = total_points
    exam.save(update_fields=["total_points", "status", "updated_at"])
    return exam


@transaction.atomic
def soft_delete_exam(exam):
    exam.is_deleted = True
    exam.save(update_fields=["is_deleted"])


@transaction.atomic
def toggle_publish_exam(exam):
    if exam.status == "draft":
        exam.status = "published"
    elif exam.status == "published":
        exam.status = "draft"
    exam.save(update_fields=["status", "updated_at"])
    return exam


@transaction.atomic
def duplicate_exam(exam, teacher):
    new_exam = Exam.objects.create(
        created_by=teacher,
        subject=exam.subject,
        title=f"{exam.title} (Salinan)",
        description=exam.description,
        instructions=exam.instructions,
        start_time=exam.start_time,
        end_time=exam.end_time,
        duration_minutes=exam.duration_minutes,
        passing_score=exam.passing_score,
        total_points=exam.total_points,
        randomize_questions=exam.randomize_questions,
        randomize_options=exam.randomize_options,
        show_results_immediately=exam.show_results_immediately,
        allow_review=exam.allow_review,
        allow_retake=exam.allow_retake,
        max_retake_attempts=exam.max_retake_attempts,
        retake_score_policy=exam.retake_score_policy,
        retake_cooldown_minutes=exam.retake_cooldown_minutes,
        retake_show_review=exam.retake_show_review,
        override_question_navigation=exam.override_question_navigation,
        global_allow_previous=exam.global_allow_previous,
        global_allow_next=exam.global_allow_next,
        global_force_sequential=exam.global_force_sequential,
        require_fullscreen=exam.require_fullscreen,
        detect_tab_switch=exam.detect_tab_switch,
        enable_screenshot_proctoring=exam.enable_screenshot_proctoring,
        screenshot_interval_seconds=exam.screenshot_interval_seconds,
        max_violations_allowed=exam.max_violations_allowed,
        status="draft",
    )

    exam_questions = exam.exam_questions.all().order_by("display_order")
    ExamQuestion.objects.bulk_create(
        [
            ExamQuestion(
                exam=new_exam,
                question=item.question,
                display_order=item.display_order,
                points_override=item.points_override,
                override_navigation=item.override_navigation,
                allow_previous_override=item.allow_previous_override,
                allow_next_override=item.allow_next_override,
                force_sequential_override=item.force_sequential_override,
            )
            for item in exam_questions
        ]
    )

    assignments = exam.assignments.all()
    ExamAssignment.objects.bulk_create(
        [
            ExamAssignment(
                exam=new_exam,
                assigned_to_type=item.assigned_to_type,
                class_obj=item.class_obj,
                student=item.student,
            )
            for item in assignments
        ]
    )
    return new_exam


def resolve_effective_navigation(exam, exam_question):
    question = exam_question.question
    if exam.override_question_navigation:
        allow_previous = exam.global_allow_previous
        allow_next = exam.global_allow_next
        force_sequential = exam.global_force_sequential
    else:
        allow_previous = question.allow_previous
        allow_next = question.allow_next
        force_sequential = question.force_sequential

    if exam_question.override_navigation:
        if exam_question.allow_previous_override is not None:
            allow_previous = exam_question.allow_previous_override
        if exam_question.allow_next_override is not None:
            allow_next = exam_question.allow_next_override
        if exam_question.force_sequential_override is not None:
            force_sequential = exam_question.force_sequential_override

    if force_sequential:
        allow_previous = False

    return {
        "allow_previous": allow_previous,
        "allow_next": allow_next,
        "force_sequential": force_sequential,
    }


def build_exam_detail_context(exam):
    exam_questions = exam.exam_questions.select_related("question", "question__subject", "question__category").order_by("display_order")
    assignment_classes = []
    assignment_students = []
    for assignment in exam.assignments.select_related("class_obj", "student"):
        if assignment.assigned_to_type == "class" and assignment.class_obj_id:
            assignment_classes.append(assignment.class_obj)
        if assignment.assigned_to_type == "student" and assignment.student_id:
            assignment_students.append(assignment.student)

    now = timezone.now()
    timing_status = "Belum Mulai"
    if exam.start_time <= now <= exam.end_time:
        timing_status = "Sedang Berlangsung"
    elif now > exam.end_time:
        timing_status = "Selesai"

    navigation_rows = []
    for item in exam_questions:
        navigation_rows.append(
            {
                "exam_question": item,
                "effective": resolve_effective_navigation(exam, item),
            }
        )

    return {
        "exam_questions": exam_questions,
        "assignment_classes": assignment_classes,
        "assignment_students": assignment_students,
        "timing_status": timing_status,
        "navigation_rows": navigation_rows,
    }
