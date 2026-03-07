import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.exams.models import Class, Exam
from apps.questions.models import Question
from apps.subjects.models import Subject


class ExamManagementViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_exam",
            email="teacher.exam@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Ujian",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_exam",
            email="student.exam@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Ujian",
            role="student",
            is_active=True,
        )
        cls.other_teacher = User.objects.create_user(
            username="teacher_exam_other",
            email="teacher.exam.other@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Lain",
            role="teacher",
            is_active=True,
        )
        cls.subject = Subject.objects.create(name="Fisika", code="FIS", is_active=True)
        cls.class_obj = Class.objects.create(name="XII IPA 2", is_active=True)
        cls.question = Question.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            question_type="multiple_choice",
            question_text="Gaya gravitasi dipengaruhi oleh ...",
            points=10,
            difficulty_level="medium",
            allow_previous=True,
            allow_next=True,
            force_sequential=False,
            is_active=True,
        )
        cls.other_question = Question.objects.create(
            created_by=cls.other_teacher,
            subject=cls.subject,
            question_type="essay",
            question_text="Jelaskan konsep energi potensial.",
            points=15,
            difficulty_level="medium",
            allow_previous=True,
            allow_next=True,
            force_sequential=False,
            is_active=True,
        )

    def _create_exam(self, status="draft"):
        now = timezone.now()
        exam = Exam.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            title="Ujian Fisika Tengah Semester",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2),
            duration_minutes=90,
            passing_score=70,
            total_points=10,
            status=status,
        )
        exam.exam_questions.create(question=self.question, display_order=1, points_override=10)
        exam.assignments.create(assigned_to_type="class", class_obj=self.class_obj)
        return exam

    def test_teacher_can_access_exam_list(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("exam_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manajemen Ujian")

    def test_non_teacher_forbidden_exam_list(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("exam_list"))
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_create_exam_from_wizard(self):
        self.client.force_login(self.teacher)
        now = timezone.localtime(timezone.now())
        start = (now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        end = (now + timedelta(days=2, hours=3)).strftime("%Y-%m-%dT%H:%M")

        selected_payload = json.dumps(
            [
                {
                    "question_id": str(self.question.id),
                    "display_order": 1,
                    "points_override": 12,
                    "override_navigation": True,
                    "allow_previous_override": False,
                    "allow_next_override": True,
                    "force_sequential_override": False,
                }
            ]
        )
        assignment_payload = json.dumps([{"type": "class", "id": str(self.class_obj.id)}])

        response = self.client.post(
            reverse("exam_create"),
            data={
                "title": "Ujian Fisika Final",
                "subject": str(self.subject.id),
                "description": "Deskripsi ujian",
                "instructions": "Kerjakan dengan teliti.",
                "start_time": start,
                "end_time": end,
                "duration_minutes": 120,
                "passing_score": 75,
                "randomize_questions": "on",
                "randomize_options": "on",
                "show_results_immediately": "",
                "allow_review": "on",
                "override_question_navigation": "on",
                "global_allow_previous": "",
                "global_allow_next": "on",
                "global_force_sequential": "on",
                "require_fullscreen": "on",
                "detect_tab_switch": "on",
                "enable_screenshot_proctoring": "on",
                "screenshot_interval_seconds": 300,
                "max_violations_allowed": 3,
                "selected_questions_payload": selected_payload,
                "assignment_payload": assignment_payload,
                "status_action": "draft",
            },
        )

        self.assertEqual(response.status_code, 302)
        exam = Exam.objects.get(title="Ujian Fisika Final")
        self.assertEqual(exam.status, "draft")
        self.assertEqual(exam.exam_questions.count(), 1)
        self.assertEqual(exam.assignments.count(), 1)
        self.assertEqual(float(exam.total_points), 12.0)

    def test_teacher_can_publish_and_unpublish_exam(self):
        exam = self._create_exam(status="draft")
        self.client.force_login(self.teacher)

        publish_response = self.client.post(reverse("exam_publish", kwargs={"pk": exam.pk}))
        self.assertEqual(publish_response.status_code, 302)
        exam.refresh_from_db()
        self.assertEqual(exam.status, "published")

        unpublish_response = self.client.post(reverse("exam_publish", kwargs={"pk": exam.pk}))
        self.assertEqual(unpublish_response.status_code, 302)
        exam.refresh_from_db()
        self.assertEqual(exam.status, "draft")

    def test_teacher_can_duplicate_exam(self):
        exam = self._create_exam(status="published")
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("exam_duplicate", kwargs={"pk": exam.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Exam.objects.filter(created_by=self.teacher, is_deleted=False).count(), 2)

    def test_teacher_can_open_exam_preview(self):
        exam = self._create_exam(status="draft")
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("exam_preview", kwargs={"pk": exam.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pratinjau Tampilan Siswa")
        self.assertEqual(response.get("X-Frame-Options"), "SAMEORIGIN")

    def test_teacher_can_fetch_exam_question_picker_data(self):
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse("exam_question_picker"),
            {"q": "gravitasi", "page_size": 20, "page": 1},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("items", payload)
        self.assertIn("pagination", payload)
        self.assertEqual(payload["pagination"]["page_size"], 20)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["id"], str(self.question.id))

    def test_question_picker_only_returns_teacher_questions(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("exam_question_picker"), {"page": 1, "page_size": 50})
        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.json().get("items", [])}
        self.assertIn(str(self.question.id), ids)
        self.assertNotIn(str(self.other_question.id), ids)
