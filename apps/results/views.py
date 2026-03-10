from datetime import datetime, time
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView
from django.utils import timezone
from django.utils.dateparse import parse_date
from types import SimpleNamespace

from apps.attempts.models import EssayGrading, StudentAnswer
from apps.attempts.services import (
    sync_missing_results_for_exam,
    sync_missing_results_for_student,
    upsert_exam_result_for_attempt,
)
from apps.core.mixins import RoleRequiredMixin
from apps.core.services import get_branding_settings, get_certificate_feature_settings
from apps.exams.models import Exam
from apps.questions.models import Question
from apps.results.models import Certificate, CertificateTemplate, ExamResult

from .certificate_generators import DEFAULT_BODY_TEMPLATE, DEFAULT_HEADER_TEXT
from .certificate_services import (
    certificate_state_label,
    get_certificate_download_url as get_direct_certificate_download_url,
    get_certificate_for_result,
    issue_missing_certificates_for_exam,
    queue_regenerate_certificates_for_template,
    revoke_certificate,
)
from .certificate_utils import render_template_text
from .exporters import (
    export_certificates_to_xlsx,
    export_results_to_csv,
    export_results_to_pdf,
    export_results_to_xlsx,
)
from .forms import CertificateTemplateForm
from .forms import EssayManualGradingForm
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
    current_sort_option,
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


def _parse_teacher_certificate_filters(request):
    status = (request.GET.get("status") or "").strip().lower()
    if status not in {"", "active", "loading", "revoked"}:
        status = ""
    date_from = parse_date((request.GET.get("date_from") or "").strip())
    date_to = parse_date((request.GET.get("date_to") or "").strip())
    if date_from and date_to and date_from > date_to:
        date_from, date_to = date_to, date_from
    return {
        "keyword": (request.GET.get("q") or "").strip(),
        "exam_id": (request.GET.get("exam") or "").strip(),
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
    }


def _teacher_certificate_queryset(user, filters):
    queryset = Certificate.objects.filter(exam__created_by=user).select_related("exam", "student")

    keyword = (filters.get("keyword") or "").strip()
    if keyword:
        queryset = queryset.filter(
            Q(certificate_number__icontains=keyword)
            | Q(exam__title__icontains=keyword)
            | Q(student__username__icontains=keyword)
            | Q(student__first_name__icontains=keyword)
            | Q(student__last_name__icontains=keyword)
        )

    exam_id = (filters.get("exam_id") or "").strip()
    if exam_id:
        queryset = queryset.filter(exam_id=exam_id)

    current_tz = timezone.get_current_timezone()
    date_from = filters.get("date_from")
    if date_from:
        start_dt = timezone.make_aware(datetime.combine(date_from, time.min), current_tz)
        queryset = queryset.filter(issued_at__gte=start_dt)
    date_to = filters.get("date_to")
    if date_to:
        end_dt = timezone.make_aware(datetime.combine(date_to, time.max), current_tz)
        queryset = queryset.filter(issued_at__lte=end_dt)

    status = (filters.get("status") or "").strip().lower()
    ready_filter = (
        (Q(pdf_generated_at__isnull=False) & Q(pdf_file_path__isnull=False) & ~Q(pdf_file_path=""))
        | (Q(certificate_url__isnull=False) & ~Q(certificate_url=""))
    )
    if status == "revoked":
        queryset = queryset.filter(Q(revoked_at__isnull=False) | Q(is_valid=False))
    elif status == "active":
        queryset = queryset.filter(revoked_at__isnull=True, is_valid=True).filter(ready_filter)
    elif status == "loading":
        queryset = queryset.filter(revoked_at__isnull=True, is_valid=True).exclude(ready_filter)

    return queryset.order_by("-issued_at", "-created_at")


def _safe_teacher_certificate_next(next_url: str) -> str:
    fallback = reverse("teacher_certificate_list")
    value = (next_url or "").strip()
    if not value:
        return fallback
    if value.startswith("/teacher/certificates/"):
        return value
    return fallback


def _safe_teacher_bulk_issue_next(next_url: str, exam_id) -> str:
    default_url = reverse("exam_results_detail", kwargs={"exam_id": exam_id})
    value = (next_url or "").strip()
    if not value:
        return default_url
    if value.startswith("/teacher/certificates/") or value.startswith("/teacher/results/"):
        return value
    return default_url


