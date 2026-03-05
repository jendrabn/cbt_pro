from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.attempts.services import sync_missing_results_for_exam, sync_missing_results_for_student
from apps.core.mixins import RoleRequiredMixin
from apps.exams.models import Exam
from apps.results.models import ExamResult

from .exporters import export_results_to_pdf, export_results_to_xlsx
from .services import (
    build_attempt_history_rows,
    build_analytics_chart_data,
    build_analytics_summary,
    build_answer_review_context,
    build_class_comparison,
    build_exam_comparison_for_teacher,
    build_exam_rows,
    build_export_rows,
    build_item_analysis,
    build_pass_fail_distribution,
    build_score_distribution,
    build_student_performance_charts,
    build_student_result_detail_context,
    build_student_result_rows,
    build_student_results_rows,
    build_student_results_summary,
    calculate_exam_summary,
    calculate_statistics_cards,
    get_certificate_download_url,
    get_exam_results_queryset,
    get_student_filter_options,
    get_student_results_queryset,
    get_teacher_filter_options,
    get_teacher_results_exam_queryset,
    parse_results_filters,
    parse_selected_result_ids,
    parse_student_results_filters,
    parse_sorting_params,
)


def _querystring_without_page(request):
    querydict = request.GET.copy()
    querydict.pop("page", None)
    return querydict.urlencode()


def _querystring_without(request, keys):
    querydict = request.GET.copy()
    for key in keys:
        querydict.pop(key, None)
    return querydict.urlencode()


class TeacherResultsBaseView(RoleRequiredMixin):
    required_role = "teacher"
    permission_denied_message = "Hanya guru yang dapat mengakses hasil & analitik ujian."


class StudentResultsBaseView(RoleRequiredMixin):
    required_role = "student"
    permission_denied_message = "Hanya siswa yang dapat mengakses hasil ujian pribadi."


