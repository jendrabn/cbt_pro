import shutil
from datetime import datetime

from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import connections
from django.db.models import Avg, Count, Max, Q
from django.utils import timezone
from django.views.generic import TemplateView

from apps.accounts.models import User, UserActivityLog
from apps.attempts.models import ExamAttempt
from apps.core.mixins import RoleRequiredMixin
from apps.exams.models import ClassStudent, Exam, ExamAssignment
from apps.notifications.models import Notification
from apps.questions.models import Question
from apps.results.models import ExamResult
from apps.results.services import build_student_results_rows
from apps.subjects.models import Subject


class DashboardBaseView(RoleRequiredMixin, TemplateView):
    permission_denied_message = "Role akun Anda tidak diizinkan untuk membuka dashboard ini."


def _previous_month_start(start: datetime, total_months: int):
    year = start.year
    month = start.month - total_months
    while month <= 0:
        month += 12
        year -= 1
    return start.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)


def _month_labels(start: datetime, count: int):
    labels = []
    year = start.year
    month = start.month
    month_names = [
        "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
        "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
    ]
    for _ in range(count):
        labels.append((year, month, f"{month_names[month - 1]} {year}"))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return labels


def _get_assigned_exam_queryset(student):
    class_ids = ClassStudent.objects.filter(student=student).values_list("class_obj_id", flat=True)
    return (
        Exam.objects.filter(
            Q(assignments__assigned_to_type="student", assignments__student=student)
            | Q(assignments__assigned_to_type="class", assignments__class_obj_id__in=class_ids),
            is_deleted=False,
        )
        .distinct()
    )


class AdminDashboardView(DashboardBaseView):
    template_name = "dashboard/admin_dashboard.html"
    required_role = "admin"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        teacher_count = User.objects.filter(role="teacher", is_active=True, is_deleted=False).count()
        student_count = User.objects.filter(role="student", is_active=True, is_deleted=False).count()
        total_users = teacher_count + student_count
        total_questions = Question.objects.filter(is_deleted=False).count()
        total_subjects = Subject.objects.count()
        active_exams = Exam.objects.filter(is_deleted=False, status__in=["published", "ongoing"]).count()
        completed_exams = Exam.objects.filter(is_deleted=False, status="completed").count()

        recent_activities = UserActivityLog.objects.select_related("user").order_by("-created_at")[:10]

        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_period = _previous_month_start(month_start, 5)
        labels_spec = _month_labels(start_period, 6)

        growth_map = {}
        growth_users = User.objects.filter(
            is_deleted=False,
            date_joined__gte=start_period,
        ).only("date_joined")
        for user_obj in growth_users:
            local_joined = timezone.localtime(user_obj.date_joined)
            key = (local_joined.year, local_joined.month)
            growth_map[key] = growth_map.get(key, 0) + 1

        status_labels = {
            "draft": "Draft",
            "published": "Dipublikasikan",
            "ongoing": "Berlangsung",
            "completed": "Selesai",
            "cancelled": "Dibatalkan",
        }
        exam_status_data = Exam.objects.filter(is_deleted=False).values("status").annotate(total=Count("id"))
        exam_status_map = {item["status"]: item["total"] for item in exam_status_data}

        database_status = "Sehat"
        try:
            connections["default"].ensure_connection()
        except Exception:
            database_status = "Gangguan"

        total_disk, used_disk, _ = shutil.disk_usage(settings.BASE_DIR)
        storage_usage = round((used_disk / total_disk) * 100, 1) if total_disk else 0

        active_sessions = Session.objects.filter(expire_date__gte=now).count()

        context.update(
            {
                "teacher_count": teacher_count,
                "student_count": student_count,
                "total_users": total_users,
                "total_questions": total_questions,
                "total_subjects": total_subjects,
                "active_exams": active_exams,
                "completed_exams": completed_exams,
                "recent_activities": recent_activities,
                "user_growth_chart": {
                    "labels": [label for _, _, label in labels_spec],
                    "values": [growth_map.get((year, month), 0) for year, month, _ in labels_spec],
                },
                "exam_status_chart": {
                    "labels": [status_labels[key] for key in status_labels],
                    "values": [exam_status_map.get(key, 0) for key in status_labels],
                },
                "database_status": database_status,
                "server_status": "Sehat",
                "storage_usage": storage_usage,
                "active_sessions": active_sessions,
            }
        )
        return context


