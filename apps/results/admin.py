from django.contrib import admin

from .models import Certificate, CertificateTemplate


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "template_name",
        "created_by",
        "layout_preset",
        "layout_type",
        "paper_size",
        "is_default",
        "updated_at",
    )
    list_filter = ("is_default", "layout_preset", "layout_type", "paper_size")
    search_fields = ("template_name", "created_by__username", "created_by__first_name", "created_by__last_name")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        "certificate_number",
        "student",
        "exam",
        "issued_at",
        "is_valid",
        "revoked_at",
        "pdf_generated_at",
    )
    list_filter = ("is_valid", "revoked_at", "issued_at")
    search_fields = (
        "certificate_number",
        "verification_token",
        "student__username",
        "student__first_name",
        "student__last_name",
        "exam__title",
    )
