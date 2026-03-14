import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

from django.conf import settings
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import path as url_path, reverse
from django.views import View

from apps.accounts.models import User
from apps.attempts.models import ExamViolation
from apps.core.enums import choice_dict, choice_label, get_enum_badge, get_enum_badge_tone
from apps.core.services import invalidate_branding_cache
from apps.exams.models import Exam
from apps.notifications.models import SystemSetting
from apps.questions.models import Question


def too_many_requests_view(request):
    return HttpResponse("Terlalu banyak permintaan.", status=429)


def crash_view(request):
    raise RuntimeError("boom")


class GetOnlyView(View):
    def get(self, request):
        return HttpResponse("OK")


urlpatterns = [
    url_path("return-429/", too_many_requests_view),
    url_path("crash/", crash_view),
    url_path("get-only/", GetOnlyView.as_view()),
]


class SystemSettingsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="admin_settings",
            email="admin.settings@cbt.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="Settings",
            role="admin",
            is_active=True,
            is_staff=True,
        )
        cls.teacher = User.objects.create_user(
            username="teacher_settings",
            email="teacher.settings@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Settings",
            role="teacher",
            is_active=True,
        )

    def setUp(self):
        self.temp_media_root = Path(settings.BASE_DIR) / "test_media" / f"cbt_media_test_{uuid4().hex}"
        self.temp_media_root.mkdir(parents=True, exist_ok=True)
        self.override = override_settings(MEDIA_ROOT=str(self.temp_media_root))
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.temp_media_root, ignore_errors=True)

    def test_admin_can_access_settings_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("system_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pengaturan Sistem")

    def test_non_admin_forbidden_access_settings_page(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("system_settings"))
        self.assertEqual(response.status_code, 403)

    def test_save_general_settings(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "save_general",
                "timezone": "Asia/Jakarta",
                "language": "id",
            },
        )
        self.assertEqual(response.status_code, 302)
        timezone_setting = SystemSetting.objects.get(setting_key="timezone")
        language_setting = SystemSetting.objects.get(setting_key="language")
        self.assertEqual(timezone_setting.setting_value, "Asia/Jakarta")
        self.assertEqual(language_setting.setting_value, "id")

    def test_save_branding_settings(self):
        self.client.force_login(self.admin)
        logo_file = SimpleUploadedFile(
            "logo.png",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0DIHDR",
            content_type="image/png",
        )
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "save_branding",
                "institution_name": "SMK Negeri 1",
                "institution_type": "SMK",
                "institution_address": "Jl. Pendidikan No. 1",
                "institution_phone": "08123456789",
                "institution_email": "info@smkn1.sch.id",
                "institution_website": "https://smkn1.sch.id",
                "primary_color": "#112233",
                "login_page_headline": "Selamat Datang di CBT SMK N 1",
                "login_page_subheadline": "Ujian cepat dan terukur",
                "landing_page_enabled": "on",
                "institution_logo_url": logo_file,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("?tab=branding", response.url)
        self.assertEqual(
            SystemSetting.objects.get(setting_key="institution_name").setting_value,
            "SMK Negeri 1",
        )
        self.assertTrue(
            SystemSetting.objects.get(setting_key="institution_logo_url").setting_value.startswith("branding/logo/")
        )

    def test_branding_tab_uses_file_input_groups_with_asset_links(self):
        SystemSetting.objects.update_or_create(
            setting_key="institution_logo_url",
            defaults={
                "setting_value": "branding/logo/logo.png",
                "setting_type": "string",
                "category": "branding",
            },
        )
        SystemSetting.objects.update_or_create(
            setting_key="institution_logo_dark_url",
            defaults={
                "setting_value": "branding/logo_dark/logo-dark.png",
                "setting_type": "string",
                "category": "branding",
            },
        )
        SystemSetting.objects.update_or_create(
            setting_key="institution_favicon_url",
            defaults={
                "setting_value": "branding/favicon/favicon.png",
                "setting_type": "string",
                "category": "branding",
            },
        )
        SystemSetting.objects.update_or_create(
            setting_key="login_page_background_url",
            defaults={
                "setting_value": "branding/login_bg/login-bg.png",
                "setting_type": "string",
                "category": "branding",
            },
        )

        self.client.force_login(self.admin)
        response = self.client.get(reverse("system_settings"), {"tab": "branding"})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "logo-preview")
        self.assertNotContains(response, "URL Aktif")
        self.assertContains(response, 'class="input-group"', html=False)
        self.assertContains(response, 'title="Buka logo utama asli"')
        self.assertContains(response, 'title="Buka logo dark asli"')
        self.assertContains(response, 'title="Buka favicon asli"')
        self.assertContains(response, 'title="Buka background login asli"')
        self.assertContains(response, '/media/branding/logo/logo.png')
        self.assertContains(response, '/media/branding/logo_dark/logo-dark.png')
        self.assertContains(response, '/media/branding/favicon/favicon.png')
        self.assertContains(response, '/media/branding/login_bg/login-bg.png')

    def test_branding_tab_uses_hex_input_for_theme_color(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("system_settings"), {"tab": "branding"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="primary_color"', html=False)
        self.assertContains(response, 'placeholder="#0d6efd"', html=False)
        self.assertContains(response, 'aria-describedby="primaryColorHelp"', html=False)
        self.assertContains(response, 'id="primaryColorHelp"', html=False)
        self.assertContains(response, 'class="form-text"', html=False)
        self.assertContains(response, "Gunakan format HEX, contoh: #0d6efd.")
        self.assertNotContains(response, 'type="color"', html=False)
        self.assertNotContains(response, "primaryColorPreview")
        self.assertNotContains(response, "text-muted d-block")

    def test_create_backup_file(self):
        SystemSetting.objects.update_or_create(
            setting_key="timezone",
            defaults={
                "setting_value": "Asia/Jakarta",
                "setting_type": "string",
                "category": "general",
            },
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse("system_settings"), data={"action": "create_backup"})
        self.assertEqual(response.status_code, 302)

        backup_dir = Path(self.temp_media_root) / "backups" / "system_settings"
        files = list(backup_dir.glob("settings_backup_*.json"))
        self.assertTrue(files, "File backup tidak dibuat.")

        payload = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertIn("settings", payload)
        self.assertGreaterEqual(len(payload["settings"]), 1)

    def test_save_security_toggles(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "save_security",
                "password_min_length": 9,
                "session_timeout_minutes": 90,
                "max_login_attempts": 7,
                "ip_whitelist": "[]",
                "auth_enable_forgot_password": "on",
                "auth_enable_password_reset": "on",
                "auth_enable_teacher_registration": "",
                "auth_enable_student_registration": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SystemSetting.objects.get(setting_key="auth_enable_forgot_password").get_value())
        self.assertTrue(SystemSetting.objects.get(setting_key="auth_enable_password_reset").get_value())
        self.assertFalse(SystemSetting.objects.get(setting_key="auth_enable_teacher_registration").get_value())
        self.assertTrue(SystemSetting.objects.get(setting_key="auth_enable_student_registration").get_value())

    def test_save_branding_supports_all_upload_fields(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "save_branding",
                "institution_logo_url": SimpleUploadedFile("logo.png", b"logo", content_type="image/png"),
                "institution_logo_dark_url": SimpleUploadedFile("logo-dark.svg", b"dark", content_type="image/svg+xml"),
                "institution_favicon_url": SimpleUploadedFile("favicon.ico", b"ico", content_type="image/x-icon"),
                "login_page_background_url": SimpleUploadedFile("bg.jpg", b"bg", content_type="image/jpeg"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SystemSetting.objects.get(setting_key="institution_logo_url").setting_value.startswith("branding/logo/")
        )
        self.assertTrue(
            SystemSetting.objects.get(setting_key="institution_logo_dark_url").setting_value.startswith(
                "branding/logo_dark/"
            )
        )
        self.assertTrue(
            SystemSetting.objects.get(setting_key="institution_favicon_url").setting_value.startswith(
                "branding/favicon/"
            )
        )
        self.assertTrue(
            SystemSetting.objects.get(setting_key="login_page_background_url").setting_value.startswith(
                "branding/login_bg/"
            )
        )

    def test_branding_rejects_invalid_upload_extension(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "save_branding",
                "institution_logo_url": SimpleUploadedFile("logo.txt", b"not-image", content_type="text/plain"),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Logo utama: format file tidak valid")
        self.assertFalse(SystemSetting.objects.filter(setting_key="institution_logo_url").exists())

    def test_save_email_keeps_existing_password_when_blank(self):
        self.client.force_login(self.admin)
        SystemSetting.objects.update_or_create(
            setting_key="smtp_password",
            defaults={
                "setting_value": "existing-secret",
                "setting_type": "string",
                "category": "email",
            },
        )
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "save_email",
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "smtp_username": "mailer",
                "smtp_password": "",
                "default_from_email": "no-reply@example.com",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SystemSetting.objects.get(setting_key="smtp_password").setting_value, "existing-secret")
        self.assertFalse(SystemSetting.objects.get(setting_key="smtp_use_tls").get_value())

    @patch("apps.core.views.send_mail")
    @patch("apps.core.views.get_connection")
    def test_test_email_uses_submitted_configuration(self, mock_get_connection, mock_send_mail):
        self.client.force_login(self.admin)
        fake_connection = Mock()
        mock_get_connection.return_value = fake_connection

        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "test_email",
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "smtp_username": "mailer",
                "smtp_password": "secret",
                "smtp_use_tls": "on",
                "default_from_email": "no-reply@example.com",
                "test_email_recipient": "receiver@example.com",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("?tab=email", response.url)
        mock_get_connection.assert_called_once_with(
            host="smtp.example.com",
            port=587,
            username="mailer",
            password="secret",
            use_tls=True,
            fail_silently=False,
        )
        mock_send_mail.assert_called_once()

    def test_save_exam_defaults_checkboxes_and_values(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "save_exam_defaults",
                "default_exam_duration": 75,
                "default_passing_score": "82.5",
                "require_fullscreen_default": "on",
                "max_violations_allowed_default": 4,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SystemSetting.objects.get(setting_key="default_exam_duration").get_value(), 75)
        self.assertEqual(SystemSetting.objects.get(setting_key="default_passing_score").get_value(), 82.5)
        self.assertTrue(SystemSetting.objects.get(setting_key="require_fullscreen_default").get_value())
        self.assertFalse(SystemSetting.objects.get(setting_key="detect_tab_switch_default").get_value())

    def test_save_notification_checkboxes(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "save_notifications",
                "notify_exam_published_email": "on",
                "notify_daily_summary": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SystemSetting.objects.get(setting_key="notify_exam_published_email").get_value())
        self.assertFalse(SystemSetting.objects.get(setting_key="notify_exam_result_email").get_value())
        self.assertFalse(SystemSetting.objects.get(setting_key="notify_system_announcement").get_value())
        self.assertTrue(SystemSetting.objects.get(setting_key="notify_daily_summary").get_value())

    def test_save_certificate_settings_toggles(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "save_certificates",
                "certificate_number_prefix": "acme",
                "certificate_pdf_dpi": 200,
                "certificate_storage_path": "my-certs",
                "certificate_verify_public": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SystemSetting.objects.get(setting_key="certificate_number_prefix").setting_value, "ACME")
        self.assertEqual(SystemSetting.objects.get(setting_key="certificate_pdf_dpi").get_value(), 200)
        self.assertEqual(SystemSetting.objects.get(setting_key="certificate_storage_path").setting_value, "my-certs/")
        self.assertFalse(SystemSetting.objects.get(setting_key="certificate_email_enabled").get_value())
        self.assertTrue(SystemSetting.objects.get(setting_key="certificate_verify_public").get_value())

    def test_restore_backup_updates_settings(self):
        self.client.force_login(self.admin)
        backup_file = SimpleUploadedFile(
            "settings_backup_test.json",
            json.dumps(
                {
                    "settings": [
                        {
                            "setting_key": "timezone",
                            "setting_value": "UTC",
                            "setting_type": "string",
                            "category": "general",
                            "description": "Zona waktu aplikasi",
                            "is_public": True,
                        },
                        {
                            "setting_key": "landing_page_enabled",
                            "setting_value": "false",
                            "setting_type": "boolean",
                            "category": "general",
                            "description": "Aktifkan landing page pada URL root",
                            "is_public": False,
                        },
                    ]
                }
            ).encode("utf-8"),
            content_type="application/json",
        )
        response = self.client.post(
            reverse("system_settings"),
            data={
                "action": "restore_backup",
                "backup_file": backup_file,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(SystemSetting.objects.get(setting_key="timezone").setting_value, "UTC")
        self.assertFalse(SystemSetting.objects.get(setting_key="landing_page_enabled").get_value())

    def test_landing_redirects_to_login_when_disabled(self):
        SystemSetting.objects.update_or_create(
            setting_key="landing_page_enabled",
            defaults={
                "setting_value": "false",
                "setting_type": "boolean",
                "category": "general",
            },
        )
        invalidate_branding_cache()
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))


class ErrorPageMiddlewareTests(TestCase):
    @override_settings(DEBUG=True)
    def test_unknown_route_uses_custom_404_page_in_debug(self):
        response = self.client.get("/student/dashboard/sss")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "404 - Halaman Tidak Ditemukan", status_code=404)

    @override_settings(DEBUG=True, ROOT_URLCONF="apps.core.tests")
    def test_generic_4xx_response_uses_family_template(self):
        response = self.client.get("/return-429/")
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "429 - Permintaan Tidak Dapat Diproses", status_code=429)

    @override_settings(DEBUG=True, ROOT_URLCONF="apps.core.tests")
    def test_method_not_allowed_uses_family_template(self):
        response = self.client.post("/get-only/")
        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "405 - Permintaan Tidak Dapat Diproses", status_code=405)

    @override_settings(DEBUG=True, ROOT_URLCONF="apps.core.tests")
    def test_unhandled_exception_uses_custom_500_page(self):
        client = self.client_class(raise_request_exception=False)
        response = client.get("/crash/")
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "500 - Terjadi Gangguan Server", status_code=500)


