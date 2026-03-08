from django.urls import path

from .views import (
    ChangePasswordView,
    ForgotPasswordDoneView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    ProfileView,
    ResetPasswordCompleteView,
    ResetPasswordConfirmView,
    StudentRegistrationView,
    TeacherRegistrationView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("password-reset/", ForgotPasswordView.as_view(), name="password_reset"),
    path("password-reset/done/", ForgotPasswordDoneView.as_view(), name="password_reset_done"),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        ResetPasswordConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("password-reset/complete/", ResetPasswordCompleteView.as_view(), name="password_reset_complete"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("register/guru/", TeacherRegistrationView.as_view(), name="register_teacher"),
    path("register/siswa/", StudentRegistrationView.as_view(), name="register_student"),
]
