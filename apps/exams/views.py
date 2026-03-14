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
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.accounts.models import User
from apps.core.mixins import RoleRequiredMixin
from apps.questions.models import Question
from apps.subjects.models import Subject

from .forms import ClassForm, ExamWizardForm
from .models import Class, ClassStudent, Exam, ExamAssignment
from .services import (
    STATUS_LABELS,
    annotate_class_usage,
    build_exam_detail_context,
    build_exam_list_rows,
    duplicate_exam,
    filter_teacher_exams,
    get_class_usage_summary,
    get_teacher_exam_queryset,
    replace_class_members,
    save_exam_from_form,
    soft_delete_exam,
    sync_classes_from_student_profiles,
    toggle_publish_exam,
)


def _querystring_without_page(request):
    querydict = request.GET.copy()
    querydict.pop("page", None)
    return querydict.urlencode()


def _as_status_filter(value):
    if value == "active":
        return True
    if value == "inactive":
        return False
    return None


class AdminClassBaseView(RoleRequiredMixin):
    required_role = "admin"
    permission_denied_message = "Hanya admin yang dapat mengakses halaman manajemen kelas."


class ClassListView(AdminClassBaseView, ListView):
    model = Class
    template_name = "exams/class_list.html"
    context_object_name = "classes"
    paginate_by = 10

    def get_base_queryset(self):
        return annotate_class_usage(Class.objects.all())

    def get_queryset(self):
        queryset = self.get_base_queryset()
        q = (self.request.GET.get("q") or "").strip()
        sort = (self.request.GET.get("sort") or "name").strip()

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q)
                | Q(grade_level__icontains=q)
                | Q(academic_year__icontains=q)
            )

        allowed_sort = {
            "name": "name",
            "-name": "-name",
            "students": "student_count",
            "-students": "-student_count",
            "assignments": "exam_assignment_count",
            "-assignments": "-exam_assignment_count",
            "updated": "updated_at",
            "-updated": "-updated_at",
        }
        return queryset.order_by(allowed_sort.get(sort, "name"), "name")

    def _redirect_to_current_list(self):
        base_url = reverse("class_list")
        qs = _querystring_without_page(self.request)
        return redirect(f"{base_url}?{qs}" if qs else base_url)

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        if action != "sync_profiles":
            messages.warning(request, "Aksi tidak dikenali.")
            return self._redirect_to_current_list()

        result = sync_classes_from_student_profiles()
        if result["students_processed"] == 0:
            messages.info(request, "Belum ada siswa aktif dengan data kelas pada profil.")
            return self._redirect_to_current_list()

        messages.success(
            request,
            "Sinkronisasi kelas selesai. "
            f"Siswa diproses: {result['students_processed']}, "
            f"kelas baru: {result['classes_created']}, "
            f"anggota ditambah: {result['memberships_created']}, "
            f"anggota diperbarui: {result['memberships_updated']}.",
        )
        return self._redirect_to_current_list()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_classes = annotate_class_usage(Class.objects.all())
        context.update(
            {
                "querystring": _querystring_without_page(self.request),
                "filters": {
                    "q": self.request.GET.get("q", ""),
                    "sort": self.request.GET.get("sort", "name"),
                },
                "summary": {
                    "total": all_classes.count(),
                    "assignments": ExamAssignment.objects.count(),
                    "memberships": ClassStudent.objects.count(),
                },
                "create_form": ClassForm(),
            }
        )
        return context


class ClassCreateView(AdminClassBaseView, CreateView):
    model = Class
    form_class = ClassForm
    template_name = "exams/class_form.html"
    success_url = reverse_lazy("class_list")

    def get(self, request, *args, **kwargs):
        return redirect("class_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Kelas '{self.object.name}' berhasil ditambahkan.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Gagal menambahkan kelas. Periksa kembali data yang diisi.")
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(self.request, error)
        return redirect("class_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Tambah Kelas",
                "submit_label": "Simpan",
                "cancel_url": reverse("class_list"),
            }
        )
        return context


class ClassUpdateView(AdminClassBaseView, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = "exams/class_form.html"
    context_object_name = "class_obj"
    success_url = reverse_lazy("class_list")

    def get(self, request, *args, **kwargs):
        return redirect("class_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Kelas '{self.object.name}' berhasil diperbarui.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Gagal memperbarui kelas. Periksa kembali data yang diisi.")
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(self.request, error)
        return redirect("class_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": "Edit Kelas",
                "submit_label": "Simpan Perubahan",
                "cancel_url": reverse("class_list"),
            }
        )
        return context


