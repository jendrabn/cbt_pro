from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from apps.accounts.models import User
from apps.questions.models import Question, QuestionCategory
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
