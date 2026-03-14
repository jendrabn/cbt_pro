from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta

from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.accounts.models import UserActivityLog
from apps.attempts.models import ExamAttempt
from apps.exams.models import Class, Exam
from apps.results.models import Certificate, ExamResult
from apps.subjects.models import Subject


COMPLETED_ATTEMPT_STATUSES = ("submitted", "auto_submitted", "completed")
EXAM_TYPE_CHOICES = [
    ("multiple_choice", "Pilihan Ganda"),
    ("essay", "Esai"),
    ("short_answer", "Jawaban Singkat"),
    ("mixed", "Campuran"),
]

REPORT_COLUMNS = [
    ("exam_title", "Nama Ujian"),
    ("subject", "Mata Pelajaran"),
    ("class_names", "Kelas"),
    ("exam_type", "Jenis Ujian"),
    ("status", "Status"),
    ("start_time", "Mulai"),
    ("end_time", "Selesai"),
    ("participants", "Peserta Unik"),
    ("attempts", "Total Percobaan"),
    ("completed_attempts", "Percobaan Selesai"),
    ("completion_rate", "Tingkat Penyelesaian (%)"),
    ("avg_score", "Rata-rata Nilai (%)"),
    ("pass_rate", "Tingkat Kelulusan (%)"),
]

SCORE_DISTRIBUTION_BINS = [
    ("0-20", 0, 20),
    ("21-40", 21, 40),
    ("41-60", 41, 60),
    ("61-80", 61, 80),
    ("81-100", 81, 100),
]


def get_exam_type_label(exam_type):
    mapping = dict(EXAM_TYPE_CHOICES)
    return mapping.get(exam_type, "Tidak Diketahui")


def parse_analytics_filters(request):
    today = timezone.localdate()
    default_from = today - timedelta(days=29)
    default_to = today

    date_from = parse_date((request.GET.get("date_from") or "").strip()) or default_from
    date_to = parse_date((request.GET.get("date_to") or "").strip()) or default_to
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    subject = (request.GET.get("subject") or "").strip()
    class_id = (request.GET.get("class") or "").strip()
    exam_type = (request.GET.get("exam_type") or "").strip()
    if exam_type not in {item[0] for item in EXAM_TYPE_CHOICES}:
        exam_type = ""

    return {
        "date_from": date_from,
        "date_to": date_to,
        "subject": subject,
        "class": class_id,
        "exam_type": exam_type,
    }


def _build_datetime_range(filters):
    current_tz = timezone.get_current_timezone()
    date_start = timezone.make_aware(datetime.combine(filters["date_from"], time.min), current_tz)
    date_end = timezone.make_aware(datetime.combine(filters["date_to"], time.max), current_tz)
    return date_start, date_end


def _derive_exam_type(question_types):
    if not question_types:
        return "mixed"
    if len(question_types) == 1:
        return next(iter(question_types))
    return "mixed"


def _final_result_metrics_for_exam(exam, result_rows):
    rows = list(result_rows or [])
    if not rows:
        return None
    policy = (exam.retake_score_policy or "highest").strip().lower()
    if policy == "latest":
        selected = max(rows, key=lambda item: int(item.attempt.attempt_number or 0))
        return {
            "result": selected,
            "percentage": float(selected.percentage or 0),
            "passed": bool(selected.passed),
        }
    if policy == "average":
        selected = max(rows, key=lambda item: int(item.attempt.attempt_number or 0))
        average_percentage = sum(float(item.percentage or 0) for item in rows) / len(rows)
        return {
            "result": selected,
            "percentage": average_percentage,
            "passed": average_percentage >= float(exam.passing_score or 0),
        }
    selected = max(
        rows,
        key=lambda item: (
            float(item.total_score or 0),
            int(item.attempt.attempt_number or 0),
        ),
    )
    return {
        "result": selected,
        "percentage": float(selected.percentage or 0),
        "passed": bool(selected.passed),
    }


