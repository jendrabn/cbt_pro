from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.accounts.models import User

from .models import Class, ClassStudent, Exam, ExamAssignment, ExamQuestion


STATUS_LABELS = dict(Exam.Status.choices)


@transaction.atomic
def sync_classes_from_student_profiles():
    students = list(
        User.objects.filter(
            role="student",
            is_active=True,
            is_deleted=False,
            profile__class_grade__isnull=False,
        )
        .exclude(profile__class_grade="")
        .select_related("profile")
        .order_by("profile__class_grade", "first_name", "last_name", "username")
    )
    if not students:
        return {
            "students_processed": 0,
            "classes_created": 0,
            "classes_reactivated": 0,
            "memberships_created": 0,
            "memberships_updated": 0,
        }

    class_names = sorted(
        {
            (student.profile.class_grade or "").strip()
            for student in students
            if getattr(student, "profile", None) and (student.profile.class_grade or "").strip()
        }
    )
    if not class_names:
        return {
            "students_processed": len(students),
            "classes_created": 0,
            "classes_reactivated": 0,
            "memberships_created": 0,
            "memberships_updated": 0,
        }

    existing_by_name = {item.name: item for item in Class.objects.filter(name__in=class_names)}
    missing_classes = [
        Class(name=class_name, is_active=True)
        for class_name in class_names
        if class_name not in existing_by_name
    ]
    if missing_classes:
        Class.objects.bulk_create(missing_classes, ignore_conflicts=True)

    classes_to_reactivate = [
        class_obj
        for class_name, class_obj in existing_by_name.items()
        if class_name in class_names and not class_obj.is_active
    ]
    if classes_to_reactivate:
        for class_obj in classes_to_reactivate:
            class_obj.is_active = True
        Class.objects.bulk_update(classes_to_reactivate, ["is_active"])

    class_by_name = {item.name: item for item in Class.objects.filter(name__in=class_names)}
    memberships_by_student = {}
    for membership in ClassStudent.objects.filter(student_id__in=[student.id for student in students]).select_related("class_obj"):
        memberships_by_student.setdefault(membership.student_id, []).append(membership)

    to_create = []
    to_update = []
    for student in students:
        class_name = (student.profile.class_grade or "").strip()
        class_obj = class_by_name.get(class_name)
        if not class_obj:
            continue
        current_memberships = memberships_by_student.get(student.id, [])
        if not current_memberships:
            to_create.append(ClassStudent(class_obj=class_obj, student=student))
            continue
        if len(current_memberships) == 1 and current_memberships[0].class_obj_id != class_obj.id:
            current_memberships[0].class_obj_id = class_obj.id
            to_update.append(current_memberships[0])
            continue
        if all(membership.class_obj_id != class_obj.id for membership in current_memberships):
            to_create.append(ClassStudent(class_obj=class_obj, student=student))

    if to_create:
        ClassStudent.objects.bulk_create(to_create, ignore_conflicts=True)
    if to_update:
        ClassStudent.objects.bulk_update(to_update, ["class_obj"])

    return {
        "students_processed": len(students),
        "classes_created": len(missing_classes),
        "classes_reactivated": len(classes_to_reactivate),
        "memberships_created": len(to_create),
        "memberships_updated": len(to_update),
    }


def annotate_class_usage(queryset):
    return queryset.annotate(
        student_count=Count("students", distinct=True),
        active_student_count=Count(
            "students",
            filter=Q(students__student__role="student", students__student__is_active=True, students__student__is_deleted=False),
            distinct=True,
        ),
        exam_assignment_count=Count("exam_assignments", distinct=True),
    )


def get_class_usage_summary(class_obj):
    memberships = ClassStudent.objects.filter(class_obj=class_obj)
    return {
        "student_count": memberships.count(),
        "active_student_count": memberships.filter(
            student__role="student",
            student__is_active=True,
            student__is_deleted=False,
        ).count(),
        "exam_assignment_count": class_obj.exam_assignments.count(),
        "profile_match_count": User.objects.filter(
            role="student",
            is_active=True,
            is_deleted=False,
            profile__class_grade=class_obj.name,
        ).count(),
    }


@transaction.atomic
def replace_class_members(class_obj, student_ids):
    valid_student_ids = set(
        User.objects.filter(
            id__in=student_ids,
            role="student",
            is_deleted=False,
        ).values_list("id", flat=True)
    )
    existing_student_ids = set(
        ClassStudent.objects.filter(class_obj=class_obj).values_list("student_id", flat=True)
    )

    to_remove = existing_student_ids - valid_student_ids
    to_add = valid_student_ids - existing_student_ids

    if to_remove:
        ClassStudent.objects.filter(class_obj=class_obj, student_id__in=to_remove).delete()
    if to_add:
        ClassStudent.objects.bulk_create(
            [ClassStudent(class_obj=class_obj, student_id=student_id) for student_id in to_add],
            ignore_conflicts=True,
        )

    return {
        "selected_total": len(valid_student_ids),
        "memberships_added": len(to_add),
        "memberships_removed": len(to_remove),
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
                "retake_badge": f"{exam.max_retake_attempts}x" if exam.allow_retake else "",
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

    exam.status = Exam.Status.PUBLISHED if cleaned.get("status_action") == "publish" else Exam.Status.DRAFT
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
    if exam.status == Exam.Status.DRAFT:
        exam.status = Exam.Status.PUBLISHED
    elif exam.status == Exam.Status.PUBLISHED:
        exam.status = Exam.Status.DRAFT
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
        certificate_enabled=exam.certificate_enabled,
        certificate_template=exam.certificate_template,
        override_question_navigation=exam.override_question_navigation,
        global_allow_previous=exam.global_allow_previous,
        global_allow_next=exam.global_allow_next,
        global_force_sequential=exam.global_force_sequential,
        require_fullscreen=exam.require_fullscreen,
        require_camera=exam.require_camera,
        require_microphone=exam.require_microphone,
        detect_tab_switch=exam.detect_tab_switch,
        disable_right_click=exam.disable_right_click,
        enable_screenshot_proctoring=exam.enable_screenshot_proctoring,
        screenshot_interval_seconds=exam.screenshot_interval_seconds,
        max_violations_allowed=exam.max_violations_allowed,
        status=Exam.Status.DRAFT,
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
