import json
import shutil
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.attempts.models import ExamViolation
from apps.core.enums import choice_dict, choice_label, get_enum_badge, get_enum_badge_tone
from apps.core.services import invalidate_branding_cache
from apps.exams.models import Exam
from apps.notifications.models import SystemSetting
from apps.questions.models import Question


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