class MediaServingTests(TestCase):
    def test_media_file_served_when_django_media_serving_enabled(self):
        target = Path(settings.MEDIA_ROOT) / "branding" / "logo" / "media-serving-test.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ok", encoding="utf-8")

        response = None
        try:
            response = self.client.get("/media/branding/logo/media-serving-test.txt")
            self.assertEqual(response.status_code, 200)
            body = b"".join(response.streaming_content)
            self.assertEqual(body, b"ok")
        finally:
            if response is not None:
                response.close()
            target.unlink(missing_ok=True)


class EnumBadgeHelpersTests(TestCase):
    def test_choice_helpers_follow_textchoices_labels(self):
        self.assertEqual(choice_label(Exam.Status, Exam.Status.ONGOING), "Berlangsung")
        self.assertEqual(choice_dict(Question.QuestionType)["essay"], "Esai")

    def test_enum_badge_registry_maps_soft_tones(self):
        self.assertEqual(get_enum_badge_tone("question_difficulty", Question.Difficulty.HARD), "danger")
        self.assertEqual(get_enum_badge_tone("violation_severity", ExamViolation.Severity.CRITICAL), "danger")
        self.assertEqual(
            get_enum_badge("exam_status", Exam.Status.CANCELLED),
            {"label": "Dibatalkan", "tone": "danger"},
        )

    def test_template_tags_render_soft_badges(self):
        rendered = Template(
            "{% load cbt_extras %}{% enum_badge 'exam_status' 'cancelled' %} {% soft_badge 'Aktif' 'success' %}"
        ).render(Context())

        self.assertIn("cbt-status-badge is-danger", rendered)
        self.assertIn("Dibatalkan", rendered)
        self.assertIn("cbt-status-badge is-success", rendered)
        self.assertIn("Aktif", rendered)


