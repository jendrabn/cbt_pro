from django.urls import path

from .views import (
    SubjectAPIView,
    SubjectCreateView,
    SubjectDeleteView,
    SubjectListView,
    SubjectUpdateView,
)

urlpatterns = [
    path("admin/subjects/", SubjectListView.as_view(), name="subject_list"),
    path("admin/subjects/create/", SubjectCreateView.as_view(), name="subject_create"),
    path("admin/subjects/<uuid:pk>/edit/", SubjectUpdateView.as_view(), name="subject_edit"),
    path("admin/subjects/<uuid:pk>/delete/", SubjectDeleteView.as_view(), name="subject_delete"),
    path("api/subjects/", SubjectAPIView.as_view(), name="subject_api"),
]