def _certificate_download_response(certificate):
    if certificate.pdf_file_path and default_storage.exists(certificate.pdf_file_path):
        file_handle = default_storage.open(certificate.pdf_file_path, mode="rb")
        filename = f"{certificate.certificate_number}.pdf"
        return FileResponse(file_handle, as_attachment=True, filename=filename)
    fallback_url = get_direct_certificate_download_url(certificate)
    if fallback_url:
        return redirect(fallback_url)
    return None


def _template_preview_context(template_obj):
    branding = get_branding_settings()
    issued_at = timezone.now()
    dummy_certificate = SimpleNamespace(
        certificate_number="CERT-202603-ABC123",
        issued_at=issued_at,
        final_score=92.50,
        final_percentage=92.50,
    )

    placeholders = {
        "student_full_name": "Siswa Contoh",
        "student_id": "2026001",
        "class_grade": "XII IPA 1",
        "exam_title": "Ujian Akhir Semester Matematika",
        "subject_name": "Matematika",
        "final_score": "92.50",
        "percentage": "92.50",
        "grade": "A",
        "issued_date": timezone.localtime(issued_at).strftime("%d %B %Y"),
        "certificate_number": dummy_certificate.certificate_number,
        "institution_name": branding.get("institution_name") or "",
        "institution_type": branding.get("institution_type") or "",
        "signatory_name": template_obj.signatory_name or "",
        "signatory_title": template_obj.signatory_title or "",
        "exam_date": timezone.localtime(issued_at).strftime("%d %B %Y"),
        "verification_url": "/certificates/verify/TOKEN-CONTOH/",
    }
    body_text = render_template_text(
        template_obj.body_text_template or DEFAULT_BODY_TEMPLATE,
        placeholders,
    )

    return {
        "certificate": dummy_certificate,
        "exam": SimpleNamespace(title=placeholders["exam_title"]),
        "student": SimpleNamespace(
            username="siswa.contoh",
            get_full_name=lambda: placeholders["student_full_name"],
        ),
        "branding": branding,
        "template": {
            "layout_preset": template_obj.layout_preset,
            "layout_type": template_obj.layout_type,
            "paper_size": template_obj.paper_size,
            "primary_color": template_obj.primary_color,
            "secondary_color": template_obj.secondary_color,
            "show_logo": template_obj.show_logo,
            "show_score": template_obj.show_score,
            "show_grade": template_obj.show_grade,
            "show_rank": template_obj.show_rank,
            "show_qr_code": template_obj.show_qr_code,
            "qr_code_size": template_obj.qr_code_size,
            "header_text": template_obj.header_text or DEFAULT_HEADER_TEXT,
            "footer_text": template_obj.footer_text or "",
            "background_image_url": template_obj.background_image_url or "",
            "signatory_name": template_obj.signatory_name or "",
            "signatory_title": template_obj.signatory_title or "",
            "signatory_signature_url": template_obj.signatory_signature_url or "",
        },
        "placeholders": placeholders,
        "body_text": body_text,
        "verification_url": placeholders["verification_url"],
    }


def _save_uploaded_asset(file_obj, folder):
    if not file_obj:
        return ""
    filename = str(file_obj.name or "asset").replace("\\", "_").replace("/", "_")
    path = f"{folder}/{timezone.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    return default_storage.save(path, file_obj)


class TeacherResultsBaseView(RoleRequiredMixin):
    required_role = "teacher"
    permission_denied_message = "Hanya guru yang dapat mengakses hasil & analitik ujian."


class StudentResultsBaseView(RoleRequiredMixin):
    required_role = "student"
    permission_denied_message = "Hanya siswa yang dapat mengakses hasil ujian pribadi."


class TeacherCertificatesBaseView(RoleRequiredMixin):
    required_role = "teacher"
    permission_denied_message = "Hanya guru yang dapat mengakses manajemen sertifikat."


