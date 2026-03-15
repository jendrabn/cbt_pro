import json
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.mail import get_connection, send_mail
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import get_valid_filename
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.session_control import invalidate_student_session_timeout_cache
from apps.core.forms import (
    BackupRestoreForm,
    BrandingSettingsForm,
    CertificateSettingsForm,
    EmailSettingsForm,
    ExamDefaultsForm,
    GeneralSettingsForm,
    NotificationSettingsForm,
    SecuritySettingsForm,
)
from apps.core.mixins import RoleRequiredMixin
from apps.core.services import (
    invalidate_auth_feature_cache,
    invalidate_branding_cache,
    invalidate_certificate_feature_cache,
)
from apps.core.utils import render_error_page
from apps.notifications.models import SystemSetting


TAB_CHOICES = (
    "general",
    "branding",
    "email",
    "security",
    "exam_defaults",
    "notifications",
    "certificates",
    "backup",
)

SETTING_META = {
    "timezone": (
        "string",
        "general",
        "Zona waktu aplikasi",
        True,
        getattr(settings, "TIME_ZONE", "Asia/Jakarta"),
    ),
    "language": (
        "string",
        "general",
        "Bahasa default",
        True,
        getattr(settings, "LANGUAGE_CODE", "id"),
    ),
    "landing_page_enabled": (
        "boolean",
        "general",
        "Aktifkan halaman landing pada URL root",
        False,
        True,
    ),
    "institution_name": (
        "string",
        "branding",
        "Nama sekolah/lembaga",
        True,
        getattr(settings, "CBT_SITE_NAME", "Sistem CBT"),
    ),
    "institution_type": (
        "string",
        "branding",
        "Jenis lembaga (SMA, SMK, MA, Universitas, dst.)",
        True,
        "",
    ),
    "institution_address": ("string", "branding", "Alamat lengkap lembaga", False, ""),
    "institution_phone": ("string", "branding", "Nomor telepon/WA lembaga", False, ""),
    "institution_email": ("string", "branding", "Email resmi lembaga", False, ""),
    "institution_website": ("string", "branding", "Website resmi lembaga", True, ""),
    "institution_logo_url": (
        "string",
        "branding",
        "Path logo utama (navbar, login, PDF header)",
        True,
        "",
    ),
    "institution_logo_dark_url": (
        "string",
        "branding",
        "Path logo versi putih/dark",
        True,
        "",
    ),
    "institution_favicon_url": ("string", "branding", "Path favicon browser", True, ""),
    "login_page_headline": ("string", "branding", "Heading halaman login", True, ""),
    "login_page_subheadline": ("string", "branding", "Tagline/sub-heading halaman login", True, ""),
    "login_page_background_url": (
        "string",
        "branding",
        "Path background image halaman login",
        True,
        "",
    ),
    "primary_color": ("string", "branding", "Warna utama UI (HEX)", True, "#1B3A6B"),
    "smtp_host": (
        "string",
        "email",
        "SMTP host",
        False,
        getattr(settings, "EMAIL_HOST", "localhost"),
    ),
    "smtp_port": (
        "number",
        "email",
        "SMTP port",
        False,
        int(getattr(settings, "EMAIL_PORT", 587)),
    ),
    "smtp_username": (
        "string",
        "email",
        "SMTP username",
        False,
        getattr(settings, "EMAIL_HOST_USER", ""),
    ),
    "smtp_password": (
        "string",
        "email",
        "SMTP password",
        False,
        getattr(settings, "EMAIL_HOST_PASSWORD", ""),
    ),
    "smtp_use_tls": (
        "boolean",
        "email",
        "SMTP gunakan TLS",
        False,
        bool(getattr(settings, "EMAIL_USE_TLS", True)),
    ),
    "default_from_email": (
        "string",
        "email",
        "Email pengirim default",
        False,
        getattr(settings, "DEFAULT_FROM_EMAIL", "CBT System <noreply@cbt.com>"),
    ),
    "password_min_length": ("number", "security", "Minimal panjang password", False, 8),
    "session_timeout_minutes": ("number", "security", "Durasi timeout sesi", False, 120),
    "max_login_attempts": ("number", "security", "Maks percobaan login", False, 5),
    "ip_whitelist": ("json", "security", "Daftar IP yang diizinkan", False, []),
    "auth_enable_forgot_password": (
        "boolean",
        "security",
        "Aktifkan fitur lupa password",
        False,
        True,
    ),
    "auth_enable_password_reset": (
        "boolean",
        "security",
        "Aktifkan reset password lewat email",
        False,
        True,
    ),
    "auth_enable_teacher_registration": (
        "boolean",
        "security",
        "Aktifkan registrasi Guru",
        False,
        False,
    ),
    "auth_enable_student_registration": (
        "boolean",
        "security",
        "Aktifkan registrasi Siswa",
        False,
        False,
    ),
    "default_exam_duration": ("number", "exam_defaults", "Durasi ujian default", False, 120),
    "default_passing_score": ("number", "exam_defaults", "Nilai lulus default", False, 60),
    "require_fullscreen_default": ("boolean", "exam_defaults", "Wajib fullscreen", False, True),
    "detect_tab_switch_default": ("boolean", "exam_defaults", "Deteksi pindah tab", False, True),
    "max_violations_allowed_default": ("number", "exam_defaults", "Batas pelanggaran", False, 3),
    "notify_exam_published_email": (
        "boolean",
        "notifications",
        "Notifikasi email ujian publish",
        False,
        True,
    ),
    "notify_exam_result_email": (
        "boolean",
        "notifications",
        "Notifikasi email hasil ujian",
        False,
        True,
    ),
    "notify_system_announcement": (
        "boolean",
        "notifications",
        "Notifikasi pengumuman sistem",
        False,
        True,
    ),
    "notify_daily_summary": ("boolean", "notifications", "Ringkasan harian", False, False),
    "certificate_number_prefix": (
        "string",
        "certificates",
        "Prefix nomor sertifikat",
        False,
        "CERT",
    ),
    "certificate_pdf_dpi": (
        "number",
        "certificates",
        "Resolusi render PDF sertifikat",
        False,
        150,
    ),
    "certificate_storage_path": (
        "string",
        "certificates",
        "Direktori penyimpanan PDF sertifikat",
        False,
        "certificates/",
    ),
    "certificate_email_enabled": (
        "boolean",
        "certificates",
        "Kirim email saat sertifikat diterbitkan",
        False,
        False,
    ),
    "certificate_verify_public": (
        "boolean",
        "certificates",
        "Verifikasi sertifikat publik",
        True,
        True,
    ),
}

