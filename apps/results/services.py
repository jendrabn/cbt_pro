from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from statistics import median, pstdev
from typing import Iterable

from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.attempts.models import ExamAttempt, ExamViolation, StudentAnswer
from apps.exams.models import Class, ClassStudent, Exam
from apps.results.models import Certificate, ExamResult
from apps.subjects.models import Subject


COMPLETED_ATTEMPT_STATUSES = ("submitted", "auto_submitted", "completed")

SORTABLE_STUDENT_COLUMNS = {
    "rank",
    "name",
    "score",
    "percentage",
    "status",
    "time",
    "violations",
    "attempts",
}

SORT_OPTION_MAP = {
    "rank_asc": ("rank", "asc"),
    "rank_desc": ("rank", "desc"),
    "name_asc": ("name", "asc"),
    "name_desc": ("name", "desc"),
    "score_desc": ("score", "desc"),
    "score_asc": ("score", "asc"),
    "percentage_desc": ("percentage", "desc"),
    "percentage_asc": ("percentage", "asc"),
    "status_asc": ("status", "asc"),
    "status_desc": ("status", "desc"),
    "time_asc": ("time", "asc"),
    "time_desc": ("time", "desc"),
    "violations_desc": ("violations", "desc"),
    "violations_asc": ("violations", "asc"),
    "attempts_desc": ("attempts", "desc"),
    "attempts_asc": ("attempts", "asc"),
}

SCORE_BINS = [
    ("0-20", 0, 20),
    ("21-40", 21, 40),
    ("41-60", 41, 60),
    ("61-80", 61, 80),
    ("81-100", 81, 100),
]

RETAKE_POLICY_LABELS = {
    "highest": "Nilai Tertinggi",
    "latest": "Nilai Terbaru",
    "average": "Nilai Rata-rata",
}


@dataclass(frozen=True)
class TeacherResultsFilters:
    date_from: date
    date_to: date
    subject: str
    class_id: str
    keyword: str


@dataclass(frozen=True)
class StudentResultsFilters:
    date_from: date
    date_to: date
    subject: str
    status: str
    keyword: str


def _to_float(value):
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _policy_label(policy):
    return RETAKE_POLICY_LABELS.get((policy or "").strip().lower(), "Nilai Tertinggi")


def _select_result_by_policy(policy, result_rows):
    if not result_rows:
        return None
    normalized = (policy or "highest").strip().lower()
    if normalized == "latest":
        return max(result_rows, key=lambda row: int(row.attempt.attempt_number or 0))
    return max(
        result_rows,
        key=lambda row: (
            _to_float(row.total_score),
            int(row.attempt.attempt_number or 0),
        ),
    )


def _resolve_final_result_metrics(exam, result_rows):
    rows = list(result_rows or [])
    if not rows:
        return {
            "selected_result": None,
            "final_score": 0.0,
            "final_percentage": 0.0,
            "passed": False,
            "policy": (exam.retake_score_policy or "highest").strip().lower(),
            "policy_label": _policy_label(exam.retake_score_policy),
            "attempts_used": 0,
        }

    policy = (exam.retake_score_policy or "highest").strip().lower()
    selected = _select_result_by_policy(policy, rows)
    attempts_used = len(rows)

    if policy == "average":
        average_score = sum(_to_float(item.total_score) for item in rows) / attempts_used
        average_percentage = sum(_to_float(item.percentage) for item in rows) / attempts_used
        passed = average_percentage >= _to_float(exam.passing_score)
        selected = max(rows, key=lambda row: int(row.attempt.attempt_number or 0))
        return {
            "selected_result": selected,
            "final_score": round(average_score, 2),
            "final_percentage": round(average_percentage, 2),
            "passed": bool(passed),
            "policy": policy,
            "policy_label": _policy_label(policy),
            "attempts_used": attempts_used,
        }

    return {
        "selected_result": selected,
        "final_score": round(_to_float(selected.total_score), 2),
        "final_percentage": round(_to_float(selected.percentage), 2),
        "passed": bool(selected.passed),
        "policy": policy,
        "policy_label": _policy_label(policy),
        "attempts_used": attempts_used,
    }


def calculate_final_score(exam_id, student_id):
    exam = Exam.objects.get(id=exam_id)
    result_rows = list(
        ExamResult.objects.filter(
            exam_id=exam_id,
            student_id=student_id,
            attempt__status__in=COMPLETED_ATTEMPT_STATUSES,
        ).select_related("attempt")
    )
    metrics = _resolve_final_result_metrics(exam, result_rows)
    return Decimal(str(metrics["final_score"])).quantize(Decimal("0.01"))


def _datetime_range(filters: TeacherResultsFilters):
    current_tz = timezone.get_current_timezone()
    date_start = timezone.make_aware(datetime.combine(filters.date_from, time.min), current_tz)
    date_end = timezone.make_aware(datetime.combine(filters.date_to, time.max), current_tz)
    return date_start, date_end


