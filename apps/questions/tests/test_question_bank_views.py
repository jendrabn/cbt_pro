import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import ProgrammingError
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook

from apps.accounts.models import User
from apps.questions.models import Question, QuestionCategory, QuestionImportLog
from apps.questions.services import get_question_import_history
from apps.subjects.models import Subject


class QuestionBankViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_qb",
            email="teacher.qb@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="BankSoal",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_qb",
            email="student.qb@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="BankSoal",
            role="student",
            is_active=True,
        )
        cls.subject = Subject.objects.create(name="Matematika", code="MAT", is_active=True)
        cls.category = QuestionCategory.objects.create(name="Aljabar", is_active=True)

    def _create_sample_question(self):
        question = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            category=self.category,
            question_type="multiple_choice",
            question_text="2 + 2 = ...",
            points=5,
            difficulty_level="easy",
            allow_previous=True,
            allow_next=True,
            force_sequential=False,
            is_active=True,
        )
        question.options.create(option_letter="A", option_text="3", is_correct=False, display_order=1)
        question.options.create(option_letter="B", option_text="4", is_correct=True, display_order=2)
        return question

    def test_teacher_can_access_question_list(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("question_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manajemen Bank Soal")

    def test_non_teacher_forbidden_question_list(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("question_list"))
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_create_multiple_choice_question(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("question_create"),
            data={
                "subject": str(self.subject.id),
                "category": str(self.category.id),
                "question_type": "multiple_choice",
                "question_text": "Ibu kota Indonesia adalah ...",
                "points": "10",
                "difficulty_level": "easy",
                "explanation": "Jawaban yang benar adalah Jakarta.",
                "allow_previous": "on",
                "allow_next": "on",
                "is_active": "on",
                "option_a": "Bandung",
                "option_b": "Jakarta",
                "option_c": "",
                "option_d": "",
                "option_e": "",
                "correct_option": "B",
                "tags": "geografi, indonesia",
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Question.objects.get(question_text__icontains="Ibu kota Indonesia")
        self.assertEqual(created.question_type, "multiple_choice")
        self.assertEqual(created.options.count(), 2)
        self.assertTrue(created.options.filter(option_letter="B", is_correct=True).exists())

    def test_teacher_can_create_multiple_choice_question_with_image_only_richtext(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("question_create"),
            data={
                "subject": str(self.subject.id),
                "category": str(self.category.id),
                "question_type": "multiple_choice",
                "question_text": '<p><img src="/media/questions/richtext/sample-question.png" width="280" height="140"></p>',
                "points": "10",
                "difficulty_level": "easy",
                "explanation": "<table><tr><th>Petunjuk</th></tr><tr><td>Perhatikan gambar pada soal.</td></tr></table>",
                "allow_previous": "on",
                "allow_next": "on",
                "is_active": "on",
                "option_a": '<p><img src="/media/questions/richtext/sample-option-a.png" width="120" height="120"></p>',
                "option_b": "<p>Gambar B</p>",
                "option_c": "",
                "option_d": "",
                "option_e": "",
                "correct_option": "B",
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Question.objects.get(created_by=self.teacher, question_type="multiple_choice", points=10)
        self.assertIn("<img", created.question_text)
        self.assertTrue(created.options.filter(option_letter="A").exists())
        self.assertIn("<img", created.options.get(option_letter="A").option_text)

    def test_teacher_can_upload_richtext_image(self):
        temp_media_root = tempfile.mkdtemp(prefix="cbt_question_media_")
        self.addCleanup(lambda: shutil.rmtree(temp_media_root, ignore_errors=True))
        self.client.force_login(self.teacher)
        image_file = SimpleUploadedFile(
            "diagram.png",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
            content_type="image/png",
        )

        with override_settings(MEDIA_ROOT=temp_media_root):
            response = self.client.post(
                reverse("question_richtext_upload"),
                data={"file": image_file},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("location", payload)
        self.assertIn("/media/questions/richtext/", payload["location"])

        relative_path = payload["location"].split("/media/", 1)[-1].lstrip("/")
        self.assertTrue((Path(temp_media_root) / relative_path).exists())

    def test_teacher_can_duplicate_question(self):
        question = self._create_sample_question()
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("question_duplicate", kwargs={"pk": question.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Question.objects.filter(created_by=self.teacher, is_deleted=False).count(), 2)

    def test_teacher_can_open_question_preview(self):
        question = self._create_sample_question()
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("question_preview", kwargs={"pk": question.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pratinjau Soal")
        self.assertEqual(response.get("X-Frame-Options"), "SAMEORIGIN")

    def test_teacher_can_export_question_excel(self):
        self._create_sample_question()
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("question_export"), data={"format": "xlsx"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            response["Content-Type"],
        )
        self.assertIn("attachment;", response["Content-Disposition"])

    def test_teacher_can_export_question_csv(self):
        self._create_sample_question()
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("question_export"), data={"format": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn(".csv", response["Content-Disposition"])

    def test_teacher_can_bulk_delete_questions(self):
        question = self._create_sample_question()
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("question_list"),
            data={
                "action": "delete",
                "selected_ids": [str(question.id)],
            },
        )
        self.assertEqual(response.status_code, 302)
        question.refresh_from_db()
        self.assertTrue(question.is_deleted)

    def test_teacher_can_import_question_excel(self):
        self.client.force_login(self.teacher)
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(
            [
                "subject",
                "category",
                "question_type",
                "question_text",
                "difficulty_level",
                "points",
                "option_a",
                "option_b",
                "correct_option",
            ]
        )
        worksheet.append(
            [
                "Matematika",
                "Aljabar",
                "multiple_choice",
                "5 + 5 = ...",
                "easy",
                5,
                "9",
                "10",
                "B",
            ]
        )
        payload = BytesIO()
        workbook.save(payload)
        upload = SimpleUploadedFile(
            "import_soal.xlsx",
            payload.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response = self.client.post(reverse("question_import"), data={"import_file": upload})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Question.objects.filter(question_text__icontains="5 + 5").exists())
        self.assertContains(response, "Ringkasan Impor Terakhir")
        self.assertContains(response, "Template Bank Soal")
        self.assertContains(response, "Riwayat Impor")
        import_log = QuestionImportLog.objects.latest("created_at")
        self.assertEqual(import_log.total_created, 1)
        self.assertEqual(import_log.total_failed, 0)
        self.assertEqual(import_log.status, "completed")

        report_response = self.client.get(reverse("question_import_report", kwargs={"log_id": import_log.id}))
        self.assertEqual(report_response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            report_response["Content-Type"],
        )

    def test_question_import_history_returns_empty_when_log_table_unavailable(self):
        with patch(
            "apps.questions.services.QuestionImportLog.objects.select_related",
            side_effect=ProgrammingError("table missing"),
        ):
            history = get_question_import_history(self.teacher, limit=10)

        self.assertEqual(history, [])
