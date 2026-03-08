import json
import os
import re
from zoneinfo import available_timezones

from django import forms


LANGUAGE_CHOICES = [
    ("id", "Bahasa Indonesia"),
    ("en", "English"),
]


def _timezone_choices():
    preferred = ["Asia/Jakarta", "Asia/Makassar", "Asia/Jayapura", "UTC"]
    all_timezones = sorted(available_timezones())
    options = [(tz, tz) for tz in preferred if tz in all_timezones]
    options.extend((tz, tz) for tz in all_timezones if tz not in preferred)
    return options


class SettingsForm(forms.Form):
    """Base form for system settings sections."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.RadioSelect):
                continue
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs["class"] = "form-control"
            else:
                field.widget.attrs["class"] = "form-control"


class GeneralSettingsForm(SettingsForm):
    timezone = forms.ChoiceField(label="Zona Waktu", choices=_timezone_choices())
    language = forms.ChoiceField(label="Bahasa", choices=LANGUAGE_CHOICES)


class BrandingSettingsForm(SettingsForm):
    institution_name = forms.CharField(label="Nama Lembaga", max_length=255, required=False)
    institution_type = forms.CharField(label="Jenis Lembaga", max_length=100, required=False)
    institution_address = forms.CharField(
        label="Alamat Lembaga",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    institution_phone = forms.CharField(label="Telepon / WhatsApp", max_length=50, required=False)
    institution_email = forms.EmailField(label="Email Lembaga", required=False)
    institution_website = forms.URLField(label="Website Lembaga", required=False)

    institution_logo_url = forms.FileField(label="Logo Utama", required=False)
    institution_logo_dark_url = forms.FileField(label="Logo Dark", required=False)
    institution_favicon_url = forms.FileField(label="Favicon", required=False)

    primary_color = forms.CharField(label="Primary Color (HEX)", max_length=7, required=False)

    login_page_headline = forms.CharField(label="Headline Halaman Login", max_length=255, required=False)
    login_page_subheadline = forms.CharField(label="Subheadline Halaman Login", max_length=255, required=False)
    login_page_background_url = forms.FileField(label="Background Login", required=False)

    landing_page_enabled = forms.BooleanField(label="Aktifkan Landing Page", required=False)

    LOGO_EXTENSIONS = {"png", "jpg", "jpeg", "svg"}
    FAVICON_EXTENSIONS = {"ico", "png"}
    LOGIN_BG_EXTENSIONS = {"png", "jpg", "jpeg"}
    HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

    def clean_primary_color(self):
        value = (self.cleaned_data.get("primary_color") or "").strip()
        if not value:
            return "#0d6efd"
        if not self.HEX_COLOR_PATTERN.match(value):
            raise forms.ValidationError("Format warna harus HEX, contoh: #0d6efd")
        return value

    def clean_institution_logo_url(self):
        return self._validate_upload(
            field_name="institution_logo_url",
            allowed_ext=self.LOGO_EXTENSIONS,
            max_size_bytes=2 * 1024 * 1024,
            label="Logo utama",
        )

    def clean_institution_logo_dark_url(self):
        return self._validate_upload(
            field_name="institution_logo_dark_url",
            allowed_ext=self.LOGO_EXTENSIONS,
            max_size_bytes=2 * 1024 * 1024,
            label="Logo dark",
        )

    def clean_institution_favicon_url(self):
        return self._validate_upload(
            field_name="institution_favicon_url",
            allowed_ext=self.FAVICON_EXTENSIONS,
            max_size_bytes=512 * 1024,
            label="Favicon",
        )

    def clean_login_page_background_url(self):
        return self._validate_upload(
            field_name="login_page_background_url",
            allowed_ext=self.LOGIN_BG_EXTENSIONS,
            max_size_bytes=5 * 1024 * 1024,
            label="Background login",
        )

    def _validate_upload(self, *, field_name, allowed_ext, max_size_bytes, label):
        file_obj = self.cleaned_data.get(field_name)
        if not file_obj:
            return file_obj

        filename = str(getattr(file_obj, "name", "") or "")
        extension = os.path.splitext(filename)[1].replace(".", "").lower()
        if extension not in allowed_ext:
            formatted = ", ".join(sorted(allowed_ext))
            raise forms.ValidationError(
                f"{label}: format file tidak valid. Gunakan salah satu: {formatted}."
            )

        file_size = int(getattr(file_obj, "size", 0) or 0)
        if file_size > max_size_bytes:
            max_mb = round(max_size_bytes / (1024 * 1024), 2)
            raise forms.ValidationError(f"{label}: ukuran file maksimum {max_mb} MB.")
        return file_obj


class EmailSettingsForm(SettingsForm):
    smtp_host = forms.CharField(label="SMTP Host", max_length=200)
    smtp_port = forms.IntegerField(label="SMTP Port", min_value=1, max_value=65535)
    smtp_username = forms.CharField(label="SMTP Username", max_length=255, required=False)
    smtp_password = forms.CharField(
        label="SMTP Password",
        required=False,
        widget=forms.PasswordInput(render_value=True),
    )
    smtp_use_tls = forms.BooleanField(label="Gunakan TLS", required=False)
    default_from_email = forms.EmailField(label="Email Pengirim Default")
    test_email_recipient = forms.EmailField(label="Email Tujuan Test", required=False)


class SecuritySettingsForm(SettingsForm):
    password_min_length = forms.IntegerField(label="Minimal Panjang Password", min_value=6, max_value=128)
    session_timeout_minutes = forms.IntegerField(label="Session Timeout (menit)", min_value=5, max_value=1440)
    max_login_attempts = forms.IntegerField(label="Maksimal Percobaan Login", min_value=1, max_value=50)
    ip_whitelist = forms.CharField(
        label="IP Whitelist (JSON array)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": '["127.0.0.1", "192.168.1.10"]'}),
    )
    auth_enable_forgot_password = forms.BooleanField(
        label="Aktifkan fitur lupa password",
        required=False,
    )
    auth_enable_password_reset = forms.BooleanField(
        label="Aktifkan konfirmasi reset password",
        required=False,
    )
    auth_enable_teacher_registration = forms.BooleanField(
        label="Aktifkan pendaftaran Guru",
        required=False,
    )
    auth_enable_student_registration = forms.BooleanField(
        label="Aktifkan pendaftaran Siswa",
        required=False,
    )

    def clean_ip_whitelist(self):
        value = self.cleaned_data.get("ip_whitelist", "").strip()
        if not value:
            return "[]"
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError("Format JSON whitelist tidak valid.") from exc
        if not isinstance(parsed, list):
            raise forms.ValidationError("IP whitelist harus berupa array JSON.")
        return json.dumps(parsed)


class ExamDefaultsForm(SettingsForm):
    default_exam_duration = forms.IntegerField(label="Durasi Ujian Default (menit)", min_value=5, max_value=600)
    default_passing_score = forms.DecimalField(
        label="Nilai Kelulusan Default",
        min_value=0,
        max_value=100,
        max_digits=5,
        decimal_places=2,
    )
    require_fullscreen_default = forms.BooleanField(label="Wajib Fullscreen", required=False)
    detect_tab_switch_default = forms.BooleanField(label="Deteksi Pindah Tab", required=False)
    max_violations_allowed_default = forms.IntegerField(
        label="Maksimal Pelanggaran",
        min_value=1,
        max_value=20,
    )


class NotificationSettingsForm(SettingsForm):
    notify_exam_published_email = forms.BooleanField(label="Email saat ujian dipublikasikan", required=False)
    notify_exam_result_email = forms.BooleanField(label="Email saat hasil ujian tersedia", required=False)
    notify_system_announcement = forms.BooleanField(label="Notifikasi pengumuman sistem", required=False)
    notify_daily_summary = forms.BooleanField(label="Ringkasan harian via email", required=False)


class BackupRestoreForm(SettingsForm):
    backup_file = forms.FileField(label="File Backup", required=False)
