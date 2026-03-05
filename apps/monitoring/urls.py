from django.urls import path

from .views import (
    ExtendTimeAPIView,
    ForceSubmitAPIView,
    MonitoringAnnouncementAPIView,
    MonitoringDashboardView,
    MonitoringSnapshotAPIView,
    StudentDetailView,
)

urlpatterns = [
    path(
        "teacher/monitoring/<uuid:exam_id>/",
        MonitoringDashboardView.as_view(),
        name="monitoring_dashboard",
    ),
    path(
        "teacher/monitoring/<uuid:exam_id>/snapshot/",
        MonitoringSnapshotAPIView.as_view(),
        name="monitoring_snapshot",
    ),
    path(
        "teacher/monitoring/<uuid:exam_id>/student/<int:student_id>/",
        StudentDetailView.as_view(),
        name="student_detail",
    ),
    path(
        "api/monitoring/<uuid:exam_id>/extend-time/",
        ExtendTimeAPIView.as_view(),
        name="extend_time",
    ),
    path(
        "api/monitoring/<uuid:attempt_id>/force-submit/",
        ForceSubmitAPIView.as_view(),
        name="force_submit",
    ),
    path(
        "api/monitoring/<uuid:exam_id>/announcement/",
        MonitoringAnnouncementAPIView.as_view(),
        name="monitoring_announcement",
    ),
]
