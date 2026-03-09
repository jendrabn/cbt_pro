from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import UserProfile
from apps.accounts.models import User
from apps.exams.forms import ExamWizardForm
from apps.exams.models import Class, ClassStudent
from apps.subjects.models import Subject
from apps.questions.models import Question


class ExamWizardFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_form_exam",
            email="teacher.form.exam@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Form",
            role="teacher",
            is_active=True,
        )
        cls.student_one = User.objects.create_user(
            username="student_form_exam_1",
            email="student.form.exam.1@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Satu",
            role="student",
            is_active=True,
        )
        cls.student_two = User.objects.create_user(
            username="student_form_exam_2",
            email="student.form.exam.2@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Dua",
            role="student",
            is_active=True,
        )
        cls.student_three = User.objects.create_user(
            username="student_form_exam_3",
            email="student.form.exam.3@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Tiga",
            role="student",
            is_active=True,
        )
        UserProfile.objects.create(user=cls.student_one, class_grade="XII IPA 1")
        UserProfile.objects.create(user=cls.student_two, class_grade="XII IPA 1")
        UserProfile.objects.create(user=cls.student_three, class_grade="XI IPS 2")

    def test_form_syncs_classes_from_student_profiles(self):
        form = ExamWizardForm(teacher=self.teacher)

        self.assertQuerySetEqual(
            form.available_classes,
            ["XI IPS 2", "XII IPA 1"],
            transform=lambda item: item.name,
            ordered=True,
        )
        self.assertEqual(form.available_students.count(), 3)
        self.assertEqual(Class.objects.filter(name="XII IPA 1", is_active=True).count(), 1)
        self.assertEqual(Class.objects.filter(name="XI IPS 2", is_active=True).count(), 1)

        class_names_by_student = {
            membership.student.username: membership.class_obj.name
            for membership in ClassStudent.objects.select_related("student", "class_obj")
        }
        self.assertEqual(class_names_by_student["student_form_exam_1"], "XII IPA 1")
        self.assertEqual(class_names_by_student["student_form_exam_2"], "XII IPA 1")
        self.assertEqual(class_names_by_student["student_form_exam_3"], "XI IPS 2")

    def test_form_requires_camera_when_screenshot_proctoring_enabled(self):
        subject = Subject.objects.create(name="Biologi", code="BIO", is_active=True)
        question = Question.objects.create(
            created_by=self.teacher,
            subject=subject,
            question_type="multiple_choice",
            question_text="Contoh soal biologi",
            points=10,
            is_active=True,
        )
        now = timezone.localtime(timezone.now())
        form = ExamWizardForm(
            data={
                "title": "Ujian Biologi",
                "subject": str(subject.id),
                "description": "Tes",
                "instructions": "Kerjakan",
                "start_time": (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
                "end_time": (now + timedelta(days=1, hours=2)).strftime("%Y-%m-%dT%H:%M"),
                "duration_minutes": 60,
                "passing_score": 70,
                "allow_review": "on",
                "global_allow_previous": "on",
                "global_allow_next": "on",
                "require_fullscreen": "on",
                "require_microphone": "on",
                "enable_screenshot_proctoring": "on",
                "screenshot_interval_seconds": 300,
                "max_violations_allowed": 3,
                "selected_questions_payload": (
                    '[{"question_id":"%s","display_order":1,"points_override":10,"override_navigation":false}]'
                    % question.id
                ),
                "assignment_payload": '[]',
                "status_action": "draft",
            },
            teacher=self.teacher,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("require_camera", form.errors)
