from django.urls import path

from .views import (
    AdminDashboardView,
    StudentDashboardView,
    TeacherDashboardView,
)

urlpatterns = [
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path(
        "teacher/dashboard/",
        TeacherDashboardView.as_view(),
        name="teacher_dashboard",
    ),
    path(
        "student/dashboard/",
        StudentDashboardView.as_view(),
        name="student_dashboard",
    ),
]