class AdminCertificatesBaseView(RoleRequiredMixin):
    required_role = "admin"
    permission_denied_message = "Hanya admin yang dapat mengelola template default sertifikat."


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
    sort_option_choices = [
        ("rank_asc", "Peringkat Tertinggi"),
        ("rank_desc", "Peringkat Terendah"),
        ("name_asc", "Nama A-Z"),
        ("name_desc", "Nama Z-A"),
        ("score_desc", "Skor Tertinggi"),
        ("score_asc", "Skor Terendah"),
        ("percentage_desc", "Persentase Tertinggi"),
        ("percentage_asc", "Persentase Terendah"),
        ("time_asc", "Waktu Tercepat"),
        ("time_desc", "Waktu Terlama"),
        ("violations_desc", "Pelanggaran Terbanyak"),
        ("violations_asc", "Pelanggaran Tersedikit"),
        ("attempts_desc", "Attempts Terbanyak"),
        ("attempts_asc", "Attempts Tersedikit"),
    ]

    def get_queryset(self):
        return (
            Exam.objects.filter(created_by=self.request.user, is_deleted=False)
            .select_related("subject")
            .prefetch_related("assignments__class_obj", "exam_questions__question__options")
        )

    def _current_querystring_without_page(self):
        return _querystring_without_page(self.request)

    def _redirect_to_current_detail(self, exam):
        base_url = reverse("exam_results_detail", kwargs={"exam_id": exam.id})
        qs = self._current_querystring_without_page()
        return redirect(f"{base_url}?{qs}" if qs else base_url)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = (request.POST.get("action") or "").strip()
        selected_ids = request.POST.getlist("selected_ids")
        sort_by, direction = parse_sorting_params(request)

        if action in {"export_csv", "export_excel"}:
            if not selected_ids:
                messages.warning(request, "Pilih minimal satu siswa untuk aksi bulk.")
                return self._redirect_to_current_detail(self.object)

            rows = build_export_rows(
                self.object,
                selected_ids=selected_ids,
                sort_by=sort_by,
                direction=direction,
            )
            if not rows:
                messages.warning(request, "Tidak ada data hasil yang dapat diekspor.")
                return self._redirect_to_current_detail(self.object)

            if action == "export_csv":
                return export_results_to_csv(self.object, rows)
            return export_results_to_xlsx(self.object, rows)

        if action == "issue_certificates":
            result = issue_missing_certificates_for_exam(self.object)
            messages.success(
                request,
                f"Proses issue manual selesai: {result['issued']} diterbitkan, {result['skipped']} dilewati.",
            )
            return self._redirect_to_current_detail(self.object)

        messages.warning(request, "Aksi tidak dikenali.")
        return self._redirect_to_current_detail(self.object)

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

        query_without_page = self._current_querystring_without_page()
        export_query = _querystring_without(self.request, ["page", "format", "ids", "selected_ids", "sort", "dir"])
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
                "current_sort_option": current_sort_option(sort_by, direction),
                "sort_option_choices": self.sort_option_choices,
                "querystring": query_without_page,
                "export_csv_url": f"{export_base}?{export_query}&format=csv"
                if export_query
                else f"{export_base}?format=csv",
                "export_xlsx_url": f"{export_base}?{export_query}&format=xlsx"
                if export_query
                else f"{export_base}?format=xlsx",
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

    def _back_url(self):
        default_back = reverse("exam_results_detail", kwargs={"exam_id": self.object.exam_id})
        return (self.request.GET.get("next") or self.request.POST.get("next") or default_back).strip() or default_back

    def _sync_manual_grading_attempt_status(self):
        pending_essay_answers = StudentAnswer.objects.filter(
            attempt=self.object.attempt,
            question__question_type=Question.QuestionType.ESSAY,
        ).exclude(
            Q(answer_text__isnull=True) | Q(answer_text__exact="")
        ).filter(
            grading__isnull=True,
        )
        next_status = "grading" if pending_essay_answers.exists() else "completed"
        if self.object.attempt.status != next_status:
            self.object.attempt.status = next_status
            self.object.attempt.save(update_fields=["status", "updated_at"])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = EssayManualGradingForm(request.POST)
        if not form.is_valid():
            message = "; ".join(
                error
                for field_errors in form.errors.values()
                for error in field_errors
            )
            messages.error(request, message or "Data penilaian esai tidak valid.")
            return redirect(request.get_full_path())

        answer = get_object_or_404(
            StudentAnswer.objects.select_related("attempt", "question"),
            id=form.cleaned_data["answer_id"],
            attempt=self.object.attempt,
        )

        if answer.question.question_type != Question.QuestionType.ESSAY:
            messages.error(request, "Hanya jawaban esai yang dapat dinilai manual.")
            return redirect(request.get_full_path())

        if not str(answer.answer_text or "").strip():
            messages.error(request, "Jawaban esai kosong. Tidak ada yang bisa dinilai.")
            return redirect(request.get_full_path())

        points_awarded = form.cleaned_data["points_awarded"]
        if points_awarded > answer.points_possible:
            messages.error(
                request,
                f"Nilai esai tidak boleh melebihi {answer.points_possible} poin.",
            )
            return redirect(request.get_full_path())

        feedback = form.cleaned_data["feedback"] or ""

        with transaction.atomic():
            EssayGrading.objects.update_or_create(
                answer=answer,
                defaults={
                    "graded_by": request.user,
                    "points_awarded": points_awarded,
                    "feedback": feedback or None,
                },
            )
            answer.points_earned = points_awarded
            answer.is_correct = bool(points_awarded > 0)
            answer.save(update_fields=["points_earned", "is_correct", "updated_at"])
            self._sync_manual_grading_attempt_status()
            upsert_exam_result_for_attempt(exam=self.object.exam, attempt=self.object.attempt)

        messages.success(request, "Nilai esai berhasil disimpan.")
        return redirect(request.get_full_path())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review_context = build_answer_review_context(self.object)
        context.update(review_context)
        context["back_url"] = self._back_url()
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
        sort_by, direction = parse_sorting_params(request)
        rows = build_export_rows(exam, selected_ids=selected_ids, sort_by=sort_by, direction=direction)

        if not rows:
            messages.warning(request, "Tidak ada data hasil yang dapat diekspor.")
            return redirect("exam_results_detail", exam_id=exam.id)

        summary = calculate_exam_summary(rows, exam)
        export_format = (request.GET.get("format") or "xlsx").strip().lower()
        if export_format == "pdf":
            return export_results_to_pdf(exam, rows, summary)
        if export_format == "csv":
            return export_results_to_csv(exam, rows)
        return export_results_to_xlsx(exam, rows)


