import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attempts.models import ExamAttempt, ExamViolation, ProctoringScreenshot, StudentAnswer
from apps.exams.models import Exam
from apps.notifications.models import Notification
from apps.questions.models import Question
from apps.subjects.models import Subject


class MonitoringViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_monitor",
            email="teacher.monitor@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Monitor",
            role="teacher",
            is_active=True,
        )
        cls.other_teacher = User.objects.create_user(
            username="teacher_other_monitor",
            email="teacher.other.monitor@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Lain",
            role="teacher",
            is_active=True,
        )
        cls.student_one = User.objects.create_user(
            username="student_monitor_1",
            email="student.monitor.1@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Satu",
            role="student",
            is_active=True,
        )
        cls.student_two = User.objects.create_user(
            username="student_monitor_2",
            email="student.monitor.2@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Dua",
            role="student",
            is_active=True,
        )

        cls.subject = Subject.objects.create(name="Kimia", code="KIM", is_active=True)
        cls.question = Question.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            question_type="multiple_choice",
            question_text="Lambang kimia air adalah ...",
            points=10,
            difficulty_level="easy",
            allow_previous=True,
            allow_next=True,
            force_sequential=False,
            is_active=True,
        )
        cls.question.options.create(option_letter="A", option_text="H2O", is_correct=True, display_order=1)
        cls.question.options.create(option_letter="B", option_text="CO2", is_correct=False, display_order=2)

        now = timezone.now()
        cls.exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            title="Ujian Kimia Monitoring",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            duration_minutes=120,
            passing_score=70,
            total_points=10,
            status="ongoing",
        )
        cls.exam.exam_questions.create(question=cls.question, display_order=1, points_override=10)
        cls.exam.assignments.create(assigned_to_type="student", student=cls.student_one)
        cls.exam.assignments.create(assigned_to_type="student", student=cls.student_two)

        cls.attempt_one = ExamAttempt.objects.create(
            exam=cls.exam,
            student=cls.student_one,
            attempt_number=1,
            start_time=now - timedelta(minutes=40),
            status="in_progress",
            time_spent_seconds=1800,
        )
        StudentAnswer.objects.create(
            attempt=cls.attempt_one,
            question=cls.question,
            answer_type="multiple_choice",
            selected_option=cls.question.options.filter(option_letter="A").first(),
            points_earned=10,
            points_possible=10,
            answer_order=1,
            time_spent_seconds=70,
        )
        ExamViolation.objects.create(
            attempt=cls.attempt_one,
            violation_type="tab_switch",
            severity="medium",
            description="Pindah tab",
        )
        ProctoringScreenshot.objects.create(
            attempt=cls.attempt_one,
            screenshot_url="https://example.com/screenshots/attempt-one.png",
            is_flagged=False,
        )

        cls.attempt_two = ExamAttempt.objects.create(
            exam=cls.exam,
            student=cls.student_two,
            attempt_number=1,
            start_time=now - timedelta(minutes=70),
            submit_time=now - timedelta(minutes=5),
            end_time=now - timedelta(minutes=5),
            status="submitted",
            time_spent_seconds=3500,
        )

    def test_teacher_can_open_monitoring_dashboard(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("monitoring_dashboard", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Grid Monitoring Siswa")

    def test_non_teacher_forbidden_monitoring_dashboard(self):
        self.client.force_login(self.student_one)
        response = self.client.get(reverse("monitoring_dashboard", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_open_other_teacher_exam_monitoring(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse("monitoring_dashboard", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(response.status_code, 404)

    def test_snapshot_api_returns_expected_payload(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("monitoring_snapshot", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("stats", payload)
        self.assertIn("students", payload)
        self.assertGreaterEqual(len(payload["students"]), 2)

    def test_student_detail_api_returns_answer_history(self):
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse(
                "student_detail",
                kwargs={"exam_id": self.exam.id, "student_id": self.student_one.id},
            )
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIsNotNone(payload["attempt"])
        self.assertEqual(len(payload["answers"]), 1)

    def test_extend_time_api_updates_attempt_end_time(self):
        self.client.force_login(self.teacher)
        old_end_time = self.attempt_one.end_time
        response = self.client.post(
            reverse("extend_time", kwargs={"exam_id": self.exam.id}),
            data=json.dumps({"student_id": str(self.student_one.id), "minutes": 15}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.attempt_one.refresh_from_db()
        self.assertIsNotNone(self.attempt_one.end_time)
        if old_end_time is not None:
            self.assertGreater(self.attempt_one.end_time, old_end_time)

    def test_force_submit_api_updates_attempt_status(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("force_submit", kwargs={"attempt_id": self.attempt_one.id}),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.attempt_one.refresh_from_db()
        self.assertEqual(self.attempt_one.status, "auto_submitted")
        self.assertIsNotNone(self.attempt_one.submit_time)

    def test_announcement_api_creates_notifications(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("monitoring_announcement", kwargs={"exam_id": self.exam.id}),
            data=json.dumps(
                {
                    "target": "all",
                    "title": "Info Ujian",
                    "message": "Harap fokus pada layar ujian.",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Notification.objects.filter(
                related_entity_type="exam",
                related_entity_id=self.exam.id,
                notification_type="announcement",
            ).count(),
            2,
        )
