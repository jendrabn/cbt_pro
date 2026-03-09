from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import StudentActiveSession, User, UserActivityLog, UserImportLog, UserProfile


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "is_deleted",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser", "is_deleted", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("CBT Fields", {"fields": ("role", "is_deleted")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("CBT Fields", {"fields": ("role",)}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "teacher_id", "student_id", "class_grade", "phone_number", "updated_at")
    search_fields = ("user__username", "user__email", "teacher_id", "student_id")
    list_select_related = ("user",)


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "ip_address", "created_at")
    search_fields = ("user__username", "action", "description")
    list_filter = ("action", "created_at")
    list_select_related = ("user",)


@admin.register(StudentActiveSession)
class StudentActiveSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "session_key", "login_at", "last_seen_at", "reset_at", "reset_by")
    search_fields = ("user__username", "user__email", "session_key", "ip_address")
    list_select_related = ("user", "reset_by")


@admin.register(UserImportLog)
class UserImportLogAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "imported_by",
        "status",
        "total_rows",
        "total_created",
        "total_skipped",
        "total_failed",
        "created_at",
    )
    search_fields = ("original_filename", "imported_by__username", "imported_by__email")
    list_filter = ("status", "send_credentials_email", "created_at")
    list_select_related = ("imported_by",)
