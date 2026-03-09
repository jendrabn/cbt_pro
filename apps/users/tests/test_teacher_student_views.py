from datetime import timedelta

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, UserProfile
from apps.attempts.models import ExamAttempt
from apps.exams.models import Class, ClassStudent, Exam, ExamAssignment
from apps.results.models import ExamResult
from apps.subjects.models import Subject


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class TeacherStudentViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_students",
            email="teacher.students@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Pembina",
            role="teacher",
            is_active=True,
        )
        cls.other_teacher = User.objects.create_user(
            username="teacher_other_students",
            email="teacher.other.students@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Lain",
            role="teacher",
            is_active=True,
        )
        cls.admin = User.objects.create_user(
            username="admin_students",
            email="admin.students@cbt.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="Satu",
            role="admin",
            is_active=True,
            is_staff=True,
        )
        cls.student_class = User.objects.create_user(
            username="student_class_view",
            email="student.class.view@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Kelas",
            role="student",
            is_active=True,
        )
        cls.student_direct = User.objects.create_user(
            username="student_direct_view",
            email="student.direct.view@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Direct",
            role="student",
            is_active=False,
        )
        cls.student_other = User.objects.create_user(
            username="student_other_view",
            email="student.other.view@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Lain",
            role="student",
            is_active=True,
        )

        UserProfile.objects.create(user=cls.student_class, student_id="NIS-1001", class_grade="XII IPA 1")
        UserProfile.objects.create(user=cls.student_direct, student_id="NIS-1002", class_grade="XII IPA 2")
        UserProfile.objects.create(user=cls.student_other, student_id="NIS-1003", class_grade="XII IPA 3")

        cls.subject = Subject.objects.create(name="Matematika", code="MAT", is_active=True)
        cls.class_obj = Class.objects.create(name="XII IPA 1", grade_level="XII", academic_year="2025/2026", is_active=True)
        cls.other_class = Class.objects.create(name="XII IPA 3", grade_level="XII", academic_year="2025/2026", is_active=True)
        ClassStudent.objects.create(class_obj=cls.class_obj, student=cls.student_class)
        ClassStudent.objects.create(class_obj=cls.other_class, student=cls.student_other)

        now = timezone.now()
        cls.exam_class = Exam.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            title="Ujian Kelas Matematika",
            start_time=now - timedelta(days=2),
            end_time=now + timedelta(days=1),
            duration_minutes=90,
            passing_score=70,
            total_points=100,
            status="completed",
        )
        cls.exam_direct = Exam.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            title="Ujian Remedial Direct",
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=2),
            duration_minutes=60,
            passing_score=70,
            total_points=100,
            status="published",
        )
        cls.exam_other_teacher = Exam.objects.create(
            created_by=cls.other_teacher,
            subject=cls.subject,
            title="Ujian Guru Lain",
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=2),
            duration_minutes=60,
            passing_score=70,
            total_points=100,
            status="published",
        )

        ExamAssignment.objects.create(exam=cls.exam_class, assigned_to_type="class", class_obj=cls.class_obj)
        ExamAssignment.objects.create(exam=cls.exam_direct, assigned_to_type="student", student=cls.student_direct)
        ExamAssignment.objects.create(exam=cls.exam_other_teacher, assigned_to_type="student", student=cls.student_other)

        cls.attempt_class = ExamAttempt.objects.create(
            exam=cls.exam_class,
            student=cls.student_class,
            attempt_number=1,
            status="completed",
            start_time=now - timedelta(hours=3),
            end_time=now - timedelta(hours=2),
            submit_time=now - timedelta(hours=2),
            total_score=82,
            percentage=82,
            passed=True,
            time_spent_seconds=3200,
        )
        cls.attempt_direct = ExamAttempt.objects.create(
            exam=cls.exam_direct,
            student=cls.student_direct,
            attempt_number=1,
            status="submitted",
            start_time=now - timedelta(hours=5),
            end_time=now - timedelta(hours=4),
            submit_time=now - timedelta(hours=4),
            total_score=68,
            percentage=68,
            passed=False,
            time_spent_seconds=2800,
        )

        ExamResult.objects.create(
            attempt=cls.attempt_class,
            exam=cls.exam_class,
            student=cls.student_class,
            total_score=82,
            percentage=82,
            passed=True,
            total_questions=40,
            correct_answers=33,
            wrong_answers=7,
            unanswered=0,
            time_taken_seconds=3200,
            total_violations=0,
        )
        ExamResult.objects.create(
            attempt=cls.attempt_direct,
            exam=cls.exam_direct,
            student=cls.student_direct,
            total_score=68,
            percentage=68,
            passed=False,
            total_questions=40,
            correct_answers=27,
            wrong_answers=13,
            unanswered=0,
            time_taken_seconds=2800,
            total_violations=0,
        )

    def test_teacher_can_access_related_student_list_only(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("teacher_student_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Data Siswa")
        self.assertContains(response, self.student_class.get_full_name())
        self.assertContains(response, self.student_direct.get_full_name())
        self.assertNotContains(response, self.student_other.get_full_name())

    def test_teacher_can_filter_students_by_related_class(self):
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse("teacher_student_list"),
            data={"class_id": str(self.class_obj.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student_class.get_full_name())
        self.assertNotContains(response, self.student_direct.get_full_name())

    def test_teacher_can_open_related_student_detail(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("teacher_student_detail", kwargs={"pk": self.student_class.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student_class.get_full_name())
        self.assertContains(response, self.exam_class.title)
        self.assertContains(response, "Riwayat Attempt")

    def test_teacher_cannot_open_unrelated_student_detail(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("teacher_student_detail", kwargs={"pk": self.student_other.id}))
        self.assertEqual(response.status_code, 404)

    def test_non_teacher_forbidden_from_teacher_student_pages(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("teacher_student_list"))
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_reset_related_student_session(self):
        student_client = Client()
        login_response = student_client.post(
            reverse("login"),
            {"username": self.student_class.username, "password": "StudentPass123!", "remember_me": "on"},
        )
        self.assertRedirects(login_response, reverse("student_dashboard"))

        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("teacher_student_reset_session", kwargs={"pk": self.student_class.pk}),
            data={"next": reverse("teacher_student_detail", kwargs={"pk": self.student_class.pk})},
        )
        self.assertEqual(response.status_code, 302)

        follow_up = student_client.get(reverse("student_dashboard"))
        self.assertEqual(follow_up.status_code, 302)
        self.assertTrue(follow_up.url.startswith(reverse("login")))

    def test_teacher_cannot_reset_unrelated_student_session(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("teacher_student_reset_session", kwargs={"pk": self.student_other.pk}),
        )
        self.assertEqual(response.status_code, 404)
