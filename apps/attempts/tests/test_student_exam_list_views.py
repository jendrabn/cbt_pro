from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.exams.models import Class, ClassStudent, Exam, ExamAssignment, ExamQuestion
from apps.questions.models import Question
from apps.subjects.models import Subject
from apps.results.models import ExamResult

from apps.attempts.models import ExamAttempt


class StudentExamListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_attempts",
            email="teacher.attempts@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Attempt",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_attempts",
            email="student.attempts@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Attempt",
            role="student",
            is_active=True,
        )
        cls.other_teacher = User.objects.create_user(
            username="teacher_other_attempts",
            email="teacher.other.attempts@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Lain",
            role="teacher",
            is_active=True,
        )

        subject = Subject.objects.create(name="Sejarah", code="SEJ", is_active=True)
        class_obj = Class.objects.create(name="XI IPS 2", is_active=True)
        ClassStudent.objects.create(class_obj=class_obj, student=cls.student)

        question = Question.objects.create(
            created_by=cls.teacher,
            subject=subject,
            question_type="multiple_choice",
            question_text="Perang Diponegoro terjadi pada tahun ...",
            points=10,
            is_active=True,
        )
        question.options.create(option_letter="A", option_text="1825", is_correct=True, display_order=1)
        question.options.create(option_letter="B", option_text="1945", is_correct=False, display_order=2)

        now = timezone.now()
        cls.upcoming_exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=subject,
            title="Ujian Sejarah Bab 1",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2),
            duration_minutes=90,
            passing_score=70,
            total_points=10,
            status="published",
        )
        cls.ongoing_exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=subject,
            title="Ujian Sejarah Bab 2",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            duration_minutes=60,
            passing_score=70,
            total_points=10,
            status="published",
        )
        cls.completed_exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=subject,
            title="Ujian Sejarah Bab 3",
            start_time=now - timedelta(days=3),
            end_time=now - timedelta(days=2, hours=22),
            duration_minutes=60,
            passing_score=70,
            total_points=10,
            status="completed",
        )
        cls.missed_exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=subject,
            title="Ujian Sejarah Bab 4",
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=2, hours=-1),
            duration_minutes=60,
            passing_score=70,
            total_points=10,
            status="published",
        )

        for exam in [cls.upcoming_exam, cls.ongoing_exam, cls.completed_exam, cls.missed_exam]:
            ExamQuestion.objects.create(exam=exam, question=question, display_order=1, points_override=10)

        ExamAssignment.objects.create(exam=cls.upcoming_exam, assigned_to_type="class", class_obj=class_obj)
        ExamAssignment.objects.create(exam=cls.ongoing_exam, assigned_to_type="student", student=cls.student)
        ExamAssignment.objects.create(exam=cls.completed_exam, assigned_to_type="student", student=cls.student)
        ExamAssignment.objects.create(exam=cls.missed_exam, assigned_to_type="class", class_obj=class_obj)

        completed_attempt = ExamAttempt.objects.create(
            exam=cls.completed_exam,
            student=cls.student,
            attempt_number=1,
            status="completed",
            start_time=now - timedelta(days=3),
            end_time=now - timedelta(days=2, hours=22),
            submit_time=now - timedelta(days=2, hours=22),
            total_score=8,
            percentage=80,
            passed=True,
            time_spent_seconds=2200,
        )
        ExamResult.objects.create(
            attempt=completed_attempt,
            exam=cls.completed_exam,
            student=cls.student,
            total_score=8,
            percentage=80,
            passed=True,
            total_questions=1,
            correct_answers=1,
            wrong_answers=0,
            unanswered=0,
            time_taken_seconds=2200,
            total_violations=0,
        )

    def test_student_can_access_exam_list(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_exam_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Daftar Ujian")

    def test_non_student_forbidden_exam_list(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse("student_exam_list"))
        self.assertEqual(response.status_code, 403)

    def test_default_tab_shows_upcoming_exam(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_exam_list"))
        self.assertContains(response, self.upcoming_exam.title)
        self.assertNotContains(response, self.ongoing_exam.title)

    def test_ongoing_tab_shows_ongoing_exam(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_exam_list"), data={"tab": "ongoing"})
        self.assertContains(response, self.ongoing_exam.title)
        self.assertNotContains(response, self.upcoming_exam.title)

    def test_completed_tab_shows_completed_exam(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_exam_list"), data={"tab": "completed"})
        self.assertContains(response, self.completed_exam.title)
        self.assertNotContains(response, self.ongoing_exam.title)

    def test_student_can_start_ongoing_exam(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("exam_start", kwargs={"exam_id": self.ongoing_exam.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("exam_room", kwargs={"exam_id": self.ongoing_exam.id}))
        self.assertTrue(
            ExamAttempt.objects.filter(exam=self.ongoing_exam, student=self.student, status="in_progress").exists()
        )

    def test_exam_start_page_includes_permission_preflight(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("exam_start", kwargs={"exam_id": self.ongoing_exam.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kamera dan mikrofon wajib diizinkan sebelum ujian dimulai")
        self.assertContains(response, "permissionPreflightModal")

    def test_exam_start_page_skips_permission_preflight_when_exam_does_not_require_it(self):
        self.ongoing_exam.require_fullscreen = False
        self.ongoing_exam.require_camera = False
        self.ongoing_exam.require_microphone = False
        self.ongoing_exam.enable_screenshot_proctoring = False
        self.ongoing_exam.save(
            update_fields=[
                "require_fullscreen",
                "require_camera",
                "require_microphone",
                "enable_screenshot_proctoring",
                "updated_at",
            ]
        )
        self.client.force_login(self.student)

        response = self.client.get(reverse("exam_start", kwargs={"exam_id": self.ongoing_exam.id}))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "permissionPreflightModal")
        self.assertContains(response, "Mulai Ujian")

    def test_student_cannot_start_upcoming_exam(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("exam_start", kwargs={"exam_id": self.upcoming_exam.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("student_exam_list"))