def _build_final_rows_for_exams(exams_qs):
    exams = list(exams_qs)
    exam_map = {exam.id: exam for exam in exams}
    exam_ids = list(exam_map.keys())
    grouped = defaultdict(lambda: defaultdict(list))
    for result in (
        ExamResult.objects.filter(
            exam_id__in=exam_ids,
            attempt__status__in=COMPLETED_ATTEMPT_STATUSES,
        )
        .select_related("attempt", "exam", "exam__subject")
        .order_by("exam_id", "student_id", "-attempt__attempt_number", "-created_at")
    ):
        grouped[result.exam_id][result.student_id].append(result)

    rows = []
    for exam_id, student_map in grouped.items():
        exam = exam_map.get(exam_id)
        if not exam:
            continue
        for student_id, result_rows in student_map.items():
            metrics = _final_result_metrics_for_exam(exam, result_rows)
            if not metrics:
                continue
            rows.append(
                {
                    "exam": exam,
                    "student_id": student_id,
                    "result": metrics["result"],
                    "percentage": metrics["percentage"],
                    "passed": metrics["passed"],
                }
            )
    return rows


def get_filtered_exams(filters):
    date_start, date_end = _build_datetime_range(filters)
    exams_qs = (
        Exam.objects.filter(
            is_deleted=False,
            start_time__range=(date_start, date_end),
        )
        .select_related("subject")
        .prefetch_related("exam_questions__question", "assignments__class_obj")
        .distinct()
    )

    if filters["subject"]:
        exams_qs = exams_qs.filter(subject_id=filters["subject"])

    if filters["class"]:
        exams_qs = exams_qs.filter(
            assignments__assigned_to_type="class",
            assignments__class_obj_id=filters["class"],
        )

    if filters["exam_type"]:
        matched_ids = []
        for exam in exams_qs:
            types = {item.question.question_type for item in exam.exam_questions.all() if item.question_id}
            if _derive_exam_type(types) == filters["exam_type"]:
                matched_ids.append(exam.id)
        exams_qs = exams_qs.filter(id__in=matched_ids)

    return exams_qs.order_by("-start_time")


def calculate_summary_metrics(exams_qs, filters):
    date_start, date_end = _build_datetime_range(filters)
    attempts_qs = ExamAttempt.objects.filter(
        exam__in=exams_qs,
        created_at__range=(date_start, date_end),
    )
    final_rows = _build_final_rows_for_exams(exams_qs)
    if filters.get("date_from") and filters.get("date_to"):
        start_dt, end_dt = _build_datetime_range(filters)
        final_rows = [
            row
            for row in final_rows
            if row["result"].attempt.submit_time
            and start_dt <= row["result"].attempt.submit_time <= end_dt
        ]

    total_attempts = attempts_qs.values("exam_id", "student_id").distinct().count()
    completed_attempts = (
        attempts_qs.filter(status__in=COMPLETED_ATTEMPT_STATUSES)
        .values("exam_id", "student_id")
        .distinct()
        .count()
    )
    completion_rate = round((completed_attempts / total_attempts) * 100, 2) if total_attempts else 0.0
    avg_score = (
        sum(float(item["percentage"]) for item in final_rows) / len(final_rows)
        if final_rows
        else 0.0
    )
    certificate_qs = Certificate.objects.filter(
        exam__in=exams_qs,
        issued_at__range=(date_start, date_end),
    )
    certificates_total = certificate_qs.count()
    certificates_revoked = certificate_qs.filter(
        Q(revoked_at__isnull=False) | Q(is_valid=False)
    ).count()
    certificates_active = certificate_qs.filter(
        revoked_at__isnull=True,
        is_valid=True,
    ).count()
    passed_total = sum(1 for row in final_rows if row["passed"])
    active_coverage_total = certificate_qs.filter(
        revoked_at__isnull=True,
        is_valid=True,
    ).values("exam_id", "student_id").distinct().count()
    certificate_coverage = round((active_coverage_total / passed_total) * 100, 2) if passed_total else 0.0

    return {
        "total_exams": exams_qs.count(),
        "total_participants": attempts_qs.values("student_id").distinct().count(),
        "total_attempts": total_attempts,
        "completed_attempts": completed_attempts,
        "completion_rate": completion_rate,
        "average_score": round(avg_score, 2),
        "certificates_total": certificates_total,
        "certificates_active": certificates_active,
        "certificates_revoked": certificates_revoked,
        "certificate_coverage": certificate_coverage,
    }


