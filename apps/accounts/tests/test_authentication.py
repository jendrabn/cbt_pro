from django.contrib.sessions.models import Session
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User


class AuthenticationFlowTests(TestCase):
    def create_user(self, username, email, role, password="Password123!"):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=role.title(),
            last_name="User",
            role=role,
            is_active=True,
        )

    def test_login_with_username_redirects_by_role(self):
        user = self.create_user("adminuser", "admin@example.com", "admin")
        response = self.client.post(
            reverse("login"),
            {"username": user.username, "password": "Password123!", "remember_me": "on"},
        )
        self.assertRedirects(response, reverse("admin_dashboard"))

    def test_login_with_email_redirects_by_role(self):
        user = self.create_user("teach1", "teacher@example.com", "teacher")
        response = self.client.post(
            reverse("login"),
            {"username": user.email, "password": "Password123!", "remember_me": "on"},
        )
        self.assertRedirects(response, reverse("teacher_dashboard"))

    def test_login_without_remember_me_sets_browser_length_session(self):
        user = self.create_user("stud1", "student@example.com", "student")
        response = self.client.post(
            reverse("login"),
            {"username": user.username, "password": "Password123!"},
        )
        self.assertRedirects(response, reverse("student_dashboard"))
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_invalid_credentials_show_error(self):
        self.create_user("wrong1", "wrong@example.com", "student")
        response = self.client.post(
            reverse("login"),
            {"username": "wrong1", "password": "invalid-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email/username atau password salah")

    def test_student_second_login_requires_manual_reset(self):
        user = self.create_user("single1", "single1@example.com", "student")
        first_client = Client()
        second_client = Client()

        first_response = first_client.post(
            reverse("login"),
            {"username": user.username, "password": "Password123!", "remember_me": "on"},
        )
        self.assertRedirects(first_response, reverse("student_dashboard"))

        second_response = second_client.post(
            reverse("login"),
            {"username": user.username, "password": "Password123!", "remember_me": "on"},
        )
        self.assertEqual(second_response.status_code, 200)
        self.assertContains(second_response, "sedang aktif di perangkat lain")

    def test_student_can_login_when_previous_session_record_is_stale(self):
        user = self.create_user("single2", "single2@example.com", "student")
        first_client = Client()
        second_client = Client()

        first_response = first_client.post(
            reverse("login"),
            {"username": user.username, "password": "Password123!", "remember_me": "on"},
        )
        self.assertRedirects(first_response, reverse("student_dashboard"))

        Session.objects.filter(session_key=first_client.session.session_key).delete()

        second_response = second_client.post(
            reverse("login"),
            {"username": user.username, "password": "Password123!", "remember_me": "on"},
        )
        self.assertRedirects(second_response, reverse("student_dashboard"))

    def test_logout_clears_session(self):
        user = self.create_user("logout1", "logout@example.com", "student")
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(
        DEMO_MODE=True,
        DEMO_TEACHER_USERNAME="guru.demo",
        DEMO_TEACHER_EMAIL="guru.demo@example.com",
        DEMO_TEACHER_PASSWORD="guru-demo-123",
        DEMO_STUDENT_USERNAME="siswa.demo",
        DEMO_STUDENT_EMAIL="siswa.demo@example.com",
        DEMO_STUDENT_PASSWORD="siswa-demo-123",
    )
    def test_login_page_shows_demo_credentials_when_enabled(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Akun Demo")
        self.assertContains(response, "guru.demo@example.com")
        self.assertContains(response, "siswa.demo@example.com")
        self.assertContains(response, "guru-demo-123")
        self.assertContains(response, "siswa-demo-123")

    @override_settings(
        DEMO_MODE=True,
        DEMO_TEACHER_USERNAME="guru.demo",
        DEMO_TEACHER_EMAIL="guru.demo@example.com",
        DEMO_STUDENT_USERNAME="siswa.demo",
        DEMO_STUDENT_EMAIL="siswa.demo@example.com",
    )
    def test_demo_teacher_cannot_open_profile_or_change_password(self):
        teacher = self.create_user("guru.demo", "guru.demo@example.com", "teacher")
        self.client.force_login(teacher)

        profile_response = self.client.get(reverse("profile"))
        password_response = self.client.get(reverse("change_password"))

        self.assertEqual(profile_response.status_code, 403)
        self.assertEqual(password_response.status_code, 403)
        self.assertContains(profile_response, "403 - Akses Ditolak", status_code=403)

    @override_settings(
        DEMO_MODE=True,
        DEMO_TEACHER_USERNAME="guru.demo",
        DEMO_TEACHER_EMAIL="guru.demo@example.com",
        DEMO_STUDENT_USERNAME="siswa.demo",
        DEMO_STUDENT_EMAIL="siswa.demo@example.com",
    )
    def test_demo_student_cannot_open_profile_or_change_password(self):
        student = self.create_user("siswa.demo", "siswa.demo@example.com", "student")
        self.client.force_login(student)

        profile_response = self.client.get(reverse("profile"))
        password_response = self.client.get(reverse("change_password"))

        self.assertEqual(profile_response.status_code, 403)
        self.assertEqual(password_response.status_code, 403)
