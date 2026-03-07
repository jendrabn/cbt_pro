from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.mixins import RoleRequiredMixin

from .exporters import (
    export_import_template_excel,
    export_questions_to_csv,
    export_questions_to_excel,
)
from .forms import QuestionForm, QuestionImportForm
from .importers import import_questions_from_excel
from .models import Question, QuestionCategory, QuestionImportLog
from .services import (
    DIFFICULTY_LABELS,
    QUESTION_TYPE_LABELS,
    duplicate_question,
    filter_teacher_questions,
    generate_question_import_report,
    get_question_import_history,
    get_teacher_question_queryset,
    save_question_from_form,
)
from apps.subjects.models import Subject


def _querystring_without_page(request):
    querydict = request.GET.copy()
    querydict.pop("page", None)
    return querydict.urlencode()


class TeacherQuestionBaseView(RoleRequiredMixin):
    required_role = "teacher"
    permission_denied_message = "Hanya guru yang dapat mengakses halaman bank soal."


class QuestionListView(TeacherQuestionBaseView, ListView):
    model = Question
    template_name = "questions/question_list.html"
    context_object_name = "questions"
    paginate_by = 10

    def get_base_queryset(self):
        return get_teacher_question_queryset(self.request.user)

    def get_queryset(self):
        queryset, filters = filter_teacher_questions(self.get_base_queryset(), self.request.GET)
        self.current_filters = filters
        return queryset

    def _current_querystring_without_page(self):
        return _querystring_without_page(self.request)

    def _redirect_to_current_list(self):
        base_url = reverse("question_list")
        qs = self._current_querystring_without_page()
        return redirect(f"{base_url}?{qs}" if qs else base_url)

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        selected_ids = request.POST.getlist("selected_ids")
        selected_qs = self.get_base_queryset().filter(id__in=selected_ids) if selected_ids else self.get_queryset()

        if action in {"export_csv", "export_excel"}:
            if not selected_qs.exists():
                messages.warning(request, "Tidak ada data soal untuk diekspor.")
                return self._redirect_to_current_list()
            return export_questions_to_csv(selected_qs) if action == "export_csv" else export_questions_to_excel(selected_qs)

        if action == "delete":
            if not selected_ids:
                messages.warning(request, "Pilih minimal satu soal untuk aksi bulk.")
                return self._redirect_to_current_list()

            deleted_count = selected_qs.update(is_deleted=True)
            messages.success(request, f"{deleted_count} soal berhasil dihapus.")
            return self._redirect_to_current_list()

        messages.warning(request, "Aksi tidak dikenali.")
        return self._redirect_to_current_list()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_string = self._current_querystring_without_page()

        context.update(
            {
                "filters": getattr(self, "current_filters", None),
                "subjects": Subject.objects.filter(is_active=True).order_by("name"),
                "categories": QuestionCategory.objects.filter(is_active=True).order_by("name"),
                "question_type_choices": QUESTION_TYPE_LABELS.items(),
                "difficulty_choices": DIFFICULTY_LABELS.items(),
                "querystring": query_string,
                "import_form": QuestionImportForm(),
                "summary": {
                    "total": self.get_base_queryset().count(),
                    "filtered": self.object_list.count(),
                    "multiple_choice": self.get_base_queryset().filter(question_type="multiple_choice").count(),
                    "essay": self.get_base_queryset().filter(question_type="essay").count(),
                    "short_answer": self.get_base_queryset().filter(question_type="short_answer").count(),
                },
            }
        )
        return context


class QuestionCreateView(TeacherQuestionBaseView, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "questions/question_form.html"
    success_url = reverse_lazy("question_list")

    def form_valid(self, form):
        question = save_question_from_form(form, self.request.user)
        self.object = question
        messages.success(self.request, "Soal berhasil dibuat.")
        if "save_and_add" in self.request.POST:
            return redirect("question_create")
        next_url = (self.request.POST.get("next") or "").strip()
        if next_url:
            return redirect(next_url)
        return redirect("question_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Tambah Soal Baru",
                "submit_label": "Simpan Soal",
                "is_create": True,
                "tinymce_api_key": settings.TINYMCE_API_KEY,
            }
        )
        return context


