from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.core.services import get_auth_feature_settings, get_branding_settings

from .forms import (
    AvatarUploadForm,
    CustomPasswordChangeForm,
    LoginForm,
    ProfileUpdateForm,
    RoleRegistrationForm,
)
from .models import User, UserProfile


def get_role_redirect_url(user):
    role_to_name = {
        "admin": "admin_dashboard",
        "teacher": "teacher_dashboard",
        "student": "student_dashboard",
    }
    return reverse(role_to_name.get(getattr(user, "role", ""), "landing"))


class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        remember_me = form.cleaned_data.get("remember_me")
        if remember_me:
            self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            self.request.session.set_expiry(0)
        self.request.session.modified = True
        return response

    def get_success_url(self):
        redirect_url = self.get_redirect_url()
        if redirect_url:
            return redirect_url
        return get_role_redirect_url(self.request.user)


class AuthFeatureToggleMixin:
    feature_key = None

    def dispatch(self, request, *args, **kwargs):
        if self.feature_key:
            features = get_auth_feature_settings()
            if not features.get(self.feature_key, False):
                raise Http404("Fitur autentikasi ini belum diaktifkan.")
        return super().dispatch(request, *args, **kwargs)


class ForgotPasswordView(AuthFeatureToggleMixin, PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")
    feature_key = "auth_enable_forgot_password"


class ForgotPasswordDoneView(AuthFeatureToggleMixin, PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"
    feature_key = "auth_enable_password_reset"


class ResetPasswordConfirmView(AuthFeatureToggleMixin, PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")
    feature_key = "auth_enable_password_reset"


class ResetPasswordCompleteView(AuthFeatureToggleMixin, PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
    feature_key = "auth_enable_password_reset"


class LogoutView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "Anda telah logout dari sistem.")
        return redirect("login")

    def get(self, request, *args, **kwargs):
        return redirect("login")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        context["profile"] = profile
        context["profile_form"] = kwargs.get("profile_form") or ProfileUpdateForm(
            instance=profile,
            user=user,
        )
        context["avatar_form"] = kwargs.get("avatar_form") or AvatarUploadForm(
            instance=profile
        )
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile, user=user)
        avatar_form = AvatarUploadForm(request.POST, request.FILES, instance=profile)

        if profile_form.is_valid() and avatar_form.is_valid():
            profile_form.save()

            avatar_file = avatar_form.cleaned_data.get("profile_picture")
            if avatar_file:
                profile.profile_picture = avatar_file
                profile.save()

            messages.success(request, "Profil berhasil diperbarui.")
            return redirect("profile")

        return self.render_to_response(
            self.get_context_data(profile_form=profile_form, avatar_form=avatar_form)
        )


class ChangePasswordView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/change_password.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["password_form"] = kwargs.get("password_form") or CustomPasswordChangeForm(
            user=self.request.user
        )
        return context

    def post(self, request, *args, **kwargs):
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if password_form.is_valid():
            password_form.save()
            update_session_auth_hash(request, password_form.user)
            messages.success(request, "Password berhasil diperbarui.")
            return redirect("change_password")

        return self.render_to_response(self.get_context_data(password_form=password_form))


class BaseRegistrationView(AuthFeatureToggleMixin, FormView):
    template_name = "accounts/register.html"
    form_class = RoleRegistrationForm
    success_url = reverse_lazy("login")
    role = None
    role_title = ""
    role_description = ""

    def dispatch(self, request, *args, **kwargs):
        if self.role is None:
            raise Http404("Role registrasi tidak valid.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = self.role
        user.is_active = True
        user.save()
        form.save_m2m()
        messages.success(
            self.request,
            f"Akun {self.role_title} berhasil dibuat. Silakan masuk untuk melanjutkan.",
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "role_title": self.role_title,
                "role_description": self.role_description,
            }
        )
        return context


class TeacherRegistrationView(BaseRegistrationView):
    role = User.Role.TEACHER
    role_title = "Guru"
    role_description = "Daftarkan akun guru agar bisa mengelola ujian, bank soal, dan pengawasan."
    feature_key = "auth_enable_teacher_registration"


class StudentRegistrationView(BaseRegistrationView):
    role = User.Role.STUDENT
    role_title = "Siswa"
    role_description = "Buat akses siswa untuk mengikuti ujian digital secara mandiri."
    feature_key = "auth_enable_student_registration"
