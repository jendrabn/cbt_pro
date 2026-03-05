from django.urls import path

from .views import (
    DownloadImportTemplateView,
    ToggleUserStatusView,
    UserCreateView,
    UserDeleteView,
    UserDetailView,
    UserExportView,
    UserImportReportView,
    UserImportView,
    UserListView,
    UserUpdateView,
)

urlpatterns = [
    path("admin/users/", UserListView.as_view(), name="user_list"),
    path("admin/users/create/", UserCreateView.as_view(), name="user_create"),
    path("admin/users/export/", UserExportView.as_view(), name="user_export"),
    path("admin/users/import/", UserImportView.as_view(), name="user_import"),
    path("admin/users/import/<uuid:log_id>/report/", UserImportReportView.as_view(), name="user_import_report"),
    path("admin/users/import/template/<str:role>/", DownloadImportTemplateView.as_view(), name="user_import_template"),
    path("admin/users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("admin/users/<int:pk>/edit/", UserUpdateView.as_view(), name="user_edit"),
    path("admin/users/<int:pk>/delete/", UserDeleteView.as_view(), name="user_delete"),
    path("admin/users/<int:pk>/toggle-status/", ToggleUserStatusView.as_view(), name="user_toggle_status"),
]
