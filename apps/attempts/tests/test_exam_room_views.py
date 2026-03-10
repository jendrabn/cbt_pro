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
        self.assertContains(response, "Persyaratan Perangkat Ujian")
        self.assertContains(response, "antiCheatMediaRule")

    def test_non_student_cannot_open_exam_room(self):
        self.client.force_login(self.other_teacher)
        response = self.client.get(reverse("exam_room", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(response.status_code, 403)

    def test_question_api_returns_question_payload(self):
        self.question_mc.audio_play_limit = 2
        self.question_mc.video_play_limit = 1
        self.question_mc.save(update_fields=["audio_play_limit", "video_play_limit"])

        self.client.force_login(self.student)
        response = self.client.get(
            reverse("attempt_question_api", kwargs={"attempt_id": self.attempt.id, "number": 1}),
            {"current_number": 1},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()["payload"]
        self.assertEqual(payload["current_number"], 1)
        self.assertEqual(payload["question"]["question_type"], "multiple_choice")
        self.assertEqual(payload["question"]["audio_play_limit"], 2)
        self.assertEqual(payload["question"]["video_play_limit"], 1)

    def test_question_api_returns_rich_html_for_option_content(self):
        self.option_a.option_text = '<p><img src="/media/questions/richtext/psychotest-a.png" width="120" height="120"></p>'
        self.option_a.save(update_fields=["option_text"])

        self.client.force_login(self.student)
        response = self.client.get(
            reverse("attempt_question_api", kwargs={"attempt_id": self.attempt.id, "number": 1}),
            {"current_number": 1},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["payload"]
        self.assertIn("<img", payload["question"]["options"][0]["text"])

    def test_question_api_sanitizes_legacy_rich_html(self):
        self.question_mc.question_text = '<p>Soal aman</p><script>alert("x")</script><img src="https://example.com/q.png" onerror="alert(1)">'
        self.question_mc.save(update_fields=["question_text"])
        self.option_a.option_text = '<p>Opsi aman</p><img src="https://example.com/a.png" onerror="alert(1)"><script>alert("x")</script>'
        self.option_a.save(update_fields=["option_text"])

        self.client.force_login(self.student)
        response = self.client.get(
            reverse("attempt_question_api", kwargs={"attempt_id": self.attempt.id, "number": 1}),
            {"current_number": 1},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["payload"]
        self.assertIn("Soal aman", payload["question"]["question_text"])
        self.assertIn("<img", payload["question"]["question_text"])
        self.assertNotIn("<script", payload["question"]["question_text"].lower())
        self.assertNotIn("onerror", payload["question"]["question_text"].lower())
        self.assertIn("Opsi aman", payload["question"]["options"][0]["text"])
        self.assertNotIn("<script", payload["question"]["options"][0]["text"].lower())
        self.assertNotIn("onerror", payload["question"]["options"][0]["text"].lower())

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

    def test_save_answer_api_saves_checkbox_answer(self):
        question_checkbox = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="checkbox",
            question_text="Pilih semua gaya yang termasuk gaya kontak.",
            points=8,
            checkbox_scoring="partial_no_penalty",
            is_active=True,
        )
        option_a = question_checkbox.options.create(option_letter="A", option_text="Gaya gesek", is_correct=True, display_order=1)
        option_b = question_checkbox.options.create(option_letter="B", option_text="Gaya gravitasi", is_correct=False, display_order=2)
        option_c = question_checkbox.options.create(option_letter="C", option_text="Gaya normal", is_correct=True, display_order=3)
        ExamQuestion.objects.create(exam=self.exam, question=question_checkbox, display_order=3, points_override=8)

        self.client.force_login(self.student)
        response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 3,
                    "selected_option_ids": [str(option_a.id), str(option_c.id)],
                    "is_marked_for_review": False,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        answer = StudentAnswer.objects.get(attempt=self.attempt, question=question_checkbox)
        self.assertEqual(answer.selected_option_ids, [str(option_a.id), str(option_c.id)])
        self.assertIsNone(answer.selected_option_id)

    def test_question_api_returns_ordering_payload(self):
        question_ordering = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="ordering",
            question_text="Urutkan tahap eksperimen.",
            points=6,
            is_active=True,
        )
        item_1 = question_ordering.ordering_items.create(item_text="Menyiapkan alat", correct_order=1)
        item_2 = question_ordering.ordering_items.create(item_text="Melakukan pengukuran", correct_order=2)
        item_3 = question_ordering.ordering_items.create(item_text="Mencatat hasil", correct_order=3)
        ExamQuestion.objects.create(exam=self.exam, question=question_ordering, display_order=3, points_override=6)

        self.client.force_login(self.student)
        response = self.client.get(
            reverse("attempt_question_api", kwargs={"attempt_id": self.attempt.id, "number": 3}),
            {"current_number": 3},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["payload"]
        ordering_items = payload["question"]["ordering_items"]
        self.assertEqual(payload["question"]["question_type"], "ordering")
        self.assertEqual({item["id"] for item in ordering_items}, {str(item_1.id), str(item_2.id), str(item_3.id)})
        self.assertEqual(payload["question"]["answer"]["answer_order_json"], [])

    def test_save_answer_api_saves_ordering_answer(self):
        question_ordering = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="ordering",
            question_text="Urutkan tahap metode ilmiah.",
            points=8,
            is_active=True,
        )
        item_1 = question_ordering.ordering_items.create(item_text="Observasi", correct_order=1)
        item_2 = question_ordering.ordering_items.create(item_text="Hipotesis", correct_order=2)
        item_3 = question_ordering.ordering_items.create(item_text="Eksperimen", correct_order=3)
        ExamQuestion.objects.create(exam=self.exam, question=question_ordering, display_order=3, points_override=8)

        self.client.force_login(self.student)
        response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 3,
                    "answer_order_json": [str(item_2.id), str(item_1.id), str(item_3.id)],
                    "is_marked_for_review": False,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        answer = StudentAnswer.objects.get(attempt=self.attempt, question=question_ordering)
        self.assertEqual(answer.answer_order_json, [str(item_2.id), str(item_1.id), str(item_3.id)])
        self.assertIsNone(answer.selected_option_id)
        self.assertEqual(answer.selected_option_ids, [])

    def test_question_api_returns_matching_payload(self):
        question_matching = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="matching",
            question_text="Pasangkan besaran dengan satuannya.",
            points=6,
            is_active=True,
        )
        pair_1 = question_matching.matching_pairs.create(prompt_text="Panjang", answer_text="Meter", pair_order=1)
        pair_2 = question_matching.matching_pairs.create(prompt_text="Massa", answer_text="Kilogram", pair_order=2)
        ExamQuestion.objects.create(exam=self.exam, question=question_matching, display_order=3, points_override=6)

        self.client.force_login(self.student)
        response = self.client.get(
            reverse("attempt_question_api", kwargs={"attempt_id": self.attempt.id, "number": 3}),
            {"current_number": 3},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["payload"]
        self.assertEqual(payload["question"]["question_type"], "matching")
        self.assertEqual({item["id"] for item in payload["question"]["matching_pairs"]}, {str(pair_1.id), str(pair_2.id)})
        self.assertEqual(
            {item["id"] for item in payload["question"]["matching_answer_choices"]},
            {str(pair_1.id), str(pair_2.id)},
        )
        self.assertEqual(payload["question"]["answer"]["answer_matching_json"], {})

    def test_save_answer_api_saves_matching_answer(self):
        question_matching = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="matching",
            question_text="Pasangkan alat dengan fungsinya.",
            points=6,
            is_active=True,
        )
        pair_1 = question_matching.matching_pairs.create(prompt_text="Termometer", answer_text="Mengukur suhu", pair_order=1)
        pair_2 = question_matching.matching_pairs.create(prompt_text="Neraca", answer_text="Mengukur massa", pair_order=2)
        ExamQuestion.objects.create(exam=self.exam, question=question_matching, display_order=3, points_override=6)

        self.client.force_login(self.student)
        response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 3,
                    "answer_matching_json": {
                        str(pair_1.id): str(pair_1.id),
                        str(pair_2.id): str(pair_1.id),
                    },
                    "is_marked_for_review": False,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        answer = StudentAnswer.objects.get(attempt=self.attempt, question=question_matching)
        self.assertEqual(
            answer.answer_matching_json,
            {str(pair_1.id): str(pair_1.id), str(pair_2.id): str(pair_1.id)},
        )

    def test_question_api_returns_fill_in_blank_payload(self):
        question_fill_blank = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="fill_in_blank",
            question_text="Satuan gaya adalah {{1}} dan satuan massa adalah {{2}}.",
            points=8,
            is_active=True,
        )
        question_fill_blank.blank_answers.create(blank_number=1, accepted_answers=["Newton"], blank_points=4)
        question_fill_blank.blank_answers.create(blank_number=2, accepted_answers=["Kilogram"], blank_points=4)
        ExamQuestion.objects.create(exam=self.exam, question=question_fill_blank, display_order=3, points_override=8)

        self.client.force_login(self.student)
        response = self.client.get(
            reverse("attempt_question_api", kwargs={"attempt_id": self.attempt.id, "number": 3}),
            {"current_number": 3},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()["payload"]
        self.assertEqual(payload["question"]["question_type"], "fill_in_blank")
        self.assertEqual(payload["question"]["blank_numbers"], [1, 2])
        self.assertEqual(payload["question"]["answer"]["answer_blanks_json"], {})

    def test_save_answer_api_saves_fill_in_blank_answer(self):
        question_fill_blank = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="fill_in_blank",
            question_text="Planet terbesar adalah {{1}}.",
            points=5,
            is_active=True,
        )
        question_fill_blank.blank_answers.create(blank_number=1, accepted_answers=["Jupiter"], blank_points=5)
        ExamQuestion.objects.create(exam=self.exam, question=question_fill_blank, display_order=3, points_override=5)

        self.client.force_login(self.student)
        response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 3,
                    "answer_blanks_json": {"1": "Jupiter"},
                    "is_marked_for_review": False,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        answer = StudentAnswer.objects.get(attempt=self.attempt, question=question_fill_blank)
        self.assertEqual(answer.answer_blanks_json, {"1": "Jupiter"})

    def test_submit_attempt_grades_checkbox_partial_score(self):
        question_checkbox = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="checkbox",
            question_text="Pilih semua bilangan prima.",
            points=8,
            checkbox_scoring="partial_no_penalty",
            is_active=True,
        )
        option_a = question_checkbox.options.create(option_letter="A", option_text="2", is_correct=True, display_order=1)
        question_checkbox.options.create(option_letter="B", option_text="4", is_correct=False, display_order=2)
        option_c = question_checkbox.options.create(option_letter="C", option_text="3", is_correct=True, display_order=3)
        ExamQuestion.objects.create(exam=self.exam, question=question_checkbox, display_order=3, points_override=8)

        self.client.force_login(self.student)
        save_response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 3,
                    "selected_option_ids": [str(option_a.id)],
                    "is_marked_for_review": False,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(save_response.status_code, 200)

        submit_response = self.client.post(
            reverse("attempt_submit_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(submit_response.status_code, 200)
        answer = StudentAnswer.objects.get(attempt=self.attempt, question=question_checkbox)
        self.assertEqual(float(answer.points_earned), 4.0)
        self.assertFalse(answer.is_correct)

    def test_submit_attempt_grades_ordering_partial_score(self):
        question_ordering = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="ordering",
            question_text="Urutkan perkembangan teori atom.",
            points=8,
            is_active=True,
        )
        item_1 = question_ordering.ordering_items.create(item_text="Dalton", correct_order=1)
        item_2 = question_ordering.ordering_items.create(item_text="Thomson", correct_order=2)
        item_3 = question_ordering.ordering_items.create(item_text="Rutherford", correct_order=3)
        item_4 = question_ordering.ordering_items.create(item_text="Bohr", correct_order=4)
        ExamQuestion.objects.create(exam=self.exam, question=question_ordering, display_order=3, points_override=8)

        self.client.force_login(self.student)
        save_response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 3,
                    "answer_order_json": [str(item_2.id), str(item_1.id), str(item_3.id), str(item_4.id)],
                    "is_marked_for_review": False,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(save_response.status_code, 200)

        submit_response = self.client.post(
            reverse("attempt_submit_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(submit_response.status_code, 200)
        answer = StudentAnswer.objects.get(attempt=self.attempt, question=question_ordering)
        self.assertEqual(float(answer.points_earned), 6.0)
        self.assertFalse(answer.is_correct)

    def test_submit_attempt_grades_matching_partial_score(self):
        question_matching = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="matching",
            question_text="Pasangkan besaran dengan satuan SI.",
            points=8,
            is_active=True,
        )
        pair_1 = question_matching.matching_pairs.create(prompt_text="Panjang", answer_text="Meter", pair_order=1)
        pair_2 = question_matching.matching_pairs.create(prompt_text="Waktu", answer_text="Sekon", pair_order=2)
        pair_3 = question_matching.matching_pairs.create(prompt_text="Massa", answer_text="Kilogram", pair_order=3)
        ExamQuestion.objects.create(exam=self.exam, question=question_matching, display_order=3, points_override=8)

        self.client.force_login(self.student)
        save_response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 3,
                    "answer_matching_json": {
                        str(pair_1.id): str(pair_1.id),
                        str(pair_2.id): str(pair_1.id),
                        str(pair_3.id): str(pair_3.id),
                    },
                    "is_marked_for_review": False,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(save_response.status_code, 200)

        submit_response = self.client.post(
            reverse("attempt_submit_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(submit_response.status_code, 200)
        answer = StudentAnswer.objects.get(attempt=self.attempt, question=question_matching)
        self.assertAlmostEqual(float(answer.points_earned), 5.33, places=2)
        self.assertFalse(answer.is_correct)

    def test_submit_attempt_grades_fill_in_blank_partial_score(self):
        question_fill_blank = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="fill_in_blank",
            question_text="Ibu kota Indonesia adalah {{1}} dan ibu kota Jepang adalah {{2}}.",
            points=8,
            is_active=True,
        )
        question_fill_blank.blank_answers.create(blank_number=1, accepted_answers=["Jakarta"], blank_points=5)
        question_fill_blank.blank_answers.create(blank_number=2, accepted_answers=["Tokyo", "Tokio"], blank_points=3)
        ExamQuestion.objects.create(exam=self.exam, question=question_fill_blank, display_order=3, points_override=8)

        self.client.force_login(self.student)
        save_response = self.client.post(
            reverse("attempt_save_answer_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "question_number": 3,
                    "answer_blanks_json": {"1": "Jakarta", "2": "Osaka"},
                    "is_marked_for_review": False,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(save_response.status_code, 200)

        submit_response = self.client.post(
            reverse("attempt_submit_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(submit_response.status_code, 200)
        answer = StudentAnswer.objects.get(attempt=self.attempt, question=question_fill_blank)
        self.assertEqual(float(answer.points_earned), 5.0)
        self.assertFalse(answer.is_correct)

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

    def test_violation_api_accepts_suspicious_activity_for_media_loss(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("attempt_violation_api", kwargs={"attempt_id": self.attempt.id}),
            data=json.dumps(
                {
                    "type": "suspicious_activity",
                    "description": "Akses kamera atau mikrofon dicabut atau terputus saat ujian berlangsung.",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertEqual(payload.get("violations_count"), 1)
        self.assertFalse(payload.get("auto_submitted"))

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
