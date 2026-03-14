from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attempts.models import ExamAttempt, StudentAnswer
from apps.exams.models import Exam, ExamAssignment, ExamQuestion
from apps.questions.models import Question, QuestionAnswer
from apps.results.models import Certificate, ExamResult
from apps.subjects.models import Subject


class StudentResultsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_student_results",
            email="teacher.student.results@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Hasil",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_results_owner",
            email="student.results.owner@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Owner",
            role="student",
            is_active=True,
        )
        cls.other_student = User.objects.create_user(
            username="student_results_other",
            email="student.results.other@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Lain",
            role="student",
            is_active=True,
        )

        cls.subject = Subject.objects.create(name="Kimia", code="KIM")
        now = timezone.now()

        cls.exam_review_on = Exam.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            title="Ujian Kimia Bab Reaksi",
            description="Ujian formatif reaksi kimia",
            start_time=now - timedelta(days=4),
            end_time=now - timedelta(days=4, hours=-1),
            duration_minutes=60,
            passing_score=70,
            total_points=20,
            show_results_immediately=True,
            allow_review=True,
            status="completed",
        )
        cls.exam_review_off = Exam.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            title="Ujian Kimia Bab Atom",
            description="Ujian formatif struktur atom",
            start_time=now - timedelta(days=3),
            end_time=now - timedelta(days=3, hours=-1),
            duration_minutes=60,
            passing_score=70,
            total_points=20,
            show_results_immediately=True,
            allow_review=False,
            status="completed",
        )

        ExamAssignment.objects.create(exam=cls.exam_review_on, assigned_to_type="student", student=cls.student)
        ExamAssignment.objects.create(exam=cls.exam_review_off, assigned_to_type="student", student=cls.student)
        ExamAssignment.objects.create(exam=cls.exam_review_on, assigned_to_type="student", student=cls.other_student)

        cls.question_one = Question.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            question_type="multiple_choice",
            question_text="Unsur dengan simbol Na adalah...",
            points=10,
            explanation="Na adalah natrium, termasuk logam alkali.",
            is_active=True,
        )
        cls.option_a = cls.question_one.options.create(
            option_letter="A",
            option_text="Natrium",
            is_correct=True,
            display_order=1,
        )
        cls.option_b = cls.question_one.options.create(
            option_letter="B",
            option_text="Nitrogen",
            is_correct=False,
            display_order=2,
        )
        cls.question_two = Question.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            question_type="essay",
            question_text="Jelaskan pengertian ikatan ion.",
            points=10,
            explanation="Ikatan ion terjadi karena perpindahan elektron.",
            is_active=True,
        )
        QuestionAnswer.objects.create(question=cls.question_two, answer_text="Terjadi transfer elektron antar atom.")

        ExamQuestion.objects.create(exam=cls.exam_review_on, question=cls.question_one, display_order=1, points_override=10)
        ExamQuestion.objects.create(exam=cls.exam_review_on, question=cls.question_two, display_order=2, points_override=10)
        ExamQuestion.objects.create(exam=cls.exam_review_off, question=cls.question_one, display_order=1, points_override=10)

        cls.attempt_review_on = ExamAttempt.objects.create(
            exam=cls.exam_review_on,
            student=cls.student,
            status="completed",
            start_time=now - timedelta(days=4, minutes=50),
            end_time=now - timedelta(days=4, minutes=5),
            submit_time=now - timedelta(days=4, minutes=5),
            total_score=17,
            percentage=85,
            passed=True,
            time_spent_seconds=2700,
        )
        cls.attempt_review_off = ExamAttempt.objects.create(
            exam=cls.exam_review_off,
            student=cls.student,
            status="completed",
            start_time=now - timedelta(days=3, minutes=45),
            end_time=now - timedelta(days=3, minutes=8),
            submit_time=now - timedelta(days=3, minutes=8),
            total_score=6,
            percentage=60,
            passed=False,
            time_spent_seconds=2220,
        )
        cls.other_attempt = ExamAttempt.objects.create(
            exam=cls.exam_review_on,
            student=cls.other_student,
            status="completed",
            start_time=now - timedelta(days=4, minutes=50),
            end_time=now - timedelta(days=4, minutes=4),
            submit_time=now - timedelta(days=4, minutes=4),
            total_score=15,
            percentage=75,
            passed=True,
            time_spent_seconds=2760,
        )

        StudentAnswer.objects.create(
            attempt=cls.attempt_review_on,
            question=cls.question_one,
            answer_type="multiple_choice",
            selected_option=cls.option_a,
            is_correct=True,
            points_earned=10,
            points_possible=10,
            time_spent_seconds=110,
        )
        StudentAnswer.objects.create(
            attempt=cls.attempt_review_on,
            question=cls.question_two,
            answer_type="essay",
            answer_text="Ikatan ion terjadi karena transfer elektron.",
            is_correct=True,
            points_earned=7,
            points_possible=10,
            time_spent_seconds=300,
        )
        StudentAnswer.objects.create(
            attempt=cls.attempt_review_off,
            question=cls.question_one,
            answer_type="multiple_choice",
            selected_option=cls.option_b,
            is_correct=False,
            points_earned=0,
            points_possible=10,
            time_spent_seconds=135,
        )

        cls.result_review_on = ExamResult.objects.create(
            attempt=cls.attempt_review_on,
            exam=cls.exam_review_on,
            student=cls.student,
            total_score=17,
            percentage=85,
            passed=True,
            total_questions=2,
            correct_answers=2,
            wrong_answers=0,
            unanswered=0,
            rank_in_exam=1,
            percentile=90,
            time_taken_seconds=2700,
            time_efficiency=88,
            total_violations=0,
        )
        cls.result_review_off = ExamResult.objects.create(
            attempt=cls.attempt_review_off,
            exam=cls.exam_review_off,
            student=cls.student,
            total_score=6,
            percentage=60,
            passed=False,
            total_questions=1,
            correct_answers=0,
            wrong_answers=1,
            unanswered=0,
            time_taken_seconds=2220,
            total_violations=0,
        )
        cls.other_result = ExamResult.objects.create(
            attempt=cls.other_attempt,
            exam=cls.exam_review_on,
            student=cls.other_student,
            total_score=15,
            percentage=75,
            passed=True,
            total_questions=2,
            correct_answers=1,
            wrong_answers=1,
            unanswered=0,
            time_taken_seconds=2760,
            total_violations=0,
        )

        Certificate.objects.create(
            result=cls.result_review_on,
            certificate_number="CERT-STUDENT-001",
            certificate_url="https://example.com/certificates/CERT-STUDENT-001.pdf",
            is_valid=True,
        )

    def test_student_can_access_results_list(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_results"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hasil & Review Ujian")
        self.assertContains(response, self.exam_review_on.title)

    def test_student_results_list_flags_pending_manual_grading(self):
        pending_exam = Exam.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            title="Ujian Kimia Essay Lanjutan",
            description="Ujian dengan penilaian manual",
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=2, hours=-1),
            duration_minutes=60,
            passing_score=70,
            total_points=10,
            show_results_immediately=True,
            allow_review=True,
            status="completed",
        )
        ExamAssignment.objects.create(exam=pending_exam, assigned_to_type="student", student=self.student)
        essay_question = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="essay",
            question_text="Jelaskan sifat ikatan kovalen.",
            points=10,
            is_active=True,
        )
        ExamQuestion.objects.create(exam=pending_exam, question=essay_question, display_order=1, points_override=10)
        pending_attempt = ExamAttempt.objects.create(
            exam=pending_exam,
            student=self.student,
            status="grading",
            start_time=timezone.now() - timedelta(days=2, minutes=40),
            end_time=timezone.now() - timedelta(days=2, minutes=5),
            submit_time=timezone.now() - timedelta(days=2, minutes=5),
            total_score=0,
            percentage=0,
            passed=False,
            time_spent_seconds=2100,
        )
        StudentAnswer.objects.create(
            attempt=pending_attempt,
            question=essay_question,
            answer_type="essay",
            answer_text="Ikatan kovalen terjadi karena pemakaian bersama pasangan elektron.",
            is_correct=None,
            points_earned=0,
            points_possible=10,
            time_spent_seconds=260,
        )
        pending_result = ExamResult.objects.create(
            attempt=pending_attempt,
            exam=pending_exam,
            student=self.student,
            total_score=0,
            percentage=0,
            passed=False,
            total_questions=1,
            correct_answers=0,
            wrong_answers=1,
            unanswered=0,
            time_taken_seconds=2100,
            total_violations=0,
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("student_results"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pending_exam.title)
        self.assertContains(response, "Belum Selesai Dinilai")
        self.assertContains(response, reverse("student_result_detail", kwargs={"result_id": pending_result.id}))

    def test_non_student_forbidden_results_list(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("student_results"))
        self.assertEqual(response.status_code, 403)

    def test_student_can_access_own_result_detail(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_result_detail", kwargs={"result_id": self.result_review_on.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ringkasan Jawaban")
        self.assertContains(response, self.exam_review_on.title)

    def test_student_result_detail_shows_pending_manual_grading_alert(self):
        pending_exam = Exam.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            title="Ujian Kimia Essay Pending",
            description="Detail status pending",
            start_time=timezone.now() - timedelta(days=1),
            end_time=timezone.now() - timedelta(days=1, hours=-1),
            duration_minutes=60,
            passing_score=70,
            total_points=10,
            show_results_immediately=True,
            allow_review=True,
            status="completed",
        )
        ExamAssignment.objects.create(exam=pending_exam, assigned_to_type="student", student=self.student)
        essay_question = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="essay",
            question_text="Jelaskan perbedaan senyawa ion dan kovalen.",
            points=10,
            is_active=True,
        )
        ExamQuestion.objects.create(exam=pending_exam, question=essay_question, display_order=1, points_override=10)
        pending_attempt = ExamAttempt.objects.create(
            exam=pending_exam,
            student=self.student,
            status="grading",
            start_time=timezone.now() - timedelta(days=1, minutes=50),
            end_time=timezone.now() - timedelta(days=1, minutes=8),
            submit_time=timezone.now() - timedelta(days=1, minutes=8),
            total_score=0,
            percentage=0,
            passed=False,
            time_spent_seconds=2520,
        )
        StudentAnswer.objects.create(
            attempt=pending_attempt,
            question=essay_question,
            answer_type="essay",
            answer_text="Ikatan ion terjadi karena transfer elektron, sedangkan kovalen karena berbagi elektron.",
            is_correct=None,
            points_earned=0,
            points_possible=10,
            time_spent_seconds=320,
        )
        pending_result = ExamResult.objects.create(
            attempt=pending_attempt,
            exam=pending_exam,
            student=self.student,
            total_score=0,
            percentage=0,
            passed=False,
            total_questions=1,
            correct_answers=0,
            wrong_answers=1,
            unanswered=0,
            time_taken_seconds=2520,
            total_violations=0,
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("student_result_detail", kwargs={"result_id": pending_result.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "belum selesai dinilai")

    def test_student_cannot_access_other_student_result_detail(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_result_detail", kwargs={"result_id": self.other_result.id}))
        self.assertEqual(response.status_code, 404)

    def test_student_can_open_answer_review_if_exam_allows(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_answer_review", kwargs={"result_id": self.result_review_on.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review Soal per Nomor")
        self.assertContains(response, "Na adalah natrium")

    def test_student_answer_review_renders_ordering_question(self):
        question_ordering = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="ordering",
            question_text="Urutkan proses pembentukan ikatan.",
            points=10,
            explanation="Elektron valensi berinteraksi sebelum terbentuk ikatan stabil.",
            is_active=True,
        )
        item_1 = question_ordering.ordering_items.create(item_text="Atom saling mendekat", correct_order=1)
        question_ordering.ordering_items.create(item_text="Elektron valensi berinteraksi", correct_order=2)
        item_3 = question_ordering.ordering_items.create(item_text="Terbentuk ikatan stabil", correct_order=3)
        ExamQuestion.objects.create(exam=self.exam_review_on, question=question_ordering, display_order=3, points_override=10)
        StudentAnswer.objects.create(
            attempt=self.attempt_review_on,
            question=question_ordering,
            answer_type="ordering",
            answer_order_json=[str(item_3.id), str(item_1.id)],
            is_correct=False,
            points_earned=3,
            points_possible=10,
            time_spent_seconds=180,
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("student_answer_review", kwargs={"result_id": self.result_review_on.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Urutkan proses pembentukan ikatan")
        self.assertContains(response, "Terbentuk ikatan stabil")

    def test_student_answer_review_renders_matching_question(self):
        question_matching = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="matching",
            question_text="Pasangkan unsur dengan lambangnya.",
            points=10,
            explanation="Gunakan simbol unsur yang benar.",
            is_active=True,
        )
        pair_1 = question_matching.matching_pairs.create(prompt_text="Natrium", answer_text="Na", pair_order=1)
        pair_2 = question_matching.matching_pairs.create(prompt_text="Kalium", answer_text="K", pair_order=2)
        ExamQuestion.objects.create(exam=self.exam_review_on, question=question_matching, display_order=3, points_override=10)
        StudentAnswer.objects.create(
            attempt=self.attempt_review_on,
            question=question_matching,
            answer_type="matching",
            answer_matching_json={str(pair_1.id): str(pair_1.id), str(pair_2.id): str(pair_1.id)},
            is_correct=False,
            points_earned=5,
            points_possible=10,
            time_spent_seconds=160,
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("student_answer_review", kwargs={"result_id": self.result_review_on.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pasangkan unsur dengan lambangnya")
        self.assertContains(response, "Natrium")
        self.assertContains(response, "Kalium")

    def test_student_answer_review_renders_fill_in_blank_question(self):
        question_fill_blank = Question.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            question_type="fill_in_blank",
            question_text="Simbol kimia emas adalah {{1}}.",
            points=10,
            explanation="Emas memiliki simbol Au.",
            is_active=True,
        )
        question_fill_blank.blank_answers.create(blank_number=1, accepted_answers=["Au"], blank_points=10)
        ExamQuestion.objects.create(exam=self.exam_review_on, question=question_fill_blank, display_order=3, points_override=10)
        StudentAnswer.objects.create(
            attempt=self.attempt_review_on,
            question=question_fill_blank,
            answer_type="fill_in_blank",
            answer_blanks_json={"1": "Ag"},
            is_correct=False,
            points_earned=0,
            points_possible=10,
            time_spent_seconds=110,
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse("student_answer_review", kwargs={"result_id": self.result_review_on.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Simbol kimia emas adalah")
        self.assertContains(response, "fill-blank-chip is-incorrect", html=False)
        self.assertContains(response, ">Ag<", html=False)
        self.assertContains(response, "fill-blank-chip is-answer-key", html=False)
        self.assertContains(response, "Au")

    def test_student_review_forbidden_if_exam_disables_review(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_answer_review", kwargs={"result_id": self.result_review_off.id}))
        self.assertEqual(response.status_code, 403)

    def test_student_can_download_certificate(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_certificate_download", kwargs={"result_id": self.result_review_on.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "https://example.com/certificates/CERT-STUDENT-001.pdf",
        )

    def test_student_certificate_redirects_to_detail_if_unavailable(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("student_certificate_download", kwargs={"result_id": self.result_review_off.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("student_result_detail", kwargs={"result_id": self.result_review_off.id}),
        )