class TeacherCertificateTemplateListView(TeacherCertificatesBaseView, ListView):
    model = CertificateTemplate
    template_name = "certificates/template_list.html"
    context_object_name = "templates"

    def get_queryset(self):
        return (
            CertificateTemplate.objects.filter(
                Q(created_by=self.request.user) | Q(is_default=True)
            )
            .select_related("created_by")
            .order_by("-is_default", "template_name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "is_admin_mode": False,
                "create_url": reverse("teacher_certificate_template_create"),
                "list_url": reverse("teacher_certificate_template_list"),
                "preview_url_name": "teacher_certificate_template_preview",
                "base_layout": "layouts/base_teacher.html",
                "topbar_partial": "partials/topbar_teacher.html",
                "header_eyebrow": "Panel Guru",
                "header_title": "Template Sertifikat",
            }
        )
        return context


class TeacherCertificateTemplateCreateView(TeacherCertificatesBaseView, CreateView):
    model = CertificateTemplate
    form_class = CertificateTemplateForm
    template_name = "certificates/template_form.html"

    def form_valid(self, form):
        template_obj = form.save(commit=False)
        template_obj.created_by = self.request.user
        template_obj.is_default = False

        background_file = form.cleaned_data.get("background_image")
        signature_file = form.cleaned_data.get("signatory_signature")
        if background_file:
            template_obj.background_image_url = _save_uploaded_asset(
                background_file,
                "certificates/backgrounds",
            )
        if signature_file:
            template_obj.signatory_signature_url = _save_uploaded_asset(
                signature_file,
                "certificates/signatures",
            )

        template_obj.save()
        messages.success(self.request, f"Template '{template_obj.template_name}' berhasil dibuat.")
        return redirect("teacher_certificate_template_detail", pk=template_obj.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Buat Template Sertifikat",
                "is_edit": False,
                "preview_url": "",
                "back_url": reverse("teacher_certificate_template_list"),
            }
        )
        return context


