from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attempts.models import ExamAttempt
from apps.exams.models import Class, Exam, ExamAssignment, ExamQuestion
from apps.questions.models import Question
from apps.results.models import Certificate, ExamResult
from apps.subjects.models import Subject


class AdminAnalyticsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="admin_analytics",
            email="admin.analytics@cbt.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="Analytics",
            role="admin",
            is_active=True,
            is_staff=True,
        )
        cls.teacher = User.objects.create_user(
            username="guru_analytics",
            email="guru.analytics@cbt.com",
            password="GuruPass123!",
            first_name="Guru",
            last_name="Analytics",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="siswa_analytics",
            email="siswa.analytics@cbt.com",
            password="SiswaPass123!",
            first_name="Siswa",
            last_name="Analytics",
            role="student",
            is_active=True,
        )

        subject = Subject.objects.create(name="Matematika", code="MATH", is_active=True)
        class_obj = Class.objects.create(name="XII IPA 1", is_active=True)
        now = timezone.now()
        exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=subject,
            title="Ujian Matematika Akhir",
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
            duration_minutes=90,
            passing_score=70,
            total_points=100,
            status="ongoing",
            require_fullscreen=True,
            detect_tab_switch=True,
        )
        question = Question.objects.create(
            created_by=cls.teacher,
            subject=subject,
            question_type="multiple_choice",
            question_text="2 + 2 = ?",
            points=10,
            is_active=True,
        )
        ExamQuestion.objects.create(exam=exam, question=question, display_order=1)
        ExamAssignment.objects.create(exam=exam, assigned_to_type="class", class_obj=class_obj)
        attempt = ExamAttempt.objects.create(
            exam=exam,
            student=cls.student,
            status="completed",
            start_time=now - timedelta(hours=1),
            end_time=now - timedelta(minutes=10),
            submit_time=now - timedelta(minutes=10),
            total_score=85,
            percentage=85,
            passed=True,
        )
        ExamResult.objects.create(
            attempt=attempt,
            exam=exam,
            student=cls.student,
            total_score=85,
            percentage=85,
            passed=True,
            total_questions=1,
            correct_answers=1,
            wrong_answers=0,
            unanswered=0,
            time_taken_seconds=3000,
            total_violations=0,
        )
        Certificate.objects.create(
            attempt=attempt,
            exam=exam,
            student=cls.student,
            certificate_number="CERT-AN-001",
            verification_token="token-an-001",
            final_score=85,
            final_percentage=85,
            template_snapshot={},
            is_valid=True,
        )

    def test_admin_can_access_analytics_dashboard(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Analitik & Laporan")
        self.assertContains(response, "Sertifikat Terbit")
        self.assertContains(response, "Status Sertifikat")

    def test_non_admin_forbidden_analytics_dashboard(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("admin_analytics"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_reports_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("system_reports"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laporan Analitik")

    def test_admin_can_export_reports_csv(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("export_analytics"),
            data={
                "format": "csv",
                "date_from": "2000-01-01",
                "date_to": "2100-12-31",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("attachment;", response["Content-Disposition"])