class ClassDeleteView(AdminClassBaseView, TemplateView):
    template_name = "exams/class_delete_warning.html"

    def dispatch(self, request, *args, **kwargs):
        self.class_obj = get_object_or_404(Class, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return redirect("class_list")

    def post(self, request, *args, **kwargs):
        confirm_name = (request.POST.get("confirm_name") or "").strip()
        if confirm_name != self.class_obj.name:
            messages.error(
                request,
                "Konfirmasi penghapusan tidak cocok. "
                f"Ketik persis nama kelas: {self.class_obj.name}",
            )
            return redirect("class_list")

        class_name = self.class_obj.name
        self.class_obj.delete()
        messages.success(request, f"Kelas '{class_name}' berhasil dihapus permanen.")
        return redirect("class_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "class_obj": self.class_obj,
                "usage": get_class_usage_summary(self.class_obj),
                "expected_confirm_text": self.class_obj.name,
                "cancel_url": reverse("class_list"),
            }
        )
        return context


class ClassMembersView(AdminClassBaseView, TemplateView):
    template_name = "exams/class_members.html"

    def dispatch(self, request, *args, **kwargs):
        self.class_obj = get_object_or_404(Class, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def _current_url(self):
        base_url = reverse("class_members", kwargs={"pk": self.class_obj.pk})
        qs = _querystring_without_page(self.request)
        return f"{base_url}?{qs}" if qs else base_url

    def get_student_queryset(self):
        queryset = User.objects.filter(role="student", is_deleted=False).select_related("profile")
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()

        if q:
            queryset = queryset.filter(
                Q(username__icontains=q)
                | Q(email__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(profile__student_id__icontains=q)
                | Q(profile__class_grade__icontains=q)
            )

        status_value = _as_status_filter(status)
        if status_value is not None:
            queryset = queryset.filter(is_active=status_value)

        return queryset.order_by("first_name", "last_name", "username")

    def post(self, request, *args, **kwargs):
        selected_student_ids = request.POST.getlist("student_ids")
        result = replace_class_members(self.class_obj, selected_student_ids)
        messages.success(
            request,
            f"Anggota kelas '{self.class_obj.name}' berhasil disimpan. "
            f"Terpilih: {result['selected_total']}, "
            f"ditambahkan: {result['memberships_added']}, "
            f"dilepas: {result['memberships_removed']}.",
        )
        return redirect(self._current_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_ids = set(
            ClassStudent.objects.filter(class_obj=self.class_obj).values_list("student_id", flat=True)
        )
        student_rows = []
        for student in self.get_student_queryset():
            profile = student.profile if hasattr(student, "profile") else None
            student_rows.append(
                {
                    "student": student,
                    "profile": profile,
                    "is_member": student.id in member_ids,
                }
            )

        context.update(
            {
                "class_obj": self.class_obj,
                "student_rows": student_rows,
                "summary": get_class_usage_summary(self.class_obj),
                "filters": {
                    "q": self.request.GET.get("q", ""),
                    "status": self.request.GET.get("status", ""),
                },
                "querystring": _querystring_without_page(self.request),
            }
        )
        return context


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
        querydict.pop("view", None)
        context.update(
            {
                "exam_rows": rows,
                "filters": getattr(self, "current_filters", None),
                "subjects": Subject.objects.order_by("name"),
                "status_choices": STATUS_LABELS.items(),
                "querystring": querydict.urlencode(),
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
            f"Ujian '{exam.title}' berhasil {'dipublikasikan' if exam.status == Exam.Status.PUBLISHED else 'disimpan sebagai draf'}.",
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
    VALID_TYPES = {
        Question.QuestionType.MULTIPLE_CHOICE,
        Question.QuestionType.CHECKBOX,
        Question.QuestionType.ORDERING,
        Question.QuestionType.MATCHING,
        Question.QuestionType.FILL_IN_BLANK,
        Question.QuestionType.ESSAY,
        Question.QuestionType.SHORT_ANSWER,
    }
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
            f"Ujian '{exam.title}' berhasil diperbarui ({'dipublikasikan' if exam.status == Exam.Status.PUBLISHED else 'draf'}).",
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
        elif updated.status == Exam.Status.PUBLISHED:
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
