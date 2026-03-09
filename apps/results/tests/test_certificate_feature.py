from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.attempts.models import ExamAttempt
from apps.core.services import invalidate_certificate_feature_cache
from apps.exams.models import Exam
from apps.notifications.models import Notification, SystemSetting
from apps.results.certificate_services import (
    issue_certificate_for_attempt,
    queue_regenerate_certificates_for_template,
)
from apps.results.models import Certificate, CertificateTemplate, ExamResult
from apps.results.tasks import send_certificate_email_task
from apps.subjects.models import Subject


class CertificateFeatureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_cert_feature",
            email="teacher.cert.feature@cbt.com",
            password="TeacherPass123!",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_cert_feature",
            email="student.cert.feature@cbt.com",
            password="StudentPass123!",
            role="student",
            is_active=True,
            first_name="Siswa",
            last_name="Sertifikat",
        )
        subject = Subject.objects.create(name="Ekonomi", code="EKO", is_active=True)
        now = timezone.now()
        cls.exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=subject,
            title="Ujian Ekonomi Sertifikat",
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
            duration_minutes=90,
            passing_score=70,
            total_points=100,
            status="published",
            certificate_enabled=True,
        )

    def _create_result_pair(self, score=88):
        now = timezone.now()
        attempt = ExamAttempt.objects.create(
            exam=self.exam,
            student=self.student,
            attempt_number=1,
            status="submitted",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            submit_time=now - timedelta(hours=1),
            total_score=score,
            percentage=score,
            passed=score >= 70,
            time_spent_seconds=1200,
        )
        result = ExamResult.objects.create(
            attempt=attempt,
            exam=self.exam,
            student=self.student,
            total_score=score,
            percentage=score,
            passed=score >= 70,
            total_questions=10,
            correct_answers=8,
            wrong_answers=2,
            unanswered=0,
            time_taken_seconds=1200,
            total_violations=0,
        )
        return attempt, result

    @patch("apps.results.certificate_services.enqueue_task_or_run")
    def test_issue_certificate_for_eligible_attempt(self, enqueue_mock):
        attempt, _ = self._create_result_pair(score=88)
        certificate, meta = issue_certificate_for_attempt(attempt)

        self.assertIsNotNone(certificate)
        self.assertTrue(meta["eligible"])
        self.assertEqual(certificate.exam_id, self.exam.id)
        self.assertEqual(certificate.student_id, self.student.id)
        self.assertEqual(certificate.attempt_id, attempt.id)
        self.assertTrue(bool(certificate.verification_token))
        self.assertEqual(float(certificate.final_percentage), 88.0)
        self.assertTrue(
            Notification.objects.filter(
                user=self.student,
                related_entity_type="certificate",
                related_entity_id=certificate.id,
            ).exists()
        )
        enqueue_mock.assert_called_once()

    @patch("apps.results.certificate_services.enqueue_task_or_run")
    def test_student_certificate_status_endpoint_loading(self, enqueue_mock):
        self.client.force_login(self.student)
        attempt, _ = self._create_result_pair(score=92)
        certificate, _ = issue_certificate_for_attempt(attempt)

        response = self.client.get(
            reverse("student_certificate_status", kwargs={"cert_id": certificate.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], "loading")
        enqueue_mock.assert_called_once()

    def test_public_verify_by_token(self):
        attempt, result = self._create_result_pair(score=90)
        cert = Certificate.objects.create(
            result=result,
            attempt=attempt,
            exam=self.exam,
            student=self.student,
            certificate_number="CERT-VERIFY-001",
            verification_token="verify-token-001",
            final_score=90,
            final_percentage=90,
            template_snapshot={},
            is_valid=True,
        )
        response = self.client.get(
            reverse("certificate_verify_token", kwargs={"token": cert.verification_token})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CERT-VERIFY-001")


class CertificateTemplateManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_template_feature",
            email="teacher.template.feature@cbt.com",
            password="TeacherPass123!",
            role="teacher",
            is_active=True,
        )
        cls.other_teacher = User.objects.create_user(
            username="teacher_template_other",
            email="teacher.template.other@cbt.com",
            password="TeacherPass123!",
            role="teacher",
            is_active=True,
        )
        cls.admin = User.objects.create_user(
            username="admin_template_feature",
            email="admin.template.feature@cbt.com",
            password="AdminPass123!",
            role="admin",
            is_active=True,
            is_staff=True,
        )

    def _template_payload(self, **overrides):
        data = {
            "template_name": "Template Sertifikat UAS",
            "layout_preset": "classic_formal",
            "layout_type": "landscape",
            "paper_size": "A4",
            "primary_color": "#1A56DB",
            "secondary_color": "#0E9F6E",
            "show_logo": "on",
            "show_score": "on",
            "show_grade": "on",
            "show_qr_code": "on",
            "qr_code_size": "M",
            "header_text": "SERTIFIKAT KELULUSAN",
            "body_text_template": "Diberikan kepada {{ student_full_name }}",
            "footer_text": "Dokumen ini sah.",
            "signatory_name": "Drs. Budi Santoso",
            "signatory_title": "Kepala Sekolah",
        }
        data.update(overrides)
        return data

    def test_teacher_can_create_template(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("teacher_certificate_template_create"),
            data=self._template_payload(),
        )
        self.assertEqual(response.status_code, 302)
        template = CertificateTemplate.objects.get(template_name="Template Sertifikat UAS")
        self.assertEqual(template.created_by_id, self.teacher.id)
        self.assertFalse(template.is_default)
        self.assertEqual(template.layout_preset, CertificateTemplate.LayoutPreset.CLASSIC_FORMAL)

    def test_portrait_preset_forces_portrait_layout(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("teacher_certificate_template_create"),
            data=self._template_payload(
                template_name="Template Portrait",
                layout_preset=CertificateTemplate.LayoutPreset.PORTRAIT_ACHIEVEMENT,
                layout_type=CertificateTemplate.LayoutType.LANDSCAPE,
            ),
        )
        self.assertEqual(response.status_code, 302)
        template = CertificateTemplate.objects.get(template_name="Template Portrait")
        self.assertEqual(
            template.layout_preset,
            CertificateTemplate.LayoutPreset.PORTRAIT_ACHIEVEMENT,
        )
        self.assertEqual(template.layout_type, CertificateTemplate.LayoutType.PORTRAIT)

    def test_teacher_list_only_shows_own_and_default_templates(self):
        own = CertificateTemplate.objects.create(
            template_name="Template Sendiri",
            created_by=self.teacher,
            is_default=False,
        )
        CertificateTemplate.objects.create(
            template_name="Template Default",
            created_by=self.other_teacher,
            is_default=True,
        )
        CertificateTemplate.objects.create(
            template_name="Template Guru Lain",
            created_by=self.other_teacher,
            is_default=False,
        )

        self.client.force_login(self.teacher)
        response = self.client.get(reverse("teacher_certificate_template_list"))
        self.assertEqual(response.status_code, 200)
        templates = list(response.context["templates"])

        self.assertTrue(any(item.id == own.id for item in templates))
        self.assertTrue(any(item.is_default for item in templates))
        self.assertFalse(any(item.template_name == "Template Guru Lain" for item in templates))

    def test_admin_can_set_default_template(self):
        current_default = CertificateTemplate.objects.create(
            template_name="Default Lama",
            created_by=self.teacher,
            is_default=True,
        )
        target = CertificateTemplate.objects.create(
            template_name="Default Baru",
            created_by=self.other_teacher,
            is_default=False,
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_certificate_template_set_default", kwargs={"pk": target.id}),
        )
        self.assertEqual(response.status_code, 302)

        current_default.refresh_from_db()
        target.refresh_from_db()
        self.assertFalse(current_default.is_default)
        self.assertTrue(target.is_default)

    def test_admin_can_preview_template(self):
        template_obj = CertificateTemplate.objects.create(
            template_name="Template Preview",
            created_by=self.teacher,
            is_default=False,
        )
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("admin_certificate_template_preview", kwargs={"pk": template_obj.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CERT-202603-ABC123")


class CertificatePhaseFiveTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_phase5_feature",
            email="teacher.phase5.feature@cbt.com",
            password="TeacherPass123!",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_phase5_feature",
            email="student.phase5.feature@cbt.com",
            password="StudentPass123!",
            role="student",
            is_active=True,
            first_name="Siswa",
            last_name="Phase5",
        )

    def tearDown(self):
        invalidate_certificate_feature_cache()

    def test_send_certificate_email_task_enabled(self):
        SystemSetting.objects.update_or_create(
            setting_key="certificate_email_enabled",
            defaults={
                "setting_value": "true",
                "setting_type": "boolean",
                "category": "certificates",
                "description": "Kirim email saat sertifikat siap",
                "is_public": False,
            },
        )
        invalidate_certificate_feature_cache()

        cert = Certificate.objects.create(
            student=self.student,
            certificate_number="CERT-EMAIL-001",
            verification_token="token-email-001",
            certificate_url="https://example.com/certificates/CERT-EMAIL-001.pdf",
            template_snapshot={},
            is_valid=True,
        )

        with patch("apps.results.tasks.send_mail") as send_mail_mock:
            result = send_certificate_email_task(str(cert.id))

        self.assertTrue(result["ok"])
        self.assertEqual(result["recipient"], self.student.email)
        send_mail_mock.assert_called_once()

    @patch("apps.results.certificate_services.enqueue_task_or_run")
    def test_queue_regenerate_certificates_for_template(self, enqueue_mock):
        template_target = CertificateTemplate.objects.create(
            template_name="Template Target",
            created_by=self.teacher,
            is_default=False,
            header_text="HEADER BARU",
        )
        template_other = CertificateTemplate.objects.create(
            template_name="Template Lain",
            created_by=self.teacher,
            is_default=False,
        )

        cert_target = Certificate.objects.create(
            student=self.student,
            certificate_number="CERT-REGEN-001",
            verification_token="token-regen-001",
            template_snapshot={
                "source_template_id": str(template_target.id),
                "template": {"header_text": "HEADER LAMA"},
                "branding": {},
            },
            pdf_file_path="certificates/old-target.pdf",
            certificate_url="https://example.com/certificates/old-target.pdf",
            pdf_generated_at=timezone.now(),
            is_valid=True,
        )
        Certificate.objects.create(
            student=self.student,
            certificate_number="CERT-REGEN-002",
            verification_token="token-regen-002",
            template_snapshot={
                "source_template_id": str(template_other.id),
                "template": {"header_text": "HEADER OTHER"},
                "branding": {},
            },
            is_valid=True,
        )

        result = queue_regenerate_certificates_for_template(template_target)
        cert_target.refresh_from_db()

        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["queued"], 1)
        self.assertEqual(result["skipped"], 0)
        self.assertIsNone(cert_target.pdf_generated_at)
        self.assertEqual(cert_target.pdf_file_path, "")
        self.assertEqual(cert_target.certificate_url, "")
        self.assertEqual(
            cert_target.template_snapshot["template"]["header_text"],
            "HEADER BARU",
        )
        enqueue_mock.assert_called_once()


class TeacherCertificateExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_export_cert",
            email="teacher.export.cert@cbt.com",
            password="TeacherPass123!",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_export_cert",
            email="student.export.cert@cbt.com",
            password="StudentPass123!",
            role="student",
            is_active=True,
        )
        subject = Subject.objects.create(name="Informatika", code="INF", is_active=True)
        now = timezone.now()
        exam = Exam.objects.create(
            created_by=cls.teacher,
            subject=subject,
            title="Ujian Informatika Export",
            start_time=now - timedelta(days=1),
            end_time=now + timedelta(days=1),
            duration_minutes=90,
            passing_score=70,
            total_points=100,
            status="published",
        )
        attempt = ExamAttempt.objects.create(
            exam=exam,
            student=cls.student,
            attempt_number=1,
            status="submitted",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            submit_time=now - timedelta(hours=1),
            total_score=90,
            percentage=90,
            passed=True,
            time_spent_seconds=1200,
        )
        Certificate.objects.create(
            attempt=attempt,
            exam=exam,
            student=cls.student,
            certificate_number="CERT-EXPORT-001",
            verification_token="token-export-001",
            final_score=90,
            final_percentage=90,
            template_snapshot={},
            is_valid=True,
        )

    def test_teacher_can_export_certificates_xlsx(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("teacher_certificate_export"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            response["Content-Type"],
        )


class TeacherCertificateManagementPolishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username="teacher_manage_cert",
            email="teacher.manage.cert@cbt.com",
            password="TeacherPass123!",
            role="teacher",
            is_active=True,
        )
        cls.student = User.objects.create_user(
            username="student_manage_cert",
            email="student.manage.cert@cbt.com",
            password="StudentPass123!",
            role="student",
            is_active=True,
            first_name="Siswa",
            last_name="Kelola",
        )
        cls.subject = Subject.objects.create(name="Fisika", code="FIS", is_active=True)
        now = timezone.now()
        cls.exam_a = Exam.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            title="Ujian Fisika A",
            start_time=now - timedelta(days=3),
            end_time=now - timedelta(days=2),
            duration_minutes=90,
            passing_score=70,
            total_points=100,
            status="completed",
            certificate_enabled=True,
        )
        cls.exam_b = Exam.objects.create(
            created_by=cls.teacher,
            subject=cls.subject,
            title="Ujian Fisika B",
            start_time=now - timedelta(days=1),
            end_time=now,
            duration_minutes=90,
            passing_score=70,
            total_points=100,
            status="completed",
            certificate_enabled=True,
        )
        cls.active_certificate = Certificate.objects.create(
            exam=cls.exam_a,
            student=cls.student,
            certificate_number="CERT-MANAGE-001",
            verification_token="token-manage-001",
            final_score=90,
            final_percentage=90,
            template_snapshot={},
            pdf_file_path="certificates/student/cert-1.pdf",
            pdf_generated_at=timezone.now(),
            is_valid=True,
        )
        cls.loading_certificate = Certificate.objects.create(
            exam=cls.exam_b,
            student=cls.student,
            certificate_number="CERT-MANAGE-002",
            verification_token="token-manage-002",
            final_score=80,
            final_percentage=80,
            template_snapshot={},
            pdf_file_path="",
            pdf_generated_at=None,
            is_valid=True,
        )

    def test_teacher_certificate_list_supports_status_and_exam_filter(self):
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse("teacher_certificate_list"),
            data={"status": "active", "exam": str(self.exam_a.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CERT-MANAGE-001")
        self.assertNotContains(response, "CERT-MANAGE-002")

    def test_teacher_certificate_list_supports_date_filter(self):
        old_date = timezone.now() - timedelta(days=30)
        recent_date = timezone.now() - timedelta(days=1)
        self.active_certificate.issued_at = old_date
        self.active_certificate.save(update_fields=["issued_at", "updated_at"])
        self.loading_certificate.issued_at = recent_date
        self.loading_certificate.save(update_fields=["issued_at", "updated_at"])

        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse("teacher_certificate_list"),
            data={"date_from": (timezone.localdate() - timedelta(days=5)).isoformat()},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "CERT-MANAGE-001")
        self.assertContains(response, "CERT-MANAGE-002")

    def test_teacher_revoke_certificate_respects_next_url(self):
        self.client.force_login(self.teacher)
        next_url = f"{reverse('teacher_certificate_list')}?status=active"
        response = self.client.post(
            reverse("teacher_certificate_revoke", kwargs={"cert_id": self.active_certificate.id}),
            data={"reason": "Dokumen pengganti diterbitkan", "next": next_url},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)
        self.active_certificate.refresh_from_db()
        self.assertIsNotNone(self.active_certificate.revoked_at)
        self.assertFalse(self.active_certificate.is_valid)

    def test_student_download_by_id_shows_revoked_message(self):
        self.client.force_login(self.student)
        self.active_certificate.revoked_at = timezone.now()
        self.active_certificate.is_valid = False
        self.active_certificate.save(update_fields=["revoked_at", "is_valid", "updated_at"])

        response = self.client.get(
            reverse("student_certificate_download_by_id", kwargs={"cert_id": self.active_certificate.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertTrue(any("telah dicabut" in str(message) for message in messages))

    @patch("apps.results.certificate_services.enqueue_task_or_run")
    def test_teacher_bulk_issue_accepts_next_redirect(self, enqueue_mock):
        exam = Exam.objects.create(
            created_by=self.teacher,
            subject=self.subject,
            title="Ujian Fisika Bulk",
            start_time=timezone.now() - timedelta(days=2),
            end_time=timezone.now() - timedelta(days=1),
            duration_minutes=90,
            passing_score=70,
            total_points=100,
            status="completed",
            certificate_enabled=True,
        )
        attempt = ExamAttempt.objects.create(
            exam=exam,
            student=self.student,
            attempt_number=1,
            status="submitted",
            start_time=timezone.now() - timedelta(days=2, hours=2),
            end_time=timezone.now() - timedelta(days=2, hours=1),
            submit_time=timezone.now() - timedelta(days=2, hours=1),
            total_score=85,
            percentage=85,
            passed=True,
            time_spent_seconds=1200,
        )
        ExamResult.objects.create(
            attempt=attempt,
            exam=exam,
            student=self.student,
            total_score=85,
            percentage=85,
            passed=True,
            total_questions=10,
            correct_answers=8,
            wrong_answers=2,
            unanswered=0,
            time_taken_seconds=1200,
            total_violations=0,
        )

        self.client.force_login(self.teacher)
        next_url = f"{reverse('teacher_certificate_list')}?status=loading"
        response = self.client.post(
            reverse("teacher_certificate_bulk_issue", kwargs={"exam_id": exam.id}),
            data={"next": next_url},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)
        self.assertTrue(Certificate.objects.filter(exam=exam, student=self.student).exists())
        enqueue_mock.assert_called()
