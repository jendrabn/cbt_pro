from django.urls import path

from .views import SettingsBackupDownloadView, SystemSettingsView

urlpatterns = [
    path("admin/settings/", SystemSettingsView.as_view(), name="system_settings"),
    path(
        "admin/settings/backup/<str:filename>/download/",
        SettingsBackupDownloadView.as_view(),
        name="system_settings_backup_download",
    ),
]