def calculate_comparison_metrics(filters):
    current_metrics = calculate_summary_metrics(get_filtered_exams(filters), filters)
    period_days = (filters["date_to"] - filters["date_from"]).days + 1

    prev_to = filters["date_from"] - timedelta(days=1)
    prev_from = prev_to - timedelta(days=period_days - 1)
    prev_filters = {
        **filters,
        "date_from": prev_from,
        "date_to": prev_to,
    }
    previous_metrics = calculate_summary_metrics(get_filtered_exams(prev_filters), prev_filters)

    def _change(current_value, previous_value):
        if previous_value == 0:
            return 0.0 if current_value == 0 else 100.0
        return round(((current_value - previous_value) / previous_value) * 100, 2)

    return {
        "total_exams_change": _change(current_metrics["total_exams"], previous_metrics["total_exams"]),
        "total_participants_change": _change(
            current_metrics["total_participants"], previous_metrics["total_participants"]
        ),
        "average_score_change": _change(current_metrics["average_score"], previous_metrics["average_score"]),
        "completion_rate_change": _change(current_metrics["completion_rate"], previous_metrics["completion_rate"]),
    }


def build_chart_data(exams_qs, filters):
    date_start, date_end = _build_datetime_range(filters)
    final_rows = [
        row
        for row in _build_final_rows_for_exams(exams_qs)
        if row["result"].attempt.submit_time
        and date_start <= row["result"].attempt.submit_time <= date_end
    ]

    trend_map = defaultdict(list)
    for row in final_rows:
        day = timezone.localtime(row["result"].attempt.submit_time).date().isoformat()
        trend_map[day].append(float(row["percentage"]))

    trend_labels = sorted(trend_map.keys())
    trend_values = [round(sum(values) / len(values), 2) for _, values in sorted(trend_map.items())]

    subject_map = defaultdict(int)
    for row in final_rows:
        subject_name = row["exam"].subject.name if row["exam"].subject_id else "-"
        subject_map[subject_name] += 1
    sorted_subject = sorted(subject_map.items(), key=lambda item: item[1], reverse=True)
    subject_labels = [item[0] for item in sorted_subject]
    subject_values = [item[1] for item in sorted_subject]

    activity_data = (
        UserActivityLog.objects.filter(
            created_at__range=(date_start, date_end),
            user__is_deleted=False,
        )
        .values("user__role")
        .annotate(total=Count("id"))
    )
    activity_map = {item["user__role"]: item["total"] for item in activity_data}
    activity_labels = ["Admin", "Guru", "Siswa"]
    activity_values = [
        activity_map.get("admin", 0),
        activity_map.get("teacher", 0),
        activity_map.get("student", 0),
    ]

    distribution_values = [0 for _ in SCORE_DISTRIBUTION_BINS]
    for row in final_rows:
        score = float(row["percentage"])
        for idx, (_, min_score, max_score) in enumerate(SCORE_DISTRIBUTION_BINS):
            if min_score <= score <= max_score:
                distribution_values[idx] += 1
                break

    certificate_qs = Certificate.objects.filter(
        exam__in=exams_qs,
        issued_at__range=(date_start, date_end),
    )
    certificate_revoked = certificate_qs.filter(
        Q(revoked_at__isnull=False) | Q(is_valid=False)
    ).count()
    certificate_ready = certificate_qs.filter(
        revoked_at__isnull=True,
        is_valid=True,
        pdf_generated_at__isnull=False,
    ).count()
    certificate_processing = certificate_qs.filter(
        revoked_at__isnull=True,
        is_valid=True,
        pdf_generated_at__isnull=True,
    ).count()

    return {
        "performance_trend": {
            "labels": trend_labels,
            "values": trend_values,
        },
        "subject_analysis": {
            "labels": subject_labels,
            "values": subject_values,
        },
        "user_activity": {
            "labels": activity_labels,
            "values": activity_values,
        },
        "score_distribution": {
            "labels": [label for label, _, _ in SCORE_DISTRIBUTION_BINS],
            "values": distribution_values,
        },
        "certificate_status": {
            "labels": ["Siap", "Diproses", "Dicabut"],
            "values": [certificate_ready, certificate_processing, certificate_revoked],
        },
    }


