from __future__ import annotations

import uuid
from io import BytesIO
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import DetailView, FormView, ListView, UpdateView
from openpyxl import Workbook

from apps.accounts.models import UserImportLog, UserProfile
from apps.attempts.models import ExamAttempt
from apps.core.mixins import RoleRequiredMixin
from apps.exams.models import Exam

from .exporters import ImportTemplateExporter
from .forms import UserCreateForm, UserEditForm, UserImportForm
from .services import (
    create_user_with_profile,
    delete_import_preview,
    execute_import,
    generate_import_report,
    get_import_history,
    parse_import_file,
    run_bulk_action,
    save_import_preview,
    soft_delete_user,
    toggle_user_status,
    update_user_with_profile,
)

User = get_user_model()


def _parse_bool_status(status):
    if status == "active":
        return True
    if status == "inactive":
        return False
    return None


def _filter_user_queryset(request, queryset):
    q = (request.GET.get("q") or "").strip()
    role = (request.GET.get("role") or "").strip()
    status = (request.GET.get("status") or "").strip()
    date_from = parse_date((request.GET.get("date_from") or "").strip()) if request.GET.get("date_from") else None
    date_to = parse_date((request.GET.get("date_to") or "").strip()) if request.GET.get("date_to") else None

    if q:
        queryset = queryset.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )

    valid_roles = {key for key, _ in User.ROLE_CHOICES}
    if role in valid_roles:
        queryset = queryset.filter(role=role)

    status_value = _parse_bool_status(status)
    if status_value is not None:
        queryset = queryset.filter(is_active=status_value)

    if date_from:
        queryset = queryset.filter(date_joined__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date_joined__date__lte=date_to)

    sort = request.GET.get("sort", "-date_joined")
    allowed_sort = {
        "username",
        "-username",
        "email",
        "-email",
        "role",
        "-role",
        "is_active",
        "-is_active",
        "date_joined",
        "-date_joined",
        "last_login",
        "-last_login",
    }
    if sort not in allowed_sort:
        sort = "-date_joined"
    return queryset.order_by(sort, "username")


def _safe_filename_timestamp():
    return timezone.localtime().strftime("%Y%m%d_%H%M%S")


def _user_rows(queryset):
    rows = []
    for user in queryset:
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = None
        rows.append(
            {
                "id": str(user.id),
                "nama": user.get_full_name().strip() or "-",
                "email": user.email,
                "username": user.username,
                "role": user.get_role_display(),
                "status": "Aktif" if user.is_active else "Nonaktif",
                "tanggal_gabung": timezone.localtime(user.date_joined).strftime("%d-%m-%Y %H:%M"),
                "last_login": timezone.localtime(user.last_login).strftime("%d-%m-%Y %H:%M") if user.last_login else "-",
                "nip": getattr(profile, "teacher_id", "") or "-",
                "nis": getattr(profile, "student_id", "") or "-",
                "kelas": getattr(profile, "class_grade", "") or "-",
                "telepon": getattr(profile, "phone_number", "") or "-",
            }
        )
    return rows


def _export_csv(queryset):
    rows = _user_rows(queryset)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="users_{_safe_filename_timestamp()}.csv"'
    response.write("\ufeff")

    header = [
        "ID",
        "Nama Lengkap",
        "Email",
        "Username",
        "Role",
        "Status",
        "Tanggal Gabung",
        "Last Login",
        "NIP",
        "NIS",
        "Kelas",
        "Telepon",
    ]
    response.write(",".join(header) + "\n")
    def _csv_escape(value):
        return '"' + str(value).replace('"', '""') + '"'

    for row in rows:
        values = [
            row["id"],
            row["nama"],
            row["email"],
            row["username"],
            row["role"],
            row["status"],
            row["tanggal_gabung"],
            row["last_login"],
            row["nip"],
            row["nis"],
            row["kelas"],
            row["telepon"],
        ]
        escaped = [_csv_escape(value) for value in values]
        response.write(",".join(escaped) + "\n")
    return response


def _export_excel(queryset):
    rows = _user_rows(queryset)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Users"

    worksheet.append(
        [
            "ID",
            "Nama Lengkap",
            "Email",
            "Username",
            "Role",
            "Status",
            "Tanggal Gabung",
            "Last Login",
            "NIP",
            "NIS",
            "Kelas",
            "Telepon",
        ]
    )

    for row in rows:
        worksheet.append(
            [
                row["id"],
                row["nama"],
                row["email"],
                row["username"],
                row["role"],
                row["status"],
                row["tanggal_gabung"],
                row["last_login"],
                row["nip"],
                row["nis"],
                row["kelas"],
                row["telepon"],
            ]
        )

    buffer = BytesIO()
    workbook.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="users_{_safe_filename_timestamp()}.xlsx"'
    return response


