import json
import shutil
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings
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


class ErrorPageMiddlewareTests(SimpleTestCase):
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
