from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attempts.models import ExamAttempt, ExamViolation, ProctoringScreenshot, StudentAnswer
from apps.exams.models import Exam, ExamAssignment, ExamQuestion
from apps.questions.models import Question
from apps.results.models import ExamResult
from apps.subjects.models import Subject


class SubjectManagementViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="admin_subject",
            email="admin.subject@cbt.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="Subject",
            role="admin",
            is_active=True,
            is_staff=True,
        )
        cls.teacher = User.objects.create_user(
            username="teacher_subject",
            email="teacher.subject@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Subject",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_subject",
            email="student.subject@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Subject",
            role="student",
            is_active=True,
        )

    def test_admin_can_access_subject_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("subject_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manajemen Mata Pelajaran")

    def test_non_admin_forbidden_subject_list(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("subject_list"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_subject(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("subject_create"),
            data={
                "name": "Matematika",
                "code": "mtk",
                "description": "Pelajaran Matematika",
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Subject.objects.get(name="Matematika")
        self.assertEqual(created.code, "MTK")

    def test_delete_requires_exact_confirmation(self):
        subject = Subject.objects.create(name="Kimia", code="KIM")
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("subject_delete", kwargs={"pk": subject.pk}),
            data={"confirm_name": "kimia"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Subject.objects.filter(id=subject.id).exists())

    def test_subject_api_returns_subjects_for_teacher(self):
        Subject.objects.create(name="Fisika", code="FIS")
        Subject.objects.create(name="Sejarah", code="SEJ")

        self.client.force_login(self.teacher)
        response = self.client.get(reverse("subject_api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        names = [item["name"] for item in payload["results"]]
        self.assertIn("Fisika", names)
        self.assertIn("Sejarah", names)

    def test_cascade_delete_subject_removes_exam_and_attempt_related_data(self):
        subject = Subject.objects.create(name="Ekonomi", code="EKO")
        question = Question.objects.create(
            created_by=self.teacher,
            subject=subject,
            question_type="multiple_choice",
            question_text="Pertanyaan ekonomi",
            points=10,
            is_active=True,
        )
        option = question.options.create(option_letter="A", option_text="Jawaban", is_correct=True, display_order=1)

        now = timezone.now()
        exam = Exam.objects.create(
            created_by=self.teacher,
            subject=subject,
            title="Ujian Ekonomi",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            duration_minutes=60,
            passing_score=70,
            total_points=10,
            status="published",
        )
        ExamQuestion.objects.create(exam=exam, question=question, display_order=1)
        ExamAssignment.objects.create(exam=exam, assigned_to_type="student", student=self.student)

        attempt = ExamAttempt.objects.create(
            exam=exam,
            student=self.student,
            status="completed",
            start_time=now - timedelta(minutes=50),
            end_time=now - timedelta(minutes=10),
            submit_time=now - timedelta(minutes=10),
            total_score=10,
            percentage=100,
            passed=True,
            time_spent_seconds=2400,
        )
        StudentAnswer.objects.create(
            attempt=attempt,
            question=question,
            answer_type="multiple_choice",
            selected_option=option,
            is_correct=True,
            points_earned=10,
            points_possible=10,
            time_spent_seconds=50,
        )
        ExamViolation.objects.create(
            attempt=attempt,
            violation_type="tab_switch",
            severity="low",
            description="Pindah tab sekali",
        )
        ProctoringScreenshot.objects.create(
            attempt=attempt,
            screenshot_url="https://example.com/ss-1.jpg",
            file_size_kb=200,
        )
        ExamResult.objects.create(
            attempt=attempt,
            exam=exam,
            student=self.student,
            total_score=10,
            percentage=100,
            passed=True,
            total_questions=1,
            correct_answers=1,
            wrong_answers=0,
            unanswered=0,
            time_taken_seconds=2400,
            total_violations=1,
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("subject_delete", kwargs={"pk": subject.pk}),
            data={"confirm_name": "Ekonomi"},
        )
        self.assertEqual(response.status_code, 302)

        self.assertFalse(Subject.objects.filter(id=subject.id).exists())
        self.assertFalse(Question.objects.filter(id=question.id).exists())
        self.assertFalse(Exam.objects.filter(id=exam.id).exists())
        self.assertFalse(ExamAttempt.objects.filter(id=attempt.id).exists())
        self.assertEqual(StudentAnswer.objects.count(), 0)
        self.assertEqual(ExamResult.objects.count(), 0)
        self.assertEqual(ExamViolation.objects.count(), 0)
        self.assertEqual(ProctoringScreenshot.objects.count(), 0)
