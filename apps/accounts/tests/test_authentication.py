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

    def test_login_page_does_not_show_has_validation_class_without_errors(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "has-validation")

    def test_empty_login_submission_marks_input_groups_invalid(self):
        response = self.client.post(reverse("login"), {"username": "", "password": ""})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has-validation is-invalid-group", count=2)
        self.assertContains(response, 'aria-describedby="id_username_feedback"', html=False)
        self.assertContains(response, 'aria-describedby="id_password_feedback"', html=False)

    def test_forgot_password_page_does_not_show_has_validation_class_without_errors(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "has-validation")

    def test_forgot_password_invalid_submission_marks_input_group_invalid(self):
        response = self.client.post(reverse("password_reset"), {"email": ""})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "has-validation is-invalid-group")
        self.assertContains(response, 'aria-describedby="id_email_feedback"', html=False)

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

    def test_profile_invalid_submission_marks_rendered_fields_invalid(self):
        user = self.create_user("profile1", "profile1@example.com", "teacher")
        self.client.force_login(user)

        response = self.client.post(
            reverse("profile"),
            {
                "first_name": "",
                "last_name": "User",
                "email": "not-an-email",
                "phone_number": "",
                "bio": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="id_first_name_feedback"', html=False)
        self.assertContains(response, 'id="id_email_feedback"', html=False)
        self.assertContains(response, "form-control is-invalid", count=2)

    def test_change_password_invalid_submission_marks_rendered_fields_invalid(self):
        user = self.create_user("changepass1", "changepass1@example.com", "teacher")
        self.client.force_login(user)

        response = self.client.post(
            reverse("change_password"),
            {"old_password": "", "new_password1": "", "new_password2": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="id_old_password_feedback"', html=False)
        self.assertContains(response, 'id="id_new_password1_feedback"', html=False)
        self.assertContains(response, 'id="id_new_password2_feedback"', html=False)
        self.assertContains(response, "form-control is-invalid", count=3)

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
        self.assertContains(response, "Username: guru.demo")
        self.assertContains(response, "Username: siswa.demo")
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
