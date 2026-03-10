from django.urls import path

from .views import (
    QuestionCreateView,
    QuestionDeleteView,
    QuestionDuplicateView,
    QuestionExportView,
    QuestionImportReportView,
    QuestionImportTemplateView,
    QuestionImportView,
    QuestionListView,
    QuestionRichTextBrowserView,
    QuestionPreviewView,
    QuestionRichTextUploadView,
    QuestionUpdateView,
)

urlpatterns = [
    path("teacher/question-bank/", QuestionListView.as_view(), name="question_list"),
    path("teacher/question-bank/create/", QuestionCreateView.as_view(), name="question_create"),
    path("teacher/question-bank/<uuid:pk>/edit/", QuestionUpdateView.as_view(), name="question_edit"),
    path("teacher/question-bank/<uuid:pk>/delete/", QuestionDeleteView.as_view(), name="question_delete"),
    path("teacher/question-bank/<uuid:pk>/duplicate/", QuestionDuplicateView.as_view(), name="question_duplicate"),
    path("teacher/question-bank/<uuid:pk>/preview/", QuestionPreviewView.as_view(), name="question_preview"),
    path(
        "teacher/question-bank/editor/upload/",
        QuestionRichTextUploadView.as_view(),
        name="question_richtext_upload",
    ),
    path(
        "teacher/question-bank/editor/browser/",
        QuestionRichTextBrowserView.as_view(),
        name="question_richtext_browser",
    ),
    path("teacher/question-bank/import/", QuestionImportView.as_view(), name="question_import"),
    path(
        "teacher/question-bank/import/template/",
        QuestionImportTemplateView.as_view(),
        name="question_import_template",
    ),
    path(
        "teacher/question-bank/import/<uuid:log_id>/report/",
        QuestionImportReportView.as_view(),
        name="question_import_report",
    ),
    path("teacher/question-bank/export/", QuestionExportView.as_view(), name="question_export"),
]
