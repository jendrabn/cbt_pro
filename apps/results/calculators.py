from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from statistics import median, pstdev

from django.db import transaction
from django.utils import timezone

from apps.attempts.models import ExamAttempt
from apps.exams.models import ClassStudent
from apps.results.models import ExamResult, ExamStatistics


COMPLETED_ATTEMPT_STATUSES = ("submitted", "auto_submitted", "completed")


def _final_metrics_for_student(exam, result_rows):
    rows = list(result_rows)
    if not rows:
        return {
            "score": 0.0,
            "percentage": 0.0,
            "passed": False,
            "time_seconds": 0,
        }

    policy = (exam.retake_score_policy or "highest").strip().lower()
    if policy == "latest":
        selected = max(rows, key=lambda item: int(item.attempt.attempt_number or 0))
        return {
            "score": float(selected.total_score or 0),
            "percentage": float(selected.percentage or 0),
            "passed": bool(selected.passed),
            "time_seconds": int(selected.time_taken_seconds or 0),
        }
    if policy == "average":
        latest = max(rows, key=lambda item: int(item.attempt.attempt_number or 0))
        avg_score = sum(float(item.total_score or 0) for item in rows) / len(rows)
        avg_percentage = sum(float(item.percentage or 0) for item in rows) / len(rows)
        return {
            "score": avg_score,
            "percentage": avg_percentage,
            "passed": avg_percentage >= float(exam.passing_score or 0),
            "time_seconds": int(latest.time_taken_seconds or 0),
        }

    selected = max(
        rows,
        key=lambda item: (
            float(item.total_score or 0),
            int(item.attempt.attempt_number or 0),
        ),
    )
    return {
        "score": float(selected.total_score or 0),
        "percentage": float(selected.percentage or 0),
        "passed": bool(selected.passed),
        "time_seconds": int(selected.time_taken_seconds or 0),
    }


@transaction.atomic
def update_exam_statistics_with_retake(exam_id):
    from apps.exams.models import Exam

    exam = Exam.objects.get(id=exam_id)
    attempts_qs = ExamAttempt.objects.filter(exam=exam)

    assignments = exam.assignments.select_related("class_obj", "student")
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
    total_assigned = len(direct_student_ids | class_student_ids)

    total_started = (
        attempts_qs.exclude(status="not_started")
        .values("student_id")
        .distinct()
        .count()
    )
    total_completed = (
        attempts_qs.filter(status__in=COMPLETED_ATTEMPT_STATUSES)
        .values("student_id")
        .distinct()
        .count()
    )
    completion_rate = round((total_completed / total_assigned) * 100, 2) if total_assigned else None
    total_retake_attempts = attempts_qs.filter(attempt_number__gt=1).count()
    total_unique_students = attempts_qs.values("student_id").distinct().count()
    avg_attempts_per_student = (
        round(attempts_qs.count() / total_unique_students, 2)
        if total_unique_students
        else 1.0
    )

    grouped_results = defaultdict(list)
    for result in (
        ExamResult.objects.filter(
            exam=exam,
            attempt__status__in=COMPLETED_ATTEMPT_STATUSES,
        ).select_related("attempt")
    ):
        grouped_results[result.student_id].append(result)

    final_scores = []
    final_times = []
    total_passed = 0
    for _, result_rows in grouped_results.items():
        metrics = _final_metrics_for_student(exam, result_rows)
        final_scores.append(metrics["score"])
        final_times.append(metrics["time_seconds"])
        if metrics["passed"]:
            total_passed += 1

    if final_scores:
        average_score = round(sum(final_scores) / len(final_scores), 2)
        median_score = round(float(median(final_scores)), 2)
        highest_score = round(max(final_scores), 2)
        lowest_score = round(min(final_scores), 2)
        standard_deviation = round(float(pstdev(final_scores)) if len(final_scores) > 1 else 0.0, 4)
        pass_rate = round((total_passed / len(final_scores)) * 100, 2)
    else:
        average_score = None
        median_score = None
        highest_score = None
        lowest_score = None
        standard_deviation = None
        pass_rate = None

    average_time_seconds = round(sum(final_times) / len(final_times)) if final_times else None
    median_time_seconds = int(median(final_times)) if final_times else None

    stats, _ = ExamStatistics.objects.update_or_create(
        exam=exam,
        defaults={
            "total_assigned": total_assigned,
            "total_started": total_started,
            "total_completed": total_completed,
            "completion_rate": completion_rate,
            "total_retake_attempts": total_retake_attempts,
            "total_unique_students": total_unique_students,
            "avg_attempts_per_student": Decimal(str(avg_attempts_per_student)).quantize(Decimal("0.01")),
            "average_score": average_score,
            "median_score": median_score,
            "highest_score": highest_score,
            "lowest_score": lowest_score,
            "standard_deviation": standard_deviation,
            "total_passed": total_passed,
            "pass_rate": pass_rate,
            "average_time_seconds": average_time_seconds,
            "median_time_seconds": median_time_seconds,
            "last_calculated_at": timezone.now(),
        },
    )
    return stats