class QuestionUpdateView(TeacherQuestionBaseView, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "questions/question_form.html"
    context_object_name = "question"

    def get_queryset(self):
        return get_teacher_question_queryset(self.request.user)

    def form_valid(self, form):
        save_question_from_form(form, self.request.user, question=self.object)
        messages.success(self.request, "Soal berhasil diperbarui.")
        next_url = (self.request.POST.get("next") or self.request.GET.get("next") or "").strip()
        return redirect(next_url or reverse("question_list"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Edit Soal",
                "submit_label": "Simpan Perubahan",
                "is_create": False,
                "tinymce_api_key": settings.TINYMCE_API_KEY,
            }
        )
        return context


class QuestionDeleteView(TeacherQuestionBaseView, View):
    def post(self, request, pk):
        question = get_object_or_404(
            Question.objects.filter(created_by=request.user, is_deleted=False),
            pk=pk,
        )
        question.is_deleted = True
        question.save(update_fields=["is_deleted"])
        messages.success(request, "Soal berhasil dihapus.")
        next_url = (request.POST.get("next") or reverse("question_list")).strip()
        return redirect(next_url or reverse("question_list"))


class QuestionDuplicateView(TeacherQuestionBaseView, View):
    def post(self, request, pk):
        source = get_object_or_404(
            Question.objects.filter(created_by=request.user, is_deleted=False)
            .prefetch_related("options", "questiontagrelation_set__tag"),
            pk=pk,
        )
        duplicated = duplicate_question(source, request.user)
        messages.success(request, f"Soal berhasil diduplikasi (ID: {duplicated.id}).")
        next_url = (request.POST.get("next") or reverse("question_list")).strip()
        return redirect(next_url or reverse("question_list"))


@method_decorator(xframe_options_sameorigin, name="dispatch")
class QuestionPreviewView(TeacherQuestionBaseView, DetailView):
    model = Question
    template_name = "questions/question_preview.html"
    context_object_name = "question"

    def get_queryset(self):
        return (
            Question.objects.filter(created_by=self.request.user, is_deleted=False)
            .select_related("subject", "category")
            .prefetch_related("options", "questiontagrelation_set__tag", "correct_answer")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["answer"] = getattr(self.object, "correct_answer", None)
        context["options"] = self.object.options.order_by("display_order")
        return context


class QuestionImportView(TeacherQuestionBaseView, View):
    template_name = "questions/question_import.html"

    def _build_context(self, **extra):
        subjects = list(Subject.objects.filter(is_active=True).order_by("name").values_list("name", flat=True))
        context = {
            "form": extra.get("form") or QuestionImportForm(),
            "import_result": extra.get("import_result"),
            "available_subjects": subjects,
            "available_subjects_csv": ", ".join(subjects),
            "history": get_question_import_history(self.request.user, limit=10),
        }
        context.update(extra)
        return context

    def get(self, request):
        return render(request, self.template_name, self._build_context())

    def post(self, request):
        form = QuestionImportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "File import tidak valid.")
            return render(request, self.template_name, self._build_context(form=form))

        upload = form.cleaned_data["import_file"]
        result = import_questions_from_excel(upload, request.user)
        import_result = {
            "total_rows": result.total_rows,
            "total_created": result.success_count,
            "total_skipped": result.skipped_count,
            "total_failed": len(result.error_details),
            "error_details": result.error_details,
            "skip_details": result.skip_details,
        }

        if result.success_count:
            messages.success(
                request,
                f"Impor selesai: {result.success_count} dari {result.total_rows} baris berhasil diproses.",
            )
        if result.skipped_count:
            messages.warning(request, f"{result.skipped_count} baris dilewati saat import soal.")
        if result.error_details:
            messages.error(request, f"{len(result.error_details)} baris gagal diproses.")

        from_modal = request.POST.get("from_modal") == "1"
        if from_modal:
            return redirect("question_list")

        return render(
            request,
            self.template_name,
            self._build_context(form=QuestionImportForm(), import_result=import_result),
        )


class QuestionImportTemplateView(TeacherQuestionBaseView, View):
    def get(self, request):
        return export_import_template_excel()


class QuestionImportReportView(TeacherQuestionBaseView, View):
    def get(self, request, log_id):
        import_log = get_object_or_404(QuestionImportLog, id=log_id, imported_by=request.user)

        try:
            report_bytes = generate_question_import_report(import_log)
        except Exception as exc:
            messages.error(request, f"Gagal membuat laporan import soal: {exc}")
            return redirect("question_import")

        response = HttpResponse(
            report_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
        response["Content-Disposition"] = f'attachment; filename="question_import_report_{timestamp}.xlsx"'
        return response


class QuestionExportView(TeacherQuestionBaseView, View):
    def get(self, request):
        export_format = (request.GET.get("format") or "xlsx").strip().lower()
        ids = request.GET.getlist("ids")
        if export_format not in {"csv", "xlsx"}:
            export_format = "xlsx"

        queryset = get_teacher_question_queryset(request.user)
        if ids:
            queryset = queryset.filter(id__in=ids)
        else:
            queryset, _ = filter_teacher_questions(queryset, request.GET)

        if not queryset.exists():
            messages.warning(request, "Tidak ada data soal untuk diekspor.")
            query_string = urlencode(
                {k: v for k, v in request.GET.items() if k not in {"format", "ids", "page"}},
                doseq=True,
            )
            target = reverse("question_list")
            return redirect(f"{target}?{query_string}" if query_string else target)

        if export_format == "csv":
            return export_questions_to_csv(queryset)
        return export_questions_to_excel(queryset)
