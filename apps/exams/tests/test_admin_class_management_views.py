from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User, UserProfile
from apps.exams.models import Class, ClassStudent, Exam, ExamAssignment
from apps.subjects.models import Subject


@override_settings(SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class AdminClassManagementViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="admin_class_mgmt",
            email="admin.class.mgmt@cbt.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="Kelas",
            role="admin",
            is_active=True,
            is_staff=True,
        )
        cls.teacher = User.objects.create_user(
            username="teacher_class_mgmt",
            email="teacher.class.mgmt@cbt.com",
            password="TeacherPass123!",
            first_name="Guru",
            last_name="Kelas",
            role="teacher",
            is_active=True,
        )
        cls.student_one = User.objects.create_user(
            username="student_class_mgmt_1",
            email="student.class.mgmt.1@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Satu",
            role="student",
            is_active=True,
        )
        cls.student_two = User.objects.create_user(
            username="student_class_mgmt_2",
            email="student.class.mgmt.2@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Dua",
            role="student",
            is_active=True,
        )
        cls.student_three = User.objects.create_user(
            username="student_class_mgmt_3",
            email="student.class.mgmt.3@cbt.com",
            password="StudentPass123!",
            first_name="Siswa",
            last_name="Tiga",
            role="student",
            is_active=False,
        )
        UserProfile.objects.create(user=cls.student_one, class_grade="XII IPA 3", student_id="S-001")
        UserProfile.objects.create(user=cls.student_two, class_grade="XII IPA 3", student_id="S-002")
        UserProfile.objects.create(user=cls.student_three, class_grade="XI IPS 1", student_id="S-003")

    def test_admin_can_access_class_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("class_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manajemen Kelas")

    def test_non_admin_forbidden_access_class_list(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("class_list"))
        self.assertEqual(response.status_code, 403)

    def test_sync_profiles_action_creates_classes_and_memberships(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("class_list"), data={"action": "sync_profiles"})
        self.assertEqual(response.status_code, 302)

        class_obj = Class.objects.get(name="XII IPA 3")
        self.assertTrue(class_obj.is_active)
        member_usernames = set(
            ClassStudent.objects.filter(class_obj=class_obj).values_list("student__username", flat=True)
        )
        self.assertEqual(member_usernames, {"student_class_mgmt_1", "student_class_mgmt_2"})
        self.assertFalse(Class.objects.filter(name="XI IPS 1").exists())

    def test_admin_can_replace_class_members(self):
        class_obj = Class.objects.create(name="Kelas Uji", is_active=True)
        ClassStudent.objects.create(class_obj=class_obj, student=self.student_one)

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("class_members", kwargs={"pk": class_obj.pk}),
            data={"student_ids": [str(self.student_two.id)]},
        )
        self.assertEqual(response.status_code, 302)

        member_usernames = set(
            ClassStudent.objects.filter(class_obj=class_obj).values_list("student__username", flat=True)
        )
        self.assertEqual(member_usernames, {"student_class_mgmt_2"})

    def test_delete_class_blocked_when_used_by_exam_assignment(self):
        class_obj = Class.objects.create(name="X IPA 9", is_active=True)
        subject = Subject.objects.create(name="Matematika Lanjut", code="MTKLJ", is_active=True)
        exam = Exam.objects.create(
            created_by=self.teacher,
            subject=subject,
            title="Ujian Kelas X IPA 9",
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
            duration_minutes=90,
            passing_score=75,
            total_points=100,
            status="draft",
        )
        ExamAssignment.objects.create(exam=exam, assigned_to_type="class", class_obj=class_obj)

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("class_delete", kwargs={"pk": class_obj.pk}),
            data={"confirm_name": class_obj.name},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Class.objects.filter(pk=class_obj.pk).exists())