class TeacherResultsListView(TeacherResultsBaseView, ListView):
    model = Exam
    template_name = "results/results_list.html"
    context_object_name = "exams"
    paginate_by = 10

    def get_queryset(self):
        self.filters = parse_results_filters(self.request)
        return get_teacher_results_exam_queryset(self.request.user, self.filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context.get("page_obj")
        page_rows = build_exam_rows(page_obj.object_list if page_obj else context.get("object_list"))
        all_rows = build_exam_rows(self.object_list)
        options = get_teacher_filter_options(self.request.user)
        summary = build_analytics_summary(all_rows)
        querystring = _querystring_without_page(self.request)

        context.update(
            {
                "filters": self.filters,
                "subjects": options["subjects"],
                "classes": options["classes"],
                "exam_rows": page_rows,
                "summary": summary,
                "querystring": querystring,
                "analytics_url": (
                    f"{reverse('teacher_results_analytics')}?{querystring}"
                    if querystring
                    else reverse("teacher_results_analytics")
                ),
            }
        )
        return context


class ExamResultsDetailView(TeacherResultsBaseView, DetailView):
    model = Exam
    pk_url_kwarg = "exam_id"
    context_object_name = "exam"
    template_name = "results/result_detail.html"
    paginate_by = 20

    def get_queryset(self):
        return (
            Exam.objects.filter(created_by=self.request.user, is_deleted=False)
            .select_related("subject")
            .prefetch_related("assignments__class_obj", "exam_questions__question__options")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sync_missing_results_for_exam(self.object)
        sort_by, direction = parse_sorting_params(self.request)
        student_rows = build_student_result_rows(
            get_exam_results_queryset(self.object),
            sort_by=sort_by,
            direction=direction,
        )
        summary = calculate_exam_summary(student_rows, self.object)
        stats_cards = calculate_statistics_cards(student_rows)

        paginator = Paginator(student_rows, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        query_without_page = _querystring_without_page(self.request)
        export_query = _querystring_without(self.request, ["page", "format", "ids", "selected_ids"])
        export_base = reverse("export_results", kwargs={"exam_id": self.object.id})

        context.update(
            {
                "summary": summary,
                "statistics_cards": stats_cards,
                "student_rows": page_obj.object_list,
                "item_analysis": build_item_analysis(self.object),
                "score_distribution": build_score_distribution(student_rows),
                "pass_fail_distribution": build_pass_fail_distribution(student_rows),
                "class_comparison_chart": build_class_comparison(student_rows),
                "exam_comparison_chart": build_exam_comparison_for_teacher(self.request.user, self.object.id),
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
                "sort_by": sort_by,
                "sort_dir": direction,
                "querystring": query_without_page,
                "export_xlsx_url": f"{export_base}?{export_query}&format=xlsx"
                if export_query
                else f"{export_base}?format=xlsx",
                "export_pdf_url": f"{export_base}?{export_query}&format=pdf"
                if export_query
                else f"{export_base}?format=pdf",
                "analytics_url": reverse("teacher_results_analytics"),
            }
        )
        return context


class AnswerReviewView(TeacherResultsBaseView, DetailView):
    model = ExamResult
    pk_url_kwarg = "result_id"
    context_object_name = "result"
    template_name = "results/answer_review.html"

    def get_queryset(self):
        return (
            ExamResult.objects.filter(exam__created_by=self.request.user)
            .select_related("exam", "exam__subject", "student", "attempt")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_context = build_answer_review_context(self.object)
        default_back = reverse("exam_results_detail", kwargs={"exam_id": self.object.exam_id})
        context.update(review_context)
        context["back_url"] = (self.request.GET.get("next") or default_back).strip() or default_back
        return context


class TeacherResultsAnalyticsView(TeacherResultsBaseView, TemplateView):
    template_name = "results/analytics_dashboard.html"
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = parse_results_filters(self.request)
        exams_qs = get_teacher_results_exam_queryset(self.request.user, filters)
        rows = build_exam_rows(exams_qs)
        summary = build_analytics_summary(rows)
        chart_data = build_analytics_chart_data(self.request.user, rows)
        options = get_teacher_filter_options(self.request.user)

        paginator = Paginator(rows, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        querystring = _querystring_without_page(self.request)
        context.update(
            {
                "filters": filters,
                "subjects": options["subjects"],
                "classes": options["classes"],
                "summary": summary,
                "chart_data": chart_data,
                "rows": page_obj.object_list,
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
                "querystring": querystring,
                "results_url": f"{reverse('teacher_results')}?{querystring}" if querystring else reverse("teacher_results"),
            }
        )
        return context


class ExportResultsView(TeacherResultsBaseView, View):
    def get(self, request, exam_id):
        exam = get_object_or_404(
            Exam.objects.filter(created_by=request.user, is_deleted=False).select_related("subject"),
            id=exam_id,
        )
        selected_ids = parse_selected_result_ids(request)
        rows = build_export_rows(exam, selected_ids=selected_ids)

        if not rows:
            messages.warning(request, "Tidak ada data hasil yang dapat diekspor.")
            return redirect("exam_results_detail", exam_id=exam.id)

        summary = calculate_exam_summary(rows, exam)
        export_format = (request.GET.get("format") or "xlsx").strip().lower()
        if export_format == "pdf":
            return export_results_to_pdf(exam, rows, summary)
        return export_results_to_xlsx(exam, rows)


class StudentResultsListView(StudentResultsBaseView, ListView):
    model = ExamResult
    template_name = "results/student_results.html"
    context_object_name = "results"
    paginate_by = 10

    def get_queryset(self):
        sync_missing_results_for_student(self.request.user)
        self.filters = parse_student_results_filters(self.request)
        return get_student_results_queryset(self.request.user, self.filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_rows = build_student_results_rows(self.object_list, status_filter=self.filters.status)
        paginator = Paginator(all_rows, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get("page"))
        summary = build_student_results_summary(all_rows)
        charts = build_student_performance_charts(all_rows)
        subjects = get_student_filter_options(self.request.user)
        querystring = _querystring_without_page(self.request)

        context.update(
            {
                "filters": self.filters,
                "subjects": subjects,
                "result_rows": page_obj.object_list,
                "summary": summary,
                "charts": charts,
                "querystring": querystring,
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
            }
        )
        return context


class StudentResultDetailView(StudentResultsBaseView, DetailView):
    model = ExamResult
    pk_url_kwarg = "result_id"
    context_object_name = "result"
    template_name = "results/student_result_detail.html"

    def get_queryset(self):
        return ExamResult.objects.filter(student=self.request.user).select_related(
            "exam",
            "exam__subject",
            "student",
            "attempt",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail_context = build_student_result_detail_context(self.object)
        default_back = reverse("student_results")
        back_url = (self.request.GET.get("next") or default_back).strip() or default_back
        review_url = reverse("student_answer_review", kwargs={"result_id": self.object.id})
        certificate_url = reverse("student_certificate_download", kwargs={"result_id": self.object.id})

        context.update(detail_context)
        context["back_url"] = back_url
        context["review_url"] = review_url
        context["certificate_download_url"] = certificate_url
        context["attempt_history_url"] = reverse(
            "student_attempt_history",
            kwargs={"exam_id": self.object.exam_id},
        )
        return context


class StudentAnswerReviewView(StudentResultsBaseView, DetailView):
    model = ExamResult
    pk_url_kwarg = "result_id"
    context_object_name = "result"
    template_name = "results/student_answer_review.html"

    def get_queryset(self):
        return ExamResult.objects.filter(student=self.request.user).select_related(
            "exam",
            "exam__subject",
            "student",
            "attempt",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.object.exam.allow_review:
            raise PermissionDenied("Review jawaban untuk ujian ini tidak diizinkan oleh guru.")

        review_context = build_answer_review_context(self.object)
        default_back = reverse("student_result_detail", kwargs={"result_id": self.object.id})
        back_url = (self.request.GET.get("next") or default_back).strip() or default_back

        context.update(review_context)
        context["back_url"] = back_url
        context["result_detail_url"] = reverse("student_result_detail", kwargs={"result_id": self.object.id})
        context["certificate_download_url"] = reverse(
            "student_certificate_download",
            kwargs={"result_id": self.object.id},
        )
        context["certificate_available"] = bool(get_certificate_download_url(self.object))
        return context


class StudentCertificateDownloadView(StudentResultsBaseView, View):
    def get(self, request, result_id):
        result = get_object_or_404(
            ExamResult.objects.filter(student=request.user).select_related("exam", "exam__subject", "attempt"),
            id=result_id,
        )
        certificate_url = get_certificate_download_url(result)
        if not certificate_url:
            messages.warning(request, "Sertifikat belum tersedia untuk hasil ujian ini.")
            return redirect("student_result_detail", result_id=result.id)
        return redirect(certificate_url)


class RetakeHistoryView(TeacherResultsBaseView, TemplateView):
    template_name = "results/retake_history_modal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(
            Exam.objects.filter(created_by=self.request.user, is_deleted=False).select_related("subject"),
            id=self.kwargs["exam_id"],
        )
        student_result = (
            ExamResult.objects.filter(exam=exam, student_id=self.kwargs["student_id"])
            .select_related("student", "attempt")
            .order_by("-attempt__attempt_number", "-created_at")
            .first()
        )
        if not student_result:
            raise Http404("Data siswa untuk ujian ini tidak ditemukan.")
        history_rows = build_attempt_history_rows(exam=exam, student=student_result.student)
        context.update(
            {
                "exam": exam,
                "student": student_result.student,
                "history_rows": history_rows,
            }
        )
        return context


class StudentAttemptHistory(StudentResultsBaseView, TemplateView):
    template_name = "results/student_attempt_history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam = get_object_or_404(Exam.objects.select_related("subject"), id=self.kwargs["exam_id"])
        if not ExamResult.objects.filter(exam=exam, student=self.request.user).exists():
            raise PermissionDenied("Anda tidak memiliki akses ke riwayat attempt ujian ini.")
        history_rows = build_attempt_history_rows(exam=exam, student=self.request.user)
        context.update(
            {
                "exam": exam,
                "history_rows": history_rows,
            }
        )
        return context
