from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.attempts.models import ExamAttempt
from apps.exams.models import Exam
from apps.results.models import ExamResult
from apps.results.services import calculate_final_score
from apps.subjects.models import Subject


class FinalScorePolicyServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_final_score",
            email="teacher.final.score@cbt.com",
            password="TeacherPass123!",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_final_score",
            email="student.final.score@cbt.com",
            password="StudentPass123!",
            role="student",
            is_active=True,
        )
        subject = Subject.objects.create(name="Geografi", code="GEO")
        now = timezone.now()
        cls.exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=subject,
            title="Ujian Geografi Final Policy",
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
            duration_minutes=60,
            passing_score=70,
            total_points=100,
            status="published",
            allow_retake=True,
            max_retake_attempts=3,
            retake_score_policy="highest",
        )

        scores = [Decimal("60.00"), Decimal("80.00"), Decimal("70.00")]
        for idx, score in enumerate(scores, start=1):
            attempt = ExamAttempt.objects.create(
                exam=cls.exam,
                student=cls.student,
                attempt_number=idx,
                status="submitted",
                start_time=now - timedelta(hours=idx + 1),
                end_time=now - timedelta(hours=idx),
                submit_time=now - timedelta(hours=idx),
                total_score=score,
                percentage=score,
                passed=score >= Decimal("70.00"),
                time_spent_seconds=1200,
            )
            ExamResult.objects.create(
                attempt=attempt,
                exam=cls.exam,
                student=cls.student,
                total_score=score,
                percentage=score,
                passed=score >= Decimal("70.00"),
                total_questions=10,
                correct_answers=int(score / 10),
                wrong_answers=0,
                unanswered=0,
                time_taken_seconds=1200,
                total_violations=0,
            )

    def test_calculate_final_score_policy_highest(self):
        self.exam.retake_score_policy = "highest"
        self.exam.save(update_fields=["retake_score_policy", "updated_at"])
        score = calculate_final_score(self.exam.id, self.student.id)
        self.assertEqual(score, Decimal("80.00"))

    def test_calculate_final_score_policy_latest(self):
        self.exam.retake_score_policy = "latest"
        self.exam.save(update_fields=["retake_score_policy", "updated_at"])
        score = calculate_final_score(self.exam.id, self.student.id)
        self.assertEqual(score, Decimal("70.00"))

    def test_calculate_final_score_policy_average(self):
        self.exam.retake_score_policy = "average"
        self.exam.save(update_fields=["retake_score_policy", "updated_at"])
        score = calculate_final_score(self.exam.id, self.student.id)
        self.assertEqual(score, Decimal("70.00"))
