import json
from urllib.parse import urlparse
from datetime import timedelta
from unittest.mock import patch

from django.db import OperationalError
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attempts.models import ExamAttempt, ProctoringScreenshot, StudentAnswer
from apps.exams.models import Exam, ExamAssignment, ExamQuestion
from apps.questions.models import Question
from apps.results.models import ExamResult
from apps.subjects.models import Subject


class StudentExamRoomViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_exam_room",
            email="teacher.exam.room@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Ruang",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_exam_room",
            email="student.exam.room@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Ruang",
            role="student",
            is_active=True,
        )
        cls.other_teacher = User.objects.create_user(
            username="teacher_exam_room_other",
            email="teacher.exam.room.other@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Lain",
            role="teacher",
            is_active=True,
        )

        cls.subject = Subject.objects.create(name="Fisika", code="FIS", is_active=True)
        now = timezone.now()
        cls.exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            title="Ujian Fisika Dinamika",
            description="Ujian untuk menguji konsep dinamika.",
            instructions="Jawab semua soal dengan teliti.",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            duration_minutes=90,
            passing_score=70,
            total_points=20,
            status="published",
            allow_retake=True,
            max_retake_attempts=3,
            retake_score_policy="highest",
            retake_cooldown_minutes=0,
            max_violations_allowed=2,
            detect_tab_switch=True,
            require_fullscreen=True,
            enable_screenshot_proctoring=True,
            screenshot_interval_seconds=120,
        )

        cls.question_mc = Question.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            question_type="multiple_choice",
            question_text="Gaya total yang bekerja pada benda disebut ...",
            points=10,
            is_active=True,
        )
        cls.option_a = cls.question_mc.options.create(
            option_letter="A",
            option_text="Resultan gaya",
            is_correct=True,
            display_order=1,
        )
        cls.question_mc.options.create(
            option_letter="B",
            option_text="Gaya gesek",
            is_correct=False,
            display_order=2,
        )

        cls.question_essay = Question.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            question_type="essay",
            question_text="Jelaskan Hukum Newton pertama.",
            points=10,
            is_active=True,
        )

        ExamQuestion.objects.create(exam=cls.exam, question=cls.question_mc, display_order=1, points_override=10)
        ExamQuestion.objects.create(exam=cls.exam, question=cls.question_essay, display_order=2, points_override=10)
        ExamAssignment.objects.create(exam=cls.exam, assigned_to_type="student", student=cls.student)

        cls.attempt = ExamAttempt.objects.create(
            exam=cls.exam,
            student=cls.student,
            attempt_number=1,
            status="in_progress",
            start_time=now - timedelta(minutes=10),
            end_time=now + timedelta(minutes=80),
            ip_address="127.0.0.1",
            user_agent="django-test-client",
        )

    def test_student_can_open_exam_room_page(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("exam_room", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ruang Ujian Siswa")

    def test_non_student_cannot_open_exam_room(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse("exam_room", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(response.status_code, 403)

    def test_question_api_returns_question_payload(self):
        self.client.force_login(self.student)
        response = self.client.get(
            reverse("attempt_question_api", kwargs={"attempt_id": self.attempt.id, "number": 1}),
            {"current_number": 1},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()["payload"]
        self.assertEqual(payload["current_number"], 1)
        self.assertEqual(payload["question"]["question_type"], "multiple_choice")

    def test_save_answer_api_saves_multiple_choice_answer(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 1,
                    "selected_option_id": str(self.option_a.id),
                    "is_marked_for_review": False,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        answer = StudentAnswer.objects.get(attempt=self.attempt, question=self.question_mc)
        self.assertEqual(answer.selected_option_id, self.option_a.id)

    @patch("apps.attempts.views.save_attempt_answer")
    def test_save_answer_api_handles_lock_timeout_gracefully(self, save_mock):
        save_mock.side_effect = OperationalError(1205, "Lock wait timeout exceeded")
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 1,
                    "selected_option_id": str(self.option_a.id),
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertFalse(payload.get("saved"))
        self.assertFalse(payload.get("auto_submitted"))
        self.assertIn("autosave", payload.get("message", "").lower())

    @patch("apps.attempts.views.auto_submit_if_time_expired")
    def test_question_api_handles_lock_timeout_gracefully(self, auto_submit_mock):
        auto_submit_mock.side_effect = OperationalError(1205, "Lock wait timeout exceeded")
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("attempt_question_api", kwargs={"attempt_id": self.attempt.id, "number": 1}),
            {"current_number": 1},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertIn("sibuk", payload.get("message", "").lower())
        self.assertIn("payload", payload)

    def test_submit_api_submits_attempt(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("attempt_submit_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, "submitted")
        self.assertIsNotNone(self.attempt.retake_available_from)
        self.assertTrue(ExamResult.objects.filter(attempt=self.attempt).exists())
        self.assertTrue(response.json().get("redirect_url"))

    @patch("apps.attempts.views.submit_attempt")
    def test_submit_api_handles_lock_timeout_when_already_submitted(self, submit_mock):
        submit_mock.side_effect = OperationalError(1205, "Lock wait timeout exceeded")
        self.attempt.status = "submitted"
        self.attempt.submit_time = timezone.now()
        self.attempt.save(update_fields=["status", "submit_time", "updated_at"])
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("attempt_submit_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertTrue(payload.get("redirect_url"))
        self.assertIn("sudah", payload.get("message", "").lower())

    @patch("apps.attempts.views.submit_attempt")
    def test_submit_api_handles_lock_timeout_with_retryable_response(self, submit_mock):
        submit_mock.side_effect = OperationalError(1205, "Lock wait timeout exceeded")
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("attempt_submit_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        payload = response.json()
        self.assertFalse(payload.get("success"))
        self.assertTrue(payload.get("retryable"))

    @override_settings(MEDIA_URL="/media/")
    def test_proctoring_api_stores_screenshot_file(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("attempt_proctoring_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "label": "interval",
                    "screenshot_data_url": "data:image/png;base64,"
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7pJ1UAAAAASUVORK5CYII=",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))

        screenshot = ProctoringScreenshot.objects.get(attempt=self.attempt)
        self.assertNotIn("proctoring.local", screenshot.screenshot_url)
        self.assertIn("/media/proctoring/", screenshot.screenshot_url)
        self.assertGreater(int(screenshot.file_size_kb or 0), 0)

        parsed = urlparse(screenshot.screenshot_url)
        path = parsed.path if parsed.path else screenshot.screenshot_url
        relative_path = path.split("/media/", 1)[-1].lstrip("/")
        self.assertTrue(default_storage.exists(relative_path))

    @patch("apps.attempts.views.record_proctoring_capture")
    def test_proctoring_api_handles_lock_timeout_gracefully(self, proctoring_mock):
        proctoring_mock.side_effect = OperationalError(1205, "Lock wait timeout exceeded")
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("attempt_proctoring_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "label": "interval",
                    "screenshot_data_url": "data:image/png;base64,abc",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload.get("success"))
        self.assertIn("dilewati", payload.get("message", "").lower())

    def test_student_can_check_and_start_retake(self):
        self.client.force_login(self.student)
        self.client.post(
            reverse("attempt_submit_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({}),
            content_type="application/json",
        )

        check_response = self.client.get(reverse("retake_check", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(check_response.status_code, 200)
        check_payload = check_response.json()
        self.assertTrue(check_payload["eligible"])
        self.assertEqual(check_payload["attempts_used"], 1)
        self.assertEqual(check_payload["max_attempts"], 3)

        start_response = self.client.post(reverse("retake_start", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(start_response.status_code, 302)
        self.assertEqual(start_response.url, reverse("exam_room", kwargs={"exam_id": self.exam.id}))

        latest_attempt = (
            ExamAttempt.objects.filter(exam=self.exam, student=self.student)
            .order_by("-attempt_number")
            .first()
        )
        self.assertIsNotNone(latest_attempt)
        self.assertEqual(latest_attempt.attempt_number, 2)

    def test_violation_api_auto_submits_when_limit_reached(self):
        self.client.force_login(self.student)
        self.client.post(
            reverse("attempt_violation_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({"type": "tab_switch", "description": "Pindah tab pertama"}),
            content_type="application/json",
        )
        response = self.client.post(
            reverse("attempt_violation_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({"type": "fullscreen_exit", "description": "Keluar fullscreen"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, "auto_submitted")
        self.assertTrue(ExamResult.objects.filter(attempt=self.attempt).exists())
        self.assertTrue(response.json().get("auto_submitted"))
        self.assertTrue(response.json().get("redirect_url"))

    @patch("apps.attempts.views.record_exam_violation")
    def test_violation_api_handles_lock_timeout_gracefully(self, record_mock):
        record_mock.side_effect = OperationalError(1205, "Lock wait timeout exceeded")
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("attempt_violation_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({"type": "tab_switch", "description": "Pindah tab saat submit"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertFalse(payload.get("auto_submitted"))
        self.assertIn("sibuk", payload.get("message", "").lower())

    def test_submitted_attempt_can_open_submit_confirmation_page(self):
        self.attempt.status = "submitted"
        self.attempt.submit_time = timezone.now()
        self.attempt.save(update_fields=["status", "submit_time", "updated_at"])

        self.client.force_login(self.student)
        response = self.client.get(reverse("exam_submit", kwargs={"attempt_id": self.attempt.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ujian Berhasil Dikirim")
