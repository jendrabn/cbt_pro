from django.urls import path

from .views import (
    ExamCreateWizard,
    ExamDeleteView,
    ExamDetailView,
    ExamDuplicateView,
    ExamListView,
    ExamPreviewView,
    ExamPublishView,
    ExamQuestionPickerView,
    ExamUpdateView,
)

urlpatterns = [
    path("teacher/exams/", ExamListView.as_view(), name="exam_list"),
    path("teacher/exams/create/", ExamCreateWizard.as_view(), name="exam_create"),
    path("teacher/exams/questions/search/", ExamQuestionPickerView.as_view(), name="exam_question_picker"),
    path("teacher/exams/<uuid:pk>/", ExamDetailView.as_view(), name="exam_detail"),
    path("teacher/exams/<uuid:pk>/edit/", ExamUpdateView.as_view(), name="exam_edit"),
    path("teacher/exams/<uuid:pk>/delete/", ExamDeleteView.as_view(), name="exam_delete"),
    path("teacher/exams/<uuid:pk>/publish/", ExamPublishView.as_view(), name="exam_publish"),
    path("teacher/exams/<uuid:pk>/preview/", ExamPreviewView.as_view(), name="exam_preview"),
    path("teacher/exams/<uuid:pk>/duplicate/", ExamDuplicateView.as_view(), name="exam_duplicate"),
]
