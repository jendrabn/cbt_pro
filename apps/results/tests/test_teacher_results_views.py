from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attempts.models import ExamAttempt, ExamViolation, StudentAnswer
from apps.exams.models import Class, ClassStudent, Exam, ExamAssignment, ExamQuestion
from apps.questions.models import Question, QuestionAnswer
from apps.results.models import ExamResult
from apps.subjects.models import Subject


class TeacherResultsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_results",
            email="teacher.results@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Hasil",
            role="teacher",
            is_active=True,
        )
        cls.student_one = User.objects.create_user(
            username="student_result_1",
            email="student.result1@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Satu",
            role="student",
            is_active=True,
        )
        cls.student_two = User.objects.create_user(
            username="student_result_2",
            email="student.result2@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Dua",
            role="student",
            is_active=True,
        )
        cls.student_three = User.objects.create_user(
            username="student_result_3",
            email="student.result3@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Tiga",
            role="student",
            is_active=True,
        )
        cls.admin = User.objects.create_user(
            username="admin_result",
            email="admin.result@cbt.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="Result",
            role="admin",
            is_active=True,
            is_staff=True,
        )

        cls.subject = Subject.objects.create(name="Biologi", code="BIO", is_active=True)
        cls.class_obj = Class.objects.create(name="XII IPA 3", is_active=True)
        now = timezone.now()

        cls.exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            title="Ujian Biologi Semester",
            description="Evaluasi semester genap",
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
            duration_minutes=90,
            passing_score=70,
            total_points=100,
            status="completed",
            require_fullscreen=True,
            detect_tab_switch=True,
        )
        ExamAssignment.objects.create(exam=cls.exam, assigned_to_type="class", class_obj=cls.class_obj)
        ClassStudent.objects.create(class_obj=cls.class_obj, student=cls.student_one)
        ClassStudent.objects.create(class_obj=cls.class_obj, student=cls.student_two)
        ClassStudent.objects.create(class_obj=cls.class_obj, student=cls.student_three)

        cls.question_mc = Question.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            question_type="multiple_choice",
            question_text="Organel penghasil energi utama pada sel adalah ...",
            points=10,
            difficulty_level="easy",
            is_active=True,
        )
        cls.option_a = cls.question_mc.options.create(
            option_letter="A",
            option_text="Nukleus",
            is_correct=False,
            display_order=1,
        )
        cls.option_b = cls.question_mc.options.create(
            option_letter="B",
            option_text="Mitokondria",
            is_correct=True,
            display_order=2,
        )
        cls.question_essay = Question.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            question_type="essay",
            question_text="Jelaskan proses fotosintesis secara singkat.",
            points=20,
            difficulty_level="medium",
            is_active=True,
        )
        QuestionAnswer.objects.create(question=cls.question_essay, answer_text="Fotosintesis adalah ...")

        ExamQuestion.objects.create(exam=cls.exam, question=cls.question_mc, display_order=1, points_override=10)
        ExamQuestion.objects.create(exam=cls.exam, question=cls.question_essay, display_order=2, points_override=20)

        cls.attempt_one = ExamAttempt.objects.create(
            exam=cls.exam,
            student=cls.student_one,
            status="completed",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            submit_time=now - timedelta(hours=1),
            total_score=24,
            percentage=80,
            passed=True,
            time_spent_seconds=3200,
        )
        cls.attempt_two = ExamAttempt.objects.create(
            exam=cls.exam,
            student=cls.student_two,
            status="completed",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1, minutes=10),
            submit_time=now - timedelta(hours=1, minutes=10),
            total_score=15,
            percentage=50,
            passed=False,
            time_spent_seconds=2800,
        )
        cls.attempt_three = ExamAttempt.objects.create(
            exam=cls.exam,
            student=cls.student_three,
            status="auto_submitted",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1, minutes=5),
            submit_time=now - timedelta(hours=1, minutes=5),
            total_score=0,
            percentage=0,
            passed=False,
            time_spent_seconds=3300,
        )

        StudentAnswer.objects.create(
            attempt=cls.attempt_one,
            question=cls.question_mc,
            answer_type="multiple_choice",
            selected_option=cls.option_b,
            is_correct=True,
            points_earned=10,
            points_possible=10,
            time_spent_seconds=120,
        )
        StudentAnswer.objects.create(
            attempt=cls.attempt_one,
            question=cls.question_essay,
            answer_type="essay",
            answer_text="Fotosintesis memanfaatkan cahaya...",
            is_correct=True,
            points_earned=14,
            points_possible=20,
            time_spent_seconds=480,
        )
        StudentAnswer.objects.create(
            attempt=cls.attempt_two,
            question=cls.question_mc,
            answer_type="multiple_choice",
            selected_option=cls.option_a,
            is_correct=False,
            points_earned=0,
            points_possible=10,
            time_spent_seconds=140,
        )
        StudentAnswer.objects.create(
            attempt=cls.attempt_three,
            question=cls.question_mc,
            answer_type="multiple_choice",
            selected_option=cls.option_b,
            points_earned=0,
            points_possible=10,
            time_spent_seconds=150,
        )

        ExamViolation.objects.create(
            attempt=cls.attempt_two,
            violation_type="tab_switch",
            severity="medium",
            description="Berpindah tab 2 kali",
        )

        cls.result_one = ExamResult.objects.create(
            attempt=cls.attempt_one,
            exam=cls.exam,
            student=cls.student_one,
            total_score=24,
            percentage=80,
            passed=True,
            total_questions=2,
            correct_answers=2,
            wrong_answers=0,
            unanswered=0,
            time_taken_seconds=3200,
            total_violations=0,
        )
        cls.result_two = ExamResult.objects.create(
            attempt=cls.attempt_two,
            exam=cls.exam,
            student=cls.student_two,
            total_score=15,
            percentage=50,
            passed=False,
            total_questions=2,
            correct_answers=0,
            wrong_answers=1,
            unanswered=1,
            time_taken_seconds=2800,
            total_violations=1,
        )

    def test_teacher_can_access_results_list(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("teacher_results"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hasil & Analitik")

    def test_non_teacher_forbidden_results_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("teacher_results"))
        self.assertEqual(response.status_code, 403)

    def test_teacher_can_access_exam_results_detail(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("exam_results_detail", kwargs={"exam_id": self.exam.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hasil Siswa")
        self.assertContains(response, self.exam.title)
        self.assertContains(response, self.student_three.get_full_name())
        self.assertTrue(ExamResult.objects.filter(attempt=self.attempt_three).exists())

    def test_teacher_can_open_answer_review_page(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("answer_review", kwargs={"result_id": self.result_one.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lembar Jawaban Lengkap")

    def test_teacher_can_access_results_analytics_dashboard(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("teacher_results_analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard Analitik Hasil")

    def test_teacher_can_export_results_xlsx(self):
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse("export_results", kwargs={"exam_id": self.exam.id}),
            data={"format": "xlsx"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            response["Content-Type"],
        )

    def test_teacher_can_export_results_csv(self):
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse("export_results", kwargs={"exam_id": self.exam.id}),
            data={"format": "csv"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])

    def test_teacher_can_bulk_export_selected_results_xlsx(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("exam_results_detail", kwargs={"exam_id": self.exam.id}),
            data={
                "action": "export_excel",
                "selected_ids": [str(self.result_one.id)],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            response["Content-Type"],
        )

    def test_teacher_can_export_results_pdf(self):
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse("export_results", kwargs={"exam_id": self.exam.id}),
            data={"format": "pdf"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response["Content-Type"])