class AdminUserBaseView(RoleRequiredMixin):
    required_role = "admin"
    permission_denied_message = "Hanya admin yang dapat mengakses halaman manajemen pengguna."


class UserListView(AdminUserBaseView, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_base_queryset(self):
        return User.objects.filter(is_deleted=False).select_related("profile")

    def get_queryset(self):
        return _filter_user_queryset(self.request, self.get_base_queryset())

    def _current_querystring_without_page(self):
        querydict = self.request.GET.copy()
        querydict.pop("page", None)
        return querydict.urlencode()

    def _redirect_to_current_list(self):
        base_url = reverse("user_list")
        qs = self._current_querystring_without_page()
        return redirect(f"{base_url}?{qs}" if qs else base_url)

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip()
        selected_ids = request.POST.getlist("selected_ids")
        selected_qs = self.get_base_queryset().filter(id__in=selected_ids) if selected_ids else self.get_queryset()

        if action in {"export_csv", "export_excel"}:
            if not selected_qs.exists():
                messages.warning(request, "Tidak ada data pengguna untuk diekspor.")
                return self._redirect_to_current_list()
            return _export_csv(selected_qs) if action == "export_csv" else _export_excel(selected_qs)

        if action in {"activate", "deactivate", "delete"}:
            if not selected_ids:
                messages.warning(request, "Pilih minimal satu pengguna untuk aksi bulk.")
                return self._redirect_to_current_list()
            try:
                result = run_bulk_action(
                    selected_qs,
                    action=action,
                    actor=request.user,
                    request=request,
                )
            except ValidationError as exc:
                messages.error(request, exc.message)
                return self._redirect_to_current_list()

            action_text = {
                "activate": "diaktifkan",
                "deactivate": "dinonaktifkan",
                "delete": "dihapus",
            }[action]
            messages.success(request, f"{result.success_count} pengguna berhasil {action_text}.")
            if result.skipped_count:
                messages.warning(request, f"{result.skipped_count} pengguna dilewati karena tidak valid.")
            return self._redirect_to_current_list()

        messages.warning(request, "Aksi tidak dikenali.")
        return self._redirect_to_current_list()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_users = self.get_base_queryset()
        sort_query = self.request.GET.copy()
        sort_query.pop("sort", None)
        sort_query.pop("page", None)
        context.update(
            {
                "filters": {
                    "q": self.request.GET.get("q", ""),
                    "role": self.request.GET.get("role", ""),
                    "status": self.request.GET.get("status", ""),
                    "date_from": self.request.GET.get("date_from", ""),
                    "date_to": self.request.GET.get("date_to", ""),
                    "sort": self.request.GET.get("sort", "-date_joined"),
                },
                "role_choices": User.ROLE_CHOICES,
                "querystring": self._current_querystring_without_page(),
                "sort_querystring": sort_query.urlencode(),
                "summary": {
                    "total": all_users.count(),
                    "active": all_users.filter(is_active=True).count(),
                    "inactive": all_users.filter(is_active=False).count(),
                    "teacher": all_users.filter(role="teacher").count(),
                    "student": all_users.filter(role="student").count(),
                },
            }
        )
        return context


class UserCreateView(AdminUserBaseView, FormView):
    template_name = "users/user_form.html"
    form_class = UserCreateForm
    success_url = reverse_lazy("user_list")

    def form_valid(self, form):
        user, _ = create_user_with_profile(
            form,
            actor=self.request.user,
            request=self.request,
        )
        messages.success(self.request, f"Pengguna {user.username} berhasil dibuat.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Tambah Pengguna", "is_create": True})
        return context


class UserUpdateView(AdminUserBaseView, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "users/user_form.html"
    context_object_name = "target_user"
    success_url = reverse_lazy("user_list")

    def get_queryset(self):
        return User.objects.filter(is_deleted=False)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        target_user = getattr(self, "object", None) or self.get_object()
        kwargs["instance"] = target_user
        profile = UserProfile.objects.filter(user=target_user).first()
        if self.request.method in ("GET", "HEAD"):
            kwargs["initial"] = {
                "phone_number": getattr(profile, "phone_number", "") or "",
                "teacher_id": getattr(profile, "teacher_id", "") or "",
                "subject_specialization": getattr(profile, "subject_specialization", "") or "",
                "student_id": getattr(profile, "student_id", "") or "",
                "class_grade": getattr(profile, "class_grade", "") or "",
            }
        return kwargs

    def form_valid(self, form):
        update_user_with_profile(
            self.object,
            form,
            actor=self.request.user,
            request=self.request,
        )
        messages.success(self.request, f"Data pengguna {self.object.username} berhasil diperbarui.")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"page_title": "Edit Pengguna", "is_create": False})
        return context