def build_report_rows(exams_qs):
    exam_ids = list(exams_qs.values_list("id", flat=True))
    if not exam_ids:
        return []

    attempts_data = {
        item["exam_id"]: item
        for item in ExamAttempt.objects.filter(exam_id__in=exam_ids)
        .values("exam_id")
        .annotate(
            attempts=Count("id"),
            participants=Count("student_id", distinct=True),
            completed_attempts=Count("id", filter=Q(status__in=COMPLETED_ATTEMPT_STATUSES)),
        )
    }

    results_group = defaultdict(lambda: defaultdict(list))
    for result in (
        ExamResult.objects.filter(
            exam_id__in=exam_ids,
            attempt__status__in=COMPLETED_ATTEMPT_STATUSES,
        )
        .select_related("exam", "attempt")
        .order_by("exam_id", "student_id", "-attempt__attempt_number", "-created_at")
    ):
        results_group[result.exam_id][result.student_id].append(result)

    rows = []
    for exam in exams_qs:
        attempts = attempts_data.get(exam.id, {})
        final_percentages = []
        passed_count = 0
        for _, student_results in results_group.get(exam.id, {}).items():
            metrics = _final_result_metrics_for_exam(exam, student_results)
            if not metrics:
                continue
            final_percentages.append(float(metrics["percentage"]))
            if metrics["passed"]:
                passed_count += 1

        exam_question_types = {item.question.question_type for item in exam.exam_questions.all() if item.question_id}
        exam_type = _derive_exam_type(exam_question_types)

        class_names = sorted(
            {
                assignment.class_obj.name
                for assignment in exam.assignments.all()
                if assignment.class_obj_id
            }
        )
        attempts_count = attempts.get("attempts", 0)
        completed = attempts.get("completed_attempts", 0)
        completion_rate = round((completed / attempts_count) * 100, 2) if attempts_count else 0.0

        total_result = len(final_percentages)
        pass_rate = round((passed_count / total_result) * 100, 2) if total_result else 0.0
        avg_score = round(sum(final_percentages) / total_result, 2) if total_result else 0.0

        rows.append(
            {
                "exam_id": str(exam.id),
                "exam_title": exam.title,
                "subject": exam.subject.name if exam.subject_id else "-",
                "class_names": ", ".join(class_names) if class_names else "-",
                "exam_type": get_exam_type_label(exam_type),
                "status": exam.get_status_display(),
                "start_time": timezone.localtime(exam.start_time),
                "end_time": timezone.localtime(exam.end_time),
                "participants": attempts.get("participants", 0),
                "attempts": attempts_count,
                "completed_attempts": completed,
                "completion_rate": completion_rate,
                "avg_score": avg_score,
                "pass_rate": pass_rate,
            }
        )
    return rows


def get_filter_options():
    subjects = Subject.objects.all().order_by("name").values("id", "name")
    classes = list(Class.objects.order_by("name").values("id", "name"))
    subject_options = [
        {
            "id": str(item["id"]),
            "name": item["name"] or "-",
        }
        for item in subjects
        if item["id"]
    ]
    return {
        "subjects": subject_options,
        "classes": [{"id": str(item["id"]), "name": item["name"]} for item in classes],
        "exam_types": [{"id": value, "name": label} for value, label in EXAM_TYPE_CHOICES],
    }
