from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class DashboardRoleAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="admin_role_test",
            email="admin.role@test.com",
            password="Password123!",
            first_name="Admin",
            last_name="Test",
            role="admin",
            is_active=True,
        )
        cls.teacher = User.objects.create_user(
            username="teacher_role_test",
            email="teacher.role@test.com",
            password="Password123!",
            first_name="Guru",
            last_name="Test",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_role_test",
            email="student.role@test.com",
            password="Password123!",
            first_name="Siswa",
            last_name="Test",
            role="student",
            is_active=True,
        )

    def test_admin_dashboard_can_be_accessed_by_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_forbidden_for_teacher(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "403 - Akses Ditolak", status_code=403)

    def test_teacher_dashboard_forbidden_for_student(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("teacher_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    @override_settings(DEMO_MODE=True)
    def test_landing_uses_demo_label_when_demo_mode_enabled(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo")
