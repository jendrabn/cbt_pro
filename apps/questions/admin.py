from django.contrib import admin

from .models import QuestionImportLog


@admin.register(QuestionImportLog)
class QuestionImportLogAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "imported_by",
        "total_rows",
        "total_created",
        "total_failed",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("original_filename", "imported_by__username", "imported_by__email")
