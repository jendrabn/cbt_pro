from django.urls import path

from .views import AdminAnalyticsView, ExportAnalyticsView, SystemReportsView

urlpatterns = [
    path("admin/analytics/", AdminAnalyticsView.as_view(), name="admin_analytics"),
    path("admin/analytics/reports/", SystemReportsView.as_view(), name="system_reports"),
    path("admin/analytics/export/", ExportAnalyticsView.as_view(), name="export_analytics"),
]