class TeacherDashboardView(DashboardBaseView):
    template_name = "dashboard/teacher_dashboard.html"
    required_role = "teacher"

    def _get_student_count(self, teacher):
        exam_ids = Exam.objects.filter(created_by=teacher, is_deleted=False).values_list("id", flat=True)
        direct_students = ExamAssignment.objects.filter(
            exam_id__in=exam_ids,
            assigned_to_type="student",
            student__isnull=False,
        ).values_list("student_id", flat=True)
        class_ids = ExamAssignment.objects.filter(
            exam_id__in=exam_ids,
            assigned_to_type="class",
            class_obj__isnull=False,
        ).values_list("class_obj_id", flat=True)
        class_students = ClassStudent.objects.filter(class_obj_id__in=class_ids).values_list("student_id", flat=True)
        student_ids = set(direct_students) | set(class_students)
        return len(student_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user
        now = timezone.now()

        teacher_exams = Exam.objects.filter(created_by=teacher, is_deleted=False)
        result_qs = ExamResult.objects.filter(exam__created_by=teacher)

        exam_aggregate = result_qs.aggregate(
            avg_score=Avg("percentage"),
            total_participant=Count("id"),
            total_lulus=Count("id", filter=Q(passed=True)),
        )
        total_students = self._get_student_count(teacher)

        upcoming_exams = teacher_exams.filter(end_time__gte=now).order_by("start_time")[:6]
        recent_results = result_qs.select_related("student", "exam").order_by("-created_at")[:8]

        pass_rate = 0
        if exam_aggregate["total_participant"]:
            pass_rate = round(
                (exam_aggregate["total_lulus"] / exam_aggregate["total_participant"]) * 100,
                1,
            )

        exam_performance = (
            result_qs.values("exam__title")
            .annotate(rata_rata=Avg("percentage"), peserta=Count("id"))
            .order_by("-rata_rata")[:6]
        )

        context.update(
            {
                "total_questions_created": Question.objects.filter(created_by=teacher, is_deleted=False).count(),
                "active_exams": teacher_exams.filter(status__in=["published", "ongoing"]).count(),
                "total_students": total_students,
                "average_score": round(float(exam_aggregate["avg_score"] or 0), 1),
                "pass_rate": pass_rate,
                "upcoming_exams": upcoming_exams,
                "recent_results": recent_results,
                "exam_performance_chart": {
                    "labels": [item["exam__title"][:24] for item in exam_performance],
                    "values": [round(float(item["rata_rata"] or 0), 1) for item in exam_performance],
                },
            }
        )
        return context


class StudentDashboardView(DashboardBaseView):
    template_name = "dashboard/student_dashboard.html"
    required_role = "student"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user
        now = timezone.now()

        assigned_exams = _get_assigned_exam_queryset(student)
        upcoming_exams = assigned_exams.filter(end_time__gte=now, status__in=["published", "ongoing"]).order_by("start_time")[:6]
        all_result_rows = build_student_results_rows(
            ExamResult.objects.filter(student=student).select_related("exam", "attempt", "student", "exam__subject")
        )
        recent_result_rows = all_result_rows[:8]
        trend_rows = list(reversed(all_result_rows[:6]))
        total_exam_taken = len(all_result_rows)
        average_score = round(sum(row["percentage"] for row in all_result_rows) / total_exam_taken, 1) if total_exam_taken else 0.0
        best_score = round(max((row["percentage"] for row in all_result_rows), default=0.0), 1)

        notifications = Notification.objects.filter(user=student).order_by("-created_at")[:6]
        unread_notifications = Notification.objects.filter(user=student, is_read=False).count()

        completed_attempts = ExamAttempt.objects.filter(
            student=student,
            status__in=["submitted", "auto_submitted", "completed"],
        ).count()

        context.update(
            {
                "now": now,
                "assigned_exam_count": assigned_exams.count(),
                "upcoming_exams": upcoming_exams,
                "recent_result_rows": recent_result_rows,
                "total_exam_taken": total_exam_taken,
                "completed_attempts": completed_attempts,
                "average_score": average_score,
                "best_score": best_score,
                "notifications": notifications,
                "unread_notifications": unread_notifications,
                "trend_chart": {
                    "labels": [row["exam"].title[:20] for row in trend_rows],
                    "values": [round(float(row["percentage"]), 1) for row in trend_rows],
                },
            }
        )
        return context
