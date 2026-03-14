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
        cls.subject = Subject.objects.create(name="Fisika", code="FIS")
        cls.class_obj = Class.objects.create(name="XII IPA 2")
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

    def _create_exam(self, status="draft", allow_retake=False, max_retake_attempts=1):
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
            allow_retake=allow_retake,
            max_retake_attempts=max_retake_attempts,
        )
        exam.exam_questions.create(question=self.question, display_order=1, points_override=10)
        exam.assignments.create(assigned_to_type="class", class_obj=self.class_obj)
        return exam

    def test_teacher_can_access_exam_list(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("exam_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manajemen Ujian")

    def test_exam_list_uses_remix_icon_for_retake_badge(self):
        self._create_exam(status="draft", allow_retake=True, max_retake_attempts=2)
        self.client.force_login(self.teacher)

        response = self.client.get(reverse("exam_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ri-repeat-line")
        self.assertContains(response, "2x")
        self.assertNotContains(response, "🔁")

    def test_exam_list_uses_cards_only_without_view_switch(self):
        self._create_exam(status="draft")
        self.client.force_login(self.teacher)

        response = self.client.get(reverse("exam_list"), {"view": "table"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="card border-0 shadow-sm h-100 exam-card"', html=False)
        self.assertNotContains(response, "Tampilan tabel")
        self.assertNotContains(response, "Tampilan kartu")

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
                "require_camera": "on",
                "require_microphone": "on",
                "detect_tab_switch": "on",
                "disable_right_click": "on",
                "block_copy_paste": "on",
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
        self.assertTrue(exam.require_camera)
        self.assertTrue(exam.require_microphone)
        self.assertTrue(exam.block_copy_paste)

    def test_exam_create_form_shows_all_question_type_filters(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("exam_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<option value="multiple_choice">Pilihan Ganda</option>', html=True)
        self.assertContains(response, '<option value="checkbox">Checkbox</option>', html=True)
        self.assertContains(response, '<option value="ordering">Ordering</option>', html=True)
        self.assertContains(response, '<option value="matching">Matching</option>', html=True)
        self.assertContains(response, '<option value="fill_in_blank">Fill In Blank</option>', html=True)
        self.assertContains(response, '<option value="essay">Esai</option>', html=True)
        self.assertContains(response, '<option value="short_answer">Jawaban Singkat</option>', html=True)

    def test_exam_create_form_uses_standard_checkboxes_in_settings_and_anticheat(self):
        self.client.force_login(self.teacher)

        response = self.client.get(reverse("exam_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pengaturan Retake")
        self.assertContains(response, "Aturan Navigasi Global")
        self.assertContains(response, "Persyaratan Perangkat & Fokus")
        self.assertContains(response, "Pemantauan")
        self.assertContains(response, "Blokir klik kanan")
        self.assertContains(response, "Blokir copy, cut, dan paste")
        self.assertContains(response, 'id="availableQuestionList"')
        self.assertContains(response, 'id="selectedQuestionList" class="list-group"')
        self.assertContains(response, 'class="form-check"', html=False)
        self.assertNotContains(response, "form-switch")
        self.assertNotContains(response, 'role="switch"', html=False)
        self.assertNotContains(response, "Kelola Template")
        self.assertNotContains(response, "Buat Template Baru")

    def test_exam_edit_form_uses_standard_checkboxes_in_settings_and_anticheat(self):
        exam = self._create_exam(status="draft")
        self.client.force_login(self.teacher)

        response = self.client.get(reverse("exam_edit", kwargs={"pk": exam.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pengaturan Retake")
        self.assertContains(response, "Persyaratan Perangkat & Fokus")
        self.assertContains(response, "Pemantauan")
        self.assertContains(response, "Blokir klik kanan")
        self.assertContains(response, "Blokir copy, cut, dan paste")
        self.assertNotContains(response, "form-switch")
        self.assertNotContains(response, 'role="switch"', html=False)
        self.assertNotContains(response, "Kelola Template")
        self.assertNotContains(response, "Buat Template Baru")

    def test_exam_edit_form_prefills_saved_start_and_end_time(self):
        exam = self._create_exam(status="draft")
        self.client.force_login(self.teacher)

        response = self.client.get(reverse("exam_edit", kwargs={"pk": exam.pk}))

        expected_start = timezone.localtime(exam.start_time).strftime("%Y-%m-%dT%H:%M")
        expected_end = timezone.localtime(exam.end_time).strftime("%Y-%m-%dT%H:%M")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'value="{expected_start}"', html=False)
        self.assertContains(response, f'value="{expected_end}"', html=False)

    def test_exam_detail_shows_right_click_anticheat_setting(self):
        exam = self._create_exam(status="draft")
        self.client.force_login(self.teacher)

        response = self.client.get(reverse("exam_detail", kwargs={"pk": exam.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Blokir Klik Kanan: Ya")

    def test_exam_detail_shows_copy_paste_anticheat_setting(self):
        exam = self._create_exam(status="draft")
        exam.block_copy_paste = True
        exam.save(update_fields=["block_copy_paste", "updated_at"])
        self.client.force_login(self.teacher)

        response = self.client.get(reverse("exam_detail", kwargs={"pk": exam.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Blokir Copy/Cut/Paste: Ya")

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

    def test_question_picker_strips_html_from_richtext_question_text(self):
        rich_question = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="multiple_choice",
            question_text="<p>Hitung <strong>gaya</strong> gesek.</p>",
            points=10,
            difficulty_level="easy",
            allow_previous=True,
            allow_next=True,
            force_sequential=False,
            is_active=True,
        )
        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse("exam_question_picker"),
            {"q": "gaya", "page_size": 20, "page": 1},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        item = next(row for row in payload["items"] if row["id"] == str(rich_question.id))
        self.assertEqual(item["text"], "Hitung gaya gesek.")
        self.assertNotIn("<p>", item["text"])
        self.assertNotIn("<strong>", item["text"])

    def test_question_picker_only_returns_teacher_questions(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("exam_question_picker"), {"page": 1, "page_size": 50})
        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.json().get("items", [])}
        self.assertIn(str(self.question.id), ids)
        self.assertNotIn(str(self.other_question.id), ids)

    def test_question_picker_can_filter_checkbox_questions(self):
        checkbox_question = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="checkbox",
            question_text="Pilih semua contoh gaya sentuh.",
            points=8,
            difficulty_level="easy",
            allow_previous=True,
            allow_next=True,
            force_sequential=False,
            is_active=True,
        )

        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse("exam_question_picker"),
            {"question_type": "checkbox", "page": 1, "page_size": 50},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item["id"] for item in payload.get("items", [])}
        self.assertIn(str(checkbox_question.id), ids)
        self.assertNotIn(str(self.question.id), ids)
