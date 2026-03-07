from __future__ import annotations

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.mixins import RoleRequiredMixin
from apps.questions.models import Question
from apps.subjects.models import Subject

from .forms import ExamWizardForm
from .models import Exam
from .services import (
    STATUS_LABELS,
    build_exam_detail_context,
    build_exam_list_rows,
    duplicate_exam,
    filter_teacher_exams,
    get_teacher_exam_queryset,
    save_exam_from_form,
    soft_delete_exam,
    toggle_publish_exam,
)


def _querystring_without_page(request):
    querydict = request.GET.copy()
    querydict.pop("page", None)
    return querydict.urlencode()


class TeacherExamBaseView(RoleRequiredMixin):
    required_role = "teacher"
    permission_denied_message = "Hanya guru yang dapat mengakses halaman manajemen ujian."


class ExamListView(TeacherExamBaseView, ListView):
    model = Exam
    template_name = "exams/exam_list.html"
    context_object_name = "exams"
    paginate_by = 10

    def get_base_queryset(self):
        return get_teacher_exam_queryset(self.request.user)

    def get_queryset(self):
        queryset, filters = filter_teacher_exams(self.get_base_queryset(), self.request.GET)
        self.current_filters = filters
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context.get("page_obj")
        rows = build_exam_list_rows(page_obj.object_list if page_obj else context.get("object_list"))
        querydict = self.request.GET.copy()
        querydict.pop("page", None)
        querydict_no_view = self.request.GET.copy()
        querydict_no_view.pop("page", None)
        querydict_no_view.pop("view", None)
        context.update(
            {
                "exam_rows": rows,
                "filters": getattr(self, "current_filters", None),
                "subjects": Subject.objects.filter(is_active=True).order_by("name"),
                "status_choices": STATUS_LABELS.items(),
                "querystring": querydict.urlencode(),
                "querystring_without_view": querydict_no_view.urlencode(),
                "view_mode": getattr(self.current_filters, "view_mode", "table"),
            }
        )
        return context


class ExamCreateWizard(TeacherExamBaseView, CreateView):
    model = Exam
    form_class = ExamWizardForm
    template_name = "exams/exam_wizard.html"
    success_url = reverse_lazy("exam_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user
        return kwargs

    def form_valid(self, form):
        exam = save_exam_from_form(form, self.request.user)
        self.object = exam
        messages.success(
            self.request,
            f"Ujian '{exam.title}' berhasil {'dipublikasikan' if exam.status == 'published' else 'disimpan sebagai draf'}.",
        )
        return redirect("exam_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Buat Ujian Baru",
                "submit_label": "Simpan Ujian",
                "is_create": True,
            }
        )
        return context


class ExamQuestionPickerView(TeacherExamBaseView, View):
    VALID_TYPES = {"multiple_choice", "essay", "short_answer"}
    MAX_PAGE_SIZE = 100
    DEFAULT_PAGE_SIZE = 50

    def get(self, request):
        keyword = (request.GET.get("q") or "").strip()
        subject_id = (request.GET.get("subject") or "").strip()
        category_id = (request.GET.get("category") or "").strip()
        question_type = (request.GET.get("question_type") or "").strip()

        try:
            page = max(int(request.GET.get("page", 1)), 1)
        except (TypeError, ValueError):
            page = 1

        try:
            page_size = int(request.GET.get("page_size", self.DEFAULT_PAGE_SIZE))
        except (TypeError, ValueError):
            page_size = self.DEFAULT_PAGE_SIZE
        page_size = max(10, min(page_size, self.MAX_PAGE_SIZE))

        queryset = (
            Question.objects.filter(created_by=request.user, is_deleted=False, is_active=True)
            .select_related("subject", "category")
            .only(
                "id",
                "question_text",
                "question_type",
                "points",
                "allow_previous",
                "allow_next",
                "force_sequential",
                "subject_id",
                "subject__name",
                "category_id",
                "category__name",
                "updated_at",
            )
            .order_by("-updated_at")
        )

        if keyword:
            queryset = queryset.filter(
                Q(question_text__icontains=keyword)
                | Q(subject__name__icontains=keyword)
                | Q(category__name__icontains=keyword)
            )
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if question_type in self.VALID_TYPES:
            queryset = queryset.filter(question_type=question_type)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        items = [
            {
                "id": str(question.id),
                "text": strip_tags(question.question_text or ""),
                "subject_id": str(question.subject_id) if question.subject_id else "",
                "subject_name": question.subject.name if question.subject_id else "",
                "category_id": str(question.category_id) if question.category_id else "",
                "category_name": question.category.name if question.category_id else "Tanpa kategori",
                "question_type": question.question_type,
                "points": str(question.points),
                "allow_previous": bool(question.allow_previous),
                "allow_next": bool(question.allow_next),
                "force_sequential": bool(question.force_sequential),
            }
            for question in page_obj.object_list
        ]

        return JsonResponse(
            {
                "items": items,
                "pagination": {
                    "page": page_obj.number,
                    "page_size": page_size,
                    "total_items": paginator.count,
                    "total_pages": paginator.num_pages,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                },
            }
        )