BRANDING_FILE_FIELDS = {
    "institution_logo_url": "branding/logo",
    "institution_logo_dark_url": "branding/logo_dark",
    "institution_favicon_url": "branding/favicon",
    "login_page_background_url": "branding/login_bg",
}


def _to_setting_string(value, setting_type):
    if setting_type == "boolean":
        return "true" if bool(value) else "false"
    if setting_type == "number":
        return str(value)
    if setting_type == "json":
        return json.dumps(value)
    return str(value or "")


def _backup_dir():
    directory = Path(settings.MEDIA_ROOT) / "backups" / "system_settings"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


class SystemSettingsView(RoleRequiredMixin, TemplateView):
    template_name = "core/settings.html"
    required_role = "admin"
    permission_denied_message = "Hanya admin yang dapat mengakses halaman pengaturan sistem."

    def _get_active_tab(self):
        tab = self.request.GET.get("tab", "general")
        return tab if tab in TAB_CHOICES else "general"

    def _settings_map(self):
        return {setting.setting_key: setting for setting in SystemSetting.objects.all()}

    def _setting_value(self, key, setting_map):
        if key in setting_map:
            return setting_map[key].get_value()
        return SETTING_META[key][4]

    def _upsert_setting(self, key, value):
        setting_type, category, description, is_public, _ = SETTING_META[key]
        SystemSetting.objects.update_or_create(
            setting_key=key,
            defaults={
                "setting_value": _to_setting_string(value, setting_type),
                "setting_type": setting_type,
                "category": category,
                "description": description,
                "is_public": is_public,
                "updated_by": self.request.user,
            },
        )

    def _save_general_settings(self, form):
        cleaned = form.cleaned_data
        self._upsert_setting("timezone", cleaned["timezone"])
        self._upsert_setting("language", cleaned["language"])

    def _save_branding_settings(self, form):
        cleaned = form.cleaned_data

        self._upsert_setting("institution_name", cleaned.get("institution_name", ""))
        self._upsert_setting("institution_type", cleaned.get("institution_type", ""))
        self._upsert_setting("institution_address", cleaned.get("institution_address", ""))
        self._upsert_setting("institution_phone", cleaned.get("institution_phone", ""))
        self._upsert_setting("institution_email", cleaned.get("institution_email", ""))
        self._upsert_setting("institution_website", cleaned.get("institution_website", ""))
        self._upsert_setting("primary_color", cleaned.get("primary_color", "#1B3A6B"))
        self._upsert_setting("login_page_headline", cleaned.get("login_page_headline", ""))
        self._upsert_setting("login_page_subheadline", cleaned.get("login_page_subheadline", ""))
        self._upsert_setting("landing_page_enabled", cleaned.get("landing_page_enabled", False))

        for field_name, folder in BRANDING_FILE_FIELDS.items():
            uploaded = cleaned.get(field_name)
            if not uploaded:
                continue
            filename = get_valid_filename(uploaded.name)
            storage_path = default_storage.save(
                f"{folder}/{timezone.now().strftime('%Y%m%d_%H%M%S')}_{filename}",
                uploaded,
            )
            self._upsert_setting(field_name, storage_path)

        invalidate_branding_cache()

    def _reset_branding_defaults(self):
        branding_keys = [
            "institution_name",
            "institution_type",
            "institution_address",
            "institution_phone",
            "institution_email",
            "institution_website",
            "institution_logo_url",
            "institution_logo_dark_url",
            "institution_favicon_url",
            "login_page_headline",
            "login_page_subheadline",
            "login_page_background_url",
            "primary_color",
        ]
        for key in branding_keys:
            self._upsert_setting(key, SETTING_META[key][4])
        self._upsert_setting("landing_page_enabled", SETTING_META["landing_page_enabled"][4])
        invalidate_branding_cache()

    def _save_email_settings(self, form):
        cleaned = form.cleaned_data
        setting_map = self._settings_map()

        self._upsert_setting("smtp_host", cleaned["smtp_host"])
        self._upsert_setting("smtp_port", cleaned["smtp_port"])
        self._upsert_setting("smtp_username", cleaned["smtp_username"])

        if cleaned["smtp_password"]:
            self._upsert_setting("smtp_password", cleaned["smtp_password"])
        elif "smtp_password" not in setting_map:
            self._upsert_setting("smtp_password", "")

        self._upsert_setting("smtp_use_tls", cleaned["smtp_use_tls"])
        self._upsert_setting("default_from_email", cleaned["default_from_email"])

    def _send_test_email(self, form):
        cleaned = form.cleaned_data
        recipient = cleaned.get("test_email_recipient")
        if not recipient:
            raise ValueError("Email tujuan test wajib diisi.")

        connection = get_connection(
            host=cleaned["smtp_host"],
            port=cleaned["smtp_port"],
            username=cleaned["smtp_username"] or None,
            password=cleaned["smtp_password"] or None,
            use_tls=cleaned["smtp_use_tls"],
            fail_silently=False,
        )

        send_mail(
            subject="Test Email Sistem CBT",
            message="Ini adalah email test dari halaman Pengaturan Sistem CBT.",
            from_email=cleaned["default_from_email"],
            recipient_list=[recipient],
            connection=connection,
            fail_silently=False,
        )

    def _save_security_settings(self, form):
        cleaned = form.cleaned_data
        self._upsert_setting("password_min_length", cleaned["password_min_length"])
        self._upsert_setting("session_timeout_minutes", cleaned["session_timeout_minutes"])
        self._upsert_setting("max_login_attempts", cleaned["max_login_attempts"])
        self._upsert_setting("ip_whitelist", json.loads(cleaned["ip_whitelist"]))
        self._upsert_setting("auth_enable_forgot_password", cleaned["auth_enable_forgot_password"])
        self._upsert_setting("auth_enable_password_reset", cleaned["auth_enable_password_reset"])
        self._upsert_setting("auth_enable_teacher_registration", cleaned["auth_enable_teacher_registration"])
        self._upsert_setting("auth_enable_student_registration", cleaned["auth_enable_student_registration"])
        invalidate_auth_feature_cache()
        invalidate_student_session_timeout_cache()

    def _save_exam_defaults(self, form):
        cleaned = form.cleaned_data
        self._upsert_setting("default_exam_duration", cleaned["default_exam_duration"])
        self._upsert_setting("default_passing_score", cleaned["default_passing_score"])
        self._upsert_setting("require_fullscreen_default", cleaned["require_fullscreen_default"])
        self._upsert_setting("detect_tab_switch_default", cleaned["detect_tab_switch_default"])
        self._upsert_setting("max_violations_allowed_default", cleaned["max_violations_allowed_default"])

    def _save_notification_settings(self, form):
        cleaned = form.cleaned_data
        self._upsert_setting("notify_exam_published_email", cleaned["notify_exam_published_email"])
        self._upsert_setting("notify_exam_result_email", cleaned["notify_exam_result_email"])
        self._upsert_setting("notify_system_announcement", cleaned["notify_system_announcement"])
        self._upsert_setting("notify_daily_summary", cleaned["notify_daily_summary"])

    def _save_certificate_settings(self, form):
        cleaned = form.cleaned_data
        self._upsert_setting("certificate_number_prefix", cleaned["certificate_number_prefix"])
        self._upsert_setting("certificate_pdf_dpi", cleaned["certificate_pdf_dpi"])
        self._upsert_setting("certificate_storage_path", cleaned["certificate_storage_path"])
        self._upsert_setting("certificate_email_enabled", cleaned["certificate_email_enabled"])
        self._upsert_setting("certificate_verify_public", cleaned["certificate_verify_public"])
        invalidate_certificate_feature_cache()

    def _create_backup(self):
        settings_payload = []
        for setting in SystemSetting.objects.order_by("category", "setting_key"):
            settings_payload.append(
                {
                    "setting_key": setting.setting_key,
                    "setting_value": setting.setting_value,
                    "setting_type": setting.setting_type,
                    "category": setting.category,
                    "description": setting.description,
                    "is_public": setting.is_public,
                }
            )

        payload = {
            "generated_at": timezone.localtime().isoformat(),
            "generated_by": self.request.user.username,
            "settings_count": len(settings_payload),
            "settings": settings_payload,
        }

        filename = f"settings_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = _backup_dir() / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return filename, len(settings_payload)

    def _restore_backup(self, upload_file):
        try:
            payload = json.loads(upload_file.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("File backup tidak valid. Pastikan format JSON benar.") from exc

        items = payload.get("settings")
        if not isinstance(items, list):
            raise ValueError("Struktur backup tidak valid: field 'settings' harus berupa array.")

        restored = 0
        for item in items:
            key = item.get("setting_key")
            if not key:
                continue
            setting_type = item.get("setting_type", "string")
            setting_value = item.get("setting_value", "")
            category = item.get("category", "general")
            description = item.get("description", "")
            is_public = bool(item.get("is_public", False))
            SystemSetting.objects.update_or_create(
                setting_key=key,
                defaults={
                    "setting_value": str(setting_value),
                    "setting_type": setting_type,
                    "category": category,
                    "description": description,
                    "is_public": is_public,
                    "updated_by": self.request.user,
                },
            )
            restored += 1
        invalidate_branding_cache()
        invalidate_auth_feature_cache()
        invalidate_certificate_feature_cache()
        invalidate_student_session_timeout_cache()
        return restored

    def _backup_history(self):
        history = []
        for path in sorted(_backup_dir().glob("settings_backup_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            stat = path.stat()
            history.append(
                {
                    "filename": path.name,
                    "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.get_current_timezone()),
                    "size_kb": round(stat.st_size / 1024, 2),
                    "download_url": reverse("system_settings_backup_download", kwargs={"filename": path.name}),
                }
            )
        return history

    def _initial_data(self):
        setting_map = self._settings_map()
        return {
            "general": {
                "timezone": self._setting_value("timezone", setting_map),
                "language": self._setting_value("language", setting_map),
            },
            "branding": {
                "institution_name": self._setting_value("institution_name", setting_map),
                "institution_type": self._setting_value("institution_type", setting_map),
                "institution_address": self._setting_value("institution_address", setting_map),
                "institution_phone": self._setting_value("institution_phone", setting_map),
                "institution_email": self._setting_value("institution_email", setting_map),
                "institution_website": self._setting_value("institution_website", setting_map),
                "primary_color": self._setting_value("primary_color", setting_map),
                "login_page_headline": self._setting_value("login_page_headline", setting_map),
                "login_page_subheadline": self._setting_value("login_page_subheadline", setting_map),
                "landing_page_enabled": self._setting_value("landing_page_enabled", setting_map),
            },
            "branding_paths": {
                "institution_logo_url": self._setting_value("institution_logo_url", setting_map),
                "institution_logo_dark_url": self._setting_value("institution_logo_dark_url", setting_map),
                "institution_favicon_url": self._setting_value("institution_favicon_url", setting_map),
                "login_page_background_url": self._setting_value("login_page_background_url", setting_map),
            },
            "email": {
                "smtp_host": self._setting_value("smtp_host", setting_map),
                "smtp_port": self._setting_value("smtp_port", setting_map),
                "smtp_username": self._setting_value("smtp_username", setting_map),
                "smtp_password": self._setting_value("smtp_password", setting_map),
                "smtp_use_tls": self._setting_value("smtp_use_tls", setting_map),
                "default_from_email": self._setting_value("default_from_email", setting_map),
            },
            "security": {
                "password_min_length": self._setting_value("password_min_length", setting_map),
                "session_timeout_minutes": self._setting_value("session_timeout_minutes", setting_map),
                "max_login_attempts": self._setting_value("max_login_attempts", setting_map),
                "ip_whitelist": json.dumps(self._setting_value("ip_whitelist", setting_map)),
                "auth_enable_forgot_password": self._setting_value("auth_enable_forgot_password", setting_map),
                "auth_enable_password_reset": self._setting_value("auth_enable_password_reset", setting_map),
                "auth_enable_teacher_registration": self._setting_value("auth_enable_teacher_registration", setting_map),
                "auth_enable_student_registration": self._setting_value("auth_enable_student_registration", setting_map),
            },
            "exam_defaults": {
                "default_exam_duration": self._setting_value("default_exam_duration", setting_map),
                "default_passing_score": self._setting_value("default_passing_score", setting_map),
                "require_fullscreen_default": self._setting_value("require_fullscreen_default", setting_map),
                "detect_tab_switch_default": self._setting_value("detect_tab_switch_default", setting_map),
                "max_violations_allowed_default": self._setting_value("max_violations_allowed_default", setting_map),
            },
            "notifications": {
                "notify_exam_published_email": self._setting_value("notify_exam_published_email", setting_map),
                "notify_exam_result_email": self._setting_value("notify_exam_result_email", setting_map),
                "notify_system_announcement": self._setting_value("notify_system_announcement", setting_map),
                "notify_daily_summary": self._setting_value("notify_daily_summary", setting_map),
            },
            "certificates": {
                "certificate_number_prefix": self._setting_value("certificate_number_prefix", setting_map),
                "certificate_pdf_dpi": self._setting_value("certificate_pdf_dpi", setting_map),
                "certificate_storage_path": self._setting_value("certificate_storage_path", setting_map),
                "certificate_email_enabled": self._setting_value("certificate_email_enabled", setting_map),
                "certificate_verify_public": self._setting_value("certificate_verify_public", setting_map),
            },
        }

    def _storage_url(self, value):
        text = str(value or "").strip()
        if not text:
            return ""
        if text.startswith(("http://", "https://", "/", "data:")):
            return text
        try:
            return default_storage.url(text)
        except Exception:
            media_url = getattr(settings, "MEDIA_URL", "/media/")
            return f"{media_url.rstrip('/')}/{text.lstrip('/')}"

    def _build_forms(self, form_overrides=None):
        form_overrides = form_overrides or {}
        initial = self._initial_data()

        forms = {
            "general_form": form_overrides.get("general_form") or GeneralSettingsForm(initial=initial["general"]),
            "branding_form": form_overrides.get("branding_form") or BrandingSettingsForm(initial=initial["branding"]),
            "email_form": form_overrides.get("email_form") or EmailSettingsForm(initial=initial["email"]),
            "security_form": form_overrides.get("security_form") or SecuritySettingsForm(initial=initial["security"]),
            "exam_defaults_form": form_overrides.get("exam_defaults_form") or ExamDefaultsForm(initial=initial["exam_defaults"]),
            "notification_form": form_overrides.get("notification_form") or NotificationSettingsForm(initial=initial["notifications"]),
            "certificate_form": form_overrides.get("certificate_form") or CertificateSettingsForm(initial=initial["certificates"]),
            "backup_form": form_overrides.get("backup_form") or BackupRestoreForm(),
            "branding_logo_url": self._storage_url(initial["branding_paths"]["institution_logo_url"]),
            "branding_logo_dark_url": self._storage_url(initial["branding_paths"]["institution_logo_dark_url"]),
            "branding_favicon_url": self._storage_url(initial["branding_paths"]["institution_favicon_url"]),
            "branding_login_background_url": self._storage_url(initial["branding_paths"]["login_page_background_url"]),
            "branding_landing_enabled": bool(initial["branding"].get("landing_page_enabled", True)),
        }
        return forms

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "active_tab": kwargs.get("active_tab", self._get_active_tab()),
                "tabs": TAB_CHOICES,
                "backup_history": self._backup_history(),
                **self._build_forms(kwargs.get("form_overrides")),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "save_general":
            form = GeneralSettingsForm(request.POST)
            if form.is_valid():
                self._save_general_settings(form)
                messages.success(request, "Pengaturan umum berhasil disimpan.")
                return redirect(f"{reverse('system_settings')}?tab=general")
            return self.render_to_response(self.get_context_data(active_tab="general", form_overrides={"general_form": form}))

        if action == "save_branding":
            form = BrandingSettingsForm(request.POST, request.FILES)
            if form.is_valid():
                self._save_branding_settings(form)
                messages.success(request, "Pengaturan branding berhasil disimpan.")
                return redirect(f"{reverse('system_settings')}?tab=branding")
            return self.render_to_response(
                self.get_context_data(active_tab="branding", form_overrides={"branding_form": form})
            )

        if action == "reset_branding_defaults":
            self._reset_branding_defaults()
            messages.success(request, "Pengaturan branding dikembalikan ke default.")
            return redirect(f"{reverse('system_settings')}?tab=branding")

        if action == "save_email":
            form = EmailSettingsForm(request.POST)
            if form.is_valid():
                self._save_email_settings(form)
                messages.success(request, "Pengaturan email berhasil disimpan.")
                return redirect(f"{reverse('system_settings')}?tab=email")
            return self.render_to_response(self.get_context_data(active_tab="email", form_overrides={"email_form": form}))

        if action == "test_email":
            form = EmailSettingsForm(request.POST)
            if form.is_valid():
                try:
                    self._send_test_email(form)
                    messages.success(request, "Email test berhasil dikirim.")
                    return redirect(f"{reverse('system_settings')}?tab=email")
                except Exception as exc:
                    messages.error(request, f"Gagal kirim email test: {exc}")
            return self.render_to_response(self.get_context_data(active_tab="email", form_overrides={"email_form": form}))

        if action == "save_security":
            form = SecuritySettingsForm(request.POST)
            if form.is_valid():
                self._save_security_settings(form)
                messages.success(request, "Pengaturan keamanan berhasil disimpan.")
                return redirect(f"{reverse('system_settings')}?tab=security")
            return self.render_to_response(self.get_context_data(active_tab="security", form_overrides={"security_form": form}))

        if action == "save_exam_defaults":
            form = ExamDefaultsForm(request.POST)
            if form.is_valid():
                self._save_exam_defaults(form)
                messages.success(request, "Pengaturan default ujian berhasil disimpan.")
                return redirect(f"{reverse('system_settings')}?tab=exam_defaults")
            return self.render_to_response(
                self.get_context_data(active_tab="exam_defaults", form_overrides={"exam_defaults_form": form})
            )

        if action == "save_notifications":
            form = NotificationSettingsForm(request.POST)
            if form.is_valid():
                self._save_notification_settings(form)
                messages.success(request, "Preferensi notifikasi berhasil disimpan.")
                return redirect(f"{reverse('system_settings')}?tab=notifications")
            return self.render_to_response(
                self.get_context_data(active_tab="notifications", form_overrides={"notification_form": form})
            )

        if action == "save_certificates":
            form = CertificateSettingsForm(request.POST)
            if form.is_valid():
                self._save_certificate_settings(form)
                messages.success(request, "Pengaturan sertifikat berhasil disimpan.")
                return redirect(f"{reverse('system_settings')}?tab=certificates")
            return self.render_to_response(
                self.get_context_data(active_tab="certificates", form_overrides={"certificate_form": form})
            )

        if action == "create_backup":
            filename, total = self._create_backup()
            messages.success(request, f"Backup berhasil dibuat ({filename}) dengan {total} entri setting.")
            return redirect(f"{reverse('system_settings')}?tab=backup")

        if action == "restore_backup":
            form = BackupRestoreForm(request.POST, request.FILES)
            if form.is_valid() and form.cleaned_data.get("backup_file"):
                try:
                    restored_count = self._restore_backup(form.cleaned_data["backup_file"])
                    messages.success(request, f"Restore backup berhasil. {restored_count} setting diperbarui.")
                    return redirect(f"{reverse('system_settings')}?tab=backup")
                except ValueError as exc:
                    messages.error(request, str(exc))
            elif form.is_valid():
                form.add_error("backup_file", "Pilih file backup terlebih dahulu.")
            return self.render_to_response(self.get_context_data(active_tab="backup", form_overrides={"backup_form": form}))

        messages.warning(request, "Aksi tidak dikenali.")
        return redirect(reverse("system_settings"))


class SettingsBackupDownloadView(RoleRequiredMixin, View):
    required_role = "admin"

    def get(self, request, filename):
        safe_name = Path(filename).name
        file_path = (_backup_dir() / safe_name).resolve()
        backup_root = _backup_dir().resolve()
        if backup_root not in file_path.parents or not file_path.exists():
            raise Http404("File backup tidak ditemukan.")
        return FileResponse(file_path.open("rb"), as_attachment=True, filename=safe_name)


def permission_denied_view(request, exception=None):
    return render_error_page(request, 403)


def bad_request_view(request, exception=None):
    return render_error_page(request, 400)


def not_found_view(request, exception=None):
    return render_error_page(request, 404)


def server_error_view(request):
    return render_error_page(request, 500)
