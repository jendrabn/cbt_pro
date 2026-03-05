from django.urls import path

from .views import (
    AttemptHistoryAPIView,
    AttemptProctoringAPIView,
    AttemptQuestionAPIView,
    AttemptViolationAPIView,
    ExamListView,
    ExamRoomView,
    ExamStartView,
    ExamSubmitConfirmationView,
    PreRetakeReviewView,
    RetakeCheckView,
    RetakeStartView,
    SaveAnswerAPIView,
    SubmitAttemptAPIView,
)

urlpatterns = [
    path("student/exams/", ExamListView.as_view(), name="student_exam_list"),
    path("student/exams/<uuid:exam_id>/start/", ExamStartView.as_view(), name="exam_start"),
    path("student/exams/<uuid:exam_id>/attempt/", ExamRoomView.as_view(), name="exam_room"),
    path(
        "student/exams/<uuid:attempt_id>/submit/",
        ExamSubmitConfirmationView.as_view(),
        name="exam_submit",
    ),
    path(
        "api/attempts/<uuid:attempt_id>/question/<int:number>/",
        AttemptQuestionAPIView.as_view(),
        name="attempt_question_api",
    ),
    path(
        "api/attempts/<uuid:attempt_id>/save-answer/",
        SaveAnswerAPIView.as_view(),
        name="attempt_save_answer_api",
    ),
    path(
        "api/attempts/<uuid:attempt_id>/submit/",
        SubmitAttemptAPIView.as_view(),
        name="attempt_submit_api",
    ),
    path(
        "api/attempts/<uuid:attempt_id>/violation/",
        AttemptViolationAPIView.as_view(),
        name="attempt_violation_api",
    ),
    path(
        "api/attempts/<uuid:attempt_id>/proctoring/",
        AttemptProctoringAPIView.as_view(),
        name="attempt_proctoring_api",
    ),
    path(
        "student/exams/<uuid:exam_id>/retake/check/",
        RetakeCheckView.as_view(),
        name="retake_check",
    ),
    path(
        "student/exams/<uuid:exam_id>/retake/review/",
        PreRetakeReviewView.as_view(),
        name="pre_retake_review",
    ),
    path(
        "student/exams/<uuid:exam_id>/retake/start/",
        RetakeStartView.as_view(),
        name="retake_start",
    ),
    path(
        "api/attempts/<uuid:exam_id>/history/",
        AttemptHistoryAPIView.as_view(),
        name="attempt_history",
    ),
]