class ExamUpdateView(TeacherExamBaseView, UpdateView):
    model = Exam
    form_class = ExamWizardForm
    template_name = "exams/exam_form.html"
    context_object_name = "exam"

    def get_queryset(self):
        return get_teacher_exam_queryset(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user
        return kwargs

    def form_valid(self, form):
        exam = save_exam_from_form(form, self.request.user, instance=self.object)
        messages.success(
            self.request,
            f"Ujian '{exam.title}' berhasil diperbarui ({'dipublikasikan' if exam.status == 'published' else 'draf'}).",
        )
        return redirect("exam_detail", pk=exam.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Edit Ujian",
                "submit_label": "Simpan Perubahan",
                "is_create": False,
            }
        )
        return context


class ExamDeleteView(TeacherExamBaseView, View):
    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk, created_by=request.user, is_deleted=False)
        title = exam.title
        soft_delete_exam(exam)
        messages.success(request, f"Ujian '{title}' berhasil dihapus.")
        next_url = (request.POST.get("next") or reverse("exam_list")).strip()
        return redirect(next_url or reverse("exam_list"))


class ExamPublishView(TeacherExamBaseView, View):
    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk, created_by=request.user, is_deleted=False)
        previous = exam.status
        updated = toggle_publish_exam(exam)
        if previous == updated.status:
            messages.info(request, f"Status ujian '{exam.title}' tidak berubah.")
        elif updated.status == "published":
            messages.success(request, f"Ujian '{exam.title}' berhasil dipublikasikan.")
        else:
            messages.success(request, f"Ujian '{exam.title}' dikembalikan ke draf.")
        next_url = (request.POST.get("next") or reverse("exam_list")).strip()
        return redirect(next_url or reverse("exam_list"))


class ExamDuplicateView(TeacherExamBaseView, View):
    def post(self, request, pk):
        exam = get_object_or_404(
            Exam.objects.filter(created_by=request.user, is_deleted=False)
            .prefetch_related("exam_questions", "assignments"),
            pk=pk,
        )
        duplicated = duplicate_exam(exam, request.user)
        messages.success(request, f"Ujian berhasil diduplikasi menjadi '{duplicated.title}'.")
        next_url = (request.POST.get("next") or reverse("exam_list")).strip()
        return redirect(next_url or reverse("exam_list"))


@method_decorator(xframe_options_sameorigin, name="dispatch")
class ExamPreviewView(TeacherExamBaseView, DetailView):
    model = Exam
    template_name = "exams/exam_preview.html"
    context_object_name = "exam"

    def get_queryset(self):
        return get_teacher_exam_queryset(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_exam_detail_context(self.object))
        context["exam_status_label"] = STATUS_LABELS.get(self.object.status, self.object.status)
        return context


class ExamDetailView(TeacherExamBaseView, DetailView):
    model = Exam
    template_name = "exams/exam_detail.html"
    context_object_name = "exam"

    def get_queryset(self):
        return get_teacher_exam_queryset(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_exam_detail_context(self.object))
        context["exam_status_label"] = STATUS_LABELS.get(self.object.status, self.object.status)
        return context