class TeacherCertificateTemplateDetailView(TeacherCertificatesBaseView, UpdateView):
    model = CertificateTemplate
    form_class = CertificateTemplateForm
    pk_url_kwarg = "pk"
    template_name = "certificates/template_form.html"
    context_object_name = "template_obj"

    def get_queryset(self):
        return CertificateTemplate.objects.filter(created_by=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = (request.POST.get("action") or "").strip().lower()
        if action == "delete":
            if self.object.is_default:
                messages.warning(request, "Template default tidak dapat dihapus.")
                return redirect("teacher_certificate_template_detail", pk=self.object.id)
            if self.object.configured_exams.exists():
                messages.warning(request, "Template masih dipakai pada ujian. Lepaskan dulu dari ujian terkait.")
                return redirect("teacher_certificate_template_detail", pk=self.object.id)
            name = self.object.template_name
            self.object.delete()
            messages.success(request, f"Template '{name}' berhasil dihapus.")
            return redirect("teacher_certificate_template_list")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        template_obj = form.save(commit=False)

        background_file = form.cleaned_data.get("background_image")
        signature_file = form.cleaned_data.get("signatory_signature")
        remove_bg = bool(form.cleaned_data.get("remove_background_image"))
        remove_sig = bool(form.cleaned_data.get("remove_signatory_signature"))

        if remove_bg:
            template_obj.background_image_url = ""
        elif background_file:
            template_obj.background_image_url = _save_uploaded_asset(
                background_file,
                "certificates/backgrounds",
            )

        if remove_sig:
            template_obj.signatory_signature_url = ""
        elif signature_file:
            template_obj.signatory_signature_url = _save_uploaded_asset(
                signature_file,
                "certificates/signatures",
            )

        template_obj.save()
        regen_result = queue_regenerate_certificates_for_template(template_obj)
        messages.success(self.request, f"Template '{template_obj.template_name}' berhasil diperbarui.")
        if regen_result["matched"]:
            messages.info(
                self.request,
                (
                    f"Regenerasi PDF dijadwalkan untuk {regen_result['queued']} sertifikat "
                    f"(total terkait: {regen_result['matched']})."
                ),
            )
        return redirect("teacher_certificate_template_detail", pk=template_obj.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Edit Template Sertifikat",
                "is_edit": True,
                "preview_url": reverse("teacher_certificate_template_preview", kwargs={"pk": self.object.id}),
                "back_url": reverse("teacher_certificate_template_list"),
            }
        )
        return context


class TeacherCertificateTemplatePreviewView(TeacherCertificatesBaseView, View):
    def get(self, request, pk):
        template_obj = get_object_or_404(
            CertificateTemplate.objects.filter(
                Q(created_by=request.user) | Q(is_default=True)
            ),
            pk=pk,
        )
        context = _template_preview_context(template_obj)
        html = render_to_string("certificates/certificate_pdf.html", context=context, request=request)
        return HttpResponse(html)


class AdminCertificateTemplateListView(AdminCertificatesBaseView, ListView):
    model = CertificateTemplate
    template_name = "certificates/template_list.html"
    context_object_name = "templates"

    def get_queryset(self):
        return CertificateTemplate.objects.select_related("created_by").order_by(
            "-is_default",
            "template_name",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "is_admin_mode": True,
                "list_url": reverse("admin_certificate_template_list"),
                "create_url": "",
                "preview_url_name": "admin_certificate_template_preview",
                "base_layout": "layouts/base_admin.html",
                "topbar_partial": "partials/topbar_admin.html",
                "header_eyebrow": "Panel Admin",
                "header_title": "Template Sertifikat",
            }
        )
        return context


class AdminCertificateTemplatePreviewView(AdminCertificatesBaseView, View):
    def get(self, request, pk):
        template_obj = get_object_or_404(CertificateTemplate, pk=pk)
        context = _template_preview_context(template_obj)
        html = render_to_string("certificates/certificate_pdf.html", context=context, request=request)
        return HttpResponse(html)