class SeedCommandTests(TestCase):
    def test_seed_creates_expected_question_bank_and_exams_for_each_teacher(self):
        call_command("seed")
        call_command("seed")

        expected_types = [
            Question.QuestionType.MULTIPLE_CHOICE,
            Question.QuestionType.CHECKBOX,
            Question.QuestionType.ORDERING,
            Question.QuestionType.MATCHING,
            Question.QuestionType.FILL_IN_BLANK,
            Question.QuestionType.ESSAY,
            Question.QuestionType.SHORT_ANSWER,
        ]

        subjects_per_teacher = 10
        teachers_count = 3
        expected_per_type = subjects_per_teacher * teachers_count * 5

        for question_type in expected_types:
            with self.subTest(question_type=question_type):
                self.assertEqual(
                    Question.objects.filter(question_type=question_type, is_deleted=False).count(),
                    expected_per_type,
                )

        self.assertEqual(
            Question.objects.filter(is_deleted=False).count(),
            subjects_per_teacher * teachers_count * len(expected_types) * 5,
        )
        self.assertEqual(Exam.objects.filter(is_deleted=False).count(), subjects_per_teacher * teachers_count)

        sample_exam = Exam.objects.filter(is_deleted=False).order_by("title").first()
        self.assertIsNotNone(sample_exam)
        self.assertEqual(sample_exam.exam_questions.count(), 35)
        self.assertTrue(sample_exam.allow_retake)
        self.assertEqual(sample_exam.max_retake_attempts, 10)
        self.assertFalse(sample_exam.require_fullscreen)
        self.assertFalse(sample_exam.require_camera)
        self.assertFalse(sample_exam.require_microphone)
        self.assertFalse(sample_exam.detect_tab_switch)
        self.assertFalse(sample_exam.disable_right_click)
        self.assertFalse(sample_exam.enable_screenshot_proctoring)
