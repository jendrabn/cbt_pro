from django.urls import path

from .views import (
    AnswerReviewView,
    ExamResultsDetailView,
    ExportResultsView,
    RetakeHistoryView,
    StudentAttemptHistory,
    StudentAnswerReviewView,
    StudentCertificateDownloadView,
    StudentResultDetailView,
    StudentResultsListView,
    TeacherResultsAnalyticsView,
    TeacherResultsListView,
)

urlpatterns = [
    path("teacher/results/", TeacherResultsListView.as_view(), name="teacher_results"),
    path("teacher/results/analytics/", TeacherResultsAnalyticsView.as_view(), name="teacher_results_analytics"),
    path("teacher/results/<uuid:exam_id>/", ExamResultsDetailView.as_view(), name="exam_results_detail"),
    path("teacher/results/<uuid:result_id>/review/", AnswerReviewView.as_view(), name="answer_review"),
    path("teacher/results/<uuid:exam_id>/export/", ExportResultsView.as_view(), name="export_results"),
    path(
        "teacher/results/<uuid:exam_id>/student/<int:student_id>/attempts/",
        RetakeHistoryView.as_view(),
        name="retake_history",
    ),
    path("student/results/", StudentResultsListView.as_view(), name="student_results"),
    path("student/results/<uuid:result_id>/", StudentResultDetailView.as_view(), name="student_result_detail"),
    path(
        "student/results/<uuid:exam_id>/attempts/",
        StudentAttemptHistory.as_view(),
        name="student_attempt_history",
    ),
    path(
        "student/results/<uuid:result_id>/review/",
        StudentAnswerReviewView.as_view(),
        name="student_answer_review",
    ),
    path(
        "student/results/<uuid:result_id>/certificate/",
        StudentCertificateDownloadView.as_view(),
        name="student_certificate_download",
    ),
]