class SetDefaultTemplateView(AdminCertificatesBaseView, View):
    @transaction.atomic
    def post(self, request, pk):
        target = get_object_or_404(CertificateTemplate, pk=pk)
        CertificateTemplate.objects.filter(is_default=True).exclude(pk=target.pk).update(
            is_default=False,
            updated_at=timezone.now(),
        )
        if not target.is_default:
            target.is_default = True
            target.save(update_fields=["is_default", "updated_at"])
        messages.success(request, f"Template '{target.template_name}' ditetapkan sebagai default sistem.")
        next_url = (request.POST.get("next") or "").strip() or reverse("admin_certificate_template_list")
        return redirect(next_url)


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
        certificate_id = detail_context.get("certificate_id")
        certificate_url = (
            reverse("student_certificate_download_by_id", kwargs={"cert_id": certificate_id})
            if certificate_id
            else reverse("student_certificate_download", kwargs={"result_id": self.object.id})
        )

        context.update(detail_context)
        context["back_url"] = back_url
        context["review_url"] = review_url
        context["certificate_download_url"] = certificate_url
        context["certificate_status_url"] = (
            reverse("student_certificate_status", kwargs={"cert_id": certificate_id})
            if certificate_id
            else ""
        )
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
        certificate = get_certificate_for_result(self.object)
        if certificate:
            context["certificate_download_url"] = reverse(
                "student_certificate_download_by_id",
                kwargs={"cert_id": certificate.id},
            )
            context["certificate_state"] = certificate_state_label(certificate)
            context["certificate_status_url"] = reverse(
                "student_certificate_status",
                kwargs={"cert_id": certificate.id},
            )
            context["certificate_available"] = context["certificate_state"] == "active"
        else:
            context["certificate_download_url"] = reverse(
                "student_certificate_download",
                kwargs={"result_id": self.object.id},
            )
            context["certificate_state"] = "hidden"
            context["certificate_status_url"] = ""
            context["certificate_available"] = False
        return context


class StudentCertificateDownloadView(StudentResultsBaseView, View):
    def get(self, request, result_id):
        result = get_object_or_404(
            ExamResult.objects.filter(student=request.user).select_related("exam", "exam__subject", "attempt"),
            id=result_id,
        )
        certificate = get_certificate_for_result(result)
        if not certificate:
            messages.warning(request, "Sertifikat belum tersedia untuk hasil ujian ini.")
            return redirect("student_result_detail", result_id=result.id)

        state = certificate_state_label(certificate)
        if state == "revoked":
            messages.warning(request, "Sertifikat untuk hasil ujian ini telah dicabut.")
            return redirect("student_result_detail", result_id=result.id)
        if state == "loading":
            messages.info(request, "Sertifikat sedang diproses. Coba lagi beberapa saat.")
            return redirect("student_result_detail", result_id=result.id)

        response = _certificate_download_response(certificate)
        if response:
            return response

        messages.warning(request, "File sertifikat belum tersedia.")
        return redirect("student_result_detail", result_id=result.id)


class StudentCertificateListView(StudentResultsBaseView, ListView):
    model = Certificate
    template_name = "certificates/certificate_list.html"
    context_object_name = "certificates"

    def get_queryset(self):
        return (
            Certificate.objects.filter(student=self.request.user)
            .select_related("exam", "student", "attempt")
            .order_by("-issued_at", "-created_at")
        )