class UserDeleteView(AdminUserBaseView, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, is_deleted=False)
        next_url = request.POST.get("next") or reverse("user_list")
        try:
            soft_delete_user(user, actor=request.user, request=request)
            messages.success(request, f"Pengguna {user.username} berhasil dihapus.")
        except ValidationError as exc:
            messages.error(request, exc.message)
        return redirect(next_url)


class ToggleUserStatusView(AdminUserBaseView, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, is_deleted=False)
        status_param = request.POST.get("status", "").strip()
        next_url = request.POST.get("next") or reverse("user_list")

        if status_param in {"active", "inactive"}:
            target_status = status_param == "active"
        else:
            target_status = not user.is_active

        try:
            toggle_user_status(user, target_status, actor=request.user, request=request)
            messages.success(
                request,
                f"Status pengguna {user.username} diubah menjadi {'aktif' if target_status else 'nonaktif'}.",
            )
        except ValidationError as exc:
            messages.error(request, exc.message)
        return redirect(next_url)


class UserDetailView(AdminUserBaseView, DetailView):
    model = User
    template_name = "users/user_detail.html"
    context_object_name = "target_user"

    def get_queryset(self):
        return User.objects.filter(is_deleted=False).select_related("profile")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        profile = UserProfile.objects.filter(user=user).first()

        exam_created_count = 0
        exam_attempt_count = 0
        completed_attempt_count = 0

        if user.role == "teacher":
            exam_created_count = Exam.objects.filter(created_by=user, is_deleted=False).count()
        if user.role == "student":
            attempt_qs = ExamAttempt.objects.filter(student=user)
            exam_attempt_count = attempt_qs.count()
            completed_attempt_count = attempt_qs.filter(
                status__in=["submitted", "auto_submitted", "completed"]
            ).count()

        context.update(
            {
                "activity_logs": user.activity_logs.order_by("-created_at")[:20],
                "profile": profile,
                "stats": {
                    "exam_created_count": exam_created_count,
                    "exam_attempt_count": exam_attempt_count,
                    "completed_attempt_count": completed_attempt_count,
                },
                "back_querystring": urlencode(
                    {
                        key: value
                        for key, value in self.request.GET.items()
                        if key != "page"
                    }
                ),
            }
        )
        return context


class UserExportView(AdminUserBaseView, View):
    def get(self, request):
        export_format = (request.GET.get("format") or "csv").lower()
        ids = request.GET.getlist("ids")

        queryset = User.objects.filter(is_deleted=False).select_related("profile")
        if ids:
            queryset = queryset.filter(id__in=ids)
        else:
            queryset = _filter_user_queryset(request, queryset)

        if not queryset.exists():
            messages.warning(request, "Tidak ada data pengguna untuk diekspor.")
            return redirect("user_list")

        if export_format == "xlsx":
            return _export_excel(queryset)
        return _export_csv(queryset)


