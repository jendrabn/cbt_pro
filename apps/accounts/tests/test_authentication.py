from django.test import TestCase
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

    def test_logout_clears_session(self):
        user = self.create_user("logout1", "logout@example.com", "student")
        self.client.force_login(user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