def format_seconds_human(total_seconds):
    if not total_seconds:
        return "0 menit"
    seconds = int(total_seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, sec = divmod(rem, 60)
    chunks = []
    if hours:
        chunks.append(f"{hours} jam")
    if minutes:
        chunks.append(f"{minutes} menit")
    if sec and not hours:
        chunks.append(f"{sec} detik")
    return " ".join(chunks) or "0 menit"


def parse_results_filters(request):
    today = timezone.localdate()
    default_from = today - timedelta(days=29)
    default_to = today

    date_from = parse_date((request.GET.get("date_from") or "").strip()) or default_from
    date_to = parse_date((request.GET.get("date_to") or "").strip()) or default_to
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    return TeacherResultsFilters(
        date_from=date_from,
        date_to=date_to,
        subject=(request.GET.get("subject") or "").strip(),
        class_id=(request.GET.get("class") or "").strip(),
        keyword=(request.GET.get("q") or "").strip(),
    )


def parse_student_results_filters(request):
    today = timezone.localdate()
    default_from = today - timedelta(days=3650)
    default_to = today

    date_from = parse_date((request.GET.get("date_from") or "").strip()) or default_from
    date_to = parse_date((request.GET.get("date_to") or "").strip()) or default_to
    if date_from > date_to:
        date_from, date_to = date_to, date_from

    status = (request.GET.get("status") or "").strip().lower()
    if status not in {"", "passed", "failed"}:
        status = ""

    return StudentResultsFilters(
        date_from=date_from,
        date_to=date_to,
        subject=(request.GET.get("subject") or "").strip(),
        status=status,
        keyword=(request.GET.get("q") or "").strip(),
    )


def get_student_filter_options(student):
    subject_rows = (
        ExamResult.objects.filter(student=student)
        .values("exam__subject_id", "exam__subject__name")
        .distinct()
        .order_by("exam__subject__name")
    )
    return [
        {"id": str(item["exam__subject_id"]), "name": item["exam__subject__name"]}
        for item in subject_rows
        if item["exam__subject_id"]
    ]


def get_student_results_queryset(student, filters: StudentResultsFilters):
    date_start, date_end = _datetime_range(filters)
    queryset = ExamResult.objects.filter(student=student).select_related(
        "exam",
        "exam__subject",
        "attempt",
        "student",
    )

    queryset = queryset.filter(
        Q(attempt__submit_time__range=(date_start, date_end))
        | Q(attempt__submit_time__isnull=True, exam__end_time__range=(date_start, date_end))
    )

    if filters.subject:
        queryset = queryset.filter(exam__subject_id=filters.subject)

    if filters.keyword:
        queryset = queryset.filter(
            Q(exam__title__icontains=filters.keyword)
            | Q(exam__description__icontains=filters.keyword)
            | Q(exam__subject__name__icontains=filters.keyword)
        )

    return queryset.order_by("exam_id", "-attempt__attempt_number", "-created_at")


def _result_certificate(result):
    try:
        return result.certificate
    except Certificate.DoesNotExist:
        return None


def get_certificate_download_url(result):
    certificate = _result_certificate(result)
    if not certificate or not certificate.is_valid:
        return ""
    return (certificate.certificate_url or "").strip()


def build_student_results_rows(results_qs, status_filter=""):
    grouped = defaultdict(list)
    for result in results_qs:
        grouped[result.exam_id].append(result)

    rows = []
    for _, result_rows in grouped.items():
        exam = result_rows[0].exam
        metrics = _resolve_final_result_metrics(exam, result_rows)
        selected_result = metrics["selected_result"]
        if not selected_result:
            continue

        submitted_at = (
            selected_result.attempt.submit_time
            or selected_result.attempt.end_time
            or selected_result.created_at
        )
        submitted_label = "-"
        if submitted_at:
            submitted_label = timezone.localtime(submitted_at).strftime("%d %b %Y %H:%M")

        if status_filter == "passed" and not metrics["passed"]:
            continue
        if status_filter == "failed" and metrics["passed"]:
            continue

        certificate = _result_certificate(selected_result)
        certificate_available = bool(
            certificate
            and certificate.is_valid
            and (certificate.certificate_url or "").strip()
        )

        status_label = "Lulus" if metrics["passed"] else "Belum Lulus"
        status_tone = "success" if metrics["passed"] else "danger"

        rows.append(
            {
                "id": str(selected_result.id),
                "result": selected_result,
                "exam": exam,
                "subject_name": exam.subject.name if exam.subject_id else "-",
                "submitted_at": submitted_at,
                "submitted_label": submitted_label,
                "total_score": round(metrics["final_score"], 2),
                "percentage": round(metrics["final_percentage"], 2),
                "passed": bool(metrics["passed"]),
                "status_label": status_label,
                "status_tone": status_tone,
                "correct_answers": int(selected_result.correct_answers or 0),
                "wrong_answers": int(selected_result.wrong_answers or 0),
                "unanswered": int(selected_result.unanswered or 0),
                "time_taken_seconds": int(selected_result.time_taken_seconds or 0),
                "time_taken_human": format_seconds_human(selected_result.time_taken_seconds or 0),
                "time_efficiency": _to_float(selected_result.time_efficiency) if selected_result.time_efficiency is not None else None,
                "review_enabled": bool(exam.allow_review),
                "certificate_available": certificate_available,
                "certificate_number": certificate.certificate_number if certificate_available else "",
                "allow_retake": bool(exam.allow_retake),
                "max_retake_attempts": int(exam.max_retake_attempts or 1),
                "attempts_used": int(metrics["attempts_used"] or 1),
                "policy_label": metrics["policy_label"],
            }
        )

    rows.sort(key=lambda item: item["submitted_at"] or item["result"].created_at, reverse=True)
    return rows


def build_student_results_summary(result_rows):
    if not result_rows:
        return {
            "total_hasil": 0,
            "rata_rata_nilai": 0.0,
            "nilai_terbaik": 0.0,
            "nilai_terendah": 0.0,
            "jumlah_lulus": 0,
            "jumlah_belum_lulus": 0,
            "persentase_lulus": 0.0,
            "jumlah_sertifikat": 0,
            "total_benar": 0,
            "total_salah": 0,
            "total_kosong": 0,
            "rata_rata_efisiensi": 0.0,
        }

    total_hasil = len(result_rows)
    percentages = [row["percentage"] for row in result_rows]
    jumlah_lulus = sum(1 for row in result_rows if row["passed"])
    jumlah_belum_lulus = total_hasil - jumlah_lulus
    persentase_lulus = round((jumlah_lulus / total_hasil) * 100, 2) if total_hasil else 0.0
    efficiency_values = [row["time_efficiency"] for row in result_rows if row["time_efficiency"] is not None]

    return {
        "total_hasil": total_hasil,
        "rata_rata_nilai": round(sum(percentages) / total_hasil, 2),
        "nilai_terbaik": round(max(percentages), 2),
        "nilai_terendah": round(min(percentages), 2),
        "jumlah_lulus": jumlah_lulus,
        "jumlah_belum_lulus": jumlah_belum_lulus,
        "persentase_lulus": persentase_lulus,
        "jumlah_sertifikat": sum(1 for row in result_rows if row["certificate_available"]),
        "total_benar": sum(row["correct_answers"] for row in result_rows),
        "total_salah": sum(row["wrong_answers"] for row in result_rows),
        "total_kosong": sum(row["unanswered"] for row in result_rows),
        "rata_rata_efisiensi": (
            round(sum(efficiency_values) / len(efficiency_values), 2) if efficiency_values else 0.0
        ),
    }


def build_student_performance_charts(result_rows):
    if not result_rows:
        return {
            "trend": {"labels": [], "values": []},
            "subject": {"labels": [], "values": []},
        }

    sorted_rows = sorted(
        result_rows,
        key=lambda item: item["submitted_at"] or item["result"].created_at,
    )

    trend_labels = []
    trend_values = []
    subject_map = defaultdict(list)

    for row in sorted_rows:
        exam_label = row["exam"].title[:20]
        if row["submitted_at"]:
            date_label = timezone.localtime(row["submitted_at"]).strftime("%d/%m")
            trend_labels.append(f"{exam_label} ({date_label})")
        else:
            trend_labels.append(exam_label)
        trend_values.append(row["percentage"])
        subject_map[row["subject_name"]].append(row["percentage"])

    subject_labels = sorted(subject_map.keys())
    subject_values = [
        round(sum(subject_map[label]) / len(subject_map[label]), 2)
        for label in subject_labels
    ]

    return {
        "trend": {"labels": trend_labels, "values": trend_values},
        "subject": {"labels": subject_labels, "values": subject_values},
    }


def build_student_result_detail_context(result):
    exam = result.exam
    student = result.student
    all_results = list(
        ExamResult.objects.filter(
            exam=exam,
            student=student,
            attempt__status__in=COMPLETED_ATTEMPT_STATUSES,
        )
        .select_related("attempt")
        .order_by("-attempt__attempt_number", "-created_at")
    )
    final_metrics = _resolve_final_result_metrics(exam, all_results)
    selected_result = final_metrics["selected_result"] or result
    review_context = build_answer_review_context(selected_result)
    certificate_url = get_certificate_download_url(selected_result)

    rows = review_context["rows"]
    score_max = sum(row["points_possible"] for row in rows)
    score_max = round(score_max, 2) if score_max else round(_to_float(exam.total_points), 2)
    explanation_total = sum(1 for row in rows if row["has_explanation"])
    history_rows = []
    for history_result in sorted(
        all_results,
        key=lambda item: int(item.attempt.attempt_number or 0),
    ):
        history_rows.append(
            {
                "result_id": str(history_result.id),
                "attempt_number": int(history_result.attempt.attempt_number or 0),
                "submit_time": history_result.attempt.submit_time,
                "submit_time_label": timezone.localtime(history_result.attempt.submit_time).strftime("%d %b %Y %H:%M")
                if history_result.attempt.submit_time
                else "-",
                "total_score": round(_to_float(history_result.total_score), 2),
                "percentage": round(_to_float(history_result.percentage), 2),
                "passed": bool(history_result.passed),
                "status_label": "Lulus" if history_result.passed else "Belum Lulus",
                "duration_label": format_seconds_human(history_result.time_taken_seconds or 0),
                "is_final": bool(selected_result.id == history_result.id),
            }
        )

    return {
        **review_context,
        "score_total": round(final_metrics["final_score"], 2),
        "score_max": score_max,
        "percentage_value": round(final_metrics["final_percentage"], 2),
        "status_label": "Lulus" if final_metrics["passed"] else "Belum Lulus",
        "status_tone": "success" if final_metrics["passed"] else "danger",
        "rank_label": selected_result.rank_in_exam or "-",
        "percentile_label": round(_to_float(selected_result.percentile), 2) if selected_result.percentile is not None else None,
        "time_taken_human": format_seconds_human(selected_result.time_taken_seconds or 0),
        "time_efficiency": round(_to_float(selected_result.time_efficiency), 2) if selected_result.time_efficiency is not None else 0.0,
        "review_enabled": bool(exam.allow_review),
        "certificate_url": certificate_url,
        "certificate_available": bool(certificate_url),
        "answer_breakdown_chart": {
            "labels": ["Benar", "Salah", "Tidak Dijawab"],
            "values": [
                int(selected_result.correct_answers or 0),
                int(selected_result.wrong_answers or 0),
                int(selected_result.unanswered or 0),
            ],
        },
        "answer_rows_preview": rows[:5],
        "explanation_total": explanation_total,
        "allow_retake": bool(exam.allow_retake),
        "final_policy_label": final_metrics["policy_label"],
        "attempts_used": int(final_metrics["attempts_used"] or 1),
        "retake_history_rows": history_rows,
    }


def get_teacher_results_exam_queryset(teacher, filters: TeacherResultsFilters):
    date_start, date_end = _datetime_range(filters)
    queryset = (
        Exam.objects.filter(
            created_by=teacher,
            is_deleted=False,
            start_time__range=(date_start, date_end),
        )
        .select_related("subject")
        .prefetch_related("assignments__class_obj")
        .distinct()
    )

    if filters.subject:
        queryset = queryset.filter(subject_id=filters.subject)

    if filters.class_id:
        queryset = queryset.filter(
            assignments__assigned_to_type="class",
            assignments__class_obj_id=filters.class_id,
        )

    if filters.keyword:
        queryset = queryset.filter(
            Q(title__icontains=filters.keyword)
            | Q(description__icontains=filters.keyword)
            | Q(subject__name__icontains=filters.keyword)
        )

    return queryset.order_by("-start_time")


def get_teacher_filter_options(teacher):
    exam_qs = Exam.objects.filter(created_by=teacher, is_deleted=False)
    subject_rows = Subject.objects.filter(exams__created_by=teacher).distinct().order_by("name").values("id", "name")
    class_ids = (
        exam_qs.filter(assignments__assigned_to_type="class")
        .values_list("assignments__class_obj_id", flat=True)
        .distinct()
    )
    class_rows = Class.objects.filter(id__in=class_ids, is_active=True).order_by("name").values("id", "name")

    return {
        "subjects": [
            {"id": str(item["id"]), "name": item["name"]}
            for item in subject_rows
            if item["id"]
        ],
        "classes": [{"id": str(item["id"]), "name": item["name"]} for item in class_rows],
    }


def build_exam_rows(exams_qs):
    exams = list(exams_qs)
    exam_ids = [exam.id for exam in exams]
    if not exam_ids:
        return []

    attempts_data = {
        row["exam_id"]: row
        for row in ExamAttempt.objects.filter(exam_id__in=exam_ids)
        .values("exam_id")
        .annotate(
            participants=Count("student_id", distinct=True),
            total_attempts=Count("id"),
            completed_attempts=Count("id", filter=Q(status__in=COMPLETED_ATTEMPT_STATUSES)),
            passed_attempts=Count("id", filter=Q(passed=True)),
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
    for exam in exams:
        attempt = attempts_data.get(exam.id, {})
        participant_count = attempt.get("participants", 0) or 0

        final_percentages = []
        total_passed = 0
        per_student_rows = results_group.get(exam.id, {})
        for _, student_rows in per_student_rows.items():
            metrics = _resolve_final_result_metrics(exam, student_rows)
            final_percentages.append(metrics["final_percentage"])
            if metrics["passed"]:
                total_passed += 1

        if final_percentages:
            avg_score = round(sum(final_percentages) / len(final_percentages), 2)
            pass_rate = round((total_passed / len(final_percentages)) * 100, 2)
        else:
            avg_score = 0.0
            total_attempts = attempt.get("total_attempts", 0) or 0
            passed_attempts = attempt.get("passed_attempts", 0) or 0
            pass_rate = round((passed_attempts / total_attempts) * 100, 2) if total_attempts else 0.0

        class_names = sorted(
            {
                assignment.class_obj.name
                for assignment in exam.assignments.all()
                if assignment.class_obj_id and assignment.class_obj
            }
        )
        rows.append(
            {
                "exam": exam,
                "participants": participant_count,
                "average_score": avg_score,
                "pass_rate": pass_rate,
                "attempt_count": attempt.get("total_attempts", 0) or 0,
                "completed_attempt_count": attempt.get("completed_attempts", 0) or 0,
                "class_names": ", ".join(class_names) if class_names else "-",
            }
        )

    return rows


def get_exam_results_queryset(exam):
    return ExamResult.objects.filter(exam=exam).select_related("student", "attempt")


def _sort_student_rows(rows, sort_by, direction):
    if sort_by not in SORTABLE_STUDENT_COLUMNS:
        sort_by = "rank"
    reverse = direction == "desc"

    key_map = {
        "rank": lambda item: item["rank"],
        "name": lambda item: item["student_name"].lower(),
        "score": lambda item: item["total_score"],
        "percentage": lambda item: item["percentage"],
        "status": lambda item: item["status_label"],
        "time": lambda item: item["time_taken_seconds"],
        "violations": lambda item: item["total_violations"],
        "attempts": lambda item: item.get("attempts_used", 1),
    }

    if sort_by == "rank":
        reverse = direction == "desc"
    return sorted(rows, key=key_map[sort_by], reverse=reverse)


def _build_student_class_map(student_ids: Iterable):
    rows = (
        ClassStudent.objects.filter(student_id__in=student_ids, class_obj__is_active=True)
        .select_related("class_obj")
        .values("student_id", "class_obj__name")
    )
    result_map = defaultdict(list)
    for row in rows:
        result_map[row["student_id"]].append(row["class_obj__name"])
    return {student_id: sorted(set(names)) for student_id, names in result_map.items()}


def build_student_result_rows(results_qs, sort_by="rank", direction="asc"):
    attempt_results = list(
        results_qs.select_related("exam", "student", "attempt").order_by(
            "student_id",
            "-attempt__attempt_number",
            "-created_at",
        )
    )
    if not attempt_results:
        return []

    grouped = defaultdict(list)
    for result in attempt_results:
        grouped[result.student_id].append(result)

    student_ids = list(grouped.keys())
    class_map = _build_student_class_map(student_ids)

    base_rows = []
    for student_id, student_results in grouped.items():
        reference_result = student_results[0]
        exam = reference_result.exam
        metrics = _resolve_final_result_metrics(exam, student_results)
        selected_result = metrics["selected_result"] or reference_result
        student_name = selected_result.student.get_full_name().strip() or selected_result.student.username
        class_names = class_map.get(student_id, [])
        base_rows.append(
            {
                "id": str(selected_result.id),
                "result": selected_result,
                "student_name": student_name,
                "student_username": selected_result.student.username,
                "class_names": class_names,
                "class_label": ", ".join(class_names) if class_names else "Belum terdaftar kelas",
                "total_score": round(metrics["final_score"], 2),
                "percentage": round(metrics["final_percentage"], 2),
                "passed": bool(metrics["passed"]),
                "status_label": "Lulus" if metrics["passed"] else "Belum Lulus",
                "time_taken_seconds": int(selected_result.time_taken_seconds or 0),
                "time_taken_human": format_seconds_human(selected_result.time_taken_seconds or 0),
                "total_violations": int(selected_result.total_violations or 0),
                "attempts_used": int(metrics["attempts_used"] or 1),
                "max_attempts": int(exam.max_retake_attempts or 1),
                "allow_retake": bool(exam.allow_retake),
                "attempts_label": f"{int(metrics['attempts_used'] or 1)}/{int(exam.max_retake_attempts or 1)}",
                "final_policy_label": metrics["policy_label"],
            }
        )

    ranking_sorted = sorted(
        base_rows,
        key=lambda item: (
            -float(item["percentage"]),
            -float(item["total_score"]),
            int(item["time_taken_seconds"]),
            item["student_name"].lower(),
        ),
    )
    rows = []
    for idx, item in enumerate(ranking_sorted, start=1):
        row = dict(item)
        row["rank"] = idx
        rows.append(
            row
        )

    return _sort_student_rows(rows, sort_by=sort_by, direction=direction)


def calculate_statistics_cards(student_rows):
    if not student_rows:
        return {
            "highest": 0.0,
            "lowest": 0.0,
            "average": 0.0,
            "median": 0.0,
            "std_dev": 0.0,
        }

    percentages = [row["percentage"] for row in student_rows]
    average = sum(percentages) / len(percentages)
    med = median(percentages)
    std_dev = pstdev(percentages) if len(percentages) > 1 else 0.0

    return {
        "highest": round(max(percentages), 2),
        "lowest": round(min(percentages), 2),
        "average": round(average, 2),
        "median": round(med, 2),
        "std_dev": round(std_dev, 2),
    }


def calculate_exam_summary(student_rows, exam):
    total = len(student_rows)
    passed = len([row for row in student_rows if row["passed"]])
    failed = total - passed
    pass_rate = round((passed / total) * 100, 2) if total else 0.0
    avg_time = round(sum(row["time_taken_seconds"] for row in student_rows) / total, 2) if total else 0

    return {
        "exam_title": exam.title,
        "subject_name": exam.subject.name if exam.subject_id else "-",
        "total_participants": total,
        "passed_count": passed,
        "failed_count": failed,
        "pass_rate": pass_rate,
        "average_time_seconds": avg_time,
        "average_time_human": format_seconds_human(avg_time),
    }


def build_score_distribution(student_rows):
    values = [0] * len(SCORE_BINS)
    for row in student_rows:
        score = row["percentage"]
        for idx, (_, min_score, max_score) in enumerate(SCORE_BINS):
            if min_score <= score <= max_score:
                values[idx] += 1
                break

    return {
        "labels": [label for label, _, _ in SCORE_BINS],
        "values": values,
    }


def build_pass_fail_distribution(student_rows):
    passed = len([row for row in student_rows if row["passed"]])
    failed = len(student_rows) - passed
    return {"labels": ["Lulus", "Belum Lulus"], "values": [passed, failed]}


def _performance_groups(exam):
    attempt_ids = list(
        ExamResult.objects.filter(exam=exam)
        .order_by("-percentage", "-total_score")
        .values_list("attempt_id", flat=True)
    )
    if not attempt_ids:
        return set(), set()
    group_size = max(1, int(len(attempt_ids) * 0.27))
    top_group = set(attempt_ids[:group_size])
    bottom_group = set(attempt_ids[-group_size:])
    return top_group, bottom_group


def build_item_analysis(exam):
    exam_questions = list(
        exam.exam_questions.select_related("question")
        .prefetch_related("question__options")
        .order_by("display_order")
    )
    if not exam_questions:
        return []

    question_ids = [item.question_id for item in exam_questions]
    answers = list(
        StudentAnswer.objects.filter(attempt__exam=exam, question_id__in=question_ids)
        .select_related("selected_option", "question")
        .order_by("question_id")
    )
    grouped_answers = defaultdict(list)
    for answer in answers:
        grouped_answers[answer.question_id].append(answer)

    participant_count = (
        ExamResult.objects.filter(exam=exam).values("student_id").distinct().count()
        or ExamAttempt.objects.filter(exam=exam).values("student_id").distinct().count()
    )
    top_group, bottom_group = _performance_groups(exam)

    items = []
    for exam_question in exam_questions:
        question = exam_question.question
        question_answers = grouped_answers.get(question.id, [])
        answered_count = sum(
            1
            for answer in question_answers
            if answer.selected_option_id or (answer.answer_text and answer.answer_text.strip())
        )
        correct_count = sum(1 for answer in question_answers if answer.is_correct is True)
        wrong_count = sum(1 for answer in question_answers if answer.is_correct is False)
        skipped_count = max(participant_count - answered_count, 0)
        difficulty = round((correct_count / answered_count) * 100, 2) if answered_count else 0.0

        top_answers = [answer for answer in question_answers if answer.attempt_id in top_group]
        bottom_answers = [answer for answer in question_answers if answer.attempt_id in bottom_group]
        top_correct = sum(1 for answer in top_answers if answer.is_correct is True)
        bottom_correct = sum(1 for answer in bottom_answers if answer.is_correct is True)
        top_ratio = (top_correct / len(top_answers)) if top_answers else 0.0
        bottom_ratio = (bottom_correct / len(bottom_answers)) if bottom_answers else 0.0
        discrimination = round((top_ratio - bottom_ratio) * 100, 2)

        distractor_rows = []
        if question.question_type == "multiple_choice":
            selection_map = defaultdict(int)
            for answer in question_answers:
                if answer.selected_option_id:
                    selection_map[answer.selected_option_id] += 1

            for option in question.options.order_by("display_order"):
                selected = selection_map.get(option.id, 0)
                percentage = round((selected / answered_count) * 100, 2) if answered_count else 0.0
                distractor_rows.append(
                    {
                        "option_letter": option.option_letter,
                        "option_text": option.option_text,
                        "selected_count": selected,
                        "selected_percentage": percentage,
                        "is_correct": option.is_correct,
                    }
                )

        items.append(
            {
                "display_order": exam_question.display_order,
                "question": question,
                "participant_count": participant_count,
                "answered_count": answered_count,
                "correct_count": correct_count,
                "wrong_count": wrong_count,
                "skipped_count": skipped_count,
                "difficulty_index": difficulty,
                "discrimination_index": discrimination,
                "distractors": distractor_rows,
            }
        )

    return items


def build_class_comparison(student_rows):
    class_map = defaultdict(list)
    pass_map = defaultdict(int)
    for row in student_rows:
        labels = row["class_names"] or ["Belum terdaftar kelas"]
        for label in labels:
            class_map[label].append(row["percentage"])
            if row["passed"]:
                pass_map[label] += 1

    labels = sorted(class_map.keys())
    average_scores = []
    pass_rates = []
    participant_counts = []
    for label in labels:
        scores = class_map[label]
        average_scores.append(round(sum(scores) / len(scores), 2) if scores else 0.0)
        participant_counts.append(len(scores))
        pass_rates.append(round((pass_map[label] / len(scores)) * 100, 2) if scores else 0.0)

    return {
        "labels": labels,
        "avg_scores": average_scores,
        "pass_rates": pass_rates,
        "participants": participant_counts,
    }


def build_exam_comparison_for_teacher(teacher, current_exam_id):
    exam_qs = (
        Exam.objects.filter(created_by=teacher, is_deleted=False)
        .select_related("subject")
        .prefetch_related("assignments__class_obj")
        .order_by("-start_time")[:10]
    )
    exam_rows = [row for row in build_exam_rows(exam_qs) if row["participants"] > 0]

    labels = []
    avg_scores = []
    pass_rates = []
    exam_ids = []
    for row in exam_rows:
        exam = row["exam"]
        labels.append(exam.title[:26])
        avg_scores.append(round(_to_float(row["average_score"]), 2))
        pass_rates.append(round(_to_float(row["pass_rate"]), 2))
        exam_ids.append(str(exam.id))

    return {
        "labels": labels,
        "avg_scores": avg_scores,
        "pass_rates": pass_rates,
        "exam_ids": exam_ids,
        "current_exam_id": str(current_exam_id),
    }


def build_answer_review_context(result):
    attempt = result.attempt
    exam = result.exam
    exam_questions = list(
        exam.exam_questions.select_related("question", "question__correct_answer")
        .prefetch_related("question__options")
        .order_by("display_order")
    )
    answers = {
        answer.question_id: answer
        for answer in StudentAnswer.objects.filter(attempt=attempt).select_related("selected_option", "question")
    }
    violations = list(ExamViolation.objects.filter(attempt=attempt).order_by("-detected_at"))

    rows = []
    for exam_question in exam_questions:
        question = exam_question.question
        answer = answers.get(question.id)
        student_answer = "-"
        correct_answer = "-"
        explanation = (question.explanation or "").strip()
        status_label = "Tidak Dijawab"
        status_type = "secondary"
        points_earned = 0.0
        points_possible = _to_float(exam_question.points_override or question.points)

        if question.question_type == "multiple_choice":
            if answer and answer.selected_option:
                student_answer = f"{answer.selected_option.option_letter}. {answer.selected_option.option_text}"
            correct_options = question.options.filter(is_correct=True).order_by("display_order")
            if correct_options.exists():
                correct_answer = ", ".join(
                    [f"{option.option_letter}. {option.option_text}" for option in correct_options]
                )
        else:
            if answer and answer.answer_text:
                student_answer = answer.answer_text
            if hasattr(question, "correct_answer") and question.correct_answer:
                correct_answer = question.correct_answer.answer_text

        if answer:
            points_earned = _to_float(answer.points_earned)
            if answer.is_correct is True:
                status_label = "Benar"
                status_type = "success"
            elif answer.is_correct is False:
                status_label = "Salah"
                status_type = "danger"
            else:
                status_label = "Menunggu Penilaian"
                status_type = "warning"

        rows.append(
            {
                "display_order": exam_question.display_order,
                "question": question,
                "answer": answer,
                "student_answer": student_answer,
                "correct_answer": correct_answer,
                "status_label": status_label,
                "status_type": status_type,
                "points_earned": round(points_earned, 2),
                "points_possible": round(points_possible, 2),
                "time_spent_human": format_seconds_human(answer.time_spent_seconds if answer else 0),
                "explanation": explanation,
                "has_explanation": bool(explanation),
            }
        )

    return {
        "attempt": attempt,
        "exam": exam,
        "result": result,
        "rows": rows,
        "violations": violations,
        "violation_total": len(violations),
    }


def parse_sorting_params(request):
    sort_option = (
        request.GET.get("sort_option")
        or request.POST.get("sort_option")
        or ""
    ).strip().lower()
    if sort_option in SORT_OPTION_MAP:
        return SORT_OPTION_MAP[sort_option]

    sort_by = (request.GET.get("sort") or request.POST.get("sort") or "rank").strip()
    direction = (request.GET.get("dir") or request.POST.get("dir") or "asc").strip().lower()
    if sort_by not in SORTABLE_STUDENT_COLUMNS:
        sort_by = "rank"
    if direction not in {"asc", "desc"}:
        direction = "asc"
    return sort_by, direction


def current_sort_option(sort_by, direction):
    for option_value, pair in SORT_OPTION_MAP.items():
        if pair == (sort_by, direction):
            return option_value
    return "rank_asc"


def parse_selected_result_ids(request):
    ids = [value for value in request.GET.getlist("ids") if value]
    ids += [value for value in request.POST.getlist("ids") if value]
    ids += [value for value in request.GET.getlist("selected_ids") if value]
    ids += [value for value in request.POST.getlist("selected_ids") if value]
    csv_value = (request.GET.get("selected_ids") or request.POST.get("selected_ids") or "").strip()
    if csv_value:
        ids += [item.strip() for item in csv_value.split(",") if item.strip()]
    normalized = []
    for value in ids:
        normalized += [item.strip() for item in str(value).split(",") if item.strip()]
    return sorted(set(normalized))


def build_attempt_history_rows(exam, student):
    attempts = list(
        ExamAttempt.objects.filter(exam=exam, student=student)
        .order_by("attempt_number", "created_at")
    )
    if not attempts:
        return []

    results = {
        result.attempt_id: result
        for result in ExamResult.objects.filter(attempt_id__in=[item.id for item in attempts])
    }
    completed_results = [result for result in results.values()]
    final_metrics = _resolve_final_result_metrics(exam, completed_results)
    selected_result = final_metrics["selected_result"]
    final_attempt_id = selected_result.attempt_id if selected_result else None

    rows = []
    for attempt in attempts:
        result = results.get(attempt.id)
        score = _to_float(result.total_score) if result else _to_float(attempt.total_score)
        percentage = _to_float(result.percentage) if result else _to_float(attempt.percentage)
        passed = bool(result.passed if result else attempt.passed)
        rows.append(
            {
                "attempt_id": str(attempt.id),
                "attempt_number": int(attempt.attempt_number or 0),
                "started_at": attempt.start_time,
                "started_at_label": timezone.localtime(attempt.start_time).strftime("%d %b %Y %H:%M")
                if attempt.start_time
                else "-",
                "submitted_at": attempt.submit_time,
                "submitted_at_label": timezone.localtime(attempt.submit_time).strftime("%d %b %Y %H:%M")
                if attempt.submit_time
                else "-",
                "status": attempt.status,
                "status_label": attempt.get_status_display() if hasattr(attempt, "get_status_display") else attempt.status,
                "total_score": round(score, 2),
                "percentage": round(percentage, 2),
                "passed": passed,
                "duration_seconds": int(attempt.time_spent_seconds or 0),
                "duration_label": format_seconds_human(attempt.time_spent_seconds or 0),
                "is_final": bool(final_attempt_id and final_attempt_id == attempt.id),
            }
        )
    return rows


def build_export_rows(exam, selected_ids=None, sort_by="rank", direction="asc"):
    base_qs = ExamResult.objects.filter(exam=exam).select_related("student").order_by(
        "-percentage",
        "-total_score",
        "time_taken_seconds",
    )
    ordered_rows = build_student_result_rows(base_qs, sort_by=sort_by, direction=direction)
    if selected_ids:
        selected_set = set(selected_ids)
        ordered_rows = [row for row in ordered_rows if row["id"] in selected_set]
    return ordered_rows


def build_analytics_summary(exam_rows):
    if not exam_rows:
        return {
            "total_exam": 0,
            "total_peserta": 0,
            "rata_rata_nilai": 0.0,
            "rata_rata_kelulusan": 0.0,
        }

    total_exam = len(exam_rows)
    total_peserta = sum(row["participants"] for row in exam_rows)
    avg_score = sum(row["average_score"] for row in exam_rows) / total_exam
    avg_pass_rate = sum(row["pass_rate"] for row in exam_rows) / total_exam
    return {
        "total_exam": total_exam,
        "total_peserta": total_peserta,
        "rata_rata_nilai": round(avg_score, 2),
        "rata_rata_kelulusan": round(avg_pass_rate, 2),
    }


def build_analytics_chart_data(teacher, exam_rows):
    trend_labels = []
    trend_values = []
    pass_labels = []
    pass_values = []
    for row in sorted(exam_rows, key=lambda item: item["exam"].start_time):
        trend_labels.append(row["exam"].title[:22])
        trend_values.append(row["average_score"])
        pass_labels.append(row["exam"].title[:22])
        pass_values.append(row["pass_rate"])

    class_perf = defaultdict(list)
    exam_ids = [row["exam"].id for row in exam_rows]
    results_group = defaultdict(lambda: defaultdict(list))
    for result in (
        ExamResult.objects.filter(
            exam_id__in=exam_ids,
            exam__created_by=teacher,
            exam__is_deleted=False,
            attempt__status__in=COMPLETED_ATTEMPT_STATUSES,
        )
        .select_related("exam", "attempt")
        .order_by("exam_id", "student_id", "-attempt__attempt_number", "-created_at")
    ):
        results_group[result.exam_id][result.student_id].append(result)

    for exam in Exam.objects.filter(created_by=teacher, is_deleted=False, id__in=exam_ids):
        class_ids = (
            exam.assignments.filter(assigned_to_type="class", class_obj__isnull=False)
            .values_list("class_obj_id", flat=True)
            .distinct()
        )
        if not class_ids:
            continue

        student_final_score_map = {}
        for student_id, student_rows in results_group.get(exam.id, {}).items():
            metrics = _resolve_final_result_metrics(exam, student_rows)
            student_final_score_map[student_id] = metrics["final_percentage"]
        if not student_final_score_map:
            continue

        membership = ClassStudent.objects.filter(
            class_obj_id__in=class_ids,
            student_id__in=student_final_score_map.keys(),
        ).values("class_obj__name", "student_id")
        for item in membership:
            class_perf[item["class_obj__name"]].append(student_final_score_map[item["student_id"]])

    class_labels = sorted(class_perf.keys())
    class_values = [
        round(sum(scores) / len(scores), 2) if scores else 0.0
        for scores in [class_perf[label] for label in class_labels]
    ]

    return {
        "trend": {"labels": trend_labels, "values": trend_values},
        "pass_rate": {"labels": pass_labels, "values": pass_values},
        "class_avg": {"labels": class_labels, "values": class_values},
    }