class UserImportView(AdminUserBaseView, View):
    template_name = "users/user_import.html"

    def _build_context(self, request, **extra):
        context = {
            "form": extra.get("form") or UserImportForm(),
            "import_result": extra.get("import_result"),
            "history": get_import_history(actor=request.user, limit=30),
        }
        context.update(extra)
        return context

    def _build_preview_data(self, uploaded_file, role, send_credentials_email, preview_result):
        return {
            "role": role,
            "filename": uploaded_file.name,
            "file_size_kb": uploaded_file.size // 1024,
            "send_credentials_email": send_credentials_email,
            "total_rows": preview_result.total_rows,
            "valid_rows": [
                {
                    "row_number": r.row_number,
                    **r.data,
                    "status": "valid",
                }
                for r in preview_result.valid_rows
            ],
            "skip_rows": [
                {
                    "row_number": r.row_number,
                    "username": r.username,
                    "email": r.email,
                    "error": r.error,
                    "status": "skip",
                }
                for r in preview_result.skip_rows
            ],
            "error_rows": [
                {
                    "row_number": r.row_number,
                    "username": r.username,
                    "email": r.email,
                    "error": r.error,
                    "status": "error",
                }
                for r in preview_result.error_rows
            ],
        }

    def get(self, request):
        return self.render_to_response(request, self._build_context(request))

    def post(self, request):
        form = UserImportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "File import tidak valid.")
            return self.render_to_response(request, self._build_context(request, form=form))

        uploaded_file = form.cleaned_data["import_file"]
        role = form.cleaned_data["role"]
        send_credentials_email = form.cleaned_data.get("send_credentials_email", False)

        try:
            preview_result = parse_import_file(uploaded_file, role)
        except Exception as exc:
            messages.error(request, f"Gagal membaca file: {exc}")
            return self.render_to_response(request, self._build_context(request, form=form))

        if preview_result.total_rows == 0:
            messages.warning(request, "File kosong atau tidak berisi data yang dapat diimport.")
            import_result = {
                "total_rows": 0,
                "total_created": 0,
                "total_skipped": 0,
                "total_failed": len(preview_result.error_rows),
                "error_details": [{"error": row.error, "row": row.row_number} for row in preview_result.error_rows],
                "skip_details": [],
            }
            return self.render_to_response(request, self._build_context(request, form=UserImportForm(), import_result=import_result))

        preview_key = str(uuid.uuid4())
        preview_data = self._build_preview_data(
            uploaded_file=uploaded_file,
            role=role,
            send_credentials_email=send_credentials_email,
            preview_result=preview_result,
        )

        save_import_preview(preview_key, preview_data)

        if not preview_data.get("valid_rows"):
            messages.warning(request, "Tidak ada data valid untuk diimport.")
            import_result = {
                "total_rows": preview_result.total_rows,
                "total_created": 0,
                "total_skipped": preview_result.skip_count,
                "total_failed": preview_result.error_count,
                "error_details": preview_data["error_rows"],
                "skip_details": preview_data["skip_rows"],
            }
            delete_import_preview(preview_key)
            return self.render_to_response(request, self._build_context(request, form=UserImportForm(), import_result=import_result))

        try:
            result = execute_import(preview_key, actor=request.user, request=request)
        except ValidationError as exc:
            messages.error(request, exc.message)
            delete_import_preview(preview_key)
            return self.render_to_response(request, self._build_context(request, form=UserImportForm()))
        except Exception as exc:
            messages.error(request, f"Terjadi kesalahan saat import: {exc}")
            delete_import_preview(preview_key)
            return self.render_to_response(request, self._build_context(request, form=UserImportForm()))

        import_result = {
            "total_rows": preview_result.total_rows,
            "total_created": result.total_created,
            "total_skipped": result.total_skipped,
            "total_failed": result.total_failed,
            "error_details": result.error_details,
            "skip_details": result.skip_details,
        }

        if result.total_created:
            messages.success(
                request,
                f"Import selesai: {result.total_created} user berhasil dibuat dari {preview_result.total_rows} baris.",
            )
        if result.total_skipped:
            messages.warning(request, f"{result.total_skipped} baris dilewati karena duplikat/invalid.")
        if result.total_failed:
            messages.error(request, f"{result.total_failed} baris gagal diproses.")

        return self.render_to_response(
            request,
            self._build_context(request, form=UserImportForm(), import_result=import_result),
        )

    def render_to_response(self, request, context):
        from django.shortcuts import render

        return render(request, self.template_name, context)


class UserImportReportView(AdminUserBaseView, View):
    def get(self, request, log_id):
        import_log = get_object_or_404(UserImportLog, id=log_id)

        try:
            report_bytes = generate_import_report(import_log)
        except Exception as exc:
            messages.error(request, f"Gagal membuat laporan: {exc}")
            return redirect("user_list")

        response = HttpResponse(
            report_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
        response["Content-Disposition"] = f'attachment; filename="import_report_{timestamp}.xlsx"'
        return response


class DownloadImportTemplateView(AdminUserBaseView, View):
    def get(self, request, role):
        if role not in ("teacher", "student"):
            return JsonResponse({"error": "Role tidak valid. Pilih 'teacher' atau 'student'."}, status=400)

        if role == "teacher":
            template_bytes = ImportTemplateExporter.create_teacher_template()
            filename = "import_template_teacher.xlsx"
        else:
            template_bytes = ImportTemplateExporter.create_student_template()
            filename = "import_template_student.xlsx"

        response = HttpResponse(
            template_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
