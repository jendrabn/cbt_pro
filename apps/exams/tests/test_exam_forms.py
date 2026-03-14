import json
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import UserProfile
from apps.accounts.models import User
from apps.exams.forms import ExamWizardForm
from apps.exams.models import Class, ClassStudent, Exam
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

    def test_checkbox_fields_use_standard_bootstrap_checkbox_attrs(self):
        form = ExamWizardForm(teacher=self.teacher)

        checkbox_fields = [
            "randomize_questions",
            "randomize_options",
            "show_results_immediately",
            "allow_review",
            "allow_retake",
            "retake_show_review",
            "certificate_enabled",
            "override_question_navigation",
            "global_allow_previous",
            "global_allow_next",
            "global_force_sequential",
            "require_fullscreen",
            "require_camera",
            "require_microphone",
            "detect_tab_switch",
            "disable_right_click",
            "block_copy_paste",
            "enable_screenshot_proctoring",
        ]

        for field_name in checkbox_fields:
            with self.subTest(field_name=field_name):
                attrs = form.fields[field_name].widget.attrs
                self.assertIn("form-check-input", attrs.get("class", ""))
                self.assertNotIn("role", attrs)

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

    def test_form_initial_payload_strips_html_from_selected_question_text(self):
        subject = Subject.objects.create(name="Kimia", code="KIM", is_active=True)
        question = Question.objects.create(
            created_by=self.teacher,
            subject=subject,
            question_type="multiple_choice",
            question_text="<p>Rumus <strong>asam</strong> adalah H<sub>2</sub>SO<sub>4</sub>.</p>",
            points=5,
            is_active=True,
        )
        now = timezone.now()
        exam = Exam.objects.create(
            created_by=self.teacher,
            subject=subject,
            title="Ujian Kimia",
            description="Tes kimia",
            instructions="Kerjakan",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            duration_minutes=60,
            passing_score=70,
            total_points=5,
            status=Exam.Status.DRAFT,
        )
        exam.exam_questions.create(question=question, display_order=1, points_override=5)

        form = ExamWizardForm(instance=exam, teacher=self.teacher)
        payload = json.loads(form.initial["selected_questions_payload"])

        self.assertEqual(payload[0]["question_text"], "Rumus asam adalah H2SO4.")
        self.assertNotIn("<strong>", payload[0]["question_text"])
        self.assertNotIn("<sub>", payload[0]["question_text"])

    def test_form_initial_uses_browser_datetime_local_format_for_edit(self):
        subject = Subject.objects.create(name="Sejarah", code="SEJ", is_active=True)
        now = timezone.now()
        exam = Exam.objects.create(
            created_by=self.teacher,
            subject=subject,
            title="Ujian Sejarah",
            description="Tes sejarah",
            instructions="Kerjakan",
            start_time=now + timedelta(days=2, minutes=15),
            end_time=now + timedelta(days=2, hours=2, minutes=45),
            duration_minutes=90,
            passing_score=75,
            total_points=0,
            status=Exam.Status.DRAFT,
        )

        form = ExamWizardForm(instance=exam, teacher=self.teacher)
        expected_start = timezone.localtime(exam.start_time).strftime("%Y-%m-%dT%H:%M")
        expected_end = timezone.localtime(exam.end_time).strftime("%Y-%m-%dT%H:%M")

        self.assertEqual(form.initial["start_time"], expected_start)
        self.assertEqual(form.initial["end_time"], expected_end)
        self.assertEqual(form["start_time"].value(), expected_start)
        self.assertEqual(form["end_time"].value(), expected_end)
