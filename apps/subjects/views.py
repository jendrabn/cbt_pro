from __future__ import annotations

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.core.mixins import RoleRequiredMixin

from .forms import SubjectForm
from .models import Subject
from .services import annotate_subject_usage, get_subject_usage_summary, list_subjects_for_dropdown


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


class AdminSubjectBaseView(RoleRequiredMixin):
    required_role = "admin"
    permission_denied_message = "Hanya admin yang dapat mengakses halaman manajemen mata pelajaran."


class SubjectListView(AdminSubjectBaseView, ListView):
    model = Subject
    template_name = "subjects/subject_list.html"
    context_object_name = "subjects"
    paginate_by = 10

    def get_base_queryset(self):
        return annotate_subject_usage(Subject.objects.all())

    def get_queryset(self):
        queryset = self.get_base_queryset()
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        sort = (self.request.GET.get("sort") or "name").strip()

        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(code__icontains=q))

        status_bool = _as_status_filter(status)
        if status_bool is not None:
            queryset = queryset.filter(is_active=status_bool)

        allowed_sort = {
            "name": "name",
            "-name": "-name",
            "code": "code",
            "-code": "-code",
            "status": "is_active",
            "-status": "-is_active",
            "questions": "question_count",
            "-questions": "-question_count",
            "exams": "exam_count",
            "-exams": "-exam_count",
            "updated": "updated_at",
            "-updated": "-updated_at",
        }
        queryset = queryset.order_by(allowed_sort.get(sort, "name"), "name")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = context.get("page_obj")
        object_list = page_obj.object_list if page_obj else context.get("object_list")

        subject_rows = []
        for subject in object_list:
            usage = get_subject_usage_summary(subject.id)
            subject_rows.append(
                {
                    "subject": subject,
                    "question_count": getattr(subject, "question_count", 0),
                    "exam_count": getattr(subject, "exam_count", 0),
                    "attempt_count": usage["exam_attempts_count"],
                    "usage": usage,
                }
            )

        all_subjects = Subject.objects.all()
        context.update(
            {
                "subject_rows": subject_rows,
                "querystring": _querystring_without_page(self.request),
                "filters": {
                    "q": self.request.GET.get("q", ""),
                    "status": self.request.GET.get("status", ""),
                    "sort": self.request.GET.get("sort", "name"),
                },
                "summary": {
                    "total": all_subjects.count(),
                    "active": all_subjects.filter(is_active=True).count(),
                    "inactive": all_subjects.filter(is_active=False).count(),
                },
                "create_form": SubjectForm(),
            }
        )
        return context


class SubjectCreateView(AdminSubjectBaseView, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = "subjects/subject_form.html"
    success_url = reverse_lazy("subject_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Mata pelajaran '{self.object.name}' berhasil ditambahkan.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Gagal menambahkan mata pelajaran. Periksa kembali data yang diisi.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Tambah Mata Pelajaran"
        context["submit_label"] = "Simpan"
        context["cancel_url"] = reverse("subject_list")
        return context


class SubjectUpdateView(AdminSubjectBaseView, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = "subjects/subject_form.html"
    success_url = reverse_lazy("subject_list")
    context_object_name = "subject"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Mata pelajaran '{self.object.name}' berhasil diperbarui.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Gagal memperbarui mata pelajaran. Periksa kembali data yang diisi.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Mata Pelajaran"
        context["submit_label"] = "Simpan Perubahan"
        context["cancel_url"] = reverse("subject_list")
        return context


class SubjectDeleteView(AdminSubjectBaseView, TemplateView):
    template_name = "subjects/subject_delete_warning.html"

    def dispatch(self, request, *args, **kwargs):
        self.subject_obj = get_object_or_404(Subject, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        confirm_name = (request.POST.get("confirm_name") or "").strip()
        if confirm_name != self.subject_obj.name:
            messages.error(
                request,
                "Konfirmasi penghapusan tidak cocok. "
                f"Ketik persis nama mata pelajaran: {self.subject_obj.name}",
            )
            return redirect("subject_list")

        subject_name = self.subject_obj.name
        self.subject_obj.delete()
        messages.success(
            request,
            f"Mata pelajaran '{subject_name}' berhasil dihapus permanen beserta seluruh data turunannya.",
        )
        return redirect("subject_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usage = get_subject_usage_summary(self.subject_obj.id)
        context.update(
            {
                "subject": self.subject_obj,
                "usage": usage,
                "expected_confirm_text": self.subject_obj.name,
                "cancel_url": reverse("subject_list"),
            }
        )
        return context


class SubjectAPIView(RoleRequiredMixin, View):
    required_roles = ("admin", "teacher", "student")
    permission_denied_message = "Anda tidak memiliki akses untuk mengambil data mata pelajaran."

    def get(self, request):
        active_only = True
        include_inactive = (request.GET.get("include_inactive") or "").strip().lower() in {"1", "true", "yes"}
        if request.user.role == "admin" and include_inactive:
            active_only = False

        queryset = list_subjects_for_dropdown(active_only=active_only)
        keyword = (request.GET.get("q") or "").strip()
        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword))

        payload = [
            {
                "id": str(subject.id),
                "name": subject.name,
                "code": subject.code,
                "description": subject.description or "",
                "is_active": subject.is_active,
            }
            for subject in queryset
        ]
        return JsonResponse({"results": payload})
