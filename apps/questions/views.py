from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.mixins import RoleRequiredMixin

from .exporters import (
    export_import_template_excel,
    export_questions_to_excel,
)
from .forms import QuestionForm, QuestionImportForm
from .importers import import_questions_from_excel
from .models import Question, QuestionCategory
from .services import (
    DIFFICULTY_LABELS,
    QUESTION_TYPE_LABELS,
    duplicate_question,
    filter_teacher_questions,
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_string = _querystring_without_page(self.request)
        export_base = reverse("question_export")
        export_xlsx_url = f"{export_base}?{query_string}&format=xlsx" if query_string else f"{export_base}?format=xlsx"

        context.update(
            {
                "filters": getattr(self, "current_filters", None),
                "subjects": Subject.objects.filter(is_active=True).order_by("name"),
                "categories": QuestionCategory.objects.filter(is_active=True).order_by("name"),
                "question_type_choices": QUESTION_TYPE_LABELS.items(),
                "difficulty_choices": DIFFICULTY_LABELS.items(),
                "querystring": query_string,
                "export_xlsx_url": export_xlsx_url,
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

        if result.success_count:
            messages.success(
                request,
                f"Impor selesai: {result.success_count} dari {result.total_rows} baris berhasil diproses.",
            )
        if result.errors:
            messages.warning(request, f"Terdapat {len(result.errors)} baris gagal diproses.")
            for error in result.errors[:10]:
                messages.error(request, error)
            if len(result.errors) > 10:
                messages.info(request, f"... dan {len(result.errors) - 10} error lainnya.")

        from_modal = request.POST.get("from_modal") == "1"
        if from_modal:
            return redirect("question_list")

        return render(
            request,
            self.template_name,
            self._build_context(form=QuestionImportForm(), import_result=result),
        )


class QuestionImportTemplateView(TeacherQuestionBaseView, View):
    def get(self, request):
        return export_import_template_excel()


class QuestionExportView(TeacherQuestionBaseView, View):
    def get(self, request):
        export_format = (request.GET.get("format") or "xlsx").strip().lower()
        ids = request.GET.getlist("ids")

        if export_format != "xlsx":
            messages.error(request, "Format ekspor JSON sudah tidak didukung. Gunakan format Excel (.xlsx).")
            query_string = urlencode(
                {k: v for k, v in request.GET.items() if k not in {"format", "ids", "page"}},
                doseq=True,
            )
            target = reverse("question_list")
            return redirect(f"{target}?{query_string}" if query_string else target)

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

        return export_questions_to_excel(queryset)
