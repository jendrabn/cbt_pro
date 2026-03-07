from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.accounts.models import User
from apps.exams.forms import ExamWizardForm
from apps.exams.models import Class, ClassStudent


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