class StudentCertificateDetailView(StudentResultsBaseView, DetailView):
    model = Certificate
    pk_url_kwarg = "cert_id"
    context_object_name = "certificate"
    template_name = "certificates/certificate_detail.html"

    def get_queryset(self):
        return Certificate.objects.filter(student=self.request.user).select_related(
            "exam",
            "student",
            "attempt",
            "attempt__exam",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        state = certificate_state_label(self.object)
        context.update(
            {
                "can_download": state == "active",
                "is_revoked": state == "revoked",
                "status_url": reverse("student_certificate_status", kwargs={"cert_id": self.object.id}),
                "verify_url": reverse("certificate_verify_token", kwargs={"token": self.object.verification_token}),
            }
        )
        return context


class StudentCertificateDownloadByIdView(StudentResultsBaseView, View):
    def get(self, request, cert_id):
        certificate = get_object_or_404(
            Certificate.objects.filter(student=request.user).select_related("exam", "student"),
            id=cert_id,
        )
        state = certificate_state_label(certificate)
        if state == "revoked":
            messages.warning(request, "Sertifikat ini telah dicabut.")
            return redirect("student_certificate_detail", cert_id=certificate.id)
        if state != "active":
            messages.warning(request, "Sertifikat belum siap diunduh.")
            return redirect("student_certificate_detail", cert_id=certificate.id)

        response = _certificate_download_response(certificate)
        if response:
            return response

        messages.warning(request, "File sertifikat belum tersedia.")
        return redirect("student_certificate_detail", cert_id=certificate.id)


class StudentCertificateStatusView(StudentResultsBaseView, View):
    def get(self, request, cert_id):
        certificate = get_object_or_404(
            Certificate.objects.filter(student=request.user),
            id=cert_id,
        )
        state = certificate_state_label(certificate)
        payload = {
            "state": state,
            "certificate_number": certificate.certificate_number,
            "is_revoked": state == "revoked",
            "is_ready": state == "active",
            "download_url": (
                reverse("student_certificate_download_by_id", kwargs={"cert_id": certificate.id})
                if state == "active"
                else ""
            ),
        }
        return JsonResponse(payload)


class VerifyCertificateTokenView(TemplateView):
    template_name = "certificates/certificate_verify.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feature_settings = get_certificate_feature_settings()
        if not feature_settings.get("certificate_verify_public", True):
            context["certificate"] = None
            return context

        token = self.kwargs.get("token", "").strip()
        context["certificate"] = (
            Certificate.objects.filter(verification_token=token)
            .select_related("exam", "student")
            .first()
        )
        return context


class VerifyCertificateNumberView(TemplateView):
    template_name = "certificates/certificate_verify.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feature_settings = get_certificate_feature_settings()
        if not feature_settings.get("certificate_verify_public", True):
            context["certificate"] = None
            return context

        cert_number = self.kwargs.get("cert_number", "").strip()
        context["certificate"] = (
            Certificate.objects.filter(certificate_number=cert_number)
            .select_related("exam", "student")
            .first()
        )
        return context


class TeacherCertificateListView(TeacherCertificatesBaseView, ListView):
    model = Certificate
    template_name = "certificates/certificate_teacher_list.html"
    context_object_name = "certificates"
    paginate_by = 20

    def get_queryset(self):
        self.filters = _parse_teacher_certificate_filters(self.request)
        return _teacher_certificate_queryset(self.request.user, self.filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        querystring = _querystring_without_page(self.request)
        exam_options = (
            Exam.objects.filter(
                created_by=self.request.user,
                is_deleted=False,
                certificate_enabled=True,
            )
            .only("id", "title")
            .order_by("-start_time", "title")
        )
        context.update(
            {
                "filters": getattr(self, "filters", _parse_teacher_certificate_filters(self.request)),
                "querystring": querystring,
                "exam_options": exam_options,
                "bulk_issue_exam_options": exam_options,
                "export_xlsx_url": (
                    f"{reverse('teacher_certificate_export')}?{querystring}"
                    if querystring
                    else reverse("teacher_certificate_export")
                ),
            }
        )
        return context


class TeacherCertificateExportView(TeacherCertificatesBaseView, View):
    def get(self, request):
        filters = _parse_teacher_certificate_filters(request)
        certificates = list(
            _teacher_certificate_queryset(request.user, filters)
        )
        if not certificates:
            messages.warning(request, "Belum ada data sertifikat untuk diekspor.")
            return redirect("teacher_certificate_list")
        return export_certificates_to_xlsx(certificates, request.user)


class TeacherRevokeCertificateView(TeacherCertificatesBaseView, View):
    def post(self, request, cert_id):
        certificate = get_object_or_404(
            Certificate.objects.filter(exam__created_by=request.user).select_related("student"),
            id=cert_id,
        )
        next_url = _safe_teacher_certificate_next(request.POST.get("next"))
        reason = (request.POST.get("reason") or "").strip()
        if not reason:
            messages.warning(request, "Alasan pencabutan sertifikat wajib diisi.")
            return redirect(next_url)

        revoke_certificate(certificate, revoked_by=request.user, reason=reason)
        messages.success(request, f"Sertifikat {certificate.certificate_number} berhasil dicabut.")
        return redirect(next_url)


class TeacherBulkIssueCertificatesView(TeacherCertificatesBaseView, View):
    def post(self, request, exam_id):
        exam = get_object_or_404(
            Exam.objects.filter(created_by=request.user, is_deleted=False),
            id=exam_id,
        )
        result = issue_missing_certificates_for_exam(exam)
        messages.success(
            request,
            f"Proses issue manual selesai: {result['issued']} diterbitkan, {result['skipped']} dilewati.",
        )
        return redirect(_safe_teacher_bulk_issue_next(request.POST.get("next"), exam.id))


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
